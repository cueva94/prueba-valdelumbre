import { HttpRequest, provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { NavigationEnd, provideRouter, Router, withComponentInputBinding } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { filter, firstValueFrom } from 'rxjs';

import { CASTLE, OIL_MUSEUM, TEST_CATALOG } from '../../../testing/pois';
import { provideTestTranslations } from '../../../testing/translations';
import { routes } from '../../app.routes';
import { LanguageService } from '../../core/services/language.service';
import { PlacesListPage } from './places-list.page';

const isCatalog = (request: HttpRequest<unknown>) =>
  request.url === '/api/pois' && request.params.keys().join() === 'idioma';
const isFiltered = (request: HttpRequest<unknown>) =>
  request.url === '/api/pois' && request.params.keys().length > 1;

describe('PlacesListPage (Explorar)', () => {
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
    await harness.navigateByUrl(url, PlacesListPage);
    TestBed.tick();
  }

  async function render(): Promise<HTMLElement> {
    await harness.fixture.whenStable();
    harness.fixture.detectChanges();
    return harness.routeNativeElement as HTMLElement;
  }

  const cardNames = (page: HTMLElement) =>
    [...page.querySelectorAll('app-poi-card h2')].map((name) => name.textContent?.trim());

  async function urlAfter(action: () => void): Promise<string> {
    const router = TestBed.inject(Router);
    const navigated = firstValueFrom(
      router.events.pipe(filter((event) => event instanceof NavigationEnd)),
    );
    action();
    await navigated;
    TestBed.tick();
    return decodeURIComponent(router.url);
  }

  const choose = (page: HTMLElement, selector: string, value: string) => () => {
    const field = page.querySelector(selector) as HTMLSelectElement;
    field.value = value;
    field.dispatchEvent(new Event('change'));
  };

  it('sin filtros pide el catálogo una sola vez y lo lista entero, con una chincheta por lugar', async () => {
    await open('/explorar');
    http.expectOne(isCatalog).flush(TEST_CATALOG);
    const page = await render();

    expect(cardNames(page)).toHaveLength(TEST_CATALOG.length);
    expect(page.querySelector('[role="status"]')?.textContent).toContain('4 lugares');
    expect(page.querySelectorAll('.pin')).toHaveLength(TEST_CATALOG.length);
    expect(page.querySelector('.pin')?.getAttribute('aria-label')).toBe(
      'Castillo de Valdelumbre, Monumento',
    );
  });

  it('envía los filtros de la URL al backend y lista lo que devuelve', async () => {
    await open('/explorar?category=museo&accessible=true&open=now');
    http.expectOne(isCatalog).flush(TEST_CATALOG);
    const filtered = http.expectOne(isFiltered);
    filtered.flush([OIL_MUSEUM]);
    const page = await render();

    expect(filtered.request.params.get('categoria')).toBe('museo');
    expect(filtered.request.params.get('accesible')).toBe('true');
    expect(filtered.request.params.get('abierto_en')).toBe('ahora');
    expect(filtered.request.params.get('idioma')).toBe('es');
    expect(cardNames(page)).toEqual(['Museo del Aceite']);
    const museums = [...page.querySelectorAll('fieldset button')].find((chip) =>
      chip.textContent?.includes('Museos'),
    );
    expect(museums?.getAttribute('aria-pressed')).toBe('true');
  });

  it('la categoría y la accesibilidad elegidas en la barra van a la URL y al backend', async () => {
    await open('/explorar');
    http.expectOne(isCatalog).flush(TEST_CATALOG);
    let page = await render();

    const museums = [...page.querySelectorAll('fieldset button')].find((chip) =>
      chip.textContent?.includes('Museos'),
    ) as HTMLButtonElement;
    expect(await urlAfter(() => museums.click())).toBe('/explorar?category=museo');
    http.expectOne(isFiltered).flush([OIL_MUSEUM]);
    page = await render();

    expect(await urlAfter(choose(page, '#filtro-accesible', 'false'))).toBe(
      '/explorar?category=museo&accessible=false',
    );
    const filtered = http.expectOne(isFiltered);
    expect(filtered.request.params.get('categoria')).toBe('museo');
    expect(filtered.request.params.get('accesible')).toBe('false');
    filtered.flush([]);
    page = await render();

    const clear = page.querySelector('.filters__summary button') as HTMLButtonElement;
    expect(await urlAfter(() => clear.click())).toBe('/explorar');
    // Sin filtros vuelve a listar el catálogo que ya tenía, sin pedir nada más.
    http.expectNone(isFiltered);
    expect(cardNames(await render())).toHaveLength(TEST_CATALOG.length);
  });

  it('el día conserva la hora elegida, y «En cualquier momento» quita el filtro de apertura', async () => {
    await open('/explorar');
    http.expectOne(isCatalog).flush(TEST_CATALOG);
    let page = await render();
    expect((page.querySelector('#filtro-hora') as HTMLSelectElement).disabled).toBe(true);

    expect(await urlAfter(choose(page, '#filtro-dia', '1'))).toBe('/explorar?open=1T12:00');
    http.expectOne(isFiltered).flush([CASTLE]);
    page = await render();

    expect(await urlAfter(choose(page, '#filtro-hora', '18:00'))).toBe('/explorar?open=1T18:00');
    http.expectOne(isFiltered).flush([CASTLE]);
    page = await render();

    expect(await urlAfter(choose(page, '#filtro-dia', '7'))).toBe('/explorar?open=7T18:00');
    const sunday = http.expectOne(isFiltered);
    expect(sunday.request.params.get('abierto_en')).toBe('7T18:00');
    sunday.flush([]);
    page = await render();

    expect(await urlAfter(choose(page, '#filtro-dia', 'now'))).toBe('/explorar?open=now');
    http.expectOne(isFiltered).flush([]);
    page = await render();
    expect((page.querySelector('#filtro-hora') as HTMLSelectElement).disabled).toBe(true);

    expect(await urlAfter(choose(page, '#filtro-dia', ''))).toBe('/explorar');
    http.expectNone(isFiltered);
  });

  it('ignora los valores de la URL que no entiende en lugar de enviarlos', async () => {
    await open('/explorar?category=castillos&accessible=quizas&open=lunes');

    http.expectOne(isCatalog).flush(TEST_CATALOG);
    http.expectNone(isFiltered);
  });

  it('al filtrar por apertura avisa de los lugares que no publican horario', async () => {
    await open('/explorar?open=1T12:00');
    http.expectOne(isCatalog).flush(TEST_CATALOG);
    http.expectOne(isFiltered).flush([CASTLE]);
    const page = await render();

    expect(page.querySelector('.notice--unknown')?.textContent).toContain(
      'De 1 lugar no tenemos el horario',
    );
  });

  it('sin resultados lo dice y ofrece preguntar; los filtros se limpian desde su barra', async () => {
    await open('/explorar?category=ruta');
    http.expectOne(isCatalog).flush(TEST_CATALOG);
    http.expectOne(isFiltered).flush([]);
    const page = await render();

    expect(page.textContent).toContain('No hay lugares con todos estos filtros');
    expect(page.querySelector('ul[aria-label="Resultados"]')).toBeNull();
    expect(page.querySelector('app-state-panel button')).toBeNull();
    expect(page.querySelector('app-state-panel a')?.getAttribute('href')).toBe('/asistente');
    expect(page.querySelector('.filters__summary button')?.textContent?.trim()).toBe(
      'Limpiar filtros',
    );
  });

  it('si la carga falla, lo dice y permite reintentar', async () => {
    await open('/explorar');
    http.expectOne(isCatalog).flush(null, { status: 500, statusText: 'Server Error' });
    let page = await render();

    expect(page.querySelector('[role="alert"]')?.textContent).toContain(
      'No hemos podido cargar los lugares',
    );

    (page.querySelector('app-state-panel button') as HTMLButtonElement).click();
    TestBed.tick();
    http.expectOne(isCatalog).flush(TEST_CATALOG);
    page = await render();

    expect(cardNames(page)).toHaveLength(TEST_CATALOG.length);
  });

  it('al cambiar de idioma traduce la interfaz y vuelve a pedir los lugares en ese idioma', async () => {
    await open('/explorar');
    http.expectOne(isCatalog).flush(TEST_CATALOG);
    await render();

    await TestBed.inject(LanguageService).use('en');
    TestBed.tick();

    const english = http.expectOne(isCatalog);
    expect(english.request.params.get('idioma')).toBe('en');
    // Mientras llega la respuesta en inglés, la lista sigue a la vista: nada de pantalla vacía.
    harness.fixture.detectChanges();
    const waiting = harness.routeNativeElement as HTMLElement;
    expect(cardNames(waiting)).toHaveLength(TEST_CATALOG.length);
    expect(waiting.querySelector('.skeleton-card')).toBeNull();

    english.flush(TEST_CATALOG);
    const page = await render();

    expect(page.querySelector('h1')?.textContent?.trim()).toBe('Explore Valdelumbre');
    expect(page.querySelector('label[for="filtro-dia"]')?.textContent?.trim()).toBe('Open');
    expect(page.querySelector('#filtro-dia option[value="1"]')?.textContent?.trim()).toBe(
      'On Monday',
    );
    expect(page.querySelector('.filters__count')?.textContent?.trim()).toBe(
      `${TEST_CATALOG.length} places`,
    );
  });

  it('al pulsar una chincheta resalta su tarjeta y abre su resumen', async () => {
    await open('/explorar');
    http.expectOne(isCatalog).flush(TEST_CATALOG);
    let page = await render();

    (page.querySelector('[data-poi-id="poi-003"]') as HTMLButtonElement).click();
    page = await render();

    expect(page.querySelector('#resultado-poi-003 article')?.classList).toContain('is-selected');
    expect(page.querySelector('.popover h3')?.textContent?.trim()).toBe('Museo del Aceite');
  });
});
