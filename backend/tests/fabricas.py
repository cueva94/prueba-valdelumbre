"""Registros crudos sintéticos para probar las reglas sin depender del catálogo real."""

import math
from typing import Any

# Centro aproximado de los datos de la prueba; los registros sintéticos se sitúan cerca.
LAT_PUEBLO, LON_PUEBLO = 40.417, -3.705

# Con la Tierra como esfera de 6371 km de radio, un grado de latitud mide siempre lo mismo.
KM_POR_GRADO_DE_LATITUD = 2 * math.pi * 6371.0 / 360


def latitud_a(km_al_norte: float) -> float:
    """Latitud del punto situado exactamente a esa distancia al norte del centro."""
    return LAT_PUEBLO + km_al_norte / KM_POR_GRADO_DE_LATITUD


def registro(**cambios: Any) -> dict[str, Any]:
    """Un registro crudo válido y completo; `cambios` sustituye los campos indicados."""
    base: dict[str, Any] = {
        "id": "poi-prueba",
        "nombre": {"es": "Sitio de prueba", "en": "Test place"},
        "categoria": "museo",
        "descripcion": {"es": "Descripción del sitio.", "en": "Description of the place."},
        "lat": LAT_PUEBLO,
        "lon": LON_PUEBLO,
        "accesible": True,
        "horario": {"always_open": True, "franjas": []},
        "precio": 0,
        "etiquetas": ["historia"],
    }
    return base | cambios


def vecinos() -> list[dict[str, Any]]:
    """Cuatro registros en cruz a ~100 m del centro (LAT_PUEBLO, LON_PUEBLO).

    Con ellos, la mediana del catálogo es exactamente el centro aunque se añada un quinto
    punto en cualquier sitio: permite situar ese punto a una distancia exacta del centro.
    """
    desplazamientos = [(0.001, 0.0), (-0.001, 0.0), (0.0, 0.001), (0.0, -0.001)]
    return [
        registro(
            id=f"poi-vecino-{i}",
            nombre={"es": f"Vecino {i}", "en": f"Neighbour {i}"},
            lat=LAT_PUEBLO + d_lat,
            lon=LON_PUEBLO + d_lon,
        )
        for i, (d_lat, d_lon) in enumerate(desplazamientos)
    ]
