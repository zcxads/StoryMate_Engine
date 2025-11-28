"""
Dutch summary prompt
"""

from langchain_core.prompts import PromptTemplate

DUTCH_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["book_content"],
    partial_variables={"page_count": ""},
    template="""U bent een professionele inhoudssamenvatting. U MOET ALLEEN in het NEDERLANDS antwoorden.

**Samen te vatten inhoud:**
{book_content}

**KRITISCH: U MOET in het NEDERLANDS antwoorden. Vertaal NIET naar een andere taal.**

**Samenvattingsrichtlijnen:**
1. **Lengterichtlijnen**:
   - Voor 1-5 pagina's: 2-3 zinnen
   - Voor 6-15 pagina's: 4-6 zinnen (1-2 alinea's)
   - Voor 16-30 pagina's: 6-10 zinnen (2-3 alinea's)
   - Voor meer dan 30 pagina's: 8-12 zinnen (3-4 alinea's)
   - Voor webinhoud (enkele pagina): 3-8 zinnen afhankelijk van de lengte van de inhoud

2. **Inhoudsrichtlijnen**:
   - Vat hoofdthema's, belangrijke gebeurtenissen en belangrijke boodschappen samen
   - Voeg specifieke details en voorbeelden toe waar relevant
   - Behoud de toon en stijl van de originele inhoud
   - Voeg geen commentaar of analyse toe tenzij deze in het origineel staan
   - Wees uitgebreid maar beknopt

**De huidige inhoud heeft {page_count} pagina's.**

**Samenvatting:**""")
