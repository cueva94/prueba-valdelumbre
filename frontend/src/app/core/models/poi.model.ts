/**
 * Contrato de GET /api/pois y GET /api/pois/{id}, tal como lo devuelve el backend.
 * Los nombres de las propiedades son los del JSON (en español); `null` significa «sin datos».
 */

export type Language = 'es' | 'en';

export const LANGUAGES: readonly Language[] = ['es', 'en'];

export function isLanguage(value: unknown): value is Language {
  return LANGUAGES.includes(value as Language);
}

export type Category =
  'monumento' | 'museo' | 'naturaleza' | 'ruta' | 'espacio_publico' | 'gastronomia' | 'servicio';

/** Texto en el idioma pedido o, si falta la traducción, en español; `idioma` dice cuál es. */
export interface LocalizedText {
  texto: string;
  idioma: Language;
}

export interface Coordinates {
  lat: number;
  lon: number;
}

/** Periodo del año, con los dos días incluidos («MM-DD»). */
export interface Season {
  inicio: string;
  fin: string;
}

export interface TimeSlot {
  /** ISO 8601: 1 = lunes … 7 = domingo. */
  dias: number[];
  abre: string;
  /** No incluida. Si es anterior a `abre`, la franja termina al día siguiente. */
  cierra: string;
  temporada: Season | null;
}

/** Sin `siempre_abierto` y sin franjas, el horario es desconocido, no «cerrado». */
export interface OpeningHours {
  siempre_abierto: boolean;
  franjas: TimeSlot[];
  incompleto: boolean;
}

export interface PriceRange {
  tipo: 'rango';
  minimo: number;
  maximo: number;
}

/** Precio original que no es un importe («consultar»). */
export interface UnparsedPrice {
  tipo: 'texto';
  texto: string;
}

export type Price = PriceRange | UnparsedPrice;

export interface Poi {
  id: string;
  nombre: LocalizedText;
  categoria: Category | null;
  descripcion: LocalizedText;
  coordenadas: Coordinates | null;
  accesible: boolean | null;
  horario: OpeningHours;
  precio: Price | null;
  etiquetas: string[];
}

/** Filtros de GET /api/pois; los que faltan no filtran. */
export interface PoiFilters {
  categoria?: Category;
  accesible?: boolean;
  /** `ahora` o día ISO y hora: `1T12:00` es lunes a las 12:00. */
  abiertoEn?: string;
}
