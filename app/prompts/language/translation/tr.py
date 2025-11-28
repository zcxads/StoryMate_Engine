"""
Turkish translation prompt
"""

TURKISH_TRANSLATION_TEMPLATE = """Please translate the following text into Turkish.

**Translation Guidelines:**
- Maintain the original meaning and nuance WITHOUT simplification or omission
- Keep the translation natural and fluent while preserving information density
- STRICT: Preserve structure, line breaks, bullet points (-, •, ・), headings, and numbering
- Maintain the same tone and style as the original
- Translate line-by-line in the same order; each input line must map to one output line
- Do NOT summarize, generalize, paraphrase, or add metaphors/analogies
- Do NOT include pronunciation guides, romanization, or parenthetical information

**Türkçe çeviri gereksinimleri:**
- KRİTİK: TÜM içeriği yalnızca Türkçe'ye çevirmelisiniz
- Uygun Türkçe dilbilgisi ve net cümle yapısı kullanın
- Diğer dillerden TÜM kelimeleri ve ifadeleri Türkçe'ye çevirin
- Orijinal anlamı, ayrıntıları ve mantıksal yapıyı koruyun
- Doğal Türkçe ifadeler kullanın
- Çeviride yabancı dil kelimelerini SAKLAMAYIN
- Çıktının %100'ünün yalnızca Türkçe olduğundan emin olun

**CRITICAL OUTPUT INSTRUCTIONS:**
- Output ONLY the translated text in Turkish
- Do NOT include the original text
- Do NOT repeat these instructions or guidelines in your output
- Do NOT add any explanatory text, labels, headers, or meta-commentary
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Start your response directly with the translated content

Text to translate:
{text}
"""

TRANSLATION_INPUT_VARIABLES = ["text"]
