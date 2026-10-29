import { Component, input } from '@angular/core';

let nextId = 0;

/**
 * Estado vacío o de error (sin resultados, ficha no encontrada, error de carga) con sus
 * acciones proyectadas. Un error se anuncia a los lectores de pantalla.
 */
@Component({
  selector: 'app-state-panel',
  templateUrl: './state-panel.html',
  styleUrl: './state-panel.css',
})
export class StatePanel {
  readonly heading = input.required<string>();
  readonly message = input('');
  readonly eyebrow = input('');
  readonly tone = input<'neutral' | 'error'>('neutral');

  protected readonly id = `state-${nextId++}`;
}
