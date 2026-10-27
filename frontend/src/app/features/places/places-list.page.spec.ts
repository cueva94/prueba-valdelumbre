import { HttpRequest, provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';

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

  it('sin resultados lo dice y ofrece limpiar los filtros', async () => {
    await open('/explorar?category=ruta');
    http.expectOne(isCatalog).flush(TEST_CATALOG);
    http.expectOne(isFiltered).flush([]);
    const page = await render();

    expect(page.textContent).toContain('No hay lugares con todos estos filtros');
    expect(page.querySelector('ul[aria-label="Resultados"]')).toBeNull();
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

    await TestBed.inject(LanguageService).use('en');
    TestBed.tick();

    const english = http.expectOne(isCatalog);
    expect(english.request.params.get('idioma')).toBe('en');
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
