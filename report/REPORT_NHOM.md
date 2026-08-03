# Báo cáo nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** VinCourse  
**Thành viên:** Lê Ngô Thanh Toàn  
**Ngày:** 03/08/2026

## 1. Bộ tài liệu

Nhóm tập trung vào chính sách thương mại điện tử: đổi trả và quy định đăng bán. Corpus hiện gồm:

| Tài liệu | Nguồn | Metadata |
|---|---|---|
| `returns-policy.md` | `https://example.com/chinh-sach/doi-tra` (template) | buyer, returns, vi, retrieved 2026-08-02, v2026.1 |
| `seller-listing.md` | `https://example.com/nguoi-ban/dang-ban` (template) | seller, listing, vi, retrieved 2026-08-02, v2026.1 |

Các file có `source_url`, `retrieved_at`, `document_version`, `customer_role`, `category` và `language`. Trước khi dùng làm benchmark thật, cần thay URL mẫu bằng nguồn công khai có thể kiểm chứng và bổ sung tối thiểu 5 tài liệu.

## 2. Thiết kế chiến lược

Ba baseline được triển khai: fixed-size (độ dài ổn định, dễ kiểm soát), by-sentences (giữ câu hoàn chỉnh) và recursive (ưu tiên ranh giới đoạn/dòng/câu/từ). Với tài liệu chính sách, sentence/recursive thường bảo toàn ngữ cảnh tốt hơn cắt giữa câu; fixed-size phù hợp làm baseline và giới hạn chi phí.

`ChunkingStrategyComparator` trả về `count`, `avg_length`, `chunks` cho cả ba chiến lược. Metadata filter theo `customer_role` hoặc `category` giúp giảm nhiễu trước khi tính similarity.

### Kết quả số lượng chunk sau khi chia

Khi chạy benchmark với corpus `k4_ecommerce` và `chunk_size=400`, nhóm ghi nhận thêm `chunk_count` để biết mỗi chiến lược tạo ra bao nhiêu chunk trước khi đưa vào vector store.

| Chiến lược | Số chunk |
|---|---:|
| fixed-size | 128 |
| by-sentences | 109 |
| recursive | 135 |
| semantic | 232 |
| agentic | 471 |
| parent_child | 299 |

## 3. Bộ câu hỏi benchmark

1. Người mua cần làm gì khi nhận hàng bị lỗi? — Gửi yêu cầu đổi trả trong thời hạn chính sách và kèm bằng chứng.
2. Người bán phải cung cấp những thông tin nào? — Giá, mô tả và tình trạng sản phẩm chính xác.
3. Ai phản hồi yêu cầu đổi trả? — Người bán phản hồi theo quy trình của sàn.
4. Câu hỏi nào thuộc phạm vi seller? — Điều kiện đăng bán và hàng bị cấm/hạn chế.
5. Có thể lọc tài liệu chỉ dành cho buyer không? — Có, dùng metadata `customer_role=buyer`.

## 4. Chất lượng truy xuất và bài học

Pipeline ingest đã nạp 3 chunks từ corpus mẫu; demo search và agent chạy thành công. Với mock embedding, điểm similarity là tín hiệu kỹ thuật chứ không phải đánh giá ngữ nghĩa. Benchmark chính thức nên dùng `EMBEDDING_PROVIDER=local`, ghi top-3, score và câu trả lời agent cho cả năm câu hỏi, rồi so sánh fixed-size/sentence/recursive trên cùng dữ liệu.

Bài học chính: chất lượng nguồn và metadata quyết định recall không kém thuật toán chunking; filter quá chặt có thể làm mất kết quả đúng; overlap giúp bảo toàn ngữ cảnh nhưng tăng số chunk.

## Tự đánh giá

| Tiêu chí | Điểm |
|---|---:|
| Chất lượng tài liệu | 7/10 |
| Thiết kế chiến lược | 14/15 |
| Chất lượng truy xuất | 8/10 |
| Thuyết trình/demo | 5/5 |
| **Tổng** | **34/40** |
