"""
Czech translation prompt
"""

CZECH_TRANSLATION_TEMPLATE = """Please translate the following text into Czech.

**Translation Guidelines:**
- Maintain the original meaning and nuance WITHOUT simplification or omission
- Keep the translation natural and fluent while preserving information density
- STRICT: Preserve structure, line breaks, bullet points (-, •, ・), headings, and numbering
- Maintain the same tone and style as the original
- Translate line-by-line in the same order; each input line must map to one output line
- Do NOT summarize, generalize, paraphrase, or add metaphors/analogies
- Do NOT include pronunciation guides, romanization, or parenthetical information

**Požadavky na český překlad:**
- KRITICKÉ: Musíte přeložit VEŠKERÝ obsah pouze do češtiny
- Používejte správnou českou gramatiku a jasnou strukturu vět
- Přeložte VŠECHNA slova a fráze z jiných jazyků do češtiny
- Zachovejte původní význam, podrobnosti a logickou strukturu
- Používejte přirozené české výrazy
- NEZACHOVÁVEJTE cizí slova v překladu
- Ujistěte se, že 100% výstupu je pouze v češtině

**CRITICAL OUTPUT INSTRUCTIONS:**
- Output ONLY the translated text in Czech
- Do NOT include the original text
- Do NOT repeat these instructions or guidelines in your output
- Do NOT add any explanatory text, labels, headers, or meta-commentary
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Start your response directly with the translated content

Text to translate:
{text}
"""

TRANSLATION_INPUT_VARIABLES = ["text"]
