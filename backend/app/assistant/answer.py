"""Redacción de la respuesta a partir de lo recuperado, en español o en inglés.

El redactor solo pone en palabras un `RetrievalResult`: no decide qué puntos se citan ni puede
añadir ninguno. Un redactor basado en un LLM tendría que cumplir la misma interfaz
(`AnswerWriter`) y recibir lo mismo; los ids seguirían saliendo de la recuperación.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import time
from typing import Protocol

from app.assistant.retrieval import Candidate, Condition, RetrievalResult
from app.assistant.vocabulary import WEEKDAY_NAMES
from app.catalog.models import Language, OpeningHours, Poi, PriceRange, TimeSlot, UnparsedPrice
from app.catalog.opening_hours import Moment

# Con más resultados, la lista solo lleva nombres: el detalle está en las fichas.
MAX_DETAILED_RESULTS = 3
MIN_WEEKDAYS_FOR_RANGE = 3
ALL_WEEKDAYS = frozenset(range(1, 8))


class AnswerWriter(Protocol):
    def write(self, result: RetrievalResult, language: Language) -> str: ...


@dataclass(frozen=True)
class _Phrases:
    nothing_understood: str
    contradictory: str  # «accesibles y no accesibles»
    negated_opening: str  # «¿qué no abre el lunes?»
    unknown_terms: str
    no_matches: str
    one_match: str
    many_matches: str
    not_unique: str
    about_named_places: str
    unverified_one: str
    unverified_many: str
    open_now: str
    open_at: str
    open_at_with_date: str
    open_on: str
    accessible: str
    free: str
    not_accessible: str
    not_free: str
    failed: Mapping[Condition, str]
    unverified: Mapping[Condition, str]
    unverified_reason: Mapping[Condition, str]
    closed_that_day: str  # «¿abre el domingo?»: un día sin hora
    unverified_that_day: str
    always_open: str
    hours_unknown: str
    hours_incomplete: str
    slot: str
    season: str
    every_day: str
    weekday_range: str
    hours_label: str
    price_label: str
    price_free: str
    price_range: str
    price_unknown: str
    spanish_only: str
    list_and: str
    list_or: str
    quote: str


_PHRASES = {
    Language.ES: _Phrases(
        nothing_understood=(
            "No he encontrado en tu pregunta nada que pueda buscar en el catálogo. Puedes "
            "preguntar por tipos de lugar (museos, monumentos, rutas…), por lugares accesibles "
            "o gratuitos, o por lo que está abierto un día y a una hora."
        ),
        contradictory=(
            "Me pides a la vez que sea {conditions} y que no lo sea, así que no puedo recomendarte "
            "nada. Dime cuál de las dos cosas buscas."
        ),
        negated_opening=(
            "No puedo buscar lugares por lo que no abren o están cerrados. Pregúntame qué está "
            "abierto un día y a una hora."
        ),
        unknown_terms=(
            "El catálogo no tiene información sobre {terms}, así que no puedo recomendarte "
            "nada sobre eso."
        ),
        no_matches=(
            "No he encontrado en el catálogo ningún lugar que cumpla todo lo que pides "
            "({criteria})."
        ),
        one_match="Según el catálogo, este lugar cumple lo que pides ({criteria}):",
        many_matches="Según el catálogo, estos {count} lugares cumplen lo que pides ({criteria}):",
        not_unique="No hay un único lugar que cumpla eso: según el catálogo, son {count}:",
        about_named_places="Según el catálogo:",
        unverified_one="De 1 lugar más no consta {reasons}, así que no lo incluyo.",
        unverified_many="De {count} lugares más no consta {reasons}, así que no los incluyo.",
        open_now="abierto ahora, {weekday} {date} a las {time}",
        open_at="abierto el {weekday} a las {time}",
        open_at_with_date="abierto el {weekday} {date} a las {time}",
        open_on="abierto el {weekday}",
        accessible="accesible",
        free="gratis",
        not_accessible="no accesible",
        not_free="de pago",
        failed={
            Condition.ACCESSIBLE: "no es accesible",
            Condition.FREE: "no es gratis",
            Condition.NOT_ACCESSIBLE: "es accesible",
            Condition.NOT_FREE: "es gratis",
            Condition.OPEN: "está cerrado en ese momento",
        },
        unverified={
            Condition.ACCESSIBLE: "no consta si es accesible",
            Condition.FREE: "no consta el precio",
            Condition.NOT_ACCESSIBLE: "no consta si es accesible",
            Condition.NOT_FREE: "no consta el precio",
            Condition.OPEN: "no consta si abre en ese momento",
        },
        unverified_reason={
            Condition.ACCESSIBLE: "si es accesible",
            Condition.FREE: "el precio",
            Condition.NOT_ACCESSIBLE: "si es accesible",
            Condition.NOT_FREE: "el precio",
            Condition.OPEN: "el horario",
        },
        closed_that_day="no abre ese día",
        unverified_that_day="no consta si abre ese día",
        always_open="abierto siempre",
        hours_unknown="no consta",
        hours_incomplete=" (incompleto)",
        slot="{days} de {opens} a {closes}{season}",
        season=" (del {start} al {end})",
        every_day="todos los días",
        weekday_range="de {first} a {last}",
        hours_label="Horario",
        price_label="Precio",
        price_free="gratis",
        price_range="de {min} a {max} €",
        price_unknown="no consta",
        spanish_only=" (solo disponible en español)",
        list_and=" y ",
        list_or=" ni ",
        quote="«{}»",
    ),
    Language.EN: _Phrases(
        nothing_understood=(
            "I couldn't find anything in your question that I can look up in the catalogue. You "
            "can ask about types of place (museums, monuments, walks…), accessible or free "
            "places, or what is open on a given day and time."
        ),
        contradictory=(
            "You're asking for places that are both {conditions} and not {conditions}, so I can't "
            "recommend anything. Tell me which one you mean."
        ),
        negated_opening=(
            "I can't search for places by when they are closed. Ask me what is open on a given day "
            "and time."
        ),
        unknown_terms=(
            "The catalogue has no information about {terms}, so I can't recommend anything "
            "about that."
        ),
        no_matches="I couldn't find any place in the catalogue that meets everything ({criteria}).",
        one_match="According to the catalogue, this place meets your request ({criteria}):",
        many_matches=(
            "According to the catalogue, these {count} places meet your request ({criteria}):"
        ),
        not_unique="There isn't just one place: according to the catalogue, there are {count}:",
        about_named_places="According to the catalogue:",
        unverified_one="For 1 more place the catalogue doesn't state {reasons}, so I left it out.",
        unverified_many=(
            "For {count} more places the catalogue doesn't state {reasons}, so I left them out."
        ),
        open_now="open now, {weekday} {date} at {time}",
        open_at="open on {weekday} at {time}",
        open_at_with_date="open on {weekday} {date} at {time}",
        open_on="open on {weekday}",
        accessible="accessible",
        free="free",
        not_accessible="not accessible",
        not_free="not free",
        failed={
            Condition.ACCESSIBLE: "is not accessible",
            Condition.FREE: "is not free",
            Condition.NOT_ACCESSIBLE: "is accessible",
            Condition.NOT_FREE: "is free",
            Condition.OPEN: "is closed at that time",
        },
        unverified={
            Condition.ACCESSIBLE: "the catalogue doesn't state whether it is accessible",
            Condition.FREE: "the catalogue doesn't state the price",
            Condition.NOT_ACCESSIBLE: "the catalogue doesn't state whether it is accessible",
            Condition.NOT_FREE: "the catalogue doesn't state the price",
            Condition.OPEN: "the catalogue doesn't state whether it is open at that time",
        },
        unverified_reason={
            Condition.ACCESSIBLE: "whether they are accessible",
            Condition.FREE: "the price",
            Condition.NOT_ACCESSIBLE: "whether they are accessible",
            Condition.NOT_FREE: "the price",
            Condition.OPEN: "the opening hours",
        },
        closed_that_day="is not open that day",
        unverified_that_day="the catalogue doesn't state whether it opens that day",
        always_open="always open",
        hours_unknown="not available",
        hours_incomplete=" (incomplete)",
        slot="{days} from {opens} to {closes}{season}",
        season=" (from {start} to {end})",
        every_day="every day",
        weekday_range="{first} to {last}",
        hours_label="Opening hours",
        price_label="Price",
        price_free="free",
        price_range="{min}\u2013{max} €",
        price_unknown="not available",
        spanish_only=" (only available in Spanish)",
        list_and=" and ",
        list_or=" or ",
        quote="“{}”",
    ),
}


class TemplateAnswerWriter:
    """Redactor determinista con plantillas: sin red, sin coste y fácil de probar."""

    def write(self, result: RetrievalResult, language: Language) -> str:
        return _Composer(result, language).compose()


class _Composer:
    def __init__(self, result: RetrievalResult, language: Language) -> None:
        self.result = result
        self.intent = result.intent
        self.language = language
        self.phrases = _PHRASES[language]

    def compose(self) -> str:
        if self.intent.is_empty:
            return self.phrases.nothing_understood
        if self.intent.negates_opening:
            return self.phrases.negated_opening
        if self.intent.contradicts_itself:
            return self.phrases.contradictory.format(conditions=self._contradicted())
        matches = self.result.matches
        lines = [self._opening(matches)]
        lines += [
            self._match_line(poi, detailed=len(matches) <= MAX_DETAILED_RESULTS) for poi in matches
        ]
        if self.result.names_specific_places:
            lines += [self._near_miss_line(candidate) for candidate in self.result.near_misses]
        else:
            lines += self._unverified_note()
        return "\n".join(line for line in lines if line)

    def _opening(self, matches: tuple[Poi, ...]) -> str:
        p = self.phrases
        if not matches:
            if self.result.names_specific_places:
                return p.about_named_places
            if self.result.unknown_terms:
                quoted = [p.quote.format(term.original) for term in self.result.unknown_terms]
                return p.unknown_terms.format(terms=_join(quoted, p.list_or))
            return p.no_matches.format(criteria=self._criteria())
        if self.intent.presumes_single_result and len(matches) > 1:
            return p.not_unique.format(count=len(matches))
        if self.result.names_specific_places and not self.intent.has_conditions:
            return p.about_named_places
        if len(matches) == 1:
            return p.one_match.format(criteria=self._criteria())
        return p.many_matches.format(count=len(matches), criteria=self._criteria())

    def _criteria(self) -> str:
        p = self.phrases
        parts = [topic.label(self.language) for topic in self.intent.topics]
        parts += [p.quote.format(term.original) for term in self.intent.terms]
        if self.intent.accessible_only:
            parts.append(p.accessible)
        if self.intent.free_only:
            parts.append(p.free)
        if self.intent.not_accessible:
            parts.append(p.not_accessible)
        if self.intent.not_free:
            parts.append(p.not_free)
        parts += self._when()
        return "; ".join(parts)

    def _contradicted(self) -> str:
        """Las condiciones que se piden a la vez en positivo y en negativo: «accesible»."""
        p = self.phrases
        conditions = []
        if self.intent.accessible_only and self.intent.not_accessible:
            conditions.append(p.accessible)
        if self.intent.free_only and self.intent.not_free:
            conditions.append(p.free)
        return _join(conditions, p.list_and)

    def _when(self) -> list[str]:
        p = self.phrases
        moment = self.intent.open_at
        if moment is not None:
            values = {
                "weekday": self._weekday(moment.weekday),
                "time": _hh_mm(moment.time_of_day),
                "date": _dd_mm(moment),
            }
            if self.intent.open_at_is_now:
                return [p.open_now.format(**values)]
            template = p.open_at_with_date if moment.calendar_date else p.open_at
            return [template.format(**values)]
        if self.intent.open_on is not None:
            return [p.open_on.format(weekday=self._weekday(self.intent.open_on.weekday))]
        return []

    def _match_line(self, poi: Poi, *, detailed: bool) -> str:
        name = poi.name.in_language(self.language).text
        details = []
        if detailed:
            description = poi.description.in_language(self.language)
            spanish_only = (
                self.phrases.spanish_only if description.language != self.language else ""
            )
            details.append(f"{description.text}{spanish_only}")
        details += self._requested_facts(poi)
        return f"- {name}: {' '.join(details)}" if details else f"- {name}"

    def _requested_facts(self, poi: Poi) -> list[str]:
        p = self.phrases
        facts = []
        if self.intent.asks_for_hours:
            facts.append(f"{p.hours_label}: {self._hours(poi.opening_hours)}.")
        if self.intent.asks_for_price:
            facts.append(f"{p.price_label}: {self._price(poi.price)}.")
        return facts

    def _near_miss_line(self, candidate: Candidate) -> str:
        p = self.phrases
        name = candidate.poi.name.in_language(self.language).text
        reasons = [self._reason(c, failed=True) for c in candidate.failed]
        reasons += [self._reason(c, failed=False) for c in candidate.unverified]
        facts = " ".join(self._requested_facts(candidate.poi))
        return f"- {name}: {_join(reasons, p.list_and)}." + (f" {facts}" if facts else "")

    def _reason(self, condition: Condition, *, failed: bool) -> str:
        p = self.phrases
        if condition is Condition.OPEN and self.intent.open_on is not None:
            return p.closed_that_day if failed else p.unverified_that_day
        return p.failed[condition] if failed else p.unverified[condition]

    def _unverified_note(self) -> list[str]:
        """Cuántos lugares encajan pero no se pueden confirmar, sin citarlos."""
        unverified = [c for c in self.result.near_misses if c.unverified and not c.failed]
        if not unverified:
            return []
        conditions = list(dict.fromkeys(c for cand in unverified for c in cand.unverified))
        reasons = _join([self.phrases.unverified_reason[c] for c in conditions], " / ")
        if len(unverified) == 1:
            return [self.phrases.unverified_one.format(reasons=reasons)]
        return [self.phrases.unverified_many.format(count=len(unverified), reasons=reasons)]

    def _hours(self, hours: OpeningHours) -> str:
        p = self.phrases
        if hours.always_open:
            return p.always_open
        if not hours.slots:
            return p.hours_unknown
        slots = "; ".join(self._slot(slot) for slot in hours.slots)
        return slots + (p.hours_incomplete if hours.incomplete else "")

    def _slot(self, slot: TimeSlot) -> str:
        p = self.phrases
        season = ""
        if slot.season is not None:
            start, end = slot.season.start, slot.season.end
            season = p.season.format(
                start=f"{start[1]:02d}/{start[0]:02d}", end=f"{end[1]:02d}/{end[0]:02d}"
            )
        return p.slot.format(
            days=self._weekdays(slot.weekdays),
            opens=_hh_mm(slot.opens),
            closes=_hh_mm(slot.closes),
            season=season,
        )

    def _weekdays(self, weekdays: frozenset[int]) -> str:
        """«todos los días», «de lunes a sábado» o «sábado y domingo»."""
        if weekdays == ALL_WEEKDAYS:
            return self.phrases.every_day
        ordered = sorted(weekdays)
        is_run = ordered == list(range(ordered[0], ordered[-1] + 1))
        if is_run and len(ordered) >= MIN_WEEKDAYS_FOR_RANGE:
            return self.phrases.weekday_range.format(
                first=self._weekday(ordered[0]), last=self._weekday(ordered[-1])
            )
        return _join([self._weekday(day) for day in ordered], self.phrases.list_and)

    def _price(self, price: PriceRange | UnparsedPrice | None) -> str:
        p = self.phrases
        if isinstance(price, UnparsedPrice):
            return price.text
        if price is None:
            return p.price_unknown
        if price.is_free:
            return p.price_free
        if price.min_eur == price.max_eur:
            return f"{self._euros(price.min_eur)} €"
        return p.price_range.format(min=self._euros(price.min_eur), max=self._euros(price.max_eur))

    def _euros(self, amount: float) -> str:
        text = f"{amount:g}"
        return text.replace(".", ",") if self.language is Language.ES else text

    def _weekday(self, weekday: int) -> str:
        return WEEKDAY_NAMES[self.language][weekday - 1]


def _join(items: list[str], last_separator: str) -> str:
    """«a, b y c»."""
    if len(items) <= 1:
        return "".join(items)
    return f"{', '.join(items[:-1])}{last_separator}{items[-1]}"


def _hh_mm(value: time) -> str:
    return f"{value:%H:%M}"


def _dd_mm(moment: Moment) -> str:
    return f"{moment.calendar_date:%d/%m}" if moment.calendar_date else ""
