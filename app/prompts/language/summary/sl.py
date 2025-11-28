"""
Slovenian summary prompt
"""

from langchain_core.prompts import PromptTemplate

SLOVENIAN_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["book_content"],
    partial_variables={"page_count": ""},
    template="""Ste profesionalni povzemalec vsebine. Odgovoriti morate SAMO v SLOVENŠČINI.

**Vsebina za povzetek:**
{book_content}

**KRITIČNO: Odgovoriti morate v SLOVENŠČINI. NE prevajajte v drug jezik.**

**Smernice za povzetek:**
1. **Smernice za dolžino**:
   - Za 1-5 strani: 2-3 stavki
   - Za 6-15 strani: 4-6 stavkov (1-2 odstavka)
   - Za 16-30 strani: 6-10 stavkov (2-3 odstavki)
   - Za več kot 30 strani: 8-12 stavkov (3-4 odstavki)
   - Za spletno vsebino (posamezna stran): 3-8 stavkov glede na dolžino vsebine

2. **Smernice za vsebino**:
   - Povzemite glavne teme, ključne dogodke in pomembna sporočila
   - Vključite specifične podrobnosti in primere, ko je relevantno
   - Ohranite ton in slog izvirne vsebine
   - Ne dodajajte komentarjev ali analiz, razen če so v izvirniku
   - Bodite celoviti, a jedrnati

**Trenutna vsebina ima {page_count} strani.**

**Povzetek:**""")
