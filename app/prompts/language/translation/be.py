"""
Belarusian translation prompt
"""

BELARUSIAN_TRANSLATION_TEMPLATE = """Please translate the following text into Belarusian.

**Translation Guidelines:**
- Maintain the original meaning and nuance WITHOUT simplification or omission
- Keep the translation natural and fluent while preserving information density
- STRICT: Preserve structure, line breaks, bullet points (-, •, ・), headings, and numbering
- Maintain the same tone and style as the original
- Translate line-by-line in the same order; each input line must map to one output line
- Do NOT summarize, generalize, paraphrase, or add metaphors/analogies
- Do NOT include pronunciation guides, romanization, or parenthetical information

**Патрабаванні да перакладу на беларускую мову:**
- КРЫТЫЧНА: Вы ПАВІННЫ перакласці ВСЁ змесціва толькі на беларускую мову
- Выкарыстоўвайце правільную беларускую граматыку і выразную структуру сказаў
- Перакладзіце ВСЕ словы і фразы з іншых моў на беларускую
- Захавайце арыгінальны сэнс, дэталі і лагічную структуру
- Выкарыстоўвайце натуральныя беларускія выразы
- НЕ пакідайце іншамоўныя словы ў перакладзе
- Пераканайцеся, што 100% вываду толькі на беларускай мове

**CRITICAL OUTPUT INSTRUCTIONS:**
- Output ONLY the translated text in Belarusian
- Do NOT include the original text
- Do NOT repeat these instructions or guidelines in your output
- Do NOT add any explanatory text, labels, headers, or meta-commentary
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Start your response directly with the translated content

Text to translate:
{text}
"""

TRANSLATION_INPUT_VARIABLES = ["text"]
