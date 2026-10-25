"""Configuración leída del entorno, con valores por defecto para desarrollo local."""

import os
from pathlib import Path

RAIZ_REPOSITORIO = Path(__file__).resolve().parents[2]

RUTA_POIS = Path(os.environ.get("VALDELUMBRE_RUTA_POIS", RAIZ_REPOSITORIO / "datos" / "pois.json"))
