from dataclasses import dataclass
from datetime import datetime

from app.assistant.answer import AnswerWriter
from app.assistant.interpretation import interpret_question
from app.assistant.retrieval import Retriever
from app.catalog.models import Language, Poi
from app.catalog.repository import PoiRepository


@dataclass(frozen=True)
class AssistantAnswer:
    text: str
    pois: tuple[Poi, ...]  # puntos en los que se apoya la respuesta, decididos por la búsqueda


class Assistant:
    """Responde solo con lo que hay en el catálogo. Sin estado entre preguntas."""

    def __init__(self, repository: PoiRepository, writer: AnswerWriter) -> None:
        self._retriever = Retriever(repository.find())
        self._writer = writer

    def answer(self, question: str, language: Language, now: datetime) -> AssistantAnswer:
        """`now` es la hora actual del pueblo; se recibe para que la respuesta sea reproducible."""
        result = self._retriever.retrieve(interpret_question(question, now))
        return AssistantAnswer(text=self._writer.write(result, language), pois=result.cited)
