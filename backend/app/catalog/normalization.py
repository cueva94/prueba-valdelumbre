"""Normalización del catálogo crudo con reglas generales; cada corrección queda como incidencia.

Ninguna regla menciona ids concretos. Los defectos y las decisiones están en DATOS.md.
El resultado es determinista: los mismos registros producen el mismo catálogo y las mismas
incidencias, en el mismo orden.
"""

import math
import re
import statistics
from dataclasses import dataclass, replace
from datetime import date, time
from types import MappingProxyType
from typing import TypeGuard

from app.catalog.models import (
    BilingualText,
    Catalog,
    Category,
    Coordinates,
    Defect,
    Incident,
    Language,
    OpeningHours,
    Poi,
    PriceRange,
    Season,
    TimeSlot,
    UnparsedPrice,
)
from app.catalog.text import normalize_text, strip_embedded_instructions

type JsonValue = bool | int | float | str | list[JsonValue] | dict[str, JsonValue] | None


@dataclass(frozen=True)
class NormalizationThresholds:
    # Un punto a más de esta distancia del centro del catálogo (la mediana) no está en el pueblo.
    # 10 km es el diámetro aproximado de un municipio español medio (~62 km²); en los datos de
    # la prueba, el punto legítimo más lejano está a 2,6 km del centro.
    town_radius_km: float = 10.0
    # Dos registros con el mismo nombre normalizado a esta distancia o menos son el mismo lugar.
    # La distancia sola nunca basta: dos sitios distintos pueden estar puerta con puerta.
    duplicate_distance_km: float = 0.05


DEFAULT_THRESHOLDS = NormalizationThresholds()

# Con menos puntos válidos no se puede estimar dónde está el pueblo (D3).
MIN_POINTS_FOR_TOWN_CENTRE = 3
EARTH_RADIUS_KM = 6371.0
MAX_ABS_LATITUDE = 90.0
MAX_ABS_LONGITUDE = 180.0
ISO_WEEKDAYS = range(1, 8)
# Año bisiesto de referencia para validar fechas de temporada: admite el 29 de febrero.
LEAP_YEAR = 2000

_CATEGORIES = {category.value: category for category in Category}
_CATEGORY_SEPARATORS = re.compile(r"[\s-]+")
_HOUR = re.compile(r"^(\d{1,2}):(\d{2})$")
_SEASON = re.compile(r"^(\d{2})-(\d{2})/(\d{2})-(\d{2})$")
_NUMBER = r"(\d+(?:[.,]\d+)?)"
# Un número o un rango con guion o guion largo (U+2013): «4,50 €», «25-35», «25 - 35 euros».
_PRICE_IN_TEXT = re.compile(rf"^{_NUMBER}(?:\s*[-\u2013]\s*{_NUMBER})?\s*(?:€|eur|euros)?$")
_FREE_WORDS = {"gratis", "gratuito", "gratuita", "free"}


def normalize_catalog(
    records: list[JsonValue], thresholds: NormalizationThresholds = DEFAULT_THRESHOLDS
) -> Catalog:
    """Aplica todas las reglas y devuelve el catálogo publicable. No modifica `records`."""
    return _Normalizer(thresholds).run(records)


