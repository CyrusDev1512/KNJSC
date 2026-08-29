# Backlog

Nơi ghi lại mọi phát hiện, ý tưởng và câu hỏi chưa được quyết định.

> **Quy tắc:** phát hiện gì thì ghi vào đây trước, **không sửa tài liệu ngay**.
> Chỉ cập nhật tài liệu sau khi đã quyết định thực hiện.
>
> Phát hiện được ghi lại không có nghĩa là sẽ làm. Có thứ đáng làm, có thứ để sau,
> có thứ không bao giờ làm.

---

## Cách đọc

| Cột | Nghĩa |
|---|---|
| Mức | Chặn · Cao · Trung bình · Thấp |
| Trạng thái | Chờ quyết định · Đã duyệt · Từ chối · Đã làm |
| Nguồn | Ai hoặc cái gì phát hiện ra |

**Mức Chặn** nghĩa là không làm thì không triển khai được.

---

## 0. Còn nợ những gì — xem ở đây trước

Một chỗ duy nhất liệt kê **mọi thứ chưa xong**, cả việc của người dùng lẫn việc
của người viết mã. Chi tiết từng mục nằm ở các phần bên dưới; phần này là bản
tóm để không phải lục.

> Cập nhật ngày 29.08.2026, sau khi xong Giai đoạn 5 và lập kế hoạch kiểm thử.

### A · Nghiệm thu — việc của anh/chị

**Chưa có gì được nghiệm thu.** Giai đoạn 0 tới 5 đều đã giao và 779 bài kiểm
thử tự động đều đạt, nhưng anh/chị **chưa trực tiếp thử màn hình nào**. Phần
trăm trên `dashboard-tien-do.html` là tiến độ *đã làm*, không phải *đã nghiệm thu*.

**Sáu việc làm được ngay bây giờ:**

| ☐ | Việc | Mã |
|---|---|---|
| ☐ | Thêm team mới, dùng ngay không khởi động lại | `AC-2.4` |
| ☐ | Mở trên điện thoại và máy tính bảng thật | `AC-10.4` |
| ☐ | Cài từ đầu trên máy sạch, chạy tới màn hình đăng nhập | `docs/04` mục 11.1 |
| ☐ | Ba vai trò đăng nhập, chạy trọn quy trình của mình | `docs/04` mục 11.2 |
| ☐ | Thử trên điện thoại và máy tính bảng thật | `docs/04` mục 11.5 |
| ☐ | Ngắt mạng giữa chừng, kiểm thông báo lỗi | `docs/04` mục 11.7 |

**Tám việc chưa làm được, và vì sao:**

| Việc | Mã | Chờ |
|---|---|---|
| Đăng nhập vào thẳng màn hình của bộ phận mình | `AC-1.7` | Tính năng chưa làm — **K18** |
| Xuất báo cáo, mở bằng Excel, đối chiếu số | `AC-5.6` · mục 11.4 | Giai đoạn 6 và 7 |
| 50 người thao tác đồng thời | `AC-10.1` | Chưa chọn công cụ đo — **K6** |
| Gặp lỗi hiện thông báo tiếng Việt, không trang trắng | `AC-10.3` | Trang 404 và 500 chưa làm — **K9** |
| Phục hồi từ bản sao lưu | `AC-10.5` · mục 11.6 | Giai đoạn 8 |
| Nhập tệp Excel thật của công ty | mục 11.3 | Giai đoạn 7 |

### B · Câu hỏi chờ anh/chị quyết

Sáu câu này **chặn việc thật**, không phải bàn cho vui:

| # | Câu hỏi | Chặn gì |
|---|---|---|
| **V4** | Mốc nào thì nghiệm thu toàn diện | Cả mục A ở trên |
| **V2** | Ai vận hành hằng ngày sau bàn giao | **K17** — có nên dựng chạy kiểm thử tự động không |
| **V1** | Máy chủ đặt ở đâu | Giai đoạn 8 |
| **N1** | Nộp báo cáo có bắt buộc đúng giờ không | **K16** — cột Trạng thái trên Lịch sử báo cáo |
| **N3** · **N6** | Chăm sóc khách hàng có trong phase 1 không | Biểu mẫu báo cáo CSKH ở Giai đoạn 4 |
| **N7** | Quản trị viên có phải thuộc một bộ phận không | BR-1 đang mâu thuẫn với mã |

