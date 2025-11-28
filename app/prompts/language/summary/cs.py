"""
Czech summary prompt
"""

from langchain_core.prompts import PromptTemplate

CZECH_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["book_content"],
    partial_variables={"page_count": ""},
    template="""Jste profesionální shrnutí obsahu. Musíte odpovídat POUZE v ČEŠTINĚ.

**Obsah k shrnutí:**
{book_content}

**KRITICKÉ: Musíte odpovídat v ČEŠTINĚ. NEPŘEKLÁDEJTE do jiného jazyka.**

**Pokyny pro shrnutí:**
1. **Pokyny pro délku**:
   - Pro 1-5 stran: 2-3 věty
   - Pro 6-15 stran: 4-6 vět (1-2 odstavce)
   - Pro 16-30 stran: 6-10 vět (2-3 odstavce)
   - Pro více než 30 stran: 8-12 vět (3-4 odstavce)
   - Pro webový obsah (jednotlivá stránka): 3-8 vět v závislosti na délce obsahu

2. **Pokyny pro obsah**:
   - Shrňte hlavní témata, klíčové události a důležité zprávy
   - Zahrňte konkrétní podrobnosti a příklady, pokud jsou relevantní
   - Zachovejte tón a styl původního obsahu
   - Nepřidávejte komentáře nebo analýzy, pokud nejsou v originálu
   - Buďte komplexní, ale struční

**Aktuální obsah má {page_count} stran.**

**Shrnutí:**""")
