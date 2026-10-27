import { Injectable } from '@angular/core';

import { isLanguage, Language } from '../models/poi.model';

export const LANGUAGE_STORAGE_KEY = 'valdelumbre.idioma';

/**
 * Preferencias del visitante guardadas en el navegador: por ahora, solo el idioma. Es el único
 * sitio que toca `localStorage`; para dejar de guardar el idioma basta con cambiar este servicio.
 */
@Injectable({ providedIn: 'root' })
export class PreferencesStorage {
  /** El idioma guardado, si lo hay y es válido. */
  language(): Language | null {
    try {
      const value = localStorage.getItem(LANGUAGE_STORAGE_KEY);
      return isLanguage(value) ? value : null;
    } catch {
      return null;
    }
  }

  saveLanguage(language: Language): void {
    try {
      localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
    } catch {
      // Sin almacenamiento (modo privado o bloqueado), el idioma dura lo que la visita.
    }
  }
}
