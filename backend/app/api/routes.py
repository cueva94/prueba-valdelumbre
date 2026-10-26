"""Rutas HTTP. Solo traducen entre HTTP y los servicios: la lógica está en catalog y assistant."""

import re
from datetime import datetime, time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import AfterValidator

from app.api.dependencies import (
    get_assistant,
    get_repository,
    get_town_now,
    only_query_parameters,
)
from app.api.schemas import AskIn, AskOut, ErrorOut, HealthOut, PoiOut
from app.assistant.service import Assistant
from app.catalog.models import Category, Language
from app.catalog.opening_hours import Moment
from app.catalog.repository import PoiFilter, PoiRepository

OPEN_AT_NOW = "ahora"
# Día ISO (1 = lunes … 7 = domingo), «T» y hora local del pueblo: «1T12:00» es lunes a las 12:00.
_OPEN_AT = re.compile(rf"{OPEN_AT_NOW}|[1-7]T([01]\d|2[0-3]):[0-5]\d")


def _validate_open_at(value: str) -> str:
    if not _OPEN_AT.fullmatch(value):
        raise ValueError(
            "usa «ahora» o un día ISO (1 = lunes … 7 = domingo) y una hora HH:MM, por ejemplo "
            "1T12:00 (lunes a las 12:00)"
        )
    return value


router = APIRouter()

RepositoryDep = Annotated[PoiRepository, Depends(get_repository)]
AssistantDep = Annotated[Assistant, Depends(get_assistant)]
NowDep = Annotated[datetime, Depends(get_town_now)]
LanguageQuery = Annotated[
    Language,
    Query(alias="idioma", description="Idioma de los textos. Sin traducción, se usa el español."),
]


@router.get("/health", tags=["sistema"])
def health() -> HealthOut:
    return HealthOut()


@router.get(
    "/pois",
    tags=["puntos de interés"],
    summary="Lista los puntos de interés, con filtros que se combinan",
    dependencies=[Depends(only_query_parameters("categoria", "accesible", "abierto_en", "idioma"))],
)
def list_pois(
    repository: RepositoryDep,
    now: NowDep,
    category: Annotated[Category | None, Query(alias="categoria")] = None,
    accessible: Annotated[
        bool | None,
        Query(
            alias="accesible",
            description="Sin datos de accesibilidad, un punto no aparece ni con true ni con false.",
        ),
    ] = None,
    open_at: Annotated[
        str | None,
        AfterValidator(_validate_open_at),
        Query(
            alias="abierto_en",
            description=(
                "`ahora` (hora de Valdelumbre, Europe/Madrid) o día ISO y hora: `1T12:00` es lunes "
                "a las 12:00. Solo aparecen los que se sabe que están abiertos; sin fecha, los "
                "horarios de temporada no se pueden confirmar."
            ),
            examples=["ahora", "1T12:00"],
        ),
    ] = None,
    language: LanguageQuery = Language.ES,
) -> list[PoiOut]:
    poi_filter = PoiFilter(
        category=category,
        accessible=accessible,
        open_at=_moment(open_at, now) if open_at else None,
    )
    return [PoiOut.from_domain(poi, language) for poi in repository.find(poi_filter)]


@router.get(
    "/pois/{poi_id}",
    tags=["puntos de interés"],
    summary="Ficha de un punto de interés",
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorOut}},
    dependencies=[Depends(only_query_parameters("idioma"))],
)
def get_poi(
    poi_id: str, repository: RepositoryDep, language: LanguageQuery = Language.ES
) -> PoiOut:
    poi = repository.get(poi_id)
    if poi is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=f"No hay ningún punto de interés con id «{poi_id}»"
        )
    return PoiOut.from_domain(poi, language)


@router.post(
    "/preguntar",
    tags=["asistente"],
    summary="Responde una pregunta solo con lo que hay en el catálogo",
)
def ask(body: AskIn, assistant: AssistantDep, now: NowDep) -> AskOut:
    answer = assistant.answer(body.question, body.language, now)
    return AskOut(
        answer=answer.text,
        ids=[poi.id for poi in answer.pois],
        pois=[PoiOut.from_domain(poi, body.language) for poi in answer.pois],
        language=body.language,
    )


def _moment(open_at: str, now: datetime) -> Moment:
    """Convierte `abierto_en`, ya validado, en el momento que se comprueba."""
    if open_at == OPEN_AT_NOW:
        return Moment.from_datetime(now)
    weekday, hour = open_at.split("T")
    return Moment(int(weekday), time.fromisoformat(hour))
