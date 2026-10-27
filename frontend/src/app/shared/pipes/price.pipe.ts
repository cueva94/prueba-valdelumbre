import { inject, Pipe, PipeTransform } from '@angular/core';

import { Price } from '../../core/models/poi.model';
import { LanguageService } from '../../core/services/language.service';
import { formatPrice } from '../../core/utils/price';

/** Impuro: se vuelve a evaluar al cambiar el idioma, aunque el precio sea el mismo. */
@Pipe({ name: 'price', pure: false })
export class PricePipe implements PipeTransform {
  private readonly language = inject(LanguageService);

  transform(price: Price | null): string {
    return formatPrice(price, this.language);
  }
}