class _Normalizer:
    """Estado de una sola normalización: las incidencias y exclusiones que se van registrando."""

    def __init__(self, thresholds: NormalizationThresholds) -> None:
        self.thresholds = thresholds
        self.incidents: list[Incident] = []
        self.excluded: dict[str, str] = {}
        self.seen_ids: set[str] = set()

    def report(self, defect: Defect, poi_id: str | None, field: str, detail: str) -> None:
        self.incidents.append(Incident(defect, poi_id, field, detail))

    def run(self, records: list[JsonValue]) -> Catalog:
        pois = [poi for i, record in enumerate(records) if (poi := self._poi(record, i))]
        pois = self._validate_coordinates(pois)
        pois = self._remove_duplicates(pois)
        return Catalog(
            pois=tuple(pois),
            excluded=MappingProxyType(dict(self.excluded)),
            incidents=tuple(self.incidents),
            records_read=len(records),
        )

    def _poi(self, record: JsonValue, position: int) -> Poi | None:
        if not isinstance(record, dict):
            self.report(
                Defect.VALIDATION, None, "registro", f"registro {position}: no es un objeto"
            )
            return None
        raw_id = record.get("id")
        if not isinstance(raw_id, str) or not raw_id.strip():
            self.report(Defect.VALIDATION, None, "id", f"registro {position}: sin id, se descarta")
            return None
        poi_id = raw_id.strip()
        if poi_id in self.seen_ids:
            self.report(Defect.VALIDATION, poi_id, "id", "id repetido: se descarta esta aparición")
            return None

        name = self._bilingual_text(record.get("nombre"), poi_id, "nombre")
        if not name.es:
            self.report(Defect.VALIDATION, poi_id, "nombre.es", "sin nombre en español: se excluye")
            self.excluded[poi_id] = "sin nombre"
            return None
        self.seen_ids.add(poi_id)

        return Poi(
            id=poi_id,
            name=name,
            category=self._category(record.get("categoria"), poi_id),
            description=self._bilingual_text(record.get("descripcion"), poi_id, "descripcion"),
            coordinates=self._coordinates(record.get("lat"), record.get("lon"), poi_id),
            accessible=self._accessible(record.get("accesible"), poi_id),
            opening_hours=self._opening_hours(record.get("horario"), poi_id),
            price=self._price(record.get("precio"), poi_id),
            tags=_tags(record.get("etiquetas")),
        )

    def _bilingual_text(self, value: JsonValue, poi_id: str, field: str) -> BilingualText:
        """D1 (instrucciones incrustadas) y D9 (traducciones vacías)."""
        raw = value if isinstance(value, dict) else {}
        texts: dict[Language, str] = {}
        for language in Language:
            raw_text = raw.get(language.value)
            clean, removed = strip_embedded_instructions(
                raw_text.strip() if isinstance(raw_text, str) else ""
            )
            for sentence in removed:
                self.report(
                    Defect.EMBEDDED_INSTRUCTION,
                    poi_id,
                    f"{field}.{language.value}",
                    "instrucción dirigida al asistente, eliminada del texto publicado: "
                    f"«{sentence}»",
                )
            texts[language] = clean
        if texts[Language.ES] and not texts[Language.EN]:
            self.report(
                Defect.MISSING_TRANSLATION,
                poi_id,
                f"{field}.en",
                "sin traducción al inglés: se usará el español",
            )
        return BilingualText(es=texts[Language.ES], en=texts[Language.EN] or None)

    def _category(self, value: JsonValue, poi_id: str) -> Category | None:
        """D8: se compara sin tildes ni mayúsculas («Gastronomía» es `gastronomia`)."""
        if not isinstance(value, str) or not value.strip():
            self.report(Defect.VALIDATION, poi_id, "categoria", "sin categoría")
            return None
        category = _CATEGORIES.get(_CATEGORY_SEPARATORS.sub("_", normalize_text(value)))
        if category is None:
            self.report(
                Defect.VALIDATION,
                poi_id,
                "categoria",
                f"categoría no reconocida «{value}»: queda como desconocida",
            )
        return category

    def _coordinates(self, lat: JsonValue, lon: JsonValue, poi_id: str) -> Coordinates | None:
        """Solo comprueba que sean números; rangos y ubicación se validan después (D3)."""
        if (
            isinstance(lat, int | float)
            and isinstance(lon, int | float)
            and _is_number(lat)
            and _is_number(lon)
        ):
            return Coordinates(lat=float(lat), lon=float(lon))
        self.report(
            Defect.VALIDATION,
            poi_id,
            "lat/lon",
            "coordenadas ausentes o no numéricas: desconocidas",
        )
        return None

    def _accessible(self, value: JsonValue, poi_id: str) -> bool | None:
        """D5: solo `true` o `false` son datos; cualquier otra cosa queda como desconocida."""
        if isinstance(value, bool):
            return value
        if value is None:
            detail = "sin datos de accesibilidad: se mantiene como desconocida"
        else:
            detail = f"valor no reconocido «{value}»: se trata como desconocida"
        self.report(Defect.UNKNOWN_ACCESSIBILITY, poi_id, "accesible", detail)
        return None

    def _price(self, value: JsonValue, poi_id: str) -> PriceRange | UnparsedPrice | None:
        """D4: números, «gratis» y rangos «25-35» pasan a euros; otro texto se conserva tal cual."""
        if isinstance(value, int | float) and _is_number(value) and value >= 0:
            return PriceRange(min_eur=float(value), max_eur=float(value))
        if isinstance(value, str) and value.strip():
            price = _price_from_text(value)
            if price is None:
                self.report(
                    Defect.PRICE,
                    poi_id,
                    "precio",
                    f"«{value}» no se puede convertir a euros: se conserva como texto",
                )
                return UnparsedPrice(value.strip())
            self.report(
                Defect.PRICE,
                poi_id,
                "precio",
                f"precio en texto «{value}»: se interpreta como {_describe_price(price)}",
            )
            return price
        if value is None:
            detail = "sin datos de precio: se muestra como desconocido"
        else:
            detail = f"valor no válido «{value}»: se muestra como desconocido"
        self.report(Defect.PRICE, poi_id, "precio", detail)
        return None

    def _opening_hours(self, value: JsonValue, poi_id: str) -> OpeningHours:
        """D6: sin franjas ni `always_open`, el horario es desconocido (no «cerrado siempre»)."""
        raw = value if isinstance(value, dict) else {}
        if raw.get("always_open") is True:
            return OpeningHours(always_open=True)
        raw_slots = raw.get("franjas")
        slots = []
        incomplete = False
        for index, raw_slot in enumerate(raw_slots if isinstance(raw_slots, list) else []):
            slot, complete = self._time_slot(raw_slot, poi_id, f"horario.franjas[{index}]")
            incomplete = incomplete or not complete
            if slot:
                slots.append(slot)
        if not slots:
            self.report(
                Defect.UNKNOWN_OPENING_HOURS,
                poi_id,
                "horario",
                "sin franjas horarias interpretables: apertura desconocida",
            )
        return OpeningHours(always_open=False, slots=tuple(slots), incomplete=incomplete)

    def _time_slot(self, raw: JsonValue, poi_id: str, field: str) -> tuple[TimeSlot | None, bool]:
        """Devuelve la franja (o None si no se puede interpretar) y si se ha leído completa.

        Lo que no se puede interpretar con seguridad se descarta: nunca se adivina. Una franja
        cuyo cierre es anterior a la apertura cruza la medianoche y es válida (20:00-02:00).
        """
        if not isinstance(raw, dict):
            return self._discard_slot(poi_id, field, "no es un objeto")

        raw_days = raw.get("dias")
        raw_days = raw_days if isinstance(raw_days, list) else []
        weekdays = frozenset(day for day in raw_days if _is_iso_weekday(day))
        complete = len(weekdays) == len(raw_days)
        if not complete:
            self.report(Defect.VALIDATION, poi_id, f"{field}.dias", "días fuera de 1 a 7 ignorados")
        if not weekdays:
            return self._discard_slot(poi_id, field, "sin días válidos")

        opens, closes = _hour(raw.get("abre")), _hour(raw.get("cierra"))
        if opens is None or closes is None:
            return self._discard_slot(poi_id, field, "hora de apertura o cierre no válida")
        if closes == opens:
            return self._discard_slot(
                poi_id, field, "abre y cierra a la misma hora: no se sabe si son 0 o 24 horas"
            )

        season = None
        if "temporada" in raw:
            raw_season = raw["temporada"]
            season = _season(raw_season)
            if season is None:
                return self._discard_slot(
                    poi_id, field, f"temporada no interpretable «{raw_season}»"
                )
            self.report(
                Defect.SEASONAL_HOURS,
                poi_id,
                f"{field}.temporada",
                f"solo abre en temporada ({raw_season}): sin fecha, la apertura es desconocida",
            )
        return TimeSlot(weekdays=weekdays, opens=opens, closes=closes, season=season), complete

    def _discard_slot(self, poi_id: str, field: str, reason: str) -> tuple[None, bool]:
        self.report(Defect.VALIDATION, poi_id, field, f"franja descartada: {reason}")
        return None, False

    def _validate_coordinates(self, pois: list[Poi]) -> list[Poi]:
        """D3: rangos geográficos y ubicación respecto al resto de puntos.

        Validar rangos no basta: una longitud española (-3.7) también es una latitud válida. Un
        punto lejos del resto que, con lat/lon intercambiadas, encaja, se corrige; si no hay
        corrección evidente, sus coordenadas quedan como desconocidas. Nunca se inventan.
        """
        valid = [c for poi in pois if (c := poi.coordinates) and _in_range(c)]
        centre = None
        if len(valid) >= MIN_POINTS_FOR_TOWN_CENTRE:
            centre = Coordinates(
                lat=statistics.median(c.lat for c in valid),
                lon=statistics.median(c.lon for c in valid),
            )
        return [self._checked_coordinates(poi, centre) for poi in pois]

    def _checked_coordinates(self, poi: Poi, centre: Coordinates | None) -> Poi:
        current = poi.coordinates
        if current is None:
            return poi
        radius = self.thresholds.town_radius_km
        if centre is None:
            # Sin centro de referencia solo se puede comprobar el rango.
            if _in_range(current):
                return poi
            detail = f"({current.lat}, {current.lon}) fuera de rango: se marcan como desconocidas"
            corrected = None
        elif _in_range(current) and _distance_km(current, centre) <= radius:
            return poi
        else:
            swapped = Coordinates(lat=current.lon, lon=current.lat)
            if _in_range(swapped) and _distance_km(swapped, centre) <= radius:
                detail = (
                    f"latitud y longitud intercambiadas ({current.lat}, {current.lon}): "
                    f"se corrigen a ({swapped.lat}, {swapped.lon})"
                )
                corrected = swapped
            else:
                detail = (
                    f"({current.lat}, {current.lon}) fuera de rango o a más de {radius:g} km del "
                    "resto, sin corrección evidente: se marcan como desconocidas"
                )
                corrected = None
        self.report(Defect.COORDINATES, poi.id, "lat/lon", detail)
        return replace(poi, coordinates=corrected)

    def _remove_duplicates(self, pois: list[Poi]) -> list[Poi]:
        """D2: mismo nombre normalizado y casi el mismo sitio; se conserva el más completo."""
        max_distance = self.thresholds.duplicate_distance_km
        groups: list[list[Poi]] = []
        for poi in pois:
            group = next((g for g in groups if _are_duplicates(g[0], poi, max_distance)), None)
            if group is None:
                groups.append([poi])
            else:
                group.append(poi)

        discarded: set[str] = set()
        for group in groups:
            best = max(group, key=_completeness)  # ante un empate, el primero del catálogo
            for poi in group:
                if poi is best:
                    continue
                discarded.add(poi.id)
                self.excluded[poi.id] = f"duplicado de {best.id}"
                self.report(
                    Defect.DUPLICATE,
                    poi.id,
                    "registro",
                    f"duplicado de {best.id} (mismo nombre en el mismo lugar): se excluye y se "
                    f"conserva {best.id}, que está más completo",
                )
        return [poi for poi in pois if poi.id not in discarded]


