"""
Russian translation prompt
"""

RUSSIAN_TRANSLATION_TEMPLATE = """Please translate the following text into Russian.

**Translation Guidelines:**
- Maintain the original meaning and nuance WITHOUT simplification or omission
- Keep the translation natural and fluent while preserving information density
- STRICT: Preserve structure, line breaks, bullet points (-, •, ・), headings, and numbering
- Maintain the same tone and style as the original
- Translate line-by-line in the same order; each input line must map to one output line
- Do NOT summarize, generalize, paraphrase, or add metaphors/analogies
- Do NOT include pronunciation guides, romanization, or parenthetical information

**Требования к переводу на русский:**
- КРИТИЧНО: Вы ДОЛЖНЫ перевести ВСЁ содержимое только на русский язык
- Используйте правильную русскую грамматику и ясную структуру предложений
- Переведите ВСЕ слова и фразы с других языков на русский
- Сохраните исходное значение, детали и логическую структуру
- Используйте естественные русские выражения
- НЕ оставляйте иностранные слова в переводе
- Убедитесь, что 100% вывода только на русском языке

**CRITICAL OUTPUT INSTRUCTIONS:**
- Output ONLY the translated text in Russian
- Do NOT include the original text
- Do NOT repeat these instructions or guidelines in your output
- Do NOT add any explanatory text, labels, headers, or meta-commentary
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Start your response directly with the translated content

Text to translate:
{text}
"""

TRANSLATION_INPUT_VARIABLES = ["text"]
