"""
Arabic translation prompt
"""

ARABIC_TRANSLATION_TEMPLATE = """Please translate the following text into Arabic.

**Translation Guidelines:**
- Maintain the original meaning and nuance WITHOUT simplification or omission
- Keep the translation natural and fluent while preserving information density
- STRICT: Preserve structure, line breaks, bullet points (-, •, ・), headings, and numbering
- Maintain the same tone and style as the original
- Translate line-by-line in the same order; each input line must map to one output line
- Do NOT summarize, generalize, paraphrase, or add metaphors/analogies
- Do NOT include pronunciation guides, romanization, or parenthetical information

**متطلبات الترجمة إلى العربية:**
- حاسم: يجب عليك ترجمة جميع المحتوى إلى العربية فقط
- استخدم القواعد العربية الصحيحة وبناء جمل واضح
- ترجم جميع الكلمات والعبارات من اللغات الأخرى إلى العربية
- حافظ على المعنى الأصلي والتفاصيل والبنية المنطقية
- استخدم تعبيرات عربية طبيعية
- لا تحتفظ بأي كلمات بلغات أجنبية في الترجمة
- تأكد من أن 100٪ من الناتج باللغة العربية فقط

**CRITICAL OUTPUT INSTRUCTIONS:**
- Output ONLY the translated text in Arabic
- Do NOT include the original text
- Do NOT repeat these instructions or guidelines in your output
- Do NOT add any explanatory text, labels, headers, or meta-commentary
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Start your response directly with the translated content

Text to translate:
{text}
"""

TRANSLATION_INPUT_VARIABLES = ["text"]
