"""
Slovak translation prompt
"""

SLOVAK_TRANSLATION_TEMPLATE = """Please translate the following text into Slovak.

**Translation Guidelines:**
- Maintain the original meaning and nuance WITHOUT simplification or omission
- Keep the translation natural and fluent while preserving information density
- STRICT: Preserve structure, line breaks, bullet points (-, •, ・), headings, and numbering
- Maintain the same tone and style as the original
- Translate line-by-line in the same order; each input line must map to one output line
- Do NOT summarize, generalize, paraphrase, or add metaphors/analogies
- Do NOT include pronunciation guides, romanization, or parenthetical information

**Požiadavky na slovenský preklad:**
- KRITICKÉ: Musíte preložiť VŠETOK obsah len do slovenčiny
- Používajte správnu slovenskú gramatiku a jasnú štruktúru viet
- Preložte VŠETKY slová a frázy z iných jazykov do slovenčiny
- Zachovajte pôvodný význam, podrobnosti a logickú štruktúru
- Používajte prirodzené slovenské výrazy
- NEZACHOVÁVAJTE cudzie slová v preklade
- Uistite sa, že 100% výstupu je len v slovenčine

**CRITICAL OUTPUT INSTRUCTIONS:**
- Output ONLY the translated text in Slovak
- Do NOT include the original text
- Do NOT repeat these instructions or guidelines in your output
- Do NOT add any explanatory text, labels, headers, or meta-commentary
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Start your response directly with the translated content

Text to translate:
{text}
"""

TRANSLATION_INPUT_VARIABLES = ["text"]
