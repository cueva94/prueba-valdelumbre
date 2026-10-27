export type TranslationParams = Record<string, string | number>;

/**
 * Lo que necesitan las funciones de formato para escribir en el idioma activo: los textos de la
 * interfaz y el locale de fechas, listas y precios. Lo cumple `LanguageService`.
 */
export interface Texts {
  t(key: string, params?: TranslationParams): string;
  locale(): string;
}
