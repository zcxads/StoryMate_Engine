"""
Malay translation prompt
"""

MALAY_TRANSLATION_TEMPLATE = """Please translate the following text into Malay.

**Translation Guidelines:**
- Maintain the original meaning and nuance WITHOUT simplification or omission
- Keep the translation natural and fluent while preserving information density
- STRICT: Preserve structure, line breaks, bullet points (-, •, ・), headings, and numbering
- Maintain the same tone and style as the original
- Translate line-by-line in the same order; each input line must map to one output line
- Do NOT summarize, generalize, paraphrase, or add metaphors/analogies
- Do NOT include pronunciation guides, romanization, or parenthetical information

**Keperluan terjemahan Bahasa Melayu:**
- PENTING: Anda MESTI menerjemahkan SEMUA kandungan hanya ke Bahasa Melayu
- Gunakan tatabahasa Bahasa Melayu yang betul dan struktur ayat yang jelas
- Terjemahkan SEMUA perkataan dan frasa dari bahasa lain ke Bahasa Melayu
- Kekalkan makna asal, butiran dan struktur logik
- Gunakan ungkapan Bahasa Melayu yang semula jadi
- JANGAN simpan perkataan bahasa asing dalam terjemahan
- Pastikan 100% output hanya dalam Bahasa Melayu

**CRITICAL OUTPUT INSTRUCTIONS:**
- Output ONLY the translated text in Malay
- Do NOT include the original text
- Do NOT repeat these instructions or guidelines in your output
- Do NOT add any explanatory text, labels, headers, or meta-commentary
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Start your response directly with the translated content

Text to translate:
{text}
"""

TRANSLATION_INPUT_VARIABLES = ["text"]
