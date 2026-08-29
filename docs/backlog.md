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

## 1. Chờ quyết định

### 1.1. Kỹ thuật

| # | Nội dung | Mức | Nguồn |
|---|---|---|---|
| K5 | Có nên đặt ngưỡng tỉ lệ bao phủ kiểm thử không | Thấp | Bàn tài liệu |
| K6 | Công cụ đo hiệu năng khi kiểm 50 người dùng đồng thời | Thấp | Bàn tài liệu |
| K7 | Đổi khoảng 60 định danh tiếng Việt trong mã Python sang tiếng Anh theo quy ước CLAUDE.md, gồm cả tên ràng buộc `team_unique_trong_bo_phan` đã vào PostgreSQL | Trung bình | Rà soát GĐ 1–2 |
| K8 | `docs/03` mục 2.1 đòi mọi bảng có cột "người sửa"; `ScopedModel` mới có `created_by`, chưa có `updated_by` | Thấp | Rà soát GĐ 1–2 |
| K9 | Chưa có trang lỗi 404 và 500 bằng tiếng Việt — NFR-6 mới đạt một phần | Trung bình | Rà soát GĐ 1–2 |
| K10 | Quy tắc Q3 "chỉ lấy cột cần hiển thị" chưa áp ở màn hình nào | Thấp | Rà soát GĐ 1–2 |
| K13 | `core/scope.py _granted_scope` vẫn trả về rỗng. Cấp quyền theo bảng và biểu mẫu đi đường riêng ở `forms_builder/services/grant_service.py` — hai cơ chế song song, nên xem lại có gộp được không | Trung bình | GĐ 3B |
| K14 | Nhánh Staff trong `apply_scope` không đọc `department_ids` lẫn `team_ids`, nên cấp thêm cả một bộ phận cho Staff không có tác dụng | Thấp | GĐ 3B |

### 1.2. Nghiệp vụ

| # | Nội dung | Mức | Nguồn |
|---|---|---|---|
| N1 | Lịch nộp báo cáo có bắt buộc đúng giờ không — chỉ ghi nhận, nhắc nhở, hay chặn nộp muộn | Trung bình | Bàn phạm vi |
| N2 | Nhân viên vận đơn có tự thêm cột vào bảng không | Thấp | Đã hỏi, trả lời là không |
| N3 | Vai trò Chăm sóc khách hàng có thuộc phase 1 không | Trung bình | Tệp vận đơn có cột CSKH, phase 1 chưa có vai trò này |
| N4 | Sáu trường trong biểu mẫu lên đơn không có trong bảng vận đơn — Facebook, Email, Quốc gia, Đơn vị phụ, Loại tiền tệ, Người bán | Trung bình | Đối chiếu biểu mẫu và tệp thật |
| N5 | Thị trường thật là những nước nào — `README.md` ghi Canada và Philippines, `CRM_Tân.xlsx` ghi hàng đi US | Cao | Rà soát GĐ 1–2 |
| N6 | Chăm sóc khách hàng có trong phase 1 không — `README.md` xếp vào phạm vi, `docs/02` mục 12 để ngỏ. Trùng với N3 nhưng nay có thêm chứng cứ vênh giữa hai tài liệu | Cao | Rà soát GĐ 1–2 |
| N7 | BR-1 nói mỗi người thuộc đúng một bộ phận, nhưng Admin hiện không thuộc bộ phận nào. Giữ nguyên hay bắt Admin cũng phải có bộ phận | Trung bình | Rà soát GĐ 1–2 |

### 1.3. Vận hành

| # | Nội dung | Mức | Nguồn |
|---|---|---|---|
| V1 | Máy chủ đặt ở đâu — thuê ngoài hay đặt tại văn phòng | Trung bình | Chưa chốt |
| V2 | Ai chịu trách nhiệm vận hành hằng ngày sau khi bàn giao | Cao | Chưa chốt |
| V3 | Kênh gửi thông báo nếu làm tính năng nhắc nộp báo cáo | Thấp | Phụ thuộc N1 |
| V4 | **Mốc nào thì nghiệm thu toàn diện.** Hiện quá ít màn hình để đánh giá được giao diện và trải nghiệm — người dùng không nghiệm thu từng phần nữa, dồn về một đợt. Đề xuất mốc: hết Giai đoạn 5, khi một bộ phận làm trọn được việc hằng ngày. Chờ người dùng chốt | Cao | Người dùng, 29.08.2026 |

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

## 6. Hiện trạng màn hình — chưa đủ để nghiệm thu

Người dùng nêu ngày 29.08.2026: **hiện quá thiếu màn hình để đánh giá được
giao diện và trải nghiệm.** Không nghiệm thu từng phần nữa; dồn về một đợt
kiểm thử toàn diện khi đủ màn hình. Mốc cụ thể xem **V4**.

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
| Lên đơn | 5 | Chưa |
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
| 29.08.2026 | Xong Giai đoạn 3 phần B, khép lại Giai đoạn 3. Chốt Q18 tới Q20, đóng K11 và K12, mở K13 và K14. Bỏ model `Position` khỏi tài liệu vì nó không tồn tại |
