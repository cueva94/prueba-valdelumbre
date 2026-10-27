import { Component, computed, inject, input, signal, viewChild } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';

import { CATEGORIES, isCategory } from '../../core/constants/categories';
import { Category, Poi, PoiFilters } from '../../core/models/poi.model';
import { LanguageService } from '../../core/services/language.service';
import { PoiService } from '../../core/services/poi.service';
import { PlacesStore } from '../../core/state/places.store';
import { isHoursUnknown, weekdayNames } from '../../core/utils/opening-hours';
import { PoiCard } from '../../shared/components/poi-card/poi-card';
import { StatePanel } from '../../shared/components/state-panel/state-panel';
import { PoiMap } from '../../shared/components/poi-map/poi-map';

/** Valor de `?open=` para «ahora»; en la API es `abierto_en=ahora`. */
const OPEN_NOW = 'now';
/** Día ISO y hora: `1T12:00` es lunes a las 12:00 (mismo formato que la API). */
const OPEN_AT = /^([1-7])T(\d{2}:\d{2})$/;
const DEFAULT_HOUR = '12:00';
/** Horas del selector (08:00 a 22:00), como en el diseño. */
const HOUR_OPTIONS = Array.from(
  { length: 15 },
  (_, index) => `${String(index + 8).padStart(2, '0')}:00`,
);
const SKELETON_CARDS = 6;

type QueryChanges = Partial<Record<'category' | 'accessible' | 'open', string | null>>;

/**
 * Explorar: lista y mapa con los filtros de GET /api/pois, guardados en la URL
 * (`?category=museo&accessible=true&open=now`) para poder compartirla y volver atrás.
 */
@Component({
  selector: 'app-places-list-page',
  imports: [RouterLink, TranslatePipe, PoiCard, PoiMap, StatePanel],
  templateUrl: './places-list.page.html',
  styleUrl: './places-list.page.css',
})
export class PlacesListPage {
  /** Parámetros de la URL, enlazados por el router. */
  readonly category = input<string>();
  readonly accessible = input<string>();
  readonly open = input<string>();

  private readonly router = inject(Router);
  private readonly poiService = inject(PoiService);
  private readonly places = inject(PlacesStore);
  private readonly language = inject(LanguageService);
  private readonly map = viewChild(PoiMap);

  /** Lo que llega en la URL, validado: un valor desconocido se ignora en lugar de enviarse. */
  protected readonly filters = computed<PoiFilters>(() => {
    const category = this.category();
    const open = this.open();
    let abiertoEn: string | undefined;
    if (open === OPEN_NOW) {
      abiertoEn = 'ahora';
    } else if (open && OPEN_AT.test(open)) {
      abiertoEn = open;
    }
    return {
      categoria: isCategory(category) ? category : undefined,
      accesible: parseBoolean(this.accessible()),
      abiertoEn,
    };
  });

  protected readonly hasFilters = computed(() => {
    const filters = this.filters();
    return !!filters.categoria || filters.accesible !== undefined || !!filters.abiertoEn;
  });

  /** Catálogo completo (compartido): encuadre del mapa, contadores y, sin filtros, la lista. */
  protected readonly catalog = this.places.catalog;
  /** Con filtros, los resultados los calcula el backend; sin filtros no se pide nada más. */
  private readonly filtered = this.poiService.list(() =>
    this.hasFilters() ? this.filters() : undefined,
  );
  /** El recurso que alimenta la lista: el filtrado o, sin filtros, el catálogo. */
  protected readonly results = computed(() => (this.hasFilters() ? this.filtered : this.catalog));

  protected readonly categories = CATEGORIES;
  /** «lunes»… en minúscula: van detrás de «El» / «On». */
  protected readonly weekdays = computed(() =>
    weekdayNames(this.language).map((name) =>
      this.language.current() === 'es' ? name.toLocaleLowerCase('es') : name,
    ),
  );
  protected readonly skeletons = Array.from({ length: SKELETON_CARDS }, (_, index) => index);
  protected readonly selectedId = signal<string | null>(null);

