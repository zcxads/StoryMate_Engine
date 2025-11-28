"""
Armenian translation prompt
"""

ARMENIAN_TRANSLATION_TEMPLATE = """Please translate the following text into Armenian.

**Translation Guidelines:**
- Maintain the original meaning and nuance WITHOUT simplification or omission
- Keep the translation natural and fluent while preserving information density
- STRICT: Preserve structure, line breaks, bullet points (-, •, ・), headings, and numbering
- Maintain the same tone and style as the original
- Translate line-by-line in the same order; each input line must map to one output line
- Do NOT summarize, generalize, paraphrase, or add metaphors/analogies
- Do NOT include pronunciation guides, romanization, or parenthetical information

**Հայերեն թարգմանության պահանջներ:**
- ԿԱՐԵՎՈՐ: Դուք ՊԵՏՔ Է թարգմանեք ԱՄԲՈՂՋ բովանդակությունը միայն հայերեն
- Օգտագործեք ճիշտ հայերեն քերականություն և հստակ նախադասությունների կառուցվածք
- Թարգմանեք ԲՈԼՈՐ բառերն ու արտահայտությունները այլ լեզուներից հայերեն
- Պահպանեք բուն իմաստը, մանրամասները և տրամաբանական կառուցվածքը
- Օգտագործեք բնական հայերեն արտահայտություններ
- ՄԻ պահպանեք օտար լեզվի բառեր թարգմանության մեջ
- Համոզվեք, որ արդյունքի 100%-ը միայն հայերեն է

**CRITICAL OUTPUT INSTRUCTIONS:**
- Output ONLY the translated text in Armenian
- Do NOT include the original text
- Do NOT repeat these instructions or guidelines in your output
- Do NOT add any explanatory text, labels, headers, or meta-commentary
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Start your response directly with the translated content

Text to translate:
{text}
"""

TRANSLATION_INPUT_VARIABLES = ["text"]
