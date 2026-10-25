# Se construye con la raíz del repositorio como contexto (ver docker-compose.yml),
# para poder copiar los datos originales de datos/ sin duplicarlos.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /srv

COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/app ./app
COPY datos ./datos

# Sin privilegios de root en ejecución.
RUN useradd --create-home --uid 10001 api
USER api

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
