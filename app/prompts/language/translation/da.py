"""
Danish translation prompt
"""

DANISH_TRANSLATION_TEMPLATE = """Please translate the following text into Danish.

**Translation Guidelines:**
- Maintain the original meaning and nuance WITHOUT simplification or omission
- Keep the translation natural and fluent while preserving information density
- STRICT: Preserve structure, line breaks, bullet points (-, •, ・), headings, and numbering
- Maintain the same tone and style as the original
- Translate line-by-line in the same order; each input line must map to one output line
- Do NOT summarize, generalize, paraphrase, or add metaphors/analogies
- Do NOT include pronunciation guides, romanization, or parenthetical information

**Danske oversættelseskrav:**
- KRITISK: Du SKAL oversætte ALT indhold kun til dansk
- Brug korrekt dansk grammatik og klar sætningsstruktur
- Oversæt ALLE ord og sætninger fra andre sprog til dansk
- Bevar den oprindelige betydning, detaljer og logiske struktur
- Brug naturlige danske udtryk
- Behold IKKE fremmedsprogede ord i oversættelsen
- Sørg for, at 100% af output kun er på dansk

**CRITICAL OUTPUT INSTRUCTIONS:**
- Output ONLY the translated text in Danish
- Do NOT include the original text
- Do NOT repeat these instructions or guidelines in your output
- Do NOT add any explanatory text, labels, headers, or meta-commentary
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Start your response directly with the translated content

Text to translate:
{text}
"""

TRANSLATION_INPUT_VARIABLES = ["text"]
