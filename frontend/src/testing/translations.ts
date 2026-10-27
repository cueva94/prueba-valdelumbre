import { EnvironmentProviders, inject, provideAppInitializer, Provider } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import {
  provideTranslateLoader,
  provideTranslateService,
  TranslateLoader,
  TranslationObject,
} from '@ngx-translate/core';
import { Observable, of } from 'rxjs';

import en from '../../public/i18n/en.json';
import es from '../../public/i18n/es.json';
import { Language } from '../app/core/models/poi.model';
import { DEFAULT_LANGUAGE, LanguageService } from '../app/core/services/language.service';

export const TRANSLATIONS: Record<Language, TranslationObject> = { es, en };

/** Las traducciones reales, sin HTTP: así `HttpTestingController` solo ve las peticiones a la API. */
class JsonLoader implements TranslateLoader {
  getTranslation(language: string): Observable<TranslationObject> {
    return of(TRANSLATIONS[language as Language] ?? TRANSLATIONS[DEFAULT_LANGUAGE]);
  }
}

/** El servicio de idioma real, ya en `language`: para probar las funciones de formato. */
export async function languageIn(language: Language): Promise<LanguageService> {
  TestBed.configureTestingModule({ providers: provideTestTranslations() });
  const service = TestBed.inject(LanguageService);
  await service.use(language);
  return service;
}

/** Como en la aplicación: el idioma se inicializa (guardado o español) antes del primer test. */
export function provideTestTranslations(): (Provider | EnvironmentProviders)[] {
  return [
    provideTranslateService({
      fallbackLang: DEFAULT_LANGUAGE,
      loader: provideTranslateLoader(JsonLoader),
    }),
    provideAppInitializer(() => inject(LanguageService).init()),
  ];
}
