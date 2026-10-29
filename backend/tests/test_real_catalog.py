"""Efecto de la normalización sobre los datos reales.

Las reglas se prueban de forma general en test_normalization.py; aquí se documenta qué hacen con
el catálogo entregado y que cada defecto produce su incidencia.
"""

from datetime import time

import pytest

from app.catalog.loader import load_catalog
from app.catalog.models import Category, Coordinates, Defect, PriceRange
from app.catalog.opening_hours import Moment, OpeningStatus, opening_status
from app.config import Settings


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(Settings().pois_path)


@pytest.fixture(scope="module")
def pois(catalog):
    return {poi.id: poi for poi in catalog.pois}


def test_17_of_18_are_published_and_the_duplicate_is_excluded(catalog):
    assert catalog.records_read == 18
    assert len(catalog.pois) == 17
    assert catalog.excluded == {"poi-004": "duplicado de poi-003"}


def test_every_defect_in_the_inventory_produces_its_incident(catalog):
    # D8 no genera incidencias: es la normalización que se usa al comparar y buscar.
    expected = {
        Defect.EMBEDDED_INSTRUCTION,
        Defect.DUPLICATE,
        Defect.COORDINATES,
        Defect.PRICE,
        Defect.UNKNOWN_ACCESSIBILITY,
        Defect.UNKNOWN_OPENING_HOURS,
        Defect.SEASONAL_HOURS,
        Defect.MISSING_TRANSLATION,
    }

    assert {incident.defect for incident in catalog.incidents} == expected


def test_loading_twice_gives_the_same_catalog_and_incidents(catalog):
    assert load_catalog(Settings().pois_path) == catalog


def test_d1_only_the_record_with_the_instruction_loses_text(catalog, pois):
    affected = {i.poi_id for i in catalog.incidents if i.defect == Defect.EMBEDDED_INSTRUCTION}

    assert affected == {"poi-013"}
    assert pois["poi-013"].description.es == "Colección de tapices flamencos."
    assert pois["poi-013"].accessible is False


def test_d3_swapped_coordinates_are_fixed(pois):
    assert pois["poi-011"].coordinates == Coordinates(lat=40.421, lon=-3.711)


def test_d4_prices_in_text(pois):
    assert pois["poi-003"].price == PriceRange(0, 0)
    assert pois["poi-009"].price == PriceRange(25, 35)
    assert pois["poi-016"].price is None


def test_d5_d6_unknown_stays_unknown(pois):
    assert pois["poi-011"].accessible is None
    monday_noon = Moment(1, time(12))
    assert opening_status(pois["poi-018"].opening_hours, monday_noon) == OpeningStatus.UNKNOWN


def test_d8_every_published_category_is_recognised(pois):
    assert all(isinstance(poi.category, Category) for poi in pois.values())


def test_text_is_read_as_utf8(pois):
    assert pois["poi-006"].name.es == "Iglesia de San Bartolomé"
