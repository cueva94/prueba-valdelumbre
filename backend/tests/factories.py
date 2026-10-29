"""Registros crudos sintéticos para probar las reglas sin depender del catálogo real."""

import math

from app.catalog.normalization import JsonValue

# Centro aproximado de los datos de la prueba; los registros sintéticos se sitúan cerca.
TOWN_LAT, TOWN_LON = 40.417, -3.705

# Con la Tierra como esfera de 6371 km de radio, un grado de latitud mide siempre lo mismo.
KM_PER_DEGREE_OF_LATITUDE = 2 * math.pi * 6371.0 / 360


def latitude_at(km_north: float) -> float:
    return TOWN_LAT + km_north / KM_PER_DEGREE_OF_LATITUDE


def record(**changes: JsonValue) -> dict[str, JsonValue]:
    """Un registro crudo válido y completo; `changes` sustituye los campos indicados."""
    base: dict[str, JsonValue] = {
        "id": "poi-test",
        "nombre": {"es": "Sitio de prueba", "en": "Test place"},
        "categoria": "museo",
        "descripcion": {"es": "Descripción del sitio.", "en": "Description of the place."},
        "lat": TOWN_LAT,
        "lon": TOWN_LON,
        "accesible": True,
        "horario": {"always_open": True, "franjas": []},
        "precio": 0,
        "etiquetas": ["historia"],
    }
    return base | changes


def neighbours() -> list[JsonValue]:
    """Cuatro registros en cruz a ~100 m del centro (TOWN_LAT, TOWN_LON).

    Con ellos, la mediana del catálogo es exactamente el centro aunque se añada un quinto
    punto en cualquier sitio: permite situar ese punto a una distancia exacta del centro.
    """
    offsets = [(0.001, 0.0), (-0.001, 0.0), (0.0, 0.001), (0.0, -0.001)]
    return [
        record(
            id=f"poi-neighbour-{i}",
            nombre={"es": f"Vecino {i}", "en": f"Neighbour {i}"},
            lat=TOWN_LAT + d_lat,
            lon=TOWN_LON + d_lon,
        )
        for i, (d_lat, d_lon) in enumerate(offsets)
    ]
