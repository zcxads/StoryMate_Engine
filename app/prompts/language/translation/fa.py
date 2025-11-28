"""
Persian translation prompt
"""

PERSIAN_TRANSLATION_TEMPLATE = """Please translate the following text into Persian.

**Translation Guidelines:**
- Maintain the original meaning and nuance WITHOUT simplification or omission
- Keep the translation natural and fluent while preserving information density
- STRICT: Preserve structure, line breaks, bullet points (-, •, ・), headings, and numbering
- Maintain the same tone and style as the original
- Translate line-by-line in the same order; each input line must map to one output line
- Do NOT summarize, generalize, paraphrase, or add metaphors/analogies
- Do NOT include pronunciation guides, romanization, or parenthetical information

**الزامات ترجمه فارسی:**
- حیاتی: شما باید تمام محتوا را فقط به فارسی ترجمه کنید
- از دستور زبان فارسی صحیح و ساختار جمله واضح استفاده کنید
- تمام کلمات و عبارات از زبان‌های دیگر را به فارسی ترجمه کنید
- معنی اصلی، جزئیات و ساختار منطقی را حفظ کنید
- از عبارات طبیعی فارسی استفاده کنید
- کلمات زبان خارجی را در ترجمه نگه ندارید
- اطمینان حاصل کنید که 100٪ خروجی فقط به فارسی است

**CRITICAL OUTPUT INSTRUCTIONS:**
- Output ONLY the translated text in Persian
- Do NOT include the original text
- Do NOT repeat these instructions or guidelines in your output
- Do NOT add any explanatory text, labels, headers, or meta-commentary
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Start your response directly with the translated content

Text to translate:
{text}
"""

TRANSLATION_INPUT_VARIABLES = ["text"]
