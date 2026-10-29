"""Estado de apertura: franjas [abre, cierra), días ISO, temporadas y desconocidos (D6, D7)."""

from datetime import date, datetime, time

import pytest

from app.catalog.models import OpeningHours, Season, TimeSlot
from app.catalog.opening_hours import (
    Moment,
    OpeningStatus,
    opening_status,
    opening_status_on_day,
)

MONDAY, TUESDAY, FRIDAY, SATURDAY, SUNDAY = 1, 2, 5, 6, 7
OPEN, CLOSED, UNKNOWN = OpeningStatus.OPEN, OpeningStatus.CLOSED, OpeningStatus.UNKNOWN

# Turno partido de lunes a sábado: 10:00-14:00 y 17:00-20:00.
SPLIT_SHIFT = OpeningHours(
    always_open=False,
    slots=(
        TimeSlot(weekdays=frozenset(range(1, 7)), opens=time(10), closes=time(14)),
        TimeSlot(weekdays=frozenset(range(1, 7)), opens=time(17), closes=time(20)),
    ),
)
SUMMER = Season(start=(6, 1), end=(9, 30))
SUMMER_ONLY = OpeningHours(
    always_open=False,
    slots=(
        TimeSlot(weekdays=frozenset(range(1, 8)), opens=time(11), closes=time(20), season=SUMMER),
    ),
)


@pytest.mark.parametrize(
    ("weekday", "hour", "expected"),
    [
        (MONDAY, time(10, 0), OPEN),  # la apertura está incluida
        (MONDAY, time(13, 59), OPEN),
        (MONDAY, time(14, 0), CLOSED),  # el cierre no está incluido
        (MONDAY, time(15, 30), CLOSED),
        (SATURDAY, time(17, 0), OPEN),
        (SUNDAY, time(12, 0), CLOSED),
    ],
)
def test_split_shift(weekday, hour, expected):
    assert opening_status(SPLIT_SHIFT, Moment(weekday, hour)) == expected


def test_weekdays_are_iso_and_1_is_monday():
    closed_on_mondays = OpeningHours(
        always_open=False,
        slots=(TimeSlot(weekdays=frozenset({2, 3, 4, 5, 6, 7}), opens=time(10), closes=time(18)),),
    )
    monday_noon = Moment.from_datetime(datetime(2026, 10, 26, 12, 0))

    assert monday_noon.weekday == MONDAY
    assert opening_status(closed_on_mondays, monday_noon) == CLOSED
    assert opening_status(closed_on_mondays, Moment(TUESDAY, time(12))) == OPEN


def test_always_open():
    assert opening_status(OpeningHours(always_open=True), Moment(SUNDAY, time(3))) == OPEN


def test_without_slots_the_status_is_unknown_not_closed():
    no_data = OpeningHours(always_open=False, slots=())

    assert opening_status(no_data, Moment(MONDAY, time(12))) == UNKNOWN


@pytest.mark.parametrize(
    ("day", "expected"),
    [
        (None, UNKNOWN),  # sin fecha no se sabe si es temporada
        (date(2026, 7, 15), OPEN),
        (date(2026, 9, 30), OPEN),  # último día incluido
        (date(2026, 10, 1), CLOSED),
    ],
)
def test_seasonal_slot_within_hours(day, expected):
    assert opening_status(SUMMER_ONLY, Moment(MONDAY, time(12), day)) == expected


def test_seasonal_slot_outside_hours_is_closed_even_without_a_date():
    assert opening_status(SUMMER_ONLY, Moment(MONDAY, time(22))) == CLOSED


@pytest.mark.parametrize(
    ("day", "included"),
    [(date(2026, 12, 20), True), (date(2027, 1, 10), True), (date(2027, 3, 1), False)],
)
def test_season_crossing_the_new_year(day, included):
    winter = Season(start=(12, 1), end=(2, 28))

    assert winter.includes(day) is included


