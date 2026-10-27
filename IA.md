# Uso de IA

## Herramientas

- **Claude Code** (extensión de VS Code, modelo Claude Opus 5.5). La he usado para analizar el enunciado y los datos, proponer y contrastar alternativas, implementar, y comprobar los resultados ejecutándolos.
- **SonarQube for IDE**, un analizador estático del editor que no es una herramienta de IA. Aparece cuando alguna de sus sugerencias motivó un cambio.

## Reparto de papeles

**El criterio técnico es mío.** Uso la IA para proponer alternativas, contrastar mis decisiones con datos, escribir el código y verificarlo. Cada decisión de este registro indica su origen:

| Origen | Significado |
|---|---|
| **Criterio mío** | La decisión parte de mí; la IA la implementó o la contrastó con datos |
| **Propuesta de la IA → aceptada** | La revisé y la asumo como decisión mía |
| **Propuesta de la IA → modificada** | Cambié el criterio; se indica cómo y por qué |
| **Propuesta de la IA → descartada** | No la apliqué; se indica por qué |
| **Pendiente de mi revisión** | La IA la aplicó en la implementación y aún no la he validado |

Desde el principio le pedí a la IA que no diera nada por funcionando sin ejecutarlo y que no inventara decisiones ni comprobaciones en esta documentación. Los errores suyos que se detectaron están al final.

## Registro de decisiones

### Análisis y plan