Còn sáu câu **H1 tới H6** cần hỏi trực tiếp người dùng cuối, không phải anh/chị
trả lời thay — xem mục 5.

### C · Lỗ hổng kỹ thuật đã biết

Không cái nào chặn triển khai. Xếp theo mức.

| # | Nội dung | Mức |
|---|---|---|
| **K18** | Điều hướng sau đăng nhập theo bộ phận — FR-1.6, nay đã đủ màn hình đích để làm | Trung bình |
| **K9** | Chưa có trang lỗi 404 và 500 tiếng Việt | Trung bình |
| **K7** | Khoảng 60 định danh tiếng Việt trong mã Python, trái quy ước `CLAUDE.md` | Trung bình |
| **K13** | Cấp quyền đi hai cơ chế song song, xem lại có gộp được không | Trung bình |
| **K16** | Cột Trạng thái trên Lịch sử báo cáo — chờ **N1** | Trung bình |
| **K17** | Chưa có gì chạy kiểm thử tự động khi đẩy mã — chờ **V2** | Trung bình |
| **K6** | Chưa chọn công cụ đo tải | Thấp |
| **K8** | `ScopedModel` chưa có cột "người sửa" | Thấp |
| **K10** | Quy tắc Q3 chưa áp ở màn hình nào | Thấp |
| **K14** | Nhánh Staff trong `apply_scope` không đọc phạm vi cấp thêm | Thấp |

### D · Tiêu chí nghiệm thu chưa có bài kiểm

12 tiêu chí đánh dấu *Tự động* nhưng chưa viết được, tất cả vì tính năng chưa
xây. Danh sách này nằm trong `app/tests/test_truy_vet.py`, biến `HOAN`, và
**có bài kiểm bắt phải ghi lý do** — không giấu được.

| Tiêu chí | Chờ |
|---|---|
| `AC-5.1` → `AC-5.5` | Báo cáo tổng hợp — Giai đoạn 6 |
| `AC-7.5` → `AC-7.9` | Nhập xuất Excel — Giai đoạn 7 |
| `AC-7.1` | 50.000 bản ghi dưới 2 giây, cần `seed_perf.py` — Giai đoạn 8 |
| `AC-10.6` | Sao lưu tự động — Giai đoạn 8 |

### E · Màn hình chưa có

Còn **2 trên 10** màn hình của bản dựng ở `prototype/`. Chi tiết ở mục 6.

| Màn hình | Giai đoạn |
|---|---|
| Báo cáo tổng hợp | 6 |
| Bảng tính | 7 |

---

## 1. Chờ quyết định

### 1.1. Kỹ thuật

| # | Nội dung | Mức | Nguồn |
|---|---|---|---|
| K6 | Công cụ đo hiệu năng khi kiểm 50 người dùng đồng thời | Thấp | Bàn tài liệu |
| K7 | Đổi khoảng 60 định danh tiếng Việt trong mã Python sang tiếng Anh theo quy ước CLAUDE.md, gồm cả tên ràng buộc `team_unique_trong_bo_phan` đã vào PostgreSQL | Trung bình | Rà soát GĐ 1–2 |
| K8 | `docs/03` mục 2.1 đòi mọi bảng có cột "người sửa"; `ScopedModel` mới có `created_by`, chưa có `updated_by` | Thấp | Rà soát GĐ 1–2 |
| K9 | Chưa có trang lỗi 404 và 500 bằng tiếng Việt — NFR-6 mới đạt một phần | Trung bình | Rà soát GĐ 1–2 |
| K10 | Quy tắc Q3 "chỉ lấy cột cần hiển thị" chưa áp ở màn hình nào | Thấp | Rà soát GĐ 1–2 |
| K13 | `core/scope.py _granted_scope` vẫn trả về rỗng. Cấp quyền theo bảng và biểu mẫu đi đường riêng ở `forms_builder/services/grant_service.py` — hai cơ chế song song, nên xem lại có gộp được không | Trung bình | GĐ 3B |
| K14 | Nhánh Staff trong `apply_scope` không đọc `department_ids` lẫn `team_ids`, nên cấp thêm cả một bộ phận cho Staff không có tác dụng | Thấp | GĐ 3B |
| K16 | Cột **Trạng thái** trên Lịch sử báo cáo (Đã nộp · Nộp muộn · Chưa nộp) chưa làm được vì chưa chốt **N1** — lịch nộp báo cáo có bắt buộc đúng giờ không. Không có hạn nộp thì không tính được thế nào là muộn | Trung bình | Đối chiếu 8010 |
| K17 | Chưa có gì chạy kiểm thử tự động khi đẩy mã lên kho. Người dùng chốt chưa dựng vì **V2** còn để ngỏ ai vận hành sau bàn giao | Trung bình | Kế hoạch kiểm thử |
| K18 | Điều hướng sau đăng nhập theo bộ phận — FR-1.6, `AC-1.7`. Hoãn từ Giai đoạn 2 vì chưa có màn hình đích; nay Giai đoạn 4 và 5 đã xong nên làm được | Trung bình | Rà soát Giai đoạn 5 |

