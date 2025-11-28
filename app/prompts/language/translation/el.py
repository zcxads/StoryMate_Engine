"""
Greek translation prompt
"""

GREEK_TRANSLATION_TEMPLATE = """Please translate the following text into Greek.

**Translation Guidelines:**
- Maintain the original meaning and nuance WITHOUT simplification or omission
- Keep the translation natural and fluent while preserving information density
- STRICT: Preserve structure, line breaks, bullet points (-, •, ・), headings, and numbering
- Maintain the same tone and style as the original
- Translate line-by-line in the same order; each input line must map to one output line
- Do NOT summarize, generalize, paraphrase, or add metaphors/analogies
- Do NOT include pronunciation guides, romanization, or parenthetical information

**Απαιτήσεις ελληνικής μετάφρασης:**
- ΚΡΙΣΙΜΟ: Πρέπει να μεταφράσετε ΟΛΟ το περιεχόμενο μόνο στα ελληνικά
- Χρησιμοποιήστε σωστή ελληνική γραμματική και σαφή δομή προτάσεων
- Μεταφράστε ΟΛΕ τις λέξεις και φράσεις από άλλες γλώσσες στα ελληνικά
- Διατηρήστε το αρχικό νόημα, τις λεπτομέρειες και τη λογική δομή
- Χρησιμοποιήστε φυσικές ελληνικές εκφράσεις
- ΜΗΝ διατηρείτε ξένες λέξεις στη μετάφραση
- Βεβαιωθείτε ότι το 100% της εξόδου είναι μόνο στα ελληνικά

**CRITICAL OUTPUT INSTRUCTIONS:**
- Output ONLY the translated text in Greek
- Do NOT include the original text
- Do NOT repeat these instructions or guidelines in your output
- Do NOT add any explanatory text, labels, headers, or meta-commentary
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Start your response directly with the translated content

Text to translate:
{text}
"""

TRANSLATION_INPUT_VARIABLES = ["text"]
