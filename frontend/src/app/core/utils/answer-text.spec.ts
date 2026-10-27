import { languageIn } from '../../../testing/translations';
import { Language } from '../models/poi.model';
import { LanguageService } from '../services/language.service';
import { humanizeAnswer } from './answer-text';

let service: LanguageService;
const humanize = (text: string, language: Language) =>
  humanizeAnswer(text, language, service.textsFor(language));

beforeEach(async () => {
  service = await languageIn('en');
  await service.use('es');
});

// Textos tal cual los devuelve POST /api/preguntar con el catálogo real.
describe('humanizeAnswer', () => {
  it('reescribe la apertura sin tocar el nombre ni la descripción del lugar', () => {
    const answer = [
      'Según el catálogo, este lugar cumple lo que pides (vino):',
      '- Bodega La Encina: Bodega familiar con visita guiada y cata. Reserva previa obligatoria.',
    ].join('\n');

    expect(humanize(answer, 'es')).toBe(
      [
        'Este lugar encaja con lo que buscas:',
        '- Bodega La Encina: Bodega familiar con visita guiada y cata. Reserva previa obligatoria.',
      ].join('\n'),
    );
  });

  it.each([
    [
      'Según el catálogo, estos 2 lugares cumplen lo que pides (museos; accesible):',
      'Estos 2 lugares encajan con lo que buscas y son accesibles:',
    ],
    [
      'Según el catálogo, estos 10 lugares cumplen lo que pides (abierto ahora, lunes 26/10 a las 12:00):',
      'Estos 10 lugares están abiertos ahora (lunes 26/10, a las 12:00):',
    ],
    [
      'Según el catálogo, estos 10 lugares cumplen lo que pides (abierto el lunes a las 12:00):',
      'Estos 10 lugares están abiertos el lunes a las 12:00:',
    ],
    [
      'Según el catálogo, estos 11 lugares cumplen lo que pides (gratis):',
      'Estos 11 lugares son gratis:',
    ],
    [
      'No hay un único lugar que cumpla eso: según el catálogo, son 2:',
      'No hay un único lugar: en realidad son 2:',
    ],
    ['Según el catálogo:', 'Te cuento lo que sé:'],
    [
      'No he encontrado en el catálogo ningún lugar que cumpla todo lo que pides (museos; accesible; abierto el lunes a las 12:00).',
      'No he encontrado ningún lugar que cumpla todo lo que pides: museos, accesible y abierto el lunes a las 12:00.',
    ],
    [
      'El catálogo no tiene información sobre «aventura» ni «tirolina», así que no puedo recomendarte nada sobre eso.',
      'Lo siento, no tengo información sobre «aventura» ni «tirolina», así que no puedo recomendarte nada sobre eso.',
    ],
    [
      'De 1 lugar más no consta el horario, así que no lo incluyo.',
      'Hay 1 lugar más que podría encajar, pero no puedo confirmarte el horario, así que no lo incluyo.',
    ],
    [
      'De 2 lugares más no consta si es accesible / el precio, así que no los incluyo.',
      'Hay 2 lugares más que podrían encajar, pero no puedo confirmarte si son accesibles ni el precio, así que no los incluyo.',
    ],
  ])('«%s»', (backend, shown) => {
    expect(humanize(backend, 'es')).toBe(shown);
  });

  it('suaviza los datos que faltan y da formato a fechas y precios de cada lugar', () => {
    expect(humanize('- Puente Romano: no consta si es accesible.', 'es')).toBe(
      '- Puente Romano: no puedo confirmarte si es accesible.',
    );
    expect(
      humanize('- Ermita de la Virgen del Cerro: Pequeña ermita. Horario: no consta.', 'es'),
    ).toBe('- Ermita de la Virgen del Cerro: Pequeña ermita. Horario: no está publicado.');
    expect(
      humanize(
        '- Piscina Natural: Poza natural. Horario: todos los días de 11:00 a 20:00 (del 01/06 al 30/09).',
        'es',
      ),
    ).toBe(
      '- Piscina Natural: Poza natural. Horario: todos los días de 11:00 a 20:00 (del 1 de junio al 30 de septiembre).',
    );
    expect(humanize('- Castillo de Valdelumbre: Fortaleza. Precio: 4,5 €.', 'es')).toBe(
      '- Castillo de Valdelumbre: Fortaleza. Precio: 4,50\u00a0€.',
    );
  });

  it('también en inglés', () => {
    expect(
      humanize(
        [
          'According to the catalogue, these 10 places meet your request (open now, Monday 26/10 at 12:00):',
          '- Valdelumbre Castle',
          "For 1 more place the catalogue doesn't state the opening hours, so I left it out.",
        ].join('\n'),
        'en',
      ),
    ).toBe(
      [
        'These 10 places are open right now (Monday 26/10, 12:00):',
        '- Valdelumbre Castle',
        "There's 1 more place that might fit, but I can't confirm its opening hours, so I've left it out.",
      ].join('\n'),
    );
    expect(
      humanize('According to the catalogue, this place meets your request (wine):', 'en'),
    ).toBe("This place matches what you're looking for:");
    expect(humanize('- Valdelumbre Castle: is not accessible.', 'en')).toBe(
      '- Valdelumbre Castle: it is not accessible.',
    );
  });

  it('una línea que no encaja con ninguna plantilla se deja tal cual', () => {
    expect(humanize('Una frase nueva del backend.', 'es')).toBe('Una frase nueva del backend.');
  });
});
