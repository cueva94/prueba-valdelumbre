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
| Código en español, coherente con el contrato y los datos | Propuesta de la IA → aceptada | — |

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
| SonarQube sugiere `<output>` en lugar de `role="status"` | — | Descartado: `role="status"` es el patrón más extendido para anunciar cambios a los lectores de pantalla. Se comprobará con NVDA en la fase de la pantalla |

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

## Errores de la IA detectados

- **Saltos de línea.** La IA afirmó que los JSON usaban CRLF, a partir de un recuento con `grep` mal planteado. Al comprobarlo byte a byte resultó falso: son LF. Se corrigió antes de actuar sobre esa base. La regla de `.gitattributes` para `datos/` se mantuvo, pero por el motivo correcto: evitar que Git convierta los saltos de línea al clonar en Windows.
- **Guion largo en el código.** Para aclarar al linter que el guion largo (U+2013) de la expresión de precios es intencionado, la IA intentó escribirlo como secuencia de escape (barra invertida seguida de `u2013`). Dos intentos dejaron el carácter literal, porque la herramienta de edición interpretaba la secuencia. El linter lo detectó las dos veces, y se resolvió con un script que construye la secuencia sin escribirla literalmente.
- **Caché en las pruebas de mutación.** La primera versión del script que introduce fallos no aislaba la caché de bytecode de Python. Cuando un fallo y su restauración tenían el mismo tamaño y ocurrían en el mismo segundo, Python reutilizaba la versión con el fallo. Se notó porque, tras restaurar el código, un test seguía fallando. Una cifra del informe anterior estaba contaminada por ello (7 tests fallidos en lugar de 3), aunque la conclusión se mantenía. Se corrigió el script, que ahora borra las cachés y ejecuta Python con `-B`, y se repitieron todas las mutaciones.

## Enfoque del asistente y medidas contra respuestas sin respaldo

Se completará en la fase del asistente. El diseño acordado es este:

- Los ids citados los decide la búsqueda sobre el catálogo; el generador solo redacta el texto.
- Los hechos (accesibilidad, horario, categoría) salen de campos estructurados, y las descripciones se tratan como datos no confiables.
- Si nada en el catálogo responde a la pregunta, el asistente lo dice y no cita ningún punto.
- **Si más adelante se incorpora un LLM** (criterio mío): el texto recuperado se trata como contenido no confiable, y el modelo no puede modificar los filtros, inventar identificadores ni alterar los datos estructurados. Solo redacta a partir de lo recuperado.
