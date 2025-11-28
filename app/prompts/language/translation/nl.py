"""
Dutch translation prompt
"""

DUTCH_TRANSLATION_TEMPLATE = """Please translate the following text into Dutch.

**Translation Guidelines:**
- Maintain the original meaning and nuance WITHOUT simplification or omission
- Keep the translation natural and fluent while preserving information density
- STRICT: Preserve structure, line breaks, bullet points (-, •, ・), headings, and numbering
- Maintain the same tone and style as the original
- Translate line-by-line in the same order; each input line must map to one output line
- Do NOT summarize, generalize, paraphrase, or add metaphors/analogies
- Do NOT include pronunciation guides, romanization, or parenthetical information

**Nederlandse vertaalvereisten:**
- KRITISCH: U MOET ALLE inhoud alleen naar het Nederlands vertalen
- Gebruik correcte Nederlandse grammatica en duidelijke zinsstructuur
- Vertaal ALLE woorden en zinnen uit andere talen naar het Nederlands
- Behoud de oorspronkelijke betekenis, details en logische structuur
- Gebruik natuurlijke Nederlandse uitdrukkingen
- Behoud GEEN vreemde woorden in de vertaling
- Zorg ervoor dat 100% van de output alleen in het Nederlands is

**CRITICAL OUTPUT INSTRUCTIONS:**
- Output ONLY the translated text in Dutch
- Do NOT include the original text
- Do NOT repeat these instructions or guidelines in your output
- Do NOT add any explanatory text, labels, headers, or meta-commentary
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Start your response directly with the translated content

Text to translate:
{text}
"""

TRANSLATION_INPUT_VARIABLES = ["text"]
