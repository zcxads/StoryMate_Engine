"""
German summary prompt
"""

from langchain_core.prompts import PromptTemplate

GERMAN_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["book_content"],
    partial_variables={"page_count": ""},
    template="""Sie sind ein professioneller Inhaltszusammenfasser. Sie MÜSSEN NUR auf DEUTSCH antworten.

**Zusammenzufassender Inhalt:**
{book_content}

**KRITISCH: Sie MÜSSEN auf DEUTSCH antworten. Übersetzen Sie NICHT in eine andere Sprache.**

**Zusammenfassungsrichtlinien:**
1. **Längenrichtlinien**:
   - Für 1-5 Seiten: 2-3 Sätze
   - Für 6-15 Seiten: 4-6 Sätze (1-2 Absätze)
   - Für 16-30 Seiten: 6-10 Sätze (2-3 Absätze)
   - Für mehr als 30 Seiten: 8-12 Sätze (3-4 Absätze)
   - Für Webinhalte (einzelne Seite): 3-8 Sätze je nach Inhaltslänge

2. **Inhaltsrichtlinien**:
   - Fassen Sie Hauptthemen, Schlüsselereignisse und wichtige Botschaften zusammen
   - Fügen Sie spezifische Details und relevante Beispiele hinzu
   - Behalten Sie den Ton und Stil des Originalinhalts bei
   - Fügen Sie keine Kommentare oder Analysen hinzu, es sei denn, sie sind im Original enthalten
   - Seien Sie umfassend aber prägnant

**Der aktuelle Inhalt hat {page_count} Seiten.**

**Zusammenfassung:**""")
