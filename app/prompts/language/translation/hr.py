"""
Croatian translation prompt
"""

CROATIAN_TRANSLATION_TEMPLATE = """Please translate the following text into Croatian.

**Translation Guidelines:**
- Maintain the original meaning and nuance WITHOUT simplification or omission
- Keep the translation natural and fluent while preserving information density
- STRICT: Preserve structure, line breaks, bullet points (-, •, ・), headings, and numbering
- Maintain the same tone and style as the original
- Translate line-by-line in the same order; each input line must map to one output line
- Do NOT summarize, generalize, paraphrase, or add metaphors/analogies
- Do NOT include pronunciation guides, romanization, or parenthetical information

**Zahtjevi za hrvatski prijevod:**
- KRITIČNO: Morate prevesti SAV sadržaj samo na hrvatski
- Koristite ispravnu hrvatsku gramatiku i jasnu strukturu rečenice
- Prevedite SVE riječi i fraze s drugih jezika na hrvatski
- Zadržite izvorni smisao, detalje i logičku strukturu
- Koristite prirodne hrvatske izraze
- NE zadržavajte strane riječi u prijevodu
- Uvjerite se da je 100% izlaza samo na hrvatskom

**CRITICAL OUTPUT INSTRUCTIONS:**
- Output ONLY the translated text in Croatian
- Do NOT include the original text
- Do NOT repeat these instructions or guidelines in your output
- Do NOT add any explanatory text, labels, headers, or meta-commentary
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Start your response directly with the translated content

Text to translate:
{text}
"""

TRANSLATION_INPUT_VARIABLES = ["text"]
