import { Category } from '../models/poi.model';

export interface CategoryInfo {
  id: Category;
  labelKey: string;
  pluralKey: string;
  /** Trazo SVG de 24 × 24 para el icono decorativo. */
  icon: string;
}

/** Las 7 categorías del catálogo, en el orden en que se muestran. */
export const CATEGORIES: readonly CategoryInfo[] = [
  {
    id: 'monumento',
    labelKey: 'categories.monumento.label',
    pluralKey: 'categories.monumento.plural',
    icon: 'M4 21V9h3V5h3v4h4V5h3v4h3v12M3 21h18M10 21v-5h4v5',
  },
  {
    id: 'museo',
    labelKey: 'categories.museo.label',
    pluralKey: 'categories.museo.plural',
    icon: 'M3 10h18M5 10v8M9.5 10v8M14.5 10v8M19 10v8M3 20h18M12 3l9 5H3z',
  },
  {
    id: 'naturaleza',
    labelKey: 'categories.naturaleza.label',
    pluralKey: 'categories.naturaleza.plural',
    icon: 'M2 20l7-12 4 6 3-4 6 10z',
  },
  {
    id: 'ruta',
    labelKey: 'categories.ruta.label',
    pluralKey: 'categories.ruta.plural',
    icon: 'M4 18a2 2 0 1 0 4 0a2 2 0 1 0-4 0M16 6a2 2 0 1 0 4 0a2 2 0 1 0-4 0M8 18h7a3 3 0 0 0 0-6H9a3 3 0 0 1 0-6h7',
  },
  {
    id: 'espacio_publico',
    labelKey: 'categories.espacio_publico.label',
    pluralKey: 'categories.espacio_publico.plural',
    icon: 'M3 20h18M5 20v-6M19 20v-6M3 14h18M8 14v-3a4 4 0 0 1 8 0v3',
  },
  {
    id: 'gastronomia',
    labelKey: 'categories.gastronomia.label',
    pluralKey: 'categories.gastronomia.plural',
    icon: 'M8 3h8l-.4 6a3.6 3.6 0 0 1-7.2 0zM12 13v7M8 21h8',
  },
  {
    id: 'servicio',
    labelKey: 'categories.servicio.label',
    pluralKey: 'categories.servicio.plural',
    icon: 'M12 21a9 9 0 1 0 0-18a9 9 0 0 0 0 18zM12 11v6M12 7.5v.5',
  },
];

export function categoryInfo(id: Category | null): CategoryInfo | undefined {
  return CATEGORIES.find((category) => category.id === id);
}

export function categoryLabelKey(id: Category | null): string {
  return categoryInfo(id)?.labelKey ?? 'common.noCategory';
}

export function isCategory(value: string | undefined): value is Category {
  return CATEGORIES.some((category) => category.id === value);
}
