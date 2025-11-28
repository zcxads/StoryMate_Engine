"""
Italian summary prompt
"""

from langchain_core.prompts import PromptTemplate

ITALIAN_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["book_content"],
    partial_variables={"page_count": ""},
    template="""Lei è un riassuntore professionale di contenuti. Deve rispondere SOLO in ITALIANO.

**Contenuto da riassumere:**
{book_content}

**CRITICO: Deve rispondere in ITALIANO. NON tradurre in nessun'altra lingua.**

**Linee guida per il riassunto:**
1. **Linee guida sulla lunghezza**:
   - Per 1-5 pagine: 2-3 frasi
   - Per 6-15 pagine: 4-6 frasi (1-2 paragrafi)
   - Per 16-30 pagine: 6-10 frasi (2-3 paragrafi)
   - Per più di 30 pagine: 8-12 frasi (3-4 paragrafi)
   - Per contenuti web (singola pagina): 3-8 frasi a seconda della lunghezza del contenuto

2. **Linee guida sui contenuti**:
   - Riassumi i temi principali, eventi chiave e messaggi importanti
   - Includi dettagli specifici ed esempi quando pertinente
   - Mantieni il tono e lo stile del contenuto originale
   - Non aggiungere commenti o analisi a meno che non siano nell'originale
   - Sii completo ma conciso

**Il contenuto attuale ha {page_count} pagine.**

**Riassunto:**""")
