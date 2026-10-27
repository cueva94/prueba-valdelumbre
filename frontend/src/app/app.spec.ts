import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';

import { provideTestTranslations } from '../testing/translations';
import { App } from './app';
import { LANGUAGE_STORAGE_KEY } from './core/persistence/preferences-storage.service';

@Component({ template: '<h1>Página</h1>' })
class BlankPage {}

describe('App', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        ...provideTestTranslations(),
        provideRouter([
          { path: '', component: BlankPage },
          { path: 'otra', component: BlankPage },
        ]),
      ],
    });
  });

  async function start() {
    const fixture = TestBed.createComponent(App);
    await TestBed.inject(Router).navigateByUrl('/');
    fixture.detectChanges();
    const element = fixture.nativeElement as HTMLElement;
    return {
      main: element.querySelector('main') as HTMLElement,
      language: element.querySelector('app-header button') as HTMLButtonElement,
      element,
    };
  }

  it('tiene navegación principal y un enlace para saltar al contenido', async () => {
    const { element, main } = await start();

    const links = [...element.querySelectorAll('nav[aria-label="Principal"] a')];
    expect(links.map((link) => link.textContent?.trim())).toEqual([
      'Inicio',
      'Explorar',
      'Asistente',
    ]);

    (element.querySelector('.skip-link') as HTMLButtonElement).click();
    expect(document.activeElement).toBe(main);
  });

  it('el pie enlaza con las categorías, la planificación de la visita y la Oficina de Turismo', async () => {
    const { element } = await start();

    const links = [...element.querySelectorAll('app-footer a')].map((link) =>
      link.getAttribute('href'),
    );
    expect(links).toEqual(
      expect.arrayContaining([
        '/explorar?category=monumento',
        '/explorar?category=servicio',
        '/explorar?open=now',
        '/explorar?accessible=true',
        '/asistente',
        '/lugares/poi-010',
      ]),
    );
  });

  it('el selector ES | EN cambia toda la interfaz al momento y recuerda la elección', async () => {
    const { element } = await start();
    const options = [...element.querySelectorAll<HTMLButtonElement>('.language button')];

    expect(options.map((option) => option.textContent?.trim())).toEqual(['ES', 'EN']);
    expect(options.map((option) => option.getAttribute('aria-label'))).toEqual([
      'Español',
      'English',
    ]);
    expect(options[0].getAttribute('aria-pressed')).toBe('true');

    options[1].click();
    await new Promise((resolve) => setTimeout(resolve));
    TestBed.tick();

    expect(options[1].getAttribute('aria-pressed')).toBe('true');
    expect(options[0].getAttribute('aria-pressed')).toBe('false');
    const links = [...element.querySelectorAll('header nav a')];
    expect(links.map((link) => link.textContent?.trim())).toEqual(['Home', 'Explore', 'Assistant']);
    expect(element.querySelector('.skip-link')?.textContent?.trim()).toBe('Skip to content');
    expect(element.querySelector('app-footer h2')?.textContent?.trim()).toBe('Discover');
    expect(document.documentElement.lang).toBe('en');
    expect(localStorage.getItem(LANGUAGE_STORAGE_KEY)).toBe('en');
  });

  it('al cambiar de página el foco pasa al contenido; al cambiar solo la URL, no se mueve', async () => {
    const { main, language } = await start();
    const router = TestBed.inject(Router);

    language.focus();
    await router.navigateByUrl('/otra');
    expect(document.activeElement).toBe(main);

    language.focus();
    await router.navigateByUrl('/otra?filtro=1');
    expect(document.activeElement).toBe(language);
  });
});
