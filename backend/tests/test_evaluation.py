"""Script de evaluación: criterio de acierto, las seis preguntas oficiales y, aparte, las preguntas
de regresión internas."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.catalog.models import Language
from app.evaluation import (
    DEFAULT_CASES_PATH,
    EXIT_CANNOT_RUN,
    Asker,
    EvaluationCase,
    evaluate,
    is_correct,
    load_cases,
    main,
    report,
)

# Preguntas escritas durante el desarrollo, no proporcionadas con la prueba. Son tests de regresión
# del asistente, no parte de la evaluación: la evaluación son las seis de datos/evaluacion.json.
REGRESSION_QUESTIONS_PATH = Path(__file__).parent / "data" / "regression_questions.json"


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
