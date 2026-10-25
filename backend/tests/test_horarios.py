"""Estado de apertura: franjas [abre, cierra), días ISO, temporadas y desconocidos (D6, D7)."""

from datetime import date, datetime, time

import pytest

from app.catalogo.horarios import EstadoApertura, Momento, estado_apertura
from app.catalogo.modelos import Franja, Horario, Temporada

LUNES, MARTES, VIERNES, SABADO, DOMINGO = 1, 2, 5, 6, 7
ABIERTO, CERRADO, DESCONOCIDO = (
    EstadoApertura.ABIERTO,
    EstadoApertura.CERRADO,
    EstadoApertura.DESCONOCIDO,
)

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


# --- Franjas que cruzan la medianoche --------------------------------------------------------

# Viernes y sábado de 20:00 a 02:00: la madrugada pertenece a la noche anterior.
NOCHES_DE_FIN_DE_SEMANA = Horario(
    siempre_abierto=False,
    franjas=(Franja(dias=frozenset({VIERNES, SABADO}), abre=time(20), cierra=time(2)),),
)


@pytest.mark.parametrize(
    ("dia", "hora", "esperado"),
    [
        (VIERNES, time(19, 59), CERRADO),
        (VIERNES, time(20, 0), ABIERTO),  # la apertura está incluida
        (VIERNES, time(23, 59), ABIERTO),
        (SABADO, time(0, 30), ABIERTO),  # madrugada del sábado: la apertura empezó el viernes
        (SABADO, time(2, 0), CERRADO),  # el cierre no está incluido
        (SABADO, time(12, 0), CERRADO),
        (SABADO, time(23, 59), ABIERTO),
        (DOMINGO, time(0, 30), ABIERTO),  # madrugada del domingo: empezó el sábado
        (DOMINGO, time(2, 0), CERRADO),
        (VIERNES, time(0, 30), CERRADO),  # el jueves no abre: su madrugada está cerrada
        (LUNES, time(0, 30), CERRADO),  # el domingo no abre
    ],
)
def test_franja_que_cruza_la_medianoche(dia, hora, esperado):
    assert estado_apertura(NOCHES_DE_FIN_DE_SEMANA, Momento(dia, hora)) == esperado


def test_la_madrugada_del_lunes_pertenece_al_domingo():
    domingo_noche = Horario(
        siempre_abierto=False,
        franjas=(Franja(dias=frozenset({DOMINGO}), abre=time(22), cierra=time(1)),),
    )

    assert estado_apertura(domingo_noche, Momento(LUNES, time(0, 30))) == ABIERTO
    assert estado_apertura(domingo_noche, Momento(DOMINGO, time(0, 30))) == CERRADO


def test_la_temporada_de_una_franja_nocturna_se_mira_el_dia_en_que_empezo():
    noches_de_verano = Horario(
        siempre_abierto=False,
        franjas=(
            Franja(dias=frozenset(range(1, 8)), abre=time(22), cierra=time(2), temporada=VERANO),
        ),
    )
    # 1/10 a la 01:00: la apertura empezó el 30/9, último día de la temporada.
    uno_de_octubre = Momento.desde_datetime(datetime(2026, 10, 1, 1, 0))
    # 1/6 a la 01:00: la apertura habría empezado el 31/5, antes de la temporada.
    uno_de_junio = Momento.desde_datetime(datetime(2026, 6, 1, 1, 0))

    assert estado_apertura(noches_de_verano, uno_de_octubre) == ABIERTO
    assert estado_apertura(noches_de_verano, uno_de_junio) == CERRADO


# --- Horarios incompletos --------------------------------------------------------------------


def test_un_horario_incompleto_no_afirma_que_este_cerrado():
    # Mismo turno partido, pero en el original había alguna franja que no se pudo interpretar.
    incompleto = Horario(siempre_abierto=False, franjas=TURNO_PARTIDO.franjas, incompleto=True)

    assert estado_apertura(incompleto, Momento(LUNES, time(12))) == ABIERTO
    assert estado_apertura(incompleto, Momento(LUNES, time(15, 30))) == DESCONOCIDO
    assert estado_apertura(TURNO_PARTIDO, Momento(LUNES, time(15, 30))) == CERRADO
