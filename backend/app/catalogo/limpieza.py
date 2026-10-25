"""Limpieza del catálogo crudo con reglas generales; cada corrección queda como incidencia.

Ninguna regla menciona ids concretos. Los defectos y las decisiones están en DATOS.md (D1…D9, V).
"""

import math
import re
import statistics
from dataclasses import dataclass, replace
from datetime import date, time
from typing import Any

from app.catalogo.modelos import (
    Catalogo,
    Coordenadas,
    Defecto,
    Franja,
    Horario,
    Incidencia,
    Poi,
    Precio,
    Temporada,
    TextoBilingue,
)
from app.catalogo.texto import normalizar_texto, quitar_instrucciones


@dataclass(frozen=True)
class UmbralesLimpieza:
    """Distancias de las reglas geográficas (DATOS.md → D2 y D3), configurables por parámetro."""

    # Un punto a más de esta distancia del centro del catálogo (la mediana) no está en el pueblo.
    # 10 km es el diámetro aproximado de un municipio español medio (~62 km²); en los datos de
    # la prueba, el punto legítimo más lejano está a 2,6 km del centro.
    radio_zona_km: float = 10.0
    # Dos registros con el mismo nombre normalizado a esta distancia o menos son el mismo lugar.
    # La distancia sola nunca basta: dos sitios distintos pueden estar puerta con puerta.
    distancia_duplicado_km: float = 0.05


UMBRALES_POR_DEFECTO = UmbralesLimpieza()

_HORA = re.compile(r"^(\d{1,2}):(\d{2})$")
_TEMPORADA = re.compile(r"^(\d{2})-(\d{2})/(\d{2})-(\d{2})$")
_NUMERO = r"(\d+(?:[.,]\d+)?)"
# Un número o un rango con guion o guion largo (U+2013): «4,50 €», «25-35», «25 - 35 euros».
_PRECIO_EN_TEXTO = re.compile(rf"^{_NUMERO}(?:\s*[-\u2013]\s*{_NUMERO})?\s*(?:€|eur|euros)?$")
_PALABRAS_GRATIS = {"gratis", "gratuito", "gratuita", "free"}


def limpiar_catalogo(
    registros: list[Any], umbrales: UmbralesLimpieza = UMBRALES_POR_DEFECTO
) -> Catalogo:
    """Aplica todas las reglas y devuelve el catálogo publicable. No modifica `registros`."""
    return _Limpieza(umbrales).ejecutar(registros)


