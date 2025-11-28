"""
Spanish translation prompt
"""

SPANISH_TRANSLATION_TEMPLATE = """Please translate the following text into Spanish.

**Translation Guidelines:**
- Maintain the original meaning and nuance WITHOUT simplification or omission
- Keep the translation natural and fluent while preserving information density
- STRICT: Preserve structure, line breaks, bullet points (-, •, ・), headings, and numbering
- Maintain the same tone and style as the original
- Translate line-by-line in the same order; each input line must map to one output line
- Do NOT summarize, generalize, paraphrase, or add metaphors/analogies
- Do NOT include pronunciation guides, romanization, or parenthetical information

**Requisitos de traducción al español:**
- CRÍTICO: Debe traducir TODO el contenido solo al español
- Use gramática española adecuada y estructura de oraciones claras
- Traduzca TODAS las palabras y frases de otros idiomas al español
- Mantenga el significado original, los detalles y la estructura lógica
- Use expresiones naturales en español
- NO mantenga palabras en idiomas extranjeros en la traducción
- Asegúrese de que el 100% de la salida esté solo en español

**CRITICAL OUTPUT INSTRUCTIONS:**
- Output ONLY the translated text in Spanish
- Do NOT include the original text
- Do NOT repeat these instructions or guidelines in your output
- Do NOT add any explanatory text, labels, headers, or meta-commentary
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Start your response directly with the translated content

Text to translate:
{text}
"""

TRANSLATION_INPUT_VARIABLES = ["text"]
