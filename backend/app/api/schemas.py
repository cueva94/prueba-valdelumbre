"""Contratos HTTP de la API.

Los nombres en JSON están en español, como los parámetros del enunciado y los datos originales
(`categoria`, `pregunta`…). En el código, los atributos están en inglés y se enlazan con alias.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.catalog.models import (
    Category,
    Language,
    LocalizedText,
    OpeningHours,
    Poi,
    PriceRange,
    Season,
    TimeSlot,
    UnparsedPrice,
)

MAX_QUESTION_LENGTH = 500


class ResponseModel(BaseModel):
    """Respuesta: se construye en el código con los nombres en inglés y se envía con los alias."""

    model_config = ConfigDict(frozen=True, validate_by_name=True, serialize_by_alias=True)


class RequestModel(BaseModel):
    """Petición: solo se aceptan los nombres del contrato y ningún campo desconocido."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class LocalizedTextOut(ResponseModel):
    text: str = Field(alias="texto")
    language: Language = Field(
        alias="idioma",
        description="Idioma en que está escrito: si falta la traducción pedida, es el español.",
    )

    @classmethod
    def from_domain(cls, text: LocalizedText) -> "LocalizedTextOut":
        return cls(text=text.text, language=text.language)


class CoordinatesOut(ResponseModel):
    lat: float
    lon: float


class SeasonOut(ResponseModel):
    start: str = Field(alias="inicio", description="MM-DD, incluido.", examples=["06-01"])
    end: str = Field(alias="fin", description="MM-DD, incluido.", examples=["09-30"])

    @classmethod
    def from_domain(cls, season: Season) -> "SeasonOut":
        return cls(start=_month_day(season.start), end=_month_day(season.end))


class TimeSlotOut(ResponseModel):
    weekdays: list[int] = Field(alias="dias", description="ISO 8601: 1 = lunes … 7 = domingo.")
    opens: str = Field(alias="abre", examples=["10:00"])
    closes: str = Field(
        alias="cierra",
        description=(
            "No incluida: a esa hora ya está cerrado. Si es anterior a `abre`, la franja termina "
            "al día siguiente."
        ),
        examples=["14:00"],
    )
    season: SeasonOut | None = Field(
        alias="temporada", description="Solo abre en ese periodo del año."
    )

    @classmethod
    def from_domain(cls, slot: TimeSlot) -> "TimeSlotOut":
        return cls(
            weekdays=sorted(slot.weekdays),
            opens=f"{slot.opens:%H:%M}",
            closes=f"{slot.closes:%H:%M}",
            season=SeasonOut.from_domain(slot.season) if slot.season else None,
        )


class OpeningHoursOut(ResponseModel):
    always_open: bool = Field(alias="siempre_abierto")
    slots: list[TimeSlotOut] = Field(
        alias="franjas",
        description="Vacío y sin `siempre_abierto`: el horario es desconocido, no «cerrado».",
    )
    incomplete: bool = Field(
        alias="incompleto",
        description="Alguna franja del original no se pudo interpretar y se ha descartado.",
    )

    @classmethod
    def from_domain(cls, hours: OpeningHours) -> "OpeningHoursOut":
        return cls(
            always_open=hours.always_open,
            slots=[TimeSlotOut.from_domain(slot) for slot in hours.slots],
            incomplete=hours.incomplete,
        )


class PriceRangeOut(ResponseModel):
    kind: Literal["rango"] = Field(default="rango", alias="tipo")
    min_eur: float = Field(alias="minimo", description="Euros. 0 es gratis.")
    max_eur: float = Field(alias="maximo", description="Euros. Igual a `minimo` si es fijo.")


class UnparsedPriceOut(ResponseModel):
    kind: Literal["texto"] = Field(default="texto", alias="tipo")
    text: str = Field(alias="texto", description="Precio original que no es un importe.")


PriceOut = Annotated[PriceRangeOut | UnparsedPriceOut, Field(discriminator="kind")]


class PoiOut(ResponseModel):
    id: str
    name: LocalizedTextOut = Field(alias="nombre")
    category: Category | None = Field(alias="categoria", description="null: desconocida.")
    description: LocalizedTextOut = Field(alias="descripcion")
    coordinates: CoordinatesOut | None = Field(
        alias="coordenadas",
        description="null: desconocidas o no fiables; el punto no se debe dibujar en el mapa.",
    )
    accessible: bool | None = Field(
        alias="accesible", description="null: sin datos (ni accesible ni no accesible)."
    )
    opening_hours: OpeningHoursOut = Field(alias="horario")
    price: PriceOut | None = Field(alias="precio", description="null: sin datos.")
    tags: list[str] = Field(alias="etiquetas", description="Tal como vienen, solo en español.")

    @classmethod
    def from_domain(cls, poi: Poi, language: Language) -> "PoiOut":
        coordinates = poi.coordinates
        return cls(
            id=poi.id,
            name=LocalizedTextOut.from_domain(poi.name.in_language(language)),
            category=poi.category,
            description=LocalizedTextOut.from_domain(poi.description.in_language(language)),
            coordinates=CoordinatesOut(lat=coordinates.lat, lon=coordinates.lon)
            if coordinates
            else None,
            accessible=poi.accessible,
            opening_hours=OpeningHoursOut.from_domain(poi.opening_hours),
            price=_price_out(poi.price),
            tags=list(poi.tags),
        )


class AskIn(RequestModel):
    question: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=MAX_QUESTION_LENGTH)
    ] = Field(alias="pregunta", examples=["¿Qué museos son accesibles?"])
    language: Language = Field(
        default=Language.ES, alias="idioma", description="Idioma de la respuesta."
    )


class AskOut(ResponseModel):
    answer: str = Field(alias="respuesta")
    ids: list[str] = Field(
        description=(
            "Ids de los puntos en los que se apoya la respuesta. Los decide la búsqueda sobre el "
            "catálogo, nunca el redactor del texto."
        )
    )
    pois: list[PoiOut] = Field(description="Fichas de esos puntos, en el mismo orden que `ids`.")
    language: Language = Field(alias="idioma")


class HealthOut(ResponseModel):
    status: Literal["ok"] = Field(default="ok", alias="estado")


class ErrorOut(ResponseModel):
    detail: str


def _price_out(price: PriceRange | UnparsedPrice | None) -> PriceRangeOut | UnparsedPriceOut | None:
    if isinstance(price, PriceRange):
        return PriceRangeOut(min_eur=price.min_eur, max_eur=price.max_eur)
    if isinstance(price, UnparsedPrice):
        return UnparsedPriceOut(text=price.text)
    return None


def _month_day(month_day: tuple[int, int]) -> str:
    month, day = month_day
    return f"{month:02d}-{day:02d}"
