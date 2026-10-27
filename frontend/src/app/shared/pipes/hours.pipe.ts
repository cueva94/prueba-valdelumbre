import { inject, Pipe, PipeTransform } from '@angular/core';

import { OpeningHours } from '../../core/models/poi.model';
import { LanguageService } from '../../core/services/language.service';
import { hoursSummary } from '../../core/utils/opening-hours';

/** Impuro: se vuelve a evaluar al cambiar el idioma, aunque el horario sea el mismo. */
@Pipe({ name: 'hoursSummary', pure: false })
export class HoursSummaryPipe implements PipeTransform {
  private readonly language = inject(LanguageService);

  transform(hours: OpeningHours): string {
    return hoursSummary(hours, this.language);
  }
}
