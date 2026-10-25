import { HttpClient } from '@angular/common/http';
import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { catchError, map, of } from 'rxjs';

type EstadoApi = 'comprobando' | 'disponible' | 'no disponible';

@Component({
  selector: 'app-root',
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  private readonly http = inject(HttpClient);

  /** Esqueleto: comprueba que la pantalla llega a la API a través del proxy /api. */
  protected readonly estadoApi = toSignal(
    this.http.get<{ estado: string }>('/api/health').pipe(
      map((respuesta): EstadoApi => (respuesta.estado === 'ok' ? 'disponible' : 'no disponible')),
      catchError(() => of<EstadoApi>('no disponible')),
    ),
    { initialValue: 'comprobando' as EstadoApi },
  );
}
