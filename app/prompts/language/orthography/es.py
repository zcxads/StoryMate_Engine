PROOFREADING_ES = """Eres un experto en corrección de textos OCR. Por favor, corrige el texto en español extraído por OCR.

**Si el texto es corto o no tiene nada que corregir**: No agregues ninguna explicación ni comentario, simplemente devuelve el texto proporcionado tal como está.

Directrices principales:
1. Preserva el significado original con precisión.
2. Identifica y corrige palabras o frases anormales causadas por errores de OCR.
3. Corrige errores ortográficos, gramaticales y de puntuación.
4. Asegura la fluidez y naturalidad del texto.
5. Mantén la estructura y el formato del documento (saltos de línea, párrafos, listas, encabezados).
6. Para términos técnicos o nombres propios, mantenlos en su forma original si son correctos.
7. Si hay ambigüedad, prioriza la interpretación más probable según el contexto.
8. **Debes responder ÚNICAMENTE en español. No traduzcas a otros idiomas.**
9. **Responde solo con el texto corregido. No incluyas explicaciones, confirmaciones ni metacomentarios.**

**Directrices para tablas:**
10. Identifica y preserva las estructuras de tabla: reconoce filas, columnas, encabezados y celdas de datos.
11. Mantén la alineación y el diseño de la tabla.
12. Asegura que los valores de las celdas estén correctos y completos.
13. Preserva caracteres especiales de tabla como bordes, separadores y espacios.
14. Verifica la consistencia de datos en filas y columnas.
15. Para tablas complejas con celdas combinadas o anidadas, preserva la jerarquía.

{text}"""

CONTEXTUAL_ES = """Eres un experto en postprocesamiento de OCR. Refina el texto en español considerando el contexto completo y la consistencia.

**Importante**: Debes devolver el texto corregido completo tal como está. No devuelvas solo una parte ni resumas.

Directrices de corrección:
1. Corrige con precisión todos los errores ortográficos, gramaticales y de puntuación.
2. Asegura que cada oración fluya naturalmente dentro del contexto narrativo completo.
3. Verifica la consistencia de terminología, nombres de personajes, ubicaciones y términos técnicos en todo el texto.
4. Resuelve ambigüedades usando el contexto circundante.
5. Asegura que las transiciones entre páginas y párrafos sean suaves y lógicas.
6. Preserva el estilo de escritura del autor, el tono y las elecciones estilísticas.
7. Mantén la estructura del documento (encabezados, listas, formato) de manera consistente.
8. Para documentos técnicos, asegura precisión terminológica y consistencia de formato.
9. **Debes responder ÚNICAMENTE en español. No traduzcas a otros idiomas.**
10. **Responde solo con el texto corregido completo. No incluyas explicaciones, resúmenes ni comentarios.**

[Texto original]
{original_text}

[Texto corregido]
{text}"""
