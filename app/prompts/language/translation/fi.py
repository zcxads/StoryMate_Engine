"""
Finnish translation prompt
"""

FINNISH_TRANSLATION_TEMPLATE = """Please translate the following text into Finnish.

**Translation Guidelines:**
- Maintain the original meaning and nuance WITHOUT simplification or omission
- Keep the translation natural and fluent while preserving information density
- STRICT: Preserve structure, line breaks, bullet points (-, •, ・), headings, and numbering
- Maintain the same tone and style as the original
- Translate line-by-line in the same order; each input line must map to one output line
- Do NOT summarize, generalize, paraphrase, or add metaphors/analogies
- Do NOT include pronunciation guides, romanization, or parenthetical information

**Suomen käännösvaatimukset:**
- KRIITTINEN: Sinun TÄYTYY kääntää KAIKKI sisältö vain suomeksi
- Käytä oikeaa suomen kielioppia ja selkeää lauserakennetta
- Käännä KAIKKI sanat ja lauseet muista kielistä suomeksi
- Säilytä alkuperäinen merkitys, yksityiskohdat ja looginen rakenne
- Käytä luonnollisia suomenkielisiä ilmaisuja
- ÄLÄ säilytä vieraskielisiä sanoja käännöksessä
- Varmista, että 100% tulosteesta on vain suomeksi

**CRITICAL OUTPUT INSTRUCTIONS:**
- Output ONLY the translated text in Finnish
- Do NOT include the original text
- Do NOT repeat these instructions or guidelines in your output
- Do NOT add any explanatory text, labels, headers, or meta-commentary
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Start your response directly with the translated content

Text to translate:
{text}
"""

TRANSLATION_INPUT_VARIABLES = ["text"]
