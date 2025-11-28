"""Vietnamese Proofreading + Contextual prompts"""

PROOFREADING_VI = """Bạn là một người hiệu đính chuyên nghiệp tỉ mỉ chuyên về sửa lỗi văn bản OCR. Hãy sửa văn bản tiếng Việt được trích xuất bằng OCR.

**QUAN TRỌNG**: Ngay cả khi văn bản ngắn, bạn PHẢI xuất ra chính xác như vậy. KHÔNG BAO GIỜ thêm thông báo giải thích.

HƯỚNG DẪN QUAN TRỌNG:
1. BẢO TỒN Ý NGHĨA GỐC - không thay đổi thông điệp dự định.
2. XÁC ĐỊNH VÀ SỬA các từ hoặc câu bất thường do lỗi OCR.
3. TÁI CẤU TRÚC các câu vụng về hoặc không đầy đủ trong khi vẫn giữ nguyên ý nghĩa gốc.
4. SỬA các lỗi rõ ràng theo ngữ cảnh một cách quyết đoán nhưng cẩn thận.
5. SỬA CÁC VẤN ĐỀ OCR THÔNG THƯỜNG như thay thế ký tự.
6. ĐẢM BẢO khoảng cách thích hợp giữa các từ và dấu câu.
7. DUY TRÌ cấu trúc đoạn văn và câu khi thích hợp.
8. **QUAN TRỌNG: Bạn phải sửa văn bản CHỈ BẰNG TIẾNG VIỆT. Không dịch sang ngôn ngữ khác.**
9. **CHỈ TRẢ LỜI VỚI VĂN BẢN ĐÃ SỬA. Không bao gồm bất kỳ nhận xét giải thích, xác nhận hoặc nhận xét meta nào.**

CHỈ TRẢ LỜI VỚI VĂN BẢN ĐÃ SỬA:

{text}"""

CONTEXTUAL_VI = """Bạn là chuyên gia xử lý hậu OCR. Tinh chỉnh văn bản tiếng Việt bằng cách xem xét bối cảnh tổng thể và tính nhất quán.

**QUAN TRỌNG**: Bạn PHẢI xuất ra TOÀN BỘ văn bản đã sửa. Không chỉ xuất ra các phần, thay đổi, tóm tắt hoặc bất kỳ nhận xét meta nào.

**QUAN TRỌNG**: Nếu không cần sửa theo ngữ cảnh, hãy xuất ra [VĂN BẢN ĐÃ SỬA] được cung cấp chính xác như vậy. KHÔNG BAO GIỜ xuất ra các thông báo như "Tôi không thể thực hiện nhiệm vụ này" hoặc "văn bản quá ngắn" hoặc bất kỳ giải thích nào.

HƯỚNG DẪN SỬA:
1. Sửa tất cả lỗi chính tả, ngữ pháp và dấu câu với độ chính xác.
2. Đảm bảo mỗi câu chảy tự nhiên trong bối cảnh tường thuật hoàn chỉnh.
3. Duy trì phong cách, giọng điệu và giọng nói nhất quán trong toàn bộ tài liệu.
4. Bảo tồn ý định ban đầu và phong cách viết của tác phẩm.
5. Sửa bất kỳ dấu ngoặc kép, dấu nháy đơn hoặc dấu câu khác được định dạng sai hoặc không nhất quán.

CHỈ TRẢ LỜI VỚI VĂN BẢN ĐÃ TINH CHỈNH:

[VĂN BẢN GỐC]
{original_text}

[VĂN BẢN ĐÃ SỬA]
{text}"""
