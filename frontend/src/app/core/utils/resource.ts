import { HttpResourceRef } from '@angular/common/http';
import {
  linkedSignal,
  Resource,
  resourceFromSnapshots,
  ResourceSnapshot,
  ResourceStatus,
  Signal,
} from '@angular/core';

/**
 * Un recurso HTTP de solo lectura que se puede volver a pedir («Volver a intentarlo»). Como
 * `HttpResourceRef`, redeclara `hasValue()` para que, comprobado, `value()` no sea `undefined`.
 */
export interface ReloadableResource<T> extends Resource<T> {
  hasValue(
    this: T extends undefined ? this : never,
  ): this is ReloadableResource<Exclude<T, undefined>>;
  hasValue(): boolean;
  reload(): boolean;
}

/**
 * El mismo recurso, pero si se vuelve a pedir lo mismo en otro idioma, sigue mostrando lo que
 * tenía hasta que llega la respuesta, en lugar de quedarse vacío un instante (el «destello» al
 * cambiar de idioma). Si cambia lo que se pide (otros filtros, otro lugar, otra pregunta), se
 * muestra la carga como siempre, para no enseñar datos de otra consulta.
 *
 * `request` es lo que se pide sin el idioma. Sigue el patrón de la guía de Angular «Resource
 * composition with snapshots» (`resourceFromSnapshots` es experimental en Angular 22).
 */
export function keepValueAcrossLanguages<T>(
  resource: HttpResourceRef<T>,
  request: () => unknown,
): ReloadableResource<T> {
  const snapshot = linkedSignal<
    { snapshot: ResourceSnapshot<T>; request: string },
    ResourceSnapshot<T>
  >({
    source: () => ({ snapshot: resource.snapshot(), request: JSON.stringify(request()) ?? '' }),
    computation: (current, previous) => {
      const shown = previous?.value;
      const sameRequest = previous?.source.request === current.request;
      if (
        current.snapshot.status === 'loading' &&
        sameRequest &&
        shown !== undefined &&
        shown.status !== 'error' &&
        shown.value !== undefined
      ) {
        return { status: 'loading', value: shown.value };
      }
      return current.snapshot;
    },
  });
  return new LanguageStableResource(resourceFromSnapshots(snapshot), resource);
}

class LanguageStableResource<T> implements ReloadableResource<T> {
  readonly value: Signal<T>;
  readonly status: Signal<ResourceStatus>;
  readonly error: Signal<Error | undefined>;
  readonly isLoading: Signal<boolean>;
  readonly snapshot: Signal<ResourceSnapshot<T>>;

  constructor(
    private readonly shown: Resource<T>,
    private readonly source: HttpResourceRef<T>,
  ) {
    this.value = shown.value;
    this.status = shown.status;
    this.error = shown.error;
    this.isLoading = shown.isLoading;
    this.snapshot = shown.snapshot;
  }

  hasValue(
    this: T extends undefined ? this : never,
  ): this is ReloadableResource<Exclude<T, undefined>>;
  hasValue(): boolean;
  hasValue(): boolean {
    return this.shown.hasValue();
  }

  reload(): boolean {
    return this.source.reload();
  }
}
