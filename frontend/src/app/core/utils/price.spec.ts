import { languageIn } from '../../../testing/translations';
import { formatPrice } from './price';

describe('formatPrice', () => {
  it.each([
    [{ tipo: 'rango' as const, minimo: 0, maximo: 0 }, 'Gratis'],
    // Entre el importe y el euro, un espacio que no se parte (como lo da Intl).
    [{ tipo: 'rango' as const, minimo: 4.5, maximo: 4.5 }, '4,50\u00a0€'],
    [{ tipo: 'rango' as const, minimo: 15, maximo: 15 }, '15\u00a0€'],
    [{ tipo: 'rango' as const, minimo: 25, maximo: 35 }, '25–35\u00a0€'],
    [{ tipo: 'texto' as const, texto: 'consultar' }, 'consultar'],
  ])('%j → %s', async (price, expected) => {
    expect(formatPrice(price, await languageIn('es'))).toBe(expected);
  });

  it('un precio desconocido no se muestra como gratis', async () => {
    expect(formatPrice(null, await languageIn('es'))).toBe('Precio por confirmar');
  });

  it('en inglés, con el formato inglés', async () => {
    const en = await languageIn('en');

    expect(formatPrice({ tipo: 'rango', minimo: 4.5, maximo: 4.5 }, en)).toBe('€4.50');
    expect(formatPrice({ tipo: 'rango', minimo: 25, maximo: 35 }, en)).toBe('€25–35');
    expect(formatPrice({ tipo: 'rango', minimo: 0, maximo: 0 }, en)).toBe('Free');
    expect(formatPrice(null, en)).toBe('Price to be confirmed');
  });
});
