"""Consulta del catálogo: filtros individuales y combinados, y registros inexistentes."""

from collections.abc import Iterable
from datetime import time

import pytest

from app.catalog.models import Category, Poi
from app.catalog.normalization import JsonValue, normalize_catalog
from app.catalog.opening_hours import Moment
from app.catalog.repository import PoiFilter, PoiRepository
from tests.factories import record

MONDAY = 1
MORNING_ONLY: JsonValue = {
    "always_open": False,
    "franjas": [{"dias": [1], "abre": "09:00", "cierra": "13:00"}],
}

# Nombres distintos y lugares distintos para que ninguna regla de duplicados intervenga.
REPOSITORY = PoiRepository(
    normalize_catalog(
        [
            record(id="museum-yes", nombre={"es": "Museo A"}, lat=40.4171, accesible=True),
            record(id="museum-no", nombre={"es": "Museo B"}, lat=40.4172, accesible=False),
            record(id="museum-unknown", nombre={"es": "Museo C"}, lat=40.4173, accesible=None),
            record(
                id="route-morning",
                nombre={"es": "Ruta D"},
                lat=40.4174,
                categoria="ruta",
                horario=MORNING_ONLY,
            ),
            record(
                id="route-no-hours",
                nombre={"es": "Ruta E"},
                lat=40.4175,
                categoria="ruta",
                horario={"always_open": False, "franjas": []},
            ),
        ]
    )
)


def ids(pois: Iterable[Poi]) -> list[str]:
    return [poi.id for poi in pois]


def test_without_filters_returns_everything_in_catalog_order():
    assert ids(REPOSITORY.find()) == [
        "museum-yes",
        "museum-no",
        "museum-unknown",
        "route-morning",
        "route-no-hours",
    ]


def test_filter_by_category():
    assert ids(REPOSITORY.find(PoiFilter(category=Category.ROUTE))) == [
        "route-morning",
        "route-no-hours",
    ]


@pytest.mark.parametrize(
    ("accessible", "expected"),
    [
        (True, ["museum-yes", "route-morning", "route-no-hours"]),
        (False, ["museum-no"]),  # la accesibilidad desconocida no cuenta como «no accesible»
    ],
)
def test_filter_by_accessibility_never_guesses_unknown_values(accessible, expected):
    assert ids(REPOSITORY.find(PoiFilter(accessible=accessible))) == expected


def test_filter_by_opening_excludes_closed_and_unknown():
    at_10 = Moment(MONDAY, time(10))
    at_15 = Moment(MONDAY, time(15))

    open_at_10 = ids(REPOSITORY.find(PoiFilter(open_at=at_10)))
    open_at_15 = ids(REPOSITORY.find(PoiFilter(open_at=at_15)))

    assert "route-morning" in open_at_10
    assert "route-morning" not in open_at_15
    assert "route-no-hours" not in open_at_10  # horario desconocido: no se afirma que abra


def test_filters_are_combined():
    poi_filter = PoiFilter(
        category=Category.ROUTE, accessible=True, open_at=Moment(MONDAY, time(10))
    )

    assert ids(REPOSITORY.find(poi_filter)) == ["route-morning"]


def test_get_returns_none_for_unknown_and_excluded_ids():
    duplicated = PoiRepository(
        normalize_catalog([record(id="kept"), record(id="dropped", precio=None)])
    )

    assert duplicated.get("kept") is not None
    assert duplicated.get("dropped") is None  # excluido por duplicado
    assert duplicated.get("does-not-exist") is None
