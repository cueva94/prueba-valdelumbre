import { Component, computed, input } from '@angular/core';

import { categoryInfo } from '../../../core/constants/categories';
import { Category } from '../../../core/models/poi.model';

/** Chincheta: para un lugar sin categoría conocida. */
const UNKNOWN_CATEGORY_ICON = 'M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21zM12 7v5';

/** Icono decorativo de una categoría: el nombre siempre va en texto al lado. */
@Component({
  selector: 'app-category-icon',
  templateUrl: './category-icon.html',
  styleUrl: './category-icon.css',
})
export class CategoryIcon {
  readonly category = input.required<Category | null>();
  readonly size = input(22);

  protected readonly path = computed(
    () => categoryInfo(this.category())?.icon ?? UNKNOWN_CATEGORY_ICON,
  );
}
