"""
German translation prompt
"""

GERMAN_TRANSLATION_TEMPLATE = """Please translate the following text into German.

**Translation Guidelines:**
- Maintain the original meaning and nuance WITHOUT simplification or omission
- Keep the translation natural and fluent while preserving information density
- STRICT: Preserve structure, line breaks, bullet points (-, •, ・), headings, and numbering
- Maintain the same tone and style as the original
- Translate line-by-line in the same order; each input line must map to one output line
- Do NOT summarize, generalize, paraphrase, or add metaphors/analogies
- Do NOT include pronunciation guides, romanization, or parenthetical information

**Anforderungen für deutsche Übersetzung:**
- KRITISCH: Sie MÜSSEN ALLE Inhalte nur auf Deutsch übersetzen
- Verwenden Sie korrekte deutsche Grammatik und klare Satzstruktur
- Übersetzen Sie ALLE fremdsprachigen Wörter und Phrasen ins Deutsche
- Behalten Sie die ursprüngliche Bedeutung, Details und logische Struktur bei
- Verwenden Sie natürliche deutsche Ausdrücke
- Behalten Sie KEINE fremdsprachigen Wörter in der Übersetzung bei
- Stellen Sie sicher, dass 100% der Ausgabe nur auf Deutsch ist

**CRITICAL OUTPUT INSTRUCTIONS:**
- Output ONLY the translated text in German
- Do NOT include the original text
- Do NOT repeat these instructions or guidelines in your output
- Do NOT add any explanatory text, labels, headers, or meta-commentary
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Start your response directly with the translated content

Text to translate:
{text}
"""

TRANSLATION_INPUT_VARIABLES = ["text"]
