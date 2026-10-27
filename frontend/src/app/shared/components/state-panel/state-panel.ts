import { Component, input } from '@angular/core';

let nextId = 0;

/**
 * Estado vacío o de error (sin resultados, ficha no encontrada, error de carga) con sus
 * acciones proyectadas. Un error se anuncia a los lectores de pantalla.
 */
@Component({
  selector: 'app-state-panel',
  template: `
    <section
      class="state"
      [class.state--error]="tone() === 'error'"
      [attr.role]="tone() === 'error' ? 'alert' : null"
      [attr.aria-labelledby]="id"
    >
      @if (eyebrow()) {
        <p class="state__eyebrow">{{ eyebrow() }}</p>
      }
      <h2 class="state__title" [id]="id">{{ heading() }}</h2>
      @if (message()) {
        <p class="state__message">{{ message() }}</p>
      }
      <div class="state__actions"><ng-content /></div>
    </section>
  `,
  styles: `
    .state {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      gap: 12px;
      padding: 40px;
      background: var(--vl-surface);
      border: 1px solid var(--vl-line);
      border-radius: var(--vl-radius-panel);
    }
    .state--error {
      border-color: var(--vl-err-line);
    }
    .state__eyebrow {
      margin: 0;
      font-size: 13px;
      font-weight: 700;
      color: var(--vl-ink-3);
    }
    .state__title {
      margin: 0;
      font-size: 19px;
      font-weight: 700;
    }
    .state--error .state__title {
      color: var(--vl-err-fg);
    }
    .state__message {
      margin: 0;
      max-width: 620px;
      font-size: 15px;
      line-height: 1.55;
      color: var(--vl-ink-2);
    }
    .state__actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 4px;
    }
    .state__actions:empty {
      display: none;
    }
    @media (max-width: 520px) {
      .state {
        padding: 24px;
      }
    }
  `,
})
export class StatePanel {
  readonly heading = input.required<string>();
  readonly message = input('');
  readonly eyebrow = input('');
  readonly tone = input<'neutral' | 'error'>('neutral');

  protected readonly id = `state-${nextId++}`;
}
