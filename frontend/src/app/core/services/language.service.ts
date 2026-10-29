import { DOCUMENT } from '@angular/common';
import { computed, inject, Injectable, signal } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { firstValueFrom } from 'rxjs';

import { Language } from '../models/poi.model';
import { PreferencesStorage } from '../persistence/preferences-storage.service';
import { Texts, TranslationParams } from '../utils/texts';

export const DEFAULT_LANGUAGE: Language = 'es';
const LOCALES: Record<Language, string> = { es: 'es-ES', en: 'en-GB' };

/**
 * Idioma de la interfaz y de la API (fichas y respuestas del asistente): un solo valor para las
 * dos. Solo cambia cuando sus traducciones ya están cargadas, así que interfaz y peticiones
 * cambian a la vez. La elección se guarda para la próxima visita (`PreferencesStorage`).
 */
@Injectable({ providedIn: 'root' })
export class LanguageService implements Texts {
  private readonly translate = inject(TranslateService);
  private readonly document = inject(DOCUMENT);
  private readonly preferences = inject(PreferencesStorage);
  private readonly language = signal<Language>(DEFAULT_LANGUAGE);

  readonly current = this.language.asReadonly();
  readonly locale = computed(() => LOCALES[this.language()]);

  init(): Promise<void> {
    return this.use(this.preferences.language() ?? DEFAULT_LANGUAGE);
  }

  /** Si no se pueden cargar sus traducciones, se usa el español; la aplicación nunca se bloquea. */
  async use(language: Language): Promise<void> {
    try {
      await firstValueFrom(this.translate.use(language));
    } catch {
      if (language !== DEFAULT_LANGUAGE) {
        await this.use(DEFAULT_LANGUAGE);
      }
      return;
    }
    this.language.set(language);
    this.document.documentElement.lang = language;
    this.preferences.saveLanguage(language);
  }

  /** Texto de la interfaz en el idioma activo. Se recalcula dentro de un computed al cambiarlo. */
  t(key: string, params?: TranslationParams): string {
    return String(this.translate.instant(key, params));
  }

  plural(key: string, count: number, params?: TranslationParams): string {
    return this.t(`${key}.${count === 1 ? 'one' : 'other'}`, { count, ...params });
  }

  /** Textos y formatos de un idioma concreto (el de una respuesta ya recibida, por ejemplo). */
  textsFor(language: Language): Texts {
    return {
      t: (key, params) => String(this.translate.instant(key, params, language)),
      locale: () => LOCALES[language],
    };
  }
}
