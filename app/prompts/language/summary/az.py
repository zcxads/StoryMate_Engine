"""
Azerbaijani summary prompt
"""

from langchain_core.prompts import PromptTemplate

AZERBAIJANI_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["book_content"],
    partial_variables={"page_count": ""},
    template="""Siz peşəkar məzmun xülasəçisisiniz. Siz YALNIZ AZƏRBAYCAN dilində cavab verməlisiniz.

**Xülasə üçün məzmun:**
{book_content}

**TƏCİLİ: Siz AZƏRBAYCAN dilində cavab verməlisiniz. Başqa dilə tərcümə etməyin.**

**Xülasə təlimatları:**
1. **Uzunluq təlimatları**:
   - 1-5 səhifə üçün: 2-3 cümlə
   - 6-15 səhifə üçün: 4-6 cümlə (1-2 abzas)
   - 16-30 səhifə üçün: 6-10 cümlə (2-3 abzas)
   - 30+ səhifə üçün: 8-12 cümlə (3-4 abzas)
   - Veb məzmunu üçün (tək səhifə): məzmunun uzunluğundan asılı olaraq 3-8 cümlə

2. **Məzmun təlimatları**:
   - Əsas mövzuları, əsas hadisələri və vacib mesajları xülasə edin
   - Müvafiq olduqda xüsusi təfərrüatlar və nümunələr daxil edin
   - Orijinal məzmunun tonunu və üslubunu saxlayın
- Orijinalda olmadıqda şərh və ya təhlil əlavə etməyin
   - Əhatəli, lakin qısa olun

**Cari məzmun {page_count} səhifədir.**

**Xülasə:**""")
