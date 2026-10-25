"""Estado de apertura de un punto en un momento dado: abierto, cerrado o desconocido."""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from enum import StrEnum

from app.catalogo.modelos import Franja, Horario


class EstadoApertura(StrEnum):
    ABIERTO = "abierto"
    CERRADO = "cerrado"
    DESCONOCIDO = "desconocido"


@dataclass(frozen=True)
class Momento:
    """Día de la semana ISO (1 = lunes … 7 = domingo) y hora; la fecha solo si se conoce."""

    dia: int
    hora: time
    fecha: date | None = None

    @classmethod
    def desde_datetime(cls, instante: datetime) -> "Momento":
        return cls(dia=instante.isoweekday(), hora=instante.time(), fecha=instante.date())


def estado_apertura(horario: Horario, momento: Momento) -> EstadoApertura:
    """Las franjas son intervalos [abre, cierra). Si faltan datos, el estado es desconocido."""
    if horario.siempre_abierto:
        return EstadoApertura.ABIERTO
    if not horario.franjas:
        return EstadoApertura.DESCONOCIDO

    depende_de_la_fecha = False
    for franja in horario.franjas:
        cubre, fecha_de_inicio = _cubre(franja, momento)
        if not cubre:
            continue
        if franja.temporada is None:
            return EstadoApertura.ABIERTO
        if fecha_de_inicio is None:
            depende_de_la_fecha = True
        elif franja.temporada.incluye(fecha_de_inicio):
            return EstadoApertura.ABIERTO

    if depende_de_la_fecha or horario.incompleto:
        return EstadoApertura.DESCONOCIDO
    return EstadoApertura.CERRADO


def _cubre(franja: Franja, momento: Momento) -> tuple[bool, date | None]:
    """Si la franja cubre el momento y en qué fecha empezó esa apertura (si se conoce)."""
    if not franja.cruza_medianoche:
        cubre = momento.dia in franja.dias and franja.abre <= momento.hora < franja.cierra
        return cubre, momento.fecha
    # Tramo de la noche: desde la apertura hasta las 24:00 del día en que empieza.
    if momento.dia in franja.dias and momento.hora >= franja.abre:
        return True, momento.fecha
    # Tramo de la madrugada: desde las 00:00 hasta el cierre, del día siguiente.
    if _dia_anterior(momento.dia) in franja.dias and momento.hora < franja.cierra:
        return True, momento.fecha - timedelta(days=1) if momento.fecha else None
    return False, None


def _dia_anterior(dia: int) -> int:
    return 7 if dia == 1 else dia - 1