  protected readonly catalogPois = this.places.pois;
  protected readonly catalogCount = this.places.count;
  protected readonly resultPois = computed<readonly Poi[]>(() => {
    const results = this.results();
    return results.hasValue() ? results.value() : [];
  });
  protected readonly activeId = computed(() => {
    const id = this.selectedId();
    return this.resultPois().some((poi) => poi.id === id) ? id : null;
  });

  /** Valor del selector «Abierto»: '' (cualquier momento), 'now' o el día ISO ('1'…'7'). */
  protected readonly openDay = computed(() => {
    const open = this.open();
    if (open === OPEN_NOW) {
      return OPEN_NOW;
    }
    return (open && OPEN_AT.exec(open)?.[1]) || '';
  });
  protected readonly openHour = computed(() => {
    const open = this.open();
    return (open && OPEN_AT.exec(open)?.[2]) || DEFAULT_HOUR;
  });
  /** Si la URL trae una hora que no está en el selector (12:30), se añade para mostrarla. */
  protected readonly hourOptions = computed(() =>
    HOUR_OPTIONS.includes(this.openHour())
      ? HOUR_OPTIONS
      : [...HOUR_OPTIONS, this.openHour()].sort((a, b) => a.localeCompare(b)),
  );

  protected readonly countLabel = computed(() => {
    const results = this.results();
    if (results.isLoading()) {
      return this.language.t('common.loadingPlaces');
    }
    if (!results.hasValue()) {
      return '';
    }
    return this.language.plural('common.places', results.value().length);
  });

  /**
   * Lugares que cumplen el resto de filtros pero no publican horario: el backend no los da por
   * abiertos, así que no aparecen al filtrar por apertura. Se avisa de cuántos son.
   */
  protected readonly unpublishedHoursCount = computed(() => {
    const filters = this.filters();
    if (!filters.abiertoEn) {
      return 0;
    }
    return this.catalogPois().filter(
      (poi) =>
        isHoursUnknown(poi.horario) &&
        (!filters.categoria || poi.categoria === filters.categoria) &&
        (filters.accesible === undefined || poi.accesible === filters.accesible),
    ).length;
  });
  protected readonly unpublishedHoursNotice = computed(() =>
    this.language.plural('places.unpublishedHours', this.unpublishedHoursCount()),
  );

  protected categoryCount(category: Category | null): number {
    return category
      ? (this.places.countByCategory()?.get(category) ?? 0)
      : (this.catalogCount() ?? 0);
  }

  protected setCategory(category: Category | null): void {
    this.navigate({ category });
  }

  protected onAccessibilityChange(event: Event): void {
    this.navigate({ accessible: (event.target as HTMLSelectElement).value || null });
  }

  /** «En cualquier momento» quita el filtro; un día de la semana conserva la hora elegida. */
  protected onDayChange(event: Event): void {
    const day = (event.target as HTMLSelectElement).value;
    let open: string | null = null;
    if (day === OPEN_NOW) {
      open = OPEN_NOW;
    } else if (day) {
      open = `${day}T${this.openHour()}`;
    }
    this.navigate({ open });
  }

  protected onHourChange(event: Event): void {
    this.navigate({ open: `${this.openDay()}T${(event.target as HTMLSelectElement).value}` });
  }

  protected clearFilters(): void {
    void this.router.navigate([], { queryParams: {}, replaceUrl: true });
  }

  protected retry(): void {
    this.places.reload();
    if (this.hasFilters()) {
      this.filtered.reload();
    }
  }

  /** «Ver en el mapa» desde la lista: selecciona la chincheta y le pasa el foco. */
  protected locate(id: string): void {
    this.selectedId.set(id);
    this.map()?.focusPin(id);
  }

  /** Chincheta pulsada en el mapa: resalta su tarjeta y la hace visible en la lista. */
  protected onMapSelection(id: string | null): void {
    this.selectedId.set(id);
    if (id) {
      document.getElementById(`resultado-${id}`)?.scrollIntoView({ block: 'nearest' });
    }
  }

  private navigate(changes: QueryChanges): void {
    void this.router.navigate([], {
      queryParams: changes,
      queryParamsHandling: 'merge',
      replaceUrl: true,
    });
  }
}

function parseBoolean(value: string | undefined): boolean | undefined {
  if (value === 'true') {
    return true;
  }
  return value === 'false' ? false : undefined;
}
