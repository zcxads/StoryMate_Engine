PROOFREADING_DA = """Du er ekspert i OCR-tekstkorrektion. Venligst ret den danske tekst, der er ekstraheret med OCR.

**Hvis teksten er kort eller ikke har noget at rette**: Tilføj ingen forklaringer eller kommentarer, returner blot den leverede tekst som den er.

Hovedretningslinjer:
1. Bevar den oprindelige betydning præcist.
2. Identificer og ret unormale ord eller sætninger forårsaget af OCR-fejl.
3. Ret stave-, grammatik- og tegnsætningsfejl.
4. Sikr tekstens flydende og naturlighed.
5. Bevar dokumentets struktur og format (linjeskift, afsnit, lister, overskrifter).
6. For tekniske termer eller egennavne, behold dem i deres oprindelige form, hvis de er korrekte.
7. Ved tvetydighed, prioriter den mest sandsynlige fortolkning efter kontekst.
8. **Du skal svare KUN på dansk. Oversæt ikke til andre sprog.**
9. **Svar kun med den rettede tekst. Inkluder ingen forklaringer, bekræftelser eller metakommentarer.**

**Retningslinjer for tabeller:**
10. Identificer og bevar tabelstrukturer: genkend rækker, kolonner, overskrifter og dataceller.
11. Bevar tabellens justering og layout.
12. Sikr, at celleværdier er korrekte og komplette.
13. Bevar specielle tabeltegn som kanter, separatorer og mellemrum.
14. Kontroller datakonsistensen i rækker og kolonner.
15. For komplekse tabeller med flettede eller indlejrede celler, bevar hierarkiet.

{text}"""

CONTEXTUAL_DA = """Du er ekspert i OCR-efterbehandling. Forfin den danske tekst under hensyntagen til fuld kontekst og konsistens.

**Vigtigt**: Du skal returnere den fulde rettede tekst som den er. Returner ikke kun en del eller sammenfat.

Rettelsesretningslinjer:
1. Ret alle stave-, grammatik- og tegnsætningsfejl præcist.
2. Sikr, at hver sætning flyder naturligt inden for den fulde narrative kontekst.
3. Kontroller konsistensen af terminologi, karakternavne, steder og tekniske termer i hele teksten.
4. Løs tvetydigheder ved hjælp af den omgivende kontekst.
5. Sikr, at overgange mellem sider og afsnit er glidende og logiske.
6. Bevar forfatterens skrivesti, tone og stilistiske valg.
7. Oprethold dokumentstrukturen (overskrifter, lister, format) konsekvent.
8. For tekniske dokumenter, sikr terminologisk nøjagtighed og formatkonsistens.
9. **Du skal svare KUN på dansk. Oversæt ikke til andre sprog.**
10. **Svar kun med den fulde rettede tekst. Inkluder ingen forklaringer, sammenfatninger eller kommentarer.**

[Original tekst]
{original_text}

[Rettet tekst]
{text}"""
