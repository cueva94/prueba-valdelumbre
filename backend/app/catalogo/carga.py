"""Lectura del catálogo original desde disco."""

import json
from pathlib import Path

from app.catalogo.limpieza import limpiar_catalogo
from app.catalogo.modelos import Catalogo


def cargar_catalogo(ruta: Path) -> Catalogo:
    """Lee el JSON original (siempre en UTF-8: en Windows no es la codificación por defecto)."""
    with ruta.open(encoding="utf-8") as fichero:
        registros = json.load(fichero)
    if not isinstance(registros, list):
        raise ValueError(f"{ruta} debe contener una lista de puntos de interés")
    return limpiar_catalogo(registros)