### 1.2. Nghiệp vụ

| # | Nội dung | Mức | Nguồn |
|---|---|---|---|
| N1 | Lịch nộp báo cáo có bắt buộc đúng giờ không — chỉ ghi nhận, nhắc nhở, hay chặn nộp muộn | Trung bình | Bàn phạm vi |
| N2 | Nhân viên vận đơn có tự thêm cột vào bảng không | Thấp | Đã hỏi, trả lời là không |
| N3 | Vai trò Chăm sóc khách hàng có thuộc phase 1 không | Trung bình | Tệp vận đơn có cột CSKH, phase 1 chưa có vai trò này |
| N6 | Chăm sóc khách hàng có trong phase 1 không — `README.md` xếp vào phạm vi, `docs/02` mục 12 để ngỏ. Trùng với N3 nhưng nay có thêm chứng cứ vênh giữa hai tài liệu | Cao | Rà soát GĐ 1–2 |
| N7 | BR-1 nói mỗi người thuộc đúng một bộ phận, nhưng Admin hiện không thuộc bộ phận nào. Giữ nguyên hay bắt Admin cũng phải có bộ phận | Trung bình | Rà soát GĐ 1–2 |

### 1.3. Vận hành

| # | Nội dung | Mức | Nguồn |
|---|---|---|---|
| V1 | Máy chủ đặt ở đâu — thuê ngoài hay đặt tại văn phòng | Trung bình | Chưa chốt |
| V2 | Ai chịu trách nhiệm vận hành hằng ngày sau khi bàn giao | Cao | Chưa chốt |
| V3 | Kênh gửi thông báo nếu làm tính năng nhắc nộp báo cáo | Thấp | Phụ thuộc N1 |
| V4 | **Mốc nào thì nghiệm thu toàn diện.** Hiện quá ít màn hình để đánh giá được giao diện và trải nghiệm — người dùng không nghiệm thu từng phần nữa, dồn về một đợt. Đề xuất mốc: hết Giai đoạn 5, khi một bộ phận làm trọn được việc hằng ngày. Chờ người dùng chốt | Cao | Người dùng, 29.08.2026 |
| V5 | **Kế hoạch kiểm thử và nghiệm thu chưa lập.** Người dùng chốt để sau, làm cùng lúc với đợt nghiệm thu ở V4. Nội dung cần có: ai kiểm, kiểm trên dữ liệu nào, bao lâu, tiêu chí nào coi là đạt, và xử lý thế nào khi không đạt | Cao | Người dùng, 29.08.2026 |

---

## 2. Đã quyết định

