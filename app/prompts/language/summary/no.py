"""
Norwegian summary prompt
"""

from langchain_core.prompts import PromptTemplate

NORWEGIAN_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["book_content"],
    partial_variables={"page_count": ""},
    template="""Du er en profesjonell innholdsoppsummerer. Du MÅ kun svare på NORSK.

**Innhold som skal oppsummeres:**
{book_content}

**KRITISK: Du MÅ svare på NORSK. Oversett IKKE til noe annet språk.**

**Oppsummeringsretningslinjer:**
1. **Lengderetningslinjer**:
   - For 1-5 sider: 2-3 setninger
   - For 6-15 sider: 4-6 setninger (1-2 avsnitt)
   - For 16-30 sider: 6-10 setninger (2-3 avsnitt)
   - For mer enn 30 sider: 8-12 setninger (3-4 avsnitt)
   - For webinnhold (enkelt side): 3-8 setninger avhengig av innholdslengden

2. **Innholdsretningslinjer**:
   - Oppsummer hovedtemaer, nøkkelhendelser og viktige budskap
   - Inkluder spesifikke detaljer og eksempler når relevant
   - Behold tonen og stilen i det originale innholdet
   - Ikke legg til kommentarer eller analyser med mindre de er i originalen
   - Vær omfattende men kortfattet

**Nåværende innhold har {page_count} sider.**

**Oppsummering:**""")
