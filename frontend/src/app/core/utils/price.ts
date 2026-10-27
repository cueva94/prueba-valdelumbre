import { Price } from '../models/poi.model';
import { Texts } from './texts';

/** «Gratis», «4,50 €» / «€4.50», «25–35 €», el texto original o «Precio por confirmar». */
export function formatPrice(price: Price | null, texts: Texts): string {
  if (price === null) {
    return texts.t('price.unknown');
  }
  if (price.tipo === 'texto') {
    return price.texto;
  }
  if (price.maximo === 0) {
    return texts.t('price.free');
  }
  const decimals = Number.isInteger(price.minimo) && Number.isInteger(price.maximo) ? 0 : 2;
  const options = { minimumFractionDigits: decimals, maximumFractionDigits: decimals };
  if (price.minimo === price.maximo) {
    return new Intl.NumberFormat(texts.locale(), {
      ...options,
      style: 'currency',
      currency: 'EUR',
    }).format(price.minimo);
  }
  const amount = new Intl.NumberFormat(texts.locale(), options);
  return texts.t('price.range', {
    min: amount.format(price.minimo),
    max: amount.format(price.maximo),
  });
}
