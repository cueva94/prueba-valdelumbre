import { TestBed } from '@angular/core/testing';
import { Title } from '@angular/platform-browser';
import { provideRouter, TitleStrategy } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';

import { provideTestTranslations } from '../../../testing/translations';
import { routes } from '../../app.routes';
import { LanguageService } from './language.service';
import { TranslatedTitleStrategy } from './translated-title.strategy';

describe('TranslatedTitleStrategy', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        ...provideTestTranslations(),
        provideRouter(routes),
        { provide: TitleStrategy, useExisting: TranslatedTitleStrategy },
      ],
    });
  });

  it('una URL desconocida muestra la página 404, con un título que cambia con el idioma', async () => {
    const harness = await RouterTestingHarness.create('/no-existe');
    TestBed.tick();
    await harness.fixture.whenStable();
    harness.fixture.detectChanges();
    const title = TestBed.inject(Title);

    expect(harness.routeNativeElement?.textContent).toContain('Esta página no existe');
    expect(title.getTitle()).toBe('Página no encontrada · Valdelumbre');

    await TestBed.inject(LanguageService).use('en');
    TestBed.tick();

    expect(title.getTitle()).toBe('Page not found · Valdelumbre');
  });
});
