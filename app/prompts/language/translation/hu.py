"""
Hungarian translation prompt
"""

HUNGARIAN_TRANSLATION_TEMPLATE = """Please translate the following text into Hungarian.

**Translation Guidelines:**
- Maintain the original meaning and nuance WITHOUT simplification or omission
- Keep the translation natural and fluent while preserving information density
- STRICT: Preserve structure, line breaks, bullet points (-, •, ・), headings, and numbering
- Maintain the same tone and style as the original
- Translate line-by-line in the same order; each input line must map to one output line
- Do NOT summarize, generalize, paraphrase, or add metaphors/analogies
- Do NOT include pronunciation guides, romanization, or parenthetical information

**Magyar fordítási követelmények:**
- KRITIKUS: MINDEN tartalmat CSAK magyarra kell fordítania
- Használjon helyes magyar nyelvtant és világos mondatszerkezetet
- Fordítson le MINDEN szót és kifejezést más nyelvekből magyarra
- Őrizze meg az eredeti jelentést, részleteket és logikai szerkezetet
- Használjon természetes magyar kifejezéseket
- NE tartson meg idegen nyelvű szavakat a fordításban
- Győződjön meg róla, hogy a kimenet 100%-a csak magyarul van

**CRITICAL OUTPUT INSTRUCTIONS:**
- Output ONLY the translated text in Hungarian
- Do NOT include the original text
- Do NOT repeat these instructions or guidelines in your output
- Do NOT add any explanatory text, labels, headers, or meta-commentary
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Start your response directly with the translated content

Text to translate:
{text}
"""

TRANSLATION_INPUT_VARIABLES = ["text"]