| # | Nội dung | Quyết định | Ngày |
|---|---|---|---|
| Q1 | Đơn hàng chảy sang bảng vận đơn theo chiều nào | Một chiều cho phase 1 | (điền) |
| Q2 | Có làm quản lý tài nguyên và kho thông tin đăng nhập không | Không làm | (điền) |
| Q3 | Mảng nhân sự, kế toán, kho | Để giai đoạn sau | (điền) |
| Q4 | Có tích hợp với phần mềm kế toán không | Không, ít nhất trong phase 1 | (điền) |
| Q5 | Ứng dụng di động | Không làm bản cài đặt, chỉ cần giao diện dùng được trên điện thoại | (điền) |
| Q6 | Trợ lý AI | Không làm trong phase 1 | (điền) |
| Q7 | Khung ứng dụng | Django 5.2, PostgreSQL 16, HTMX, Celery với Redis, Docker Compose — ADR-005 | 28.08.2026 |
| Q8 | Danh sách module trong `app/` | Bảy module: core, org, forms_builder, reports, orders, dashboard, crm | 28.08.2026 |
| Q9 | Quản trị viên trong mô hình bộ phận × cấp bậc | Cấp bậc thứ tư tên Admin, phạm vi mọi bộ phận, có tất cả các quyền | 28.08.2026 |
| Q10 | Loại tiền tệ | Phase 1 dùng VND và USD, mỗi số tiền lưu kèm loại tiền, không quy đổi khi lưu | 28.08.2026 |
| Q11 | Mức độ công thức trên bảng — K1, FR-7.8 | Bảng dữ liệu chỉ có cột tính sẵn; gõ công thức tự do tách sang màn hình Bảng tính, không ghi ngược — ADR-006 | 29.08.2026 |
| Q12 | Bảng đích khi tạo biểu mẫu — K2 | Luôn chọn bảng có sẵn, không tự sinh bảng mới — ADR-007 | 29.08.2026 |
| Q13 | Bảy nhãn ý nghĩa — K3 và N8 | Theo `docs/03` mục 2.5: Ngày, Khách hàng, Số điện thoại, Doanh thu, Người bán, Sản phẩm, Trạng thái — ADR-007 | 29.08.2026 |
| Q14 | Chia Giai đoạn 3 làm mấy đợt | Hai đợt có điểm dừng: 3A bảng dữ liệu, 3B biểu mẫu và phân quyền theo bảng | 29.08.2026 |
| Q15 | Màn hình Bảng tính xếp vào giai đoạn nào | Giai đoạn 7, làm chung với nhập xuất Excel | 29.08.2026 |
| Q16 | Có làm màn hình Ma trận phân quyền không | Có, bản chỉ đọc sinh thẳng từ mã nguồn — làm trong 3A | 29.08.2026 |
| Q17 | Ai thấy định nghĩa bảng | Cả bộ phận, mọi cấp bậc. Phạm vi theo cấp bậc chỉ áp cho bản ghi trong bảng | 29.08.2026 |
| Q18 | Cấu trúc trường biểu mẫu | Bốn bảng đúng `docs/03` mục 2.2: FieldDef, FormDef, FormField, FormTableLink | 29.08.2026 |
| Q19 | Mức chi tiết của phân quyền — FR-8.4 | Cấp thêm cho từng người hoặc từng team, cộng vào phạm vi cấp bậc | 29.08.2026 |
| Q20 | K11 và K12 | Đã xong ở 3B: màn hình điền biểu mẫu, và quyền sửa ô tính qua `grant_service.can_edit_record` | 29.08.2026 |
| Q21 | Nội dung báo cáo hằng ngày lưu ở đâu | Trong `DataRecord` do biểu mẫu sinh ra; `DailyReport` chỉ giữ ai nộp, ngày nào, lúc nào — ADR-008 | 29.08.2026 |
| Q22 | Dựng vỏ hết màn hình trước hay làm từng giai đoạn | Làm từng giai đoạn, mỗi màn hình chạy thật rồi mới sang màn tiếp | 29.08.2026 |
| Q23 | Thị trường thật — N5 | Ba nước: Hoa Kỳ, Canada, Philippines. Ô chọn cố định, khai một chỗ trong `orders/constants.py` | 29.08.2026 |
| Q24 | Sáu trường không có trong bảng vận đơn — N4 | Thêm sáu cột vào bảng vận đơn. Vận đơn cần liên lạc được với khách khi giao hỏng | 29.08.2026 |
| Q25 | BLACK LIST — G1 | Cờ đánh dấu trên khách hàng kèm lý do. Lên đơn cho khách trong danh sách đen thì **cảnh báo, không chặn** — chưa có yêu cầu nào cho chặn | 29.08.2026 |
| Q26 | Trạng thái vận chuyển và thanh toán — G2 | Bộ phận Vận đơn sửa thẳng trên bảng, dùng lại chức năng sửa ô của Giai đoạn 3. Không viết màn hình riêng | 29.08.2026 |
| Q27 | Dòng trên bảng động thuộc bộ phận nào | Bộ phận **sở hữu bảng**, không phải bộ phận người ghi. Thêm cờ `is_shared` cho bảng là hàng đợi việc chung | 29.08.2026 |
| Q28 | Ô "Có chỉ mục" trong bản dựng — K15 | Bỏ. Chỉ mục suy ra từ nhãn ý nghĩa, không phải lựa chọn của người dùng — ADR-001 | 29.08.2026 |
| Q29 | Cột "Chỉ mục GIN" trên danh sách bảng | Bỏ. Mọi bảng động đều có chỉ mục GIN trên cột JSON, hiện lên không nói thêm được gì | 29.08.2026 |
| Q30 | Ngưỡng bao phủ kiểm thử — K5 | Đo bằng `pytest-cov` để biết chỗ hổng, **không đặt ngưỡng chặn**. Ngưỡng đẻ ra bài kiểm viết cho đủ số | 29.08.2026 |
| Q31 | Kiểm giao diện tự động tới đâu | Ở mức HTML, không thêm thư viện trình duyệt. Phần cần trình duyệt thật thì bấm tay | 29.08.2026 |
| Q32 | Ai vào được màn hình Lên đơn | Chỉ bộ phận Sale, theo ma trận kiểm chéo `docs/04` mục 3. Thêm bộ lọc bộ phận cho `NavItem` và `assert_departments` | 29.08.2026 |
| Q33 | Ai vào được màn hình Quản lý biểu mẫu | Manager trở lên. Nhân viên điền biểu mẫu qua màn hình Nộp báo cáo ngày | 29.08.2026 |

