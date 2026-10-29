import json
from pathlib import Path

from app.catalog.models import Catalog
from app.catalog.normalization import JsonValue, normalize_catalog


class CatalogFormatError(ValueError):
    """El fichero es JSON válido, pero no tiene la forma de un catálogo."""


def load_catalog(path: Path) -> Catalog:
    """Lee el JSON original (siempre en UTF-8: en Windows no es la codificación por defecto)."""
    with path.open(encoding="utf-8") as file:
        records: JsonValue = json.load(file)
    if not isinstance(records, list):
        raise CatalogFormatError(f"{path} debe contener una lista de puntos de interés")
    return normalize_catalog(records)
