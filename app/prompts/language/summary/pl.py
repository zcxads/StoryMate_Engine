"""
Polish summary prompt
"""

from langchain_core.prompts import PromptTemplate

POLISH_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["book_content"],
    partial_variables={"page_count": ""},
    template="""Jesteś profesjonalnym streszczeniem treści. Musisz odpowiadać TYLKO po POLSKU.

**Treść do podsumowania:**
{book_content}

**KRYTYCZNE: Musisz odpowiadać po POLSKU. NIE tłumacz na inny język.**

**Wytyczne dotyczące streszczenia:**
1. **Wytyczne dotyczące długości**:
   - Dla 1-5 stron: 2-3 zdania
   - Dla 6-15 stron: 4-6 zdań (1-2 akapity)
   - Dla 16-30 stron: 6-10 zdań (2-3 akapity)
   - Dla ponad 30 stron: 8-12 zdań (3-4 akapity)
   - Dla treści internetowych (pojedyncza strona): 3-8 zdań w zależności od długości treści

2. **Wytyczne dotyczące treści**:
   - Podsumuj główne tematy, kluczowe wydarzenia i ważne przesłania
   - Uwzględnij konkretne szczegóły i przykłady, gdy są istotne
   - Zachowaj ton i styl oryginalnej treści
   - Nie dodawaj komentarzy ani analiz, chyba że są w oryginale
   - Bądź wszechstronny, ale zwięzły

**Obecna treść ma {page_count} stron.**

**Streszczenie:**""")
