"""
Bulgarian translation prompt
"""

BULGARIAN_TRANSLATION_TEMPLATE = """Please translate the following text into Bulgarian.

**Translation Guidelines:**
- Maintain the original meaning and nuance WITHOUT simplification or omission
- Keep the translation natural and fluent while preserving information density
- STRICT: Preserve structure, line breaks, bullet points (-, •, ・), headings, and numbering
- Maintain the same tone and style as the original
- Translate line-by-line in the same order; each input line must map to one output line
- Do NOT summarize, generalize, paraphrase, or add metaphors/analogies
- Do NOT include pronunciation guides, romanization, or parenthetical information

**Изисквания за български превод:**
- КРИТИЧНО: Трябва да преведете ЦЯЛОТО съдържание само на български
- Използвайте правилна българска граматика и ясна структура на изречението
- Преведете ВСИЧКИ думи и фрази от други езици на български
- Запазете оригиналния смисъл, детайлите и логическата структура
- Използвайте естествени български изрази
- НЕ запазвайте чужди думи в превода
- Уверете се, че 100% от изхода е само на български

**CRITICAL OUTPUT INSTRUCTIONS:**
- Output ONLY the translated text in Bulgarian
- Do NOT include the original text
- Do NOT repeat these instructions or guidelines in your output
- Do NOT add any explanatory text, labels, headers, or meta-commentary
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Start your response directly with the translated content

Text to translate:
{text}
"""

TRANSLATION_INPUT_VARIABLES = ["text"]
