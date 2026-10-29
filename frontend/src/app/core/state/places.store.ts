import { computed, inject, Injectable, Resource } from '@angular/core';

import { Category, Poi } from '../models/poi.model';
import { PoiService } from '../services/poi.service';

/**
 * El catálogo completo, compartido por Inicio, Explorar y la ficha (encuadre del mapa,
 * contadores y lista). Se pide una vez y solo se vuelve a pedir al cambiar de idioma o con
 * `reload()`. Los filtros no viven aquí: están en la URL de Explorar, que es quien los usa.
 */
@Injectable({ providedIn: 'root' })
export class PlacesStore {
  private readonly resource = inject(PoiService).list();

  readonly catalog: Resource<Poi[] | undefined> = this.resource;
  readonly pois = computed<readonly Poi[]>(() =>
    this.resource.hasValue() ? this.resource.value() : [],
  );
  readonly count = computed(() => (this.resource.hasValue() ? this.resource.value().length : null));
  readonly countByCategory = computed<ReadonlyMap<Category, number> | null>(() => {
    if (!this.resource.hasValue()) {
      return null;
    }
    const counts = new Map<Category, number>();
    for (const poi of this.resource.value()) {
      if (poi.categoria) {
        counts.set(poi.categoria, (counts.get(poi.categoria) ?? 0) + 1);
      }
    }
    return counts;
  });

  reload(): void {
    this.resource.reload();
  }
}