class _Limpieza:
    def __init__(self, umbrales: UmbralesLimpieza) -> None:
        self.umbrales = umbrales
        self.incidencias: list[Incidencia] = []
        self.excluidos: dict[str, str] = {}
        self.ids_vistos: set[str] = set()

    def anotar(self, defecto: Defecto, poi_id: str | None, campo: str, detalle: str) -> None:
        self.incidencias.append(Incidencia(defecto, poi_id, campo, detalle))

    def ejecutar(self, registros: list[Any]) -> Catalogo:
        pois = [poi for i, registro in enumerate(registros) if (poi := self._registro(registro, i))]
        pois = self._corregir_coordenadas(pois)
        pois = self._quitar_duplicados(pois)
        return Catalogo(
            pois=tuple(pois),
            excluidos=dict(self.excluidos),
            incidencias=tuple(self.incidencias),
            registros_leidos=len(registros),
        )

    # --- Registro a registro ---------------------------------------------------------------

    def _registro(self, registro: Any, posicion: int) -> Poi | None:
        if not isinstance(registro, dict):
            self.anotar(
                Defecto.VALIDACION,
                None,
                "registro",
                f"registro {posicion}: no es un objeto, se descarta",
            )
            return None
        poi_id = registro.get("id")
        if not isinstance(poi_id, str) or not poi_id.strip():
            self.anotar(Defecto.VALIDACION, None, "id", f"registro {posicion}: sin id, se descarta")
            return None
        poi_id = poi_id.strip()
        if poi_id in self.ids_vistos:
            self.anotar(Defecto.VALIDACION, poi_id, "id", "id repetido: se descarta esta aparición")
            return None

        nombre = self._texto(registro.get("nombre"), poi_id, "nombre")
        if not nombre.es:
            self.anotar(
                Defecto.VALIDACION, poi_id, "nombre.es", "sin nombre en español: se excluye"
            )
            self.excluidos[poi_id] = "sin nombre"
            return None
        self.ids_vistos.add(poi_id)

        return Poi(
            id=poi_id,
            nombre=nombre,
            categoria=self._categoria(registro.get("categoria"), poi_id),
            descripcion=self._texto(registro.get("descripcion"), poi_id, "descripcion"),
            coordenadas=self._coordenadas(registro.get("lat"), registro.get("lon"), poi_id),
            accesible=self._accesible(registro.get("accesible"), poi_id),
            horario=self._horario(registro.get("horario"), poi_id),
            precio=self._precio(registro.get("precio"), poi_id),
            etiquetas=_etiquetas(registro.get("etiquetas")),
        )

    def _texto(self, valor: Any, poi_id: str, campo: str) -> TextoBilingue:
        """D1 (instrucciones incrustadas) y D9 (traducciones vacías)."""
        crudo = valor if isinstance(valor, dict) else {}
        textos: dict[str, str] = {}
        for idioma in ("es", "en"):
            texto = crudo.get(idioma)
            limpio, eliminadas = quitar_instrucciones(
                texto.strip() if isinstance(texto, str) else ""
            )
            for frase in eliminadas:
                self.anotar(
                    Defecto.INSTRUCCION_INCRUSTADA,
                    poi_id,
                    f"{campo}.{idioma}",
                    f"instrucción dirigida al asistente, eliminada del texto publicado: «{frase}»",
                )
            textos[idioma] = limpio
        if textos["es"] and not textos["en"]:
            self.anotar(
                Defecto.TRADUCCION,
                poi_id,
                f"{campo}.en",
                "sin traducción al inglés: se usará el español",
            )
        return TextoBilingue(es=textos["es"], en=textos["en"] or None)

    def _categoria(self, valor: Any, poi_id: str) -> str | None:
        if isinstance(valor, str) and valor.strip():
            return valor.strip()
        self.anotar(Defecto.VALIDACION, poi_id, "categoria", "sin categoría")
        return None

    def _coordenadas(self, lat: Any, lon: Any, poi_id: str) -> Coordenadas | None:
        if _es_numero(lat) and _es_numero(lon):
            return Coordenadas(lat=float(lat), lon=float(lon))
        self.anotar(
            Defecto.VALIDACION,
            poi_id,
            "lat/lon",
            "coordenadas ausentes o no numéricas: desconocidas",
        )
        return None

    def _accesible(self, valor: Any, poi_id: str) -> bool | None:
        """D5: solo `true` o `false` son datos; cualquier otra cosa queda como desconocida."""
        if isinstance(valor, bool):
            return valor
        if valor is None:
            detalle = "sin datos de accesibilidad: se mantiene como desconocida"
        else:
            detalle = f"valor no reconocido «{valor}»: se trata como desconocida"
        self.anotar(Defecto.ACCESIBILIDAD_DESCONOCIDA, poi_id, "accesible", detalle)
        return None

    def _precio(self, valor: Any, poi_id: str) -> Precio | None:
        """D4: números, «gratis» y rangos «25-35» se normalizan a un rango en euros."""
        if valor is None:
            self.anotar(
                Defecto.PRECIO, poi_id, "precio", "sin datos de precio: se muestra como desconocido"
            )
            return None
        if _es_numero(valor) and valor >= 0:
            return Precio(minimo=float(valor), maximo=float(valor))
        precio = _precio_en_texto(valor) if isinstance(valor, str) else None
        if precio is None:
            self.anotar(
                Defecto.PRECIO,
                poi_id,
                "precio",
                f"valor no interpretable «{valor}»: se muestra como desconocido",
            )
        else:
            self.anotar(
                Defecto.PRECIO,
                poi_id,
                "precio",
                f"precio en texto «{valor}»: se interpreta como {_describir_precio(precio)}",
            )
        return precio

    def _horario(self, valor: Any, poi_id: str) -> Horario:
        """D6: sin franjas ni `always_open`, el horario es desconocido (no «cerrado siempre»)."""
        crudo = valor if isinstance(valor, dict) else {}
        if crudo.get("always_open") is True:
            return Horario(siempre_abierto=True)
        franjas_crudas = crudo.get("franjas")
        franjas = []
        incompleto = False
        for indice, cruda in enumerate(franjas_crudas if isinstance(franjas_crudas, list) else []):
            franja, completa = self._franja(cruda, poi_id, f"horario.franjas[{indice}]")
            incompleto = incompleto or not completa
            if franja:
                franjas.append(franja)
        if not franjas:
            self.anotar(
                Defecto.HORARIO_DESCONOCIDO,
                poi_id,
                "horario",
                "sin franjas horarias interpretables: apertura desconocida",
            )
        return Horario(siempre_abierto=False, franjas=tuple(franjas), incompleto=incompleto)

    def _franja(self, cruda: Any, poi_id: str, campo: str) -> tuple[Franja | None, bool]:
        """Devuelve la franja (o None si no se puede interpretar) y si se ha leído completa.

        Lo que no se puede interpretar con seguridad se descarta: nunca se adivina. Una franja
        cuyo cierre es anterior a la apertura cruza la medianoche y es válida (20:00-02:00).
        """
        if not isinstance(cruda, dict):
            return self._descartar_franja(poi_id, campo, "no es un objeto")

        dias_crudos = cruda.get("dias") if isinstance(cruda.get("dias"), list) else []
        dias = frozenset(d for d in dias_crudos if _es_dia(d))
        completa = len(dias) == len(dias_crudos)
        if not completa:
            self.anotar(
                Defecto.VALIDACION, poi_id, f"{campo}.dias", "días fuera de 1 a 7 ignorados"
            )
        if not dias:
            return self._descartar_franja(poi_id, campo, "sin días válidos")

        abre, cierra = _hora(cruda.get("abre")), _hora(cruda.get("cierra"))
        if abre is None or cierra is None:
            return self._descartar_franja(poi_id, campo, "hora de apertura o cierre no válida")
        if cierra == abre:
            return self._descartar_franja(
                poi_id, campo, "abre y cierra a la misma hora: no se sabe si son 0 o 24 horas"
            )

        temporada = None
        if "temporada" in cruda:
            temporada = _temporada(cruda["temporada"])
            if temporada is None:
                return self._descartar_franja(
                    poi_id, campo, f"temporada no interpretable «{cruda['temporada']}»"
                )
            self.anotar(
                Defecto.TEMPORADA,
                poi_id,
                f"{campo}.temporada",
                f"solo abre en temporada ({cruda['temporada']}): "
                "sin fecha, la apertura es desconocida",
            )
        return Franja(dias=dias, abre=abre, cierra=cierra, temporada=temporada), completa

    def _descartar_franja(self, poi_id: str, campo: str, motivo: str) -> tuple[None, bool]:
        self.anotar(Defecto.VALIDACION, poi_id, campo, f"franja descartada: {motivo}")
        return None, False

    # --- Reglas sobre el catálogo completo -------------------------------------------------

    def _corregir_coordenadas(self, pois: list[Poi]) -> list[Poi]:
        """D3: un punto lejos del resto que, con lat/lon intercambiadas, encaja, se corrige.

        Validar rangos no basta: una longitud española (-3.7) también es una latitud válida.
        """
        conocidas = [poi.coordenadas for poi in pois if poi.coordenadas]
        if len(conocidas) < 3:  # sin suficientes puntos no se puede saber dónde está el pueblo
            return pois
        centro = Coordenadas(
            lat=statistics.median(c.lat for c in conocidas),
            lon=statistics.median(c.lon for c in conocidas),
        )

        radio = self.umbrales.radio_zona_km
        resultado = []
        for poi in pois:
            actual = poi.coordenadas
            if actual is None or _distancia_km(actual, centro) <= radio:
                resultado.append(poi)
                continue
            invertidas = Coordenadas(lat=actual.lon, lon=actual.lat)
            if _en_rango(invertidas) and _distancia_km(invertidas, centro) <= radio:
                detalle = (
                    f"latitud y longitud intercambiadas ({actual.lat}, {actual.lon}): "
                    f"se corrigen a ({invertidas.lat}, {invertidas.lon})"
                )
                corregidas: Coordenadas | None = invertidas
            else:
                detalle = (
                    f"({actual.lat}, {actual.lon}) a más de {radio:g} km del resto y sin "
                    "corrección evidente: se marcan como desconocidas"
                )
                corregidas = None
            self.anotar(Defecto.COORDENADAS, poi.id, "lat/lon", detalle)
            resultado.append(replace(poi, coordenadas=corregidas))
        return resultado

    def _quitar_duplicados(self, pois: list[Poi]) -> list[Poi]:
        """D2: mismo nombre normalizado y casi el mismo sitio; se conserva el más completo."""
        distancia_maxima = self.umbrales.distancia_duplicado_km
        grupos: list[list[Poi]] = []
        for poi in pois:
            grupo = next((g for g in grupos if _son_duplicados(g[0], poi, distancia_maxima)), None)
            if grupo is None:
                grupos.append([poi])
            else:
                grupo.append(poi)

        descartados: set[str] = set()
        for grupo in grupos:
            mejor = max(grupo, key=_completitud)  # ante un empate, el primero del catálogo
            for poi in grupo:
                if poi is mejor:
                    continue
                descartados.add(poi.id)
                self.excluidos[poi.id] = f"duplicado de {mejor.id}"
                self.anotar(
                    Defecto.DUPLICADO,
                    poi.id,
                    "registro",
                    f"duplicado de {mejor.id} (mismo nombre en el mismo lugar): se excluye y se "
                    f"conserva {mejor.id}, que está más completo",
                )
        return [poi for poi in pois if poi.id not in descartados]


