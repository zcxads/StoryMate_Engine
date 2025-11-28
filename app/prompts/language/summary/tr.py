"""
Turkish summary prompt
"""

from langchain_core.prompts import PromptTemplate

TURKISH_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["book_content"],
    partial_variables={"page_count": ""},
    template="""Profesyonel bir içerik özetleyicisiniz. SADECE TÜRKÇE cevap vermelisiniz.

**Özetlenecek içerik:**
{book_content}

**KRİTİK: TÜRKÇE cevap vermelisiniz. Başka bir dile çevirmeyin.**

**Özet yönergeleri:**
1. **Uzunluk yönergeleri**:
   - 1-5 sayfa için: 2-3 cümle
   - 6-15 sayfa için: 4-6 cümle (1-2 paragraf)
   - 16-30 sayfa için: 6-10 cümle (2-3 paragraf)
   - 30'dan fazla sayfa için: 8-12 cümle (3-4 paragraf)
   - Web içeriği için (tek sayfa): içerik uzunluğuna bağlı olarak 3-8 cümle

2. **İçerik yönergeleri**:
   - Ana temaları, önemli olayları ve önemli mesajları özetleyin
   - İlgili olduğunda özel ayrıntılar ve örnekler ekleyin
   - Orijinal içeriğin tonunu ve stilini koruyun
   - Orijinalde yoksa yorum veya analiz eklemeyin
   - Kapsamlı ama özlü olun

**Mevcut içerik {page_count} sayfadır.**

**Özet:**""")
