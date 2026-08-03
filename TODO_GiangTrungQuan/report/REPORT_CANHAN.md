# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Giang Trung Quân
**Nhóm:** Nhóm 1
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao nghĩa là các vector nhúng (embeddings) của hai đoạn văn bản chỉ về cùng một hướng (hoặc gần cùng hướng) trong không gian vector. Điều này biểu thị rằng hai văn bản có sự tương đồng mạnh mẽ về mặt ngữ nghĩa (semantic similarity), cùng thảo luận về một chủ đề hoặc ý tưởng, mặc dù từ ngữ hoặc độ dài của chúng có thể khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Tôi muốn đổi trả sản phẩm này vì nó bị lỗi."
- Câu B: "Sản phẩm bị hỏng nên tôi cần gửi lại để hoàn tiền."
- Tại sao tương đồng: Cả hai câu đều thể hiện cùng một ý định (người mua muốn gửi trả hàng do sản phẩm bị lỗi/hỏng), mặc dù sử dụng các từ ngữ khác nhau như "đổi trả" vs "gửi lại để hoàn tiền", và "lỗi" vs "hỏng".

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Chính sách bảo hành sản phẩm kéo dài trong vòng 12 tháng."
- Câu B: "Hôm nay trời nắng đẹp thích hợp đi dã ngoại."
- Tại sao khác: Hai câu nói về hai chủ đề hoàn toàn khác nhau và không liên quan gì đến nhau (một bên là điều khoản bảo hành sản phẩm thương mại điện tử, một bên là thời tiết và hoạt động giải trí dã ngoại).

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Khoảng cách Euclid đo khoảng cách trực tiếp giữa hai điểm đầu mút vector nên bị ảnh hưởng lớn bởi độ dài của văn bản (độ dài vector). Ngược lại, độ tương tự cosine chỉ tập trung vào góc giữa hai vector (hướng đi của ngữ nghĩa) và hoàn toàn không phụ thuộc vào độ dài văn bản, giúp so sánh chính xác độ tương đồng ngữ nghĩa giữa các văn bản dài ngắn khác nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Phép tính:
> - Sử dụng công thức: `số lượng chunk = làm_tròn_lên((độ_dài_tài_liệu - độ_chồng_chéo) / (kích_thước_chunk - độ_chồng_chéo))`
> - Thay số: `làm_tròn_lên((10000 - 50) / (500 - 50)) = làm_tròn_lên(9950 / 450) = làm_tròn_lên(22.11) = 23`
>
> **Đáp án:** 23 chunks

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> - Khi overlap tăng lên 100, số lượng chunk sẽ tăng lên: `làm_tròn_lên((10000 - 100) / (500 - 100)) = làm_tròn_lên(9900 / 400) = làm_tròn_lên(24.75) = 25` chunks.
> - Lý do muốn tăng độ chồng chéo: Để bảo toàn liên kết ngữ cảnh giữa các chunk liền kề. Giúp tránh việc các thông tin quan trọng hoặc câu văn bị ngắt đôi ngay tại ranh giới phân tách chunk, đảm bảo mô hình truy xuất RAG không bị mất thông tin ngữ cảnh khi tìm kiếm.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng biểu thức chính quy (regex) có cơ chế lookbehind `(?<=\. )|(?<=\! )|(?<=\? )|(?<=\.\n)` để tách văn bản thành các câu mà không làm mất đi dấu kết thúc câu và khoảng trắng ngăn cách. Sau đó, gom các câu này thành từng nhóm có số lượng tối đa là `max_sentences_per_chunk` câu, rồi tiến hành loại bỏ khoảng trắng thừa ở đầu/cuối của từng chunk bằng `strip()`.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán đệ quy duyệt qua danh sách dấu phân cách theo độ ưu tiên giảm dần.
> - Trường hợp cơ sở (base case): Nếu độ dài văn bản nhỏ hơn hoặc bằng `chunk_size`, trả về văn bản đó. Nếu danh sách dấu phân cách trống hoặc gặp dấu `""`, chia văn bản theo ký tự.
> - Trường hợp đệ quy: Sử dụng dấu phân cách hiện tại để tách văn bản. Đối với các đoạn phân tách có độ dài lớn hơn `chunk_size`, gọi đệ quy `_split` bằng các dấu phân cách tiếp theo. Cuối cùng, gộp các đoạn nhỏ lại với nhau bằng dấu phân cách hiện tại sao cho tổng độ dài của mỗi chunk không vượt quá `chunk_size`.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> - `add_documents`: Hỗ trợ lưu trữ thông qua ChromaDB (gọi hàm `add()` với các mảng tương ứng) hoặc lưu trực tiếp trong bộ nhớ RAM qua danh sách `self._store` chứa các record dictionary chuẩn hóa gồm `id`, `content`, `metadata`, và `embedding`.
> - `search`: Nếu dùng ChromaDB, gọi hàm query trực tiếp. Nếu dùng bộ nhớ RAM, ta nhúng chuỗi truy vấn, tính toán độ tương tự cosine đối với tất cả các record bằng `compute_similarity`, sắp xếp giảm dần theo điểm tương đồng và trả về top-k record có điểm cao nhất.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> - `search_with_filter`: Đối với in-memory store, thực hiện lọc các record trong `self._store` thỏa mãn toàn bộ các điều kiện khóa-giá trị của `metadata_filter` trước (pre-filtering), rồi mới tiến hành tính độ tương tự cosine và xếp hạng. Với ChromaDB, truyền tham số `where` vào hàm `query()`.
> - `delete_document`: Xóa các record bằng cách kiểm tra xem `metadata['doc_id'] == doc_id` hoặc ID của record bằng `doc_id` hoặc bắt đầu bằng tiền tố `doc_id::` (để bao quát cả tài liệu thô lẫn tài liệu đã chia nhỏ thành các chunk).

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Thực hiện RAG bằng cách: Gọi `self.store.search` để lấy ra top-k chunk ngữ cảnh có độ liên quan cao nhất đối với câu hỏi. Sau đó, nối các chunk này lại bằng ký tự xuống dòng kép `\n\n` để làm phần ngữ cảnh (context), rồi chèn ngữ cảnh cùng câu hỏi vào một template prompt RAG chuẩn mực, cuối cùng gọi hàm `self.llm_fn` để lấy câu trả lời cuối cùng từ mô hình ngôn ngữ lớn.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
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

