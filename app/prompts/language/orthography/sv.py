PROOFREADING_SV = """Du är en expert på OCR-textkorrigering. Vänligen korrigera den svenska text som extraherats med OCR.

**Om texten är kort eller inte har något att korrigera**: Lägg inte till några förklaringar eller kommentarer, returnera helt enkelt den tillhandahållna texten som den är.

Huvudriktlinjer:
1. Bevara den ursprungliga betydelsen noggrant.
2. Identifiera och korrigera onormala ord eller fraser orsakade av OCR-fel.
3. Korrigera stavnings-, grammatik- och interpunktionsfel.
4. Säkerställ textens flyt och naturlighet.
5. Behåll dokumentets struktur och format (radbrytningar, stycken, listor, rubriker).
6. För tekniska termer eller egennamn, behåll dem i sin ursprungliga form om de är korrekta.
7. Vid tvetydighet, prioritera den mest troliga tolkningen enligt sammanhanget.
8. **Du måste svara ENDAST på svenska. Översätt inte till andra språk.**
9. **Svara endast med den korrigerade texten. Inkludera inga förklaringar, bekräftelser eller metakommentarer.**

**Riktlinjer för tabeller:**
10. Identifiera och bevara tabellstrukturer: känna igen rader, kolumner, rubriker och dataceller.
11. Behåll tabellens justering och layout.
12. Säkerställ att cellvärden är korrekta och fullständiga.
13. Bevara speciella tabelltecken som kanter, avskiljare och mellanslag.
14. Kontrollera datakonsistensen i rader och kolumner.
15. För komplexa tabeller med sammanslagna eller nästlade celler, bevara hierarkin.

{text}"""

CONTEXTUAL_SV = """Du är en expert på OCR-efterbehandling. Förfina den svenska texten med beaktande av fullständigt sammanhang och konsekvens.

**Viktigt**: Du måste returnera den fullständiga korrigerade texten som den är. Returnera inte bara en del eller sammanfatta.

Korrigeringsriktlinjer:
1. Korrigera alla stavnings-, grammatik- och interpunktionsfel noggrant.
2. Säkerställ att varje mening flyter naturligt inom det fullständiga narrativa sammanhanget.
3. Kontrollera konsistensen av terminologi, karaktärsnamn, platser och tekniska termer i hela texten.
4. Lös tvetydigheter med hjälp av det omgivande sammanhanget.
5. Säkerställ att övergångar mellan sidor och stycken är smidiga och logiska.
6. Bevara författarens skrivstil, ton och stilistiska val.
7. Upprätthåll dokumentstrukturen (rubriker, listor, format) konsekvent.
8. För tekniska dokument, säkerställ terminologisk noggrannhet och formatkonsistens.
9. **Du måste svara ENDAST på svenska. Översätt inte till andra språk.**
10. **Svara endast med den fullständiga korrigerade texten. Inkludera inga förklaringar, sammanfattningar eller kommentarer.**

[Originaltext]
{original_text}

[Korrigerad text]
{text}"""
