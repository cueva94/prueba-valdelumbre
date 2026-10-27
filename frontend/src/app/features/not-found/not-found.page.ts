import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';

import { StatePanel } from '../../shared/components/state-panel/state-panel';

@Component({
  selector: 'app-not-found-page',
  imports: [RouterLink, TranslatePipe, StatePanel],
  template: `
    <div class="page">
      <h1 class="visually-hidden">{{ 'notFound.heading' | translate }}</h1>
      <app-state-panel
        [eyebrow]="'common.error404' | translate"
        [heading]="'notFound.title' | translate"
        [message]="'notFound.message' | translate"
      >
        <a class="vl-btn vl-btn--primary" routerLink="/explorar">{{
          'common.seeAllPlaces' | translate
        }}</a>
        <a class="vl-btn vl-btn--outline" routerLink="/">{{ 'notFound.goHome' | translate }}</a>
      </app-state-panel>
    </div>
  `,
})
export class NotFoundPage {}
