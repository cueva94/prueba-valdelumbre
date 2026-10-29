"""Consulta del catálogo normalizado, en memoria: con 18 registros no hace falta base de datos."""

from dataclasses import dataclass
from types import MappingProxyType

from app.catalog.models import Catalog, Category, Poi
from app.catalog.opening_hours import Moment, OpeningStatus, opening_status


@dataclass(frozen=True)
class PoiFilter:
    """Filtros que se combinan entre sí (todos deben cumplirse). `None`: no se filtra por eso."""

    category: Category | None = None
    accessible: bool | None = None
    open_at: Moment | None = None

    def matches(self, poi: Poi) -> bool:
        if self.category is not None and poi.category != self.category:
            return False
        # Una accesibilidad desconocida no cumple ni `accessible=True` ni `accessible=False`.
        if self.accessible is not None and poi.accessible != self.accessible:
            return False
        # Solo cuenta lo que se puede confirmar: un horario desconocido no es «abierto».
        return self.open_at is None or (
            opening_status(poi.opening_hours, self.open_at) is OpeningStatus.OPEN
        )


NO_FILTER = PoiFilter()


class PoiRepository:
    """Acceso de solo lectura al catálogo: es inmutable y seguro de compartir entre peticiones."""

    def __init__(self, catalog: Catalog) -> None:
        self._pois = catalog.pois
        self._by_id = MappingProxyType({poi.id: poi for poi in catalog.pois})

    def get(self, poi_id: str) -> Poi | None:
        """El punto publicado con ese id; None si no existe o se excluyó al normalizar."""
        return self._by_id.get(poi_id)

    def find(self, poi_filter: PoiFilter = NO_FILTER) -> tuple[Poi, ...]:
        return tuple(poi for poi in self._pois if poi_filter.matches(poi))
