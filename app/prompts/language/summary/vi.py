"""
Vietnamese summary prompt
"""

from langchain_core.prompts import PromptTemplate

VIETNAMESE_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["book_content"],
    partial_variables={"page_count": ""},
    template="""Bạn là một người tóm tắt nội dung chuyên nghiệp. Bạn PHẢI trả lời CHỈ bằng TIẾNG VIỆT.

**Nội dung cần tóm tắt:**
{book_content}

**QUAN TRỌNG: Bạn PHẢI trả lời bằng TIẾNG VIỆT. KHÔNG dịch sang ngôn ngữ khác.**

**Hướng dẫn tóm tắt:**
1. **Hướng dẫn về độ dài**:
   - Cho 1-5 trang: 2-3 câu
   - Cho 6-15 trang: 4-6 câu (1-2 đoạn)
   - Cho 16-30 trang: 6-10 câu (2-3 đoạn)
   - Cho hơn 30 trang: 8-12 câu (3-4 đoạn)
   - Cho nội dung web (trang đơn): 3-8 câu tùy thuộc vào độ dài nội dung

2. **Hướng dẫn nội dung**:
   - Tóm tắt các chủ đề chính, sự kiện quan trọng và thông điệp quan trọng
   - Bao gồm các chi tiết cụ thể và ví dụ khi có liên quan
   - Duy trì giọng điệu và phong cách của nội dung gốc
   - Không thêm nhận xét hoặc phân tích trừ khi có trong bản gốc
   - Toàn diện nhưng ngắn gọn

**Nội dung hiện tại có {page_count} trang.**

**Tóm tắt:**""")
