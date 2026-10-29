import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, effect, inject, input } from '@angular/core';
import { Title } from '@angular/platform-browser';
import { Router, RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';

import { categoryInfo, categoryLabelKey } from '../../core/constants/categories';
import { QUICK_QUESTIONS } from '../../core/constants/example-questions';
import { TOURIST_OFFICE_ID } from '../../core/constants/places';
import { LanguageService } from '../../core/services/language.service';
import { PoiService } from '../../core/services/poi.service';
import { PlacesStore } from '../../core/state/places.store';
import {
  isHoursUnknown,
  months,
  seasonMonths,
  seasonsOf,
  seasonText,
  sharedSeason,
  weekdayInTown,
  weeklySchedule,
} from '../../core/utils/opening-hours';
import { AccessBadge } from '../../shared/components/access-badge/access-badge';
import { AskBox } from '../../shared/components/ask-box/ask-box';
import { CategoryIcon } from '../../shared/components/category-icon/category-icon';
import { PoiMap } from '../../shared/components/poi-map/poi-map';
import { StatePanel } from '../../shared/components/state-panel/state-panel';
import { PricePipe } from '../../shared/pipes/price.pipe';

const NOT_FOUND = 404;

type OpeningStatus = 'open' | 'closed' | 'unconfirmed';

interface TodayHours {
  ranges: string[];
  text: string;
  seasonal: boolean;
}

/** Ficha de un lugar: GET /api/pois/{id}. Un id inexistente o excluido muestra el estado 404. */
@Component({
  selector: 'app-place-detail-page',
  imports: [
    RouterLink,
    TranslatePipe,
    AccessBadge,
    AskBox,
    CategoryIcon,
    PoiMap,
    StatePanel,
    PricePipe,
  ],
  templateUrl: './place-detail.page.html',
  styleUrl: './place-detail.page.css',
})
export class PlaceDetailPage {
  readonly id = input.required<string>();

  private readonly router = inject(Router);
  private readonly title = inject(Title);
  private readonly poiService = inject(PoiService);
  private readonly language = inject(LanguageService);

  protected readonly place = this.poiService.get(this.id);
  protected readonly notFound = computed(() => {
    const error = this.place.error();
    return error instanceof HttpErrorResponse && error.status === NOT_FOUND;
  });
  /** Encuadre del mapa «Dónde está»: todo el catálogo, como en Inicio y Explorar. */
  protected readonly catalog = inject(PlacesStore).catalog;
  /** Si está abierto ahora lo decide el backend (abierto_en=ahora), no el navegador. */
  private readonly openNow = this.poiService.list(() =>
    this.place.hasValue() && !isHoursUnknown(this.place.value().horario)
      ? { categoria: this.place.value().categoria ?? undefined, abiertoEn: 'ahora' }
      : undefined,
  );
  /** Sin horario publicado no hay estado: los datos clave ya dicen «Horario no publicado». */
  protected readonly openingStatus = computed<OpeningStatus | null>(() => {
    if (!this.place.hasValue() || !this.openNow.hasValue()) {
      return null;
    }
    const poi = this.place.value();
    if (this.openNow.value().some((open) => open.id === poi.id)) {
      return 'open';
    }
    // Con el horario incompleto, no aparecer como abierto no basta para decir que está cerrado.
    return poi.horario.incompleto ? 'unconfirmed' : 'closed';
  });
  protected readonly tags = computed(() =>
    this.place.hasValue()
      ? this.place
          .value()
          .etiquetas.map(
            (tag) => tag.charAt(0).toLocaleUpperCase(this.language.locale()) + tag.slice(1),
          )
      : [],
  );
  protected readonly category = computed(() =>
    this.place.hasValue() ? categoryInfo(this.place.value().categoria) : undefined,
  );
  protected readonly categoryLabel = computed(() =>
    categoryLabelKey(this.place.hasValue() ? this.place.value().categoria : null),
  );
  protected readonly schedule = computed(() =>
    this.place.hasValue()
      ? weeklySchedule(this.place.value().horario, weekdayInTown(), this.language)
      : [],
  );
  protected readonly scheduleSeason = computed(() => {
    const season = this.place.hasValue() ? sharedSeason(this.place.value().horario) : null;
    return season ? seasonText(season, this.language, 'inline') : '';
  });
  /**
   * El horario publicado para hoy: sus tramos o, si no hay, un texto. Si es de temporada se
   * avisa: aquí no se decide si hoy lo es.
   */
  protected readonly today = computed<TodayHours>(() => {
    if (!this.place.hasValue()) {
      return { ranges: [], text: '', seasonal: false };
    }
    const hours = this.place.value().horario;
    const ranges = this.schedule().find((day) => day.isToday)?.ranges ?? [];
    let key = hours.incompleto ? 'placeDetail.noData' : 'placeDetail.closed';
    if (hours.siempre_abierto) {
      key = 'hours.alwaysOpen';
    } else if (isHoursUnknown(hours)) {
      key = 'hours.unpublished';
    }
    return {
      ranges,
      text: this.language.t(key),
      seasonal: ranges.length > 0 && !!this.scheduleSeason(),
    };
  });
  protected readonly hoursUnknown = computed(
    () => this.place.hasValue() && isHoursUnknown(this.place.value().horario),
  );
  private readonly seasonList = computed(() =>
    this.place.hasValue() ? seasonsOf(this.place.value().horario) : [],
  );
  protected readonly seasons = computed(() =>
    this.seasonList().map((season) => seasonText(season, this.language)),
  );
  protected readonly seasonsInline = computed(() =>
    this.seasonList().map((season) => seasonText(season, this.language, 'inline')),
  );
  protected readonly months = computed(() => {
    const inSeason = this.place.hasValue() ? seasonMonths(this.place.value().horario) : [];
    return months(this.language).map(({ name, initial }, month) => ({
      initial,
      inSeason: inSeason[month] ?? false,
      label: this.language.t(
        inSeason[month] ? 'placeDetail.monthInSeason' : 'placeDetail.monthOutOfSeason',
        { month: name },
      ),
    }));
  });
  /** Sin horario publicado, a quién preguntar; no se ofrece en la ficha de la propia oficina. */
  protected readonly touristOffice = computed(() =>
    this.place.hasValue() && this.place.value().id !== TOURIST_OFFICE_ID
      ? ['/lugares', TOURIST_OFFICE_ID]
      : null,
  );
  protected readonly quickQuestions = computed(() => {
    const place = this.place.hasValue() ? this.place.value().nombre.texto : null;
    return place ? QUICK_QUESTIONS.map((key) => this.language.t(key, { place })) : [];
  });

  constructor() {
    // El título de la pestaña (y lo primero que anuncia un lector de pantalla) es el lugar.
    effect(() => {
      if (this.place.hasValue()) {
        this.title.setTitle(
          this.language.t('titles.placeNamed', { name: this.place.value().nombre.texto }),
        );
      } else {
        this.title.setTitle(
          this.language.t(this.notFound() ? 'titles.placeNotFound' : 'titles.place'),
        );
      }
    });
  }

  /** La pregunta se refiere a este lugar: si no lo nombra, se añade para que el asistente lo sepa. */
  protected ask(question: string): void {
    if (!this.place.hasValue()) {
      return;
    }
    const name = this.place.value().nombre.texto;
    const aboutThisPlace = normalize(question).includes(normalize(name))
      ? question
      : `${question} (${name})`;
    void this.router.navigate(['/asistente'], { queryParams: { q: aboutThisPlace } });
  }
}

function normalize(text: string): string {
  return text
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .toLowerCase();
}
