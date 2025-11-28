"""
Portuguese translation prompt
"""

PORTUGUESE_TRANSLATION_TEMPLATE = """Please translate the following text into Portuguese.

**Translation Guidelines:**
- Maintain the original meaning and nuance WITHOUT simplification or omission
- Keep the translation natural and fluent while preserving information density
- STRICT: Preserve structure, line breaks, bullet points (-, •, ・), headings, and numbering
- Maintain the same tone and style as the original
- Translate line-by-line in the same order; each input line must map to one output line
- Do NOT summarize, generalize, paraphrase, or add metaphors/analogies
- Do NOT include pronunciation guides, romanization, or parenthetical information

**Requisitos de tradução em português:**
- CRÍTICO: Você DEVE traduzir TODO o conteúdo apenas para português
- Use gramática portuguesa adequada e estrutura de frases claras
- Traduza TODAS as palavras e frases de outros idiomas para português
- Mantenha o significado original, detalhes e estrutura lógica
- Use expressões portuguesas naturais
- NÃO mantenha palavras em idiomas estrangeiros na tradução
- Certifique-se de que 100% da saída esteja apenas em português

**CRITICAL OUTPUT INSTRUCTIONS:**
- Output ONLY the translated text in Portuguese
- Do NOT include the original text
- Do NOT repeat these instructions or guidelines in your output
- Do NOT add any explanatory text, labels, headers, or meta-commentary
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Start your response directly with the translated content

Text to translate:
{text}
"""

TRANSLATION_INPUT_VARIABLES = ["text"]
