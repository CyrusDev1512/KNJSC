# Tổng quan sản phẩm

| Mục | Nội dung |
|---|---|
| Dự án | Kim Ngân JSC — Hệ thống vận hành nội bộ |
| Giai đoạn | Phase 1 |
| Phiên bản tài liệu | 0.1 — bản nháp |
| Ngày | (điền ngày) |
| Người viết | (điền tên) |
| Người duyệt | (điền tên) |

> Tài liệu này dành cho người quyết định phạm vi và người sử dụng hệ thống.
> Nội dung kỹ thuật nằm ở `03-thiet-ke-ky-thuat.md`.

---

## 1. Hệ thống này giải quyết gì

### 1.1. Cách làm việc hiện tại

Ba bộ phận phối hợp trong một chuỗi, mỗi bộ phận dùng công cụ riêng:

```
Marketing  ──▶  Sale  ──▶  Vận đơn
   │            │            │
biểu mẫu     biểu mẫu     bảng tính
riêng        riêng        riêng
```

Dữ liệu chuyển giữa các bộ phận bằng cách sao chép thủ công hoặc nhắn tin.

### 1.2. Ba vấn đề

| # | Vấn đề | Hệ quả |
|---|---|---|
| 1 | Dữ liệu nằm rời ở nhiều nơi | Không đối chiếu được giữa các bộ phận, số liệu lệch nhau |
| 2 | Không phân quyền được | Ai cũng xem được dữ liệu của người khác |
| 3 | Báo cáo tổng hợp làm thủ công | Tốn thời gian mỗi ngày, dễ sai sót |

### 1.3. Điều hệ thống hướng tới

Một nơi làm việc chung, nơi:

- Dữ liệu nhập một lần, mọi bộ phận liên quan đều thấy
- Mỗi người chỉ thấy phần thuộc quyền của mình
- Báo cáo tổng hợp tự động từ dữ liệu đã có

---

## 2. Người sử dụng

### 2.1. Ba bộ phận

| Bộ phận | Công việc chính trên hệ thống |
|---|---|
| **Marketing** | Nộp báo cáo hằng ngày · Xem và cập nhật bảng dữ liệu |
| **Sale** | Nộp báo cáo hằng ngày · Lên đơn hàng |
| **Vận đơn** | Nộp báo cáo hằng ngày · Xem và cập nhật bảng vận đơn |

### 2.2. Ba cấp bậc

| Cấp bậc | Thấy được dữ liệu của ai |
|---|---|
| **Staff** | Chỉ bản thân |
| **Leader** | Toàn bộ team mình phụ trách |
| **Manager** | Toàn bộ bộ phận |

Một bộ phận có thể có nhiều team. Số lượng team do quản lý tự thêm khi cần.

---

## 3. Sáu hạng mục của phase 1

### 3.1. Đăng nhập và phân quyền

Mỗi người có một tài khoản riêng. Sau khi đăng nhập, hệ thống đưa thẳng tới
phần việc của người đó — Sale vào màn hình lên đơn, Vận đơn vào bảng vận đơn.

Người không có quyền không nhìn thấy chức năng đó, và cũng không truy cập được
bằng bất kỳ cách nào khác.

### 3.2. Báo cáo hằng ngày

Mỗi bộ phận có biểu mẫu báo cáo riêng, nội dung do quản lý quyết định.

Nhân viên nộp báo cáo theo lịch quy định. Hệ thống ghi nhận thời điểm nộp.
Người đã nộp xem lại được báo cáo cũ của mình, nhưng không sửa được.

### 3.3. Báo cáo tổng hợp

Thống kê số liệu từ báo cáo hằng ngày và đơn hàng, theo bốn cách nhóm:

```
Tổng hợp toàn bộ
Theo từng nhân viên
Theo sản phẩm
Theo thị trường
```

Có bộ lọc theo khoảng thời gian và theo sản phẩm.

### 3.4. Lên đơn

Sale nhập đơn hàng qua biểu mẫu. Mỗi đơn có thông tin khách hàng, danh sách
sản phẩm kèm số lượng, giá bán và phương thức thanh toán.

Sau khi lưu, đơn tự động ghi sang bảng vận đơn để bộ phận vận đơn xử lý.

Sale xem lại được đơn cũ của mình, không sửa được sau khi đã lưu.

### 3.5. Bảng tính

Bảng dữ liệu dùng chung cho Marketing và Vận đơn, với các thao tác quen thuộc:

- Xem nhiều dòng cùng lúc, cuộn và tìm kiếm
- Lọc và sắp xếp theo từng cột
- Công thức tính toán
- Nhập và xuất tệp Excel

### 3.6. Quản lý biểu mẫu và bảng

Mỗi thị trường có cấu trúc dữ liệu khác nhau. Quản lý tự tạo được biểu mẫu và
bảng cho thị trường mới mà không cần người phát triển can thiệp.

```
Quản lý tạo biểu mẫu  →  chọn các trường, sắp xếp thứ tự
Chọn bảng đích        →  dữ liệu từ biểu mẫu ghi vào bảng nào
Phân quyền            →  ai được điền biểu mẫu, ai được xem bảng
```

---

## 4. Ngoài phạm vi phase 1

Những phần sau thuộc giai đoạn tiếp theo:

| Nhóm | Nội dung |
|---|---|
| Nhân sự | Đánh giá năng lực, đào tạo, chấm công, nghỉ phép, bảo hiểm |
| Kế toán | Thống kê và đối chiếu với phần mềm kế toán |
| Kho | Hàng sản xuất, vận chuyển, tồn kho, xuất kho |
| Trợ lý AI | Hỗ trợ Sale và Chăm sóc khách hàng |
| Ứng dụng di động | Bản cài đặt từ cửa hàng ứng dụng |

Hệ thống chạy trên trình duyệt, dùng được trên máy tính, máy tính bảng và
điện thoại. Đây không phải ứng dụng cài đặt riêng.

---

## 5. Giả định

Những điều sau được coi là đúng khi thiết kế. Nếu sai thì phải xem lại phạm vi.

| # | Giả định |
|---|---|
| 1 | Số người dùng dưới 100, tối đa 50 người truy cập cùng lúc |
| 2 | Khối lượng dữ liệu khoảng 2.000 tới 5.000 dòng mỗi tháng cho mỗi team |
| 3 | Toàn bộ người dùng thuộc cùng một công ty |
| 4 | Giao diện và thông báo bằng tiếng Việt |
| 5 | Người dùng làm việc chủ yếu trên máy tính, điện thoại dùng để nộp báo cáo |

---

## 6. Nội dung chưa quyết định

Những điểm sau cần thống nhất trước khi triển khai. Chi tiết ở `backlog.md`.

| # | Nội dung | Ảnh hưởng |
|---|---|---|
| 1 | Bảng tính cho phép người dùng gõ công thức tự do tới mức nào | Độ phức tạp và thời gian triển khai |
| 2 | Biểu mẫu tạo mới thì tự sinh bảng, hay luôn phải chọn bảng có sẵn | Cách vận hành hằng ngày |
| 3 | Lịch nộp báo cáo có bắt buộc đúng giờ không | Có cần cơ chế nhắc và chặn hay không |
