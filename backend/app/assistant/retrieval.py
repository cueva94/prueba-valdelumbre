"""Recuperación: qué puntos del catálogo responden a la pregunta y cuáles se citan.

Un punto está relacionado con la pregunta si encaja con todos sus temas y contiene todas sus
palabras de contenido. Una palabra que no aparece en ningún punto («tirolina») no se puede
verificar: no hay resultados, y la respuesta lo dice en lugar de presentar puntos que no la cumplen.

Las condiciones (accesible, gratis, abierto) se comprueban con los campos estructurados y con la
misma función de horario que GET /pois; un dato desconocido nunca se da por bueno. Las
descripciones solo sirven para encontrar candidatos por sus palabras: no pueden cambiar las
condiciones ni añadir puntos que no estén en el catálogo.
"""

import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from enum import StrEnum

from app.assistant.interpretation import QueryIntent, SearchTerm
from app.assistant.vocabulary import Topic
from app.catalog.models import Poi, PriceRange
from app.catalog.opening_hours import OpeningStatus, opening_status, opening_status_on_day
from app.catalog.text import normalize_text

# Longitud mínima para probar un singular: «mes» no se toma por plural de «me».
MIN_PLURAL_LENGTH = 4
NAME_MATCH_WEIGHT = 2
TEXT_MATCH_WEIGHT = 1

_WORD = re.compile(r"\w+")


class Condition(StrEnum):
    ACCESSIBLE = "accesible"
    FREE = "gratis"
    NOT_ACCESSIBLE = "no accesible"
    NOT_FREE = "no gratis"
    OPEN = "abierto"


@dataclass(frozen=True)
class Candidate:
    """Punto relacionado con lo que se pregunta y cómo queda frente a cada condición."""

    poi: Poi
    relevance: int
    failed: tuple[Condition, ...]  # el dato dice que no la cumple
    unverified: tuple[Condition, ...]  # falta el dato para comprobarla

    @property
    def meets_all_conditions(self) -> bool:
        return not self.failed and not self.unverified


@dataclass(frozen=True)
class RetrievalResult:
    intent: QueryIntent
    candidates: tuple[Candidate, ...]  # relacionados con la pregunta, los más relevantes antes
    unknown_terms: tuple[SearchTerm, ...]  # términos que no aparecen en ningún punto
    names_specific_places: bool  # la pregunta nombra lugares concretos («el castillo»)

    @property
    def matches(self) -> tuple[Poi, ...]:
        return tuple(c.poi for c in self.candidates if c.meets_all_conditions)

    @property
    def near_misses(self) -> tuple[Candidate, ...]:
        return tuple(c for c in self.candidates if not c.meets_all_conditions)

    @property
    def cited(self) -> tuple[Poi, ...]:
        """Los puntos en los que se apoya la respuesta, en el orden en que se mencionan.

        Los que cumplen todo; y, si la pregunta nombra lugares concretos, también esos lugares
        aunque no cumplan, porque la respuesta explica por qué. Una pregunta general («museos
        accesibles») nunca cita los que no cumplen.
        """
        if self.names_specific_places:
            return self.matches + tuple(c.poi for c in self.near_misses)
        return self.matches


@dataclass(frozen=True)
class _SearchablePoi:
    poi: Poi
    words: frozenset[str]  # formas de las palabras de nombre, descripción, etiquetas y categoría
    name_words: frozenset[str]
    padded_text: str  # palabras en orden, entre espacios, para buscar frases (« car park »)
    tags: frozenset[str]


class Retriever:
    """Índice de búsqueda del catálogo, construido una vez. Es inmutable."""

    def __init__(self, pois: Iterable[Poi]) -> None:
        self._index = tuple(_searchable(poi) for poi in pois)

    def retrieve(self, intent: QueryIntent) -> RetrievalResult:
        # Sin nada que buscar, con condiciones contradictorias o buscando lo cerrado, no hay
        # ningún punto en el que apoyarse: la respuesta lo explica.
        if intent.is_empty or intent.contradicts_itself or intent.negates_opening:
            return RetrievalResult(intent, (), (), names_specific_places=False)

        unknown_terms = tuple(
            term for term in intent.terms if not any(_has_term(p, term) for p in self._index)
        )
        # Sin temas ni términos («¿qué está abierto ahora?»), todo el catálogo es candidato.
        related = [
            p
            for p in self._index
            if all(_has_topic(p, t) for t in intent.topics)
            and all(_has_term(p, t) for t in intent.terms)
        ]

        # Si alguna palabra coincide con el nombre de un candidato («el castillo», «el museo del
        # aceite»), la pregunta es sobre ese lugar: la respuesta habla de él aunque no cumpla.
        named = [p for p in related if any(_in_name(p, t) for t in intent.terms)]
        names_specific_places = bool(named)
        if named:
            related = named

        candidates = [_candidate(p, intent) for p in related]
        # Orden estable: a igual relevancia, el orden del catálogo.
        candidates.sort(key=lambda candidate: -candidate.relevance)
        return RetrievalResult(intent, tuple(candidates), unknown_terms, names_specific_places)


