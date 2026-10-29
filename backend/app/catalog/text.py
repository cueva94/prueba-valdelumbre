import re
import unicodedata

_WHITESPACE = re.compile(r"\s+")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")

# Los patrones se aplican sobre texto normalizado (minúsculas y sin tildes), en español e inglés.
_ASKS_TO_IGNORE_INSTRUCTIONS = re.compile(
    r"\b(ignora|ignore|olvida|forget|disregard|omite)\b.*"
    r"\b(instrucciones|instructions|indicaciones|reglas|rules|prompt)\b"
)
_ADDRESSES_THE_ASSISTANT = re.compile(r"\b(asistente|assistant|chatbot|ia|ai|llm)\b")
_COMMAND = re.compile(
    r"\b(ignora|ignore|olvida|forget|recomienda|recommend|responde|answer|reply|di|say|tell"
    r"|actua|act|finge|pretend|menciona|mention|prioriza|prioritize)\b"
)


def normalize_text(text: str) -> str:
    """Minúsculas, sin tildes y con espacios simples. Solo para comparar, nunca para mostrar."""
    decomposed = unicodedata.normalize("NFD", text.casefold())
    without_accents = "".join(c for c in decomposed if not unicodedata.combining(c))
    return _WHITESPACE.sub(" ", without_accents).strip()


def is_embedded_instruction(sentence: str) -> bool:
    """Frase que pide ignorar instrucciones, o que se dirige al asistente para ordenarle algo."""
    normalized = normalize_text(sentence)
    if _ASKS_TO_IGNORE_INSTRUCTIONS.search(normalized):
        return True
    return bool(_ADDRESSES_THE_ASSISTANT.search(normalized) and _COMMAND.search(normalized))


def strip_embedded_instructions(text: str) -> tuple[str, list[str]]:
    """Quita del texto las frases que son instrucciones incrustadas.

    Devuelve el texto limpio y las frases eliminadas. Si no hay ninguna, el texto queda intacto.
    """
    sentences = _SENTENCE_END.split(text.strip())
    removed = [sentence for sentence in sentences if is_embedded_instruction(sentence)]
    if not removed:
        return text, []
    kept = [sentence for sentence in sentences if sentence not in removed]
    return " ".join(kept), removed
