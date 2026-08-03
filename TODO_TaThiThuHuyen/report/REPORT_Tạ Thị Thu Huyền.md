# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Tạ Thị Thu Huyền 
**Nhóm:** VinCourse
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao nghĩa là hai vector đại diện cho hai đoạn văn bản có hướng gần nhau trong không gian nhiều chiều. Điều này thường cho thấy hai văn bản có ý nghĩa ngữ nghĩa tương đồng.

**Ví dụ có độ tương tự CAO:**
- Câu A: Con mèo ngủ say trên chiếc ghế sofa.
- Câu B: Một chú mèo con đang nằm nghỉ trên chiếc ghế dài. 
- Tại sao tương đồng: Cả hai câu đều miêu tả một con mèo đang nghỉ trên ghế, dù sử dụng các từ gần nghĩa như “ngủ say”/“nằm nghỉ” và “sofa”/“ghế dài”.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Con mèo ngủ say trên chiếc sofa. 
- Câu B: Giá vàng hôm nay trên thị trường tiếp tục giảm mạnh. 
- Tại sao khác: Hai câu thuộc hai lĩnh vực hoàn toàn khác nhau (động vật/ đời sống so với tài chính/kinh tế), không có sự giao thoa về ngữ cảnh hay từ vựng.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Độ tương tự cosine đánh giá góc giữa hai vector thay vì khoảng cách tuyệt đối, nhờ đó ít bị ảnh hưởng bởi độ lớn của vector. Điều này phù hợp khi so sánh ý nghĩa của các văn bản có độ dài khác nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Số chunk = ceil((10,000 - 50) / (500 - 50))
> = ceil(9,950 / 450)
> = ceil(22.111...)
> = **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Số chunk = ceil((10,000 - 100) / (500 - 100)) = ceil(24.75) = **25 chunks**. Khi overlap tăng, bước nhảy giảm từ 450 xuống 400 ký tự nên số chunk tăng từ 23 lên 25. Overlap lớn hơn giúp bảo toàn ngữ cảnh ở ranh giới giữa các chunk, nhưng cũng làm tăng dữ liệu trùng lặp và chi phí xử lý.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> *Viết 2-3 câu: dùng biểu thức chính quy (regex) gì để phát hiện câu? Xử lý trường hợp ngoại lệ (edge case) nào?* 
Tôi sử dụng biểu thức chính quy để tách văn bản tại các ranh giới
`. `, `! `, `? ` hoặc `.\n`, đồng thời giữ lại dấu kết thúc câu.
Sau đó, tôi loại bỏ khoảng trắng thừa và nhóm tối đa
`max_sentences_per_chunk` câu vào mỗi chunk. Với văn bản rỗng, hàm
trả về danh sách rỗng; các câu còn dư được đưa vào chunk cuối cùng.

*Ý tưởng hoạt động:* 
Văn bản
   ↓
Tách thành từng câu
   ↓
Loại bỏ khoảng trắng thừa
   ↓
