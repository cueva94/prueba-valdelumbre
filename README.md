# Valdelumbre — Asistente turístico

Una pequeña aplicación para consultar los puntos de interés de Valdelumbre, un pueblo ficticio, y hacer preguntas sobre ellos.

El proyecto incluye una API en FastAPI, un asistente que responde a partir de los datos del catálogo y una interfaz en Angular para explorar los lugares y consultar información en español e inglés.

## Arranque

### Opción 1: con Docker

La forma más sencilla de ejecutar el proyecto es con Docker Compose.

```bash
git clone https://github.com/cueva94/prueba-valdelumbre.git
cd prueba-valdelumbre
docker compose up --build
```

Cuando termine de arrancar, puedes acceder a:

- **Aplicación:** http://localhost:8080
- **Documentación de la API:** http://localhost:8000/docs

La primera ejecución puede tardar unos minutos mientras se descargan las imágenes y se construye la aplicación.

Para detener los servicios, pulsa `Ctrl+C` y ejecuta:

```bash
docker compose down
```

### Opción 2: ejecutar por separado

Si prefieres trabajar sin Docker, puedes arrancar el backend y el frontend en dos terminales distintas.

**Backend**

Necesitas Python 3.12. Desde la carpeta `backend/`:

```bash
python3.12 -m venv .venv
```

Activa el entorno virtual e instala las dependencias:

```bash
# Linux / macOS
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Después, instala las dependencias y arranca la API:

```bash
pip install -r requirements-dev.txt
python -m uvicorn app.main:app --reload --port 8000
```

La API estará disponible en http://localhost:8000 y su documentación en http://localhost:8000/docs.

**Frontend**

Necesitas Node.js y npm. Desde la carpeta `frontend/`, abre otra terminal y ejecuta:

```bash
npm ci
npm start
```

La aplicación estará disponible en http://localhost:4200. Durante el desarrollo, las peticiones a `/api` se redirigen al backend local.

## Qué incluye

- **Explorar lugares:** consultar los puntos de interés y filtrar por categoría, accesibilidad y horario.
- **Ficha de cada lugar:** ver su información, ubicación y horarios disponibles.
- **Asistente turístico:** hacer preguntas y recibir respuestas con referencias a los lugares del catálogo.
- **Español e inglés:** cambiar el idioma desde la interfaz.

## El asistente

El asistente permite hacer preguntas sobre los lugares de Valdelumbre y encontrar aquellos que mejor encajan con lo que busca el visitante.

Por ahora, funciona sin un modelo de lenguaje externo: utiliza el catálogo y una serie de reglas para interpretar las preguntas y construir las respuestas. Así, las respuestas son reproducibles y se basan en la información disponible.

Si el catálogo no contiene la información necesaria, el asistente lo indica en lugar de inventar una respuesta. Además, muestra los lugares en los que se basa para que el usuario pueda consultar sus fichas.

## Evaluación

El proyecto incluye una evaluación con las seis preguntas proporcionadas en la prueba. Para ejecutarla con Docker Compose, utiliza:

```bash
docker compose exec api python -m app.evaluation
```

El resultado actual es de **6/6 respuestas correctas**. La evaluación comprueba que el asistente cita los puntos de interés esperados y no incluye los que deberían quedar excluidos.

## API

Los principales endpoints son:

| Método y ruta | Descripción |
|---|---|
| `GET /pois` | Lista los puntos de interés y permite aplicar filtros. |
| `GET /pois/{id}` | Devuelve la información de un lugar. |
| `POST /preguntar` | Responde a una pregunta sobre el catálogo. |
| `GET /health` | Comprueba el estado de la API. |

La API utiliza el catálogo incluido en `datos/pois.json`.

## Estructura del repositorio

```text
├── backend/       API y lógica del asistente
├── frontend/      Interfaz web en Angular
├── datos/         Catálogo y datos de evaluación
├── docker-compose.yml
├── README.md
├── DATOS.md
└── IA.md
```

El backend se encarga de consultar el catálogo y generar las respuestas del asistente.
El frontend permite explorar los lugares e interactuar con él.
La carpeta `datos/` contiene la información utilizada por la aplicación y los datos de evaluación.

## Documentación adicional

- [`DATOS.md`](DATOS.md): problemas encontrados en el catálogo y criterios aplicados para tratarlos.
- [`IA.md`](IA.md): uso de herramientas de inteligencia artificial durante el desarrollo.

## Con más tiempo

Si continuara desarrollando el proyecto, estas serían algunas de las mejoras que priorizaría:

- **Integración de un LLM:** mejorar la comprensión de preguntas más naturales y variadas, manteniendo las respuestas fundamentadas en información recuperada del catálogo y evitando afirmaciones sin respaldo.
- **Información meteorológica:** integrar una API del tiempo para tener en cuenta la previsión y recomendar actividades más adecuadas para cada día.
- **Reservas y pagos:** permitir consultar disponibilidad y reservar visitas o actividades, con integración de una pasarela de pago cuando el proveedor lo permita.
- **Búsqueda más flexible:** añadir soporte para sinónimos y erratas para que las consultas no dependan tanto de palabras concretas.
