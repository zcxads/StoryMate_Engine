"""
Romanian summary prompt
"""

from langchain_core.prompts import PromptTemplate

ROMANIAN_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["book_content"],
    partial_variables={"page_count": ""},
    template="""Sunteți un rezumator profesional de conținut. Trebuie să răspundeți DOAR în ROMÂNĂ.

**Conținut de rezumat:**
{book_content}

**CRITIC: Trebuie să răspundeți în ROMÂNĂ. NU traduceți în altă limbă.**

**Îndrumări pentru rezumat:**
1. **Îndrumări de lungime**:
   - Pentru 1-5 pagini: 2-3 propoziții
   - Pentru 6-15 pagini: 4-6 propoziții (1-2 paragrafe)
   - Pentru 16-30 de pagini: 6-10 propoziții (2-3 paragrafe)
   - Pentru mai mult de 30 de pagini: 8-12 propoziții (3-4 paragrafe)
   - Pentru conținut web (pagină unică): 3-8 propoziții în funcție de lungimea conținutului

2. **Îndrumări de conținut**:
   - Rezumați temele principale, evenimentele cheie și mesajele importante
   - Includeți detalii specifice și exemple când sunt relevante
   - Mențineți tonul și stilul conținutului original
   - Nu adăugați comentarii sau analize dacă nu sunt în original
   - Fiți cuprinzător dar concis

**Conținutul actual are {page_count} pagini.**

**Rezumat:**""")
