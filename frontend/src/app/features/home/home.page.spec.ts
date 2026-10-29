import { HttpRequest, provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';

import { CASTLE, OIL_MUSEUM, TEST_CATALOG } from '../../../testing/pois';
import { provideTestTranslations } from '../../../testing/translations';
import { routes } from '../../app.routes';
import { Poi } from '../../core/models/poi.model';
import { HomePage } from './home.page';

const isCatalog = (request: HttpRequest<unknown>) => request.url === '/api/pois';

/** Copias numeradas de una ficha, para tener más lugares de los que caben en una tanda. */
const copiesOf = (poi: Poi, count: number): Poi[] =>
  Array.from({ length: count }, (_, index) => ({
    ...poi,
    id: `${poi.id}-${index + 1}`,
    nombre: { ...poi.nombre, texto: `${poi.nombre.texto} ${index + 1}` },
  }));
const LARGE_CATALOG = [...copiesOf(CASTLE, 7), ...copiesOf(OIL_MUSEUM, 1)];

describe('HomePage (Inicio)', () => {
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

  // También comprueba que filtrar con los chips no hace otra petición.
  afterEach(() => http.verify());

  async function open(): Promise<void> {
    harness = await RouterTestingHarness.create();
    await harness.navigateByUrl('/', HomePage);
    TestBed.tick();
  }

  async function render(): Promise<HTMLElement> {
    await harness.fixture.whenStable();
    harness.fixture.detectChanges();
    return harness.routeNativeElement?.querySelector('.section--map') as HTMLElement;
  }

  const text = (element: Element | null | undefined) =>
    element?.textContent?.replace(/\s+/g, ' ').trim();
  const cardNames = (section: HTMLElement) =>
    [...section.querySelectorAll('app-poi-card h4')].map(text);
  const chip = (section: HTMLElement, label: string) =>
    [...section.querySelectorAll<HTMLButtonElement>('fieldset button')].find((button) =>
      button.textContent?.includes(label),
    );

  it('muestra todos los lugares en el mapa y en la lista, con cuántos hay de cada categoría', async () => {
    await open();
    http.expectOne(isCatalog).flush(TEST_CATALOG);
    const section = await render();

    expect(cardNames(section)).toHaveLength(TEST_CATALOG.length);
    expect(section.querySelectorAll('.pin')).toHaveLength(TEST_CATALOG.length);
    expect(text(section.querySelector('#places-title'))).toBe('Los 4 lugares');
    expect(text(chip(section, 'Todos'))).toBe('Todos 4');
    expect(text(chip(section, 'Monumentos'))).toBe('Monumentos 2');
    expect(section.querySelector('.places__more')).toBeNull();
  });

  it('con más de 6 lugares enseña los 6 primeros; «Cargar más» muestra el resto y desaparece', async () => {
    await open();
    http.expectOne(isCatalog).flush(LARGE_CATALOG);
    let section = await render();

    expect(cardNames(section)).toHaveLength(6);
    expect(section.querySelectorAll('.pin')).toHaveLength(LARGE_CATALOG.length);

    section.querySelector<HTMLButtonElement>('.places__more button')?.click();
    section = await render();

    expect(cardNames(section)).toHaveLength(LARGE_CATALOG.length);
    expect(section.querySelector('.places__more')).toBeNull();
    expect(document.activeElement).toBe(section.querySelectorAll('.places > li')[6]);
  });

  it('al cambiar de categoría, la lista vuelve a la primera tanda', async () => {
    await open();
    http.expectOne(isCatalog).flush(LARGE_CATALOG);
    let section = await render();

    section.querySelector<HTMLButtonElement>('.places__more button')?.click();
    section = await render();
    chip(section, 'Monumentos')?.click();
    section = await render();

    expect(cardNames(section)).toHaveLength(6);
    expect(section.querySelector('.places__more button')).not.toBeNull();

    chip(section, 'Museos')?.click();
    section = await render();

    expect(cardNames(section)).toEqual(['Museo del Aceite 1']);
    expect(section.querySelector('.places__more')).toBeNull();
  });

  it('los chips filtran el mapa y la lista al momento, sin pedir nada más al backend', async () => {
    await open();
    http.expectOne(isCatalog).flush(TEST_CATALOG);
    let section = await render();

    chip(section, 'Museos')?.click();
    section = await render();

    expect(cardNames(section)).toEqual(['Museo del Aceite']);
    expect(section.querySelectorAll('.pin')).toHaveLength(1);
    expect(text(section.querySelector('#places-title'))).toBe('1 lugar de Museos');
    expect(chip(section, 'Museos')?.getAttribute('aria-pressed')).toBe('true');
    const explore = [...section.querySelectorAll('a')].find((link) =>
      link.textContent?.includes('Filtrar por accesibilidad y horario'),
    );
    expect(explore?.getAttribute('href')).toBe('/explorar?category=museo');
  });

  it('«Ver en el mapa» selecciona la chincheta del lugar y abre su resumen', async () => {
    await open();
    http.expectOne(isCatalog).flush(TEST_CATALOG);
    let section = await render();

    const card = [...section.querySelectorAll('app-poi-card')].find((element) =>
      element.textContent?.includes('Museo del Aceite'),
    );
    card?.querySelector('button')?.click();
    section = await render();

    expect(text(section.querySelector('.popover h3'))).toBe('Museo del Aceite');
    expect(card?.querySelector('article')?.classList).toContain('is-selected');
  });

  it('si el catálogo no carga, lo dice y permite reintentar; la pregunta sigue disponible', async () => {
    await open();
    http.expectOne(isCatalog).flush(null, { status: 500, statusText: 'Server Error' });
    let section = await render();

    expect(text(section.querySelector('[role="alert"]'))).toContain(
      'No hemos podido cargar los lugares',
    );
    expect(harness.routeNativeElement?.querySelector('app-ask-box input')).not.toBeNull();

    section.querySelector<HTMLButtonElement>('app-state-panel button')?.click();
    TestBed.tick();
    http.expectOne(isCatalog).flush(TEST_CATALOG);
    section = await render();

    expect(cardNames(section)).toHaveLength(TEST_CATALOG.length);
  });
});
