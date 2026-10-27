import { Language, Poi } from './poi.model';

/** Contrato de POST /api/preguntar. */
export interface AskRequest {
  pregunta: string;
  idioma: Language;
}

export interface AskResponse {
  respuesta: string;
  /** Puntos en los que se apoya la respuesta; los decide la búsqueda del backend. */
  ids: string[];
  /** Fichas de esos puntos, en el mismo orden que `ids`. */
  pois: Poi[];
  idioma: Language;
}

/** Límite de la API para `pregunta`. */
export const MAX_QUESTION_LENGTH = 500;
