import { Component, inject } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';

import { LANGUAGES } from '../../../core/models/poi.model';
import { LanguageService } from '../../../core/services/language.service';

@Component({
  selector: 'app-header',
  imports: [RouterLink, RouterLinkActive, TranslatePipe],
  templateUrl: './header.html',
  styleUrl: './header.css',
})
export class Header {
  protected readonly language = inject(LanguageService);
  protected readonly languages = LANGUAGES;
}
