"""Dependencias de las rutas: servicios de la aplicación, reloj y validación de parámetros."""

from collections.abc import Callable
from datetime import datetime

from fastapi import Request
from fastapi.exceptions import RequestValidationError

from app.assistant.service import Assistant
from app.catalog.repository import PoiRepository
from app.config import TOWN_TIMEZONE


def get_repository(request: Request) -> PoiRepository:
    repository = request.app.state.repository
    if not isinstance(repository, PoiRepository):
        raise TypeError("La aplicación no tiene catálogo: créala con app.main.create_app()")
    return repository


def get_assistant(request: Request) -> Assistant:
    assistant = request.app.state.assistant
    if not isinstance(assistant, Assistant):
        raise TypeError("La aplicación no tiene asistente: créala con app.main.create_app()")
    return assistant


def get_town_now() -> datetime:
    """Hora actual en el pueblo. Los tests la sustituyen para que «ahora» sea fijo."""
    return datetime.now(TOWN_TIMEZONE)


def only_query_parameters(*allowed: str) -> Callable[[Request], None]:
    """Rechaza parámetros desconocidos (`?categoría=museo`, con tilde) o repetidos
    (`?categoria=museo&categoria=ruta`) en lugar de ignorarlos o quedarse con uno.

    Cualquiera de las dos cosas daría un resultado silenciosamente incorrecto: el catálogo sin
    filtrar o filtrado por un solo valor sin avisar.
    """

    def check(request: Request) -> None:
        params = request.query_params
        errors = [
            {
                "type": "extra_forbidden",
                "loc": ("query", name),
                "msg": f"Parámetro no admitido. Admitidos: {', '.join(allowed)}",
                "input": params[name],
            }
            for name in params
            if name not in allowed
        ] + [
            {
                "type": "multiple_values",
                "loc": ("query", name),
                "msg": "Parámetro repetido: indica un solo valor",
                "input": params.getlist(name),
            }
            for name in params
            if name in allowed and len(params.getlist(name)) > 1
        ]
        if errors:
            raise RequestValidationError(errors)

    return check
