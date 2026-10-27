import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { CASTLE, HERMITAGE, OIL_MUSEUM } from '../../../../testing/pois';
import { provideTestTranslations } from '../../../../testing/translations';
import { Poi } from '../../../core/models/poi.model';
import { PoiMap } from './poi-map';

const SOUTH_WEST: Poi = { ...OIL_MUSEUM, id: 'sw', coordenadas: { lat: 40.4, lon: -3.8 } };
const NORTH_EAST: Poi = { ...CASTLE, id: 'ne', coordenadas: { lat: 40.5, lon: -3.6 } };

describe('PoiMap', () => {
  let fixture: ComponentFixture<PoiMap>;
  let selections: (string | null)[];

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideRouter([]), ...provideTestTranslations()],
    });
    fixture = TestBed.createComponent(PoiMap);
    selections = [];
    fixture.componentInstance.selectedChange.subscribe((id) => selections.push(id));
  });

  function render(pois: Poi[], selectedId: string | null = null): HTMLElement {
    fixture.componentRef.setInput('pois', pois);
    fixture.componentRef.setInput('frame', [SOUTH_WEST, NORTH_EAST]);
    fixture.componentRef.setInput('selectedId', selectedId);
    fixture.detectChanges();
    return fixture.nativeElement as HTMLElement;
  }

  const pin = (map: HTMLElement, id: string) =>
    map.querySelector(`[data-poi-id="${id}"]`) as HTMLButtonElement;

  it('coloca cada lugar según sus coordenadas: el norte arriba y el este a la derecha', () => {
    const map = render([SOUTH_WEST, NORTH_EAST]);

    expect(pin(map, 'sw').style.left).toBe('8%');
    expect(pin(map, 'sw').style.top).toBe('92%');
    expect(pin(map, 'ne').style.left).toBe('92%');
    expect(pin(map, 'ne').style.top).toBe('8%');
  });

  it('no dibuja un lugar sin coordenadas, pero lo nombra', () => {
    const map = render([SOUTH_WEST, { ...HERMITAGE, coordenadas: null }]);

    expect(map.querySelectorAll('.pin')).toHaveLength(1);
    expect(map.querySelector('.map__unplaced')?.textContent).toContain(
      'Ermita de la Virgen del Cerro',
    );
  });

  it('el fondo se ancla a coordenadas: se proyecta igual que las chinchetas', () => {
    // Un lugar en el origen del fondo (40.435, −3.73) cae en el punto (0, 0) de sus formas.
    const atOrigin: Poi = { ...CASTLE, id: 'origin', coordenadas: { lat: 40.435, lon: -3.73 } };
    const map = render([atOrigin]);

    const transform = map.querySelector('.map__ground g')?.getAttribute('transform') ?? '';
    const [, , , , offsetX, offsetY] = (transform.match(/-?\d+(?:\.\d+)?(?:e-?\d+)?/g) ?? []).map(
      Number,
    );
    expect(offsetX).toBeCloseTo(Number.parseFloat(pin(map, 'origin').style.left), 6);
    expect(offsetY).toBeCloseTo(Number.parseFloat(pin(map, 'origin').style.top), 6);
    expect([...map.querySelectorAll('.map__label')].map((label) => label.textContent)).toEqual([
      'VALDELUMBRE',
      'Río Lumbre',
    ]);
  });

  it('sin un encuadre con extensión (un solo lugar), el fondo es una cuadrícula neutra', () => {
    fixture.componentRef.setInput('pois', [SOUTH_WEST]);
    fixture.componentRef.setInput('frame', [SOUTH_WEST]);
    fixture.detectChanges();
    const map = fixture.nativeElement as HTMLElement;

    expect(map.querySelector('.map__ground g')).toBeNull();
    expect(map.querySelector('.map__grid')).not.toBeNull();
    expect(map.querySelector('.map__label')).toBeNull();
  });

  it('focusPin muestra el mapa y lleva el foco a la chincheta', () => {
    const map = render([SOUTH_WEST, NORTH_EAST]);
    const scroll = vi.spyOn(Element.prototype, 'scrollIntoView');

    fixture.componentInstance.focusPin('ne');

    expect(scroll).toHaveBeenCalledWith({ block: 'nearest' });
    expect(document.activeElement).toBe(pin(map, 'ne'));
    scroll.mockRestore();
  });

  it('sin interacción solo sitúa los lugares: sin botones ni resumen, con su nombre para lectores', () => {
    fixture.componentRef.setInput('interactive', false);
    const map = render([NORTH_EAST], 'ne');

    expect(map.querySelector('button')).toBeNull();
    expect(map.querySelector('.popover')).toBeNull();
    expect(map.querySelector('.pin')?.classList).toContain('is-selected');
    expect(map.querySelector('.pin')?.textContent?.trim()).toBe(
      `${CASTLE.nombre.texto}, Monumento`,
    );
  });

  it('pulsar una chincheta la selecciona, y Escape cierra el resumen', () => {
    let map = render([SOUTH_WEST, NORTH_EAST]);
    pin(map, 'ne').click();

    map = render([SOUTH_WEST, NORTH_EAST], 'ne');
    expect(map.querySelector('.popover h3')?.textContent?.trim()).toBe(CASTLE.nombre.texto);

    pin(map, 'ne').dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));

    expect(selections).toEqual(['ne', null]);
  });
});
