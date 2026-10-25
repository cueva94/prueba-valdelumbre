"""Utilidades de texto: normalización para comparar y detección de instrucciones incrustadas."""

import re
import unicodedata

_ESPACIOS = re.compile(r"\s+")
_FIN_DE_FRASE = re.compile(r"(?<=[.!?])\s+")

# Los patrones se aplican sobre texto normalizado (minúsculas y sin tildes), en español e inglés.
_PIDE_IGNORAR_INSTRUCCIONES = re.compile(
    r"\b(ignora|ignore|olvida|forget|disregard|omite)\b.*"
    r"\b(instrucciones|instructions|indicaciones|reglas|rules|prompt)\b"
)
_DIRIGIDA_AL_ASISTENTE = re.compile(r"\b(asistente|assistant|chatbot|ia|ai|llm)\b")
_ORDEN = re.compile(
    r"\b(ignora|ignore|olvida|forget|recomienda|recommend|responde|answer|reply|di|say|tell"
    r"|actua|act|finge|pretend|menciona|mention|prioriza|prioritize)\b"
)


def normalizar_texto(texto: str) -> str:
    """Minúsculas, sin tildes y con espacios simples. Solo para comparar, nunca para mostrar."""
    descompuesto = unicodedata.normalize("NFD", texto.casefold())
    sin_tildes = "".join(c for c in descompuesto if not unicodedata.combining(c))
    return _ESPACIOS.sub(" ", sin_tildes).strip()


def es_instruccion_incrustada(frase: str) -> bool:
    """Frase que pide ignorar instrucciones, o que se dirige al asistente para ordenarle algo."""
    normalizada = normalizar_texto(frase)
    if _PIDE_IGNORAR_INSTRUCCIONES.search(normalizada):
        return True
    return bool(_DIRIGIDA_AL_ASISTENTE.search(normalizada) and _ORDEN.search(normalizada))


def quitar_instrucciones(texto: str) -> tuple[str, list[str]]:
    """Quita del texto las frases que son instrucciones incrustadas.

    Devuelve el texto limpio y las frases eliminadas. Si no hay ninguna, el texto queda intacto.
    """
    frases = _FIN_DE_FRASE.split(texto.strip())
    eliminadas = [frase for frase in frases if es_instruccion_incrustada(frase)]
    if not eliminadas:
        return texto, []
    conservadas = [frase for frase in frases if frase not in eliminadas]
    return " ".join(conservadas), eliminadas
