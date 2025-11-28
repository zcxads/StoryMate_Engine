"""
Slovenian translation prompt
"""

SLOVENIAN_TRANSLATION_TEMPLATE = """Please translate the following text into Slovenian.

**Translation Guidelines:**
- Maintain the original meaning and nuance WITHOUT simplification or omission
- Keep the translation natural and fluent while preserving information density
- STRICT: Preserve structure, line breaks, bullet points (-, •, ・), headings, and numbering
- Maintain the same tone and style as the original
- Translate line-by-line in the same order; each input line must map to one output line
- Do NOT summarize, generalize, paraphrase, or add metaphors/analogies
- Do NOT include pronunciation guides, romanization, or parenthetical information

**Zahteve za slovenski prevod:**
- KRITIČNO: Prevesti morate VSO vsebino samo v slovenščino
- Uporabljajte pravilno slovensko slovnico in jasno strukturo stavkov
- Prevedite VSE besede in fraze iz drugih jezikov v slovenščino
- Ohranite izvirni pomen, podrobnosti in logično strukturo
- Uporabljajte naravne slovenske izraze
- NE obdržite tujih besed v prevodu
- Prepričajte se, da je 100% rezultata samo v slovenščini

**CRITICAL OUTPUT INSTRUCTIONS:**
- Output ONLY the translated text in Slovenian
- Do NOT include the original text
- Do NOT repeat these instructions or guidelines in your output
- Do NOT add any explanatory text, labels, headers, or meta-commentary
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Start your response directly with the translated content

Text to translate:
{text}
"""

TRANSLATION_INPUT_VARIABLES = ["text"]
