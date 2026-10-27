import { Component, computed, input } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';

/** Accesibilidad según la ficha: sí, no o sin datos (borde discontinuo, nunca «no»). */
@Component({
  selector: 'app-access-badge',
  imports: [TranslatePipe],
  template: `<span [class]="classes()">{{ label() | translate }}</span>`,
  styles: `
    .badge {
      display: inline-flex;
      align-items: center;
      padding: 3px 9px;
      border-radius: var(--vl-radius-chip);
      border: 1px solid transparent;
      font-size: 12px;
      font-weight: 600;
      white-space: nowrap;
    }
    .badge--ok {
      background: var(--vl-ok-bg);
      color: var(--vl-ok-fg);
    }
    .badge--no {
      background: #eef1f4;
      color: var(--vl-ink-2);
    }
    .badge--unknown {
      background: var(--vl-surface);
      color: var(--vl-ink-3);
      border: 1px dashed var(--vl-unknown);
    }
    .badge--large {
      padding: 5px 12px;
      font-size: 14px;
    }
  `,
})
export class AccessBadge {
  readonly accessible = input.required<boolean | null>();
  readonly large = input(false);

  protected readonly tone = computed(() => {
    const accessible = this.accessible();
    if (accessible === null) {
      return 'unknown';
    }
    return accessible ? 'ok' : 'no';
  });

  protected readonly classes = computed(
    () => `badge badge--${this.tone()}${this.large() ? ' badge--large' : ''}`,
  );

  protected readonly label = computed(() => {
    const accessible = this.accessible();
    if (accessible === null) {
      return 'accessibility.unknown';
    }
    return accessible ? 'accessibility.accessible' : 'accessibility.notAccessible';
  });
}
