import os
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POIS_PATH = REPOSITORY_ROOT / "datos" / "pois.json"
POIS_PATH_VARIABLE = "VALDELUMBRE_POIS_PATH"

# Los horarios del catálogo son horas locales del pueblo. «Ahora» se calcula siempre en esta
# zona, nunca con la del servidor (los contenedores van en UTC) ni con la del visitante.
TOWN_TIMEZONE = ZoneInfo("Europe/Madrid")


@dataclass(frozen=True)
class Settings:
    pois_path: Path = DEFAULT_POIS_PATH

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(pois_path=Path(os.environ.get(POIS_PATH_VARIABLE, DEFAULT_POIS_PATH)))
