"""
Indonesian summary prompt
"""

from langchain_core.prompts import PromptTemplate

INDONESIAN_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["book_content"],
    partial_variables={"page_count": ""},
    template="""Anda adalah peringkas konten profesional. Anda HARUS menjawab HANYA dalam BAHASA INDONESIA.

**Konten yang akan diringkas:**
{book_content}

**PENTING: Anda HARUS menjawab dalam BAHASA INDONESIA. JANGAN terjemahkan ke bahasa lain.**

**Pedoman ringkasan:**
1. **Pedoman panjang**:
   - Untuk 1-5 halaman: 2-3 kalimat
   - Untuk 6-15 halaman: 4-6 kalimat (1-2 paragraf)
   - Untuk 16-30 halaman: 6-10 kalimat (2-3 paragraf)
   - Untuk lebih dari 30 halaman: 8-12 kalimat (3-4 paragraf)
   - Untuk konten web (halaman tunggal): 3-8 kalimat tergantung panjang konten

2. **Pedoman konten**:
   - Ringkas tema utama, peristiwa kunci, dan pesan penting
   - Sertakan detail spesifik dan contoh yang relevan
   - Pertahankan nada dan gaya konten asli
   - Jangan tambahkan komentar atau analisis kecuali ada di aslinya
   - Komprehensif tetapi ringkas

**Konten saat ini memiliki {page_count} halaman.**

**Ringkasan:**""")
