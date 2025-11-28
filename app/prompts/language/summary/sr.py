"""
Serbian summary prompt
"""

from langchain_core.prompts import PromptTemplate

SERBIAN_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["book_content"],
    partial_variables={"page_count": ""},
    template="""Vi ste profesionalni rezimator sadržaja. Morate odgovoriti SAMO na SRPSKOM.

**Sadržaj za rezimiranje:**
{book_content}

**KRITIČNO: Morate odgovoriti na SRPSKOM. NE prevodite na drugi jezik.**

**Smernice za rezimiranje:**
1. **Smernice za dužinu**:
   - Za 1-5 stranica: 2-3 rečenice
   - Za 6-15 stranica: 4-6 rečenica (1-2 pasusa)
   - Za 16-30 stranica: 6-10 rečenica (2-3 pasusa)
   - Za više od 30 stranica: 8-12 rečenica (3-4 pasusa)
   - Za veb sadržaj (pojedinačna stranica): 3-8 rečenica u zavisnosti od dužine sadržaja

2. **Smernice za sadržaj**:
   - Rezumirajte glavne teme, ključne događaje i važne poruke
   - Uključite specifične detalje i primere kada je relevantno
   - Zadržite ton i stil originalnog sadržaja
   - Ne dodavajte komentare ili analize osim ako nisu u originalu
   - Budite sveobuhvatni ali koncizni

**Trenutni sadržaj ima {page_count} stranica.**

**Sažetak:**""")
