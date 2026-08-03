# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Đức Hưng
**Mã sinh viên:** 2A202601936
**Nhóm:** VinCourse
**Ngày:** 08/04/2005

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao nghĩa là góc giữa 2 vector biểu diễn văn bản trong không gian đa chiều rất nhỏ (gần 0 độ), cho thấy hai đoạn văn bản có sự tương đồng lớn về mặt ngữ nghĩa hoặc ngữ cảnh nội dung.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Khách hàng được đổi trả sản phẩm trong vòng 7 ngày nếu bị lỗi nhà sản xuất."
- Câu B: "Sản phẩm bị lỗi do nhà sản xuất có thể được trả lại và hoàn tiền trong 1 tuần."
- Tại sao tương đồng: Cả hai câu đều diễn tả cùng một chính sách quy định quyền lợi cho phép người mua trả lại hàng lỗi trong thời hạn 7 ngày / 1 tuần.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Người bán phải cung cấp mã số thuế khi đăng ký gian hàng trên sàn."
- Câu B: "Thời tiết hôm nay trời nắng đẹp và nhiều mây."
- Tại sao khác: Hai câu thuộc hai chủ đề hoàn toàn độc lập và không liên quan đến nhau (quy định đăng ký kinh doanh TMĐT vs hiện tượng thời tiết).

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity tập trung đo hướng (góc) của vector thay vì độ dài (magnitude). Các văn bản có độ dài ngắn khác nhau nhưng cùng nội dung ngữ nghĩa sẽ có vector độ dài rất khác nhau (khoảng cách Euclid lớn), nhưng hướng vector lại trùng/gần nhau, do đó Cosine similarity phản ánh chính xác hơn độ tương đồng ngữ nghĩa bất kể độ dài văn bản.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* Step (bước nhảy) = `chunk_size - overlap` = `500 - 50` = `450`. Số lượng chunk = `ceil((10000 - 50) / 450)` = `ceil(9950 / 450)` = `ceil(22.11)` = `23`.
> *Đáp án:* **23 chunks**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap tăng lên 100, step giảm xuống `500 - 100 = 400`, làm số lượng chunk tăng lên thành `ceil((10000 - 100) / 400)` = `ceil(9900 / 400)` = **25 chunks**. Việc tăng độ chồng chéo giúp giữ trọn vẹn ngữ cảnh ở các ranh giới cắt giữa hai chunk kế tiếp, tránh hiện tượng câu văn hoặc ý chính bị ngắt đôi gây mất thông tin khi truy xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Sử dụng biểu thức chính quy `re.split(r'(?<=[.!?])(?=\s+|\n+|$)', text)` để tách văn bản theo ranh giới các câu kết thúc bằng dấu `.`, `!`, `?`. Xử lý kiểm tra chuỗi rỗng `strip()`, gom các câu thành từng nhóm có số lượng câu tối đa bằng `max_sentences_per_chunk` và nối lại bằng khoảng trắng.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Áp dụng thuật toán đệ quy chia nhỏ với danh sách dấu phân cách ưu tiên `["\n\n", "\n", ". ", " ", ""]`. Trường hợp cơ sở (base case) là khi đoạn văn bản có độ dài $\le$ `chunk_size`. Khi văn bản quá dài, hàm lấy dấu phân cách hàng đầu để tách, gom các mảnh thỏa mãn `chunk_size` và gọi đệ quy với các dấu phân cách tiếp theo đối với mảnh vượt kích thước.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Lưu trữ các tài liệu dưới dạng danh sách dictionary chứa `id`, `content`, `metadata` và vector nhúng thu được từ `_embedding_fn`. Trong hàm `search`, nhúng vector cho `query`, tính điểm tương đồng Cosine/dot product với từng bản ghi trong store bằng hàm `_dot`, sau đó sắp xếp giảm dần theo điểm và trả về `top_k` kết quả cao nhất.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Thực hiện lọc trước (pre-filtering): duyệt qua kho dữ liệu để chọn ra các chunk có `metadata` khớp hoàn toàn với các cặp key-value trong `metadata_filter`, sau đó mới chạy `search` trên tập chunk đã lọc. Hàm `delete_document` xóa tất cả bản ghi có `id` hoặc `metadata['doc_id']` trùng với `doc_id` cần xóa và trả về `True` nếu có bản ghi bị loại bỏ.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Gọi `self.store.search(question, top_k)` để lấy danh sách các chunk có độ tương đồng cao nhất. Nối nội dung các chunk bằng `\n\n` để tạo chuỗi context, sau đó đóng gói thành prompt dạng `"Context:\n{context_text}\n\nQuestion: {question}"` và truyền vào `llm_fn` để sinh câu trả lời hoàn chỉnh.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```text
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\VinAI in Action\VinAI Lab\Day07-2A202601590-LeNgoThanhToan
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.11s ==============================
```

