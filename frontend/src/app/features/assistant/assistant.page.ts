import { Component, computed, inject, input, linkedSignal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';

import { STARTER_QUESTIONS, TOPICS } from '../../core/constants/example-questions';
import { AssistantService } from '../../core/services/assistant.service';
import { LanguageService } from '../../core/services/language.service';
import { humanizeAnswer } from '../../core/utils/answer-text';
import { AskBox } from '../../shared/components/ask-box/ask-box';
import { PoiCard } from '../../shared/components/poi-card/poi-card';

/** Bloque de la respuesta: un párrafo o una lista (las líneas que empiezan por «- »). */
export type AnswerBlock = { kind: 'paragraph'; text: string } | { kind: 'list'; items: string[] };

const LIST_ITEM = '- ';

/**
 * Asistente: la pregunta vive en la URL (`?q=`) para poder enlazarla desde el inicio o una ficha.
 * Muestra el texto de POST /api/preguntar, con sus frases fijas redactadas de forma más cercana
 * (`humanizeAnswer`), y las fichas de los lugares citados.
 */
@Component({
  selector: 'app-assistant-page',
  imports: [RouterLink, TranslatePipe, AskBox, PoiCard],
  templateUrl: './assistant.page.html',
  styleUrl: './assistant.page.css',
})
export class AssistantPage {
  /** Parámetro `?q=` de la URL. */
  readonly q = input<string>();

  private readonly router = inject(Router);
  private readonly language = inject(LanguageService);

  protected readonly question = computed(() => this.q()?.trim() ?? '');
  /** Texto de la caja: empieza con la pregunta actual y el usuario puede editarlo. */
  protected readonly draft = linkedSignal(() => this.question());
  protected readonly answer = inject(AssistantService).ask(this.question);
  protected readonly topics = TOPICS;
  protected readonly starters = STARTER_QUESTIONS;

  protected readonly blocks = computed<AnswerBlock[]>(() => {
    if (!this.answer.hasValue()) {
      return [];
    }
    const { respuesta, idioma } = this.answer.value();
    return answerBlocks(humanizeAnswer(respuesta, idioma, this.language.textsFor(idioma)));
  });
  /** Sin lugares citados, el catálogo no respalda ninguna recomendación. */
  protected readonly grounded = computed(
    () => this.answer.hasValue() && this.answer.value().ids.length > 0,
  );

  protected ask(question: string): void {
    if (question === this.question()) {
      this.answer.reload();
      return;
    }
    void this.router.navigate(['/asistente'], { queryParams: { q: question } });
  }

  /** Pregunta de ejemplo (clave de traducción), en el idioma activo. */
  protected askExample(key: string): void {
    this.ask(this.language.t(key));
  }
}

/** Separa el texto del backend en párrafos y listas, sin cambiar ni una palabra. */
export function answerBlocks(text: string): AnswerBlock[] {
  const blocks: AnswerBlock[] = [];
  for (const line of text.split('\n').filter((line) => line.trim())) {
    const last = blocks.at(-1);
    if (!line.startsWith(LIST_ITEM)) {
      blocks.push({ kind: 'paragraph', text: line });
    } else if (last?.kind === 'list') {
      last.items.push(line.slice(LIST_ITEM.length));
    } else {
      blocks.push({ kind: 'list', items: [line.slice(LIST_ITEM.length)] });
    }
  }
  return blocks;
}
