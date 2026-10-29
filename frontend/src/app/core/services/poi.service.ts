import { httpResource } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';

import { Poi, PoiFilters } from '../models/poi.model';
import { keepValueAcrossLanguages, ReloadableResource } from '../utils/resource';
import { LanguageService } from './language.service';

export const API_URL = '/api';

/**
 * Lugares del catálogo. Los recursos se vuelven a pedir solos cuando cambian sus parámetros o el
 * idioma; al cambiar solo el idioma, mantienen lo que mostraban hasta que llega la respuesta.
 * Deben crearse en un contexto de inyección (por ejemplo, al inicializar un componente).
 */
@Injectable({ providedIn: 'root' })
export class PoiService {
  private readonly language = inject(LanguageService).current;

  /** GET /api/pois: los filtros los aplica el backend. Con `undefined` no se hace la petición. */
  list(filters: () => PoiFilters | undefined = () => ({})): ReloadableResource<Poi[] | undefined> {
    const resource = httpResource<Poi[]>(() => {
      const current = filters();
      if (!current) {
        return undefined;
      }
      return {
        url: `${API_URL}/pois`,
        params: { ...toQueryParams(current), idioma: this.language() },
      };
    });
    return keepValueAcrossLanguages(resource, filters);
  }

  /** GET /api/pois/{id}: 404 si el lugar no existe o se excluyó del catálogo. */
  get(id: () => string): ReloadableResource<Poi | undefined> {
    const resource = httpResource<Poi>(() => ({
      url: `${API_URL}/pois/${encodeURIComponent(id())}`,
      params: { idioma: this.language() },
    }));
    return keepValueAcrossLanguages(resource, id);
  }
}

function toQueryParams(filters: PoiFilters): Record<string, string> {
  const params: Record<string, string> = {};
  if (filters.categoria) {
    params['categoria'] = filters.categoria;
  }
  if (filters.accesible !== undefined) {
    params['accesible'] = String(filters.accesible);
  }
  if (filters.abiertoEn) {
    params['abierto_en'] = filters.abiertoEn;
  }
  return params;
}
