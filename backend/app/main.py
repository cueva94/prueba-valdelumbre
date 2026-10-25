"""Punto de entrada de la API del asistente turístico de Valdelumbre."""

from fastapi import FastAPI

app = FastAPI(
    title="Valdelumbre · Asistente turístico",
    version="0.1.0",
)


@app.get("/health", tags=["sistema"])
def salud() -> dict[str, str]:
    """Comprobación de vida: la usan Docker Compose y la pantalla."""
    return {"estado": "ok"}
