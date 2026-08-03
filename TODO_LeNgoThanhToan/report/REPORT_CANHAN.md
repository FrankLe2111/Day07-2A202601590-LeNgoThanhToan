# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Lê Ngô Thanh Toàn
**Nhóm:** VinCourse
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm gồm lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá và demo được nộp chung trong `REPORT_NHOM.md`. Chi tiết thang điểm được trình bày trong `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60 điểm** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine — Cosine Similarity (Bài tập 1.1)

#### Độ tương tự cosine cao nghĩa là gì?

Độ tương tự cosine cao nghĩa là hai vector embedding có hướng gần giống nhau trong không gian vector. Điều này thường cho thấy hai đoạn văn bản có nội dung, chủ đề hoặc ý nghĩa ngữ nghĩa tương đồng, ngay cả khi chúng không sử dụng chính xác cùng một từ.

#### Ví dụ có độ tương tự cao

* **Câu A:** Sinh viên cần đăng ký môn học trước thời hạn.
* **Câu B:** Học viên phải hoàn thành việc đăng ký học phần trước ngày hết hạn.
* **Tại sao tương đồng:** Hai câu sử dụng từ ngữ khác nhau nhưng đều truyền đạt cùng một ý nghĩa: sinh viên phải đăng ký môn học trước một thời điểm nhất định.

#### Ví dụ có độ tương tự thấp

* **Câu A:** Sinh viên cần đăng ký môn học trước thời hạn.
* **Câu B:** Hôm nay thời tiết có mưa lớn ở Hà Nội.
* **Tại sao khác:** Hai câu nói về hai chủ đề hoàn toàn khác nhau. Câu A liên quan đến đăng ký học tập, trong khi câu B liên quan đến thời tiết.

#### Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?

Cosine similarity tập trung vào góc giữa hai vector, tức là hướng biểu diễn ngữ nghĩa, thay vì độ lớn tuyệt đối của vector. Vì độ dài văn bản hoặc chuẩn của embedding có thể làm thay đổi độ lớn vector, cosine similarity thường ổn định và phù hợp hơn để so sánh ý nghĩa của các văn bản.

---

### Bài toán tính toán Chunking (Bài tập 1.2)

#### Tài liệu 10.000 ký tự, `chunk_size = 500`, `overlap = 50`. Có bao nhiêu chunks?

Kích thước bước nhảy giữa hai chunk liên tiếp là:

```text
step = chunk_size - overlap
     = 500 - 50
     = 450 ký tự
```

Số lượng chunk được tính bằng:

```text
Số chunks = ceil((document_length - chunk_size) / step) + 1
           = ceil((10.000 - 500) / 450) + 1
           = ceil(9.500 / 450) + 1
           = ceil(21,11) + 1
           = 22 + 1
           = 23 chunks
```

**Đáp án: 23 chunks.**

Chunk cuối cùng có thể chứa ít hơn 500 ký tự vì nó chỉ lưu phần còn lại của tài liệu.

#### Nếu overlap tăng lên 100, số lượng chunk thay đổi thế nào?

Khi `overlap = 100`, bước nhảy mới là:

```text
step = 500 - 100 = 400 ký tự
```

Số lượng chunk là:

```text
Số chunks = ceil((10.000 - 500) / 400) + 1
           = ceil(9.500 / 400) + 1
           = ceil(23,75) + 1
           = 24 + 1
           = 25 chunks
