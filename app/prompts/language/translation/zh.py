"""
Chinese translation prompt
"""

CHINESE_TRANSLATION_TEMPLATE = """Please translate the following text into Chinese.

**Translation Guidelines:**
- Maintain the original meaning and nuance WITHOUT simplification or omission
- Keep the translation natural and fluent while preserving information density
- STRICT: Preserve structure, line breaks, bullet points (-, •, ・), headings, and numbering
- Maintain the same tone and style as the original
- Translate line-by-line in the same order; each input line must map to one output line
- Do NOT summarize, generalize, paraphrase, or add metaphors/analogies
- Do NOT include pronunciation guides, romanization, or parenthetical information

**中文翻译必须要求:**
- 重要: 必须将所有内容翻译成中文
- 使用标准正式中文
- 将所有韩语/日语/英语单词和短语翻译成中文
- 韩语人名转换为中文: 使用音译 (황준서→黄俊瑞, 김민수→金敏秀)
- 日语人名转换为中文: 保持意义或使用音译 (田中太郎→田中太郎)
- 地名翻译成中文 (서울→首尔, 东京→東京/东京)
- 使用正确的中文语法、句子结构和标点符号 (。！？)
- 使用自然的中文表达
- 不要保留任何韩语/日语/英语单词
- 确保输出的100%仅为中文

**CRITICAL OUTPUT INSTRUCTIONS:**
- Output ONLY the translated text in Chinese
- Do NOT include the original text
- Do NOT repeat these instructions or guidelines in your output
- Do NOT add any explanatory text, labels, headers, or meta-commentary
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Start your response directly with the translated content

Text to translate:
{text}
"""

TRANSLATION_INPUT_VARIABLES = ["text"]
