# Biến thể K4 (K4 Variant) — Truy xuất Chính sách Thương mại điện tử (E-commerce Policy Retrieval)

K4 dùng chung cam kết mã nguồn cốt lõi (core coding contract) với K3, nhưng Giai đoạn 2 (Phase 2) phải xây dựng cơ sở tri thức (knowledge base) về **chính sách thương mại điện tử hoặc hỗ trợ khách hàng (customer support)** (ví dụ: thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán).

## Quy tắc riêng của K4

- Mỗi tài liệu (document) phải có metadata `customer_role` (ví dụ: `buyer`, `seller`, `both`) và ít nhất một trường (field) hữu ích khác.
- Ngoài việc truy xuất bằng metadata, mỗi tài liệu phải có `source_url`, `retrieved_at` và `document_version`; chỉ dùng chính sách công khai hoặc được phép chia sẻ.
- Trong 5 câu hỏi đánh giá (benchmark query), có ít nhất một câu hỏi cần `metadata_filter={"customer_role": "seller"}` hoặc `buyer`.
- Ít nhất một thành viên thử chia nhỏ (chunking) theo điều/khoản, tiêu đề (heading) hoặc cặp câu hỏi thường gặp (FAQ pair).
- Câu trả lời chuẩn (Gold answer) phải trích được từ tài liệu nhóm thu thập; không dùng chính sách không có trong tập tài liệu (corpus) để chấm truy xuất (retrieval).

Thư mục `data/k4_ecommerce/` có dữ liệu khởi động nhỏ; nhóm vẫn cần bổ sung tập tài liệu (corpus) 5–10 tài liệu theo yêu cầu Lab.
