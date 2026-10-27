import { httpResource, HttpResourceRef } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';

import { AskRequest, AskResponse } from '../models/assistant.model';
import { LanguageService } from './language.service';
import { API_URL } from './poi.service';

@Injectable({ providedIn: 'root' })
export class AssistantService {
  private readonly language = inject(LanguageService).current;

  /**
   * POST /api/preguntar con la pregunta actual; sin pregunta no se hace ninguna petición.
   * Es una consulta sin efectos, así que se repite si cambia la pregunta o el idioma.
   */
  ask(question: () => string | undefined): HttpResourceRef<AskResponse | undefined> {
    return httpResource<AskResponse>(() => {
      const pregunta = question()?.trim();
      if (!pregunta) {
        return undefined;
      }
      const body: AskRequest = { pregunta, idioma: this.language() };
      return { url: `${API_URL}/preguntar`, method: 'POST', body };
    });
  }
}
