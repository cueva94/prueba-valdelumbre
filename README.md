# Valdelumbre · Asistente turístico

Asistente turístico para Valdelumbre, un pueblo inventado. Consta de una API que expone su catálogo de puntos de interés, un asistente que responde preguntas **solo con lo que hay en el catálogo**, citando los ids de los puntos en los que se apoya, y una pantalla accesible para consultarlo.

Los datos de partida (`datos/`) traen defectos deliberados: duplicados, coordenadas invertidas, campos desconocidos e incluso una instrucción maliciosa dentro de una descripción. Buena parte del trabajo consiste en tratarlos con reglas generales y comprobables, que se describen en [DATOS.md](DATOS.md). El uso de IA durante el desarrollo y el diseño del asistente están en [IA.md](IA.md).

> **Estado del desarrollo:** la API, el asistente (6/6 en la evaluación oficial) y la pantalla, en español e inglés, están completos y verificados. La tabla [Estado](#estado) indica qué está hecho y verificado.

## Arranque rápido

**1. Requisitos.** Git y [Docker Desktop](https://www.docker.com/products/docker-desktop/) (o Docker Engine con Docker Compose v2), en marcha. No hace falta instalar Node.js, Python ni ninguna dependencia del proyecto: todo se compila dentro de Docker.

**2. Clonar el repositorio** (o descargarlo como ZIP desde GitHub y descomprimirlo):

```bash
git clone https://github.com/cueva94/prueba-valdelumbre.git
cd prueba-valdelumbre
```

**3. Configuración.** Ninguna. No hay `.env` ni claves: el asistente no usa servicios externos.

**4. Arrancar**, desde la carpeta del repositorio:

```bash
docker compose up --build
```

La primera vez descarga las imágenes base y compila la pantalla, así que tarda unos minutos. Está lista cuando el registro muestra `web-1 | … Configuration complete; ready for start up` (la pantalla arranca cuando la API ya responde). Para dejarlo en segundo plano, añade `-d`.

**5. Abrir:**

| Dirección | Qué es |
|---|---|
| http://localhost:8080 | Pantalla |
| http://localhost:8000/docs | Documentación interactiva de la API (OpenAPI) |
| http://localhost:8080/api/… | La misma API, a través de la pantalla (así la llama el navegador) |

**6. Comprobar que funciona:**

```bash
docker compose ps                                     # api: «healthy»; web: «Up»
curl http://localhost:8080/api/health                 # {"estado":"ok"}: pantalla y API conectadas
docker compose exec api python -m app.evaluation      # evaluación oficial: «Aciertos: 6/6 (100 %)»
```

En PowerShell, usa `curl.exe` (en Windows PowerShell 5, `curl` es otro comando) o abre la dirección en el navegador.

**7. Ver los registros:** `docker compose logs -f` (todos) o `docker compose logs -f api` (solo la API).

**8. Parar:** `Ctrl+C` si está en primer plano, y `docker compose down` para eliminar los contenedores.

**9. Después de cambiar el código:** `docker compose up --build` vuelve a construir lo que haya cambiado.

**10. Si algo falla:**

| Síntoma | Solución |
|---|---|
| `port is already allocated` o `Bind for 0.0.0.0:8080 failed` | Otro programa usa ese puerto. Elige otros con `WEB_PORT` (pantalla) y `API_PORT` (API): `WEB_PORT=9090 API_PORT=9001 docker compose up --build` en macOS, Linux o Git Bash, o `$env:WEB_PORT=9090; $env:API_PORT=9001; docker compose up --build` en PowerShell. La pantalla queda en http://localhost:9090. También puedes escribirlos en un fichero `.env` en la raíz (`WEB_PORT=9090`), que Docker Compose lee solo y Git ignora |
| `Cannot connect to the Docker daemon` o, en Windows, `open //./pipe/docker…` | Docker no está en marcha: abre Docker Desktop y espera a que indique que está listo |
| Errores al descargar imágenes (`no such host`, `TLS handshake timeout`) | Problema de red o de DNS al conectar con Docker Hub. Comprueba la conexión (o el proxy) y repite el comando |
| La pantalla carga pero no muestra lugares | La API no está disponible: `docker compose ps` y `docker compose logs api` |
| No se ven los cambios | Vuelve a construir con `docker compose up --build` y recarga el navegador sin caché (`Ctrl+F5`) |

## Desarrollo sin Docker

Requisitos: Python 3.12 y Node.js 24 (≥ 24.15) con npm.

**API** (terminal 1). No hace falta activar el entorno virtual: cada comando llama directamente al Python del entorno. Así funciona igual en cualquier terminal y, si el entorno no existe, falla con un error claro en lugar de instalar en el Python del sistema.

macOS y Linux:

```bash
cd backend
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt   # ejecución + tests, lint, formato y tipos
.venv/bin/python -m uvicorn app.main:app --reload --port 8000
```

Windows (PowerShell o Git Bash; en cmd, con barras invertidas):

```bash
cd backend
py -3.12 -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt
.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000
```

Si algo falla:

- **No se encuentra `python3.12` o `py`:** instala Python 3.12 desde python.org (en Windows, el instalador incluye el lanzador `py`). En Windows, evita `python3`: suele abrir la Microsoft Store.
- **Debian o Ubuntu, «ensurepip is not available»:** falta el módulo de entornos virtuales: `sudo apt install python3.12-venv`.
- **Si prefieres activar el entorno** para escribir `python` a secas: `source .venv/bin/activate` (macOS y Linux), `source .venv/Scripts/activate` (Git Bash), `.venv\Scripts\activate.bat` (cmd) o `.venv\Scripts\Activate.ps1` (PowerShell; si la política de ejecución lo bloquea, ejecuta antes `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, que solo afecta a esa ventana).

**Pantalla** (terminal 2):

```bash
cd frontend
npm ci
npm start                          # http://localhost:4200 · /api se redirige a localhost:8000
```

## API

| Ruta | Qué hace |
|---|---|
| `GET /pois` | Lista los puntos de interés. Filtros, que se combinan (deben cumplirse todos): `categoria`, `accesible`, `abierto_en` e `idioma` |
| `GET /pois/{id}` | Ficha de un punto. `404` si no existe o si se excluyó al normalizar (`poi-004`, duplicado) |
| `POST /preguntar` | Responde una pregunta solo con el catálogo y devuelve los ids en los que se apoya |
| `GET /health` | `{"estado": "ok"}` |

**Filtros de `GET /pois`:**

| Parámetro | Valores | Notas |
|---|---|---|
| `categoria` | `monumento`, `museo`, `naturaleza`, `ruta`, `espacio_publico`, `gastronomia`, `servicio` | |
| `accesible` | `true`, `false` | Un punto sin datos de accesibilidad no aparece con ninguno de los dos |
| `abierto_en` | `ahora` o día ISO y hora: `1T12:00` es lunes a las 12:00 | Hora local de Valdelumbre (`Europe/Madrid`). Solo aparecen los que **se sabe** que están abiertos: un horario desconocido no cuenta como abierto. Con un día de la semana no hay fecha, así que una franja de temporada no se puede confirmar; con `ahora`, sí |
| `idioma` | `es` (por defecto), `en` | Si falta la traducción, se devuelve el español y se indica en el propio texto |

Un parámetro desconocido (por ejemplo `categoría`, con tilde) o repetido (`?categoria=museo&categoria=ruta`) devuelve `422`. Ignorarlo, o quedarse con uno de los valores, daría un resultado silenciosamente incorrecto.

**Ficha de un punto** (la documentación completa de cada campo está en `/docs`):

```json
{
  "id": "poi-001",
  "nombre": {"texto": "Castillo de Valdelumbre", "idioma": "es"},
  "categoria": "monumento",
  "descripcion": {"texto": "Fortaleza del siglo XII…", "idioma": "es"},
  "coordenadas": {"lat": 40.4172, "lon": -3.7051},
  "accesible": false,
  "horario": {
    "siempre_abierto": false,
    "franjas": [{"dias": [1, 2, 3, 4, 5, 6], "abre": "10:00", "cierra": "14:00", "temporada": null}],
    "incompleto": false
  },
  "precio": {"tipo": "rango", "minimo": 4.5, "maximo": 4.5},
  "etiquetas": ["historia", "vistas"]
}
```

`null` significa siempre «sin datos», nunca «no» ni «cero»: `accesible: null` (desconocida), `coordenadas: null` (desconocidas o no fiables: el punto no se dibuja en el mapa), `precio: null` (desconocido). Un horario sin `siempre_abierto` y sin franjas es desconocido, no «cerrado». Un precio que no es un importe se conserva como `{"tipo": "texto", "texto": "…"}`.

**`POST /preguntar`:**

```bash
curl -X POST http://localhost:8000/preguntar \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "¿Dónde puedo probar vino de la zona?", "idioma": "es"}'
```

```json
{
  "respuesta": "Según el catálogo, este lugar cumple lo que pides (vino):\n- Bodega La Encina: Bodega familiar con visita guiada y cata. Reserva previa obligatoria.",
  "ids": ["poi-008"],
  "pois": [{"id": "poi-008", "…": "ficha completa, como en GET /pois/{id}"}],
  "idioma": "es"
}
```

> En la consola de Windows, `curl -d` no envía las tildes en UTF-8 y la API responde `422` («error parsing the body»). Allí es más cómodo probar desde http://localhost:8000/docs, o enviar el cuerpo desde un fichero UTF-8 con `--data-binary @pregunta.json`.

`pregunta` es obligatoria (de 1 a 500 caracteres) e `idioma` es opcional (`es` por defecto). `pois` lleva las fichas de los puntos citados, en el mismo orden que `ids`, para que la pantalla no tenga que pedirlas una a una. Los errores de validación devuelven `422` con el formato estándar de FastAPI, y un id inexistente devuelve `404` con `{"detail": "…"}`.

**Configuración.** La API lee `datos/pois.json`. Para usar otro fichero con el mismo formato, define la variable de entorno `VALDELUMBRE_POIS_PATH`. No hay ninguna otra configuración ni secretos.

## El asistente, en resumen

El asistente es un sistema conversacional determinista, basado en la búsqueda sobre el catálogo y en respuestas mediante plantillas. No utiliza un LLM, lo que permite obtener resultados reproducibles, explicables y comprobables sin conexión externa. El detalle, las protecciones y los límites están en [IA.md → Enfoque del asistente](IA.md#enfoque-del-asistente-y-medidas-contra-respuestas-sin-respaldo).

1. **Interpretar** la pregunta con un vocabulario bilingüe (`app/assistant/vocabulary.py`): temas («museos», «con niños», «al aire libre»…), condiciones (accesible, gratis, abierto un día y a una hora, «hoy» o «ahora») y términos sueltos («castillo», «ascensor», «tirolina»).
2. **Recuperar** los puntos que encajan con todos los temas y contienen todas las palabras de contenido de la pregunta. Una palabra que no aparece en ningún punto («tirolina») no se puede verificar: el asistente lo dice y no presenta ningún resultado como si la cumpliera.
3. **Comprobar las condiciones con los campos estructurados**, con la misma función de horario que `GET /pois`. Un dato desconocido nunca se da por bueno.
4. **Citar** solo los puntos que cumplen todo. Si la pregunta nombra un lugar concreto («¿es accesible el castillo?»), se cita ese lugar y se explica por qué cumple o no.
5. **Redactar** con plantillas en el idioma pedido. El redactor está detrás de una interfaz (`AnswerWriter`): se puede sustituir por un LLM, pero no decide los ids.

Si nada del catálogo responde a la pregunta, lo dice y no cita ningún punto. Si la pregunta parte de una premisa falsa («¿cuál es el único sitio accesible?»), la corrige con los datos.

## Idiomas

La pantalla está en español y en inglés. El selector **ES | EN** del header cambia el idioma al momento, sin recargar la página.

- **Un solo idioma para todo.** El idioma elegido es el de la interfaz y el que se envía a la API (`idioma=es|en` en `GET /pois` y `GET /pois/{id}`, y en el cuerpo de `POST /preguntar`). Al cambiarlo, las peticiones se repiten en el nuevo idioma. Lo gestiona un único servicio, `LanguageService`.
- **Textos en JSON.** Todos los textos de la interfaz están en `frontend/public/i18n/es.json` y `en.json`, con las mismas claves, agrupadas por pantalla. Se cargan con `@ngx-translate/core` y su `http-loader` (18.0.0, compatibles con Angular 22 y el modo zoneless).
- **Preferencia guardada.** El idioma se guarda en `localStorage`, a través de `PreferencesStorage` (el único servicio que lo usa), y se recupera al volver. Sin preferencia, o con un valor no válido, la pantalla empieza en español. La aplicación no se muestra hasta tener cargadas las traducciones, así que no aparece primero en el idioma equivocado. Si no se puede cargar el idioma guardado, sigue en español sin bloquearse.
- **Formatos regionales.** Días, meses, fechas de temporada, listas («a, b y c» / «a, b and c») y precios («4,50 €» / «€4.50») se escriben con `Intl` y el locale del idioma (`es-ES` o `en-GB`).
- **Contenido del catálogo.** Los nombres, descripciones y etiquetas de los lugares llegan de la API en el idioma pedido y no se traducen en la pantalla. El asistente responde en el idioma de la pregunta. La pantalla solo redacta de forma más cercana las frases fijas con las que el backend envuelve la respuesta («Según el catálogo, este lugar cumple lo que pides…»), con textos de los mismos JSON. Una frase que no reconoce se muestra tal cual llega.

## Estado de la pantalla

El estado se gestiona con signals de Angular, sin librerías de estado. Solo se comparte lo que usan varias pantallas:

| Pieza | Qué guarda | Quién lo usa |
|---|---|---|
| `LanguageService` | El idioma activo (`es` o `en`), el único lugar donde existe | Toda la interfaz, y `PoiService` y `AssistantService` para el parámetro `idioma` |
| `PlacesStore` | El catálogo completo, de solo lectura, con el total y los lugares por categoría calculados | Inicio, Explorar y la ficha. Se pide una vez y solo se vuelve a pedir al cambiar de idioma o al reintentar tras un error |
| `PreferencesStorage` | El idioma guardado en el navegador | `LanguageService` |
| La URL | Los filtros de Explorar (`?category=&accessible=&open=`) y la pregunta del asistente (`?q=`) | Se pueden compartir y el botón «atrás» funciona. No se copian en ningún store |

Las peticiones HTTP siguen en `PoiService` y `AssistantService`. Los resultados filtrados, la respuesta del asistente y el estado propio de cada componente (chincheta seleccionada, «Cargar más») viven en su pantalla, porque no los usa nadie más. No hay `AssistantStore`: la pregunta ya está en la URL y no hay historial de conversación.

## Evaluación

**Las preguntas oficiales** son las seis de `datos/evaluacion.json`, que se entregaron con el enunciado junto al catálogo (`datos/pois.json`). Es la única evaluación de la prueba. El fichero no se modifica: su huella SHA-256 se comprueba en cada ejecución de los tests.

El script `app/evaluation.py` las pasa contra `POST /preguntar` y muestra, para cada una, los ids esperados, los excluidos, los obtenidos y si acierta; al final, el total y el porcentaje.

```bash
# Con Docker Compose en marcha:
docker compose exec api python -m app.evaluation

# En local, desde backend/ y con la API arrancada (en Windows, .venv/Scripts/python):
.venv/bin/python -m app.evaluation                                   # las seis preguntas oficiales
.venv/bin/python -m app.evaluation --url http://localhost:8080/api  # a través del proxy
```

**Criterio de acierto.** El enunciado pide contar cuántas acierta, pero no define qué es un acierto; esto es una decisión propia:
- Una pregunta acierta si la respuesta cita todos los ids de `esperado_incluye` y ninguno de `esperado_excluye`.
- Si una pregunta no espera ni excluye ninguno (q6: el catálogo no tiene la respuesta), solo acierta si no cita ninguno. Sin esa regla, citar cualquier cosa contaría como acierto.
- Con el criterio más permisivo (q6 acierta siempre), el resultado sería el mismo.

El script devuelve `0` si acierta todas, `1` si falla alguna y `2` si no puede ejecutarse (por ejemplo, si la API no está arrancada).

**Resultado: 6/6**, comprobado contra la API en local y dentro del contenedor. El test `test_the_six_official_questions_pass` repite la evaluación en cada ejecución de `pytest`, sin levantar un servidor.

## Tests, lint, formato y tipos

Los comandos del backend se ejecutan en `backend/`, con el entorno virtual creado como en el apartado anterior. En Windows, cambia `.venv/bin/python` por `.venv/Scripts/python`. Los del frontend se ejecutan en `frontend/`.

| | Backend | Frontend |
|---|---|---|
| Tests | `.venv/bin/python -m pytest` | `npm test -- --watch=false` |
| Lint | `.venv/bin/python -m ruff check .` | `npm run lint` (incluye las reglas de accesibilidad de plantillas de angular-eslint) |
| Formato (comprobar) | `.venv/bin/python -m ruff format --check .` | `npm run format:check` |
| Formato (aplicar) | `.venv/bin/python -m ruff format .` | `npm run format` |
| Tipos | `.venv/bin/python -m mypy` (modo estricto) | `npm run build` (TypeScript y plantillas en modo estricto) |

- **Ruff** revisa (lint) y formatea el código Python. Su configuración está en `backend/pyproject.toml`.
- **mypy**, en modo estricto, comprueba los tipos de `app/` y de los tests (con el plugin de Pydantic). El código no usa `Any`, `cast` ni `type: ignore`.
- **ESLint**, con angular-eslint, revisa el TypeScript y las plantillas, incluidas reglas de accesibilidad. Además de las recomendadas, activa reglas que usan la información de tipos (signals que se leen sin llamarlos, promesas sin `await`) y otras de plantillas (botones sin `type`, `tabindex` positivo, `$any()`). Su configuración está en `frontend/eslint.config.js`.
- **Prettier** formatea el frontend. Su configuración está en `frontend/.prettierrc`.

**Con VS Code:** `.vscode/` recomienda las extensiones (el editor las propone al abrir la carpeta) y aplica estas mismas reglas al guardar. Los JSON no se formatean al guardar, para no reescribir los datos originales de `datos/`.

Qué cubren los tests del backend (212, más 1 `xfail` que documenta un límite conocido):

- **Normalización:** cada regla de [DATOS.md](DATOS.md), con registros sintéticos para demostrar que es general, y su efecto sobre el catálogo real; que es determinista y que no modifica los datos de entrada.
- **Horarios:** turnos partidos, límites de apertura y cierre, días ISO, franjas que cruzan la medianoche, temporadas y horarios desconocidos o incompletos.
- **Consultas:** cada filtro por separado y combinados, y registros inexistentes o excluidos.
- **API:** contratos de respuesta, códigos `404` y `422`, parámetros desconocidos o repetidos, idiomas y nombres del contrato en OpenAPI.
- **Asistente:** interpretación de la pregunta, todas las condiciones a la vez, condiciones que el catálogo no puede verificar, datos desconocidos que no se afirman, premisas falsas, preguntas sin respuesta o sin contenido, respuestas en los dos idiomas, instrucciones maliciosas en las descripciones y un redactor sustituto que no puede cambiar los ids.
- **Evaluación:** el criterio de acierto y las seis preguntas oficiales contra la API.
- **Preguntas de regresión internas** contra la API (ver abajo).
- Que `datos/` sigue idéntico a los originales, comprobado con su huella SHA-256.

**Preguntas de regresión internas.** `backend/tests/data/regression_questions.json` tiene 23 preguntas con el mismo formato que las oficiales, pero **no las proporcionó iUrban ni forman parte de la evaluación**. Se escribieron durante el desarrollo:
- **p01 a p20**, en la fase del backend, para comprobar que el asistente no está ajustado solo a las seis oficiales: variaciones de redacción, inglés, varias condiciones a la vez, lugares concretos y datos desconocidos.
- **p21 a p23**, en la auditoría, para el caso de una condición que el catálogo no puede verificar («¿Qué museos tienen tirolina?»).

El test `test_internal_regression_questions_pass` las ejecuta contra la API.

En el frontend (96 tests, con Vitest), los tests cubren las pantallas contra la API simulada, el catálogo compartido (una sola petición al navegar entre pantallas, nueva petición al cambiar de idioma y tras un error), la preferencia guardada (también si el navegador bloquea el almacenamiento), el mapa, la caja de pregunta, los formatos de horario y precio, y la redacción de las frases del asistente. Del idioma comprueban que `es.json` y `en.json` tienen las mismas claves y ningún texto vacío, que la preferencia se guarda y se recupera, que un valor no válido o un fallo de carga dejan la pantalla en español, que el selector cambia toda la interfaz, y que las peticiones, también la de `/preguntar`, llevan el idioma activo.

Para ver qué hace la normalización con los datos reales: `.venv/bin/python -m app.catalog` en `backend/`. Muestra los registros publicados y excluidos, y cada incidencia con su código de defecto.

## Arquitectura

```
Navegador ──► web (nginx): sirve la pantalla Angular ya compilada
                 │  /api/*  → proxy al servicio api (mismo origen: sin CORS)
                 ▼
             api (FastAPI)
              ├─ GET /pois, GET /pois/{id} ──► repositorio (filtros) ─┐
              └─ POST /preguntar ──► asistente                        ├─► catálogo normalizado
                    interpretar → recuperar → redactar ───────────────┘   (en memoria, inmutable)

Al arrancar: datos/pois.json ─► normalización (D1…D9, V) ─► catálogo + incidencias
```

El catálogo se carga y normaliza una vez al crear la aplicación. Si no se puede leer, la API no arranca. Todo lo que se comparte entre peticiones es inmutable. El dominio (`catalog`) y el asistente no dependen de FastAPI.

| Módulo | Responsabilidad |
|---|---|
| `catalog/models.py` | Modelo del catálogo normalizado: estructuras inmutables y tipadas. Lo desconocido es `None`, nunca `False`, `0` ni `""` |
| `catalog/normalization.py` | Del JSON original al catálogo: las reglas generales de [DATOS.md](DATOS.md), y cada corrección registrada como incidencia |
| `catalog/text.py` | Normalización de texto para comparar y detección de instrucciones incrustadas |
| `catalog/opening_hours.py` | La única función que decide si algo está abierto: abierto, cerrado o desconocido |
| `catalog/repository.py` | Consulta en memoria y filtros de `GET /pois` |
| `catalog/loader.py` | Lectura del JSON original en UTF-8 |
| `assistant/vocabulary.py` | Vocabulario bilingüe: temas, condiciones y palabras vacías |
| `assistant/interpretation.py` | De la pregunta a temas, términos y condiciones |
| `assistant/retrieval.py` | Qué puntos responden a la pregunta y cuáles se citan |
| `assistant/answer.py` | Redacción con plantillas en español e inglés, detrás de la interfaz `AnswerWriter` |
| `assistant/service.py` | Caso de uso «preguntar»: une las tres piezas |
| `api/schemas.py` | Contratos HTTP con Pydantic: atributos en inglés y nombres JSON del enunciado (en español) mediante alias |
| `api/routes.py` · `api/dependencies.py` | Rutas, validación de parámetros y reloj del pueblo |
| `evaluation.py` | Script de evaluación |

## Estructura del repositorio

```
├── docker-compose.yml     arranque de todo con un comando
├── datos/                 datos originales de la prueba, sin modificar
├── backend/               API (Python 3.12, FastAPI)
│   ├── app/
│   │   ├── catalog/       modelo, normalización, horarios y consulta del catálogo
│   │   ├── assistant/     interpretación, recuperación y redacción
│   │   ├── api/           rutas y contratos HTTP
│   │   └── evaluation.py  script de evaluación
│   ├── tests/             (data/regression_questions.json: preguntas de regresión internas, no oficiales)
│   └── Dockerfile
├── frontend/              pantalla (Angular 22) servida con nginx
│   ├── src/
│   ├── public/i18n/       textos de la pantalla en español e inglés (es.json, en.json)
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
| Hora de «ahora» | `Europe/Madrid`, calculada en la API y pasada como parámetro al dominio | Importa la hora del pueblo, no la del servidor (los contenedores van en UTC) ni la del visitante. Las funciones de horario no leen el reloj: son deterministas |
| `idioma` | Idioma de los textos (`es`/`en`). Si falta la traducción, se usa el español y cada texto indica su idioma real | No se inventan traducciones ni se presenta como inglés un texto en español. Las etiquetas solo existen en español y se devuelven tal cual |
| Intervalos horarios | `[apertura, cierre)`: a la hora de cierre ya está cerrado | Evita dar por abierto un sitio que cierra justo en ese minuto |
| Datos desconocidos en los filtros | No cumplen ningún filtro: ni `accesible=true` ni `accesible=false`, ni `abierto_en` | Tratarlos como sí o como no sería inventarse el dato |
| Respuesta de `/preguntar` | `respuesta`, `ids` e `idioma`, más `pois` con las fichas de los ids citados | El enunciado pide texto e ids; las fichas evitan a la pantalla una petición por punto |
| Qué ids se citan | Los puntos que cumplen todas las condiciones. Si la pregunta nombra un lugar concreto, también ese lugar aunque no cumpla, porque la respuesta explica por qué | Los ids son los puntos en los que se apoya la respuesta. Una pregunta general («museos accesibles») nunca cita los que no cumplen |
| Preguntas sin respuesta | Respuesta negativa y `ids: []`. En la evaluación, una pregunta que no espera ni excluye ningún punto solo cuenta como acierto si no se cita ninguno | Si no, una pregunta sin respuesta «acertaría» devolviendo cualquier cosa |
| Duplicados | Una regla general de deduplicación. El registro excluido no se publica (`GET /pois/poi-004` → 404) | Ver [DATOS.md](DATOS.md), defecto D2 |
| Parámetros desconocidos o repetidos | `422`, con la lista de parámetros admitidos | Ignorarlos, o quedarse con uno de los valores, daría resultados incorrectos sin avisar |
| Palabras de la pregunta | Todas las palabras de contenido filtran, también junto a un tema. Si una no aparece en ningún punto, no se cita nada y se dice que el catálogo no tiene esa información | Reconocer «museos» no basta para responder «museos con tirolina»: presentar los museos sería afirmar algo que no se puede verificar |

### Código e infraestructura

- **Código en inglés, contrato en español.** Los nombres del código (módulos, clases, funciones y tests) están en inglés. Los nombres del contrato HTTP siguen el enunciado y los datos (`categoria`, `abierto_en`, `pregunta`), y se enlazan con alias de Pydantic. Los textos (docstrings, incidencias y respuestas) están en español, y las respuestas también en inglés.
- **Sin base de datos.** Con 18 registros, el catálogo vive en memoria, normalizado e inmutable.
- **Asistente sin LLM.** Las respuestas se generan con plantillas deterministas, detrás de una interfaz que permite añadir un LLM sin tocar el resto y ejecutar los tests sin red.
- **Esqueleto de extremo a extremo antes que la lógica.** Docker Compose, Angular, el proxy y la API se validaron primero con un único endpoint (`/health`), para eliminar pronto el riesgo técnico.
- **Mismo origen.** nginx sirve la pantalla y redirige `/api/*` a la API. No hace falta CORS y la API mantiene exactamente las rutas del enunciado (`/pois`, `/preguntar`).
- **Instalación reproducible.** Las dependencias de Python están fijadas con `==` y solo son las imprescindibles: FastAPI, uvicorn, Pydantic y `tzdata` en ejecución; pytest, httpx2 (cliente de tests), Ruff y mypy en desarrollo. Las de Node están fijadas en `package-lock.json` y se instalan con `npm ci`.
- **Imágenes mínimas y sin privilegios.** El contexto de construcción de la API es una lista blanca (`.dockerignore`): solo entran el código, los requirements y los dos JSON de `datos/`. Dentro del contenedor se reproduce la estructura del repositorio (`/srv/backend` y `/srv/datos`), así que las rutas por defecto sirven igual en local y en Docker. La API se ejecuta con un usuario sin privilegios.
- **Scripts de instalación de npm denegados** (`allowScripts` en `package.json` y `--ignore-scripts` en Docker). Cuatro dependencias (`esbuild`, `lmdb`, `msgpackr-extract` y `@parcel/watcher`) traen scripts de instalación; se comprobó que el build y los tests funcionan sin ellos.

## Estado

| Fase | Contenido | Estado |
|---|---|---|
| Infraestructura | Docker Compose, API y pantalla mínimas, proxy | ✅ verificado |
| Calidad | Tests, lint, formato y tipos | ✅ verificado |
| Datos | Normalización del catálogo y estado de apertura | ✅ verificado |
| Backend | `GET /pois` y `GET /pois/{id}` | ✅ verificado (tests y Docker) |
| Asistente | `POST /preguntar` | ✅ verificado (tests y evaluación oficial: 6/6) |
| Pruebas | Script de evaluación y pruebas de integración | ✅ verificado |
| Frontend | Pantalla accesible, en español e inglés | ✅ verificado (tests, navegador y Docker) |
| Documentación | Revisión final desde un clon limpio | ⏳ |

## Limitaciones conocidas y qué haría con más tiempo

- **Asistente** (detalle en [IA.md](IA.md#límites-conocidos-del-asistente)):
  - Entiende lo que está en su vocabulario y las palabras que aparecen en el catálogo. Es conservador a propósito: si la pregunta incluye una palabra que no aparece en ningún punto (un sinónimo no previsto, «fin de semana»), responde que el catálogo no tiene esa información antes que arriesgarse a un resultado que no cumple lo pedido.
  - Una palabra que aparece en la ficha de un punto se toma como requisito aunque en la ficha signifique otra cosa. Las fichas son cortas y no ha dado problemas con estos datos.
  - La comparación de palabras es simple (sin tildes ni mayúsculas y con un plural aproximado). No hay corrección de erratas ni cálculo de distancias («cerca del castillo»).
- **Datos:**
  - `accesible` es un único booleano: no distingue movilidad reducida de discapacidad visual.
  - Las etiquetas solo están en español. Con la pantalla en inglés se muestran tal cual las da la API, sin traducir.
  - Con un día de la semana como `abierto_en` no hay fecha, así que los horarios de temporada no se pueden confirmar.
- **Idiomas:** el título y la descripción de `index.html` están en español hasta que arranca la aplicación (sin renderizado en servidor, un buscador los vería en español). La redacción de las frases del asistente en la pantalla depende de la redacción del backend: si este cambiara una frase, se mostraría tal cual hasta añadir su patrón.
- **Limpieza de datos:** la detección de instrucciones incrustadas funciona por patrones y es una medida de limpieza, no una defensa infalible. Los duplicados se detectan solo con nombre idéntico, y las coordenadas erróneas por pocos kilómetros no se detectan. El detalle está en [DATOS.md → Límites conocidos](DATOS.md#límites-conocidos-de-estas-reglas).
- **Trabajo futuro:**
  - Un redactor con LLM detrás de `AnswerWriter`, que solo reciba lo recuperado y cuyo texto se valide contra los puntos citados.
  - `abierto_en` con fecha completa, para confirmar temporadas.
  - Un informe de *posibles* duplicados para revisarlos a mano.
  - Búsqueda semántica si el catálogo creciera tanto que el vocabulario dejara de bastar.