---

## 3. Ý tưởng cho giai đoạn sau

Những thứ đáng làm nhưng chưa tới lượt.

| # | Ý tưởng | Ghi chú |
|---|---|---|
| S1 | Đồng bộ hai chiều giữa đơn hàng và bảng vận đơn | Cần xử lý xung đột khi hai bên cùng sửa |
| S2 | Cho phép cấp trên chia sẻ quyền xem cho cấp dưới | Khung phạm vi đã thiết kế sẵn chỗ mở rộng |
| S3 | Thông báo chủ động khi có việc cần xử lý | Cần tầng dịch vụ tách khỏi giao diện |
| S4 | Kênh báo sự cố cho nhân viên không có tài khoản | Biểu mẫu công khai, người quản lý xử lý |
| S5 | Bảng tổng hợp dạng xoay chiều | Chưa rõ nhu cầu thật |
| S6 | Nhiều người cùng sửa một bảng theo thời gian thực | Phức tạp, cần đánh giá lại nhu cầu |

---

## 4. Rủi ro đã nhận diện

| # | Rủi ro | Mức ảnh hưởng | Cách giảm |
|---|---|---|---|
| R1 | Dữ liệu cũ dần vì phụ thuộc người dùng cập nhật | Cao | Nhắc nhở, và làm sao cho nhập liệu nhanh hơn cách hiện tại |
| R2 | Chỉ một người biết vận hành hệ thống | Cao | Sổ tay vận hành đủ chi tiết để người khác tiếp nhận |
| R3 | Phạm vi phình ra trong quá trình làm | Trung bình | Danh sách ngoài phạm vi trong tài liệu, thay đổi phải được duyệt |
| R4 | Bảng do người dùng tự tạo làm chậm truy vấn | Trung bình | Tách cột có nhãn ý nghĩa ra cột riêng có chỉ mục |
| R5 | Người dùng thấy hệ thống chậm hơn cách làm cũ nên không dùng | Cao | Đo thời gian thao tác thực tế, so với cách làm hiện tại |
| R6 | Bản sao lưu chưa từng được phục hồi thử | Cao | Thử phục hồi trước khi bàn giao |
| R7 | Nghiệm thu dồn về một đợt cuối nên sai về giao diện và trải nghiệm phát hiện muộn, lúc đó sửa đắt hơn | Cao | Bám sát bản dựng ở `prototype/` làm chuẩn giao diện; mỗi giai đoạn vẫn chạy thử tay và báo cáo, chỉ không đòi người dùng nghiệm thu |