def _candidate(searchable: _SearchablePoi, intent: QueryIntent) -> Candidate:
    failed: list[Condition] = []
    unverified: list[Condition] = []
    for condition, verdict in _verdicts(searchable.poi, intent):
        if verdict is False:
            failed.append(condition)
        elif verdict is None:
            unverified.append(condition)
    relevance = sum(
        NAME_MATCH_WEIGHT if _in_name(searchable, term) else TEXT_MATCH_WEIGHT
        for term in intent.terms
        if _has_term(searchable, term)
    )
    return Candidate(searchable.poi, relevance, tuple(failed), tuple(unverified))


def _verdicts(poi: Poi, intent: QueryIntent) -> Iterator[tuple[Condition, bool | None]]:
    """Para cada condición pedida: True (la cumple), False (no) o None (no consta)."""
    if intent.accessible_only:
        yield Condition.ACCESSIBLE, poi.accessible
    if intent.free_only:
        yield Condition.FREE, poi.price.is_free if isinstance(poi.price, PriceRange) else None
    # Las contrarias tampoco suponen nada: sin el dato, «no accesible» y «no gratis» no constan.
    if intent.not_accessible:
        yield Condition.NOT_ACCESSIBLE, None if poi.accessible is None else not poi.accessible
    if intent.not_free:
        is_paid = not poi.price.is_free if isinstance(poi.price, PriceRange) else None
        yield Condition.NOT_FREE, is_paid
    if intent.open_at is not None:
        yield Condition.OPEN, _as_verdict(opening_status(poi.opening_hours, intent.open_at))
    elif intent.open_on is not None:
        day = intent.open_on
        status = opening_status_on_day(poi.opening_hours, day.weekday, day.calendar_date)
        yield Condition.OPEN, _as_verdict(status)


def _as_verdict(status: OpeningStatus) -> bool | None:
    if status is OpeningStatus.UNKNOWN:
        return None
    return status is OpeningStatus.OPEN


def _has_topic(searchable: _SearchablePoi, topic: Topic) -> bool:
    return (
        searchable.poi.category in topic.categories
        or not searchable.tags.isdisjoint(topic.tags)
        or any(f" {keyword} " in searchable.padded_text for keyword in topic.keywords)
    )


def _has_term(searchable: _SearchablePoi, term: SearchTerm) -> bool:
    return not searchable.words.isdisjoint(_forms(term.normalized))


def _in_name(searchable: _SearchablePoi, term: SearchTerm) -> bool:
    return not searchable.name_words.isdisjoint(_forms(term.normalized))


def _searchable(poi: Poi) -> _SearchablePoi:
    texts = [
        poi.name.es,
        poi.name.en or "",
        poi.description.es,
        poi.description.en or "",
        *poi.tags,
        poi.category.replace("_", " ") if poi.category else "",  # «espacio_publico»
    ]
    words = _words(" ".join(texts))
    name_words = _words(f"{poi.name.es} {poi.name.en or ''}")
    return _SearchablePoi(
        poi=poi,
        words=frozenset(form for word in words for form in _forms(word)),
        name_words=frozenset(form for word in name_words for form in _forms(word)),
        padded_text=f" {' '.join(words)} ",
        tags=frozenset(normalize_text(tag) for tag in poi.tags),
    )


def _words(text: str) -> list[str]:
    return _WORD.findall(normalize_text(text))


def _forms(word: str) -> frozenset[str]:
    """La palabra y sus posibles singulares: dos palabras coinciden si comparten alguna forma.

    «museos» → museo, «ascensores» → ascensor, «bridges» → bridge.
    """
    forms = {word}
    if word.endswith("s") and len(word) >= MIN_PLURAL_LENGTH:
        forms.add(word[:-1])
        if word.endswith("es") and len(word) > MIN_PLURAL_LENGTH:
            forms.add(word[:-2])
    return frozenset(forms)
