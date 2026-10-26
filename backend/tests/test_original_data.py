"""Los datos originales de la prueba no se modifican (DATOS.md → Principios)."""

import hashlib
from pathlib import Path

import pytest

DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "datos"

ORIGINAL_SHA256 = {
    "pois.json": "5f9d5636e9b019f0ae20bbea70d837dd843b6c7f7396a2a6c48b731065758072",
    "evaluacion.json": "1be49ad076b3262531991e07125fb07510b3da26c7269b3fb94bf3300214edb9",
}


@pytest.mark.parametrize(("file_name", "sha256"), ORIGINAL_SHA256.items())
def test_original_data_is_unchanged(file_name, sha256):
    content = (DATA_DIRECTORY / file_name).read_bytes()

    assert hashlib.sha256(content).hexdigest() == sha256
