"""
Thai translation prompt
"""

THAI_TRANSLATION_TEMPLATE = """Please translate the following text into Thai.

**Translation Guidelines:**
- Maintain the original meaning and nuance WITHOUT simplification or omission
- Keep the translation natural and fluent while preserving information density
- STRICT: Preserve structure, line breaks, bullet points (-, •, ・), headings, and numbering
- Maintain the same tone and style as the original
- Translate line-by-line in the same order; each input line must map to one output line
- Do NOT summarize, generalize, paraphrase, or add metaphors/analogies
- Do NOT include pronunciation guides, romanization, or parenthetical information

**ข้อกำหนดการแปลภาษาไทย:**
- สำคัญมาก: คุณต้องแปลเนื้อหาทั้งหมดเป็นภาษาไทยเท่านั้น
- ใช้ไวยากรณ์ภาษาไทยที่ถูกต้องและโครงสร้างประโยคที่ชัดเจน
- แปลคำและวลีทั้งหมดจากภาษาอื่นเป็นภาษาไทย
- รักษาความหมายเดิม รายละเอียด และโครงสร้างเชิงตรรกะ
- ใช้การแสดงออกภาษาไทยที่เป็นธรรมชาติ
- ห้ามเก็บคำภาษาต่างประเทศในการแปล
- ตรวจสอบให้แน่ใจว่า 100% ของผลลัพธ์เป็นภาษาไทยเท่านั้น

**CRITICAL OUTPUT INSTRUCTIONS:**
- Output ONLY the translated text in Thai
- Do NOT include the original text
- Do NOT repeat these instructions or guidelines in your output
- Do NOT add any explanatory text, labels, headers, or meta-commentary
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Start your response directly with the translated content

Text to translate:
{text}
"""

TRANSLATION_INPUT_VARIABLES = ["text"]
