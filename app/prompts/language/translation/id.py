"""
Indonesian translation prompt
"""

INDONESIAN_TRANSLATION_TEMPLATE = """Please translate the following text into Indonesian.

**Translation Guidelines:**
- Maintain the original meaning and nuance WITHOUT simplification or omission
- Keep the translation natural and fluent while preserving information density
- STRICT: Preserve structure, line breaks, bullet points (-, •, ・), headings, and numbering
- Maintain the same tone and style as the original
- Translate line-by-line in the same order; each input line must map to one output line
- Do NOT summarize, generalize, paraphrase, or add metaphors/analogies
- Do NOT include pronunciation guides, romanization, or parenthetical information

**Persyaratan terjemahan bahasa Indonesia:**
- PENTING: Anda HARUS menerjemahkan SEMUA konten hanya ke bahasa Indonesia
- Gunakan tata bahasa Indonesia yang tepat dan struktur kalimat yang jelas
- Terjemahkan SEMUA kata dan frasa dari bahasa lain ke bahasa Indonesia
- Pertahankan makna asli, detail, dan struktur logis
- Gunakan ekspresi bahasa Indonesia yang alami
- JANGAN simpan kata bahasa asing dalam terjemahan
- Pastikan 100% output hanya dalam bahasa Indonesia

**CRITICAL OUTPUT INSTRUCTIONS:**
- Output ONLY the translated text in Indonesian
- Do NOT include the original text
- Do NOT repeat these instructions or guidelines in your output
- Do NOT add any explanatory text, labels, headers, or meta-commentary
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Start your response directly with the translated content

Text to translate:
{text}
"""

TRANSLATION_INPUT_VARIABLES = ["text"]
