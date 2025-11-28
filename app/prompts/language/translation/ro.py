"""
Romanian translation prompt
"""

ROMANIAN_TRANSLATION_TEMPLATE = """Please translate the following text into Romanian.

**Translation Guidelines:**
- Maintain the original meaning and nuance WITHOUT simplification or omission
- Keep the translation natural and fluent while preserving information density
- STRICT: Preserve structure, line breaks, bullet points (-, •, ・), headings, and numbering
- Maintain the same tone and style as the original
- Translate line-by-line in the same order; each input line must map to one output line
- Do NOT summarize, generalize, paraphrase, or add metaphors/analogies
- Do NOT include pronunciation guides, romanization, or parenthetical information

**Cerințe de traducere în română:**
- CRITIC: Trebuie să traduceți TOT conținutul doar în română
- Utilizați gramatică română corectă și structură clară a propozițiilor
- Traduceți TOATE cuvintele și expresiile din alte limbi în română
- Păstrați sensul original, detaliile și structura logică
- Utilizați expresii naturale în română
- NU păstrați cuvinte în limbi străine în traducere
- Asigurați-vă că 100% din rezultat este doar în română

**CRITICAL OUTPUT INSTRUCTIONS:**
- Output ONLY the translated text in Romanian
- Do NOT include the original text
- Do NOT repeat these instructions or guidelines in your output
- Do NOT add any explanatory text, labels, headers, or meta-commentary
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Start your response directly with the translated content

Text to translate:
{text}
"""

TRANSLATION_INPUT_VARIABLES = ["text"]