============================= 42 passed in 0.42s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Quy trình đổi trả sản phẩm được thực hiện trong vòng 7 ngày kể từ ngày nhận hàng. | Khách hàng có thể trả lại hàng và nhận hoàn tiền trong 7 ngày đầu tiên. | Cao | -0.2889 | Sai |
| 2 | Người bán phải chịu phí vận chuyển nếu gửi sai sản phẩm. | Phí ship hàng đổi trả do nhà bán hàng thanh toán nếu giao nhầm mẫu. | Cao | -0.1664 | Sai |
| 3 | Vui lòng giữ nguyên tem mác khi hoàn trả sản phẩm. | Sản phẩm đổi trả cần có đầy đủ nhãn mác và chưa qua sử dụng. | Cao | 0.0712 | Sai |
| 4 | Chính sách này áp dụng cho tất cả người mua hàng trên nền tảng. | Người bán cần đăng ký thông tin doanh nghiệp trước khi đăng bán sản phẩm. | Thấp | 0.1463 | Sai |
| 5 | Hôm nay tôi ăn cơm tấm sườn bì chả rất ngon. | Đại lộ Thăng Long là con đường huyết mạch của thủ đô Hà Nội. | Thấp | -0.3303 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Kết quả bất ngờ nhất là các câu có ý nghĩa rất giống nhau (Cặp 1, 2, 3) lại có độ tương tự cosine rất thấp (thậm chí âm), trong khi cặp câu không mấy liên quan (Cặp 4) lại có điểm số dương cao hơn.
> Điều này xảy ra bởi vì ta đang sử dụng `MockEmbedder` để tạo vector dựa trên việc hash chuỗi ký tự bằng MD5. Kết quả này phản ánh rằng mô hình Mock không lưu giữ bất kỳ ý nghĩa ngữ nghĩa nào của từ ngữ mà chỉ đại diện cho sự ngẫu nhiên của các chuỗi ký tự. Để các embeddings biểu diễn đúng ý nghĩa ngữ nghĩa thực sự, ta bắt buộc phải sử dụng các mô hình ngôn ngữ huấn luyện sẵn (như `sentence-transformers` cục bộ hoặc OpenAI API) - nơi mà các từ đồng nghĩa hoặc ngữ cảnh tương tự sẽ được ánh xạ về gần nhau trong không gian vector đa chiều.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