# Viernes y sábado de 20:00 a 02:00: la madrugada pertenece a la noche anterior.
WEEKEND_NIGHTS = OpeningHours(
    always_open=False,
    slots=(TimeSlot(weekdays=frozenset({FRIDAY, SATURDAY}), opens=time(20), closes=time(2)),),
)


@pytest.mark.parametrize(
    ("weekday", "hour", "expected"),
    [
        (FRIDAY, time(19, 59), CLOSED),
        (FRIDAY, time(20, 0), OPEN),  # la apertura está incluida
        (FRIDAY, time(23, 59), OPEN),
        (SATURDAY, time(0, 30), OPEN),  # madrugada del sábado: la apertura empezó el viernes
        (SATURDAY, time(2, 0), CLOSED),  # el cierre no está incluido
        (SATURDAY, time(12, 0), CLOSED),
        (SATURDAY, time(23, 59), OPEN),
        (SUNDAY, time(0, 30), OPEN),  # madrugada del domingo: empezó el sábado
        (SUNDAY, time(2, 0), CLOSED),
        (FRIDAY, time(0, 30), CLOSED),  # el jueves no abre: su madrugada está cerrada
        (MONDAY, time(0, 30), CLOSED),  # el domingo no abre
    ],
)
def test_slot_crossing_midnight(weekday, hour, expected):
    assert opening_status(WEEKEND_NIGHTS, Moment(weekday, hour)) == expected


def test_monday_early_hours_belong_to_sunday():
    sunday_night = OpeningHours(
        always_open=False,
        slots=(TimeSlot(weekdays=frozenset({SUNDAY}), opens=time(22), closes=time(1)),),
    )

    assert opening_status(sunday_night, Moment(MONDAY, time(0, 30))) == OPEN
    assert opening_status(sunday_night, Moment(SUNDAY, time(0, 30))) == CLOSED


def test_season_of_a_night_slot_is_checked_on_the_day_it_started():
    summer_nights = OpeningHours(
        always_open=False,
        slots=(
            TimeSlot(
                weekdays=frozenset(range(1, 8)), opens=time(22), closes=time(2), season=SUMMER
            ),
        ),
    )
    # 1/10 a la 01:00: la apertura empezó el 30/9, último día de la temporada.
    october_first = Moment.from_datetime(datetime(2026, 10, 1, 1, 0))
    # 1/6 a la 01:00: la apertura habría empezado el 31/5, antes de la temporada.
    june_first = Moment.from_datetime(datetime(2026, 6, 1, 1, 0))

    assert opening_status(summer_nights, october_first) == OPEN
    assert opening_status(summer_nights, june_first) == CLOSED


def test_incomplete_hours_never_claim_closed():
    incomplete = OpeningHours(always_open=False, slots=SPLIT_SHIFT.slots, incomplete=True)

    assert opening_status(incomplete, Moment(MONDAY, time(12))) == OPEN
    assert opening_status(incomplete, Moment(MONDAY, time(15, 30))) == UNKNOWN
    assert opening_status(SPLIT_SHIFT, Moment(MONDAY, time(15, 30))) == CLOSED


@pytest.mark.parametrize(
    ("hours", "weekday", "day", "expected"),
    [
        (SPLIT_SHIFT, MONDAY, None, OPEN),
        (SPLIT_SHIFT, SUNDAY, None, CLOSED),
        (WEEKEND_NIGHTS, SUNDAY, None, OPEN),  # madrugada de la noche del sábado
        (WEEKEND_NIGHTS, MONDAY, None, CLOSED),
        (SUMMER_ONLY, MONDAY, None, UNKNOWN),  # sin fecha no se sabe si es temporada
        (SUMMER_ONLY, MONDAY, date(2026, 7, 13), OPEN),
        (SUMMER_ONLY, MONDAY, date(2026, 10, 26), CLOSED),
        (OpeningHours(always_open=False), MONDAY, None, UNKNOWN),
    ],
)
def test_opening_status_on_day(hours, weekday, day, expected):
    assert opening_status_on_day(hours, weekday, day) == expected
