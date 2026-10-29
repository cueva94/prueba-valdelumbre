import { Component, ElementRef, inject, viewChild } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { NavigationEnd, Router, RouterOutlet } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { filter, map } from 'rxjs';

import { Footer } from './shared/components/footer/footer';
import { Header } from './shared/components/header/header';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, TranslatePipe, Header, Footer],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  private readonly main = viewChild.required<ElementRef<HTMLElement>>('main');

  constructor() {
    // Al cambiar de página, el foco pasa al contenido para que el lector de pantalla no se quede
    // en el enlace pulsado. Solo si cambia la ruta.
    let previousPath: string | null = null;
    inject(Router)
      .events.pipe(
        filter((event) => event instanceof NavigationEnd),
        map((event) => event.urlAfterRedirects.split(/[?#]/)[0]),
        takeUntilDestroyed(),
      )
      .subscribe((path) => {
        if (previousPath !== null && path !== previousPath) {
          this.main().nativeElement.focus({ preventScroll: true });
        }
        previousPath = path;
      });
  }

  protected skipToContent(): void {
    this.main().nativeElement.focus();
  }
}
