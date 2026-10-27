/**
 * Fichas reales de la API (GET /api/pois/{id}), copiadas tal cual para los tests.
 * Cubren los casos que importan a la interfaz: horario partido, gratis, temporada y horario no
 * publicado.
 */

import { Poi } from '../app/core/models/poi.model';

export const CASTLE: Poi = {
  id: 'poi-001',
  nombre: { texto: 'Castillo de Valdelumbre', idioma: 'es' },
  categoria: 'monumento',
  descripcion: {
    texto:
      'Fortaleza del siglo XII sobre el cerro, con vistas a todo el valle. Acceso por una cuesta empedrada.',
    idioma: 'es',
  },
  coordenadas: { lat: 40.4172, lon: -3.7051 },
  accesible: false,
  horario: {
    siempre_abierto: false,
    franjas: [
      { dias: [1, 2, 3, 4, 5, 6], abre: '10:00', cierra: '14:00', temporada: null },
      { dias: [1, 2, 3, 4, 5, 6], abre: '17:00', cierra: '20:00', temporada: null },
    ],
    incompleto: false,
  },
  precio: { tipo: 'rango', minimo: 4.5, maximo: 4.5 },
  etiquetas: ['historia', 'vistas'],
};

export const OIL_MUSEUM: Poi = {
  id: 'poi-003',
  nombre: { texto: 'Museo del Aceite', idioma: 'es' },
  categoria: 'museo',
  descripcion: {
    texto: 'Museo etnográfico sobre la almazara tradicional. Ascensor y audioguía con subtítulos.',
    idioma: 'es',
  },
  coordenadas: { lat: 40.416, lon: -3.708 },
  accesible: true,
  horario: {
    siempre_abierto: false,
    franjas: [{ dias: [2, 3, 4, 5, 6, 7], abre: '10:00', cierra: '18:00', temporada: null }],
    incompleto: false,
  },
  precio: { tipo: 'rango', minimo: 0, maximo: 0 },
  etiquetas: ['historia', 'gastronomía', 'familias'],
};

export const NATURAL_POOL: Poi = {
  id: 'poi-014',
  nombre: { texto: 'Piscina Natural del Charco Verde', idioma: 'es' },
  categoria: 'naturaleza',
  descripcion: {
    texto:
      'Poza natural en el río. Solo en temporada de baño (junio a septiembre). Sin socorrista.',
    idioma: 'es',
  },
  coordenadas: { lat: 40.435, lon: -3.725 },
  accesible: false,
  horario: {
    siempre_abierto: false,
    franjas: [
      {
        dias: [1, 2, 3, 4, 5, 6, 7],
        abre: '11:00',
        cierra: '20:00',
        temporada: { inicio: '06-01', fin: '09-30' },
      },
    ],
    incompleto: false,
  },
  precio: { tipo: 'rango', minimo: 0, maximo: 0 },
  etiquetas: ['naturaleza', 'verano'],
};

export const HERMITAGE: Poi = {
  id: 'poi-018',
  nombre: { texto: 'Ermita de la Virgen del Cerro', idioma: 'es' },
  categoria: 'monumento',
  descripcion: {
    texto:
      'Pequeña ermita a la que se llega por un camino de tierra de 2 km. Romería el segundo domingo de mayo.',
    idioma: 'es',
  },
  coordenadas: { lat: 40.426, lon: -3.695 },
  accesible: false,
  horario: { siempre_abierto: false, franjas: [], incompleto: false },
  precio: { tipo: 'rango', minimo: 0, maximo: 0 },
  etiquetas: ['historia', 'senderismo'],
};

export const TEST_CATALOG: readonly Poi[] = [CASTLE, OIL_MUSEUM, NATURAL_POOL, HERMITAGE];
