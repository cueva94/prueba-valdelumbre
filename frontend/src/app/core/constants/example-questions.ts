/**
 * Preguntas de ejemplo de la interfaz, como claves de traducción. Todas se han comprobado contra
 * la API en los dos idiomas: las que tienen respuesta citan lugares del catálogo, y la de la
 * tirolina muestra que el asistente no inventa.
 */

export interface Topic {
  labelKey: string;
  questionKey: string;
}

export const EXAMPLE_QUESTIONS: readonly string[] = [
  'questions.examples.accessibleMuseums',
  'questions.examples.outdoorWithKids',
  'questions.examples.openMondayNoon',
  'questions.examples.localWine',
  'questions.examples.zipLine',
];

export const STARTER_QUESTIONS: readonly string[] = [
  ...EXAMPLE_QUESTIONS,
  'questions.examples.free',
];

export const TOPICS: readonly Topic[] = [
  'hours',
  'accessibility',
  'kids',
  'wine',
  'outdoors',
  'free',
].map((topic) => ({
  labelKey: `questions.topics.${topic}.label`,
  questionKey: `questions.topics.${topic}.question`,
}));

/** Preguntas rápidas de la ficha de un lugar: el asistente las responde sobre ese lugar. */
export const QUICK_QUESTIONS: readonly string[] = [
  'questions.aboutPlace.hours',
  'questions.aboutPlace.accessible',
  'questions.aboutPlace.price',
];
