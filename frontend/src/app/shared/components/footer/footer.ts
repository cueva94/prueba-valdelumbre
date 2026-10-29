import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';

import { CATEGORIES } from '../../../core/constants/categories';
import { TOURIST_OFFICE_ID } from '../../../core/constants/places';

@Component({
  selector: 'app-footer',
  imports: [RouterLink, TranslatePipe],
  templateUrl: './footer.html',
  styleUrl: './footer.css',
})
export class Footer {
  protected readonly categories = CATEGORIES;
  protected readonly touristOffice = ['/lugares', TOURIST_OFFICE_ID];
}
