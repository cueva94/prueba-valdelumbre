/**
 * Preparación común de los tests (angular.json → test → setupFiles).
 *
 * jsdom no maqueta, así que no implementa `scrollIntoView`: aquí no hace nada, como en un
 * navegador donde el elemento ya está a la vista. Los tests que lo necesiten pueden espiarlo.
 */
const element: Partial<Pick<Element, 'scrollIntoView'>> = Element.prototype;
element.scrollIntoView ??= function scrollIntoView(): void {
  // Sin maquetación no hay nada que desplazar.
};

// El idioma elegido se guarda en el navegador: cada test empieza sin preferencia guardada.
afterEach(() => localStorage.clear());
