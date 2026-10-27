import { HttpRequest, provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';

import { CASTLE, TEST_CATALOG } from '../../../testing/pois';
import { provideTestTranslations } from '../../../testing/translations';
import { routes } from '../../app.routes';
import { LanguageService } from '../services/language.service';
import { PlacesStore } from './places.store';

const isCatalog = (language: string) => (request: HttpRequest<unknown>) =>
  request.url === '/api/pois' &&
  request.params.keys().join() === 'idioma' &&
  request.params.get('idioma') === language;

describe('PlacesStore', () => {
  let http: HttpTestingController;

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

  /** Deja que el recurso procese la respuesta (o lance la siguiente petición). */
  async function settle(): Promise<void> {
    await new Promise((resolve) => setTimeout(resolve));
    TestBed.tick();
  }

  it('pide el catálogo una vez y calcula el total y los lugares por categoría', async () => {
    const store = TestBed.inject(PlacesStore);
    TestBed.tick();

    expect(store.count()).toBeNull();
    expect(store.countByCategory()).toBeNull();
    expect(store.catalog.isLoading()).toBe(true);

    http.expectOne(isCatalog('es')).flush(TEST_CATALOG);
    await settle();

    expect(store.pois()).toEqual(TEST_CATALOG);
    expect(store.count()).toBe(TEST_CATALOG.length);
    expect(store.countByCategory()?.get('monumento')).toBe(
      TEST_CATALOG.filter((poi) => poi.categoria === 'monumento').length,
    );
    expect(store.countByCategory()?.get('servicio')).toBeUndefined();
  });

  it('al pasar de Inicio a Explorar y a una ficha no vuelve a pedir el catálogo', async () => {
    const harness = await RouterTestingHarness.create();
    await harness.navigateByUrl('/');
    TestBed.tick();
    http.expectOne(isCatalog('es')).flush(TEST_CATALOG);

    await harness.navigateByUrl('/explorar');
    TestBed.tick();
    await harness.navigateByUrl(`/lugares/${CASTLE.id}`);
    TestBed.tick();
    http.expectOne(`/api/pois/${CASTLE.id}?idioma=es`).flush(CASTLE);
    await new Promise((resolve) => setTimeout(resolve));
    TestBed.tick();
    // La ficha solo pide «abierto ahora» para su categoría; el catálogo ya estaba.
    http
      .match((request) => request.params.get('abierto_en') === 'ahora')
      .forEach((r) => r.flush([]));

    http.expectNone(isCatalog('es'));
  });

  it('al cambiar de idioma vuelve a pedir el catálogo en ese idioma', async () => {
    const store = TestBed.inject(PlacesStore);
    TestBed.tick();
    http.expectOne(isCatalog('es')).flush(TEST_CATALOG);

    await TestBed.inject(LanguageService).use('en');
    TestBed.tick();

    http.expectOne(isCatalog('en')).flush(TEST_CATALOG);
    await settle();
    expect(store.count()).toBe(TEST_CATALOG.length);
  });

  it('tras un error, reload() lo vuelve a pedir', async () => {
    const store = TestBed.inject(PlacesStore);
    TestBed.tick();
    http.expectOne(isCatalog('es')).flush(null, { status: 503, statusText: 'Service Unavailable' });
    await settle();

    expect(store.catalog.error()).toBeTruthy();
    expect(store.pois()).toEqual([]);
    expect(store.count()).toBeNull();

    store.reload();
    TestBed.tick();
    http.expectOne(isCatalog('es')).flush(TEST_CATALOG);
    await settle();

    expect(store.catalog.error()).toBeUndefined();
    expect(store.count()).toBe(TEST_CATALOG.length);
  });
});
