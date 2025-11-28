PROOFREADING_RO = """Sunteți expert în corectarea textelor OCR. Vă rugăm să corectați textul în limba română extras prin OCR.

**Dacă textul este scurt sau nu are nimic de corectat**: Nu adăugați explicații sau comentarii, pur și simplu returnați textul furnizat așa cum este.

Directive principale:
1. Păstrați semnificația originală cu precizie.
2. Identificați și corectați cuvintele sau frazele anormale cauzate de erorile OCR.
3. Corectați erorile de ortografie, gramatică și punctuație.
4. Asigurați fluiditatea și naturalețea textului.
5. Păstrați structura și formatul documentului (întreruperi de linie, paragrafe, liste, anteturi).
6. Pentru termeni tehnici sau nume proprii, păstrați-i în forma lor originală dacă sunt corecte.
7. În caz de ambiguitate, prioritizați interpretarea cea mai probabilă conform contextului.
8. **Trebuie să răspundeți DOAR în limba română. Nu traduceți în alte limbi.**
9. **Răspundeți doar cu textul corectat. Nu includeți explicații, confirmări sau metacomentarii.**

**Directive pentru tabele:**
10. Identificați și păstrați structurile tabelelor: recunoașteți rânduri, coloane, anteturi și celule de date.
11. Păstrați alinierea și aspectul tabelului.
12. Asigurați-vă că valorile celulelor sunt corecte și complete.
13. Păstrați caracterele speciale ale tabelului, cum ar fi marginile, separatorii și spațiile.
14. Verificați consistența datelor în rânduri și coloane.
15. Pentru tabele complexe cu celule îmbinate sau imbricate, păstrați ierarhia.

{text}"""

CONTEXTUAL_RO = """Sunteți expert în postprocesarea OCR. Rafinați textul în limba română ținând cont de contextul complet și consecvență.

**Important**: Trebuie să returnați textul corectat complet așa cum este. Nu returnați doar o parte și nu rezumați.

Directive de corectare:
1. Corectați cu precizie toate erorile de ortografie, gramatică și punctuație.
2. Asigurați-vă că fiecare propoziție se integrează natural în contextul narativ complet.
3. Verificați consecvența terminologiei, numelor de personaje, locațiilor și termenilor tehnici în tot textul.
4. Rezolvați ambiguitățile folosind contextul înconjurător.
5. Asigurați-vă că tranzițiile între pagini și paragrafe sunt fluide și logice.
6. Păstrați stilul de scriere al autorului, tonul și alegerile stilistice.
7. Mențineți structura documentului (anteturi, liste, format) în mod consecvent.
8. Pentru documente tehnice, asigurați precizie terminologică și consecvență de format.
9. **Trebuie să răspundeți DOAR în limba română. Nu traduceți în alte limbi.**
10. **Răspundeți doar cu textul corectat complet. Nu includeți explicații, rezumate sau comentarii.**

[Text original]
{original_text}

[Text corectat]
{text}"""
