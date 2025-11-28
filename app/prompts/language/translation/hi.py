"""
Hindi translation prompt
"""

HINDI_TRANSLATION_TEMPLATE = """Please translate the following text into Hindi.

**Translation Guidelines:**
- Maintain the original meaning and nuance WITHOUT simplification or omission
- Keep the translation natural and fluent while preserving information density
- STRICT: Preserve structure, line breaks, bullet points (-, •, ・), headings, and numbering
- Maintain the same tone and style as the original
- Translate line-by-line in the same order; each input line must map to one output line
- Do NOT summarize, generalize, paraphrase, or add metaphors/analogies
- Do NOT include pronunciation guides, romanization, or parenthetical information

**हिंदी अनुवाद आवश्यकताएं:**
- महत्वपूर्ण: आपको सभी सामग्री को केवल हिंदी में अनुवाद करना होगा
- उचित हिंदी व्याकरण और स्पष्ट वाक्य संरचना का उपयोग करें
- अन्य भाषाओं के सभी शब्दों और वाक्यांशों का हिंदी में अनुवाद करें
- मूल अर्थ, विवरण और तार्किक संरचना बनाए रखें
- प्राकृतिक हिंदी अभिव्यक्तियों का उपयोग करें
- अनुवाद में विदेशी भाषा के शब्दों को न रखें
- सुनिश्चित करें कि 100% आउटपुट केवल हिंदी में हो

**CRITICAL OUTPUT INSTRUCTIONS:**
- Output ONLY the translated text in Hindi
- Do NOT include the original text
- Do NOT repeat these instructions or guidelines in your output
- Do NOT add any explanatory text, labels, headers, or meta-commentary
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Start your response directly with the translated content

Text to translate:
{text}
"""

TRANSLATION_INPUT_VARIABLES = ["text"]
