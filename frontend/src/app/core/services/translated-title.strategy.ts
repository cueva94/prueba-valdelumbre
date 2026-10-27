import { effect, inject, Injectable, signal } from '@angular/core';
import { Title } from '@angular/platform-browser';
import { RouterStateSnapshot, TitleStrategy } from '@angular/router';

import { LanguageService } from './language.service';

/**
 * El `title` de cada ruta es una clave de traducción: el título de la pestaña se traduce y
 * cambia con el idioma. Una ruta sin `title` (la ficha) pone el suyo desde la página.
 */
@Injectable({ providedIn: 'root' })
export class TranslatedTitleStrategy extends TitleStrategy {
  private readonly title = inject(Title);
  private readonly language = inject(LanguageService);
  private readonly key = signal<string | undefined>(undefined);

  constructor() {
    super();
    effect(() => {
      const key = this.key();
      if (key) {
        this.title.setTitle(this.language.t(key));
      }
    });
  }

  override updateTitle(snapshot: RouterStateSnapshot): void {
    this.key.set(this.buildTitle(snapshot));
  }
}
