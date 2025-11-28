"""
French translation prompt
"""

FRENCH_TRANSLATION_TEMPLATE = """Please translate the following text into French.

**Translation Guidelines:**
- Maintain the original meaning and nuance WITHOUT simplification or omission
- Keep the translation natural and fluent while preserving information density
- STRICT: Preserve structure, line breaks, bullet points (-, •, ・), headings, and numbering
- Maintain the same tone and style as the original
- Translate line-by-line in the same order; each input line must map to one output line
- Do NOT summarize, generalize, paraphrase, or add metaphors/analogies
- Do NOT include pronunciation guides, romanization, or parenthetical information

**Exigences de traduction en français:**
- CRITIQUE: Vous DEVEZ traduire TOUT le contenu en français uniquement
- Utilisez une grammaire française appropriée et une structure de phrase claire
- Traduisez TOUS les mots et phrases d'autres langues en français
- Conservez le sens original, les détails et la structure logique
- Utilisez des expressions françaises naturelles
- NE conservez PAS de mots en langues étrangères dans la traduction
- Assurez-vous que 100% de la sortie est uniquement en français

**CRITICAL OUTPUT INSTRUCTIONS:**
- Output ONLY the translated text in French
- Do NOT include the original text
- Do NOT repeat these instructions or guidelines in your output
- Do NOT add any explanatory text, labels, headers, or meta-commentary
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Start your response directly with the translated content

Text to translate:
{text}
"""

TRANSLATION_INPUT_VARIABLES = ["text"]
