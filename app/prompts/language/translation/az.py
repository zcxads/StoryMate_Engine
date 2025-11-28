"""
Azerbaijani translation prompt
"""

AZERBAIJANI_TRANSLATION_TEMPLATE = """Please translate the following text into Azerbaijani.

**Translation Guidelines:**
- Maintain the original meaning and nuance WITHOUT simplification or omission
- Keep the translation natural and fluent while preserving information density
- STRICT: Preserve structure, line breaks, bullet points (-, •, ・), headings, and numbering
- Maintain the same tone and style as the original
- Translate line-by-line in the same order; each input line must map to one output line
- Do NOT summarize, generalize, paraphrase, or add metaphors/analogies
- Do NOT include pronunciation guides, romanization, or parenthetical information

**Azərbaycan dilinə tərcümə tələbləri:**
- TƏCİLİ: Siz bütün məzmunu YALNIZ Azərbaycan dilinə tərcümə etməlisiniz
- Düzgün Azərbaycan qrammatikası və aydın cümlə quruluşundan istifadə edin
- Digər dillərdən BÜTÜN sözləri və ifadələri Azərbaycan dilinə tərcümə edin
- Orijinal mənasını, təfərrüatları və məntiqi strukturu saxlayın
- Təbii Azərbaycan ifadələrindən istifadə edin
- Tərcümədə xarici dil sözlərini saxlamayın
- Nəticənin 100%-nin yalnız Azərbaycan dilində olduğuna əmin olun

**CRITICAL OUTPUT INSTRUCTIONS:**
- Output ONLY the translated text in Azerbaijani
- Do NOT include the original text
- Do NOT repeat these instructions or guidelines in your output
- Do NOT add any explanatory text, labels, headers, or meta-commentary
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Start your response directly with the translated content

Text to translate:
{text}
"""

TRANSLATION_INPUT_VARIABLES = ["text"]
