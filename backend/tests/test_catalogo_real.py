"""Efecto de la limpieza sobre los datos reales de la prueba (DATOS.md → Inventario de defectos).

Las reglas se prueban de forma general en test_limpieza.py; aquí se documenta qué hacen con
el catálogo entregado y que cada defecto del inventario produce su incidencia.
"""

from datetime import time

import pytest

from app.catalogo.carga import cargar_catalogo
from app.catalogo.horarios import EstadoApertura, Momento, estado_apertura
from app.catalogo.modelos import Coordenadas, Defecto
from app.config import RUTA_POIS


@pytest.fixture(scope="module")
def catalogo():
    return cargar_catalogo(RUTA_POIS)


@pytest.fixture(scope="module")
def pois(catalogo):
    return {poi.id: poi for poi in catalogo.pois}


def test_se_publican_17_de_18_y_se_excluye_el_duplicado(catalogo):
    assert catalogo.registros_leidos == 18
    assert len(catalogo.pois) == 17
    assert catalogo.excluidos == {"poi-004": "duplicado de poi-003"}


def test_cada_defecto_del_inventario_genera_su_incidencia(catalogo):
    # D8 no genera incidencias: es la normalización que se usa al comparar y buscar.
    esperados = {
        Defecto.INSTRUCCION_INCRUSTADA,
        Defecto.DUPLICADO,
        Defecto.COORDENADAS,
        Defecto.PRECIO,
        Defecto.ACCESIBILIDAD_DESCONOCIDA,
        Defecto.HORARIO_DESCONOCIDO,
        Defecto.TEMPORADA,
        Defecto.TRADUCCION,
    }

    assert {incidencia.defecto for incidencia in catalogo.incidencias} == esperados


def test_d1_solo_se_elimina_texto_del_registro_con_la_instruccion(catalogo, pois):
    afectados = {
        i.poi_id for i in catalogo.incidencias if i.defecto == Defecto.INSTRUCCION_INCRUSTADA
    }

    assert afectados == {"poi-013"}
    assert pois["poi-013"].descripcion.es == "Colección de tapices flamencos."
    assert pois["poi-013"].accesible is False


def test_d3_se_corrigen_las_coordenadas_intercambiadas(pois):
    assert pois["poi-011"].coordenadas == Coordenadas(lat=40.421, lon=-3.711)


def test_d4_precios_en_texto(pois):
    assert pois["poi-003"].precio.gratis
    assert (pois["poi-009"].precio.minimo, pois["poi-009"].precio.maximo) == (25, 35)
    assert pois["poi-016"].precio is None


def test_d5_d6_lo_desconocido_sigue_desconocido(pois):
    assert pois["poi-011"].accesible is None
    assert (
        estado_apertura(pois["poi-018"].horario, Momento(1, time(12))) == EstadoApertura.DESCONOCIDO
    )


def test_se_lee_en_utf8(pois):
    assert pois["poi-006"].nombre.es == "Iglesia de San Bartolomé"
