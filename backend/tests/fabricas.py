"""Registros crudos sintéticos para probar las reglas sin depender del catálogo real."""

from typing import Any

# Centro aproximado de los datos de la prueba; los registros sintéticos se sitúan cerca.
LAT_PUEBLO, LON_PUEBLO = 40.417, -3.705


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


def vecinos(cantidad: int) -> list[dict[str, Any]]:
    """Registros distintos repartidos a pocos cientos de metros: definen dónde está el pueblo."""
    return [
        registro(
            id=f"poi-vecino-{i}",
            nombre={"es": f"Vecino {i}", "en": f"Neighbour {i}"},
            lat=LAT_PUEBLO + i * 0.001,
            lon=LON_PUEBLO - i * 0.001,
        )
        for i in range(cantidad)
    ]
