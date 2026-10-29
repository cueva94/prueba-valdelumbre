# DATOS.md — Tratamiento del catálogo

El catálogo `datos/pois.json` contiene 18 puntos de interés con algunas inconsistencias. Antes de utilizarlos en la aplicación, he añadido una fase de limpieza para corregir los errores que se pueden identificar con suficiente seguridad y evitar que el asistente dé información incorrecta.

Los datos originales se mantienen sin modificar. Las reglas de limpieza se aplican al cargar el catálogo y las incidencias quedan registradas para poder revisar qué ha ocurrido.

## Problemas encontrados

- **Texto con instrucciones dirigidas al asistente.** La descripción de uno de los museos incluía una instrucción para recomendarlo como accesible, aunque el dato del catálogo indicaba lo contrario. Se elimina ese fragmento de la descripción. En cualquier caso, las condiciones como la accesibilidad se comprueban utilizando los campos del catálogo, no el texto libre.
- **Registro duplicado.** Había una ficha antigua del Museo del Aceite con información incompleta que correspondía al mismo lugar que otra ficha más completa. Se conserva la ficha más completa y se excluye la duplicada.
- **Coordenadas incorrectas.** Un punto tenía la latitud y la longitud intercambiadas, lo que lo situaba muy lejos del pueblo. Se corrigen cuando el patrón permite identificar el error con suficiente seguridad. Si no es posible determinar la posición correcta, no se muestra el punto en el mapa.
- **Precios con formatos diferentes.** Se normalizan valores como importes numéricos, «gratis» o rangos de precios. Los textos que no se pueden interpretar con seguridad se conservan para mostrarlos, pero no se utilizan como valores numéricos.
- **Datos de accesibilidad incompletos.** Un valor desconocido no se interpreta como accesible ni como no accesible. El asistente indica que no consta esa información.
- **Horarios ausentes o incompletos.** Si no hay información suficiente para determinar si un lugar está abierto, se mantiene ese estado como desconocido en lugar de asumir que está cerrado.
- **Horarios de temporada.** Algunos horarios solo son válidos durante determinados meses. Para confirmar si un lugar está abierto en esos casos es necesario conocer la fecha.
- **Categorías y textos inconsistentes.** Se ignoran las diferencias de mayúsculas, tildes y espacios al comparar categorías y nombres, pero se conserva el texto original para mostrarlo.
- **Traducciones vacías.** Si falta el nombre o la descripción en inglés, se utiliza el contenido en español y se indica el idioma real del texto.

Después de aplicar las reglas, se publican 17 de los 18 registros originales. El restante se excluye por estar duplicado.

## Criterios de limpieza

He seguido cuatro criterios principales:

1. **Conservar los datos originales.** Las correcciones se aplican mediante código, sin modificar manualmente los ficheros de partida.
2. **Aplicar reglas generales.** Las reglas buscan resolver tipos de problemas, en lugar de introducir excepciones específicas para cada registro.
3. **No inventar información.** Cuando un valor no se puede interpretar con seguridad, se mantiene como desconocido o se descarta si impide utilizar el dato correctamente.
4. **Registrar las incidencias.** Las correcciones y exclusiones quedan documentadas para facilitar su revisión.

### Tratamiento de los horarios

Los horarios se comprueban con las mismas reglas tanto en la API como en el asistente.

- A la hora de cierre, el establecimiento ya se considera cerrado.
- Se contemplan los horarios que continúan después de medianoche.
- Los horarios que dependen de una temporada necesitan una fecha para poder confirmarse.
- Si una franja horaria no se puede interpretar correctamente, se descarta y no se da por hecho que el establecimiento esté cerrado.

## Limitaciones

La limpieza reduce los errores, pero no puede resolver todos los casos automáticamente.

- La detección de instrucciones dentro de las descripciones se basa en patrones y puede pasar por alto otras formas de redactarlas o marcar texto legítimo por error.
- La detección de duplicados requiere que coincidan el nombre normalizado y la proximidad entre los puntos. Por eso, puede no detectar dos fichas del mismo lugar si tienen nombres diferentes.
- La corrección de coordenadas identifica errores evidentes, pero no permite detectar con seguridad todos los desplazamientos.
- La accesibilidad se representa mediante un único campo, por lo que no distingue entre necesidades diferentes.
- Cuando faltan datos de horarios, precios o accesibilidad, la aplicación no puede ofrecer una respuesta definitiva sobre esas condiciones.

## Evaluación de los datos

El fichero `datos/evaluacion.json` contiene las seis preguntas proporcionadas con la prueba. Se utiliza para comprobar que las respuestas del asistente incluyen los puntos de interés esperados y no citan los que deberían quedar excluidos.

El resultado obtenido es de **6/6 respuestas correctas**. El criterio de evaluación y los detalles para ejecutar la comprobación están en el [README](README.md#evaluación).
