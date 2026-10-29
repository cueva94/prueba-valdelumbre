from fastapi import FastAPI

from app.api.routes import router
from app.assistant.answer import TemplateAnswerWriter
from app.assistant.service import Assistant
from app.catalog.loader import load_catalog
from app.catalog.repository import PoiRepository
from app.config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Carga y normaliza el catálogo una vez y monta la API sobre él.

    Si el catálogo no se puede leer, la aplicación no arranca: es mejor fallar al inicio que
    responder con un catálogo vacío.
    """
    settings = settings or Settings.from_env()
    repository = PoiRepository(load_catalog(settings.pois_path))

    app = FastAPI(
        title="Valdelumbre · Asistente turístico",
        version="1.0.0",
        description=(
            "Catálogo de puntos de interés de Valdelumbre y un asistente que responde solo con lo "
            "que hay en él, citando los ids de los puntos en los que se apoya."
        ),
    )
    app.state.repository = repository
    app.state.assistant = Assistant(repository, TemplateAnswerWriter())
    app.include_router(router)
    return app


app = create_app()
