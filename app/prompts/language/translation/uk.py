"""
Ukrainian translation prompt
"""

UKRAINIAN_TRANSLATION_TEMPLATE = """Please translate the following text into Ukrainian.

**Translation Guidelines:**
- Maintain the original meaning and nuance WITHOUT simplification or omission
- Keep the translation natural and fluent while preserving information density
- STRICT: Preserve structure, line breaks, bullet points (-, •, ・), headings, and numbering
- Maintain the same tone and style as the original
- Translate line-by-line in the same order; each input line must map to one output line
- Do NOT summarize, generalize, paraphrase, or add metaphors/analogies
- Do NOT include pronunciation guides, romanization, or parenthetical information

**Вимоги до українського перекладу:**
- КРИТИЧНО: Ви ПОВИННІ перекласти ВЕСЬ вміст лише українською
- Використовуйте правильну українську граматику та чітку структуру речень
- Перекладіть УСІ слова та фрази з інших мов українською
- Збережіть оригінальне значення, деталі та логічну структуру
- Використовуйте природні українські вирази
- НЕ залишайте іноземні слова в перекладі
- Переконайтеся, що 100% виводу лише українською

**CRITICAL OUTPUT INSTRUCTIONS:**
- Output ONLY the translated text in Ukrainian
- Do NOT include the original text
- Do NOT repeat these instructions or guidelines in your output
- Do NOT add any explanatory text, labels, headers, or meta-commentary
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Start your response directly with the translated content

Text to translate:
{text}
"""

TRANSLATION_INPUT_VARIABLES = ["text"]