def _is_number(value: int | float) -> bool:
    """Excluye booleanos (en Python, `True` es un `int`) y valores no finitos."""
    return not isinstance(value, bool) and math.isfinite(value)


def _is_iso_weekday(value: JsonValue) -> TypeGuard[int]:
    return isinstance(value, int) and not isinstance(value, bool) and value in ISO_WEEKDAYS


def _hour(value: JsonValue) -> time | None:
    match = _HOUR.match(value) if isinstance(value, str) else None
    if not match:
        return None
    hours, minutes = int(match[1]), int(match[2])
    return time(hours, minutes) if hours < 24 and minutes < 60 else None


def _season(value: JsonValue) -> Season | None:
    """Formato «MM-DD/MM-DD», ambos días incluidos."""
    match = _SEASON.match(value) if isinstance(value, str) else None
    if not match:
        return None
    start_month, start_day, end_month, end_day = (int(part) for part in match.groups())
    try:
        date(LEAP_YEAR, start_month, start_day)
        date(LEAP_YEAR, end_month, end_day)
    except ValueError:
        return None
    return Season(start=(start_month, start_day), end=(end_month, end_day))


def _price_from_text(value: str) -> PriceRange | None:
    text = normalize_text(value)
    if text in _FREE_WORDS:
        return PriceRange(min_eur=0.0, max_eur=0.0)
    match = _PRICE_IN_TEXT.match(text)
    if not match:
        return None
    min_eur = float(match[1].replace(",", "."))
    max_eur = float(match[2].replace(",", ".")) if match[2] else min_eur
    return PriceRange(min_eur=min_eur, max_eur=max_eur) if min_eur <= max_eur else None