Cứ mỗi 3 câu tạo thành một chunk

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Tôi chia văn bản đệ quy theo thứ tự ưu tiên `"\n\n"`, `"\n"`, `". "`, `" "` và cuối cùng là từng ký tự. Base case là khi đoạn hiện tại không vượt quá `chunk_size`; nếu hết separator mà đoạn vẫn quá dài, đoạn được cắt trực tiếp theo số ký tự để bảo đảm kích thước.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> `add_documents` tạo embedding cho nội dung, sao chép metadata, bổ sung `doc_id` nếu thiếu và lưu record gồm ID, content, metadata và embedding. `search` embedding câu truy vấn, tính dot product với từng vector đã lưu, sắp xếp điểm giảm dần rồi trả về tối đa `top_k` kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` lọc record theo tất cả cặp key-value trong `metadata_filter` trước, sau đó mới tính độ tương tự trên các ứng viên còn lại. `delete_document` tìm và xóa toàn bộ chunk có `metadata["doc_id"]` trùng với ID được yêu cầu; hàm trả về `True` nếu có dữ liệu bị xóa và `False` nếu không tìm thấy.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> `answer` truy xuất các chunk liên quan nhất và ghép chúng thành phần ngữ cảnh có đánh số trong prompt. Prompt yêu cầu LLM chỉ trả lời dựa trên ngữ cảnh và thừa nhận thiếu thông tin nếu context không đủ, sau đó toàn bộ prompt được truyền cho `llm_fn`.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts ==============================
platform darwin -- Python 3.11.14, pytest-9.1.1
collected 42 items

tests/test_solution.py ..........................................        [100%]

============================== 42 passed in 0.27s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Khách hàng có thể yêu cầu hoàn tiền cho sản phẩm bị lỗi. | Người mua được quyền đề nghị hoàn tiền khi hàng hóa có lỗi. | cao | -0.101 | Không |
| 2 | Người bán phải mô tả sản phẩm chính xác. | Thông tin sản phẩm do người bán cung cấp phải đúng sự thật. | cao | -0.003 | Không |
| 3 | Đơn hàng sẽ được giao trong ba ngày làm việc. | Thời gian vận chuyển dự kiến là ba ngày làm việc. | cao | 0.193 | Có (cao nhất trong 5 cặp) |
| 4 | Người mua cần gửi bằng chứng khi hàng không đúng mô tả. | Sản phẩm bị cấm không được phép đăng bán. | thấp | 0.126 | Có |
| 5 | Chính sách đổi trả bảo vệ quyền lợi người mua. | Mạng nơ-ron sâu được sử dụng trong trí tuệ nhân tạo. | thấp | 0.042 | Có |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Kết quả bất ngờ nhất là hai cặp đầu có ý nghĩa rất gần nhau nhưng điểm lại gần 0 hoặc âm. Nguyên nhân là lần chạy này sử dụng `_mock_embed`, vốn sinh vector xác định từ toàn bộ chuỗi nhưng không biểu diễn ngữ nghĩa; vì vậy các điểm trên chỉ dùng để kiểm tra `compute_similarity`, chưa phù hợp để kết luận về chất lượng ngữ nghĩa. Cần chạy lại bảng bằng `LocalEmbedder` trước khi nộp kết quả benchmark chính thức.

### Giải thích vì sao `Điểm thực tế` có thể âm

- Cosine similarity có phạm vi từ -1 đến 1; giá trị âm có nghĩa là hai vector có hướng gần như ngược nhau (không phải lỗi tính toán tự nhiên).  
- Nếu dùng dot product mà **không chuẩn hoá** (L2-normalize) các embedding, kết quả có thể âm do ảnh hưởng của cả hướng và độ lớn (magnitude).  
- Việc sử dụng `_mock_embed` (hoặc embedder không biểu diễn ngữ nghĩa) có thể tạo ra vectors không phản ánh ngữ nghĩa, dẫn tới điểm gần 0 hoặc âm dù hai câu thực sự tương đồng.  
- Lỗi logic (ví dụ tính `expected - actual` thay vì `actual - expected`, hoặc nhân với trọng số âm) cũng có thể gây ra giá trị âm.

Hướng khắc phục và các bước kiểm tra nhanh:
- Chạy lại bảng bằng `LocalEmbedder` thay vì `_mock_embed` để có embedding biểu diễn ngữ nghĩa.  
- Chuẩn hoá embedding trước khi tính cosine: `emb /= np.linalg.norm(emb, axis=-1, keepdims=True)`.  
- In/log các thành phần trung gian (embedding vectors, dot/cosine trước và sau chuẩn hoá, reward, penalty, baseline) để xác định bước nào gây dấu âm.  
- Kiểm tra hàm similarity: đảm bảo dùng cosine đã chuẩn hoá hoặc tính cosine bằng `dot(normalize(a), normalize(b))`.  
- Nếu điểm âm vẫn xuất hiện sau chuẩn hoá và dùng embedder thực tế, ghi chú rõ trong báo cáo rằng giá trị âm là hợp lệ với cosine và giải thích ý nghĩa (khác hướng, không tương đồng).

Ví dụ kiểm tra nhanh (Python):

```python
emb1 = embed_fn(text1)
emb2 = embed_fn(text2)
emb1 = emb1 / np.linalg.norm(emb1)
emb2 = emb2 / np.linalg.norm(emb2)
sim = float(np.dot(emb1, emb2))
print('cosine:', sim)
```

Kết luận: những giá trị âm trong bảng (ví dụ -0.101, -0.003) có khả năng do `mock` embedding hoặc thiếu chuẩn hoá; cần chạy lại với `LocalEmbedder` và làm các bước debug ở trên để xác nhận và sửa báo cáo nếu cần.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Khi Nhà Bán bấm khiếu nại, Tiki sẽ phản hồi trong bao lâu? | Mục IV hỗ trợ Nhà Bán, chứa thời hạn phản hồi | 0,8669 | Có, top-1 | Chưa chạy LLM; chunk đủ căn cứ cho đáp án 03–05 ngày làm việc |
| 2 | Giá bán không khuyến mãi có được thấp hơn 1.000 đồng không? | Mục quy định giá tối thiểu và ngoại lệ quà tặng | 0,8104 | Có, top-1 | Chưa chạy LLM; chunk đủ căn cứ trả lời “không”, trừ quà tặng |
| 3 | Nhà Bán thao tác thế nào để tạo kho trả hàng? | Chunk chứa thông tin người nhận và các bước tạo kho | 0,6315 | Có, top-1 | Chưa chạy LLM; bằng chứng top-1 chứa quy trình thao tác |
| 4 | Nêu 5 từ/cụm từ không được dùng trong nội dung sản phẩm nhóm Làm đẹp – Sức khỏe, Mẹ và bé hoặc Bách Hóa Online.| Mục II chứa bảng từ không hợp lệ và hợp lệ | 0,6447 | Có, top-1 | Chưa chạy LLM; chunk đủ năm ví dụ trong gold answer |
| 5 | Sản phẩm hoàn trả có vấn đề thì làm gì và trong thời hạn nào? | Chunk đổi trả chứa thao tác Khiếu nại và thời hạn 02 ngày | 0,7204 | Có, top-1 | Chưa chạy LLM; chunk đủ căn cứ để trả lời gold answer |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5 (10/10 điểm retrieval; SemanticChunker + LocalEmbedder đa ngữ)

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Qua demo các nhóm, mình học được vài điểm thực tiễn rất hữu ích:
>
> - Lựa chọn bộ câu hỏi đánh giá sát thực tế giúp benchmark retrieval rõ ràng hơn.  
> - Chunking theo ngữ nghĩa (SemanticChunker) thường trả về các chunk liên quan hơn so với tách theo ký tự thuần tuý.  
> - Luôn dùng embedding thực tế (ví dụ `LocalEmbedder`) thay vì mock khi đánh giá chất lượng — kết quả mock có thể gây hiểu nhầm.  
> - Thiết kế prompt rõ ràng và log các giá trị trung gian (embeddings, norms, dot/cosine, reward/penalty) giúp phát hiện nguyên nhân điểm bất thường (như giá trị âm).  
>
> Những thực hành này đã giúp nhóm mình cải thiện chất lượng truy xuất và độ tin cậy khi đánh giá kết quả.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5/ 5 |
| Hướng tiếp cận của tôi (My Approach) | 10/ 10 |
| Hoàn thiện code (Core Implementation — tests) | 30/ 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5/ 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10/ 10 |
| **Tổng phần cá nhân** | **60/ 60** |
