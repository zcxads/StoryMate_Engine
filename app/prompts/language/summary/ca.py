"""
Catalan summary prompt
"""

from langchain_core.prompts import PromptTemplate

CATALAN_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["book_content"],
    partial_variables={"page_count": ""},
    template="""Sou un resumidor professional de contingut. Heu de respondre NOMÉS en CATALÀ.

**Contingut a resumir:**
{book_content}

**CRÍTIC: Heu de respondre en CATALÀ. NO traduïu a cap altre idioma.**

**Directrius de resum:**
1. **Directrius de longitud**:
   - Per a 1-5 pàgines: 2-3 frases
   - Per a 6-15 pàgines: 4-6 frases (1-2 paràgrafs)
   - Per a 16-30 pàgines: 6-10 frases (2-3 paràgrafs)
   - Per a més de 30 pàgines: 8-12 frases (3-4 paràgrafs)
   - Per a contingut web (pàgina única): 3-8 frases segons la longitud del contingut

2. **Directrius de contingut**:
   - Resumiu els temes principals, esdeveniments clau i missatges importants
   - Incloeu detalls específics i exemples quan sigui rellevant
   - Manteniu el to i l'estil del contingut original
   - No afegiu comentaris o anàlisis tret que estiguin a l'original
   - Sigueu exhaustius però concisos

**El contingut actual té {page_count} pàgines.**

**Resum:**""")