```

Như vậy, số lượng chunk tăng từ **23 lên 25 chunks**. Overlap lớn hơn giúp giữ lại nhiều ngữ cảnh tại ranh giới giữa các chunk, hạn chế trường hợp một câu hoặc một ý quan trọng bị chia tách, nhưng đồng thời làm tăng số lượng vector cần lưu trữ và tìm kiếm.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ — Chunking Functions

#### `SentenceChunker.chunk` — Hướng tiếp cận

Tôi sử dụng biểu thức chính quy như `(?<=[.!?])\s+` để xác định vị trí kết thúc câu dựa trên các dấu `.`, `!` và `?`, sau đó ghép lần lượt các câu vào một chunk cho đến khi đạt gần `chunk_size`. Khi thêm một câu mới khiến chunk vượt quá giới hạn, chunk hiện tại được lưu lại và một chunk mới được tạo.

Tôi cũng xử lý các trường hợp ngoại lệ như văn bản rỗng, văn bản không có dấu kết thúc câu, khoảng trắng dư thừa và một câu riêng lẻ dài hơn `chunk_size`. Với câu quá dài, câu được chia nhỏ theo từ hoặc theo số ký tự để bảo đảm không tạo ra chunk vượt quá giới hạn cho phép.

#### `RecursiveChunker.chunk` / `_split` — Hướng tiếp cận

Recursive chunking thử chia văn bản theo thứ tự từ cấu trúc lớn đến cấu trúc nhỏ, chẳng hạn:

```python
["\n\n", "\n", ". ", " ", ""]
```

Đầu tiên, thuật toán thử chia theo đoạn văn. Nếu một phần vẫn dài hơn `chunk_size`, hàm `_split` tiếp tục gọi đệ quy với separator nhỏ hơn như dòng, câu hoặc khoảng trắng.

Base case xảy ra khi độ dài văn bản đã nhỏ hơn hoặc bằng `chunk_size`. Nếu đã sử dụng hết separator nhưng văn bản vẫn còn quá dài, thuật toán thực hiện hard split theo số ký tự và có thể giữ lại phần overlap giữa hai chunk liên tiếp.

---

### Lớp `EmbeddingStore`

#### `add_documents` + `search` — Hướng tiếp cận

Trong `add_documents`, mỗi tài liệu hoặc chunk được chuyển thành vector thông qua embedding model. Store lưu đồng thời nội dung văn bản, vector embedding, metadata và mã định danh của tài liệu để có thể truy xuất hoặc quản lý về sau.

Trong `search`, câu truy vấn được chuyển thành query embedding. Sau đó, tôi chuẩn hóa các vector và tính cosine similarity giữa query embedding với từng document embedding. Các kết quả được sắp xếp theo score giảm dần và trả về `top_k` chunk có điểm cao nhất.

Công thức cosine similarity được sử dụng là:

```text
cosine_similarity(A, B) = (A · B) / (||A|| × ||B||)
```

Nếu embedding đã được chuẩn hóa về vector đơn vị, cosine similarity có thể được tính trực tiếp bằng tích vô hướng:

```text
similarity = A · B
```

#### `search_with_filter` + `delete_document` — Hướng tiếp cận

Trong `search_with_filter`, tôi lọc các tài liệu dựa trên metadata trước khi xếp hạng kết quả. Ví dụ, hệ thống có thể chỉ giữ lại các chunk có `course_id`, `document_type` hoặc `source` phù hợp, sau đó mới tính hoặc lựa chọn các score cao nhất trong tập đã lọc. Cách này giúp tránh trả về tài liệu không thuộc phạm vi người dùng yêu cầu.

Trong `delete_document`, tôi xác định tất cả chunk có cùng `document_id`, sau đó xóa đồng bộ nội dung, embedding và metadata tương ứng. Việc xóa toàn bộ chunk theo `document_id` giúp bảo đảm không còn phần dữ liệu cũ của tài liệu tồn tại trong vector store.

---

### Tác tử `KnowledgeBaseAgent`

#### `answer` — Hướng tiếp cận

Trong hàm `answer`, tôi xây dựng prompt gồm ba thành phần chính: hướng dẫn vai trò của agent, các chunk ngữ cảnh được truy xuất từ vector store và câu hỏi của người dùng. Các chunk được đánh số hoặc ghi kèm nguồn để mô hình có thể phân biệt từng đoạn và dựa vào đúng nội dung liên quan.

Ví dụ cấu trúc prompt:

```text
Bạn là trợ lý hỏi đáp dựa trên cơ sở tri thức.

Chỉ sử dụng thông tin trong phần NGỮ CẢNH để trả lời.
Nếu ngữ cảnh không chứa đủ thông tin, hãy nói rõ rằng chưa đủ dữ liệu.
Không tự tạo thông tin không xuất hiện trong ngữ cảnh.

NGỮ CẢNH:
[1] Nội dung chunk thứ nhất...
[2] Nội dung chunk thứ hai...
[3] Nội dung chunk thứ ba...

CÂU HỎI:
Câu hỏi của người dùng...

