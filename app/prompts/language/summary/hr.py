"""
Croatian summary prompt
"""

from langchain_core.prompts import PromptTemplate

CROATIAN_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["book_content"],
    partial_variables={"page_count": ""},
    template="""Vi ste profesionalni sažetak sadržaja. Morate odgovoriti SAMO na HRVATSKOM.

**Sadržaj za sažimanje:**
{book_content}

**KRITIČNO: Morate odgovoriti na HRVATSKOM. NE prevodite na drugi jezik.**

**Smjernice za sažimanje:**
1. **Smjernice za duljinu**:
   - Za 1-5 stranica: 2-3 rečenice
   - Za 6-15 stranica: 4-6 rečenica (1-2 odlomka)
   - Za 16-30 stranica: 6-10 rečenica (2-3 odlomka)
   - Za više od 30 stranica: 8-12 rečenica (3-4 odlomka)
   - Za web sadržaj (pojedinačna stranica): 3-8 rečenica ovisno o duljini sadržaja

2. **Smjernice za sadržaj**:
   - Sažmite glavne teme, ključne događaje i važne poruke
   - Uključite specifične detalje i primjere kada je relevantno
   - Zadržite ton i stil izvornog sadržaja
   - Ne dodavajte komentare ili analize osim ako nisu u izvorniku
   - Budite sveobuhvatni ali koncizni

**Trenutni sadržaj ima {page_count} stranica.**

**Sažetak:**""")
