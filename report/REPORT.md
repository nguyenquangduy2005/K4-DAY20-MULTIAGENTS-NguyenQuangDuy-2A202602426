# Báo cáo Lab Multi-Agent / Self-Evolving Agent

## 1. Thông tin sinh viên và cấu hình

- Họ và tên: Nguyễn Quang Duy
- MSSV: 2A202602426
- Môi trường thực thi: WSL Ubuntu
- Python: 3.14.4
- deepagents: 0.7.21
- langchain-openai: 1.6.7
- langchain: 1.4.3
- Model: `openai:gpt-4.1-mini`
- Temperature: `0`
- Recursion limit: sử dụng cấu hình mặc định của lab

Các kết quả trong báo cáo được lấy từ các run thực tế lưu trong thư mục `results/`.

---

## 2. Giả thuyết trước freeze

- H1: Subagents được dự đoán không vượt baseline trên tập evaluation. Trên learning tasks, baseline đạt 12/18 technical checks trong khi subagents chỉ đạt 7/18; subagents chỉ thực sự delegate ở 2/3 tác vụ, nên việc thêm subagent chưa cho thấy cải thiện độ chính xác.

- H2: Skills-auto được dự đoán không cải thiện đáng kể so với baseline trên tập evaluation nếu agent tiếp tục không đọc skill. Trên learning tasks, baseline và skills-auto đều đạt 12/18 technical checks và 0/9 house-rule checks, trong khi skills_read của skills-auto là 0/3.

- H3: Kết quả trên evaluation có thể khác learning vì dữ liệu và quy ước mới, nhưng baseline và skills-auto được dự đoán vẫn gần nhau nếu skills_read tiếp tục bằng 0. Các skill do curator sinh từ lỗi learning chỉ có thể transfer sang evaluation khi agent thực sự đọc và áp dụng chúng.

---

## 3. Làm quen với Deep Agents

Qua bước làm quen với framework, tôi xác định agent mặc định được cung cấp các công cụ để tương tác với workspace và thực thi công việc. Trong đó, công cụ shell/execute được sử dụng để chạy các lệnh thực tế trong môi trường làm việc.

Công cụ `task` cho phép main agent giao một nhiệm vụ cho subagent. Việc delegation giúp tách một phần công việc khỏi luồng chính và có thể giảm lượng context mà main agent phải tự xử lý. Tuy nhiên, main agent vẫn cần cung cấp đủ context cho subagent và kiểm chứng kết quả trả về.

Một điểm quan trọng trong mô tả hành vi của agent là agent phải thực sự thực hiện công việc thay vì chỉ mô tả cách làm. Tương tự, khi sử dụng công cụ execute, agent cần dựa vào kết quả thực thi thực tế để kiểm tra trạng thái của workspace trước khi tuyên bố hoàn thành.

---

## 4. Baseline và phân loại lỗi

### 4.1. Kết quả baseline trên learning tasks

| Task | Score | Checks | Tokens | Tool calls |
|---|---:|---:|---:|---:|
| code-learn | 0.600 | 6/10 | 38,802 | 12 |
| data-learn | 0.625 | 5/8 | 87,589 | 14 |
| logs-learn | 0.111 | 1/9 | 24,985 | 4 |

Tổng token của baseline learning:

`38,802 + 87,589 + 24,985 = 151,376`

Trung bình:

`50,458.67 tokens/task`

Theo `check_breakdown.py`:

- Technical checks: **12/18**
- House-rule checks: **0/9**

Baseline vì vậy vượt qua 12/27 checks tổng cộng, nhưng cần phân biệt rõ rằng 12/18 là technical checks còn 0/9 là house-rule checks.

### 4.2. Error taxonomy

Các nhóm lỗi được sử dụng:

- A: Bỏ qua đặc tả
- B: Không kiểm chứng
- C: Vá triệu chứng
- D: Bỏ sót dữ liệu bẩn/định dạng
- E: Vi phạm quy ước tổ chức
- F: Báo cáo hoàn thành sai sự thật
- G: Khác

### 4.3. Phân tích lỗi baseline

