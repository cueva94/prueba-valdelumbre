"""Estado de apertura de un punto en un momento dado: abierto, cerrado o desconocido."""

from dataclasses import dataclass
from datetime import date, datetime, time
from enum import StrEnum

from app.catalogo.modelos import Horario


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
        if momento.dia not in franja.dias or not franja.abre <= momento.hora < franja.cierra:
            continue
        if franja.temporada is None:
            return EstadoApertura.ABIERTO
        if momento.fecha is None:
            depende_de_la_fecha = True
        elif franja.temporada.incluye(momento.fecha):
            return EstadoApertura.ABIERTO

    return EstadoApertura.DESCONOCIDO if depende_de_la_fecha else EstadoApertura.CERRADO
