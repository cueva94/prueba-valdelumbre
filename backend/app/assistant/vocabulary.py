"""Vocabulario bilingüe del asistente: qué palabras de una pregunta corresponden a qué datos.

Es la única pieza que hay que ampliar para que el asistente entienda más formas de preguntar.
Todo se escribe ya normalizado (minúsculas y sin tildes), como el texto con el que se compara.
"""

from dataclasses import dataclass
from datetime import time
from types import MappingProxyType

from app.catalog.models import Category, Language


def _terms(text: str) -> frozenset[str]:
    """«museo, museos, aire libre» → {"museo", "museos", "aire libre"}."""
    return frozenset(term.strip() for term in text.split(",") if term.strip())


@dataclass(frozen=True)
class Topic:
    """Algo que se puede pedir («museos», «con niños»).

    Un punto encaja si tiene alguna de las categorías o etiquetas, o si alguna de las palabras
    clave aparece en su nombre o descripción. Las descripciones son datos no confiables: solo
    sirven para encontrar candidatos, nunca para decidir accesibilidad, horario o precio.
    """

    label_es: str
    label_en: str
    triggers: frozenset[str]
    categories: frozenset[Category] = frozenset()
    tags: frozenset[str] = frozenset()
    keywords: frozenset[str] = frozenset()

    def label(self, language: Language) -> str:
        return self.label_en if language is Language.EN else self.label_es


TOPICS: tuple[Topic, ...] = (
    Topic(
        "museos",
        "museums",
        _terms("museo, museos, exposicion, exposiciones, museum, museums, exhibition, exhibitions"),
        categories=frozenset({Category.MUSEUM}),
    ),
    Topic(
        "monumentos",
        "monuments",
        _terms("monumento, monumentos, patrimonio, monument, monuments, heritage"),
        categories=frozenset({Category.MONUMENT}),
    ),
    Topic(
        "al aire libre",
        "outdoors",
        _terms("aire libre, al aire libre, exterior, outdoors, outdoor, outside, open air"),
        categories=frozenset({Category.NATURE, Category.ROUTE, Category.PUBLIC_SPACE}),
    ),
    Topic(
        "naturaleza",
        "nature",
        _terms("naturaleza, natural, campo, flora, fauna, nature, countryside, wildlife"),
        categories=frozenset({Category.NATURE}),
        tags=frozenset({"naturaleza"}),
    ),
    Topic(
        "para ir con niños",
        "for children",
        _terms(
            "nino, ninos, nina, ninas, crio, crios, hijo, hijos, hija, hijas, familia, familias, "
            "familiar, infantil, kid, kids, child, children, family, families, toddler, toddlers"
        ),
        tags=frozenset({"familias"}),
        keywords=_terms("infantil, playground"),
    ),
    Topic(
        "vino",
        "wine",
        _terms(
            "vino, vinos, bodega, bodegas, cata, catas, enoturismo, "
            "wine, wines, winery, wineries, tasting"
        ),
        tags=frozenset({"vino"}),
        keywords=_terms("vino, bodega, cata, wine, winery, tasting"),
    ),
    Topic(
        "comer",
        "food",
        _terms(
            "comer, comida, comidas, restaurante, restaurantes, almorzar, almuerzo, cenar, cena, "
            "menu, tapas, gastronomia, gastronomica, eat, eating, food, restaurant, restaurants, "
            "lunch, dinner, meal"
        ),
        categories=frozenset({Category.GASTRONOMY}),
    ),
    Topic(
        "historia",
        "history",
        # Sin «romano» ni «medieval»: forman parte de nombres propios («Puente Romano»).
        _terms(
            "historia, historico, historica, historicos, historicas, history, historic, historical"
        ),
        tags=frozenset({"historia"}),
    ),
    Topic(
        "arte",
        "art",
        _terms("arte, artistico, artistica, art, artistic"),
        tags=frozenset({"arte"}),
    ),
    Topic(
        "vistas",
        "views",
        _terms(
            "vistas, vista, mirador, miradores, panoramica, panoramicas, "
            "views, view, viewpoint, viewpoints, panoramic"
        ),
        tags=frozenset({"vistas"}),
        keywords=_terms("mirador, viewpoint"),
    ),
    Topic(
        "atardecer",
        "sunset",
        _terms("atardecer, puesta de sol, anochecer, sunset, sundown"),
        tags=frozenset({"atardecer"}),
    ),
    Topic(
        "rutas y senderismo",
        "walks and hiking",
        _terms(
            "senderismo, sendero, senderos, ruta, rutas, caminar, andar, pasear, paseo, excursion, "
            "hiking, hike, trail, trails, walk, walking, route, routes"
        ),
        categories=frozenset({Category.ROUTE}),
        tags=frozenset({"senderismo"}),
    ),
    Topic(
        "compras",
        "shopping",
        _terms(
            "compras, comprar, tienda, tiendas, mercado, mercadillo, shopping, shop, shops, market"
        ),
        tags=frozenset({"compras"}),
        keywords=_terms("mercado, market"),
    ),
    Topic(
        "bañarse",
        "swimming",
        _terms(
            "banarse, banarme, banarnos, bano, banos, nadar, piscina, piscinas, poza, "
            "swim, swimming, bathe, bathing, pool"
        ),
        keywords=_terms("poza, piscina, bano, pool, bathing"),
    ),
    Topic(
        "farmacia",
        "pharmacy",
        _terms("farmacia, farmacias, medicamento, medicamentos, pharmacy, chemist, medicine"),
        keywords=_terms("farmacia, pharmacy"),
    ),
    Topic(
        "aparcar",
        "parking",
        _terms("aparcar, aparcamiento, aparcamientos, parking, car park, park the car"),
        keywords=_terms("aparcamiento, car park, parking"),
    ),
    Topic(
        "información turística",
        "tourist information",
        _terms(
            "oficina de turismo, turismo, informacion turistica, plano, planos, mapa, mapas, "
            "tourist office, tourist information, map, maps"
        ),
        keywords=_terms("turismo, tourist"),
    ),
)
# Los lugares concretos («el castillo», «la ermita», «the church») no son temas: se buscan por
# su nombre, que está en los dos idiomas, y así la respuesta habla de ese lugar en particular.

