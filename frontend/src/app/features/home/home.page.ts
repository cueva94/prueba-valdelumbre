import {
  afterNextRender,
  Component,
  computed,
  ElementRef,
  inject,
  Injector,
  linkedSignal,
  signal,
  viewChild,
  viewChildren,
} from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';

import { CATEGORIES, categoryInfo } from '../../core/constants/categories';
import { EXAMPLE_QUESTIONS } from '../../core/constants/example-questions';
import { Category } from '../../core/models/poi.model';
import { LanguageService } from '../../core/services/language.service';
import { PlacesStore } from '../../core/state/places.store';
import { AskBox } from '../../shared/components/ask-box/ask-box';
import { CategoryIcon } from '../../shared/components/category-icon/category-icon';
import { PoiCard } from '../../shared/components/poi-card/poi-card';
import { PoiMap } from '../../shared/components/poi-map/poi-map';
import { StatePanel } from '../../shared/components/state-panel/state-panel';

/** Lugares por tanda en la lista de Inicio: dos filas de tres. */
const PLACES_PAGE_SIZE = 6;

@Component({
  selector: 'app-home-page',
  imports: [RouterLink, TranslatePipe, AskBox, CategoryIcon, PoiCard, PoiMap, StatePanel],
  templateUrl: './home.page.html',
  styleUrl: './home.page.css',
})
export class HomePage {
  private readonly router = inject(Router);
  private readonly injector = inject(Injector);
  private readonly language = inject(LanguageService);
  private readonly map = viewChild(PoiMap);
  private readonly placeItems = viewChildren<ElementRef<HTMLElement>>('placeItem');

  /** Contadores, mapa y lista. Si el catálogo no carga, la pregunta al asistente sigue funcionando. */
  protected readonly places = inject(PlacesStore);
  protected readonly catalog = this.places.catalog;
  protected readonly examples = EXAMPLE_QUESTIONS;

  /** Categoría elegida en los chips del mapa; null = todas. */
  protected readonly mapCategory = signal<Category | null>(null);
  private readonly selectedId = signal<string | null>(null);

  protected readonly catalogPois = this.places.pois;
  protected readonly placeCount = this.places.count;
  protected readonly categories = computed(() => {
    const counts = this.places.countByCategory();
    return CATEGORIES.map((category) => ({
      ...category,
      count: counts ? (counts.get(category.id) ?? 0) : null,
    }));
  });
  /** La categoría es un campo de la ficha: se filtra el catálogo ya cargado, sin otra petición. */
  protected readonly mapPois = computed(() => {
    const category = this.mapCategory();
    const pois = this.catalogPois();
    return category ? pois.filter((poi) => poi.categoria === category) : pois;
  });
  protected readonly activeId = computed(() => {
    const id = this.selectedId();
    return this.mapPois().some((poi) => poi.id === id) ? id : null;
  });
  private readonly visibleCount = linkedSignal({
    source: this.mapCategory,
    computation: () => PLACES_PAGE_SIZE,
  });
  protected readonly visiblePlaces = computed(() => this.mapPois().slice(0, this.visibleCount()));
  protected readonly hasMorePlaces = computed(() => this.mapPois().length > this.visibleCount());
  protected readonly listTitle = computed(() => {
    if (!this.catalog.hasValue()) {
      return this.language.t('common.loadingPlaces');
    }
    const count = this.mapPois().length;
    const category = categoryInfo(this.mapCategory());
    return category
      ? this.language.plural('home.listCategory', count, {
          category: this.language.t(category.pluralKey),
        })
      : this.language.plural('home.listAll', count);
  });

  protected ask(question: string): void {
    void this.router.navigate(['/asistente'], { queryParams: { q: question } });
  }

  protected locate(id: string): void {
    this.selectedId.set(id);
    this.map()?.focusPin(id);
  }

  protected onMapSelection(id: string | null): void {
    this.selectedId.set(id);
  }

  /** «Cargar más»: la siguiente tanda. El foco pasa al primer lugar nuevo para seguir desde ahí. */
  protected showMorePlaces(): void {
    const firstNew = this.visibleCount();
    this.visibleCount.update((count) => count + PLACES_PAGE_SIZE);
    afterNextRender(() => this.placeItems()[firstNew]?.nativeElement.focus(), {
      injector: this.injector,
    });
  }
}