| Decisión | Origen | Mi decisión |
|---|---|---|
| Analizar, diseñar y planificar antes de programar; implementar por fases y validar cada una antes del commit | Criterio mío | — |
| Interpretación de las seis ambigüedades del enunciado (README → Decisiones) | Propuesta de la IA → aceptada | Con una condición mía: si alguna contradice el enunciado, prevalece el enunciado y se documenta el motivo |
| Arquitectura: catálogo en memoria limpiado al arrancar; asistente con filtros estructurados y búsqueda por palabras, sin embeddings; ids citados decididos por la búsqueda, no por el generador | Propuesta de la IA → aceptada | Al confirmar el plan |
| Respuestas con plantillas deterministas, con una interfaz preparada para un LLM | Propuesta de la IA → aceptada | Elegida entre las opciones planteadas (plantillas o LLM con clave propia) |
| Código en español, coherente con el contrato y los datos | Propuesta de la IA → aceptada; **sustituida después por criterio mío** | En la fase del backend decidí nombres de código en inglés y contrato HTTP en español (ver [Backend](#backend-api-asistente-y-evaluación)) |

### Git y GitHub

| Decisión | Origen | Mi decisión |
|---|---|---|
| El proyecto va en mi cuenta personal (`cueva94`), con la identidad configurada solo en este repositorio, sin tocar la configuración global del trabajo | Criterio mío | La IA comprobó que la configuración global de Git y la sesión de `gh` eran las del trabajo antes de configurar nada |
| Correo `noreply` de GitHub en los commits, en lugar del principal (marcado como privado en GitHub) | Propuesta de la IA → aceptada | — |
| `Co-Authored-By: Claude` en cada commit | Propuesta de la IA → descartada | Prefiero documentar el uso real de la IA en este fichero |
| `ENUNCIADO.md` fuera del repositorio público, con una copia local excluida mediante `.git/info/exclude` | La IA planteó la duda; criterio mío | No consta que la empresa autorice publicarlo; los requisitos se resumen en el README |
| Revisar que no se publiquen secretos ni material privado antes de crear el remoto o hacer push | Criterio mío | La IA lo comprobó con búsquedas de patrones y con gitleaks sobre el historial |
| Repositorio privado durante el desarrollo, público al entregar | Propuesta de la IA → aceptada | Para no exponer el trabajo a medias |
| Commits por fases: infraestructura, calidad, datos, backend, asistente, frontend, pruebas y documentación | Criterio mío | — |

### Esqueleto del proyecto

**Criterio mío:** no avanzar a la lógica de negocio sin un esqueleto validado. La IA lo implementó como un esqueleto de extremo a extremo (pantalla → nginx → API), comprobado con Docker Compose y en local.

Durante la instalación aparecieron varios avisos. La IA comprobó cada uno en su origen antes de actuar, y yo revisé el resultado en el resumen de la fase:

| Aviso | Comprobación | Resultado |
|---|---|---|
| Starlette marca `httpx` como obsoleto en el cliente de tests y recomienda `httpx2` | Metadatos del paquete: lo firma el autor de `httpx` y lo publica la organización de Pydantic. Starlette lo importa en primer lugar | Cambiado a `httpx2` |
| Angular 22 marca `withFetch()` como obsoleto | La nota de obsolescencia en el código de Angular indica que `FetchBackend` ya es el backend por defecto | Eliminado |
| npm bloqueó los scripts de instalación de 4 paquetes | El build y los tests pasan sin ellos | Denegados de forma explícita (`allowScripts`), y `--ignore-scripts` en Docker |
| SonarQube sugiere `<output>` en lugar de `role="status"` | — | Descartado: `role="status"` es el patrón más extendido para anunciar cambios a los lectores de pantalla. **Pendiente:** comprobarlo con un lector de pantalla (NVDA); todavía no se ha hecho |

### Limpieza de datos

La IA implementó las reglas acordadas en el análisis (DATOS.md, D1 a D9). Después revisé las decisiones de detalle que había tomado:

| Decisión | Origen | Mi decisión y motivo |
|---|---|---|
| **Duplicados a 50 m o menos**, con el mismo nombre normalizado | Propuesta de la IA → aceptada | Como regla configurable y siempre combinada con el nombre: la distancia nunca basta sola, porque dos establecimientos distintos pueden estar muy cerca. Pedí probar los casos justo por debajo y por encima del umbral |
| **Radio de la zona para validar coordenadas** | Propuesta de la IA (50 km) → modificada | 50 km me pareció demasiado permisivo para detectar un punto mal ubicado en un pueblo. Pedí justificarlo por la extensión esperada del municipio y las coordenadas de referencia, comprobar cuánto se aleja poi-011 y qué pasa con los demás, y probar los casos límite. Con ese criterio, la IA midió las distancias (DATOS.md → Umbral de la zona) y propuso **10 km**. **Pendiente de mi confirmación** |
| **Franjas que cruzan la medianoche** (20:00–02:00) | Propuesta de la IA (descartarlas) → modificada | Descartarlas elimina horarios válidos: un local abierto hasta las 02:00 aparecería cerrado. Decidí implementar el cruce de forma explícita, comprobando el día en que empieza la franja y el siguiente. Cuando los datos no permitan saberlo con seguridad, el resultado es desconocido, no abierto. Pedí pruebas a las 20:00, 23:59, 00:30 y 02:00, con cambio de día |
| **Duplicados solo con nombre idéntico**, sin similitud aproximada | Propuesta de la IA → aceptada | Dos sitios con nombres parecidos pueden ser distintos; no se añade similitud sin una necesidad demostrada. Mejora futura mía: un informe de *posibles* duplicados para revisión manual, sin eliminarlos automáticamente |
| **Detección de instrucciones incrustadas por patrones** | Propuesta de la IA → aceptada con una precisión | Es una medida de limpieza, no una defensa infalible: puede no detectar una instrucción redactada de otra forma o marcar un texto legítimo. Hay que mantener pruebas de falsos positivos y de falsos negativos. La defensa real es que la accesibilidad y el horario salen de campos estructurados y los ids, de la búsqueda |

**Extensiones que la IA aplicó a partir de mi criterio sobre los horarios. Pendientes de mi revisión:**
- Una franja con apertura y cierre a la misma hora (¿0 o 24 horas?) se descarta.
- Si se descarta alguna franja, el horario queda *incompleto*: lo que cubren las franjas válidas está abierto y el resto es **desconocido, no cerrado**. Es la versión simétrica de «desconocido, no abierto».
- La temporada de una franja nocturna se comprueba con la fecha en que empezó la apertura.
- El falso negativo conocido de la detección de instrucciones queda documentado como test `xfail(strict=True)`. Si algún día se detecta, el test avisará de que hay que actualizar la documentación.

**Otras decisiones de la IA, pendientes de mi revisión:** las reglas preventivas (V) para registros mal formados que no aparecen en los datos actuales (DATOS.md → Reglas preventivas).

**Sugerencia de SonarQube:** partir dos `assert a and b` en asserts separados, para que un fallo indique qué condición concreta no se cumple. Aceptada.

**Cómo se comprobó que los tests sirven:** además de ejecutarlos (103 en verde y 1 `xfail` esperado), se introdujeron a propósito ocho fallos en el código, uno cada vez, y se restauró el código después. Los tests detectaron los ocho:
- incluir la hora de cierre;
- conservar el duplicado menos completo;
- no detectar órdenes al asistente;
- no corregir coordenadas;
- ignorar el tramo de madrugada;
- calcular mal el paso de domingo a lunes;
- ignorar un horario incompleto;
- volver al radio de 50 km.

### Backend: API, asistente y evaluación

Para esta fase escribí un encargo detallado con mis criterios. La IA inspeccionó el repositorio, presentó un diagnóstico y un plan, y lo implementó por fases, verificando cada una antes de pasar a la siguiente.

**Criterios míos** (del encargo):

| Criterio | Cómo quedó |
|---|---|
| Nombres del código en inglés, y docstrings con un único criterio | Se renombró todo lo existente (módulos, clases, funciones y tests) sin cambiar la lógica. Docstrings y comentarios en español |
| Sin `Any`, `cast`, `type: ignore` ni excepciones genéricas; modelos tipados en lugar de diccionarios sueltos | El JSON crudo se tipa con un alias `JsonValue` y se acota con `isinstance`. mypy en modo estricto lo comprueba |
| Arquitectura por responsabilidades: dominio y normalización, repositorio en memoria, casos de uso y API | `catalog/` (modelo, normalización, horarios, repositorio), `assistant/` y `api/`. Sin base de datos |
| Funciones de horario deterministas: reciben el instante, no leen el reloj | «Ahora» se calcula en la API (`Europe/Madrid`) y se pasa como parámetro |
| Asistente determinista; los ids salen de la recuperación, nunca del redactor; tests sin red | Ver [Enfoque del asistente](#enfoque-del-asistente-y-medidas-contra-respuestas-sin-respaldo) |
| No ajustar el asistente a las seis preguntas; añadir casos propios | La IA escribió 20 preguntas (p01 a p20), hoy en `backend/tests/data/regression_questions.json`. Son tests de regresión internos, no evaluación: ver [Evaluación oficial y preguntas de regresión](#evaluación-oficial-y-preguntas-de-regresión) |
| Si algo del encargo contradice el enunciado, prevalece el enunciado | Los nombres JSON del contrato siguen el enunciado (en español), aunque el código esté en inglés |

**Decisiones de la IA al implementar. Pendientes de mi revisión:**

| Decisión | Motivo que dio la IA |
|---|---|
| **Contrato JSON en español con alias de Pydantic** | Concilia mi criterio de código en inglés con el enunciado, que fija `categoria`, `abierto_en`, `pregunta`… |
| **mypy estricto** (con el plugin de Pydantic) como dependencia de desarrollo | Sin un verificador de tipos no se puede comprobar «sin errores de tipado». Detectó un error real (un filtro de días que no acotaba el tipo a `int`) |
| **Más familias de reglas en Ruff**: nombres, pytest, comprensiones, pathlib, `return` y código innecesario | Encajan con el encargo y no exigieron desactivar ninguna regla |
| **Categoría como valor enumerado**; una no reconocida queda como desconocida, con incidencia `V` | Normalizar valores enumerados, y que `GET /pois` rechace una categoría inexistente en lugar de devolver una lista vacía |
| **Precio no interpretable conservado como texto** (`{"tipo": "texto"}`) | El encargo pide conservar lo que no se puede convertir con seguridad. Antes se perdía |
| **Validación de rangos de coordenadas**, con el centro del pueblo calculado solo con las coordenadas en rango | El encargo pide validar rangos; un punto fuera de rango no debe «mover» el pueblo |
| **`/preguntar` devuelve también las fichas** (`pois`) | Lo permite el encargo; la pantalla no tiene que pedir cada ficha por separado |
| **Parámetros desconocidos → `422`** | Un `?categoría=museo` (con tilde) ignorado devolvería el catálogo sin filtrar, sin avisar |
| **Qué ids se citan**: los que cumplen todas las condiciones; un lugar nombrado en la pregunta, aunque no cumpla, porque la respuesta explica por qué | Que los ids sean los puntos en los que se apoya la respuesta, sin citar nunca en una pregunta general un punto que no cumple (q1 excluye poi-013) |
| **Cómo se leen las referencias temporales**: una hora sin día es hoy; un día sin hora, «abre en algún momento de ese día»; «hoy» sin hora, todo el día de hoy (corregido en la auditoría: antes se leía como «ahora»); «¿está abierto?» sin decir cuándo, ahora; «¿a qué hora abre?» describe el horario en lugar de comprobar si está abierto | Lo que entendería una persona; los casos están en los tests de interpretación |
| ~~**Con un tema reconocido, las demás palabras solo ordenan**~~ **Sustituida en la auditoría** por mi criterio: todas las palabras filtran (ver [Auditoría final](#auditoría-final-del-backend)) | El motivo era que, si filtraran, «vino de la zona» dejaría fuera la bodega. Pero así «museos con tirolina» presentaba los museos como si la tuvieran |
| **Lo que no se puede confirmar se cuenta, no se cita** («De 2 lugares más no consta el horario») | Ser transparente sin afirmar nada que no se sabe |
| **El contenedor reproduce la estructura del repositorio** (`/srv/backend` y `/srv/datos`), y el `.dockerignore` solo deja entrar los dos JSON de `datos/` | Corrige un fallo latente (ver errores) y evita que `ENUNCIADO.md` entre en la imagen |
| **Script de evaluación solo con la biblioteca estándar** y códigos de salida 0, 1 y 2 | Sin dependencias nuevas; utilizable en CI |

**Sugerencias de SonarQube aceptadas:**
- Renombrar un atributo que se llamaba igual que su clase (`_Text._text`).
- Reescribir un test que comparaba dos expresiones idénticas: ahora guarda cada respuesta en una variable.

**Cómo se comprobó** (al cerrar esta fase; las cifras finales están en la [auditoría](#auditoría-final-del-backend)):
- Tests: 203 en verde y 1 `xfail` esperado. Ruff, el formato y mypy estricto, sin errores.
- Evaluación oficial contra la API real por HTTP: 6/6. Aparte, las 20 preguntas de regresión internas que había entonces: 20/20.
- Docker: imágenes construidas con Docker Compose y arrancadas en puertos libres. La API respondió directamente y a través de nginx, la evaluación dio 6/6 dentro del contenedor y la imagen solo contiene los dos JSON de `datos/`.
- Pruebas de mutación: se introdujeron diez fallos en las reglas críticas, uno cada vez, borrando las cachés y ejecutando Python con `-B`, y se restauró el código después. Los tests detectaron los diez:
  - accesibilidad desconocida tratada como accesible, en el asistente;
  - horario desconocido tratado como cerrado (se perdía el «no consta»);
  - citar siempre los puntos que no cumplen;
  - combinar los temas con «o» en vez de «y»;
  - filtro `accesible` que deja pasar los desconocidos;
  - leer números sueltos como horas («7 km»);
  - no corregir la premisa falsa;
  - criterio de evaluación sin la regla de las preguntas sin respuesta;
  - ignorar parámetros desconocidos;
  - calcular el centro del pueblo con coordenadas fuera de rango.

### Auditoría final del backend

Antes de pasar al frontend pedí una auditoría crítica del backend, sin reescrituras.

**Criterios míos** (del encargo de auditoría):
- El asistente no puede dar a entender que los resultados cumplen una condición que no ha podido verificar. El caso que señalé fue «¿Qué museos tienen tirolina?».
- Limpiar solo lo que se confirme innecesario.
- Revisar que la documentación describa el comportamiento real.
- Revisar las decisiones pendientes sin darlas por aceptadas.

**Problemas encontrados y corregidos:**

| Problema | Corrección | Tests |
|---|---|---|
| Con un tema reconocido, las demás palabras no filtraban. «¿Qué museos tienen tirolina?», «Museums with a zip line» y «Restaurantes con terraza» presentaban todos los museos o restaurantes como si cumplieran; «Museos con ascensor» citaba los tres museos, aunque solo uno tiene ascensor | Todas las palabras de contenido filtran, haya tema o no. Una palabra que no aparece en ningún punto no se puede verificar: no se cita nada y se dice. Para que «vino de la zona» siga encontrando la bodega, los calificativos genéricos de lugar («zona», «local») y los verbos de relleno («probar», «ofrecen», «taste»…) pasan a ser palabras vacías. La comparación admite plurales en «-es» («ascensores») | `test_a_recognised_topic_never_hides_a_condition_the_catalog_cannot_verify`, `test_every_word_of_the_question_filters_within_a_topic`, `test_a_word_found_only_outside_the_topic_gives_no_match`. Además, la IA añadió por iniciativa propia 3 preguntas de regresión internas (p21 a p23), que repiten casos de esos tests. Si se vuelve al comportamiento anterior, fallan 7 tests |
| «¿Qué está abierto hoy?» se interpretaba como «ahora» | «Hoy» sin hora es todo el día de hoy, con su fecha. Se quitó «tonight»: tomarlo como todo el día podría dar por abierto esta noche un sitio que solo abre por la mañana | `test_today_without_a_time_asks_about_the_whole_day` |
| «¿Abre el castillo el domingo?» respondía «está cerrado en ese momento» | Textos propios para las preguntas por un día: «no abre ese día» y «no consta si abre ese día» | `test_a_day_question_about_a_named_place_answers_for_that_day` |
| Un parámetro repetido (`?categoria=museo&categoria=ruta`) se resolvía con el último valor, sin avisar | `422` con el tipo `multiple_values`, en la misma dependencia que rechaza los desconocidos | `test_repeated_parameters_are_rejected_instead_of_keeping_one` |
| La categoría `espacio_publico` no se podía encontrar por sus palabras («espacio público») | El índice de búsqueda separa la categoría en palabras | Comprobado a mano |
| El ejemplo de `curl` del README falla en la consola de Windows, que no envía las tildes en UTF-8 | Nota en el README: usar `/docs` o un fichero UTF-8 | — |

**Limpieza:**
- **Eliminado:**
  - la función `_stem`, sustituida por `_forms`, que también reconoce los plurales en «-es»;
  - la comparación de momentos con la que se deducía si una pregunta era por «ahora», sustituida por un indicador explícito;
  - las ramas duplicadas de la recuperación, ahora un único filtro;
  - el disparador «tonight»;
  - `frontend/dist/`, salida de una compilación de verificación (estaba ignorada por Git).
- **Revisado sin encontrar nada que eliminar:** funciones, clases, constantes e imports sin uso (análisis con `ast` y reglas F de Ruff), campos de plantilla sin uso, directorios vacíos y ficheros temporales dentro del repositorio.
- **Conservado, con motivo:**
  - `tzdata`: la imagen de Docker ya trae la base de zonas horarias, pero Windows no, y sin el paquete `ZoneInfo("Europe/Madrid")` falla en el desarrollo local;
  - `VALDELUMBRE_POIS_PATH`: lo usa `Settings.from_env()`. Ahora está documentado en el README;
  - la interfaz `AnswerWriter`: la pide el enunciado si se usa un LLM, y un test la usa para demostrar que el redactor no decide los ids;
  - las comprobaciones `isinstance` de `api/dependencies.py`: `app.state` no está tipado;
  - el `xfail` de D1: documenta un límite real, y se ha comprobado que el patrón sigue sin detectar esa frase.
- **Dependencias:** todas necesarias, sin cambios. Ejecución: FastAPI, uvicorn, Pydantic y `tzdata`. Desarrollo: pytest, httpx2 (lo necesita `TestClient`), Ruff y mypy.

**Estado de las decisiones pendientes.** He comprobado cada una en el código y con sus tests. No marco ninguna como aceptada: indico lo que propongo.

| Decisión | Qué hace el código (comprobado) | Propuesta |
|---|---|---|
| Radio de 10 km para validar coordenadas | `NormalizationThresholds.town_radius_km = 10.0`. Hay tests justo dentro y fuera del límite, y el número está justificado con medidas en DATOS.md | **Tu confirmación** (la marcaste como pendiente) |
| Franja con apertura y cierre a la misma hora: se descarta | Se descarta y el horario queda incompleto | Cerrar |
| Horario incompleto: lo no cubierto es desconocido, no cerrado | `_status` devuelve «desconocido» | Cerrar |
| Temporada de una franja nocturna: se mira el día en que empezó | `_covers_moment` usa la fecha del día anterior para la madrugada | Cerrar |
| `xfail(strict=True)` para el falso negativo de D1 | Sigue fallando como se espera | Cerrar |
| Reglas preventivas (V) | Con tests | Cerrar |
| Contrato JSON en español con alias | OpenAPI muestra los nombres del contrato (test) | Cerrar |
| mypy estricto, más reglas de Ruff, categoría enumerada, precio como texto, rangos de coordenadas | Pasan las herramientas y los tests de cada regla | Cerrar |
| Parámetros desconocidos o repetidos → `422` | Comprobado por HTTP | Cerrar |
| Estructura del contenedor y `.dockerignore`; script de evaluación con la biblioteca estándar | Docker Compose desde una copia limpia y evaluación dentro del contenedor | Cerrar |
| `/preguntar` devuelve también las fichas (`pois`) | Amplía el contrato del enunciado sin romperlo | **Tu confirmación**: afecta al frontend |
| Un lugar nombrado se cita aunque no cumpla, con el motivo; lo que no se puede confirmar se cuenta, pero no se cita | `RetrievalResult.cited` y la nota de «no consta» | **Tu confirmación**: define qué significa «los ids en los que se apoya» |
| Interpretación temporal (hora sin día, día sin hora, «hoy», «¿está abierto?») | Tests de interpretación | **Tu confirmación**: decisión de producto |
| Todas las palabras filtran; palabras vacías nuevas; plurales | Lo descrito arriba | Sale de tu criterio; **la lista concreta de palabras vacías, a tu revisión** |

**Cómo se comprobó** (estado final):
- **Tests:** 212 en verde y 1 `xfail` esperado. Ruff, el formato y mypy estricto, sin errores.
- **Instalación desde cero:** en una copia limpia del repositorio (los ficheros versionados y los nuevos no ignorados, sin `.venv`, `node_modules` ni `ENUNCIADO.md`), siguiendo los pasos del README, pasaron los tests, Ruff y mypy.
- **API real por HTTP:**
  - los tres endpoints;
  - filtros válidos, combinados y en inglés;
  - `422` para una categoría, accesibilidad, idioma o `abierto_en` inválidos, y para parámetros desconocidos o repetidos;
  - `404` para `poi-004` y para un id inexistente;
  - `422` para una pregunta vacía o un idioma no admitido;
  - las preguntas con condiciones que no se pueden verificar.
- **Evaluación oficial por HTTP:** 6/6. Aparte, las preguntas de regresión internas: 23/23.
- **Docker Compose desde la copia limpia,** con otro nombre de proyecto y otros puertos para no tocar el stack en marcha:
  - la API arrancó *healthy* y respondió directamente y a través de nginx, y la pantalla también;
  - dentro del contenedor solo están los dos JSON de `datos/`, y se ejecuta con un usuario sin privilegios;
  - `docker compose exec api python -m app.evaluation` dio 6/6;
  - después se eliminaron sus contenedores, su red y sus imágenes.

### Evaluación oficial y preguntas de regresión

**Criterio mío:** la evaluación se basa solo en el enunciado, el catálogo y las preguntas que entregó iUrban. Las preguntas escritas durante el desarrollo no se presentan como parte de la evaluación.

| Fichero | Origen (comprobado en el repositorio) | Uso |
|---|---|---|
| `datos/evaluacion.json` | Entregado con la prueba. El enunciado lo cita, entró en el primer commit (`b28aa40`) junto a `datos/pois.json` y no ha cambiado: su huella SHA-256 se comprueba en los tests | **La evaluación**: 6 preguntas (q1 a q6). `python -m app.evaluation` las usa por defecto |
| `backend/tests/data/regression_questions.json` | Escrito por la IA durante el desarrollo; está en el repositorio desde el commit `9ba0919`, ya con este nombre. p01 a p20, en la fase del backend, porque mi encargo pedía casos propios para comprobar variaciones de redacción. p21 a p23, en la auditoría, por iniciativa de la IA: repiten casos que ya cubren los tests del asistente | Tests de regresión internos (`test_internal_regression_questions_pass`). **No es evaluación** |

Para separarlos, sin cambiar el comportamiento ni las preguntas:
- el fichero se llamaba `extra_evaluation.json`, un nombre que lo presentaba como evaluación adicional; ahora es `regression_questions.json`;
- las preguntas oficiales y las internas tienen tests separados (`test_the_six_official_questions_pass` y `test_internal_regression_questions_pass`);
- el README, DATOS.md y la ayuda del script de evaluación solo presentan como evaluación las seis preguntas oficiales.

### Frontend: idiomas (español e inglés)

Pedí incorporar la internacionalización completa de la pantalla. Antes de tocar nada, la IA revisó el proyecto y presentó un plan, que aprobé con ajustes: comprobar antes la compatibilidad de las versiones, cuidar la reactividad de los textos calculados en TypeScript, una inicialización robusta con vuelta al español, y formatos regionales.

| Decisión | Origen | Mi decisión |
|---|---|---|
| Textos en JSON por idioma, cambio de idioma sin recargar, selector en el header, preferencia en `localStorage` y español por defecto | Criterio mío | — |
| `@ngx-translate/core` y su `http-loader`, versión estable 18.0.0 (las 18.1 eran *release candidates*) | Criterio mío; la IA comprobó la compatibilidad | Antes de instalar, la IA revisó las dependencias declaradas (Angular ≥ 18, sin más dependencias que `tslib`) y el código de la librería: compilada para Angular 22, basada en signals y sin zone.js |
| Un solo idioma para la interfaz y para la API, gestionado por `LanguageService`; `PoiService` y `AssistantService` no cambian | Propuesta de la IA → aceptada | — |
| Selector **ES \| EN** con `aria-pressed`, en lugar del botón único que había | Propuesta de la IA → aceptada | — |
| La aplicación espera a tener las traducciones antes de mostrarse; si falla el idioma guardado, español; si falla también el español, arranca igualmente | Criterio mío (ajuste al plan) | — |
| Textos calculados en TypeScript dentro de `computed()`, que se recalculan al cambiar el idioma porque `instant()` lee signals de la librería; los pipes de precio y horario son impuros por el mismo motivo | Propuesta de la IA → aceptada | Pedí revisarlo expresamente: `instant()` por sí solo no es reactivo |
| Formatos con `Intl` y locale `es-ES` / `en-GB` | Criterio mío (ajuste al plan) | — |
| No traducir el contenido del catálogo; las etiquetas, que la API solo da en español, se muestran tal cual también en inglés | Criterio mío | — |
| La redacción de las frases fijas del asistente: los patrones que las reconocen siguen en TypeScript, porque dependen del texto del backend, y lo que se muestra sale de los JSON | Propuesta de la IA → aceptada | — |
| Preguntas sugeridas en inglés comprobadas contra la API: deben citar los mismos lugares que en español. «Which outdoor walks are there?» no citaba ninguno y se cambió por «What outdoor trails are there?» | Pendiente de mi revisión | — |
| Rango de precios con una plantilla del JSON en lugar de `Intl.NumberFormat.formatRange`, que es de ES2023 y el proyecto compila con ES2022 | Pendiente de mi revisión | Se evita cambiar la configuración de TypeScript |
| Títulos de pestaña traducidos con una `TitleStrategy` propia (el `title` de cada ruta es una clave); la ficha pone el suyo | Pendiente de mi revisión | — |
| `Cache-Control: no-cache` para `/i18n/` en nginx, porque los JSON no llevan hash en el nombre y un navegador podría seguir usando unas traducciones antiguas | Pendiente de mi revisión | — |

Comprobaciones: los tests nuevos y los existentes (86), lint, formato y build de producción; el navegador en desarrollo y en Docker, con pasos en inglés tras elegirlo en el selector, que cargan cada URL desde cero (la preferencia se conserva al recargar) y buscan claves sin resolver y textos fijos en español.

### Frontend: estado con signals

Pedí revisar la gestión del estado con signals y stores propios, sin librerías de estado, y crear stores solo donde aportaran algo. La IA hizo primero un diagnóstico y yo aprobé su propuesta.

| Decisión | Origen | Mi decisión |
|---|---|---|
| Signals de Angular, sin Redux, NgRx ni otras librerías | Criterio mío | — |
| `PlacesStore` para el catálogo completo: lo pedían por separado Inicio, Explorar y la ficha, y el cálculo de contadores estaba repetido | Propuesta de la IA → aceptada | Acepté que el catálogo quede guardado durante la visita (los datos no cambian mientras se navega) |
| Los filtros siguen en la URL y no pasan al store | Propuesta de la IA → aceptada | Copiarlos obligaría a sincronizar dos fuentes con un `effect` |
| Sin `AssistantStore` | Propuesta de la IA → aceptada | La pregunta ya está en la URL, hay una sola pantalla que la usa y no hay historial |
| `PreferencesStorage`, el único servicio que toca `localStorage`; mismo comportamiento de inicio y misma clave | Propuesta de la IA → aceptada | — |
| Los idiomas admitidos (`LANGUAGES`, `isLanguage`) pasan junto al tipo `Language`, en el modelo del contrato | Pendiente de mi revisión | Evita una dependencia circular entre `PreferencesStorage` y `LanguageService` |

Comprobaciones: los tests existentes de filtros, resultados, carga, errores y estado vacío pasaron sin cambiarlos; los nuevos cubren el store y la persistencia (96 en total); lint, formato y build. En el navegador, en desarrollo y en Docker, ir de Inicio a Explorar, a una ficha y volver hace una sola petición del catálogo.

## Errores de la IA detectados

- **Saltos de línea.** La IA afirmó que los JSON usaban CRLF, a partir de un recuento con `grep` mal planteado. Al comprobarlo byte a byte resultó falso: son LF. Se corrigió antes de actuar sobre esa base. La regla de `.gitattributes` para `datos/` se mantuvo, pero por el motivo correcto: evitar que Git convierta los saltos de línea al clonar en Windows.
- **Guion largo en el código.** Para aclarar al linter que el guion largo (U+2013) de la expresión de precios es intencionado, la IA intentó escribirlo como secuencia de escape (barra invertida seguida de `u2013`). Dos intentos dejaron el carácter literal, porque la herramienta de edición interpretaba la secuencia. El linter lo detectó las dos veces, y se resolvió con un script que construye la secuencia sin escribirla literalmente.
- **Caché en las pruebas de mutación.** La primera versión del script que introduce fallos no aislaba la caché de bytecode de Python. Cuando un fallo y su restauración tenían el mismo tamaño y ocurrían en el mismo segundo, Python reutilizaba la versión con el fallo. Se notó porque, tras restaurar el código, un test seguía fallando. Una cifra del informe anterior estaba contaminada por ello (7 tests fallidos en lugar de 3), aunque la conclusión se mantenía. Se corrigió el script, que ahora borra las cachés y ejecuta Python con `-B`, y se repitieron todas las mutaciones.

En la fase del backend:

- **El guion largo, otra vez.** La herramienta de edición volvió a convertir la secuencia de escape en el carácter literal, en tres ficheros. El linter lo detectó y se corrigió con el mismo script de la vez anterior.
- **`type: ignore` prohibido.** La IA escribió dos, en contra del encargo: uno para reconfigurar la salida de la consola y otro en un test que modificaba a propósito un registro de solo lectura. Se sustituyó el primero por una comprobación con `isinstance` y se eliminó el test, porque el tipo de solo lectura ya impide escribir en él.
- **Código muerto.** Dejó una función sin usar en el redactor de respuestas. Se eliminó al revisar el fichero.
- **Horas inventadas.** La primera versión del reconocimiento de horas aceptaba números sueltos, así que «ruta de 7 km» se habría leído como las 7:00. Se vio al revisar el patrón, se corrigió y hay un test.
- **Temas que se tragaban lugares concretos.** Un tema «lugares religiosos» hacía que «¿está abierta la ermita?» respondiera con la iglesia, y el adjetivo «romano» del tema de historia hacía lo mismo con el Puente Romano. Se vio al probar preguntas a mano. Se quitó ese tema, porque los nombres ya están en los dos idiomas, se quitaron del tema de historia los adjetivos que forman parte de nombres propios, y la detección de «lugar concreto» pasó a aplicarse siempre.
- **Fallo latente en Docker.** En el contenedor, `app/` estaba en `/srv/app`, así que la raíz del repositorio que calcula `config.py` era `/` y no existía `/datos/pois.json`. No fallaba porque hasta ahora la API no cargaba el catálogo al arrancar. Se detectó al revisar la configuración antes de probar con Docker, y se corrigió haciendo que el contenedor reproduzca la estructura del repositorio.

En la auditoría final:

- **Falsos positivos por diseño.** La decisión de la IA de que, con un tema reconocido, las demás palabras solo ordenaran (para no perder «vino de la zona») hacía pasar por cumplidas condiciones que no se habían comprobado: la tirolina, que no está en el catálogo, y el ascensor, que solo tiene un museo. Lo señalé yo con el caso de la tirolina; la auditoría encontró los demás. Corregido (ver [Auditoría final](#auditoría-final-del-backend)).
- **Fallos menores de interpretación y de contrato,** encontrados al probar combinaciones durante la auditoría: «hoy» se leía como «ahora»; una pregunta por un día respondía «en ese momento»; un parámetro repetido se resolvía con el último valor; y la categoría `espacio_publico` no se encontraba por sus palabras.
- **Una prueba propia mal planteada.** La IA comprobó la API con `curl -d` desde Git Bash, y las preguntas con tildes devolvieron `422`: la consola de Windows no las envía en UTF-8. Repetidas desde un fichero UTF-8, respondieron bien. Sirvió para añadir una nota al README, cuyo ejemplo habría fallado igual en Windows.
- **Preguntas propias presentadas junto a la evaluación oficial.** La IA llamó al fichero de preguntas propias `extra_evaluation.json` y presentó su resultado (20/20 y luego 23/23) al lado del 6/6 oficial. Además, en la auditoría añadió tres preguntas por iniciativa propia. Podía dar a entender que formaban parte de la evaluación. Lo señalé yo y se separaron (ver [Evaluación oficial y preguntas de regresión](#evaluación-oficial-y-preguntas-de-regresión)).

## Enfoque del asistente y medidas contra respuestas sin respaldo

El asistente es un sistema conversacional determinista, basado en la búsqueda sobre el catálogo y en respuestas mediante plantillas. No utiliza un LLM, lo que permite obtener resultados reproducibles, explicables y comprobables sin conexión externa. El enunciado no puntúa el modelo, sino lo que lo rodea.

### Cómo responde

1. **Interpretación** ([`interpretation.py`](backend/app/assistant/interpretation.py)). La pregunta se normaliza (minúsculas y sin tildes) y se compara con un vocabulario bilingüe ([`vocabulary.py`](backend/app/assistant/vocabulary.py)). De ahí salen:
   - **Temas:** «museos», «con niños», «al aire libre», «vino», «comer»… Cada uno se define por categorías, etiquetas o palabras clave.
   - **Condiciones:** accesible, gratis, abierto en un momento («un lunes a las 12:00», «ahora») o un día («el domingo»).
   - **Términos sueltos:** las palabras que quedan sin ser palabras vacías («castillo», «tirolina»).
   - **Señales:** si pregunta por el horario o el precio, o si presupone que hay un único resultado.
2. **Recuperación** ([`retrieval.py`](backend/app/assistant/retrieval.py)):
   - Son candidatos los puntos que encajan con **todos** los temas y contienen **todos** los términos, haya tema o no. «Museos con ascensor» solo devuelve el museo cuya ficha menciona el ascensor.
   - Un término que no aparece en ningún punto («tirolina») es una condición que el catálogo no puede verificar: no hay candidatos, y la respuesta dice que no hay información sobre él. Así, reconocer el tema «museos» nunca hace pasar por cumplida una condición que no se ha comprobado.
   - Los verbos de relleno («ofrecen», «probar») y los calificativos genéricos de lugar («zona», «local») son palabras vacías: en un catálogo de un solo pueblo no distinguen un punto de otro. Por eso «vino de la zona» sigue encontrando la bodega.
   - La comparación admite plurales sencillos («ascensores» encuentra «ascensor»).
   - Sin temas ni términos, todo el catálogo: «¿qué está abierto ahora?».
   - Si algún término coincide con el nombre de un candidato, la pregunta es sobre ese lugar.
3. **Condiciones.** Cada candidato se comprueba con los campos estructurados (`accesible`, `precio`, `horario`), con la misma función de horario que `GET /pois`. El resultado de cada condición es «cumple», «no cumple» o «no consta».
4. **Citas.** Se citan los que cumplen todo. En una pregunta sobre un lugar concreto, también ese lugar, con el motivo. Los que no se pueden confirmar se cuentan («De 2 lugares más no consta el horario»), pero no se citan.
5. **Redacción** ([`answer.py`](backend/app/assistant/answer.py)). Plantillas en español e inglés, según `idioma`. Si hay pocos resultados, se incluye la descripción y, si se pidió, el horario o el precio. Si falta la traducción de un texto, se indica.

### Medidas contra respuestas sin respaldo

- **Los ids los decide la recuperación.** El redactor recibe el resultado y solo devuelve texto: no puede añadir, quitar ni reordenar ids. Un test sustituye el redactor por uno que «se inventa» un lugar y comprueba que los ids no cambian.
- **Ningún dato desconocido se afirma.** Accesibilidad `null`, horario sin franjas, temporada sin fecha o precio desconocido no cumplen ninguna condición: se dice que no constan.
- **Las condiciones se respetan todas.** «Museos accesibles abiertos el lunes a las 12:00» no devuelve nada, porque los dos museos accesibles cierran los lunes, y lo dice.
- **Un tema reconocido no tapa una condición que no se puede verificar.** «¿Qué museos tienen tirolina?» responde que el catálogo no tiene información sobre la tirolina, en lugar de listar los museos.
- **Las premisas falsas se corrigen con datos.** «¿Cuál es el único sitio accesible?» responde que no hay uno, sino diez, y los enumera.
- **Sin información, no se inventa.** «¿Hay algún sitio de aventura con tirolina?» responde que el catálogo no tiene información sobre «aventura» ni «tirolina», y no cita nada. Una pregunta sin nada buscable recibe una orientación sobre qué se puede preguntar.

### Datos maliciosos

Las descripciones son **datos no confiables**:

- Las frases con forma de instrucción se eliminan al normalizar (DATOS.md, D1). Es una medida de limpieza, no la defensa.
- **La defensa es estructural:**
  - las descripciones solo sirven para encontrar candidatos por sus palabras;
  - la accesibilidad, el horario y el precio salen de campos estructurados;
  - las reglas del asistente están en el código y no dependen de ningún texto del catálogo;
  - un punto que no está en el catálogo no se puede citar.
- Un test lo comprueba con un museo cuya descripción incluye una afirmación falsa que el filtro de D1 no detecta («es el único museo accesible») y una instrucción explícita. El museo no se cita, porque su campo `accesible` es `false`.
- Lo que una descripción sí puede hacer es atraer búsquedas con palabras clave, como cualquier texto. Nunca puede saltarse una condición.

### Si se incorpora un LLM

**Criterio mío:** el texto recuperado se trata como contenido no confiable, y el modelo no puede modificar los filtros, inventar identificadores ni alterar los datos estructurados. Solo redacta a partir de lo recuperado.

En la práctica bastaría con otra implementación de `AnswerWriter` que reciba el mismo `RetrievalResult`. Los ids seguirían saliendo de la recuperación. Habría que añadir una validación del texto generado (que no mencione lugares fuera de los citados) y mantener el redactor de plantillas para los tests y como respaldo sin red.

### Límites conocidos del asistente

- **Vocabulario cerrado.** Entiende los temas y sinónimos que están en `vocabulary.py`. Las palabras del nombre o la descripción de un punto se encuentran igualmente, pero un sinónimo que no esté en ninguna parte («zip line» por «tirolina») no se reconoce, y se dice que no hay información. Ampliarlo es añadir términos a ese fichero.
- **Conservador ante palabras desconocidas.** Como todas las palabras filtran, una palabra de relleno que no esté entre las palabras vacías ni aparezca en el catálogo («fin de semana») hace que responda que no tiene esa información. Es intencionado: es preferible a presentar resultados que no cumplen lo pedido. Se corrige añadiendo la palabra al vocabulario.
- **Una palabra se toma como requisito aunque en la ficha signifique otra cosa.** No hay análisis del sentido. Las fichas son cortas y no ha dado problemas con estos datos.
- **Palabras de tema que forman parte de un nombre.** «¿Está abierto el mirador?» responde sobre todos los puntos con vistas, salvo que la pregunta incluya otra palabra del nombre (por ejemplo, «el Mirador del Alto»).
- **Comparación simple.** Sin tildes ni mayúsculas y con un plural aproximado (quitar una «s» final). No hay corrección de erratas ni análisis gramatical.
- **Etiquetas solo en español.** Por eso los temas del vocabulario incluyen los términos en inglés que corresponden a cada etiqueta.
