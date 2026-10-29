import json

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response

from app.api.dependencies import get_town_now
from app.config import TOWN_TIMEZONE, Settings
from app.main import create_app
from tests.conftest import with_fixed_clock
from tests.factories import record

ACCESSIBLE = {
    "poi-002",
    "poi-003",
    "poi-005",
    "poi-008",
    "poi-009",
    "poi-010",
    "poi-012",
    "poi-015",
    "poi-016",
    "poi-017",
}


def ids(response: Response) -> list[str]:
    return [poi["id"] for poi in response.json()]


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"estado": "ok"}


def test_list_returns_the_published_catalog_without_the_duplicate(client):
    response = client.get("/pois")

    assert response.status_code == 200
    assert len(response.json()) == 17
    assert "poi-004" not in ids(response)


def test_poi_contract(client):
    poi = next(p for p in client.get("/pois").json() if p["id"] == "poi-001")

    assert set(poi) == {
        "id",
        "nombre",
        "categoria",
        "descripcion",
        "coordenadas",
        "accesible",
        "horario",
        "precio",
        "etiquetas",
    }
    assert poi["nombre"] == {"texto": "Castillo de Valdelumbre", "idioma": "es"}
    assert poi["precio"] == {"tipo": "rango", "minimo": 4.5, "maximo": 4.5}
    assert poi["horario"]["franjas"][0] == {
        "dias": [1, 2, 3, 4, 5, 6],
        "abre": "10:00",
        "cierra": "14:00",
        "temporada": None,
    }


def test_filter_by_category(client):
    assert ids(client.get("/pois", params={"categoria": "museo"})) == [
        "poi-003",
        "poi-013",
        "poi-015",
    ]


def test_filter_by_accessibility_leaves_unknown_out_of_both_answers(client):
    accessible = set(ids(client.get("/pois", params={"accesible": "true"})))
    not_accessible = set(ids(client.get("/pois", params={"accesible": "false"})))

    assert accessible == ACCESSIBLE
    assert "poi-011" not in accessible | not_accessible  # accesibilidad desconocida


def test_filter_open_at_weekday_and_hour(client):
    open_monday_noon = set(ids(client.get("/pois", params={"abierto_en": "1T12:00"})))

    assert {"poi-001", "poi-002", "poi-005", "poi-006", "poi-010"} <= open_monday_noon
    # Cerrados los lunes, horario desconocido (poi-018) o temporada sin fecha (poi-014).
    assert open_monday_noon.isdisjoint({"poi-003", "poi-015", "poi-008", "poi-018", "poi-014"})


def test_filter_open_now_uses_the_town_clock(client):
    # El reloj fijo es lunes a las 12:00, en octubre: la poza (temporada de verano) está cerrada.
    now = ids(client.get("/pois", params={"abierto_en": "ahora"}))

    assert now == ids(client.get("/pois", params={"abierto_en": "1T12:00"}))
    assert "poi-014" not in now


def test_now_is_the_town_time_not_the_server_time():
    # Los demás tests fijan el reloj; este comprueba el real (los contenedores van en UTC).
    assert get_town_now().tzinfo == TOWN_TIMEZONE


def test_filters_are_combined(client):
    response = client.get(
        "/pois", params={"categoria": "monumento", "accesible": "false", "abierto_en": "1T12:00"}
    )

    assert ids(response) == ["poi-001", "poi-006"]


def test_texts_in_english(client):
    poi = client.get("/pois/poi-001", params={"idioma": "en"}).json()

    assert poi["nombre"] == {"texto": "Valdelumbre Castle", "idioma": "en"}


def test_missing_translation_falls_back_to_spanish_and_says_so(tmp_path):
    catalog_file = tmp_path / "pois.json"
    catalog_file.write_text(json.dumps([record(nombre={"es": "Solo en español", "en": ""})]))
    app = with_fixed_clock(create_app(Settings(pois_path=catalog_file)))

    with TestClient(app) as client:
        poi = client.get("/pois", params={"idioma": "en"}).json()[0]

    assert poi["nombre"] == {"texto": "Solo en español", "idioma": "es"}