TRẢ LỜI:
```

Ngữ cảnh được inject bằng cách nối các chunk top-k vào prompt trước khi gọi mô hình ngôn ngữ. Tôi yêu cầu agent không suy đoán ngoài dữ liệu và phải thông báo rõ khi thông tin truy xuất chưa đủ để trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết quả kiểm thử — Test Results

Lệnh được sử dụng:

```bash
pytest tests/ -v
```

Kết quả chạy thực tế ngày 03/08/2026 trên Python 3.11.4:

```text
platform win32 -- Python 3.11.4, pytest-9.1.1
collected 48 items
tests/test_solution.py ................................................ [100%]
============================= 48 passed in 0.31s ==============================
```

Toàn bộ các nhóm kiểm thử đều đạt: cấu trúc project, các chunker (fixed-size,
sentence, recursive, semantic, agentic, parent-child), cosine similarity,
EmbeddingStore (add/search/filter/delete), KnowledgeBaseAgent và comparator.

**Số lượng bài test vượt qua: 48 / 48.**


---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Tôi lựa chọn năm cặp câu có mức độ tương đồng khác nhau để kiểm tra khả năng biểu diễn ngữ nghĩa của embedding model.

| Cặp | Câu A                                                   | Câu B                                                                 | Dự đoán       |       Điểm thực tế | Đúng?        |
| --- | ------------------------------------------------------- | --------------------------------------------------------------------- | ------------- | -----------------: | ------------ |
| 1   | Sinh viên phải đăng ký môn học trước thời hạn.          | Học viên cần hoàn thành đăng ký học phần trước ngày hết hạn.          | Cao           | -0,1158 | Không |
| 2   | Hệ thống sử dụng vector embedding để tìm kiếm tài liệu. | Công cụ chuyển văn bản thành vector để thực hiện truy xuất ngữ nghĩa. | Cao           | 0,0164  | Không |
| 3   | Hôm nay trời mưa rất lớn.                               | Cách tính cosine similarity giữa hai vector.                          | Thấp          | -0,0778 | Có    |
| 4   | Tôi không thích môn học này.                            | Tôi thích môn học này.                                                | Tương đối cao | 0,1253 | Không |
| 5   | Python là một ngôn ngữ lập trình phổ biến.              | Java được sử dụng để phát triển nhiều hệ thống phần mềm.              | Trung bình    | 0,0755 | Không |

Các số liệu trên được chạy bằng `_mock_embed` có sẵn trong project, sau đó tính
cosine similarity đúng theo công thức trong phần mã bên dưới. Vì mock embedder
sinh vector xác định theo chuỗi, các điểm số này chỉ dùng để kiểm chứng luồng
tính toán, không phải phép đo chất lượng ngữ nghĩa.

Để lấy điểm thực tế, có thể sử dụng đoạn mã tương tự sau và thay tên embedding model theo project:

```python
import numpy as np


def cosine_similarity(vector_a: np.ndarray, vector_b: np.ndarray) -> float:
    denominator = np.linalg.norm(vector_a) * np.linalg.norm(vector_b)

    if denominator == 0:
        return 0.0

    return float(np.dot(vector_a, vector_b) / denominator)


sentence_pairs = [
    (
        "Sinh viên phải đăng ký môn học trước thời hạn.",
        "Học viên cần hoàn thành đăng ký học phần trước ngày hết hạn.",
    ),
    (
        "Hệ thống sử dụng vector embedding để tìm kiếm tài liệu.",
        "Công cụ chuyển văn bản thành vector để thực hiện truy xuất ngữ nghĩa.",
    ),
    (
        "Hôm nay trời mưa rất lớn.",
        "Cách tính cosine similarity giữa hai vector.",
    ),
    (
        "Tôi không thích môn học này.",
        "Tôi thích môn học này.",
    ),
    (
        "Python là một ngôn ngữ lập trình phổ biến.",
        "Java được sử dụng để phát triển nhiều hệ thống phần mềm.",
    ),
]

for index, (sentence_a, sentence_b) in enumerate(sentence_pairs, start=1):
    embedding_a = embedding_model.embed(sentence_a)
    embedding_b = embedding_model.embed(sentence_b)

    score = cosine_similarity(
        np.asarray(embedding_a),
        np.asarray(embedding_b),
    )

    print(f"Pair {index}: {score:.4f}")
