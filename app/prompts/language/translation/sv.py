"""
Swedish translation prompt
"""

SWEDISH_TRANSLATION_TEMPLATE = """Please translate the following text into Swedish.

**Translation Guidelines:**
- Maintain the original meaning and nuance WITHOUT simplification or omission
- Keep the translation natural and fluent while preserving information density
- STRICT: Preserve structure, line breaks, bullet points (-, •, ・), headings, and numbering
- Maintain the same tone and style as the original
- Translate line-by-line in the same order; each input line must map to one output line
- Do NOT summarize, generalize, paraphrase, or add metaphors/analogies
- Do NOT include pronunciation guides, romanization, or parenthetical information

**Svenska översättningskrav:**
- KRITISKT: Du MÅSTE översätta ALLT innehåll endast till svenska
- Använd korrekt svensk grammatik och tydlig meningsstruktur
- Översätt ALLA ord och fraser från andra språk till svenska
- Behåll den ursprungliga betydelsen, detaljerna och den logiska strukturen
- Använd naturliga svenska uttryck
- Behåll INTE främmande ord i översättningen
- Se till att 100% av utdata endast är på svenska

**CRITICAL OUTPUT INSTRUCTIONS:**
- Output ONLY the translated text in Swedish
- Do NOT include the original text
- Do NOT repeat these instructions or guidelines in your output
- Do NOT add any explanatory text, labels, headers, or meta-commentary
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Start your response directly with the translated content

Text to translate:
{text}
"""

TRANSLATION_INPUT_VARIABLES = ["text"]
