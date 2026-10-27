import { Language } from '../models/poi.model';
import { Texts, TranslationParams } from './texts';

/**
 * Redacción más cercana de las frases fijas con las que el backend envuelve su respuesta
 * («Según el catálogo, estos 2 lugares cumplen lo que pides (museos; accesible):»). Solo se
 * reescriben esas plantillas: los nombres y las descripciones de los lugares no se tocan, y una
 * línea que no encaja con ninguna plantilla se muestra tal cual llega.
 *
 * Los patrones reconocen el texto del backend en el idioma de la respuesta; lo que se muestra
 * sale de las traducciones y los formatos de ese mismo idioma (`texts`).
 */
export function humanizeAnswer(text: string, language: Language, texts: Texts): string {
  const backend = BACKEND[language];
  // Las claves de `assistant.answer` van sin prefijo; la conjunción es la común de la interfaz.
  const t: Translate = (key, params) =>
    texts.t(key === AND ? key : `assistant.answer.${key}`, params);
  return text
    .split('\n')
    .map((line) =>
      line.startsWith('- ')
        ? replaceAll(line, backend.items(t, texts))
        : replaceFirst(line, backend.lines(t, backend)),
    )
    .join('\n');
}

type Translate = (key: string, params?: TranslationParams) => string;

const AND = 'common.and';
type Rule = [RegExp, (...groups: string[]) => string];

/** Cómo escribe el backend cada idioma: sus criterios, sus frases y sus motivos. */
interface Backend {
  accessible: string;
  free: string;
  /** Prefijo de los criterios de apertura: «abierto el lunes a las 12:00». */
  open: string;
  /** «ahora, lunes 26/10 a las 12:00» → «lunes 26/10, a las 12:00»; null si no es «ahora». */
  now: (moment: string) => string | null;
  /** Motivos de «no consta …» y su clave en `assistant.answer.reason`. */
  reasons: Readonly<Record<string, string>>;
  lines: (t: Translate, backend: Backend) => readonly Rule[];
  items: (t: Translate, texts: Texts) => readonly Rule[];
}

function replaceFirst(line: string, rules: readonly Rule[]): string {
  for (const [pattern, render] of rules) {
    const match = pattern.exec(line);
    if (match) {
      return render(...match.slice(1));
    }
  }
  return line;
}

function replaceAll(line: string, rules: readonly Rule[]): string {
  return rules.reduce(
    (current, [pattern, render]) =>
      current.replace(pattern, (...args: string[]) => render(...args.slice(1))),
    line,
  );
}

/** «a, b y c». */
function join(items: string[], lastSeparator: string): string {
  return items.length > 1
    ? `${items.slice(0, -1).join(', ')}${lastSeparator}${items.at(-1)}`
    : (items[0] ?? '');
}

const form = (count: number) => (count === 1 ? 'one' : 'other');

function moment(criterion: string, backend: Backend, t: Translate): string {
  const value = criterion.slice(backend.open.length);
  const when = backend.now(value);
  return when === null ? value : t('momentNow', { when });
}

/** Lo que se afirma de los lugares: «encajan con lo que buscas y son accesibles». */
function predicates(criteria: string, count: number, backend: Backend, t: Translate): string {
  const stated: string[] = [];
  let matchesRequest = false;
  for (const criterion of criteria.split('; ')) {
    if (criterion === backend.accessible) {
      stated.push(t(`isAccessible.${form(count)}`));
    } else if (criterion === backend.free) {
      stated.push(t(`isFree.${form(count)}`));
    } else if (criterion.startsWith(backend.open)) {
      stated.push(t(`isOpen.${form(count)}`, { moment: moment(criterion, backend, t) }));
    } else {
      matchesRequest = true;
    }
  }
  const all = matchesRequest ? [t(`matchesRequest.${form(count)}`), ...stated] : stated;
  return join(all, t(AND));
}

