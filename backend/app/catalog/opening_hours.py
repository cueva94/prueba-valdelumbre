"""Estado de apertura de un punto: abierto, cerrado o desconocido.

Las funciones son deterministas: reciben el momento que se quiere comprobar, nunca consultan la
hora actual. La hora del pueblo («ahora») la calcula quien llama (ver app/config.py).
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from enum import StrEnum

from app.catalog.models import OpeningHours, TimeSlot

SUNDAY = 7


class OpeningStatus(StrEnum):
    OPEN = "abierto"
    CLOSED = "cerrado"
    UNKNOWN = "desconocido"


@dataclass(frozen=True)
class Moment:
    """Día de la semana ISO (1 = lunes … 7 = domingo) y hora; la fecha solo si se conoce."""

    weekday: int
    time_of_day: time
    calendar_date: date | None = None

    @classmethod
    def from_datetime(cls, instant: datetime) -> "Moment":
        return cls(instant.isoweekday(), instant.time(), instant.date())


# Si una franja cubre lo que se comprueba y, en ese caso, la fecha en que empezó la apertura
# (None si no se conoce). La fecha decide las temporadas.
type _Coverage = Callable[[TimeSlot], tuple[bool, date | None]]


def opening_status(hours: OpeningHours, moment: Moment) -> OpeningStatus:
    """Si está abierto en ese momento. Las franjas son intervalos [abre, cierra)."""
    return _status(hours, lambda slot: _covers_moment(slot, moment))


def opening_status_on_day(
    hours: OpeningHours, weekday: int, calendar_date: date | None = None
) -> OpeningStatus:
    """Si abre en algún momento de ese día, incluida la madrugada de una franja nocturna."""
    return _status(hours, lambda slot: _covers_day(slot, weekday, calendar_date))


def _status(hours: OpeningHours, covers: _Coverage) -> OpeningStatus:
    """Abierto si una franja lo cubre; desconocido si faltan datos para afirmar que está cerrado."""
    if hours.always_open:
        return OpeningStatus.OPEN
    if not hours.slots:
        return OpeningStatus.UNKNOWN

    depends_on_date = False
    for slot in hours.slots:
        covered, start_date = covers(slot)
        if not covered:
            continue
        if slot.season is None:
            return OpeningStatus.OPEN
        if start_date is None:
            depends_on_date = True
        elif slot.season.includes(start_date):
            return OpeningStatus.OPEN

    if depends_on_date or hours.incomplete:
        return OpeningStatus.UNKNOWN
    return OpeningStatus.CLOSED


def _covers_moment(slot: TimeSlot, moment: Moment) -> tuple[bool, date | None]:
    if not slot.crosses_midnight:
        covered = moment.weekday in slot.weekdays and slot.opens <= moment.time_of_day < slot.closes
        return covered, moment.calendar_date
    # Tramo de la noche: desde la apertura hasta las 24:00 del día en que empieza.
    if moment.weekday in slot.weekdays and moment.time_of_day >= slot.opens:
        return True, moment.calendar_date
    # Tramo de la madrugada: desde las 00:00 hasta el cierre, del día siguiente.
    if _previous_weekday(moment.weekday) in slot.weekdays and moment.time_of_day < slot.closes:
        return True, _previous_date(moment.calendar_date)
    return False, None


def _covers_day(
    slot: TimeSlot, weekday: int, calendar_date: date | None
) -> tuple[bool, date | None]:
    if weekday in slot.weekdays:
        return True, calendar_date
    if slot.crosses_midnight and _previous_weekday(weekday) in slot.weekdays:
        return True, _previous_date(calendar_date)
    return False, None


def _previous_weekday(weekday: int) -> int:
    return SUNDAY if weekday == 1 else weekday - 1


def _previous_date(day: date | None) -> date | None:
    return day - timedelta(days=1) if day else None
