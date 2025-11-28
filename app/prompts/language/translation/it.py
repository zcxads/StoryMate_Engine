"""
Italian translation prompt
"""

ITALIAN_TRANSLATION_TEMPLATE = """Please translate the following text into Italian.

**Translation Guidelines:**
- Maintain the original meaning and nuance WITHOUT simplification or omission
- Keep the translation natural and fluent while preserving information density
- STRICT: Preserve structure, line breaks, bullet points (-, •, ・), headings, and numbering
- Maintain the same tone and style as the original
- Translate line-by-line in the same order; each input line must map to one output line
- Do NOT summarize, generalize, paraphrase, or add metaphors/analogies
- Do NOT include pronunciation guides, romanization, or parenthetical information

**Requisiti di traduzione italiana:**
- CRITICO: Devi tradurre TUTTI i contenuti solo in italiano
- Usa una grammatica italiana appropriata e una struttura chiara delle frasi
- Traduci TUTTE le parole e frasi di altre lingue in italiano
- Mantieni il significato originale, i dettagli e la struttura logica
- Usa espressioni italiane naturali
- NON mantenere parole in lingue straniere nella traduzione
- Assicurati che il 100% dell'output sia solo in italiano

**CRITICAL OUTPUT INSTRUCTIONS:**
- Output ONLY the translated text in Italian
- Do NOT include the original text
- Do NOT repeat these instructions or guidelines in your output
- Do NOT add any explanatory text, labels, headers, or meta-commentary
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Start your response directly with the translated content

Text to translate:
{text}
"""

TRANSLATION_INPUT_VARIABLES = ["text"]
