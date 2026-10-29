import {
  Component,
  computed,
  ElementRef,
  inject,
  input,
  model,
  output,
  signal,
  viewChild,
} from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';

import { Topic } from '../../../core/constants/example-questions';
import { MAX_QUESTION_LENGTH } from '../../../core/models/assistant.model';
import { LanguageService } from '../../../core/services/language.service';

let nextId = 0;

@Component({
  selector: 'app-ask-box',
  imports: [TranslatePipe],
  templateUrl: './ask-box.html',
  styleUrl: './ask-box.css',
})
export class AskBox {
  readonly label = input.required<string>();
  readonly showLabel = input(true);
  readonly placeholder = input('');
  readonly topics = input<readonly Topic[]>([]);
  readonly compact = input(false);
  readonly value = model('');
  /** Pregunta sin espacios sobrantes; nunca vacía. */
  readonly submitted = output<string>();

  protected readonly id = `ask-${nextId++}`;
  protected readonly maxLength = MAX_QUESTION_LENGTH;
  protected readonly showError = signal(false);
  protected readonly errorKey = computed(() =>
    this.topics().length ? 'askBox.requiredOrTopic' : 'askBox.required',
  );

  private readonly language = inject(LanguageService);

  private readonly field = viewChild.required<ElementRef<HTMLInputElement>>('field');

  protected onInput(event: Event): void {
    this.value.set((event.target as HTMLInputElement).value);
    if (this.value().trim()) {
      this.showError.set(false);
    }
  }

  protected submit(event: Event): void {
    event.preventDefault();
    const question = this.value().trim();
    if (!question) {
      this.showError.set(true);
      this.field().nativeElement.focus();
      return;
    }
    this.submitted.emit(question);
  }

  protected pickTopic(topic: Topic): void {
    this.value.set(this.language.t(topic.questionKey));
    this.showError.set(false);
    this.field().nativeElement.focus();
  }
}
