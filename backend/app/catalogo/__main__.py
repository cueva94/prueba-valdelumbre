"""Informe de limpieza del catálogo. Uso, desde backend/: python -m app.catalogo"""

import sys

from app.catalogo.carga import cargar_catalogo
from app.config import RUTA_POIS


def main() -> None:
    # En Windows, la salida redirigida (tuberías, Git Bash) no usa UTF-8 por defecto.
    sys.stdout.reconfigure(encoding="utf-8")
    catalogo = cargar_catalogo(RUTA_POIS)
    print(
        f"{RUTA_POIS.name}: {catalogo.registros_leidos} registros leídos · "
        f"publicados: {len(catalogo.pois)} · excluidos: {len(catalogo.excluidos)}"
    )
    for poi_id, motivo in catalogo.excluidos.items():
        print(f"  excluido {poi_id}: {motivo}")

    print(f"\nIncidencias ({len(catalogo.incidencias)}), por punto de interés:")
    for incidencia in sorted(catalogo.incidencias, key=lambda i: (i.poi_id or "", i.defecto)):
        origen = f"{incidencia.poi_id or '-':<8} {incidencia.defecto:<3} {incidencia.campo:<28}"
        print(f"  {origen} {incidencia.detalle}")


if __name__ == "__main__":
    main()
