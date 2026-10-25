"""Estado de apertura: franjas [abre, cierra), días ISO, temporadas y desconocidos (D6, D7)."""

from datetime import date, datetime, time

import pytest

from app.catalogo.horarios import EstadoApertura, Momento, estado_apertura
from app.catalogo.modelos import Franja, Horario, Temporada

LUNES, MARTES, SABADO, DOMINGO = 1, 2, 6, 7

# Turno partido de lunes a sábado: 10:00-14:00 y 17:00-20:00.
TURNO_PARTIDO = Horario(
    siempre_abierto=False,
    franjas=(
        Franja(dias=frozenset(range(1, 7)), abre=time(10), cierra=time(14)),
        Franja(dias=frozenset(range(1, 7)), abre=time(17), cierra=time(20)),
    ),
)
VERANO = Temporada(inicio=(6, 1), fin=(9, 30))
SOLO_EN_VERANO = Horario(
    siempre_abierto=False,
    franjas=(
        Franja(dias=frozenset(range(1, 8)), abre=time(11), cierra=time(20), temporada=VERANO),
    ),
)


@pytest.mark.parametrize(
    ("dia", "hora", "esperado"),
    [
        (LUNES, time(10, 0), EstadoApertura.ABIERTO),  # la apertura está incluida
        (LUNES, time(13, 59), EstadoApertura.ABIERTO),
        (LUNES, time(14, 0), EstadoApertura.CERRADO),  # el cierre no está incluido
        (LUNES, time(15, 30), EstadoApertura.CERRADO),  # entre turnos
        (SABADO, time(17, 0), EstadoApertura.ABIERTO),  # segundo turno
        (DOMINGO, time(12, 0), EstadoApertura.CERRADO),  # día no incluido
    ],
)
def test_turno_partido(dia, hora, esperado):
    assert estado_apertura(TURNO_PARTIDO, Momento(dia, hora)) == esperado


def test_los_dias_son_iso_y_el_1_es_el_lunes():
    cerrado_los_lunes = Horario(
        siempre_abierto=False,
        franjas=(Franja(dias=frozenset({2, 3, 4, 5, 6, 7}), abre=time(10), cierra=time(18)),),
    )
    lunes_a_mediodia = Momento.desde_datetime(datetime(2026, 10, 26, 12, 0))  # lunes 26/10/2026

    assert lunes_a_mediodia.dia == LUNES
    assert estado_apertura(cerrado_los_lunes, lunes_a_mediodia) == EstadoApertura.CERRADO
    assert estado_apertura(cerrado_los_lunes, Momento(MARTES, time(12))) == EstadoApertura.ABIERTO


def test_siempre_abierto():
    assert (
        estado_apertura(Horario(siempre_abierto=True), Momento(DOMINGO, time(3)))
        == EstadoApertura.ABIERTO
    )


def test_sin_franjas_el_estado_es_desconocido_no_cerrado():
    sin_datos = Horario(siempre_abierto=False, franjas=())

    assert estado_apertura(sin_datos, Momento(LUNES, time(12))) == EstadoApertura.DESCONOCIDO


@pytest.mark.parametrize(
    ("fecha", "esperado"),
    [
        (None, EstadoApertura.DESCONOCIDO),  # sin fecha no se sabe si es temporada
        (date(2026, 7, 15), EstadoApertura.ABIERTO),
        (date(2026, 9, 30), EstadoApertura.ABIERTO),  # último día incluido
        (date(2026, 10, 1), EstadoApertura.CERRADO),
    ],
)
def test_franja_de_temporada_dentro_del_horario(fecha, esperado):
    assert estado_apertura(SOLO_EN_VERANO, Momento(LUNES, time(12), fecha)) == esperado


def test_franja_de_temporada_fuera_de_hora_esta_cerrada_aunque_no_haya_fecha():
    assert estado_apertura(SOLO_EN_VERANO, Momento(LUNES, time(22))) == EstadoApertura.CERRADO


@pytest.mark.parametrize(
    ("fecha", "incluida"),
    [(date(2026, 12, 20), True), (date(2027, 1, 10), True), (date(2027, 3, 1), False)],
)
def test_temporada_que_cruza_el_fin_de_ano(fecha, incluida):
    invierno = Temporada(inicio=(12, 1), fin=(2, 28))

    assert invierno.incluye(fecha) is incluida