---

## 5. Câu hỏi cần hỏi người dùng

Những câu chưa có đáp án, cần hỏi trực tiếp người sử dụng.

| # | Câu hỏi | Hỏi ai |
|---|---|---|
| H1 | Trong tệp Excel hiện tại, anh chị có gõ công thức không? Gõ những gì? | Vận đơn, Marketing |
| H2 | Anh chị có hay kéo góc ô để điền cả cột không? | Vận đơn, Marketing |
| H3 | Anh chị có dán dữ liệu từ tệp Excel khác vào không? | Vận đơn, Marketing |
| H4 | Mỗi ngày mất bao lâu cho việc nhập liệu và tổng hợp thủ công? | Cả ba bộ phận |
| H5 | Lần gần nhất cần tìm một thông tin mà tìm không ra là khi nào? | Cả ba bộ phận |
| H6 | Một bộ phận hiện có mấy team, ai phân team? | Quản lý |

---

## 6. Hiện trạng màn hình — chưa nghiệm thu

Người dùng nêu ngày 29.08.2026: **hiện quá thiếu màn hình để đánh giá được
giao diện và trải nghiệm.** Không nghiệm thu từng phần nữa; dồn về một đợt
kiểm thử toàn diện khi đủ màn hình. Mốc cụ thể xem **V4**, kế hoạch kiểm thử
xem **V5** — cả hai đều chưa chốt.

> **Chưa có gì được nghiệm thu.** Giai đoạn 0 tới 4 đều đã giao và đã chạy
> kiểm thử tự động, nhưng **người dùng chưa trực tiếp thử màn hình nào**. Mọi
> phần trăm trong `dashboard-tien-do.html` là tiến độ *đã làm*, không phải
> tiến độ *đã nghiệm thu*. Hai con số đó có thể lệch nhau, và chỉ đóng lại
> được sau đợt kiểm thử ở V4.

| Giai đoạn | Đã giao | Người dùng đã thử |
|---|---|---|
| 0 · Tài liệu và quyết định | ✓ | — |
| 1 · Nền móng | ✓ | Chưa |
| 2 · Cơ cấu tổ chức và giao diện chung | ✓ | Chưa |
| 3 · Biểu mẫu và bảng động | ✓ | Chưa |
| 4 · Báo cáo hằng ngày | ✓ | Chưa |

Bản dựng giao diện tĩnh ở `prototype/` là chuẩn để đối chiếu. Nó có 10 màn
hình mà bản Django chưa có; bảng dưới đây theo dõi việc lấp dần.

| Màn hình trong bản dựng | Giai đoạn | Trạng thái |
|---|---|---|
| Bảng vận đơn — bảng dữ liệu chung | 3A | Đã có, dưới tên `/bang/<mã>/` |
| Ma trận phân quyền | 3A | Đã có, bản chỉ đọc |
| Quản lý biểu mẫu | 3B | Đã có |
| Trình tạo biểu mẫu | 3B | Đã có |
| Nộp báo cáo ngày | 4 | Đã có |
| Lịch sử báo cáo | 4 | Đã có |
| Lên đơn | 5 | Đã có |
| Báo cáo tổng hợp | 6 | Chưa |
| Bảng tính | 7 | Chưa — Q15 |
| Bảng tính, màn hình chi tiết | 7 | Chưa — Q15 |

**Thiếu sót đã biết, không phải màn hình riêng nhưng ảnh hưởng trải nghiệm:**

