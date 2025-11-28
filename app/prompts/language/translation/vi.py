"""
Vietnamese translation prompt
"""

VIETNAMESE_TRANSLATION_TEMPLATE = """Please translate the following text into Vietnamese.

**Translation Guidelines:**
- Maintain the original meaning and nuance WITHOUT simplification or omission
- Keep the translation natural and fluent while preserving information density
- STRICT: Preserve structure, line breaks, bullet points (-, •, ・), headings, and numbering
- Maintain the same tone and style as the original
- Translate line-by-line in the same order; each input line must map to one output line
- Do NOT summarize, generalize, paraphrase, or add metaphors/analogies
- Do NOT include pronunciation guides, romanization, or parenthetical information

**Yêu cầu dịch sang tiếng Việt:**
- QUAN TRỌNG: Bạn PHẢI dịch TẤT CẢ nội dung chỉ sang tiếng Việt
- Sử dụng ngữ pháp tiếng Việt phù hợp và cấu trúc câu rõ ràng
- Dịch TẤT CẢ các từ và cụm từ từ ngôn ngữ khác sang tiếng Việt
- Duy trì ý nghĩa gốc, chi tiết và cấu trúc logic
- Sử dụng các biểu đạt tiếng Việt tự nhiên
- KHÔNG giữ bất kỳ từ ngoại ngữ nào trong bản dịch
- Đảm bảo 100% đầu ra chỉ bằng tiếng Việt

**CRITICAL OUTPUT INSTRUCTIONS:**
- Output ONLY the translated text in Vietnamese
- Do NOT include the original text
- Do NOT repeat these instructions or guidelines in your output
- Do NOT add any explanatory text, labels, headers, or meta-commentary
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Start your response directly with the translated content

Text to translate:
{text}
"""

TRANSLATION_INPUT_VARIABLES = ["text"]
