"""Los datos originales de la prueba no se modifican (DATOS.md → Principios)."""

import hashlib
from pathlib import Path

import pytest

DIRECTORIO_DATOS = Path(__file__).resolve().parents[2] / "datos"

HUELLAS_ORIGINALES = {
    "pois.json": "5f9d5636e9b019f0ae20bbea70d837dd843b6c7f7396a2a6c48b731065758072",
    "evaluacion.json": "1be49ad076b3262531991e07125fb07510b3da26c7269b3fb94bf3300214edb9",
}


@pytest.mark.parametrize(("fichero", "huella"), HUELLAS_ORIGINALES.items())
def test_datos_originales_sin_modificar(fichero, huella):
    contenido = (DIRECTORIO_DATOS / fichero).read_bytes()

    assert hashlib.sha256(contenido).hexdigest() == huella