#### code-learn

Các check thất bại:

- `tests_not_modified` — E
- `rule_type_hints` — E
- `rule_regression_tests` — E
- `rule_changelog` — E

Agent hoàn thành phần chức năng chính tương đối tốt nhưng không tuân thủ đầy đủ các quy ước tổ chức của repository.

#### data-learn

Các check thất bại:

- `rule_money_in_cents` — E
- `rule_meta_block` — E
- `rule_clean_csv` — E

Agent xử lý được phần lớn yêu cầu kỹ thuật nhưng bỏ sót các quy tắc về biểu diễn dữ liệu và output artifact.

#### logs-learn

Các lỗi kỹ thuật liên quan đến:

- số lượng entry
- chuẩn hóa timestamp UTC
- trường exception
- repeat count
- thống kê theo service

Các lỗi này được xếp chủ yếu vào nhóm D vì agent chưa xử lý đầy đủ dữ liệu log và các trường hợp định dạng.

Các lỗi house-rule gồm:

- `rule_service_names` — E
- `rule_sorted_errors` — E
- `rule_schema_header` — E

`logs-learn` là task yếu nhất của baseline, chỉ đạt 1/9 checks.

### 4.4. Nhận xét baseline

Baseline có khả năng giải quyết một phần đáng kể các yêu cầu kỹ thuật nhưng đặc biệt yếu ở house rules.

Kết quả `12/18` technical nhưng `0/9` house rules cho thấy vấn đề không chỉ nằm ở khả năng viết code mà còn ở việc phát hiện và tuân thủ các quy ước riêng của repository.

---

## 5. Thử nghiệm với subagents

### 5.1. Thiết kế subagents

Tôi triển khai ba subagent:

- `explorer`: khảo sát workspace, yêu cầu và cấu trúc hiện có.
- `implementer`: thực hiện thay đổi cần thiết.
- `reviewer`: kiểm tra kết quả và tìm các vấn đề còn thiếu.

Mục tiêu của thiết kế là tách quá trình khám phá, triển khai và kiểm tra thành các vai trò chuyên biệt.

### 5.2. Kết quả subagents trên learning tasks

| Task | Score | Checks | Tokens | Tool calls | Subagent calls |
|---|---:|---:|---:|---:|---:|
| code-learn | 0.600 | 6/10 | 49,437 | 13 | 0 |
| data-learn | 0.125 | 1/8 | 48,579 | 2 | 1 |
| logs-learn | 0.000 | 0/9 | 20,023 | 2 | 1 |

Tổng token:

`49,437 + 48,579 + 20,023 = 118,039`

Trung bình:

`39,346.33 tokens/task`

Theo `check_breakdown.py`:

- Technical checks: **7/18**
- House-rule checks: **0/9**

### 5.3. So sánh với baseline

Baseline:

- Technical: 12/18
- House rules: 0/9
- Mean tokens: 50,458.67

Subagents:

- Technical: 7/18
- House rules: 0/9
- Mean tokens: 39,346.33

Subagents sử dụng ít token hơn khoảng 22% so với baseline, nhưng số technical checks vượt qua giảm từ 12 xuống 7.

Điều này cho thấy việc bổ sung subagent không tự động làm chất lượng tốt hơn.

### 5.4. Hành vi delegation

Ở `code-learn`, `subagent_calls = 0`, nghĩa là agent không delegate dù các subagent đã được cung cấp.

Ở `data-learn` và `logs-learn`, mỗi task có một lần gọi subagent.

Như vậy delegation chỉ thực sự xảy ra ở 2/3 learning tasks.

Kết quả cho thấy thiết kế subagent tồn tại nhưng main agent chưa khai thác nó một cách ổn định. Việc có subagent không đảm bảo agent sẽ sử dụng subagent đúng thời điểm hoặc kiểm chứng đầy đủ kết quả của subagent.

---

## 6. Self-evolving skills

### 6.1. Curator

Curator được triển khai để đọc evidence từ baseline learning runs và sử dụng các lỗi quan sát được để tạo skill tự động.

Curator tạo ba skill:

