"""Script de evaluación: criterio de acierto, las seis preguntas oficiales y, aparte, las preguntas
de regresión internas."""

import json
import threading
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
import uvicorn
from fastapi.testclient import TestClient

from app.catalog.models import Language
from app.evaluation import (
    DEFAULT_CASES_PATH,
    EXIT_ALL_PASSED,
    EXIT_CANNOT_RUN,
    EXIT_SOME_FAILED,
    Asker,
    EvaluationCase,
    evaluate,
    is_correct,
    load_cases,
    main,
    report,
)
from app.main import create_app
from tests.conftest import with_fixed_clock

# Preguntas escritas durante el desarrollo, no proporcionadas con la prueba. Son tests de regresión
# del asistente, no parte de la evaluación: la evaluación son las seis de datos/evaluacion.json.
REGRESSION_QUESTIONS_PATH = Path(__file__).parent / "data" / "regression_questions.json"
SERVER_START_TIMEOUT_SECONDS = 10


def case(include: tuple[str, ...] = (), exclude: tuple[str, ...] = ()) -> EvaluationCase:
    return EvaluationCase(
        id="c",
        idioma=Language.ES,
        pregunta="?",
        esperado_incluye=include,
        esperado_excluye=exclude,
    )


@pytest.mark.parametrize(
    ("expected", "obtained", "passed"),
    [
        (case(include=("a", "b")), ["a", "b", "c"], True),  # citar más de lo esperado vale
        (case(include=("a", "b")), ["a"], False),
        (case(include=("a",), exclude=("x",)), ["a", "x"], False),
        (case(exclude=("x",)), ["a"], True),
        (case(exclude=("x",)), [], True),
        (case(), [], True),  # sin respuesta en el catálogo: no se cita nada
        (case(), ["a"], False),
    ],
)
def test_success_criterion(expected, obtained, passed):
    assert is_correct(expected, obtained) is passed


def test_reads_the_six_official_questions():
    cases = load_cases(DEFAULT_CASES_PATH)

    assert [c.id for c in cases] == ["q1", "q2", "q3", "q4", "q5", "q6"]
    assert cases[1].language is Language.EN


def asker(client: TestClient) -> Asker:
    def ask(question: str, language: Language) -> list[str]:
        response = client.post("/preguntar", json={"pregunta": question, "idioma": language})
        response.raise_for_status()
        ids: list[str] = response.json()["ids"]
        return ids

    return ask


def test_the_six_official_questions_pass(client):
    results = evaluate(load_cases(DEFAULT_CASES_PATH), asker(client))

    failed = [result.case.id for result in results if not result.passed]
    assert failed == []


def test_official_questions_cite_exactly_what_the_catalog_supports(client):
    """Más estricto que el criterio oficial (`is_correct`), que no se cambia.

    El enunciado no dice cómo se puntúa. El criterio oficial deja citar puntos de más y, si una
    pregunta solo tiene excluidos (q5), da por buena una respuesta vacía. Aquí se exige el
    conjunto exacto que respalda el catálogo; donde hay un filtro equivalente, sale de GET /pois.
    """

    def listed(path: str) -> list[str]:
        return [poi["id"] for poi in client.get(path).json()]

    expected = {
        "q1": listed("/pois?categoria=museo&accesible=true"),
        "q2": ["poi-007", "poi-012"],  # con niños y al aire libre: la ruta y el parque
        "q3": listed("/pois?abierto_en=1T12:00"),
        "q4": ["poi-008"],
        "q5": listed("/pois?accesible=true"),  # premisa falsa: todos los accesibles
        "q6": [],
    }
    results = evaluate(load_cases(DEFAULT_CASES_PATH), asker(client))

    assert {result.case.id: list(result.obtained) for result in results} == expected
    assert expected["q5"]  # una respuesta vacía no basta para q5


def test_internal_regression_questions_pass(client):
    results = evaluate(load_cases(REGRESSION_QUESTIONS_PATH), asker(client))

    failed = [result.case.id for result in results if not result.passed]
    assert failed == []


def test_report_shows_each_question_and_the_total(client):
    results = evaluate(load_cases(DEFAULT_CASES_PATH), asker(client))

    text = report(results)

    assert "q6 [es] ACIERTO" in text
    assert "obtenidos: poi-008" in text
    assert text.endswith("Aciertos: 6/6 (100 %)")


def test_cli_fails_clearly_when_the_api_is_not_running(capsys):
    exit_code = main(["--url", "http://127.0.0.1:9"])

    assert exit_code == EXIT_CANNOT_RUN
    assert "No se puede ejecutar la evaluación" in capsys.readouterr().err


@pytest.fixture(scope="module")
def api_url() -> Iterator[str]:
    """La API real escuchando por HTTP en un puerto libre, como la usa el comando del README."""
    config = uvicorn.Config(
        with_fixed_clock(create_app()), host="127.0.0.1", port=0, log_level="warning"
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + SERVER_START_TIMEOUT_SECONDS
    while not server.started:
        if not thread.is_alive() or time.monotonic() > deadline:
            pytest.fail("La API de prueba no ha arrancado")
        time.sleep(0.01)
    port = server.servers[0].sockets[0].getsockname()[1]
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    thread.join()


def test_cli_evaluates_the_official_questions_over_http(api_url, capsys):
    # El mismo camino que `python -m app.evaluation`: HTTP real, no TestClient.
    exit_code = main(["--url", api_url])

    assert exit_code == EXIT_ALL_PASSED
    assert capsys.readouterr().out.rstrip().endswith("Aciertos: 6/6 (100 %)")


def test_cli_exit_code_reports_a_failed_question(api_url, tmp_path, capsys):
    impossible = {
        "id": "x1",
        "idioma": "es",
        "pregunta": "¿Hay algún sitio con tirolina?",
        "esperado_incluye": ["poi-001"],
        "esperado_excluye": [],
    }
    cases = tmp_path / "casos.json"
    cases.write_text(json.dumps([impossible]), encoding="utf-8")

    # Con la barra final, como al copiar la URL del navegador.
    exit_code = main(["--url", f"{api_url}/", "--casos", str(cases)])

    assert exit_code == EXIT_SOME_FAILED
    assert "x1 [es] FALLO" in capsys.readouterr().out