# --- Condiciones que se comprueban con datos estructurados ------------------------------------

ACCESSIBILITY_TRIGGERS = _terms(
    "accesible, accesibles, accesibilidad, silla de ruedas, sillas de ruedas, movilidad reducida, "
    "minusvalido, minusvalida, discapacidad, adaptado, adaptada, adaptados, adaptadas, "
    "wheelchair, wheelchairs, accessible, accessibility, disabled, reduced mobility"
)
FREE_TRIGGERS = _terms(
    "gratis, gratuito, gratuita, gratuitos, gratuitas, sin pagar, sin coste, "
    "free, free of charge, no cost"
)
# Preguntar si algo está abierto sin decir cuándo se entiende como «ahora».
OPEN_TRIGGERS = _terms("abierto, abierta, abiertos, abiertas, abre, abren, open, opens")
NOW_TRIGGERS = _terms("ahora, ahora mismo, en este momento, now, right now, at the moment")
TODAY_TRIGGERS = _terms("hoy, today")
NOON_TRIGGERS = _terms("mediodia, noon, midday")
NOON = time(12, 0)
# Pregunta por el horario en sí: se describe, en vez de comprobar si está abierto ahora.
HOURS_TRIGGERS = _terms(
    "horario, horarios, a que hora, que hora, cuando abre, cuando cierra, hasta que hora, "
    "what time, opening hours, opening times, hours, when does"
)
PRICE_TRIGGERS = _terms(
    "precio, precios, cuesta, cuestan, cuanto vale, cuanto cuesta, coste, tarifa, "
    "price, prices, cost, costs, how much, fee, fees"
)
# Presuposición de que solo hay uno («el único sitio accesible»): si hay más, se corrige.
UNIQUENESS_TRIGGERS = _terms("el unico, la unica, lo unico, the only, only one")

WEEKDAYS: MappingProxyType[str, int] = MappingProxyType(
    {
        **dict.fromkeys(["lunes", "monday", "mondays"], 1),
        **dict.fromkeys(["martes", "tuesday", "tuesdays"], 2),
        **dict.fromkeys(["miercoles", "wednesday", "wednesdays"], 3),
        **dict.fromkeys(["jueves", "thursday", "thursdays"], 4),
        **dict.fromkeys(["viernes", "friday", "fridays"], 5),
        **dict.fromkeys(["sabado", "sabados", "saturday", "saturdays"], 6),
        **dict.fromkeys(["domingo", "domingos", "sunday", "sundays"], 7),
    }
)

WEEKDAY_NAMES: MappingProxyType[Language, tuple[str, ...]] = MappingProxyType(
    {
        Language.ES: ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"),
        Language.EN: (
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ),
    }
)

# Palabras sin contenido para buscar: no se usan como términos de búsqueda. Cualquier otra
# palabra de la pregunta tiene que aparecer en el punto, así que aquí van también los verbos de
# relleno («ofrecen», «probar») y los calificativos genéricos de lugar («zona», «local»): en un
# catálogo de un solo pueblo no distinguen un punto de otro.
STOPWORDS = _terms(
    # español
    "al, algo, algun, alguna, algunas, alguno, algunos, alli, aqui, area, asi, cada, como, con, "
    "conocer, cosa, cosas, cual, cuales, cuando, decir, degustar, del, desde, dia, dias, dime, "
    "dispone, disponen, donde, ella, entre, esa, ese, eso, esta, estan, estar, estas, este, esto, "
    "estos, estoy, favor, gracias, gustaria, hacer, hago, hasta, hay, haya, hola, hora, horas, "
    "incluye, incluyen, interesante, las, les, local, locales, lugar, lugares, mas, mejor, "
    "mejores, mis, mucha, mucho, muy, nada, nos, ofrece, ofrecen, opcion, opciones, otra, otro, "
    "para, pero, plan, planes, poco, podemos, poder, podria, por, porque, probar, puede, pueden, "
    "puedes, puedo, pueblo, que, querria, quien, quiero, quisiera, recomendacion, recomendar, "
    "recomienda, recomiendas, saber, sea, ser, sin, sitio, sitios, sobre, son, sus, tal, tambien, "
    "tenga, tengan, tengo, tiene, tienen, todo, todos, tus, una, unas, uno, unos, valdelumbre, "
    "vamos, ver, visita, visitar, visitas, voy, zona, zonas, "
    # inglés
    "about, all, and, any, anything, are, area, around, best, can, could, does, for, from, get, "
    "good, has, have, here, how, include, includes, interesting, its, like, local, many, much, "
    "near, nice, offer, offers, place, places, please, recommend, see, should, some, something, "
    "somewhere, spot, spots, taste, that, the, there, thing, things, this, town, try, visit, want, "
    "what, where, which, who, will, with, would, you, your"
)
