"""Interpretación de la pregunta: qué temas pide y qué condiciones deben cumplirse.

Es determinista y no consulta el catálogo: solo traduce el texto a restricciones. «Ahora» se
recibe como parámetro para que el resultado no dependa del reloj.
"""

import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, time

from app.assistant.vocabulary import (
    ACCESSIBILITY_TRIGGERS,
    CONDITION_CONNECTORS,
    FREE_TRIGGERS,
    HOURS_TRIGGERS,
    NEGATION_VERBS,
    NEGATIONS,
    NOON,
    NOON_TRIGGERS,
    NOT_ACCESSIBLE_TRIGGERS,
    NOT_FREE_TRIGGERS,
    NOW_TRIGGERS,
    OPEN_TRIGGERS,
    PRICE_TRIGGERS,
    STOPWORDS,
    TODAY_TRIGGERS,
    TOPICS,
    UNIQUENESS_TRIGGERS,
    WEEKDAYS,
    Topic,
)
from app.catalog.opening_hours import Moment
from app.catalog.text import normalize_text

MIN_TERM_LENGTH = 3
HOURS_PER_HALF_DAY = 12

_WORD = re.compile(r"\w+")
# «12:00», «a las 12», «a las 9 h», «at 5 pm», «5pm», «12h». Un número suelto («7 km») no es
# una hora: hace falta «a las»/«at», minutos o un sufijo.
_TIME = re.compile(
    r"(?<![\w:])(?:(?P<prefix>a las|at)\s+)?(?P<hour>\d{1,2})"
    r"(?::(?P<minute>\d{2})|\s*(?P<suffix>am|pm|h)\b)?(?![\w:])"
)


@dataclass(frozen=True)
class DayQuery:
    """«¿Qué abre el domingo?»: un día sin hora concreta."""

    weekday: int
    calendar_date: date | None = None


@dataclass(frozen=True)
class SearchTerm:
    """Palabra de la pregunta que no es vocabulario conocido: se busca tal cual en el catálogo."""

    normalized: str
    original: str


@dataclass(frozen=True)
class QueryIntent:
    topics: tuple[Topic, ...]
    terms: tuple[SearchTerm, ...]
    accessible_only: bool
    free_only: bool
    not_accessible: bool  # «no accesible»: accesible es false (no basta con que no conste)
    not_free: bool  # «no gratis»: precio conocido mayor que cero
    negates_opening: bool  # «¿qué no abre…?»: buscar lo cerrado no está soportado
    open_at: Moment | None
    open_at_is_now: bool  # el momento es «ahora»: la respuesta dice qué hora se ha usado
    open_on: DayQuery | None
    asks_for_hours: bool
    asks_for_price: bool
    presumes_single_result: bool

    @property
    def has_conditions(self) -> bool:
        return (
            self.accessible_only
            or self.free_only
            or self.not_accessible
            or self.not_free
            or self.open_at is not None
            or self.open_on is not None
        )

    @property
    def contradicts_itself(self) -> bool:
        return (self.accessible_only and self.not_accessible) or (self.free_only and self.not_free)

    @property
    def is_empty(self) -> bool:
        return not (self.topics or self.terms or self.has_conditions)


def interpret_question(question: str, now: datetime) -> QueryIntent:
    text = _Text(normalize_text(question))

    topics = tuple(topic for topic in TOPICS if text.take(topic.triggers))
    # Las negaciones, antes que las condiciones: si no, «no accesibles» se leería como «accesibles».
    not_accessible = text.take(NOT_ACCESSIBLE_TRIGGERS) | text.take_negated(ACCESSIBILITY_TRIGGERS)
    accessible_only = text.take(ACCESSIBILITY_TRIGGERS)
    not_free = text.take(NOT_FREE_TRIGGERS) | text.take_negated(FREE_TRIGGERS)
    free_only = text.take(FREE_TRIGGERS)
    asks_for_hours = text.take(HOURS_TRIGGERS)
    asks_for_price = text.take(PRICE_TRIGGERS)
    presumes_single_result = text.take(UNIQUENESS_TRIGGERS)
    negates_opening = text.take_negated(OPEN_TRIGGERS)
    asks_if_open = text.take(OPEN_TRIGGERS)
    asks_for_now = text.take(NOW_TRIGGERS)
    asks_for_today = text.take(TODAY_TRIGGERS)
    weekday = text.take_weekday()
    hour = NOON if text.take(NOON_TRIGGERS) else text.take_time()

    when = _when(
        now,
        weekday=weekday,
        hour=hour,
        now_requested=asks_for_now,
        today_requested=asks_for_today,
        open_requested=asks_if_open and not asks_for_hours,
    )
    return QueryIntent(
        topics=topics,
        terms=_search_terms(text.remaining_words(), question),
        accessible_only=accessible_only,
        free_only=free_only,
        not_accessible=not_accessible,
        not_free=not_free,
        negates_opening=negates_opening,
        open_at=when.open_at,
        open_at_is_now=when.is_now,
        open_on=when.open_on,
        asks_for_hours=asks_for_hours,
        asks_for_price=asks_for_price,
        presumes_single_result=presumes_single_result,
    )