def _describe_price(price: PriceRange) -> str:
    if price.min_eur == price.max_eur:
        return f"{price.min_eur:g} €"
    return f"de {price.min_eur:g} a {price.max_eur:g} €"


def _tags(value: JsonValue) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(tag.strip() for tag in value if isinstance(tag, str) and tag.strip())


def _in_range(coordinates: Coordinates) -> bool:
    return abs(coordinates.lat) <= MAX_ABS_LATITUDE and abs(coordinates.lon) <= MAX_ABS_LONGITUDE


def _distance_km(a: Coordinates, b: Coordinates) -> float:
    """Distancia sobre la esfera terrestre (fórmula del semiverseno)."""
    lat1, lon1, lat2, lon2 = map(math.radians, (a.lat, a.lon, b.lat, b.lon))
    h = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(min(1.0, h)))


def _are_duplicates(a: Poi, b: Poi, max_distance_km: float) -> bool:
    if a.coordinates is None or b.coordinates is None:
        return False  # sin saber dónde están, no se puede afirmar que sean el mismo lugar
    same_name = normalize_text(a.name.es) == normalize_text(b.name.es)
    return same_name and _distance_km(a.coordinates, b.coordinates) <= max_distance_km


def _completeness(poi: Poi) -> tuple[int, int]:
    """Cuántos campos informativos tiene el registro; desempata la longitud de la descripción."""
    fields = (
        poi.name.en,
        poi.description.en,
        poi.accessible is not None,
        poi.price,
        poi.opening_hours.always_open or poi.opening_hours.slots,
        poi.tags,
        poi.category,
    )
    return sum(bool(field) for field in fields), len(poi.description.es)
