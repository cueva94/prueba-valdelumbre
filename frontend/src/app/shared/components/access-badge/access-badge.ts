import { Component, computed, input } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';

/** Accesibilidad según la ficha: sí, no o sin datos (borde discontinuo, nunca «no»). */
@Component({
  selector: 'app-access-badge',
  imports: [TranslatePipe],
  templateUrl: './access-badge.html',
  styleUrl: './access-badge.css',
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