@dataclass(frozen=True)
class _When:
    open_at: Moment | None = None
    open_on: DayQuery | None = None
    is_now: bool = False


def _when(
    now: datetime,
    *,
    weekday: int | None,
    hour: time | None,
    now_requested: bool,
    today_requested: bool,
    open_requested: bool,
) -> _When:
    """Momento (día y hora) o día sin hora por el que se pregunta, de lo más a lo menos explícito.

    Un día de la semana sin más («un lunes») no tiene fecha, así que las temporadas quedan sin
    confirmar. Una hora sin día se entiende como hoy, en la hora del pueblo. «Hoy» sin hora es
    todo el día; «¿está abierto?» sin decir cuándo, ahora.
    """
    today = Moment.from_datetime(now)
    if weekday is not None and hour is not None:
        return _When(open_at=Moment(weekday, hour))
    if weekday is not None:
        return _When(open_on=DayQuery(weekday))
    if hour is not None:
        return _When(open_at=Moment(today.weekday, hour, today.calendar_date))
    if now_requested:
        return _When(open_at=today, is_now=True)
    if today_requested:
        return _When(open_on=DayQuery(today.weekday, today.calendar_date))
    if open_requested:
        return _When(open_at=today, is_now=True)
    return _When()


def _search_terms(words: Iterable[str], question: str) -> tuple[SearchTerm, ...]:
    """Palabras con contenido, sin repetir, con su forma original para citarlas en la respuesta."""
    originals = {normalize_text(word): word for word in reversed(_WORD.findall(question))}
    terms: dict[str, SearchTerm] = {}
    for word in words:
        if len(word) >= MIN_TERM_LENGTH and not word.isdigit() and word not in STOPWORDS:
            terms.setdefault(word, SearchTerm(word, originals.get(word, word)))
    return tuple(terms.values())


class _Text:
    """Texto normalizado de la pregunta del que se van retirando las partes ya reconocidas.

    Así una misma palabra no cuenta dos veces (la «a las» de una hora no es un término de
    búsqueda) y lo que queda al final son los términos que se buscan tal cual.
    """

    def __init__(self, normalized: str) -> None:
        self._remaining = normalized

    def take(self, phrases: frozenset[str]) -> bool:
        """Retira las frases que aparezcan como palabras completas; dice si había alguna."""
        return self._take_pattern(_alternatives(phrases))

    def take_negated(self, phrases: frozenset[str]) -> bool:
        """Retira una condición negada y las que la sigan encadenadas; dice si había alguna.

        «no son accesibles», «sin accesibilidad», «not wheelchair accessible», «no accesible
        para silla de ruedas». La negación tiene que ir justo antes: en «¿no hay museos
        accesibles?» no niega la accesibilidad.
        """
        condition = _alternatives(phrases)
        chained = rf"(?:\s+(?:(?:{_alternatives(CONDITION_CONNECTORS)})\s+)?(?:{condition}))*"
        return self._take_pattern(
            rf"(?:{_alternatives(NEGATIONS)})\s+(?:(?:{_alternatives(NEGATION_VERBS)})\s+)?"
            rf"(?:{condition}){chained}"
        )

    def _take_pattern(self, pattern: str) -> bool:
        self._remaining, count = re.subn(rf"(?<!\w)(?:{pattern})(?!\w)", " ", self._remaining)
        return count > 0

    def take_weekday(self) -> int | None:
        for word in _WORD.findall(self._remaining):
            if word in WEEKDAYS:
                self.take(frozenset({word}))
                return WEEKDAYS[word]
        return None

    def take_time(self) -> time | None:
        for match in _TIME.finditer(self._remaining):
            if not (match["prefix"] or match["minute"] or match["suffix"]):
                continue
            hour = _to_time(match["hour"], match["minute"], match["suffix"])
            if hour is not None:
                self._remaining = (
                    self._remaining[: match.start()] + " " + self._remaining[match.end() :]
                )
                return hour
        return None

    def remaining_words(self) -> list[str]:
        return _WORD.findall(self._remaining)


def _alternatives(phrases: frozenset[str]) -> str:
    """Alternativas de una expresión regular, las más largas primero: así «silla de ruedas» no se
    queda en «silla»."""
    return "|".join(re.escape(p) for p in sorted(phrases, key=len, reverse=True))


def _to_time(hour_text: str, minute_text: str | None, suffix: str | None) -> time | None:
    hour, minute = int(hour_text), int(minute_text or 0)
    if suffix == "pm" and hour < HOURS_PER_HALF_DAY:
        hour += HOURS_PER_HALF_DAY
    elif suffix == "am" and hour == HOURS_PER_HALF_DAY:
        hour = 0
    if hour > 23 or minute > 59:
        return None
    return time(hour, minute)
