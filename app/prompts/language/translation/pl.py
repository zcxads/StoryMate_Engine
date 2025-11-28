"""
Polish translation prompt
"""

POLISH_TRANSLATION_TEMPLATE = """Please translate the following text into Polish.

**Translation Guidelines:**
- Maintain the original meaning and nuance WITHOUT simplification or omission
- Keep the translation natural and fluent while preserving information density
- STRICT: Preserve structure, line breaks, bullet points (-, •, ・), headings, and numbering
- Maintain the same tone and style as the original
- Translate line-by-line in the same order; each input line must map to one output line
- Do NOT summarize, generalize, paraphrase, or add metaphors/analogies
- Do NOT include pronunciation guides, romanization, or parenthetical information

**Wymagania tłumaczenia polskiego:**
- KRYTYCZNE: Musisz przetłumaczyć CAŁĄ treść tylko na język polski
- Używaj właściwej gramatyki polskiej i przejrzystej struktury zdań
- Przetłumacz WSZYSTKIE słowa i zwroty z innych języków na polski
- Zachowaj oryginalne znaczenie, szczegóły i strukturę logiczną
- Używaj naturalnych polskich wyrażeń
- NIE zachowuj obcojęzycznych słów w tłumaczeniu
- Upewnij się, że 100% wyniku jest tylko po polsku

**CRITICAL OUTPUT INSTRUCTIONS:**
- Output ONLY the translated text in Polish
- Do NOT include the original text
- Do NOT repeat these instructions or guidelines in your output
- Do NOT add any explanatory text, labels, headers, or meta-commentary
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Start your response directly with the translated content

Text to translate:
{text}
"""

TRANSLATION_INPUT_VARIABLES = ["text"]
