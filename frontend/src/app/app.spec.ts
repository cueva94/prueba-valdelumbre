import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { App } from './app';

describe('App (esqueleto)', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [App],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  async function renderizarConRespuesta(
    responder: (peticion: ReturnType<typeof http.expectOne>) => void,
  ) {
    const fixture = TestBed.createComponent(App);
    responder(http.expectOne('/api/health'));
    await fixture.whenStable();
    return (fixture.nativeElement as HTMLElement).querySelector('[role="status"]')?.textContent;
  }

  it('muestra la API como disponible cuando /api/health responde ok', async () => {
    const estado = await renderizarConRespuesta((peticion) => peticion.flush({ estado: 'ok' }));

    expect(estado).toContain('Estado de la API: disponible');
  });

  it('muestra la API como no disponible si la llamada falla', async () => {
    const estado = await renderizarConRespuesta((peticion) =>
      peticion.flush(null, { status: 503, statusText: 'Service Unavailable' }),
    );

    expect(estado).toContain('Estado de la API: no disponible');
  });
});
