# Uso de IA

## Herramientas

- **Claude Code**, desde VS Code, con Claude Opus 5.5. La he utilizado durante todo el desarrollo: para analizar el enunciado y los datos, valorar distintas soluciones, implementar el código y ejecutar las comprobaciones.
- **SonarQube for IDE**, para analizar el código desde el editor.
## Cómo he trabajado

He dividido el trabajo en fases para poder revisar cada parte antes de seguir avanzando:

1. Analizar el enunciado y los datos disponibles.
2. Montar una primera versión funcional de extremo a extremo, con pantalla, API y Nginx, y comprobar que todo arrancaba con Docker.
3. Trabajar en la limpieza de datos, la API, el asistente y la interfaz.
4. Revisar el backend con una auditoría y hacer otra revisión final centrada en la calidad y los posibles errores.

Desde el principio insistí en dos cosas: no dar por hecho que algo funcionaba sin comprobarlo y no documentar decisiones o pruebas que realmente no se hubieran realizado.

## Decisiones que tomé

Estas son algunas de las decisiones que marcaron el desarrollo:

- **Organización del trabajo:** preferí analizar y planificar antes de programar, en lugar de implementar todo de una vez.
- **Idioma del código:** mantuve el código en inglés y el contrato HTTP en español, tal como establece el enunciado.
- **Backend:** pedí separar responsabilidades, evitar `Any`, `cast` y `type: ignore`, y mantener las funciones que calculan horarios independientes del reloj del sistema.
- **Respuestas del asistente:** los lugares citados debían proceder de la búsqueda, no de una decisión posterior al redactar la respuesta.
- **Evaluación:** separé las seis preguntas oficiales de las pruebas adicionales que preparé para detectar regresiones. 
- **Información desconocida:** el asistente no debía afirmar que algo se cumple cuando los datos no permiten comprobarlo. Un ejemplo fue la pregunta «¿Qué museos tienen tirolina?».
- **Negaciones:** distinguí entre que un lugar no sea accesible y que no tengamos información sobre su accesibilidad. Tampoco quería que una pregunta con condiciones contradictorias se resolviera ignorando una de ellas.
- **Interfaz:** opté por guardar los textos en archivos JSON por idioma, usar español por defecto y recordar la preferencia del usuario. Para las traducciones utilicé `@ngx-translate` 18.0.0 y, para el estado, signals de Angular sin añadir una librería específica.

## Soluciones que elegí entre las propuestas

La IA me ayudó a comparar alternativas, pero algunas decisiones importantes fueron elegir una solución frente a otras que también eran posibles.

- **Catálogo:** cargar los datos en memoria y limpiarlos al arrancar la aplicación.
- **Búsqueda:** combinar filtros estructurados con búsqueda por palabras, sin utilizar embeddings.
- **Respuestas:** utilizar plantillas deterministas detrás de una interfaz que permitiría incorporar un LLM en el futuro. Preferí esta opción a depender de un modelo y de una clave externa para una prueba de este alcance.
- **Duplicados:** considerar duplicados los registros con el mismo nombre normalizado y una distancia de 50 metros o menos. Pedí comprobar también los casos próximos al límite.
- **Instrucciones dentro de los datos:** detectar ciertos patrones sospechosos como medida de limpieza, sin tratarla como una defensa infalible. La información estructurada sigue siendo la referencia para aplicar filtros y condiciones.
- **Horarios:** admitir intervalos que cruzan la medianoche, en lugar de descartarlos por simplificar la implementación.
- **Búsqueda por condiciones:** exigir que se cumplan todas las palabras relevantes de la consulta. Reconocer un tema no debía bastar para mostrar lugares que no cumplían el resto de la petición.

## Qué tuve que corregir

Durante el desarrollo aparecieron varios errores que no se detectaron en la primera implementación. Algunos se encontraron probando preguntas manualmente y otros durante las auditorías.

- **Negaciones invertidas:** «no» se descartaba por su longitud y «sin» se trataba como una palabra vacía. Como consecuencia, una pregunta sobre lugares no accesibles podía devolver los accesibles. La auditoría de QA detectó el problema y añadí pruebas que fallaban con el código anterior.
- **Horas interpretadas incorrectamente:** el reconocimiento de horas podía interpretar un número aislado como una hora. Por ejemplo, en «ruta de 7 km», el 7 podía convertirse en las 7:00.
- **Lugares confundidos:** al preguntar «¿Está abierta la ermita?», el asistente podía responder con información de la iglesia.
- **Condiciones de búsqueda incompletas:** al principio, si reconocía el tema principal, podía mostrar resultados que no cumplían el resto de la pregunta. Lo corregí para que todas las palabras relevantes filtraran los resultados.
- **Código contrario a los requisitos:** la IA introdujo dos usos de `type: ignore`, que eliminé porque había pedido expresamente evitarlos.
- **Problema con Docker:** detecté que la ruta de los datos no existía dentro del contenedor al revisar la configuración.
- **Comprobaciones incorrectas:** la IA afirmó que los JSON utilizaban saltos de línea CRLF, cuando eran LF. Lo comprobé byte a byte antes de cambiar nada. También tuve que corregir un script de pruebas de mutación cuyo resultado estaba afectado por la caché de Python.

## Cómo he comprobado el resultado

La IA ejecutó las comprobaciones y revisé los resultados al cerrar cada fase. Estas fueron las principales:

- **Backend:** tests, Ruff, formato y mypy en modo estricto.
- **Frontend:** lint, formato y compilación.
- **API y evaluación:** probé la API real mediante HTTP y ejecuté la evaluación oficial tanto en local como dentro de Docker. El resultado fue de 6/6.
- **Teclado:** comprobé automáticamente en Chrome la navegación por las cuatro pantallas.
