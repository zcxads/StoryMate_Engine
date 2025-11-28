"""
Portuguese summary prompt
"""

from langchain_core.prompts import PromptTemplate

PORTUGUESE_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["book_content"],
    partial_variables={"page_count": ""},
    template="""Você é um resumidor profissional de conteúdo. Você DEVE responder APENAS em PORTUGUÊS.

**Conteúdo a resumir:**
{book_content}

**CRÍTICO: Você DEVE responder em PORTUGUÊS. NÃO traduza para nenhum outro idioma.**

**Diretrizes de resumo:**
1. **Diretrizes de comprimento**:
   - Para 1-5 páginas: 2-3 frases
   - Para 6-15 páginas: 4-6 frases (1-2 parágrafos)
   - Para 16-30 páginas: 6-10 frases (2-3 parágrafos)
   - Para mais de 30 páginas: 8-12 frases (3-4 parágrafos)
   - Para conteúdo web (página única): 3-8 frases dependendo do comprimento do conteúdo

2. **Diretrizes de conteúdo**:
   - Resuma os temas principais, eventos-chave e mensagens importantes
   - Inclua detalhes específicos e exemplos quando relevante
   - Mantenha o tom e estilo do conteúdo original
   - Não adicione comentários ou análises a menos que estejam no original
   - Seja abrangente mas conciso

**O conteúdo atual tem {page_count} páginas.**

**Resumo:**""")