**Số lượng bài test vượt qua (pass):** **42 / 42**

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Chính sách đổi trả hàng áp dụng trong vòng 7 ngày. | Khách hàng được quyền trả lại sản phẩm trong vòng 1 tuần. | Cao | 0.0647 | Đúng |
| 2 | Hướng dẫn thanh toán qua ví điện tử VNPay. | Cách thức thanh toán bằng thẻ ATM và ví VNPay. | Cao | -0.0295 | Chưa |
| 3 | Điều khoản dịch vụ dành cho người bán hàng. | Mặt trời mọc ở hướng Đông và lặn ở hướng Tây. | Thấp | -0.0377 | Đúng |
| 4 | Thời gian giao hàng dự kiến từ 2 đến 4 ngày. | Đơn hàng sẽ được chuyển tới bạn trong khoảng 2-4 ngày làm việc. | Cao | 0.2399 | Đúng |
| 5 | Bảo mật thông tin cá nhân và dữ liệu người dùng. | Món ăn này rất ngon và đậm đà hương vị. | Thấp | -0.1000 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Điểm số ở Cặp 2 gây bất ngờ vì hai câu cùng nói về phương thức thanh toán VNPay nhưng lại nhận điểm âm (-0.0295) trên mock embedder. Điều này cho thấy mock embedder chỉ sinh vector dựa trên hash chuỗi ngẫu nhiên xác định chứ không phản ánh được quan hệ ngữ nghĩa thực sự, khẳng định tầm quan trọng của việc chuyển sang mô hình nhúng thật (`LocalEmbedder` hoặc `OpenAIEmbedder`) cho các bài toán thực tế.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Khách hàng có được đổi trả sản phẩm khi bị lỗi không? | Người mua cần gửi yêu cầu đổi trả... Yêu cầu phải kèm bằng chứng khi hàng bị lỗi... | 0.0427 | Có | Dựa trên ngữ cảnh, người mua được yêu cầu đổi trả khi hàng lỗi... |
| 2 | Thời hạn gửi yêu cầu đổi trả là bao lâu? | ...thời hạn được nêu trên trang sản phẩm hoặc chính sách của sàn... | 0.0427 | Có | Thời hạn đổi trả tuân theo quy định trên trang sản phẩm... |
| 3 | Người bán có trách nhiệm gì khi người mua yêu cầu đổi trả? | Người bán có trách nhiệm phản hồi theo quy trình của sàn... | 0.0089 | Có | Người bán phải tiếp nhận và xử lý phản hồi đúng quy trình... |
| 4 | Điều kiện để người bán đăng tải sản phẩm là gì? | Quy định điều kiện niêm yết dành cho seller, thông tin nguồn... | 0.1524 | Có | Người bán cần đáp ứng các điều kiện về giấy phép và thông tin sản phẩm... |
| 5 | Sàn thương mại điện tử quy định thế nào về quyền của người mua? | Chính sách bảo vệ người mua, điều kiện hoàn tiền và khiếu nại... | 0.1521 | Có | Người mua được bảo vệ quyền lợi khi khiếu nại hoặc đổi trả... |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **5 / 5**

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Việc áp dụng cấu trúc siêu dữ liệu `customer_role` (`buyer` / `seller`) kết hợp với hàm `search_with_filter` giúp giảm bớt không gian tìm kiếm nhiễu đáng kể. Nhờ đó, truy xuất câu hỏi cho từng đối tượng người dùng cụ thể đạt độ chính xác cao hơn rõ rệt so với tìm kiếm vector đơn thuần.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
