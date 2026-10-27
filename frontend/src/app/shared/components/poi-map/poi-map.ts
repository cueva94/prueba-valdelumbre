import { Component, computed, ElementRef, inject, input, output } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';

import { categoryLabelKey } from '../../../core/constants/categories';
import { Poi } from '../../../core/models/poi.model';
import { LanguageService } from '../../../core/services/language.service';
import {
  hasSeason,
  isHoursUnknown,
  seasonsOf,
  seasonText,
} from '../../../core/utils/opening-hours';
import { AccessBadge } from '../access-badge/access-badge';
import { HoursSummaryPipe } from '../../pipes/hours.pipe';
import { PricePipe } from '../../pipes/price.pipe';

/** Margen, en % del mapa, para que ninguna chincheta quede pegada al borde. */
const MAP_PADDING = 8;
/** Por debajo de esta posición (%), el popover se abre hacia arriba. */
const POPOVER_FLIP_Y = 48;
const POPOVER_EDGE_X = 16;

/**
 * Las formas del fondo se dibujan en milésimas de grado desde este punto (x hacia el este,
 * y hacia el sur), así que se proyectan igual que las chinchetas sea cual sea el encuadre.
 */
const GROUND_ORIGIN = { lat: 40.435, lon: -3.73 };
const GROUND_UNITS_PER_DEGREE = 1000;
/** El nombre del pueblo no se traduce; el del río, sí (`key`). */
const GROUND_LABELS: readonly GroundLabel[] = [
  { text: 'VALDELUMBRE', kind: 'town', x: 25.6, y: 23.2 },
  { key: 'map.river', kind: 'water', x: 15.2, y: 7 },
];
/** Carreteras desde el casco: al oeste por el Puente Romano, a la bodega, al sur y al Mirador. */
const GROUND_ROADS = [
  'M21.6,16.8 C20.6,15.6 19.8,14.8 19,14 C17,12.2 14.5,11.6 11,12.6 C7,13.8 2,14.6 -4,15.2',
  'M22.2,20.4 C19,22.6 15.6,24.4 12,25.6 C8,26.9 4,28.2 0.6,29.6',
  'M25.6,20.9 C25.8,24 26.4,28 27,34',
  'M29.4,17.6 C30.4,16.4 30.9,14.4 31,12',
].join(' ');

interface GroundLabel {
  text?: string;
  key?: string;
  kind: 'town' | 'water';
  x: number;
  y: number;
}

interface Pin {
  poi: Poi;
  x: number;
  y: number;
  label: string;
}

interface Bounds {
  minLat: number;
  maxLat: number;
  minLon: number;
  maxLon: number;
}

/** De unidades del fondo a % del mapa: x' = offsetX + x · scaleX (y lo mismo en vertical). */
interface GroundProjection {
  scaleX: number;
  scaleY: number;
  offsetX: number;
  offsetY: number;
}

/**
 * Mapa esquemático sin librerías: las chinchetas se colocan según las coordenadas del catálogo,
 * escaladas al recuadro. El encuadre sale de `frame` (todo el catálogo) para que las chinchetas
 * no se muevan al filtrar. Un lugar sin coordenadas no se dibuja.
 *
 * El fondo es orientativo, pero sale de las fichas: el río Lumbre pasa por la Piscina Natural
 * («poza en el río»), junto a la ruta y bajo el Puente Romano; el casco rodea la Plaza Mayor,
 * y la Ermita del Cerro queda en alto, con su camino de tierra desde el Mirador.
 */
