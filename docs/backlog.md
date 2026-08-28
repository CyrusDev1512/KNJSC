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
| K1 | Bảng dữ liệu cho phép gõ công thức tự do tới mức nào — chỉ cột tính sẵn, chọn phép tính từ danh sách, hay gõ cú pháp đầy đủ | Cao | Phân tích tệp vận đơn thật |
| K2 | Tạo biểu mẫu thì tự sinh bảng mới, hay luôn phải chọn bảng có sẵn | Trung bình | Bàn thiết kế |
| K3 | Danh sách nhãn ý nghĩa cuối cùng cho cột trong bảng tự tạo | Cao | Bàn thiết kế |
| K4 | Khung ứng dụng cụ thể sẽ dùng | Chặn | Chưa bàn |
| K5 | Có nên đặt ngưỡng tỉ lệ bao phủ kiểm thử không | Thấp | Bàn tài liệu |
| K6 | Công cụ đo hiệu năng khi kiểm 50 người dùng đồng thời | Thấp | Bàn tài liệu |
| K7 | Đổi khoảng 60 định danh tiếng Việt trong mã Python sang tiếng Anh theo quy ước CLAUDE.md, gồm cả tên ràng buộc `team_unique_trong_bo_phan` đã vào PostgreSQL | Trung bình | Rà soát GĐ 1–2 |
| K8 | `docs/03` mục 2.1 đòi mọi bảng có cột "người sửa"; `ScopedModel` mới có `created_by`, chưa có `updated_by` | Thấp | Rà soát GĐ 1–2 |
| K9 | Chưa có trang lỗi 404 và 500 bằng tiếng Việt — NFR-6 mới đạt một phần | Trung bình | Rà soát GĐ 1–2 |
| K10 | Quy tắc Q3 "chỉ lấy cột cần hiển thị" chưa áp ở màn hình nào | Thấp | Rà soát GĐ 1–2 |

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
| N8 | Bảy nhãn ý nghĩa: `docs/03` mục 2.5 ghi Ngày, Khách hàng, Số điện thoại, Doanh thu, Người bán, Sản phẩm, Trạng thái. Bản dựng giao diện lại đề xuất Ngày, Số lượng, Tiền, Tỉ lệ, Người, Sản phẩm, Thị trường. Chốt danh sách nào | Cao | Rà soát GĐ 1–2 |

### 1.3. Vận hành

| # | Nội dung | Mức | Nguồn |
|---|---|---|---|
| V1 | Máy chủ đặt ở đâu — thuê ngoài hay đặt tại văn phòng | Trung bình | Chưa chốt |
| V2 | Ai chịu trách nhiệm vận hành hằng ngày sau khi bàn giao | Cao | Chưa chốt |
| V3 | Kênh gửi thông báo nếu làm tính năng nhắc nộp báo cáo | Thấp | Phụ thuộc N1 |

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

## Nhật ký cập nhật

| Ngày | Nội dung |
|---|---|
| (điền) | Tạo tài liệu |
| 28.08.2026 | Rà soát Giai đoạn 1 và 2 — 19 phát hiện. Sửa 18, hoãn K7. Thêm K7–K10 và N5–N8 |
