"""
English summary prompt
"""

from langchain_core.prompts import PromptTemplate

ENGLISH_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["book_content"],
    partial_variables={"page_count": ""},
    template="""You are a professional content summarizer. You MUST respond in ENGLISH ONLY.

**Content to Summarize:**
{book_content}

**CRITICAL: You MUST respond in ENGLISH. Do NOT translate to any other language.**

**Summary Guidelines:**
1. **Length Guidelines**:
   - For 1-5 pages: 2-3 sentences
   - For 6-15 pages: 4-6 sentences (1-2 paragraphs)
   - For 16-30 pages: 6-10 sentences (2-3 paragraphs)
   - For 30+ pages: 8-12 sentences (3-4 paragraphs)
   - For web content (single page): 3-8 sentences depending on content length

2. **Content Guidelines**:
   - Summarize main themes, key events, and important messages
   - Include specific details and examples when relevant
   - Maintain the tone and style of the original content
   - Do not add commentary or analysis unless it's in the original
   - Be comprehensive but concise

**Current content has {page_count} pages.**

**FINAL REMINDER: Respond in ENGLISH ONLY.**

**Summary:**""")