| # | Nội dung | Giai đoạn xử lý |
|---|---|---|
| 1 | ~~Bảng động chưa có chỗ thêm dòng mới~~ — xong ở 3B, màn hình điền biểu mẫu | — |
| 2 | Chưa có trang lỗi 404 và 500 tiếng Việt — K9 | Chưa xếp |
| 3 | Giao diện chưa kiểm trên điện thoại và máy tính bảng — NFR-7, AC-10.4 | 8 |
| 4 | Điều hướng sau đăng nhập theo bộ phận — FR-1.6 | Chờ màn hình đích của 4 và 5 |
| 5 | Chưa có dữ liệu mẫu đủ lớn để thấy bảng chạy thật thế nào | 8, `seed_perf.py` |

**Khi tới đợt kiểm thử toàn diện, chạy theo `docs/04` mục 3 và mục 10:** ma
trận kiểm chéo chín vai trò, các tiêu chí thủ công `AC-8.1`, `AC-10.3`,
`AC-10.4`, `AC-5.6`, và đối chiếu từng màn hình với bản dựng ở `prototype/`.

---

## Nhật ký cập nhật

| Ngày | Nội dung |
|---|---|
| (điền) | Tạo tài liệu |
| 28.08.2026 | Rà soát Giai đoạn 1 và 2 — 19 phát hiện. Sửa 18, hoãn K7. Thêm K7–K10 và N5–N8 |
| 29.08.2026 | Chốt K1, K2, K3 và N8 — gỡ hết điểm chặn Giai đoạn 3. Ghi ADR-006 và ADR-007 |
| 29.08.2026 | Xong Giai đoạn 3 phần A. Chốt Q14 tới Q17. Thêm AC-3.8, AC-7.10 tới AC-7.12 vào `docs/04`. Mở K11 và K12 |
| 29.08.2026 | Người dùng nêu: quá thiếu màn hình để nghiệm thu. Hoãn nghiệm thu tới một đợt toàn diện — mở V4 và R7, thêm mục 6 theo dõi hiện trạng màn hình |
| 29.08.2026 | Xong Giai đoạn 4 — báo cáo hằng ngày. Chốt Q21 và Q22. Ghi ADR-008 |
| 29.08.2026 | Lập kế hoạch kiểm thử toàn diện — `docs/06`. Từ 249 lên **779 bài đạt**, bao phủ 83%. Thêm bốn tầng: tệp chuyển đổi, kiểm khói, ma trận 35 ô, truy vết. Tìm ra 4 lỗi phân quyền, 1 lỗi tiền, 3 lỗi giao diện. Chốt Q30 tới Q33, đóng K5 và K15, mở K17 |
| 29.08.2026 | Đối chiếu toàn bộ 8020 với 8010 theo từng trường. Bổ sung: cột Doanh số ở Lịch sử báo cáo, cột Người tạo và Cập nhật ở Quản lý biểu mẫu, Giá trị mặc định cho định nghĩa trường, cột tính sẵn hiện ngay trên biểu mẫu. Làm K15 thành bài kiểm thật. Chốt Q28 Q29, mở K16 |
| 29.08.2026 | Người dùng đối chiếu màn Lên đơn với bản dựng: thiếu cột Thành tiền, khối Tóm tắt, khối Sau khi lưu. Phát hiện thêm `.luoi-2cot` không tồn tại nên bốn màn hình hiện một cột, và ba lớp `.o-tinh` `.o-loi` `.o-trong-bang` chưa có kiểu dáng. Đã bổ sung hết, mở K15 |
| 29.08.2026 | Xong Giai đoạn 5 — lên đơn và vận đơn. Chốt thêm Q27 sau khi chạy thử tay phát hiện Vận đơn không thấy dòng nào |
| 29.08.2026 | Bàn Giai đoạn 5. Chốt Q23 tới Q26 — gỡ N4, N5, G1, G2 |
| 29.08.2026 | Người dùng xác nhận chưa thử màn hình nào, chưa nghiệm thu được. Kế hoạch kiểm thử cũng để sau — mở V5, ghi bảng đã giao / đã thử vào mục 6 |
| 29.08.2026 | Xong Giai đoạn 3 phần B, khép lại Giai đoạn 3. Chốt Q18 tới Q20, đóng K11 và K12, mở K13 và K14. Bỏ model `Position` khỏi tài liệu vì nó không tồn tại |