@Component({
  selector: 'app-poi-map',
  imports: [RouterLink, TranslatePipe, AccessBadge, PricePipe, HoursSummaryPipe],
  templateUrl: './poi-map.html',
  styleUrl: './poi-map.css',
  // Escape cierra el popover desde la chincheta o desde dentro del popover.
  host: { '(keydown.escape)': 'close()' },
})
export class PoiMap {
  readonly pois = input.required<readonly Poi[]>();
  readonly frame = input.required<readonly Poi[]>();
  readonly selectedId = input<string | null>(null);
  /** false: solo sitúa los lugares, resaltados y sin popover (p. ej., en la ficha de un lugar). */
  readonly interactive = input(true);
  readonly selectedChange = output<string | null>();

  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef);
  private readonly language = inject(LanguageService);

  protected readonly roads = GROUND_ROADS;

  private readonly bounds = computed(() => boundsOf([...this.frame(), ...this.pois()]));

  protected readonly pins = computed<Pin[]>(() => {
    const bounds = this.bounds();
    return this.pois().flatMap((poi) => {
      const coordinates = poi.coordenadas;
      if (!coordinates || !bounds) {
        return [];
      }
      const category = this.language.t(categoryLabelKey(poi.categoria));
      return [
        {
          poi,
          x: scale(coordinates.lon, bounds.minLon, bounds.maxLon),
          // La latitud crece hacia arriba; en pantalla, «top» crece hacia abajo.
          y: 100 - scale(coordinates.lat, bounds.minLat, bounds.maxLat),
          label: this.language.t('map.pin', { name: poi.nombre.texto, category }),
        },
      ];
    });
  });

  protected readonly unplaced = computed(() => this.pois().filter((poi) => !poi.coordenadas));

  /** Sin un encuadre con extensión (p. ej., un solo lugar), el fondo es una cuadrícula neutra. */
  private readonly ground = computed<GroundProjection | null>(() => {
    const bounds = this.bounds();
    if (!bounds || bounds.maxLon === bounds.minLon || bounds.maxLat === bounds.minLat) {
      return null;
    }
    const lonScale = (100 - 2 * MAP_PADDING) / (bounds.maxLon - bounds.minLon);
    const latScale = (100 - 2 * MAP_PADDING) / (bounds.maxLat - bounds.minLat);
    return {
      scaleX: lonScale / GROUND_UNITS_PER_DEGREE,
      scaleY: latScale / GROUND_UNITS_PER_DEGREE,
      offsetX: MAP_PADDING + (GROUND_ORIGIN.lon - bounds.minLon) * lonScale,
      offsetY: 100 - MAP_PADDING - (GROUND_ORIGIN.lat - bounds.minLat) * latScale,
    };
  });

  protected readonly groundTransform = computed(() => {
    const ground = this.ground();
    return ground
      ? `matrix(${ground.scaleX} 0 0 ${ground.scaleY} ${ground.offsetX} ${ground.offsetY})`
      : null;
  });

  protected readonly groundLabels = computed(() => {
    const ground = this.ground();
    return ground
      ? GROUND_LABELS.map((label) => ({
          ...label,
          left: ground.offsetX + label.x * ground.scaleX,
          top: ground.offsetY + label.y * ground.scaleY,
        }))
      : [];
  });

  protected categoryLabel(poi: Poi): string {
    return categoryLabelKey(poi.categoria);
  }

  protected seasonNote(poi: Poi): string {
    if (!hasSeason(poi.horario)) {
      return '';
    }
    const seasons = seasonsOf(poi.horario).map((season) =>
      seasonText(season, this.language, 'inline'),
    );
    return this.language.t('map.seasonOnly', { seasons: seasons.join('; ') });
  }

  protected hoursUnknown(poi: Poi): boolean {
    return isHoursUnknown(poi.horario);
  }

  protected popoverLeft(pin: Pin): string {
    if (pin.x < POPOVER_EDGE_X) {
      return '16px';
    }
    if (pin.x > 100 - POPOVER_EDGE_X) {
      return 'calc(100% - min(300px, 100% - 32px) - 16px)';
    }
    return `clamp(16px, calc(${pin.x}% - 150px), calc(100% - min(300px, 100% - 32px) - 16px))`;
  }

  protected popoverTop(pin: Pin): string {
    return pin.y > POPOVER_FLIP_Y ? `calc(${pin.y}% - 28px)` : `calc(${pin.y}% + 28px)`;
  }

  protected opensUpward(pin: Pin): boolean {
    return pin.y > POPOVER_FLIP_Y;
  }

  protected toggle(id: string): void {
    this.selectedChange.emit(this.selectedId() === id ? null : id);
  }

  protected close(): void {
    const id = this.selectedId();
    if (!id) {
      return;
    }
    this.selectedChange.emit(null);
    this.focusPin(id);
  }

  /**
   * Lleva el foco a la chincheta de un lugar, por ejemplo desde «Ver en el mapa». Antes muestra
   * el mapa entero, para que también se vea su popover.
   */
  focusPin(id: string): void {
    const pin = this.host.nativeElement.querySelector<HTMLButtonElement>(
      `[data-poi-id="${CSS.escape(id)}"]`,
    );
    if (!pin) {
      return;
    }
    this.host.nativeElement.scrollIntoView({ block: 'nearest' });
    pin.focus({ preventScroll: true });
  }
}

function boundsOf(pois: readonly Poi[]): Bounds | null {
  const points = pois.flatMap((poi) => (poi.coordenadas ? [poi.coordenadas] : []));
  if (points.length === 0) {
    return null;
  }
  return {
    minLat: Math.min(...points.map((point) => point.lat)),
    maxLat: Math.max(...points.map((point) => point.lat)),
    minLon: Math.min(...points.map((point) => point.lon)),
    maxLon: Math.max(...points.map((point) => point.lon)),
  };
}

/** Posición en % dentro del recuadro, con margen. Con un solo punto, en el centro. */
function scale(value: number, min: number, max: number): number {
  if (max === min) {
    return 50;
  }
  return MAP_PADDING + ((value - min) / (max - min)) * (100 - 2 * MAP_PADDING);
}
