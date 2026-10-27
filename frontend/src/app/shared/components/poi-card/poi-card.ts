import { Component, computed, input, output } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';

import { categoryLabelKey } from '../../../core/constants/categories';
import { Poi } from '../../../core/models/poi.model';
import { hasSeason, isHoursUnknown } from '../../../core/utils/opening-hours';
import { HoursSummaryPipe } from '../../pipes/hours.pipe';
import { PricePipe } from '../../pipes/price.pipe';
import { AccessBadge } from '../access-badge/access-badge';

/**
 * Tarjeta de un lugar. `list`: en las listas de Inicio y Explorar, con «Ver en el mapa» y
 * «Saber más». `cited`: lugar citado por el asistente; toda la tarjeta enlaza con la ficha.
 */
@Component({
  selector: 'app-poi-card',
  imports: [RouterLink, TranslatePipe, AccessBadge, PricePipe, HoursSummaryPipe],
  templateUrl: './poi-card.html',
  styleUrl: './poi-card.css',
})
export class PoiCard {
  readonly poi = input.required<Poi>();
  readonly variant = input<'list' | 'cited'>('list');
  readonly headingLevel = input<2 | 3 | 4>(2);
  readonly selected = input(false);
  /** Muestra «Ver en el mapa» (solo si el lugar tiene coordenadas). */
  readonly locatable = input(false);
  readonly locate = output<string>();

  protected readonly categoryLabel = computed(() => categoryLabelKey(this.poi().categoria));
  protected readonly seasonal = computed(() => hasSeason(this.poi().horario));
  protected readonly hoursUnknown = computed(() => isHoursUnknown(this.poi().horario));
  protected readonly canLocate = computed(() => this.locatable() && !!this.poi().coordenadas);
}
