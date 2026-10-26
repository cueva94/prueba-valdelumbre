"""Fixtures compartidas: la API con el catálogo real y un reloj fijo."""

from collections.abc import Iterator
from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import get_town_now
from app.config import TOWN_TIMEZONE
from app.main import create_app

# Lunes 26 de octubre de 2026 a las 12:00 en Valdelumbre: fuera de la temporada de baño.
FIXED_NOW = datetime(2026, 10, 26, 12, 0, tzinfo=TOWN_TIMEZONE)


def with_fixed_clock(app: FastAPI) -> FastAPI:
    app.dependency_overrides[get_town_now] = lambda: FIXED_NOW
    return app


@pytest.fixture(scope="session")
def client() -> Iterator[TestClient]:
    with TestClient(with_fixed_clock(create_app())) as test_client:
        yield test_client
