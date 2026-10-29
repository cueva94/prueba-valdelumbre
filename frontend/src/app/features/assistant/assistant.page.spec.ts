import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { NavigationEnd, provideRouter, Router, withComponentInputBinding } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { filter, firstValueFrom } from 'rxjs';

import { OIL_MUSEUM } from '../../../testing/pois';
import { provideTestTranslations } from '../../../testing/translations';
import { routes } from '../../app.routes';
import { AskResponse } from '../../core/models/assistant.model';
import { LanguageService } from '../../core/services/language.service';
import { answerBlocks, AssistantPage } from './assistant.page';

const GROUNDED: AskResponse = {
  respuesta:
    'Según el catálogo, este lugar cumple lo que pides (museos; accesible):\n' +
    '- Museo del Aceite: Museo etnográfico sobre la almazara tradicional.',
  ids: ['poi-003'],
  pois: [OIL_MUSEUM],
  idioma: 'es',
};

const NO_MATCH: AskResponse = {
  respuesta:
    'El catálogo no tiene información sobre «tirolina», así que no puedo recomendarte nada sobre eso.',
  ids: [],
  pois: [],
  idioma: 'es',
};

describe('AssistantPage', () => {
  let http: HttpTestingController;
  let harness: RouterTestingHarness;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        ...provideTestTranslations(),
        provideRouter(routes, withComponentInputBinding()),
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  async function open(url: string): Promise<void> {
    harness = await RouterTestingHarness.create();
    await harness.navigateByUrl(url, AssistantPage);
    TestBed.tick();
  }

  async function render(): Promise<HTMLElement> {
    await harness.fixture.whenStable();
    harness.fixture.detectChanges();
    return harness.routeNativeElement as HTMLElement;
  }

  it('sin pregunta da la bienvenida y no llama a la API', async () => {
    await open('/asistente');
    const page = await render();

    http.expectNone('/api/preguntar');
    expect(page.textContent).toContain('¿Por dónde empezamos?');
  });

  it('envía la pregunta de la URL y muestra la respuesta con las fichas citadas', async () => {
    await open('/asistente?q=¿Qué museos son accesibles?');
    const request = http.expectOne('/api/preguntar');
    request.flush(GROUNDED);
    const page = await render();

    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual({ pregunta: '¿Qué museos son accesibles?', idioma: 'es' });
    expect(page.querySelector('#answer-question')?.textContent).toContain(
      '¿Qué museos son accesibles?',
    );
    expect(page.querySelector('.answer__text p')?.textContent).toBe(
      'Este lugar encaja con lo que buscas y es accesible:',
    );
    expect(page.querySelector('.answer__text li')?.textContent).toContain('Museo del Aceite');
    expect(
      page.querySelector('ul[aria-label="Lugares de esta respuesta"] a')?.getAttribute('href'),
    ).toBe('/lugares/poi-003');
  });

  it('sin lugares citados muestra que el catálogo no respalda ninguna recomendación', async () => {
    await open('/asistente?q=¿Hay algún sitio con tirolina?');
    http.expectOne('/api/preguntar').flush(NO_MATCH);
    const page = await render();

    expect(page.querySelector('.answer__text--no-match')?.textContent).toContain('tirolina');
    expect(page.querySelector('ul[aria-label="Lugares de esta respuesta"]')).toBeNull();
  });

  it('si falla, conserva la pregunta y permite reintentar', async () => {
    await open('/asistente?q=¿Qué museos son accesibles?');
    http.expectOne('/api/preguntar').flush(null, { status: 503, statusText: 'Unavailable' });
    let page = await render();

    expect(page.querySelector('[role="alert"]')?.textContent).toContain(
      'Vaya, no he podido responderte',
    );
    expect(page.querySelector('#answer-question')?.textContent).toContain('¿Qué museos');

    (page.querySelector('.answer__error button') as HTMLButtonElement).click();
    TestBed.tick();
    http.expectOne('/api/preguntar').flush(GROUNDED);
    page = await render();

    expect(page.querySelectorAll('ul[aria-label="Lugares de esta respuesta"] li')).toHaveLength(1);
  });

  it('en inglés, pregunta con idioma «en» y muestra la respuesta y la interfaz en inglés', async () => {
    await open('/asistente?q=Which museums are accessible?');
    http.expectOne('/api/preguntar').flush(GROUNDED);

    await TestBed.inject(LanguageService).use('en');
    TestBed.tick();
    const request = http.expectOne('/api/preguntar');
    expect(request.request.body).toEqual({
      pregunta: 'Which museums are accessible?',
      idioma: 'en',
    });
    request.flush({
      ...GROUNDED,
      respuesta:
        'According to the catalogue, this place meets your request (museums; accessible):\n' +
        '- Olive Oil Museum: Ethnographic museum about the traditional olive mill.',
      idioma: 'en',
    });
    const page = await render();

    expect(page.querySelector('h1')?.textContent?.trim()).toBe('What would you like to know?');
    expect(page.querySelector('.answer__eyebrow')?.textContent?.trim()).toBe('Your question');
    expect(page.querySelector('.answer__text p')?.textContent).toBe(
      "This place matches what you're looking for and is accessible:",
    );
    expect(page.querySelector('ul[aria-label="Places in this answer"]')).not.toBeNull();
  });

  it('al cambiar de idioma mantiene la respuesta a la vista hasta que llega la nueva', async () => {
    await open('/asistente?q=¿Qué museos son accesibles?');
    http.expectOne('/api/preguntar').flush(GROUNDED);
    await render();

    await TestBed.inject(LanguageService).use('en');
    TestBed.tick();
    const english = http.expectOne('/api/preguntar');
    harness.fixture.detectChanges();
    const waiting = harness.routeNativeElement as HTMLElement;

    expect(waiting.querySelector('.skeleton')).toBeNull();
    expect(waiting.querySelectorAll('ul.cited li')).toHaveLength(1);
    english.flush({ ...GROUNDED, idioma: 'en' });
  });

  it('una pregunta nueva no enseña la respuesta anterior mientras carga', async () => {
    await open('/asistente?q=¿Qué museos son accesibles?');
    http.expectOne('/api/preguntar').flush(GROUNDED);
    await render();

    await harness.navigateByUrl('/asistente?q=¿Hay algún sitio con tirolina?');
    TestBed.tick();
    const next = http.expectOne('/api/preguntar');
    harness.fixture.detectChanges();
    const waiting = harness.routeNativeElement as HTMLElement;

    expect(waiting.querySelector('.skeleton')).not.toBeNull();
    expect(waiting.querySelector('ul.cited')).toBeNull();
    next.flush(NO_MATCH);
  });

  it('preguntar desde la caja lleva la pregunta a la URL', async () => {
    await open('/asistente');
    const page = await render();
    const navigated = firstValueFrom(
      TestBed.inject(Router).events.pipe(filter((event) => event instanceof NavigationEnd)),
    );

    const field = page.querySelector('input') as HTMLInputElement;
    field.value = '¿Qué es gratis?';
    field.dispatchEvent(new Event('input'));
    (page.querySelector('button[type="submit"]') as HTMLButtonElement).click();
    await navigated;
    TestBed.tick();

    expect(decodeURIComponent(TestBed.inject(Router).url)).toBe('/asistente?q=¿Qué es gratis?');
    http.expectOne('/api/preguntar').flush(NO_MATCH);
  });
});

describe('answerBlocks', () => {
  it('separa párrafos y listas sin cambiar el texto', () => {
    expect(answerBlocks('Introducción:\n- Uno\n- Dos\nNota final.')).toEqual([
      { kind: 'paragraph', text: 'Introducción:' },
      { kind: 'list', items: ['Uno', 'Dos'] },
      { kind: 'paragraph', text: 'Nota final.' },
    ]);
  });
});
