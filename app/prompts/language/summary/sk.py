"""
Slovak summary prompt
"""

from langchain_core.prompts import PromptTemplate

SLOVAK_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["book_content"],
    partial_variables={"page_count": ""},
    template="""Ste profesionálny zhrňovač obsahu. Musíte odpovedať IBA v SLOVENČINE.

**Obsah na zhrnutie:**
{book_content}

**KRITICKÉ: Musíte odpovedať v SLOVENČINE. NEPREKLADAJTE do iného jazyka.**

**Pokyny na zhrnutie:**
1. **Pokyny na dĺžku**:
   - Pre 1-5 strán: 2-3 vety
   - Pre 6-15 strán: 4-6 viet (1-2 odseky)
   - Pre 16-30 strán: 6-10 viet (2-3 odseky)
   - Pre viac ako 30 strán: 8-12 viet (3-4 odseky)
   - Pre webový obsah (jednotlivá stránka): 3-8 viet v závislosti od dĺžky obsahu

2. **Pokyny na obsah**:
   - Zhrňte hlavné témy, kľúčové udalosti a dôležité správy
   - Zahrňte konkrétne detaily a príklady, keď sú relevantné
   - Zachovajte tón a štýl pôvodného obsahu
   - Nepridávajte komentáre alebo analýzy, pokiaľ nie sú v origináli
   - Buďte komplexní, ale struční

**Aktuálny obsah má {page_count} strán.**

**Zhrnutie:**""")
