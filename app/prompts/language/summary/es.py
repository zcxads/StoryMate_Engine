"""
Spanish summary prompt
"""

from langchain_core.prompts import PromptTemplate

SPANISH_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["book_content"],
    partial_variables={"page_count": ""},
    template="""Usted es un resumidor profesional de contenido. Debe responder SOLO en ESPAÑOL.

**Contenido a resumir:**
{book_content}

**CRÍTICO: Debe responder en ESPAÑOL. NO traduzca a ningún otro idioma.**

**Pautas de resumen:**
1. **Pautas de longitud**:
   - Para 1-5 páginas: 2-3 oraciones
   - Para 6-15 páginas: 4-6 oraciones (1-2 párrafos)
   - Para 16-30 páginas: 6-10 oraciones (2-3 párrafos)
   - Para más de 30 páginas: 8-12 oraciones (3-4 párrafos)
   - Para contenido web (página única): 3-8 oraciones según la longitud del contenido

2. **Pautas de contenido**:
   - Resuma los temas principales, eventos clave y mensajes importantes
   - Incluya detalles específicos y ejemplos cuando sea relevante
   - Mantenga el tono y estilo del contenido original
   - No agregue comentarios o análisis a menos que esté en el original
   - Sea completo pero conciso

**El contenido actual tiene {page_count} páginas.**

**Resumen:**""")
