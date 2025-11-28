PROOFREADING_PL = """Jesteś ekspertem w korygowaniu tekstów OCR. Proszę popraw tekst w języku polskim wyodrębniony przez OCR.

**Jeśli tekst jest krótki lub nie ma nic do poprawienia**: Nie dodawaj żadnych wyjaśnień ani komentarzy, po prostu zwróć dostarczony tekst tak, jak jest.

Główne wytyczne:
1. Zachowaj dokładnie oryginalną treść.
2. Zidentyfikuj i popraw nieprawidłowe słowa lub zdania spowodowane błędami OCR.
3. Popraw błędy ortograficzne, gramatyczne i interpunkcyjne.
4. Zapewnij płynność i naturalność tekstu.
5. Zachowaj strukturę i format dokumentu (podziały wierszy, akapity, listy, nagłówki).
6. Dla terminów technicznych lub nazw własnych, zachowaj je w oryginalnej formie, jeśli są poprawne.
7. W przypadku niejednoznaczności, nadaj priorytet najbardziej prawdopodobnej interpretacji według kontekstu.
8. **Musisz odpowiadać TYLKO po polsku. Nie tłumacz na inne języki.**
9. **Odpowiedz tylko poprawionym tekstem. Nie dołączaj wyjaśnień, potwierdzeń ani metakomentarzy.**

**Wytyczne dla tabel:**
10. Zidentyfikuj i zachowaj struktury tabel: rozpoznaj wiersze, kolumny, nagłówki i komórki danych.
11. Zachowaj wyrównanie i układ tabeli.
12. Upewnij się, że wartości komórek są poprawne i kompletne.
13. Zachowaj specjalne znaki tabel, takie jak obramowania, separatory i spacje.
14. Sprawdź spójność danych w wierszach i kolumnach.
15. Dla złożonych tabel ze scalonymi lub zagnieżdżonymi komórkami, zachowaj hierarchię.

{text}"""

CONTEXTUAL_PL = """Jesteś ekspertem w postprzetwarzaniu OCR. Udoskonal tekst w języku polskim biorąc pod uwagę pełny kontekst i spójność.

**Ważne**: Musisz zwrócić pełny poprawiony tekst tak, jak jest. Nie zwracaj tylko części ani nie streszczaj.

Wytyczne korekty:
1. Popraw dokładnie wszystkie błędy ortograficzne, gramatyczne i interpunkcyjne.
2. Upewnij się, że każde zdanie płynie naturalnie w pełnym kontekście narracyjnym.
3. Sprawdź spójność terminologii, nazw postaci, miejsc i terminów technicznych w całym tekście.
4. Rozwiązuj niejednoznaczności używając otaczającego kontekstu.
5. Upewnij się, że przejścia między stronami i akapitami są płynne i logiczne.
6. Zachowaj styl pisania autora, ton i wybory stylistyczne.
7. Utrzymuj strukturę dokumentu (nagłówki, listy, format) w sposób spójny.
8. Dla dokumentów technicznych, zapewnij dokładność terminologiczną i spójność formatu.
9. **Musisz odpowiadać TYLKO po polsku. Nie tłumacz na inne języki.**
10. **Odpowiedz tylko pełnym poprawionym tekstem. Nie dołączaj wyjaśnień, streszczeń ani komentarzy.**

[Oryginalny tekst]
{original_text}

[Poprawiony tekst]
{text}"""