/** «museos; accesible; abierto el lunes» → «museos, accesible y abierto el lunes». */
function criteriaList(criteria: string, backend: Backend, t: Translate): string {
  const items = criteria
    .split('; ')
    .map((criterion) =>
      criterion.startsWith(backend.open)
        ? t('openCriterion', { moment: moment(criterion, backend, t) })
        : criterion,
    );
  return join(items, t(AND));
}

/** «si es accesible / el precio» → «si son accesibles ni el precio». */
function reasonList(reasons: string, count: number, backend: Backend, t: Translate): string {
  const items = reasons.split(' / ').map((reason) => {
    const key = backend.reasons[reason];
    return key ? t(`reason.${key}.${form(count)}`) : reason;
  });
  return join(items, t('or'));
}

/** «01/06» → «1 de junio» / «1 June». */
function dayAndMonth(dayMonth: string, texts: Texts): string {
  const [day, month] = dayMonth.split('/').map(Number);
  return new Intl.DateTimeFormat(texts.locale(), {
    day: 'numeric',
    month: 'long',
    timeZone: 'UTC',
  }).format(Date.UTC(2024, month - 1, day));
}

/** Temporada y precio de un lugar con el formato del idioma: «(del 01/06 al 30/09)», «4,5 €». */
function formats(season: RegExp, price: RegExp, texts: Texts): Rule[] {
  return [
    [
      season,
      (start, end) =>
        `(${texts.t('hours.seasonInline', {
          start: dayAndMonth(start, texts),
          end: dayAndMonth(end, texts),
        })})`,
    ],
    [
      price,
      (whole, tenths) =>
        new Intl.NumberFormat(texts.locale(), {
          style: 'currency',
          currency: 'EUR',
          minimumFractionDigits: 2,
        }).format(Number(`${whole}.${tenths}`)),
    ],
  ];
}

const SPANISH: Backend = {
  accessible: 'accesible',
  free: 'gratis',
  open: 'abierto ',
  now: (value) =>
    value.startsWith('ahora, ')
      ? value.slice('ahora, '.length).replace(' a las ', ', a las ')
      : null,
  reasons: { 'si es accesible': 'accessible', 'el precio': 'price', 'el horario': 'hours' },
  lines: (t, backend) => [
    [
      /^Según el catálogo, este lugar cumple lo que pides \((.+)\):$/,
      (criteria) => t('oneMatch', { predicates: predicates(criteria, 1, backend, t) }),
    ],
    [
      /^Según el catálogo, estos (\d+) lugares cumplen lo que pides \((.+)\):$/,
      (count, criteria) =>
        t('manyMatches', { count, predicates: predicates(criteria, Number(count), backend, t) }),
    ],
    [
      /^No hay un único lugar que cumpla eso: según el catálogo, son (\d+):$/,
      (count) => t('notUnique', { count }),
    ],
    [/^Según el catálogo:$/, () => t('aboutNamedPlaces')],
    [
      /^No he encontrado en el catálogo ningún lugar que cumpla todo lo que pides \((.+)\)\.$/,
      (criteria) => t('noMatches', { criteria: criteriaList(criteria, backend, t) }),
    ],
    [
      /^El catálogo no tiene información sobre (.+), así que no puedo recomendarte nada sobre eso\.$/,
      (terms) => t('unknownTerms', { terms }),
    ],
    [
      /^No he encontrado en tu pregunta nada que pueda buscar en el catálogo\./,
      () => t('nothingUnderstood'),
    ],
    [
      /^De 1 lugar más no consta (.+), así que no lo incluyo\.$/,
      (reasons) => t('unverified.one', { reasons: reasonList(reasons, 1, backend, t) }),
    ],
    [
      /^De (\d+) lugares más no consta (.+), así que no los incluyo\.$/,
      (count, reasons) =>
        t('unverified.other', { count, reasons: reasonList(reasons, Number(count), backend, t) }),
    ],
  ],
  items: (t, texts) => [
    [/no consta si es accesible/g, () => t('notConfirmed.accessible')],
    [/no consta el precio/g, () => t('notConfirmed.price')],
    [/no consta si abre en ese momento/g, () => t('notConfirmed.open')],
    [/no consta si abre ese día/g, () => t('notConfirmed.thatDay')],
    [/está cerrado en ese momento/g, () => t('failed.open')],
    [/Horario: no consta\./g, () => t('hoursUnpublished')],
    [/Precio: no consta\./g, () => t('priceUnpublished')],
    [/ \(incompleto\)\./g, () => t('hoursIncomplete')],
    ...formats(/\(del (\d\d\/\d\d) al (\d\d\/\d\d)\)/g, /\b(\d{1,4}),(\d) €/g, texts),
  ],
};

