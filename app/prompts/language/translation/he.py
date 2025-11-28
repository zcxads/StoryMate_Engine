"""
Hebrew translation prompt
"""

HEBREW_TRANSLATION_TEMPLATE = """Please translate the following text into Hebrew.

**Translation Guidelines:**
- Maintain the original meaning and nuance WITHOUT simplification or omission
- Keep the translation natural and fluent while preserving information density
- STRICT: Preserve structure, line breaks, bullet points (-, •, ・), headings, and numbering
- Maintain the same tone and style as the original
- Translate line-by-line in the same order; each input line must map to one output line
- Do NOT summarize, generalize, paraphrase, or add metaphors/analogies
- Do NOT include pronunciation guides, romanization, or parenthetical information

**דרישות תרגום לעברית:**
- קריטי: עליך לתרגם את כל התוכן לעברית בלבד
- השתמש בדקדוק עברי נכון ובמבנה משפטים ברור
- תרגם את כל המילים והביטויים משפות אחרות לעברית
- שמור על המשמעות המקורית, הפרטים והמבנה הלוגי
- השתמש בביטויים עבריים טבעיים
- אל תשאיר מילים בשפות זרות בתרגום
- וודא ש-100% מהפלט הוא רק בעברית

**CRITICAL OUTPUT INSTRUCTIONS:**
- Output ONLY the translated text in Hebrew
- Do NOT include the original text
- Do NOT repeat these instructions or guidelines in your output
- Do NOT add any explanatory text, labels, headers, or meta-commentary
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Start your response directly with the translated content

Text to translate:
{text}
"""

TRANSLATION_INPUT_VARIABLES = ["text"]