1. `preserve-original-test-files`
2. `enforce-type-annotations-on-public-functions`
3. `normalize-and-validate-data-before-analysis`

Các skill được sinh tự động bởi curator và không được chỉnh sửa thủ công sau khi sinh.

### 6.2. Ý nghĩa của các skill

#### preserve-original-test-files

Skill nhắc agent không chỉnh sửa test có sẵn và kiểm tra rằng các test gốc vẫn được giữ nguyên.

Skill này liên quan trực tiếp đến lỗi `tests_not_modified` trong `code-learn`.

#### enforce-type-annotations-on-public-functions

Skill yêu cầu kiểm tra các public function và bổ sung đầy đủ type annotation.

Skill này phản ánh lỗi `rule_type_hints`.

#### normalize-and-validate-data-before-analysis

Skill tập trung vào:

- chuẩn hóa categorical data
- parse timestamp
- chuẩn hóa UTC
- biểu diễn tiền bằng integer cents
- deduplicate
- validate schema

Skill này tổng quát hóa một số lỗi quan sát được trong data và log processing.

### 6.3. Kết quả skills-auto trên learning tasks

| Task | Score | Checks | Tokens | Tool calls | Skills read |
|---|---:|---:|---:|---:|---:|
| code-learn | 0.600 | 6/10 | 89,514 | 19 | 0 |
| data-learn | 0.625 | 5/8 | 49,406 | 8 | 0 |
| logs-learn | 0.111 | 1/9 | 27,957 | 4 | 0 |

Tổng token:

`89,514 + 49,406 + 27,957 = 166,877`

Trung bình:

`55,625.67 tokens/task`

Theo `check_breakdown.py`:

- Technical checks: **12/18**
- House-rule checks: **0/9**
- Runs đọc skill: **0/3**

### 6.4. Phân tích

Điểm của skills-auto trên learning tasks giống baseline:

- Baseline: 12/18 technical, 0/9 house rules
- Skills-auto: 12/18 technical, 0/9 house rules

Tuy nhiên skills-auto sử dụng trung bình nhiều token hơn baseline.

Quan trọng nhất là `skills_read = 0/3`.

Vì agent không thực sự đọc các skill được curator tạo ra, các run này chưa cung cấp bằng chứng rằng nội dung skill đã tác động đến hành vi của agent.

Do đó không thể kết luận rằng skill không hữu ích chỉ dựa trên điểm số. Kết luận chính xác hơn là cơ chế hiện tại chưa khiến agent sử dụng các skill trong ba learning runs đã quan sát.

---

## 7. So sánh tổng hợp

### 7.1. Learning tasks

| Condition | Technical | House rules | Mean tokens |
|---|---:|---:|---:|
| baseline | 12/18 | 0/9 | 50,458.67 |
| subagents | 7/18 | 0/9 | 39,346.33 |
| skills-auto | 12/18 | 0/9 | 55,625.67 |

Tổng token của 9 learning runs:

`151,376 + 118,039 + 166,877 = 436,292`

Trong ba condition, baseline và skills-auto đạt cùng số technical checks. Subagents sử dụng ít token nhất nhưng cũng đạt ít technical checks nhất.

Không condition nào vượt qua house-rule check trong learning tasks.

### 7.2. Evaluation

Tại thời điểm hoàn thiện báo cáo này, evaluation runs chưa được thực hiện đầy đủ do giới hạn billing/API.

Vì vậy báo cáo không tạo hoặc suy đoán số liệu evaluation.

Các giả thuyết H1-H3 ở mục 2 được giữ nguyên như các dự đoán trước evaluation.

---

## 8. Phân tích

### 8.1. Subagents có giúp cải thiện chất lượng không?

Không có bằng chứng từ learning runs cho thấy subagents cải thiện chất lượng.

Baseline đạt 12/18 technical checks trong khi subagents đạt 7/18.

Tuy nhiên subagents sử dụng ít token hơn, nên có dấu hiệu về trade-off giữa chi phí và chất lượng trong các run quan sát được.

### 8.2. Main agent có sử dụng subagents ổn định không?

Không.

