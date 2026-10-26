"""Informe de normalización del catálogo. Uso, desde backend/: python -m app.catalog"""

from app.catalog.loader import load_catalog
from app.config import Settings
from app.console import use_utf8_output


def main() -> None:
    use_utf8_output()
    pois_path = Settings.from_env().pois_path
    catalog = load_catalog(pois_path)
    print(
        f"{pois_path.name}: {catalog.records_read} registros leídos · "
        f"publicados: {len(catalog.pois)} · excluidos: {len(catalog.excluded)}"
    )
    for poi_id, reason in catalog.excluded.items():
        print(f"  excluido {poi_id}: {reason}")

    print(f"\nIncidencias ({len(catalog.incidents)}), por punto de interés:")
    for incident in sorted(catalog.incidents, key=lambda i: (i.poi_id or "", i.defect)):
        origin = f"{incident.poi_id or '-':<8} {incident.defect:<3} {incident.field:<28}"
        print(f"  {origin} {incident.detail}")


if __name__ == "__main__":
    main()
