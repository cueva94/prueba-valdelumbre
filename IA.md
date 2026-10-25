# Uso de IA

## Herramientas

- **Claude Code** (extensión de VS Code, modelo Claude Opus 5.5). La he usado para analizar el enunciado y los datos, proponer la arquitectura y el plan, generar código y comandos, y comprobar los resultados ejecutándolos.

## Cómo he trabajado con ella

- Primero le pedí **análisis, arquitectura y plan, sin programar**. Después, implementar por fases y validar cada una (comandos ejecutados y resultados reales) antes de hacer commit.
- La IA propone y yo acepto, modifico o descarto. Abajo queda el registro.
- Le pedí que no diera nada por funcionando sin ejecutarlo, y que no se inventara decisiones ni comprobaciones en esta documentación.

## Registro de decisiones

### Análisis y plan

**Propuesta de la IA:**
- El inventario de defectos de los datos (ver [DATOS.md](DATOS.md)).
- Lo que evalúa cada pregunta de `evaluacion.json`.
- Seis decisiones para las ambigüedades del enunciado.
- Una arquitectura en la que el catálogo vive en memoria y se limpia al arrancar, el asistente combina filtros estructurados y búsqueda por palabras (sin embeddings), y los ids citados los decide la búsqueda, no el generador de texto.
- Un plan por fases.

**Aceptado:**
- Las seis decisiones sobre ambigüedades (README → Decisiones), con una condición mía: si alguna contradice el enunciado, prevalece el enunciado y se documenta el motivo.
- Plantillas deterministas por defecto, con una interfaz preparada para incorporar un LLM más adelante.
- Código en español, coherente con el contrato y los datos.

### Git y GitHub

- **Cuenta:** el proyecto va en mi cuenta personal (`cueva94`), no en la del trabajo. La IA comprobó que la configuración global de Git y la sesión de `gh` eran las del trabajo, y configuró la identidad solo para este repositorio, sin tocar la global.
- **Correo de los commits:** la IA señaló que mi correo principal está marcado como privado en GitHub, y que publicarlo en el historial lo expondría o haría que GitHub rechazara el push. Propuso el correo `noreply` de GitHub. **Aceptado.**
- **`Co-Authored-By: Claude` en cada commit:** propuesto por la IA. **Descartado:** prefiero documentar el uso real de la IA en este fichero.
- **`ENUNCIADO.md`:** queda fuera del repositorio público, porque no consta que la empresa autorice publicarlo. Conservo una copia local (excluida solo en mi máquina mediante `.git/info/exclude`) y los requisitos se resumen en el README.

### Esqueleto del proyecto

Al instalar y validar aparecieron varios avisos de las herramientas. Ninguno se aplicó ni se ignoró sin más: cada uno se comprobó en su origen antes de decidir.

| Aviso | Comprobación | Decisión |
|---|---|---|
| Starlette marca `httpx` como obsoleto en el cliente de tests y recomienda `httpx2` | Metadatos del paquete: lo firma el autor de `httpx` y lo publica la organización de Pydantic. Starlette lo importa en primer lugar | Cambiado a `httpx2` |
| Angular 22 marca `withFetch()` como obsoleto | La nota de obsolescencia en el código de Angular indica que `FetchBackend` ya es el backend por defecto | Eliminado |
| npm bloqueó los scripts de instalación de 4 paquetes | El build y los tests pasan sin ellos | Denegados de forma explícita (`allowScripts`), y `--ignore-scripts` en Docker |
| El analizador del IDE (SonarQube for IDE, que no es una herramienta de IA) sugiere `<output>` en lugar de `role="status"` | — | Descartado: `role="status"` es el patrón más extendido para anunciar cambios a los lectores de pantalla, y `<output>` se anuncia de forma menos consistente en algunos. Se comprobará con NVDA en la fase de la pantalla |

### Repositorio remoto

- La IA propuso crear el repositorio como **privado** durante el desarrollo y hacerlo público al entregar, para que el trabajo a medias no fuera visible antes de tiempo. **Aceptado.**

### Limpieza de datos

**Lo que hizo la IA:** implementó las reglas acordadas en el análisis (DATOS.md, D1 a D9) y las pruebas. Antes de escribir los tests ejecutó la limpieza sobre los datos reales para comprobar su efecto.

**Decisiones de detalle tomadas por la IA durante la implementación** (documentadas en DATOS.md → Límites conocidos):
- Umbrales: 50 km para decidir si un punto está fuera del pueblo y 50 m para considerar duplicados dos registros con el mismo nombre.
- Las franjas que cruzan la medianoche se descartan en lugar de interpretarse, porque no hay ninguna en los datos y así no se da por abierto algo que no lo está.
- Los duplicados exigen el mismo nombre normalizado, sin similitud aproximada, para no fusionar lugares distintos.
- Reglas preventivas (V) para registros mal formados que no aparecen en los datos actuales.

**Cómo se comprobó que los tests sirven:** además de ejecutarlos (81 en verde), se introdujeron a propósito cuatro fallos en el código, uno cada vez: incluir la hora de cierre, conservar el duplicado menos completo, no detectar instrucciones dirigidas al asistente y no corregir coordenadas. Los tests detectaron los cuatro, y el código se restauró después.

**Sugerencia del analizador del IDE:** partir dos `assert a and b` en asserts separados, para que un fallo indique qué condición concreta no se cumple. **Aceptada.**

### Errores de la IA detectados

- **Saltos de línea:** la IA afirmó que los JSON usaban CRLF, a partir de un recuento con `grep` mal planteado. Al comprobarlo byte a byte resultó falso: son LF. Se corrigió antes de actuar sobre esa base. La regla de `.gitattributes` para `datos/` se mantuvo, pero por el motivo correcto: evitar que Git convierta los saltos de línea al clonar en Windows.
- **Guion largo en el código:** para aclarar al linter que el guion largo (U+2013) de la expresión de precios es intencionado, la IA intentó escribirlo como secuencia de escape (barra invertida seguida de `u2013`). Dos intentos dejaron el carácter literal, porque la herramienta de edición interpretaba la secuencia. El linter lo detectó las dos veces, y se resolvió con un script que construye la secuencia sin escribirla literalmente.

## Enfoque del asistente y medidas contra respuestas sin respaldo

Se completará en la fase del asistente. El diseño acordado es este:

- Los ids citados los decide la búsqueda sobre el catálogo; el generador solo redacta el texto.
- Los hechos (accesibilidad, horario, categoría) salen de campos estructurados, y las descripciones se tratan como datos no confiables.
- Si nada en el catálogo responde a la pregunta, el asistente lo dice y no cita ningún punto.
