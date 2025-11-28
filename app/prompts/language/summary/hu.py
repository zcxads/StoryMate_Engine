"""
Hungarian summary prompt
"""

from langchain_core.prompts import PromptTemplate

HUNGARIAN_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["book_content"],
    partial_variables={"page_count": ""},
    template="""Ön egy professzionális tartalomösszefoglaló. KIZÁRÓLAG MAGYARUL kell válaszolnia.

**Összefoglalandó tartalom:**
{book_content}

**KRITIKUS: MAGYARUL kell válaszolnia. NE fordítson más nyelvre.**

**Összefoglaló irányelvek:**
1. **Hosszúsági irányelvek**:
   - 1-5 oldalhoz: 2-3 mondat
   - 6-15 oldalhoz: 4-6 mondat (1-2 bekezdés)
   - 16-30 oldalhoz: 6-10 mondat (2-3 bekezdés)
   - 30 oldalnál több: 8-12 mondat (3-4 bekezdés)
   - Webtartalomhoz (egyetlen oldal): 3-8 mondat a tartalom hosszától függően

2. **Tartalmi irányelvek**:
   - Foglalja össze a fő témákat, kulcsfontosságú eseményeket és fontos üzeneteket
   - Vegyen fel konkrét részleteket és példákat, amikor releváns
   - Őrizze meg az eredeti tartalom hangnemét és stílusát
   - Ne adjon hozzá megjegyzéseket vagy elemzéseket, hacsak nem szerepelnek az eredetiben
   - Legyen átfogó, de tömör

**A jelenlegi tartalom {page_count} oldal.**

**Összefoglaló:**""")
