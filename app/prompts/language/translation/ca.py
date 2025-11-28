"""
Catalan translation prompt
"""

CATALAN_TRANSLATION_TEMPLATE = """Please translate the following text into Catalan.

**Translation Guidelines:**
- Maintain the original meaning and nuance WITHOUT simplification or omission
- Keep the translation natural and fluent while preserving information density
- STRICT: Preserve structure, line breaks, bullet points (-, •, ・), headings, and numbering
- Maintain the same tone and style as the original
- Translate line-by-line in the same order; each input line must map to one output line
- Do NOT summarize, generalize, paraphrase, or add metaphors/analogies
- Do NOT include pronunciation guides, romanization, or parenthetical information

**Requisits de traducció al català:**
- CRÍTIC: Heu de traduir TOT el contingut només al català
- Utilitzeu gramàtica catalana adequada i estructura de frases clara
- Traduïu TOTES les paraules i frases d'altres idiomes al català
- Manteniu el significat original, els detalls i l'estructura lògica
- Utilitzeu expressions catalanes naturals
- NO mantingueu paraules en idiomes estrangers a la traducció
- Assegureu-vos que el 100% de la sortida sigui només en català

**CRITICAL OUTPUT INSTRUCTIONS:**
- Output ONLY the translated text in Catalan
- Do NOT include the original text
- Do NOT repeat these instructions or guidelines in your output
- Do NOT add any explanatory text, labels, headers, or meta-commentary
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Start your response directly with the translated content

Text to translate:
{text}
"""

TRANSLATION_INPUT_VARIABLES = ["text"]
