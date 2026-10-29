import { TestBed } from '@angular/core/testing';
import {
  provideTranslateLoader,
  provideTranslateService,
  TranslateLoader,
  TranslateService,
  TranslationObject,
} from '@ngx-translate/core';
import { Observable, of, throwError } from 'rxjs';

import { TRANSLATIONS } from '../../../testing/translations';
import { LANGUAGE_STORAGE_KEY } from '../persistence/preferences-storage.service';
import { LanguageService } from './language.service';

function keysOf(translations: TranslationObject, prefix = ''): string[] {
  return Object.entries(translations).flatMap(([key, value]) => {
    const path = prefix ? `${prefix}.${key}` : key;
    return typeof value === 'object' && value !== null
      ? keysOf(value as TranslationObject, path)
      : [path];
  });
}

/** Sirve las traducciones reales; las de `failing` fallan, como un JSON que no llega. */
function setUp(failing: string[] = []): LanguageService {
  class Loader implements TranslateLoader {
    getTranslation(language: string): Observable<TranslationObject> {
      return failing.includes(language)
        ? throwError(() => new Error(`No se ha podido cargar ${language}`))
        : of(TRANSLATIONS[language as 'es' | 'en']);
    }
  }
  TestBed.configureTestingModule({
    providers: [provideTranslateService({ loader: provideTranslateLoader(Loader) })],
  });
  return TestBed.inject(LanguageService);
}

describe('Traducciones', () => {
  it('el español y el inglés tienen exactamente las mismas claves', () => {
    expect(keysOf(TRANSLATIONS.en).sort()).toEqual(keysOf(TRANSLATIONS.es).sort());
  });

  it('ningún texto está vacío', () => {
    for (const translations of Object.values(TRANSLATIONS)) {
      const empty = keysOf(translations).filter((key) => {
        const value = key
          .split('.')
          .reduce<unknown>(
            (node, part) => (node as Record<string, unknown> | undefined)?.[part],
            translations,
          );
        return typeof value !== 'string' || !value.trim();
      });
      expect(empty).toEqual([]);
    }
  });
});

describe('LanguageService', () => {
  beforeEach(() => vi.spyOn(console, 'warn').mockImplementation(() => undefined));

  it('sin preferencia guardada, empieza en español', async () => {
    const language = setUp();

    await language.init();

    expect(language.current()).toBe('es');
    expect(language.locale()).toBe('es-ES');
    expect(document.documentElement.lang).toBe('es');
    expect(language.t('navigation.home')).toBe('Inicio');
  });

  it('recupera el idioma guardado', async () => {
    localStorage.setItem(LANGUAGE_STORAGE_KEY, 'en');
    const language = setUp();

    await language.init();

    expect(language.current()).toBe('en');
    expect(language.t('navigation.home')).toBe('Home');
  });

  it.each(['fr', 'EN', 'english', ''])(
    'una preferencia guardada no válida («%s») se ignora: español',
    async (stored) => {
      localStorage.setItem(LANGUAGE_STORAGE_KEY, stored);
      const language = setUp();

      await language.init();

      expect(language.current()).toBe('es');
    },
  );

  it('al cambiar de idioma lo guarda, lo marca en <html> y traduce los textos', async () => {
    const language = setUp();
    await language.init();

    await language.use('en');

    expect(language.current()).toBe('en');
    expect(localStorage.getItem(LANGUAGE_STORAGE_KEY)).toBe('en');
    expect(document.documentElement.lang).toBe('en');
    expect(language.plural('common.places', 1)).toBe('1 place');
    expect(language.plural('common.places', 3)).toBe('3 places');
  });

  it('si no carga el idioma guardado, sigue en español sin bloquear la aplicación', async () => {
    localStorage.setItem(LANGUAGE_STORAGE_KEY, 'en');
    const language = setUp(['en']);

    await language.init();

    expect(language.current()).toBe('es');
    expect(TestBed.inject(TranslateService).getCurrentLang()).toBe('es');
    expect(language.t('navigation.home')).toBe('Inicio');
  });

  it('si al cambiar de idioma no carga, se queda en el que estaba', async () => {
    const language = setUp(['en']);
    await language.init();

    await language.use('en');

    expect(language.current()).toBe('es');
    expect(localStorage.getItem(LANGUAGE_STORAGE_KEY)).toBe('es');
  });

  it('si no carga ningún idioma, la inicialización termina igualmente', async () => {
    const language = setUp(['es', 'en']);

    await expect(language.init()).resolves.toBeUndefined();
    expect(language.current()).toBe('es');
  });
});