@pytest.mark.parametrize(
    "params",
    [
        {"categoria": "museos"},
        {"accesible": "quizas"},
        {"idioma": "fr"},
        {"abierto_en": "lunes 12:00"},
        {"abierto_en": "8T12:00"},
        {"abierto_en": "1T24:00"},
        {"abierto_en": "1T9:00"},
        {"categoría": "museo"},  # con tilde: parámetro desconocido, no se ignora
    ],
)
def test_invalid_parameters_are_rejected_with_422(client, params):
    response = client.get("/pois", params=params)

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["query", next(iter(params))]


def test_repeated_parameters_are_rejected_instead_of_keeping_one(client):
    response = client.get("/pois", params=[("categoria", "museo"), ("categoria", "ruta")])

    assert response.status_code == 422
    error = response.json()["detail"][0]
    assert (error["type"], error["loc"]) == ("multiple_values", ["query", "categoria"])


def test_get_poi_returns_normalized_data(client):
    poi = client.get("/pois/poi-011").json()

    assert poi["coordenadas"] == {"lat": 40.421, "lon": -3.711}  # corregidas (D3)
    assert poi["accesible"] is None  # desconocida (D5)


def test_unparseable_hours_are_exposed_as_unknown(client):
    hours = client.get("/pois/poi-018").json()["horario"]

    assert hours == {"siempre_abierto": False, "franjas": [], "incompleto": False}


def test_seasonal_hours_contract(client):
    slot = client.get("/pois/poi-014").json()["horario"]["franjas"][0]

    assert slot["temporada"] == {"inicio": "06-01", "fin": "09-30"}  # MM-DD, ambos incluidos


def test_a_price_that_is_not_an_amount_is_published_as_text(tmp_path):
    catalog_file = tmp_path / "pois.json"
    catalog_file.write_text(json.dumps([record(precio="consultar en taquilla")]))
    app = with_fixed_clock(create_app(Settings(pois_path=catalog_file)))

    with TestClient(app) as client:
        poi = client.get("/pois/poi-test").json()

    assert poi["precio"] == {"tipo": "texto", "texto": "consultar en taquilla"}


@pytest.mark.parametrize("poi_id", ["poi-004", "poi-999"])
def test_unknown_or_excluded_poi_returns_404(client, poi_id):
    response = client.get(f"/pois/{poi_id}")

    assert response.status_code == 404
    assert response.json() == {"detail": f"No hay ningún punto de interés con id «{poi_id}»"}


def test_ask_contract(client):
    response = client.post(
        "/preguntar", json={"pregunta": "¿Dónde puedo probar vino?", "idioma": "es"}
    )

    body = response.json()
    assert response.status_code == 200
    assert set(body) == {"respuesta", "ids", "pois", "idioma"}
    assert body["ids"] == ["poi-008"]
    assert [poi["id"] for poi in body["pois"]] == body["ids"]
    assert "Bodega La Encina" in body["respuesta"]


def test_ask_defaults_to_spanish(client):
    body = client.post("/preguntar", json={"pregunta": "museos"}).json()

    assert body["idioma"] == "es"


def test_ask_accepts_a_question_of_the_maximum_length(client):
    # La caja de la pantalla admite hasta 500 caracteres: la API tiene que aceptarlos todos.
    assert client.post("/preguntar", json={"pregunta": "x" * 500}).status_code == 200


@pytest.mark.parametrize(
    "payload",
    [
        {"pregunta": ""},
        {"pregunta": "   "},
        {"pregunta": "x" * 501},
        {"idioma": "es"},
        {"pregunta": "museos", "idioma": "fr"},
        {"pregunta": "museos", "question": "otro campo"},
    ],
)
def test_ask_rejects_invalid_requests_with_422(client, payload):
    assert client.post("/preguntar", json=payload).status_code == 422


def test_openapi_documents_the_contract_names(client):
    schemas = client.get("/openapi.json").json()["components"]["schemas"]

    assert set(schemas["AskIn"]["properties"]) == {"pregunta", "idioma"}
    assert set(schemas["AskOut"]["properties"]) == {"respuesta", "ids", "pois", "idioma"}
    assert "abierto_en" in json.dumps(client.get("/openapi.json").json()["paths"]["/pois"])
