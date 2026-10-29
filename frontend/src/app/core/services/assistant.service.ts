import { httpResource } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';

import { AskRequest, AskResponse } from '../models/assistant.model';
import { keepValueAcrossLanguages, ReloadableResource } from '../utils/resource';
import { LanguageService } from './language.service';
import { API_URL } from './poi.service';

@Injectable({ providedIn: 'root' })
export class AssistantService {
  private readonly language = inject(LanguageService).current;

  /**
   * POST /api/preguntar con la pregunta actual; sin pregunta no se hace ninguna petición.
   * Es una consulta sin efectos, así que se repite si cambia la pregunta o el idioma; si solo cambia
   * el idioma, la respuesta anterior se mantiene hasta que llega la nueva.
   */
  ask(question: () => string | undefined): ReloadableResource<AskResponse | undefined> {
    const resource = httpResource<AskResponse>(() => {
      const pregunta = question()?.trim();
      if (!pregunta) {
        return undefined;
      }
      const body: AskRequest = { pregunta, idioma: this.language() };
      return { url: `${API_URL}/preguntar`, method: 'POST', body };
    });
    return keepValueAcrossLanguages(resource, () => question()?.trim());
  }
}
