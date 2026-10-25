"""Modelo del catálogo ya limpio. Los datos crudos solo existen dentro de limpieza.py."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, time
from enum import StrEnum
from typing import Literal

Idioma = Literal["es", "en"]


class Defecto(StrEnum):
    """Tipos de defecto. Los códigos son los del inventario de DATOS.md."""

    INSTRUCCION_INCRUSTADA = "D1"
    DUPLICADO = "D2"
    COORDENADAS = "D3"
    PRECIO = "D4"
    ACCESIBILIDAD_DESCONOCIDA = "D5"
    HORARIO_DESCONOCIDO = "D6"
    TEMPORADA = "D7"
    TRADUCCION = "D9"
    VALIDACION = "V"


@dataclass(frozen=True)
class TextoBilingue:
    es: str
    en: str | None  # None: sin traducción

    def en_idioma(self, idioma: Idioma) -> tuple[str, Idioma]:
        """Texto en el idioma pedido o, si falta la traducción, en español; y el idioma devuelto."""
        if idioma == "en" and self.en:
            return self.en, "en"
        return self.es, "es"


@dataclass(frozen=True)
class Temporada:
    """Periodo del año entre dos (mes, día), ambos incluidos. Puede cruzar el fin de año."""

    inicio: tuple[int, int]
    fin: tuple[int, int]

    def incluye(self, fecha: date) -> bool:
        dia = (fecha.month, fecha.day)
        if self.inicio <= self.fin:
            return self.inicio <= dia <= self.fin
        return dia >= self.inicio or dia <= self.fin


@dataclass(frozen=True)
class Franja:
    dias: frozenset[int]  # ISO 8601: 1 = lunes … 7 = domingo
    abre: time
    cierra: time  # excluida: a esta hora ya está cerrado
    temporada: Temporada | None = None


@dataclass(frozen=True)
class Horario:
    siempre_abierto: bool
    franjas: tuple[Franja, ...] = ()


@dataclass(frozen=True)
class Precio:
    """Rango en euros; un precio fijo tiene mínimo igual a máximo."""

    minimo: float
    maximo: float

    @property
    def gratis(self) -> bool:
        return self.maximo == 0


@dataclass(frozen=True)
class Coordenadas:
    lat: float
    lon: float


@dataclass(frozen=True)
class Poi:
    id: str
    nombre: TextoBilingue
    categoria: str | None
    descripcion: TextoBilingue
    coordenadas: Coordenadas | None  # None: desconocidas o no fiables
    accesible: bool | None  # None: sin datos
    horario: Horario
    precio: Precio | None  # None: sin datos
    etiquetas: tuple[str, ...]


@dataclass(frozen=True)
class Incidencia:
    """Problema encontrado en un registro y qué se ha hecho con él."""

    defecto: Defecto
    poi_id: str | None
    campo: str
    detalle: str


@dataclass(frozen=True)
class Catalogo:
    pois: tuple[Poi, ...]
    excluidos: Mapping[str, str]  # id -> motivo
    incidencias: tuple[Incidencia, ...]
    registros_leidos: int