```

#### Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?

Kết quả bất ngờ nhất là cặp 1: hai câu có nghĩa gần như tương đương nhưng điểm
mock lại là `-0,1158`. Kết quả này xác nhận cảnh báo của lab: `_mock_embed`
không biểu diễn ngữ nghĩa và không nên dùng để đánh giá chất lượng retrieval.
Khi đánh giá chính thức, cần dùng `EMBEDDING_PROVIDER=local` hoặc backend thật;
khi đó cặp 1 được kỳ vọng có điểm cao hơn hẳn cặp 3.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Tôi chạy năm câu hỏi chính thức trong `data/k4_ecommerce/benchmark_queries.json`
trên corpus 130 chunks, dùng `FixedSizeChunker(chunk_size=400, overlap=50)` và
`_mock_embed`. Riêng câu 3 có áp dụng filter `customer_role=seller` theo dữ liệu
benchmark. Cột “đúng tài liệu trong top-3” được đối chiếu với `document_id` đã
được quy định trong benchmark.

| # | Câu hỏi (Query) | Top-1 thực tế | Score | Top-1 liên quan? | Đúng tài liệu trong top-3? | Kết quả Agent |
| -: | --- | --- | ---: | --- | --- | --- |
| 1 | Tiki phản hồi khiếu nại của Nhà Bán trong bao lâu? | `tiki-noi-dung-mo-ta-san-pham`; đoạn về các lỗi nội dung mô tả. | 0,3749 | Không | Không | `demo_llm` chỉ trả preview của prompt, nên không đánh giá là câu trả lời có căn cứ. |
| 2 | Giá sản phẩm không khuyến mãi có được thấp hơn 1.000 đồng không? | `tiki-quy-dinh-gia-san-pham`; hướng dẫn cập nhật hàng loạt giá. | 0,3011 | Có (đúng tài liệu) | Có | Có đủ ngữ cảnh từ tài liệu giá, nhưng demo LLM không sinh câu trả lời nghiệp vụ hoàn chỉnh. |
| 3 | Nhà Bán tạo kho trả hàng như thế nào? | `tiki-quy-dinh-gia-san-pham`; đoạn về giá khuyến mãi. | 0,3072 | Không | Không | Không dùng để kết luận chất lượng generation vì retrieved context sai. |
| 4 | Liệt kê 5 từ/cụm từ bị cấm cho ngành Làm đẹp – Sức khỏe/Mẹ và bé/Bách Hóa Online. | `tiki-doi-tra-bao-hanh`; đoạn về đóng gói hàng đổi trả. | 0,3207 | Không | Không | Không dùng để kết luận chất lượng generation vì retrieved context sai. |
| 5 | Sản phẩm hoàn trả có vấn đề thì Nhà Bán phải làm gì? | `tiki-tieu-chuan-san-pham`; đoạn về tiêu chuẩn sản phẩm. | 0,2715 | Không | Không | Không dùng để kết luận chất lượng generation vì retrieved context sai. |

`KnowledgeBaseAgent` được kiểm thử trong unit test và trả về chuỗi không rỗng,
nhưng demo hiện dùng `demo_llm`, một hàm chỉ hiển thị preview prompt. Vì vậy tôi
không gán cho agent các câu trả lời nghiệp vụ mà nó chưa thật sự sinh ra. Đây là
ranh giới rõ ràng giữa kiểm thử pipeline và đánh giá generation bằng LLM thật.

**Số câu hỏi có đúng tài liệu trong top-3: 1 / 5.**

Kết quả thấp này là kết quả chạy thật với mock embedder, không phải lỗi che giấu.
Nó cho thấy benchmark ngữ nghĩa cần dùng local multilingual embedder trước khi
đưa ra kết luận về chiến lược chunking. Câu 2 truy xuất đúng tài liệu; bốn câu
còn lại không đúng tài liệu kỳ vọng trong top-3.

#### Điều hay nhất tôi học được từ thành viên khác hoặc nhóm khác qua demo

Điều hay nhất tôi học được là chất lượng của hệ thống RAG không chỉ phụ thuộc vào embedding model mà còn phụ thuộc rất nhiều vào cách chia chunk, overlap, metadata và cách xây dựng bộ câu hỏi đánh giá. Một chiến lược chunking phù hợp có thể cải thiện kết quả truy xuất đáng kể mà không cần thay đổi sang một mô hình embedding lớn hơn.

Tôi cũng học được rằng cần đánh giá riêng retrieval và generation. Nếu agent trả lời sai, nguyên nhân có thể đến từ việc vector store truy xuất sai chunk hoặc từ việc mô hình ngôn ngữ không sử dụng đúng ngữ cảnh, vì vậy hai giai đoạn cần được kiểm tra độc lập.

---

## Tự đánh giá (Phần Cá Nhân)

| Tiêu chí                                        |           Điểm tự đánh giá |
| ----------------------------------------------- | -------------------------: |
| Khởi động (Warm-up)                             |                      5 / 5 |
| Hướng tiếp cận của tôi (My Approach)            |                    10 / 10 |
| Hoàn thiện code (Core Implementation — tests)   | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions)    | 1 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 2 / 10 |
| **Tổng phần cá nhân**                           | **48 / 60** |

### Công thức tự tính điểm phần test

Nếu điểm phần implementation được tính tỷ lệ theo số bài test vượt qua:

```text
Điểm test = số test pass / tổng số test × 30
```

Ví dụ:

```text
48 test pass: 48 / 48 × 30 = 30 điểm
```

### Kết luận cá nhân

Qua Lab 7, tôi hiểu rõ hơn toàn bộ quy trình xây dựng một hệ thống hỏi đáp dựa trên cơ sở tri thức, từ chia nhỏ tài liệu, sinh embedding, lưu trữ vector, tính cosine similarity, truy xuất top-k đến đưa retrieved context vào prompt của agent. Tôi nhận thấy rằng mỗi thành phần đều ảnh hưởng trực tiếp đến chất lượng cuối cùng và cần được kiểm thử riêng thay vì chỉ đánh giá dựa trên câu trả lời cuối của agent.