# --- Funciones auxiliares sin estado ---------------------------------------------------------


def _es_numero(valor: Any) -> bool:
    return isinstance(valor, int | float) and not isinstance(valor, bool) and math.isfinite(valor)


def _es_dia(valor: Any) -> bool:
    return isinstance(valor, int) and not isinstance(valor, bool) and 1 <= valor <= 7


def _hora(valor: Any) -> time | None:
    coincidencia = _HORA.match(valor) if isinstance(valor, str) else None
    if not coincidencia:
        return None
    horas, minutos = int(coincidencia[1]), int(coincidencia[2])
    return time(horas, minutos) if horas < 24 and minutos < 60 else None


def _temporada(valor: Any) -> Temporada | None:
    """Formato «MM-DD/MM-DD», ambos días incluidos."""
    coincidencia = _TEMPORADA.match(valor) if isinstance(valor, str) else None
    if not coincidencia:
        return None
    mes_inicio, dia_inicio, mes_fin, dia_fin = (int(parte) for parte in coincidencia.groups())
    try:  # 2000 es bisiesto: admite el 29 de febrero
        date(2000, mes_inicio, dia_inicio)
        date(2000, mes_fin, dia_fin)
    except ValueError:
        return None
    return Temporada(inicio=(mes_inicio, dia_inicio), fin=(mes_fin, dia_fin))


