"""Pasa preguntas de evaluación contra POST /preguntar y cuenta cuántas acierta.

Por defecto usa las seis preguntas oficiales de la prueba (datos/evaluacion.json), que son la
evaluación que pide el enunciado. Uso, desde backend/ con la API arrancada:

    python -m app.evaluation                                   # las seis preguntas oficiales
    python -m app.evaluation --url http://localhost:8080/api   # a través del proxy de la pantalla

`--casos` admite otro fichero con el mismo formato.

Con Docker Compose: docker compose exec api python -m app.evaluation
"""

import argparse
import json
import sys
import urllib.request
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError

from app.catalog.models import Language
from app.config import REPOSITORY_ROOT
from app.console import use_utf8_output

DEFAULT_URL = "http://localhost:8000"
DEFAULT_CASES_PATH = REPOSITORY_ROOT / "datos" / "evaluacion.json"
REQUEST_TIMEOUT_SECONDS = 10.0
EXIT_ALL_PASSED, EXIT_SOME_FAILED, EXIT_CANNOT_RUN = 0, 1, 2

# Recibe la pregunta y el idioma y devuelve los ids citados.
type Asker = Callable[[str, Language], list[str]]


class EvaluationCase(BaseModel):
    """Una pregunta de evaluación, con el formato de datos/evaluacion.json."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    language: Language = Field(alias="idioma")
    question: str = Field(alias="pregunta")
    must_include: tuple[str, ...] = Field(alias="esperado_incluye")
    must_exclude: tuple[str, ...] = Field(alias="esperado_excluye")


class _AskResponseIds(BaseModel):
    ids: list[str]


_CASES = TypeAdapter(list[EvaluationCase])


@dataclass(frozen=True)
class CaseResult:
    case: EvaluationCase
    obtained: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return is_correct(self.case, self.obtained)


def is_correct(case: EvaluationCase, obtained_ids: Sequence[str]) -> bool:
    """Acierto: cita todos los esperados y ninguno de los excluidos.

    Si la pregunta no espera ni excluye ninguno (el catálogo no tiene la respuesta), solo
    acierta si no cita ninguno: de lo contrario, citar cualquier cosa contaría como acierto.
    """
    obtained = set(obtained_ids)
    if not case.must_include and not case.must_exclude:
        return not obtained
    return set(case.must_include) <= obtained and obtained.isdisjoint(case.must_exclude)


def load_cases(path: Path) -> list[EvaluationCase]:
    return _CASES.validate_json(path.read_bytes())


def evaluate(cases: Sequence[EvaluationCase], ask: Asker) -> list[CaseResult]:
    return [CaseResult(case, tuple(ask(case.question, case.language))) for case in cases]


def http_asker(base_url: str) -> Asker:
    """Pregunta a una API en marcha por HTTP, solo con la biblioteca estándar."""
    if urlparse(base_url).scheme not in {"http", "https"}:
        raise ValueError(f"URL no válida: {base_url}")
    endpoint = f"{base_url.rstrip('/')}/preguntar"

    def ask(question: str, language: Language) -> list[str]:
        body = json.dumps({"pregunta": question, "idioma": language}).encode()
        request = urllib.request.Request(
            endpoint, data=body, headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return _AskResponseIds.model_validate_json(response.read()).ids

    return ask


def report(results: Sequence[CaseResult]) -> str:
    lines = []
    for result in results:
        case = result.case
        verdict = "ACIERTO" if result.passed else "FALLO"
        lines += [
            f"{case.id} [{case.language}] {verdict}  {case.question}",
            f"    esperados: {_ids(case.must_include)} · excluidos: {_ids(case.must_exclude)}",
            f"    obtenidos: {_ids(result.obtained)}",
        ]
    passed = sum(result.passed for result in results)
    percentage = 100 * passed / len(results) if results else 0
    lines.append(f"\nAciertos: {passed}/{len(results)} ({percentage:.0f} %)")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evalúa POST /preguntar con preguntas de prueba.")
    parser.add_argument("--url", default=DEFAULT_URL, help=f"URL de la API ({DEFAULT_URL})")
    parser.add_argument(
        "--casos",
        type=Path,
        default=DEFAULT_CASES_PATH,
        help="Fichero de preguntas (JSON). Por defecto, las seis oficiales: datos/evaluacion.json",
    )
    arguments = parser.parse_args(argv)
    use_utf8_output()

    try:
        cases = load_cases(arguments.casos)
        results = evaluate(cases, http_asker(arguments.url))
    except (OSError, ValidationError, ValueError) as error:
        # OSError incluye URLError (API no disponible) y un fichero de casos inexistente.
        print(f"No se puede ejecutar la evaluación: {error}", file=sys.stderr)
        return EXIT_CANNOT_RUN

    print(report(results))
    return EXIT_ALL_PASSED if all(result.passed for result in results) else EXIT_SOME_FAILED


def _ids(ids: Sequence[str]) -> str:
    return ", ".join(ids) if ids else "—"


if __name__ == "__main__":
    sys.exit(main())
