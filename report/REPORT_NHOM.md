# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** VinCourse
**Ngày:** 03/08/2026
**Thành viên:**

| STT | Họ và tên | Mã sinh viên |
|---|---|---|
| 1 | Lê Ngô Thanh Toàn | 2A202601590 |
| 2 | Nguyễn Đức Hưng | 2A202601936 |
| 3 | Tạ Thị Thu Huyền | 2A202601782 |
| 4 | Giang Trung Quân | 2A202601098 |

> Báo cáo này tổng hợp nội dung từ các thư mục cá nhân của nhóm: TODO_GiangTrungQuan, TODO_LeNgoThanhToan, TODO_TaThiThuHuyen và DAY07_2A202601936_NguyenDucHung. Phần cá nhân vẫn được lưu riêng trong từng file REPORT_CANHAN của mỗi người.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng, tập trung vào các vấn đề đổi trả, quy định đăng bán, quyền lợi người mua và người bán.

**Phạm vi cụ thể nhóm tập trung:**
> Chúng tôi xây dựng hệ thống RAG cho các chính sách thương mại điện tử, ưu tiên các câu hỏi liên quan đến đổi trả, điều kiện đăng bán và trách nhiệm của người bán/người mua.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Chính sách đổi trả | Template / dữ liệu lab | 2026-08-02 / v2026.1 | Khoảng 2k-5k | buyer, returns, vi, retrieved 2026-08-02 |
| 2 | Quy định đăng bán | Template / dữ liệu lab | 2026-08-02 / v2026.1 | Khoảng 2k-5k | seller, listing, vi, retrieved 2026-08-02 |
| 3 | Chính sách hỗ trợ khách hàng | Template / dữ liệu lab | 2026-08-02 / v2026.1 | Khoảng 2k-5k | customer_support, vi |
| 4 | Tài liệu benchmark quy định sản phẩm | Template / dữ liệu lab | 2026-08-02 / v2026.1 | Khoảng 2k-5k | category, seller, vi |
| 5 | Tài liệu tham khảo nội dung sản phẩm | Template / dữ liệu lab | 2026-08-02 / v2026.1 | Khoảng 2k-5k | category, buyer, vi |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chủ yếu dùng dữ liệu lab và template có thể kiểm chứng được trong phạm vi bài tập.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` hoặc ngày hiệu lực trong metadata.
- [x] Metadata có thể phân loại theo vai trò `customer_role`, `category` và `language` để hỗ trợ lọc trước khi truy xuất.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `source_url` | string | `https://example.com/chinh-sach/doi-tra` | Giúp kiểm chứng nguồn và kiểm soát chất lượng dữ liệu. |
| `retrieved_at` | date | `2026-08-02` | Cho biết thời điểm thu thập tài liệu. |
| `document_version` | string | `v2026.1` | Giúp theo dõi phiên bản và tránh dùng tài liệu cũ. |
| `customer_role` | string | `buyer`, `seller` | Hữu ích để lọc các tài liệu phù hợp với vai trò người dùng. |
| `category` | string | `returns`, `listing` | Giúp nhóm dữ liệu theo chủ đề và giảm nhiễu. |
| `language` | string | `vi` | Hỗ trợ xử lý đa ngôn ngữ và lọc nội dung đúng ngôn ngữ. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử một hướng tiếp cận khác nhau trên cùng bộ tài liệu; nhóm tổng hợp lại để so sánh hiệu quả.

### Phân tích đường cơ sở (Baseline Analysis)

Nhóm đã thử các chiến lược chia chunk cơ bản như fixed-size, sentence-based và recursive. Mục tiêu là giữ ngữ cảnh ở ranh giới câu và đoạn văn mà vẫn kiểm soát kích thước chunk.

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| Chính sách đổi trả | Fixed-size | 128 | Trung bình | Có, nhưng hơi bị cắt ngắt ở ranh giới |
| Chính sách đổi trả | Sentence-based | 109 | Trung bình | Có, tốt hơn ở các câu hoàn chỉnh |
| Chính sách đổi trả | Recursive | 135 | Trung bình | Tốt nhất, bảo toàn ngữ cảnh đoạn văn |

### Chiến lược của từng thành viên

**Thành viên 1 — Giang Trung Quân**
- **Loại chiến lược:** Sentence chunking và Recursive chunking
- **Mô tả & lý do chọn:** Quân tập trung vào việc tách văn bản theo câu và cấu trúc đoạn để tránh cắt mất ý nghĩa giữa các câu. Cách này phù hợp cho chính sách có nhiều điều khoản và điều kiện.

**Thành viên 2 — Lê Ngô Thanh Toàn**
- **Loại chiến lược:** Recursive chunking và hệ thống embedding store
- **Mô tả & lý do chọn:** Toàn chú trọng vào việc xây dựng pipeline RAG đầy đủ: chunk, embedding, lưu trữ, tìm kiếm và trả lời bằng agent. Mục tiêu là giữ được ngữ cảnh và dễ dàng mở rộng cho các truy vấn phức tạp.

**Thành viên 3 — Tạ Thị Thu Huyền**
- **Loại chiến lược:** Semantic/meaning-based retrieval và metadata filtering
- **Mô tả & lý do chọn:** Huyền cho rằng retrieval hiệu quả không chỉ phụ thuộc vào chunking mà còn phụ thuộc vào việc lọc metadata và dùng embedding thực tế để tìm đúng tài liệu liên quan.

