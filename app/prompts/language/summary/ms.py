"""
Malay summary prompt
"""

from langchain_core.prompts import PromptTemplate

MALAY_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["book_content"],
    partial_variables={"page_count": ""},
    template="""Anda adalah peringkas kandungan profesional. Anda MESTI menjawab HANYA dalam BAHASA MELAYU.

**Kandungan untuk diringkaskan:**
{book_content}

**PENTING: Anda MESTI menjawab dalam BAHASA MELAYU. JANGAN terjemahkan ke bahasa lain.**

**Garis panduan ringkasan:**
1. **Garis panduan panjang**:
   - Untuk 1-5 muka surat: 2-3 ayat
   - Untuk 6-15 muka surat: 4-6 ayat (1-2 perenggan)
   - Untuk 16-30 muka surat: 6-10 ayat (2-3 perenggan)
   - Untuk lebih daripada 30 muka surat: 8-12 ayat (3-4 perenggan)
   - Untuk kandungan web (muka surat tunggal): 3-8 ayat bergantung pada panjang kandungan

2. **Garis panduan kandungan**:
   - Ringkaskan tema utama, peristiwa penting, dan mesej penting
   - Sertakan butiran khusus dan contoh yang berkaitan
   - Kekalkan nada dan gaya kandungan asal
   - Jangan tambah komen atau analisis melainkan ada dalam asal
   - Menyeluruh tetapi ringkas

**Kandungan semasa mempunyai {page_count} muka surat.**

**Ringkasan:**""")
