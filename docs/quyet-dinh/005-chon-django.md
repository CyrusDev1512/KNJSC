# ADR-005 — Chọn Django làm khung ứng dụng

| Mục | Nội dung |
|---|---|
| Trạng thái | Đã áp dụng |
| Ngày | (điền ngày) |
| Người quyết định | (điền tên) |
| Liên quan | ADR-001, ADR-003 |

---

## Bối cảnh

Cần chọn ngôn ngữ và khung ứng dụng trước khi tạo repo. Bốn hướng được cân nhắc: Django, Laravel, Rails, Node với TypeScript.

Việc so sánh không dựa trên đặc điểm chung của từng khung, mà dựa trên **bốn yêu cầu khó nhất của KNJSC**.

---

## Bốn yêu cầu dùng để so sánh

### 1. Bảng và cột do người dùng tự tạo

Lưu dạng JSON, cần lọc và đánh chỉ mục trên nội dung JSON.

| Khung | Xử lý |
|---|---|
| Django | `JSONField` gắn PostgreSQL, lọc bằng cú pháp ORM, chỉ mục GIN |
| Laravel | Eloquent hỗ trợ cột JSON, cú pháp truy vấn tương đương |
| Rails | Kiểu `jsonb` qua ActiveRecord, tương đương |
| Node | Prisma hỗ trợ JSON nhưng lọc sâu phải viết truy vấn thô |

Ba khung đầu ngang nhau, Node yếu hơn.

### 2. Phân quyền theo phạm vi, áp ở một chỗ duy nhất

Yêu cầu quan trọng nhất — sai là rò rỉ dữ liệu giữa các bộ phận.

| Khung | Cơ chế |
|---|---|
| Django | Custom Manager — mọi truy vấn trên model tự động qua bộ lọc |
| Laravel | Global Scope — cùng cơ chế |
| Rails | `default_scope` — có, nhưng cộng đồng khuyên tránh vì khó gỡ khi cần |
| Node | Không có cơ chế sẵn, phải tự dựng lớp bọc |

Django và Laravel mạnh hơn rõ.

### 3. Trang quản trị

Tạo tài khoản, gán bộ phận và team, khoá tài khoản, tra nhật ký.

| Khung | Có sẵn |
|---|---|
| Django | Django Admin — không viết dòng nào |
| Laravel | Cần cài thêm và cấu hình |
| Rails | Cần thư viện ngoài |
| Node | Viết từ đầu |

Django tiết kiệm khoảng ba mươi giờ ở hạng mục này.

### 4. Đọc và ghi tệp Excel

Bốn khung đều có thư viện chín. Python nhỉnh hơn nhờ hệ sinh thái xử lý dữ liệu.

---

## Quyết định

**Chọn Django**, kèm:

| Thành phần | Lựa chọn |
|---|---|
| Cơ sở dữ liệu | PostgreSQL |
| Giao diện | HTMX, không dùng khung giao diện riêng |
| Tác vụ nền | Celery với Redis |
| Đóng gói | Docker Compose |

---

## Lý do

**Loại Node** vì thiếu hai thứ quan trọng nhất — cơ chế áp phạm vi quyền ở một chỗ, và trang quản trị. Phải tự viết cả hai, ước khoảng năm mươi tới sáu mươi giờ thêm.

**Loại Rails** vì `default_scope` bị chính cộng đồng Rails khuyên tránh, và cộng đồng ở Việt Nam nhỏ nhất trong bốn.

**Giữa Django và Laravel**, hai khung ngang nhau về mặt kỹ thuật. Khác biệt nằm ở hai điểm:

| | Django | Laravel |
|---|---|---|
| Trang quản trị | Có sẵn | Cài thêm |
| Tuyển người tại Việt Nam | Khó hơn | Dễ nhất |

**Chọn Django** vì dự án do một người làm, không thuê ngoài. Điểm mạnh về tuyển dụng của Laravel không phát huy, còn ba mươi giờ tiết kiệm từ trang quản trị thì có giá trị ngay.

---

## Vì sao HTMX thay vì khung giao diện riêng

Hệ thống nội bộ dưới một trăm người dùng, không cần ứng dụng một trang.

| Được | Mất |
|---|---|
| Không có bước dựng gói giao diện | Tương tác phức tạp khó hơn |
| Một ngôn ngữ, một kho mã nguồn | Ít người biết HTMX hơn React |
| Trang tải nhanh, ít mã kịch bản | |

Bảng dữ liệu là màn hình phức tạp nhất — lọc, sắp xếp, phân trang, sửa từng ô. HTMX làm được cả bốn mà không cần dựng gói.

---

## Hệ quả

**Được gì**

- Xác thực, phân quyền theo đối tượng, trang quản trị có sẵn
- Chuyển đổi cấu trúc dữ liệu chạy xuôi và ngược được
- `JSONField` với chỉ mục GIN phù hợp với quyết định ở ADR-001
- Thư viện đọc ghi Excel chín

**Mất gì**

- Chậm hơn Node ở tải rất cao — nhưng dưới ngưỡng của dự án này
- Cộng đồng Việt Nam nhỏ hơn Laravel, khó tuyển hơn nếu sau này cần
- Giao diện phải tự dựng, không có thư viện thành phần sẵn như React

**Chỗ cần cẩn thận về sau**

- Phải dùng Custom Manager cho phạm vi quyền, không viết điều kiện lọc rải rác
- Trang quản trị mặc định bỏ qua tầng dịch vụ — chỉ dùng cho quản trị viên, không dùng cho nghiệp vụ hằng ngày
- HTMX cần kỷ luật về cách tổ chức mảnh giao diện, nếu không sẽ khó theo dõi

---

## Điều kiện xem lại

Xem lại khi có một trong ba tình huống:

- Cần tuyển người bảo trì và không tìm được người biết Django
- Giao diện cần tương tác phức tạp vượt khả năng HTMX
- Số người dùng đồng thời vượt xa dự kiến và Django thành nút thắt đo được