def _precio_en_texto(valor: str) -> Precio | None:
    texto = normalizar_texto(valor)
    if texto in _PALABRAS_GRATIS:
        return Precio(minimo=0.0, maximo=0.0)
    coincidencia = _PRECIO_EN_TEXTO.match(texto)
    if not coincidencia:
        return None
    minimo = float(coincidencia[1].replace(",", "."))
    maximo = float(coincidencia[2].replace(",", ".")) if coincidencia[2] else minimo
    return Precio(minimo=minimo, maximo=maximo) if minimo <= maximo else None


def _describir_precio(precio: Precio) -> str:
    if precio.minimo == precio.maximo:
        return f"{precio.minimo:g} €"
    return f"de {precio.minimo:g} a {precio.maximo:g} €"


def _etiquetas(valor: Any) -> tuple[str, ...]:
    if not isinstance(valor, list):
        return ()
    return tuple(e.strip() for e in valor if isinstance(e, str) and e.strip())


def _en_rango(coordenadas: Coordenadas) -> bool:
    return -90 <= coordenadas.lat <= 90 and -180 <= coordenadas.lon <= 180


def _distancia_km(a: Coordenadas, b: Coordenadas) -> float:
    """Distancia sobre la esfera terrestre (fórmula del semiverseno)."""
    lat1, lon1, lat2, lon2 = map(math.radians, (a.lat, a.lon, b.lat, b.lon))
    h = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    )
    return 2 * 6371.0 * math.asin(math.sqrt(min(1.0, h)))


def _son_duplicados(a: Poi, b: Poi, distancia_maxima_km: float) -> bool:
    if a.coordenadas is None or b.coordenadas is None:
        return False  # sin saber dónde están, no se puede afirmar que sean el mismo lugar
    mismo_nombre = normalizar_texto(a.nombre.es) == normalizar_texto(b.nombre.es)
    return mismo_nombre and _distancia_km(a.coordenadas, b.coordenadas) <= distancia_maxima_km


def _completitud(poi: Poi) -> tuple[int, int]:
    """Cuántos campos informativos tiene el registro; desempata la longitud de la descripción."""
    campos = (
        poi.nombre.en,
        poi.descripcion.en,
        poi.accesible is not None,
        poi.precio,
        poi.horario.siempre_abierto or poi.horario.franjas,
        poi.etiquetas,
        poi.categoria,
    )
    return sum(bool(campo) for campo in campos), len(poi.descripcion.es)
