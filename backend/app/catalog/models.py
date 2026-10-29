"""Modelo del catálogo ya normalizado. Los datos crudos solo existen dentro de normalization.py."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, time
from enum import StrEnum


class Language(StrEnum):
    """Idiomas de los textos del catálogo y de las respuestas."""

    ES = "es"
    EN = "en"


class Category(StrEnum):
    """Categorías del catálogo. Los valores son los del JSON original, ya normalizados."""

    MONUMENT = "monumento"
    MUSEUM = "museo"
    NATURE = "naturaleza"
    ROUTE = "ruta"
    PUBLIC_SPACE = "espacio_publico"
    GASTRONOMY = "gastronomia"
    SERVICE = "servicio"


class Defect(StrEnum):
    EMBEDDED_INSTRUCTION = "D1"
    DUPLICATE = "D2"
    COORDINATES = "D3"
    PRICE = "D4"
    UNKNOWN_ACCESSIBILITY = "D5"
    UNKNOWN_OPENING_HOURS = "D6"
    SEASONAL_HOURS = "D7"
    MISSING_TRANSLATION = "D9"
    VALIDATION = "V"


@dataclass(frozen=True)
class LocalizedText:
    """Un texto y el idioma en que está realmente escrito."""

    text: str
    language: Language


@dataclass(frozen=True)
class BilingualText:
    es: str
    en: str | None

    def in_language(self, language: Language) -> LocalizedText:
        """Texto en el idioma pedido o, si falta la traducción, en español (nunca se inventa)."""
        if language is Language.EN and self.en:
            return LocalizedText(self.en, Language.EN)
        return LocalizedText(self.es, Language.ES)


@dataclass(frozen=True)
class Season:
    """Periodo del año entre dos (mes, día), ambos incluidos. Puede cruzar el fin de año."""

    start: tuple[int, int]
    end: tuple[int, int]

    def includes(self, day: date) -> bool:
        month_day = (day.month, day.day)
        if self.start <= self.end:
            return self.start <= month_day <= self.end
        return month_day >= self.start or month_day <= self.end


@dataclass(frozen=True)
class TimeSlot:
    """Apertura en los días indicados. Si `closes` es anterior a `opens`, cruza la medianoche:
    termina el día siguiente (viernes 20:00-02:00 cubre hasta el sábado a las 02:00)."""

    weekdays: frozenset[int]  # ISO 8601: 1 = lunes … 7 = domingo; día en que empieza la franja
    opens: time
    closes: time  # excluida: a esta hora ya está cerrado
    season: Season | None = None

    @property
    def crosses_midnight(self) -> bool:
        return self.closes < self.opens


@dataclass(frozen=True)
class OpeningHours:
    always_open: bool
    slots: tuple[TimeSlot, ...] = ()
    # Alguna franja del original no se pudo interpretar: fuera de las franjas válidas no se
    # puede afirmar que esté cerrado.
    incomplete: bool = False


@dataclass(frozen=True)
class PriceRange:
    """Rango en euros; un precio fijo tiene mínimo igual a máximo."""

    min_eur: float
    max_eur: float

    @property
    def is_free(self) -> bool:
        return self.max_eur == 0


@dataclass(frozen=True)
class UnparsedPrice:
    """Precio en texto que no se puede convertir a euros con seguridad («consultar»).

    Se conserva tal cual para mostrarlo; nunca se usa como número.
    """

    text: str


@dataclass(frozen=True)
class Coordinates:
    lat: float
    lon: float


@dataclass(frozen=True)
class Poi:
    id: str
    name: BilingualText
    category: Category | None  # None: ausente o no reconocida
    description: BilingualText
    coordinates: Coordinates | None  # None: desconocidas o no fiables
    accessible: bool | None  # None: sin datos
    opening_hours: OpeningHours
    price: PriceRange | UnparsedPrice | None  # None: sin datos
    tags: tuple[str, ...]


@dataclass(frozen=True)
class Incident:
    defect: Defect
    poi_id: str | None
    field: str
    detail: str


@dataclass(frozen=True)
class Catalog:
    pois: tuple[Poi, ...]
    excluded: Mapping[str, str]  # id -> motivo; de solo lectura
    incidents: tuple[Incident, ...]
    records_read: int
