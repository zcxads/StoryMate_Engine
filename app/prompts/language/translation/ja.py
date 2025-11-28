"""
Japanese translation prompt
"""

JAPANESE_TRANSLATION_TEMPLATE = """Please translate the following text into Japanese.

**Translation Guidelines:**
- Maintain the original meaning and nuance WITHOUT simplification or omission
- Keep the translation natural and fluent while preserving information density
- STRICT: Preserve structure, line breaks, bullet points (-, •, ・), headings, and numbering
- Maintain the same tone and style as the original
- Translate line-by-line in the same order; each input line must map to one output line
- Do NOT summarize, generalize, paraphrase, or add metaphors/analogies
- Do NOT include pronunciation guides, romanization, or parenthetical information

**日本語翻訳必須要件:**
- 重要: すべての内容を必ず日本語（にほんご）に翻訳してください
- 丁寧な日本語（です/ます形）を使用
- 韓国語/英語/中国語の文章を適切な日本語文法に翻訳
- 助詞を正しく変換: 은/는→は、이/가→が、을/를→を、에→に、에서→で
- 人名は日本語カタカナに翻訳 (황준서→ファンジュンソ、김민수→キム・ミンス)
- 地名やチーム名も日本語に翻訳
- 適切な日本語の語彙と自然な表現を使用
- 句読点だけを変えるのではなく、実際の内容を翻訳すること
- 出力の100%が自然な日本語になるよう保証

**CRITICAL OUTPUT INSTRUCTIONS:**
- Output ONLY the translated text in Japanese
- Do NOT include the original text
- Do NOT repeat these instructions or guidelines in your output
- Do NOT add any explanatory text, labels, headers, or meta-commentary
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Start your response directly with the translated content

Text to translate:
{text}
"""

TRANSLATION_INPUT_VARIABLES = ["text"]