Agent chỉ delegate ở 2/3 learning tasks và không delegate ở `code-learn`.

Điều này cho thấy chỉ khai báo subagent chưa đủ; hành vi của main agent quyết định subagent có thực sự được sử dụng hay không.

### 8.3. Curator đã học được gì từ baseline?

Curator tạo các skill tập trung vào những lỗi có thật trong learning evidence, gồm:

- bảo vệ test gốc
- type annotations
- data normalization và validation

Các skill không đơn thuần ghi nhớ output của một task mà cố gắng diễn đạt các quy tắc tổng quát có thể tái sử dụng.

### 8.4. Skills-auto có cải thiện learning performance không?

Không quan sát được cải thiện về số checks:

- baseline: 12/18 technical
- skills-auto: 12/18 technical

Skills-auto cũng sử dụng nhiều token hơn trong các run đã thực hiện.

Tuy nhiên `skills_read = 0/3`, vì vậy chưa thể đánh giá trực tiếp hiệu quả của nội dung các skill.

### 8.5. House rules cho thấy điều gì?

Cả ba condition đều đạt 0/9 house-rule checks trên learning tasks.

Đây là dấu hiệu cho thấy house rules là điểm yếu chung của agent.

Agent có thể giải quyết chức năng chính nhưng vẫn thất bại nếu không chủ động tìm và tuân thủ các quy ước riêng của repository.

### 8.6. Có thể kết luận gì về khả năng transfer sang evaluation?

Chưa thể đưa ra kết luận thực nghiệm vì evaluation chưa được hoàn thành.

H1-H3 chỉ là các giả thuyết được hình thành từ learning evidence.

Đặc biệt, khả năng transfer của skills-auto phụ thuộc vào việc agent có thực sự đọc và áp dụng skill trong task mới hay không.

---

## 9. Hạn chế

Thí nghiệm có ít nhất các hạn chế sau:

1. Số lượng task nhỏ nên khó khái quát hóa kết quả.

2. Main agent không sử dụng subagents một cách ổn định; `code-learn` có `subagent_calls = 0`.

3. Skills-auto không đọc skill trong cả ba learning runs (`skills_read = 0/3`), nên chưa đo được tác động thực tế của nội dung skill.

4. Evaluation chưa được hoàn thành do giới hạn billing/API, vì vậy không có đủ dữ liệu để kiểm chứng H1-H3 trên tập evaluation.

5. Chi phí token thay đổi đáng kể giữa các task và condition, đặc biệt `data-learn` của baseline và `code-learn` của skills-auto.

---

## 10. Kết luận

1. Baseline đạt 12/18 technical checks nhưng 0/9 house-rule checks trên learning tasks.

2. Subagents giảm lượng token trung bình nhưng cũng giảm số technical checks xuống 7/18.

3. Curator tạo được ba skill tổng quát từ learning evidence, nhưng agent không đọc skill trong các skills-auto learning runs.

4. House rules là điểm yếu chung của cả ba condition trong learning phase.

5. Do evaluation chưa được hoàn thành, H1-H3 vẫn là giả thuyết và không được trình bày như kết luận thực nghiệm.

---

## Phụ lục

### Learning results

Baseline:

- `code-learn`: 6/10, 38,802 tokens
- `data-learn`: 5/8, 87,589 tokens
- `logs-learn`: 1/9, 24,985 tokens

Subagents:

- `code-learn`: 6/10, 49,437 tokens
- `data-learn`: 1/8, 48,579 tokens
- `logs-learn`: 0/9, 20,023 tokens

Skills-auto:

- `code-learn`: 6/10, 89,514 tokens
- `data-learn`: 5/8, 49,406 tokens
- `logs-learn`: 1/9, 27,957 tokens

### Tổng hợp token

- Baseline: 151,376
- Subagents: 118,039
- Skills-auto: 166,877
- Tổng cộng: 436,292

### Offline tests

Bộ test offline đã chạy thành công:

`32 passed`

Bao gồm:

- `test_01_provided.py`
- `test_02_agent.py`
- `test_03_runner.py`
- `test_04_curator.py`