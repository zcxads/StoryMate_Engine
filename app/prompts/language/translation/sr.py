"""
Serbian translation prompt
"""

SERBIAN_TRANSLATION_TEMPLATE = """Please translate the following text into Serbian.

**Translation Guidelines:**
- Maintain the original meaning and nuance WITHOUT simplification or omission
- Keep the translation natural and fluent while preserving information density
- STRICT: Preserve structure, line breaks, bullet points (-, •, ・), headings, and numbering
- Maintain the same tone and style as the original
- Translate line-by-line in the same order; each input line must map to one output line
- Do NOT summarize, generalize, paraphrase, or add metaphors/analogies
- Do NOT include pronunciation guides, romanization, or parenthetical information

**Zahtevi za prevod na srpski:**
- KRITIČNO: Morate prevesti SAV sadržaj samo na srpski
- Koristite ispravnu srpsku gramatiku i jasnu strukturu rečenice
- Prevedite SVE reči i fraze sa drugih jezika na srpski
- Zadržite originalno značenje, detalje i logičku strukturu
- Koristite prirodne srpske izraze
- NE zadržavajte strane reči u prevodu
- Uverite se da je 100% izlaza samo na srpskom

**CRITICAL OUTPUT INSTRUCTIONS:**
- Output ONLY the translated text in Serbian
- Do NOT include the original text
- Do NOT repeat these instructions or guidelines in your output
- Do NOT add any explanatory text, labels, headers, or meta-commentary
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Start your response directly with the translated content

Text to translate:
{text}
"""

TRANSLATION_INPUT_VARIABLES = ["text"]
