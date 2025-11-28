"""
Korean translation prompt
"""

KOREAN_TRANSLATION_TEMPLATE = """Please translate the following text into Korean.

**Translation Guidelines:**
- Maintain the original meaning and nuance WITHOUT simplification or omission
- Keep the translation natural and fluent while preserving information density
- STRICT: Preserve structure, line breaks, bullet points (-, •, ・), headings, and numbering
- Maintain the same tone and style as the original
- Translate line-by-line in the same order; each input line must map to one output line
- Do NOT summarize, generalize, paraphrase, or add metaphors/analogies
- Do NOT include pronunciation guides, romanization, or parenthetical information

**한국어 번역 필수 요구사항:**
- 중요: 모든 내용을 반드시 한국어(한국어)로 번역해야 합니다
- 격식체 사용 (합니다 체, 해요 체 금지)
- 영어/일본어/중국어 단어와 구문을 모두 한국어로 번역
- 적절한 한국어 문법과 조사(은/는/이/가/을/를) 사용
- 자연스러운 한국어 표현 사용
- 외국어 단어를 절대 그대로 두지 말 것
- 출력의 100%가 한국어로만 되도록 보장

**CRITICAL OUTPUT INSTRUCTIONS:**
- Output ONLY the translated text in Korean
- Do NOT include the original text
- Do NOT repeat these instructions or guidelines in your output
- Do NOT add any explanatory text, labels, headers, or meta-commentary
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Start your response directly with the translated content

Text to translate:
{text}
"""

TRANSLATION_INPUT_VARIABLES = ["text"]