const ENGLISH: Backend = {
  accessible: 'accessible',
  free: 'free',
  open: 'open ',
  now: (value) =>
    value.startsWith('now, ') ? value.slice('now, '.length).replace(' at ', ', ') : null,
  reasons: {
    'whether they are accessible': 'accessible',
    'the price': 'price',
    'the opening hours': 'hours',
  },
  lines: (t, backend) => [
    [
      /^According to the catalogue, this place meets your request \((.+)\):$/,
      (criteria) => t('oneMatch', { predicates: predicates(criteria, 1, backend, t) }),
    ],
    [
      /^According to the catalogue, these (\d+) places meet your request \((.+)\):$/,
      (count, criteria) =>
        t('manyMatches', { count, predicates: predicates(criteria, Number(count), backend, t) }),
    ],
    [
      /^There isn't just one place: according to the catalogue, there are (\d+):$/,
      (count) => t('notUnique', { count }),
    ],
    [/^According to the catalogue:$/, () => t('aboutNamedPlaces')],
    [
      /^I couldn't find any place in the catalogue that meets everything \((.+)\)\.$/,
      (criteria) => t('noMatches', { criteria: criteriaList(criteria, backend, t) }),
    ],
    [
      /^The catalogue has no information about (.+), so I can't recommend anything about that\.$/,
      (terms) => t('unknownTerms', { terms }),
    ],
    [
      /^I couldn't find anything in your question that I can look up in the catalogue\./,
      () => t('nothingUnderstood'),
    ],
    [
      /^For 1 more place the catalogue doesn't state (.+), so I left it out\.$/,
      (reasons) => t('unverified.one', { reasons: reasonList(reasons, 1, backend, t) }),
    ],
    [
      /^For (\d+) more places the catalogue doesn't state (.+), so I left them out\.$/,
      (count, reasons) =>
        t('unverified.other', { count, reasons: reasonList(reasons, Number(count), backend, t) }),
    ],
  ],
  items: (t, texts) => [
    [/the catalogue doesn't state whether it is accessible/g, () => t('notConfirmed.accessible')],
    [/the catalogue doesn't state the price/g, () => t('notConfirmed.price')],
    [/the catalogue doesn't state whether it is open at that time/g, () => t('notConfirmed.open')],
    [/the catalogue doesn't state whether it opens that day/g, () => t('notConfirmed.thatDay')],
    // Motivos tras el nombre («Valdelumbre Castle: is not accessible»): la frase necesita sujeto.
    [/: is not accessible/g, () => `: ${t('failed.accessible')}`],
    [/: is not free/g, () => `: ${t('failed.free')}`],
    [/: is closed at that time/g, () => `: ${t('failed.open')}`],
    [/: is not open that day/g, () => `: ${t('failed.thatDay')}`],
    [/Opening hours: not available\./g, () => t('hoursUnpublished')],
    [/Price: not available\./g, () => t('priceUnpublished')],
    [/ \(incomplete\)\./g, () => t('hoursIncomplete')],
    ...formats(/\(from (\d\d\/\d\d) to (\d\d\/\d\d)\)/g, /\b(\d{1,4})\.(\d) €/g, texts),
  ],
};

const BACKEND: Record<Language, Backend> = { es: SPANISH, en: ENGLISH };
