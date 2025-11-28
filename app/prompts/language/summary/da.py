"""
Danish summary prompt
"""

from langchain_core.prompts import PromptTemplate

DANISH_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["book_content"],
    partial_variables={"page_count": ""},
    template="""Du er en professionel indholdssamlere. Du SKAL kun svare på DANSK.

**Indhold der skal opsummeres:**
{book_content}

**KRITISK: Du SKAL svare på DANSK. Oversæt IKKE til noget andet sprog.**

**Opsummeringsretningslinjer:**
1. **Længderetningslinjer**:
   - For 1-5 sider: 2-3 sætninger
   - For 6-15 sider: 4-6 sætninger (1-2 afsnit)
   - For 16-30 sider: 6-10 sætninger (2-3 afsnit)
   - For mere end 30 sider: 8-12 sætninger (3-4 afsnit)
   - For webindhold (enkelt side): 3-8 sætninger afhængigt af indholdslængden

2. **Indholdsretningslinjer**:
   - Opsummer hovedtemaer, nøglebegivenheder og vigtige budskaber
   - Inkluder specifikke detaljer og eksempler når relevant
   - Bevar tonen og stilen i det originale indhold
   - Tilføj ikke kommentarer eller analyser medmindre de er i originalen
   - Vær omfattende men kortfattet

**Nuværende indhold har {page_count} sider.**

**Opsummering:**""")