*(Dữ liệu bên dưới được đo trực tiếp từ file dữ liệu khởi động `data/k4_ecommerce/` bằng SentenceChunker)*

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Yêu cầu đổi trả cần những bằng chứng gì? | k4-returns-policy::chunk_1: "Yêu cầu phải kèm bằng chứng phù hợp khi hàng bị lỗi hoặc không đúng mô tả..." | 0.1573 | Có | Câu trả lời dựa trên ngữ cảnh: Yêu cầu phải kèm bằng chứng phù hợp khi hàng bị lỗi hoặc không đúng mô tả... |
| 2 | Người bán có trách nhiệm gì trong quy trình đổi trả hàng? | k4-returns-policy::chunk_1: "Yêu cầu phải kèm bằng chứng phù hợp khi hàng bị lỗi... Người bán có trách nhiệm phản hồi theo quy trình của sàn..." | 0.0831 | Có | Câu trả lời dựa trên ngữ cảnh: Người bán có trách nhiệm phản hồi theo quy trình của sàn... |
| 3 | Người bán chịu trách nhiệm cung cấp những thông tin sản phẩm nào khi đăng bán? | k4-seller-listing::chunk_1: "Nhóm cần bổ sung danh mục hàng cấm và quy trình xử lý vi phạm từ nguồn chính thức trước khi tạo..." | 0.1553 | Không (nằm ở Rank 2) | Câu trả lời dựa trên ngữ cảnh: Nhóm cần bổ sung danh mục hàng cấm và quy trình xử lý vi phạm từ nguồn chính thức... |
| 4 | Những sản phẩm nào không được phép đăng bán trên sàn? | k4-seller-listing::chunk_1: "Nhóm cần bổ sung danh mục hàng cấm và quy trình xử lý vi phạm từ nguồn chính thức trước khi tạo..." | 0.3398 | Không (nằm ở Rank 2) | Câu trả lời dựa trên ngữ cảnh: Nhóm cần bổ sung danh mục hàng cấm và quy trình xử lý vi phạm từ nguồn chính thức... |
| 5 | Quy định đăng bán sản phẩm dành riêng cho người bán là gì? | k4-seller-listing::chunk_1: "Nhóm cần bổ sung danh mục hàng cấm và quy trình xử lý vi phạm từ nguồn chính thức trước khi tạo..." | 0.1691 | Không (nằm ở Rank 2) | Câu trả lời dựa trên ngữ cảnh: Nhóm cần bổ sung danh mục hàng cấm và quy trình xử lý vi phạm... |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5
*(Giải thích: Mặc dù với MockEmbedder, vị trí Rank 1 bị sai lệch và đưa ra thông tin không đúng ý nghĩa, nhưng các chunk chứa câu trả lời đúng cho các câu hỏi 3, 4, 5 vẫn nằm ở Rank 2 của kết quả tìm kiếm top-3).*

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Tôi học được rằng việc sử dụng bộ lọc siêu dữ liệu (metadata filtering) trước khi tìm kiếm là vô cùng quan trọng để loại bỏ nhiễu ngữ cảnh. Khi ta chỉ tìm kiếm trên các tài liệu phù hợp với vai trò của người dùng (ví dụ: chỉ lọc tài liệu dành cho `buyer` hoặc `seller`), chất lượng tìm kiếm tăng lên rõ rệt và tránh được việc nhầm lẫn thông tin giữa các nhóm chính sách khác nhau.

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
