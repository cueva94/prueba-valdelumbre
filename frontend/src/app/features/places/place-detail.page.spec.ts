import { HttpRequest, provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
  TestRequest,
} from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Title } from '@angular/platform-browser';
import { NavigationEnd, provideRouter, Router, withComponentInputBinding } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { filter, firstValueFrom } from 'rxjs';

import { CASTLE, HERMITAGE, NATURAL_POOL, TEST_CATALOG } from '../../../testing/pois';
import { provideTestTranslations } from '../../../testing/translations';
import { routes } from '../../app.routes';
import { Poi } from '../../core/models/poi.model';
import { PlaceDetailPage } from './place-detail.page';

const placeRequest = (id: string) => (request: HttpRequest<unknown>) =>
  request.url === `/api/pois/${id}` && request.params.get('idioma') === 'es';
const isCatalog = (request: HttpRequest<unknown>) =>
  request.url === '/api/pois' && request.params.keys().join() === 'idioma';
const isOpenNow = (request: HttpRequest<unknown>) =>
  request.url === '/api/pois' && request.params.get('abierto_en') === 'ahora';

describe('PlaceDetailPage (Ficha)', () => {
  let http: HttpTestingController;
  let harness: RouterTestingHarness;
  let openNowRequest: TestRequest | undefined;

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
    openNowRequest = undefined;
  });

  afterEach(() => {
    http.verify();
    vi.useRealTimers();
  });

  /** Deja que la ficha procese su respuesta y lance las peticiones que dependen de ella. */
  async function settle(): Promise<void> {
    await new Promise((resolve) => setTimeout(resolve));
    TestBed.tick();
    await new Promise((resolve) => setTimeout(resolve));
  }

  /** Abre la ficha y responde: la ficha, el catálogo (mapa) y los lugares abiertos ahora. */
  async function show(
    id: string,
    respond: (request: TestRequest) => void,
    openNow: readonly Poi[] = [],
  ): Promise<HTMLElement> {
    harness = await RouterTestingHarness.create();
    await harness.navigateByUrl(`/lugares/${id}`, PlaceDetailPage);
    TestBed.tick();
    respond(http.expectOne(placeRequest(id)));
    await settle();
    http.match(isCatalog).forEach((request) => request.flush(TEST_CATALOG));
    [openNowRequest] = http.match(isOpenNow);
    openNowRequest?.flush(openNow);
    await harness.fixture.whenStable();
    harness.fixture.detectChanges();
    return harness.routeNativeElement as HTMLElement;
  }

  const text = (element: Element | null | undefined) =>
    element?.textContent?.replace(/\s+/g, ' ').trim();
  const fact = (page: HTMLElement, label: string) =>
    text(
      [...page.querySelectorAll('.fact')]
        .find((item) => text(item.querySelector('dt')) === label)
        ?.querySelector('dd'),
    );

  it('muestra los datos clave, las etiquetas, el horario semanal y dónde está', async () => {
    // Lunes 26/10/2026 a las 10:30 en Valdelumbre: solo se falsea la fecha, no los temporizadores.
    vi.useFakeTimers({ toFake: ['Date'] });
    vi.setSystemTime(new Date('2026-10-26T09:30:00Z'));
    const page = await show('poi-001', (request) => request.flush(CASTLE), [CASTLE]);

    expect(text(page.querySelector('h1'))).toBe('Castillo de Valdelumbre');
    expect(text(page.querySelector('.status'))).toBe('Abierto ahora');
    expect(openNowRequest?.request.params.get('categoria')).toBe('monumento');
    expect([...page.querySelectorAll('.tags li')].map(text)).toEqual(['Historia', 'Vistas']);
    expect(fact(page, 'Hoy')).toBe('10:00 – 14:00 y 17:00 – 20:00');
    expect(fact(page, 'Precio')).toBe('4,50 €');
    expect(fact(page, 'Accesibilidad')).toBe('No accesible');

    const rows = [...page.querySelectorAll('table.hours tr')].map(text);
    expect(rows).toHaveLength(7);
    expect(rows.find((row) => row?.startsWith('Domingo'))).toContain('Cerrado');
    expect(page.querySelector('#season-title')).toBeNull();

    const map = page.querySelector('app-poi-map') as HTMLElement;
    expect(map.querySelectorAll('.pin')).toHaveLength(1);
    expect(map.querySelector('button')).toBeNull();
    expect(text(map.querySelector('.pin'))).toBe('Castillo de Valdelumbre, Monumento');

    expect(
      page.querySelectorAll('ul[aria-label="Preguntas rápidas sobre este lugar"] a'),
    ).toHaveLength(3);
    expect(TestBed.inject(Title).getTitle()).toBe('Castillo de Valdelumbre · Valdelumbre');
  });

  it('si el backend no lo da por abierto ahora, dice «Cerrado ahora»', async () => {
    const page = await show('poi-001', (request) => request.flush(CASTLE), []);

    expect(text(page.querySelector('.status'))).toBe('Cerrado ahora');
  });

  it('con el horario incompleto, no estar abierto ahora no lo da por cerrado', async () => {
    // Lunes 26/10/2026 a las 10:30 en Valdelumbre.
    vi.useFakeTimers({ toFake: ['Date'] });
    vi.setSystemTime(new Date('2026-10-26T09:30:00Z'));
    const weekendsOnly: Poi = {
      ...CASTLE,
      horario: {
        siempre_abierto: false,
        // En el original había alguna franja más que no se pudo interpretar.
        incompleto: true,
        franjas: [{ dias: [6, 7], abre: '10:00', cierra: '14:00', temporada: null }],
      },
    };
    const page = await show('poi-001', (request) => request.flush(weekendsOnly), []);

    expect(text(page.querySelector('.status'))).toBe('Horario por confirmar');
    expect(fact(page, 'Hoy')).toBe('Sin datos');
    const rows = [...page.querySelectorAll('table.hours tr')].map(text);
    expect(rows.find((row) => row?.startsWith('Martes'))).toBe('Martes Sin datos');
    expect(rows.find((row) => row?.startsWith('Sábado'))).toBe('Sábado 10:00 – 14:00');
  });

  it('un horario no publicado no se presenta como cerrado', async () => {
    const page = await show('poi-018', (request) => request.flush(HERMITAGE));

    expect(openNowRequest).toBeUndefined();
    expect(page.querySelector('.status')).toBeNull();
    expect(fact(page, 'Hoy')).toBe('Horario no publicado');
    expect(text(page.querySelector('.hours-state__title'))).toBe('Horario no publicado');
    expect(page.textContent).toContain('Este lugar no publica su horario');
    expect(page.querySelector('table.hours')).toBeNull();
    expect(page.querySelector('.hours-state a')?.getAttribute('href')).toBe('/lugares/poi-010');
  });

  it('un lugar abierto siempre lo dice en lugar de mostrar una tabla de horario', async () => {
    const viewpoint: Poi = {
      ...HERMITAGE,
      id: 'poi-005',
      horario: { siempre_abierto: true, franjas: [], incompleto: false },
    };
    const page = await show('poi-005', (request) => request.flush(viewpoint), [viewpoint]);

    expect(text(page.querySelector('.status'))).toBe('Abierto ahora');
    expect(fact(page, 'Hoy')).toBe('Abierto siempre');
    expect(text(page.querySelector('.hours-state--open .hours-state__title'))).toBe(
      'Abierto siempre',
    );
    expect(page.querySelector('table.hours')).toBeNull();
  });

  it('muestra la temporada en texto y en los meses del año', async () => {
    const page = await show('poi-014', (request) => request.flush(NATURAL_POOL));

    expect(fact(page, 'Hoy')).toBe('11:00 – 20:00 Solo en temporada');
    expect(page.textContent).toContain('Del 1 de junio al 30 de septiembre');
    expect(page.querySelector('table.hours')?.textContent).not.toContain('temporada');
    expect(page.textContent).toContain(
      'Este horario solo es válido del 1 de junio al 30 de septiembre.',
    );
    const inSeason = [...page.querySelectorAll('ol.months li')].filter((month) =>
      month.getAttribute('aria-label')?.endsWith(': en temporada'),
    );
    expect(inSeason.map((month) => month.getAttribute('aria-label'))).toEqual([
      'junio: en temporada',
      'julio: en temporada',
      'agosto: en temporada',
      'septiembre: en temporada',
    ]);
  });

  it('un lugar que no está en el catálogo muestra el estado 404', async () => {
    const page = await show('poi-999', (request) =>
      request.flush(
        { detail: 'No hay ningún punto de interés' },
        { status: 404, statusText: 'Not Found' },
      ),
    );

    expect(page.textContent).toContain('No encontramos este lugar');
    expect(page.querySelector('[role="alert"]')).toBeNull();
    expect(page.querySelector('h1')?.textContent?.trim()).toBe('Lugar no encontrado');
    expect(TestBed.inject(Title).getTitle()).toBe('Lugar no encontrado · Valdelumbre');
  });

  it('una pregunta sobre el lugar lo nombra para que el asistente sepa de cuál se trata', async () => {
    const page = await show('poi-001', (request) => request.flush(CASTLE));
    const navigated = firstValueFrom(
      TestBed.inject(Router).events.pipe(filter((event) => event instanceof NavigationEnd)),
    );

    const field = page.querySelector('.ask-here input') as HTMLInputElement;
    field.value = '¿Es accesible?';
    field.dispatchEvent(new Event('input'));
    (page.querySelector('.ask-here button[type="submit"]') as HTMLButtonElement).click();
    await navigated;
    TestBed.tick();

    expect(decodeURIComponent(TestBed.inject(Router).url)).toBe(
      '/asistente?q=¿Es accesible? (Castillo de Valdelumbre)',
    );
    http.expectOne('/api/preguntar');
  });
});
