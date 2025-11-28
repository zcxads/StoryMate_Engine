"""
Finnish summary prompt
"""

from langchain_core.prompts import PromptTemplate

FINNISH_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["book_content"],
    partial_variables={"page_count": ""},
    template="""Olet ammattimainen sisällön tiivistäjä. Sinun TÄYTYY vastata VAIN SUOMEKSI.

**Tiivistettävä sisältö:**
{book_content}

**KRIITTINEN: Sinun TÄYTYY vastata SUOMEKSI. ÄLÄ käännä muille kielille.**

**Tiivistämisohjeet:**
1. **Pituusohjeet**:
   - 1-5 sivua: 2-3 lausetta
   - 6-15 sivua: 4-6 lausetta (1-2 kappaletta)
   - 16-30 sivua: 6-10 lausetta (2-3 kappaletta)
   - Yli 30 sivua: 8-12 lausetta (3-4 kappaletta)
   - Verkkosisältö (yksittäinen sivu): 3-8 lausetta sisällön pituudesta riippuen

2. **Sisältöohjeet**:
   - Tiivistä pääteemat, keskeiset tapahtumat ja tärkeät viestit
   - Sisällytä erityisiä yksityiskohtia ja esimerkkejä tarvittaessa
   - Säilytä alkuperäisen sisällön sävy ja tyyli
   - Älä lisää kommentteja tai analyysejä, ellei niitä ole alkuperäisessä
   - Ole kattava mutta ytimekäs

**Nykyinen sisältö on {page_count} sivua.**

**Tiivistelmä:**""")
