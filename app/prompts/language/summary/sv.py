"""
Swedish summary prompt
"""

from langchain_core.prompts import PromptTemplate

SWEDISH_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["book_content"],
    partial_variables={"page_count": ""},
    template="""Du är en professionell innehållssammanfattare. Du MÅSTE svara ENDAST på SVENSKA.

**Innehåll att sammanfatta:**
{book_content}

**KRITISKT: Du MÅSTE svara på SVENSKA. Översätt INTE till något annat språk.**

**Sammanfattningsriktlinjer:**
1. **Längdriktlinjer**:
   - För 1-5 sidor: 2-3 meningar
   - För 6-15 sidor: 4-6 meningar (1-2 stycken)
   - För 16-30 sidor: 6-10 meningar (2-3 stycken)
   - För mer än 30 sidor: 8-12 meningar (3-4 stycken)
   - För webbinnehåll (enskild sida): 3-8 meningar beroende på innehållets längd

2. **Innehållsriktlinjer**:
   - Sammanfatta huvudteman, viktiga händelser och viktiga budskap
   - Inkludera specifika detaljer och exempel när det är relevant
   - Behåll tonen och stilen i det ursprungliga innehållet
   - Lägg inte till kommentarer eller analyser om de inte finns i originalet
   - Var omfattande men koncis

**Nuvarande innehåll har {page_count} sidor.**

**Sammanfattning:**""")
