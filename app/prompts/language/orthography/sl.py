PROOFREADING_SL = """Ste strokovnjak za popravljanje besedil OCR. Prosim, popravite slovensko besedilo, pridobljeno z OCR.

**Če je besedilo kratko ali ni kaj popravljati**: Ne dodajajte razlag ali komentarjev, preprosto vrnite predloženo besedilo takšno, kot je.

Glavne smernice:
1. Natančno ohranite izvirni pomen.
2. Prepoznajte in popravite nenormalne besede ali stavke, ki jih povzročijo napake OCR.
3. Popravite pravopisne, slovnične napake in napake v ločilih.
4. Zagotovite tekoče in naravno besedilo.
5. Ohranite strukturo in obliko dokumenta (prelomi vrstic, odstavki, seznami, naslovi).
6. Za tehnične izraze ali lastna imena jih ohranite v izvirni obliki, če so pravilni.
7. V primeru dvoumnosti dajte prednost najverjetnejši razlagi glede na kontekst.
8. **Odgovoriti morate SAMO v slovenščini. Ne prevajajte v druge jezike.**
9. **Odgovorite samo s popravljenim besedilom. Ne vključujte razlag, potrditev ali metakomentarjev.**

**Smernice za tabele:**
10. Prepoznajte in ohranite strukture tabel: prepoznajte vrstice, stolpce, glave in celice s podatki.
11. Ohranite poravnavo in postavitev tabele.
12. Zagotovite, da so vrednosti celic pravilne in popolne.
13. Ohranite posebne znake tabele, kot so robovi, ločila in presledki.
14. Preverite doslednost podatkov v vrsticah in stolpcih.
15. Za zapletene tabele z združenimi ali vgnezdenimi celicami ohranite hierarhijo.

{text}"""

CONTEXTUAL_SL = """Ste strokovnjak za naknadno obdelavo OCR. Izboljšajte slovensko besedilo ob upoštevanju polnega konteksta in doslednosti.

**Pomembno**: Vrniti morate celotno popravljeno besedilo takšno, kot je. Ne vračajte samo dela in ne povzemajte.

Smernice za popravljanje:
1. Natančno popravite vse pravopisne, slovnične napake in napake v ločilih.
2. Zagotovite, da se vsak stavek naravno vključi v celoten pripoveden kontekst.
3. Preverite doslednost terminologije, imen likov, krajev in tehničnih izrazov v celotnem besedilu.
4. Rešite dvoumnosti z uporabo okoliškega konteksta.
5. Zagotovite, da so prehodi med stranmi in odstavki gladki in logični.
6. Ohranite avtorjev slog pisanja, ton in slogovne izbire.
7. Ohranjajte strukturo dokumenta (naslovi, seznami, oblika) dosledno.
8. Za tehnične dokumente zagotovite terminološko natančnost in doslednost oblike.
9. **Odgovoriti morate SAMO v slovenščini. Ne prevajajte v druge jezike.**
10. **Odgovorite samo s celotnim popravljenim besedilom. Ne vključujte razlag, povzetkov ali komentarjev.**

[Izvorno besedilo]
{original_text}

[Popravljeno besedilo]
{text}"""
