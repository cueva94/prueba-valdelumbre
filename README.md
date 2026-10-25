# Valdelumbre · Asistente turístico

Asistente turístico para Valdelumbre, un pueblo inventado. Consta de una API que expone su catálogo de puntos de interés, un asistente que responde preguntas **solo con lo que hay en el catálogo**, citando los ids de los puntos en los que se apoya, y una pantalla accesible para consultarlo.

Los datos de partida (`datos/`) traen defectos deliberados: duplicados, coordenadas invertidas, campos desconocidos e incluso una instrucción maliciosa dentro de una descripción. Buena parte del trabajo consiste en tratarlos con reglas generales y comprobables, que se describen en [DATOS.md](DATOS.md). El uso de IA durante el desarrollo está en [IA.md](IA.md).

> **Estado del desarrollo:** está validado el esqueleto de extremo a extremo (pantalla → proxy → API). La lógica de negocio se añade por fases. La tabla [Estado](#estado) indica qué está hecho y verificado.

## Arranque rápido

Requisitos: Git y Docker con Docker Compose v2, y los puertos 8000 y 8080 libres.

```bash
git clone https://github.com/cueva94/prueba-valdelumbre.git
cd prueba-valdelumbre
docker compose up --build
```

| Dirección | Qué es |
|---|---|
| http://localhost:8080 | Pantalla |
| http://localhost:8000/docs | Documentación interactiva de la API (OpenAPI) |
| http://localhost:8080/api/… | La misma API, a través del proxy de la pantalla |

Para comprobar que todo responde, ejecuta `curl http://localhost:8080/api/health`. Debe devolver `{"estado":"ok"}`, y la pantalla debe mostrar «Estado de la API: disponible».

Para parar: `docker compose down`.

## Desarrollo sin Docker

Requisitos: Python 3.12 y Node.js 24 (≥ 24.15) con npm.

**API** (terminal 1):

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Pantalla** (terminal 2):

```bash
cd frontend
npm ci
npm start                          # http://localhost:4200 · /api se redirige a localhost:8000
```

## Arquitectura

```
Navegador ──► web (nginx): sirve la pantalla Angular ya compilada
                 │  /api/*  → proxy al servicio api (mismo origen: sin CORS)
                 ▼
             api (FastAPI)
              ├─ GET /health                                ✅
              ├─ GET /pois, GET /pois/{id} ──► catálogo     ⏳ fase 2
              └─ POST /preguntar ──► asistente              ⏳ fase 3
                    interpretar → recuperar → generar texto
                    (plantillas deterministas; interfaz preparada para un LLM)

Al arrancar (⏳ fase 1): datos/pois.json original ─► limpieza ─► catálogo + incidencias
```

## Estructura del repositorio

```
├── docker-compose.yml     arranque de todo con un comando
├── datos/                 datos originales de la prueba, sin modificar
├── backend/               API (Python 3.12, FastAPI)
│   ├── app/
│   └── Dockerfile
├── frontend/              pantalla (Angular 22) servida con nginx
│   ├── src/
│   ├── nginx.conf
│   └── Dockerfile
└── README.md · DATOS.md · IA.md
```

## Decisiones

### Interpretación del enunciado

Donde el enunciado deja margen se ha decidido lo siguiente. Si alguna decisión contradijera el enunciado, prevalece el enunciado.

| Tema | Decisión | Motivo |
|---|---|---|
| Formato de `abierto_en` | `abierto_en=1T12:00` (día ISO: 1 = lunes … 7 = domingo; hora `HH:MM`) o `abierto_en=ahora` | Es un solo parámetro, como pide el enunciado, sin ambigüedad y fácil de validar |
| Hora de «ahora» | `Europe/Madrid`, calculada en la API | Importa la hora del pueblo, no la del servidor (los contenedores van en UTC) ni la del visitante |
| `idioma` | Idioma de los textos de la respuesta (`es`/`en`). Si falta la traducción, se usa el español y se indica | Así no se pierden puntos por una traducción ausente |
| Intervalos horarios | `[apertura, cierre)`: a la hora de cierre ya está cerrado | Evita dar por abierto un sitio que cierra justo en ese minuto |
| Preguntas sin respuesta | Respuesta negativa y `ids: []`. En la evaluación, una pregunta que no espera ni excluye ningún punto solo cuenta como acierto si no se cita ninguno | Si no, una pregunta sin respuesta «acertaría» devolviendo cualquier cosa |
| Duplicados | Una regla general de deduplicación. El registro excluido no se publica (`GET /pois/poi-004` → 404) | Ver [DATOS.md](DATOS.md), defecto D2 |

### Infraestructura

- **Esqueleto de extremo a extremo antes que la lógica.** Docker Compose, Angular, el proxy y la API se validaron con un único endpoint (`/health`), para eliminar pronto el riesgo técnico.
- **Mismo origen.** nginx sirve la pantalla y redirige `/api/*` a la API. No hace falta CORS y la API mantiene exactamente las rutas del enunciado (`/pois`, `/preguntar`).
- **Instalación reproducible.** Las dependencias de Python están fijadas con `==`. Las de Node están fijadas en `package-lock.json` y se instalan con `npm ci`.
- **Imágenes mínimas y sin privilegios.** El contexto de construcción de la API es una lista blanca (`.dockerignore`), así que no entran `.git`, `.env`, `node_modules` ni entornos virtuales. La API se ejecuta con un usuario sin privilegios.
- **Scripts de instalación de npm denegados** (`allowScripts` en `package.json` y `--ignore-scripts` en Docker). Cuatro dependencias (`esbuild`, `lmdb`, `msgpackr-extract` y `@parcel/watcher`) traen scripts de instalación; se comprobó que el build y los tests funcionan sin ellos.
- **Asistente sin LLM por defecto.** Las respuestas se generan con plantillas deterministas, detrás de una interfaz que permite añadir un LLM sin tocar el resto y ejecutar los tests sin red.
- **Código en español**, coherente con el contrato del enunciado y con los datos (`categoria`, `abierto_en`, `franjas`).

## Estado

| Fase | Contenido | Estado |
|---|---|---|
| Infraestructura | Docker Compose, API y pantalla mínimas, proxy | ✅ verificado |
| Calidad | Tests, lint y formato | ⏳ |
| Datos | Limpieza y normalización del catálogo | ⏳ |
| Backend | `GET /pois` y `GET /pois/{id}` | ⏳ |
| Asistente | `POST /preguntar` | ⏳ |
| Frontend | Pantalla accesible | ⏳ |
| Pruebas | Script de evaluación y pruebas de integración | ⏳ |
| Documentación | Revisión final desde un clon limpio | ⏳ |

## Limitaciones conocidas y trabajo futuro

Se completará al cerrar el desarrollo.
