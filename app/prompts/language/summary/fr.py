"""
French summary prompt
"""

from langchain_core.prompts import PromptTemplate

FRENCH_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["book_content"],
    partial_variables={"page_count": ""},
    template="""Vous êtes un résumé professionnel de contenu. Vous DEVEZ répondre UNIQUEMENT en FRANÇAIS.

**Contenu à résumer:**
{book_content}

**CRITIQUE: Vous DEVEZ répondre en FRANÇAIS. NE traduisez pas dans une autre langue.**

**Directives de résumé:**
1. **Directives de longueur**:
   - Pour 1-5 pages: 2-3 phrases
   - Pour 6-15 pages: 4-6 phrases (1-2 paragraphes)
   - Pour 16-30 pages: 6-10 phrases (2-3 paragraphes)
   - Pour plus de 30 pages: 8-12 phrases (3-4 paragraphes)
   - Pour contenu web (page unique): 3-8 phrases selon la longueur du contenu

2. **Directives de contenu**:
   - Résumez les thèmes principaux, événements clés et messages importants
   - Incluez des détails spécifiques et des exemples pertinents
   - Maintenez le ton et le style du contenu original
   - N'ajoutez pas de commentaires ou d'analyses sauf s'ils sont dans l'original
   - Soyez complet mais concis

**Le contenu actuel a {page_count} pages.**

**Résumé:**""")
