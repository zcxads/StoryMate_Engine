"""
Norwegian translation prompt
"""

NORWEGIAN_TRANSLATION_TEMPLATE = """Please translate the following text into Norwegian.

**Translation Guidelines:**
- Maintain the original meaning and nuance WITHOUT simplification or omission
- Keep the translation natural and fluent while preserving information density
- STRICT: Preserve structure, line breaks, bullet points (-, •, ・), headings, and numbering
- Maintain the same tone and style as the original
- Translate line-by-line in the same order; each input line must map to one output line
- Do NOT summarize, generalize, paraphrase, or add metaphors/analogies
- Do NOT include pronunciation guides, romanization, or parenthetical information

**Norske oversettelseskrav:**
- KRITISK: Du MÅ oversette ALT innhold kun til norsk
- Bruk korrekt norsk grammatikk og klar setningsstruktur
- Oversett ALLE ord og setninger fra andre språk til norsk
- Bevar den opprinnelige betydningen, detaljer og logisk struktur
- Bruk naturlige norske uttrykk
- Behold IKKE fremmedspråklige ord i oversettelsen
- Sørg for at 100% av output kun er på norsk

**CRITICAL OUTPUT INSTRUCTIONS:**
- Output ONLY the translated text in Norwegian
- Do NOT include the original text
- Do NOT repeat these instructions or guidelines in your output
- Do NOT add any explanatory text, labels, headers, or meta-commentary
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Start your response directly with the translated content

Text to translate:
{text}
"""

TRANSLATION_INPUT_VARIABLES = ["text"]