**Thành viên 4 — Nguyễn Đức Hưng**
- **Loại chiến lược:** Recursive/Sentence chunking kết hợp pre-filtering metadata
- **Mô tả & lý do chọn:** Hưng nhấn mạnh rằng metadata như `customer_role` và `category` giúp giảm nhiễu và nâng cao độ chính xác cho câu hỏi chuyên biệt của người mua hoặc người bán.

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Giang Trung Quân | Sentence/Recursive | 8.5 | Bảo toàn ngữ cảnh tốt | Cần thêm metadata để giảm nhiễu |
| Lê Ngô Thanh Toàn | Recursive + store/search | 8.5 | Pipeline rõ ràng, dễ mở rộng | Cần embedding thực tế hơn cho benchmark |
| Tạ Thị Thu Huyền | Semantic + metadata filter | 9.0 | Chính xác cho câu hỏi cụ thể | Yêu cầu chuẩn bị dữ liệu và metadata tốt hơn |
| Nguyễn Đức Hưng | Recursive + pre-filter | 8.5 | Giảm nhiễu, phù hợp cho truy vấn theo vai trò | Cần kiểm thử nhiều hơn với dữ liệu thực |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Chiến lược tốt nhất cho chủ đề chính sách thương mại điện tử là kết hợp recursive chunking với metadata filtering. Recursive chunking tốt ở việc giữ ngữ cảnh, còn metadata filtering giúp hệ thống không bị lẫn giữa các tài liệu của người mua và người bán. Đây là cách hiệu quả nhất để tăng độ chính xác của retrieval.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> Nhóm thống nhất 5 câu hỏi đa dạng, có thể kiểm chứng và có ít nhất một câu cần dùng metadata lọc để trả lời tốt hơn.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Khách hàng có được đổi trả sản phẩm khi bị lỗi không? | Có, nếu sản phẩm bị lỗi hoặc không đúng mô tả và có đủ bằng chứng kèm theo. | Chính sách đổi trả |
| 2 | Thời hạn gửi yêu cầu đổi trả là bao lâu? | Thường phải gửi trong thời hạn quy định của chính sách và trong vòng thời gian nhất định từ khi nhận hàng. | Chính sách đổi trả |
| 3 | Người bán có trách nhiệm gì khi người mua yêu cầu đổi trả? | Người bán phải phản hồi, xử lý theo quy trình của sàn và cung cấp thông tin chính xác. | Chính sách đổi trả / seller policy |
| 4 | Điều kiện để người bán đăng tải sản phẩm là gì? | Người bán cần cung cấp thông tin sản phẩm đúng, đầy đủ và tuân thủ quy định đăng bán. | Quy định đăng bán |
| 5 | Sàn thương mại điện tử có quy định gì về quyền lợi người mua? | Người mua được bảo vệ bởi chính sách đổi trả, khiếu nại và quy định về thông tin sản phẩm. | Chính sách hỗ trợ khách hàng |

### Tổng hợp chất lượng truy xuất của nhóm

> Theo cách chấm của lab, mỗi câu được chấm 2 điểm nếu tìm được chunk liên quan trong top-3 và agent trả lời đúng. Nếu chỉ có chunk liên quan nhưng không ở top-1, điểm sẽ giảm.

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Khách hàng đổi trả khi lỗi | Recursive + metadata filter | Có | Câu này phù hợp với `buyer` |
| 2 | Thời hạn đổi trả | Sentence chunking | Có | Chunk cần giữ ngữ cảnh thời gian |
| 3 | Trách nhiệm người bán | Recursive + filter | Có | Metadata giúp tránh nhầm với seller policy |
| 4 | Điều kiện đăng bán | Metadata filter | Có | Câu này rõ ràng nhất cho `seller` |
| 5 | Quyền lợi người mua | Semantic retrieval | Có | Cần ngữ cảnh tổng quát và không bị nhiễu |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Có, đặc biệt ở các câu hỏi liên quan đến vai trò `buyer` hoặc `seller`. Ví dụ câu hỏi về điều kiện đăng bán nên lọc theo `customer_role=seller` để tránh trả về các chunk về chính sách đổi trả cho người mua. Metadata giúp giảm nhiễu và tăng độ chính xác của truy xuất.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
- Chunking tốt giúp bảo toàn ngữ cảnh, nhưng nếu không kết hợp metadata thì retrieval vẫn dễ bị nhiễu.
- Chính sách thương mại điện tử phù hợp để làm benchmark vì có nhiều câu hỏi rõ ràng và có thể kiểm chứng.
- Mô hình embedding thực tế cho kết quả tốt hơn mock embedding, đặc biệt khi đánh giá ngữ nghĩa.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng một bộ tài liệu nhưng chiến lược khác nhau cho kết quả khác biệt. Recursive chunking giúp giữ ngữ cảnh tốt hơn, trong khi metadata filtering làm tăng độ đúng của retrieval. Đây là hai yếu tố quan trọng trong RAG.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ dùng dữ liệu chất lượng hơn, bổ sung nhiều nguồn công khai và metadata đầy đủ hơn; đồng thời sẽ chuyển sang embedder thực tế thay vì mock embedder trong benchmark chính thức.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10/10 |
| Thiết kế chiến lược (Strategy Design) | 15/15 |
| Chất lượng truy xuất (Retrieval Quality) | 10/10 |
| Thuyết trình (Demo) | 5/5 |
| **Tổng phần nhóm** | **40/40** |
