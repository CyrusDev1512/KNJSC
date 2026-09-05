# Thiết kế kỹ thuật

| Mục | Nội dung |
|---|---|
| Dự án | Kim Ngân JSC — Hệ thống vận hành nội bộ |
| Giai đoạn | Phase 1 |
| Phiên bản tài liệu | 0.1 — bản nháp |
| Ngày | (điền ngày) |
| Người viết | (điền tên) |
| Tài liệu liên quan | `02-yeu-cau-san-pham.md` · `04-tieu-chi-nghiem-thu.md` · `quyet-dinh/` |

> Tài liệu này dành cho người phát triển và AI hỗ trợ viết mã.
> Nó trả lời câu hỏi **làm thế nào**, còn `02-yeu-cau-san-pham.md` trả lời **phải làm được gì**.

---

## 1. Tổng quan kiến trúc

### 1.1. Phân lớp

```
Giao diện          màn hình, biểu mẫu, bảng
    ↓
Tầng xử lý         nhận yêu cầu, kiểm quyền, trả kết quả
    ↓
Tầng dịch vụ       quy tắc nghiệp vụ — không biết gì về giao thức web
    ↓
Tầng truy cập      truy vấn dữ liệu, áp phạm vi quyền
    ↓
Cơ sở dữ liệu
```

**Quy tắc bắt buộc:** quy tắc nghiệp vụ nằm ở tầng dịch vụ, không nằm ở tầng xử lý.

Lý do: tác vụ chạy nền và lệnh dòng lệnh cần dùng lại quy tắc đó mà không đi qua trình duyệt.
Nếu quy tắc nằm lẫn trong tầng xử lý thì phải viết lại, và hai bản sẽ lệch nhau.

### 1.2. Lựa chọn nền tảng

| Thành phần | Công nghệ | Lý do |
|---|---|---|
| Khung ứng dụng | Django 5.2 | Có sẵn xác thực, phân quyền, lớp truy cập dữ liệu — ADR-005 |
| Cơ sở dữ liệu | PostgreSQL | Ràng buộc toàn vẹn, giao dịch, chịu nhiều người ghi |
| Đóng gói | Docker Compose | Chạy giống nhau trên mọi máy |
| Bảng dữ liệu | Tự viết, chỉ cột tính sẵn | Không nhúng thư viện ngoài — ADR-002, ADR-006 |

### 1.3. Sơ đồ triển khai

```
┌──────────────── Máy chủ ─────────────────┐
│                                          │
│  ┌────────────┐      ┌────────────────┐  │
│  │  web       │─────▶│  db            │  │
│  │  ứng dụng  │      │  PostgreSQL    │  │
│  └─────┬──────┘      └───────┬────────┘  │
│        │                     │           │
│   thư mục tệp          vùng lưu dữ liệu  │
│   (bind mount)         (docker volume)   │
└──────────────────────────────────────────┘
```

| Mục | Chi tiết |
|---|---|
| Cơ sở dữ liệu | Vùng lưu do Docker quản lý, không mất khi dựng lại container |
| Tệp đính kèm và sao lưu | Thư mục thật trên máy, người vận hành lấy được không cần biết Docker |
| Cổng cơ sở dữ liệu | Không mở ra ngoài, chỉ ứng dụng gọi được |

---

## 2. Mô hình dữ liệu

### 2.1. Quy ước chung

Mọi bảng có:

| Trường | Nội dung |
|---|---|
| Khoá chính | Định danh duy nhất |
| Thời điểm tạo, thời điểm sửa | Lưu theo giờ quốc tế |
| Người tạo, người sửa | Liên kết tới tài khoản |
| Đánh dấu đã xoá | Xoá là đánh dấu, không xoá vĩnh viễn — BR-4 |

### 2.2. Các bảng chính

| Bảng | Nội dung | Ghi chú |
|---|---|---|
| Bộ phận | Tên, trạng thái hoạt động | Sale, Marketing, Vận đơn |
| Team | Tên, thuộc bộ phận nào, người phụ trách | Một bộ phận nhiều team — FR-2.2 |
| Tài khoản | Email, mật khẩu đã băm, trạng thái khoá | Tách khỏi hồ sơ nhân sự |
| Hồ sơ người dùng | Họ tên, bộ phận, team, cấp bậc | Cấp bậc: Staff, Leader, Manager |
| Định nghĩa trường | Tên hiển thị, kiểu dữ liệu, nhãn ý nghĩa | Dùng cho biểu mẫu tự tạo |
| Biểu mẫu | Tên, bộ phận áp dụng, danh sách trường, thứ tự | FR-8.1 |
| Bảng dữ liệu | Tên, danh sách cột, cấu hình hiển thị | Nơi dữ liệu từ biểu mẫu ghi vào |
| Liên kết biểu mẫu và bảng | Trường nào của biểu mẫu ghi vào cột nào của bảng | FR-8.3 |
| Bản ghi dữ liệu | Nội dung một dòng trong bảng | |
| Báo cáo hằng ngày | Người nộp, thời điểm nộp, nội dung | FR-4.2 |
| Đơn hàng | Khách hàng, giá bán, phương thức thanh toán, người tạo | |
| Dòng sản phẩm trong đơn | Đơn nào, sản phẩm nào, số lượng, đơn giá | Một đơn nhiều dòng — FR-6.2 |
| Danh mục sản phẩm | Tên, nhóm, đơn vị tính | Quản lý tự thêm |
| Nhật ký hoạt động | Ai làm gì, trên đối tượng nào, khi nào | Chỉ ghi thêm — BR-6 |

### 2.3. Quan hệ chính

```
Bộ phận ──1:n── Team ──1:n── Hồ sơ người dùng ──1:1── Tài khoản
                                     │
                                     ├──1:n── Báo cáo hằng ngày
                                     └──1:n── Đơn hàng ──1:n── Dòng sản phẩm
                                                   │
                                                   └──ghi vào──▶ Bản ghi dữ liệu

Biểu mẫu ──n:m── Định nghĩa trường
    │
    └──liên kết──▶ Bảng dữ liệu ──1:n── Bản ghi dữ liệu
```

### 2.4. Cột cần đánh chỉ mục

Đánh chỉ mục cho mọi cột dùng để lọc, tìm kiếm hoặc nối bảng.

| Bảng | Cột | Lý do |
|---|---|---|
| Báo cáo hằng ngày | Ngày, người nộp | Lọc theo thời gian và theo người |
| Đơn hàng | Ngày tạo, người tạo, số điện thoại khách | Lọc, thống kê, phát hiện khách mua lại — FR-6.7 |
| Bản ghi dữ liệu | Bảng chứa nó, ngày tạo | Lọc theo bảng và thời gian |
| Hồ sơ người dùng | Bộ phận, team | Áp phạm vi quyền |
| Nhật ký hoạt động | Thời điểm, người thực hiện | Tra cứu |

**Không đánh chỉ mục mọi cột.** Mỗi chỉ mục làm việc ghi chậm hơn và chiếm thêm dung lượng.

### 2.5. Bảng dữ liệu do người dùng tạo

Đây là phần khác biệt so với các bảng cố định.

Người dùng tạo bảng mới thì hệ thống không tạo bảng vật lý trong cơ sở dữ liệu.
Thay vào đó, dữ liệu lưu theo mô hình:

```
Bảng dữ liệu       định nghĩa: tên bảng, danh sách cột
Bản ghi dữ liệu    một dòng, nội dung lưu theo cấu trúc khoá và giá trị
```

**Đánh đổi:** linh hoạt nhưng truy vấn chậm hơn bảng cố định.

**Cách bù:** mỗi cột có **nhãn ý nghĩa** để hệ thống hiểu nó là gì:

| Nhãn | Hệ thống dùng để |
|---|---|
| Ngày | Lọc theo khoảng thời gian |
| Khách hàng | Đếm khách mới, khách cũ |
| Số điện thoại | Phát hiện mua lại |
| Doanh thu | Cộng tổng, tính trung bình |
| Người bán | Thống kê theo người |
| Sản phẩm | Thống kê theo sản phẩm |
| Trạng thái | Lọc và đếm theo trạng thái |

Cột có nhãn thì được tách ra cột riêng có chỉ mục, để lọc và thống kê nhanh.
Cột không nhãn chỉ lưu và hiển thị.

---

## 3. Phân quyền

### 3.1. Ba tầng

```
1. Bộ phận      người dùng thuộc bộ phận nào
2. Cấp bậc      Staff, Leader, Manager
3. Phạm vi      suy ra từ hai tầng trên
```

### 3.2. Cách áp phạm vi

**Toàn bộ truy vấn dữ liệu đi qua một hàm duy nhất:**

```
pham_vi(nguoi_dung) → danh sách team hoặc bộ phận được xem
```

| Cấp bậc | Trả về |
|---|---|
| Staff | Chỉ bản ghi do chính người đó tạo |
| Leader | Toàn bộ team người đó phụ trách |
| Manager | Toàn bộ bộ phận |

**Không viết điều kiện lọc rải rác ở từng màn hình.** Lý do: mỗi màn hình mới lại phải nhớ
lọc, và đó là chỗ dễ sót nhất dẫn tới rò rỉ dữ liệu.

### 3.3. Nguyên tắc thực thi

| # | Nguyên tắc |
|---|---|
| P1 | Quyền kiểm ở máy chủ, không chỉ ẩn chức năng trên giao diện — FR-3.6 |
| P2 | Phạm vi áp ở tầng truy cập dữ liệu, không lọc ở giao diện |
| P3 | Truy cập ngoài phạm vi trả về lỗi từ chối, không trả danh sách rỗng — FR-3.5 |
| P4 | Khi đổi quyền hoặc khoá tài khoản, phiên đang mở mất hiệu lực ngay — FR-1.5 |
| P5 | Mỗi lần xuất dữ liệu phải ghi vào nhật ký |

### 3.4. Thiết kế mở rộng

Phase 1 chỉ có phạm vi suy ra từ cấp bậc. Nhưng hàm `pham_vi` được thiết kế để
sau này cộng thêm phần được cấp riêng:

```
pham_vi = phạm vi theo cấp bậc  +  phạm vi được cấp thêm
```

Phase 1 phần thứ hai luôn rỗng. Thêm sau không phải sửa chỗ nào khác.

---

## 4. Luồng nghiệp vụ chính

### 4.1. Lên đơn và ghi sang bảng vận đơn

```
Sale điền biểu mẫu
    ↓
Hệ thống kiểm tra dữ liệu hợp lệ
    ↓
Lưu đơn hàng và các dòng sản phẩm
    ↓
Tra cứu liên kết: biểu mẫu này ghi vào bảng nào
    ↓
Tạo bản ghi mới trong bảng đích
    ↓
Lưu mã liên kết giữa đơn và bản ghi          ← FR-6.4
    ↓
Ghi nhật ký
```

**Một chiều.** Sửa bản ghi trên bảng vận đơn không cập nhật ngược lại đơn hàng.

Mã liên kết ở bước áp chót cho phép sau này làm hai chiều mà không phải chuyển đổi dữ liệu cũ.

**Xử lý lỗi:** nếu bước tạo bản ghi thất bại, toàn bộ giao dịch phải quay lui — không được
để đơn hàng đã lưu mà bảng vận đơn không có dòng tương ứng.

### 4.2. Nộp báo cáo hằng ngày

```
Người dùng mở biểu mẫu của bộ phận mình
    ↓
Điền và gửi
    ↓
Hệ thống ghi nhận thời điểm nộp
    ↓
Báo cáo chuyển sang trạng thái đã nộp, không sửa được   ← BR-2
```

### 4.3. Tạo biểu mẫu mới

```
Manager chọn các trường từ danh sách định nghĩa trường
    ↓
Sắp xếp thứ tự, đánh dấu trường bắt buộc
    ↓
Chọn bảng đích
    ↓
Hệ thống kiểm tra tương thích kiểu dữ liệu    ← FR-8.6
    ↓
Phân quyền: ai điền biểu mẫu, ai xem bảng
```

### 4.4. Nhập tệp Excel vào bảng — FR-7.5

```
Kiểm cỡ (≤ 10 MB), loại thật của tệp (chữ ký đầu tệp so với đuôi)   ← S7, AC-7.8, AC-7.9
    ↓
Đọc tối đa 5.000 dòng; dò hàng tiêu đề trong 10 hàng đầu
    ↓
Ánh xạ cột: tên cột → bí danh (Name, Phone, "SL <sản phẩm>"…) → cột bảng
    ↓
Lưu tệp vào storage/uploads/imports/, tạo tác vụ *Chờ xác nhận*  ← chưa ghi gì
    ↓
Người dùng xem trước, bấm Xác nhận → tác vụ *Chờ xử lý* → hàng đợi Celery
    ↓
Worker: đọc lại tệp, ép kiểu từng ô, ghi theo lô 500 (bulk_create),
        gọi tay cột tính sẵn và cột tách, báo tiến độ, gom dòng lỗi
    ↓
Một dòng nhật ký IMPORT; tệp tạm xoá
```

Dòng lỗi **không** chặn dòng hợp lệ (AC-7.6); số hàng báo lỗi là số hàng thật
trong Excel. Cột kiểu *Chọn một* có sổ danh sách (`choice_registry`) thì giá
trị phải nằm trong sổ — nhập không phân biệt hoa thường.

Tác vụ *Chờ xử lý* quá 15 phút không ai nhận → đánh dấu **kẹt**, ghi nhật
ký, thư cho người vận hành (worker không chạy).

### 4.5. Xuất tệp Excel — FR-7.6, ADR-002

Cùng bộ đọc bộ lọc với màn hình bảng (`query.read_filters`), nên tệp xuất là
**đúng thứ đang hiện**. Ghi nhật ký EXPORT trước khi trả tệp (P5). Dưới
2.000 dòng trả ngay; lớn hơn chạy nền, tệp ở `storage/exports/` 24 giờ; trần
50.000 dòng. Tiêu đề là tên cột, giá trị giữ kiểu (Decimal, ngày thật) để nhập
lại được (AC-7.7).

### 4.6. Bảng tính — ADR-009, ADR-010

Lưới kiểu Excel cho **mọi bảng** trong phạm vi quyền (`/bang-tinh/<mã>/`),
dựng đầu tiên cho bảng `van_don`. Là một cách nhìn lên `DataRecord`; phần
riêng của vận đơn bật theo `grid_service.is_waybill`:

| Việc | Cách làm |
|---|---|
| Phạm vi | `DataRecord.objects.in_scope(user)` — bảng dùng chung nên cả bộ phận thấy mọi dòng |
| Lọc, sắp xếp | `forms_builder.query` — toán tử `trong`, `chua`, `lon_bang`/`nho_bang`, `rong`/`co`; cột JSON số nguyên được ép kiểu để so được |
| Lọc trùng | Cột ảo: `Subquery` đếm dòng cùng `val_phone` trong bảng; số trống không tính |
| Thứ tự cột | `dispatch_service.GRID_ORDER`, cột `sl_*` chèn sau thông tin khách |
| Danh sách chọn | `forms_builder.choice_registry` — `crm` đăng ký lúc khởi động; *chặt* với trạng thái, *gợi ý* với nhân viên |
| Sửa ô | `record_service.update_cell` — cùng đường với Bảng dữ liệu; `can_edit_record` trả False khi bảng nằm trong `GRID_ONLY_TABLES` |
| Dịch vụ riêng | `knjsc/settings/bangtinh.py`: URLconf thu hẹp, `GRID_ONLY_TABLES` rỗng; container `bangtinh` cổng 8021; tương lai subdomain với `SESSION_COOKIE_DOMAIN` |
| Trạng thái lưới | Trên URL (`f_<cột>`, `sap`, `chieu`, `trung`, `sp`); không lưu máy chủ |
| Phạm vi bảng | `TableDef.objects.in_scope(user)` — ngoài phạm vi 404; `/bang-tinh/` mở `van_don` nếu thấy, không thì bảng đầu tiên |
| Dòng trống | `GRID_SPARE_ROWS` dòng cuối lưới; POST `dong-moi/` → `record_service.create_record`; quyền `grant_service.can_create_record` |
| Định dạng ô | `DataRecord.style` JSON, sổ đóng `record_service.STYLE_SCHEMA`; `update_styles` ghi bằng `update_fields`; POST `dinh-dang/` trả ô hx-swap-oob; lớp CSS cố định `dd-*` |
| Cột khoá | `ColumnDef.is_key`, ràng buộc một cột/bảng; ô có liên kết `?f_<cột>=<giá trị>` |
| Thanh bên trái | `crm/services/sidebar_service.py` — chọn nhanh và khoảng ngày viết vào `f_<Ngày>__lon_bang/__nho_bang`; sản phẩm vào `f_<Sản phẩm>__trong` hoặc `sp=` (vận đơn) |
| Xuất đúng lưới | `export_service.QUERYSET_BUILDERS` — `crm` đăng ký builder `grid` lúc khởi động |
| Thư mục | `forms_builder.Folder` (phẳng, theo bộ phận, xoá mềm), `TableDef.folder`; `folder_service.tree` hai truy vấn; quyền `can_manage_folders` |

---

## 5. Quy tắc viết truy vấn

Bốn quy tắc bắt buộc, áp cho mọi màn hình.

| # | Quy tắc | Lý do |
|---|---|---|
| Q1 | Mọi màn hình danh sách phải có phân trang | Không tải toàn bộ bảng về |
| Q2 | Truy vấn có quan hệ phải lấy sẵn dữ liệu liên quan trong cùng một lệnh | Tránh chạy N lệnh cho N dòng |
| Q3 | Chỉ lấy các cột cần hiển thị, không lấy toàn bộ | Giảm dữ liệu truyền |
| Q4 | Không dùng lệnh lấy toàn bộ bảng trong màn hình danh sách | |

**Cách kiểm:** bật ghi lại truy vấn khi phát triển. Một màn hình danh sách chạy quá 10 lệnh
truy vấn là dấu hiệu vi phạm Q2.

---

## 6. Hiệu năng

### 6.1. Ngân sách thời gian

| Thao tác | Ngưỡng | Yêu cầu liên quan |
|---|---|---|
| Tải màn hình danh sách | Dưới 2 giây với 50.000 bản ghi | NFR-1 |
| Nhập tệp Excel 2.000 dòng | Dưới 60 giây | NFR-3 |
| Người dùng đồng thời | 50 | NFR-2 |

### 6.2. Kỹ thuật áp dụng

| Kỹ thuật | Áp dụng ở đâu |
|---|---|
| Phân trang | Mọi màn hình danh sách, mặc định 25 dòng mỗi trang |
| Chỉ mục | Các cột ở mục 2.4 |
| Gộp truy vấn | Mọi màn hình có dữ liệu liên quan |
| Lưu đệm | Danh sách bộ phận, team, danh mục sản phẩm, quyền người dùng |
| Chạy nền | Nhập tệp lớn, xuất báo cáo lớn, gửi thông báo hàng loạt |
| Nén khi truyền | Toàn bộ phản hồi |
| Lưu đệm tệp tĩnh | Ảnh, biểu định kiểu, mã kịch bản |

### 6.3. Giới hạn đầu vào

Không phải để tăng tốc, mà để hệ thống không sập vì đầu vào bất thường.

| Giới hạn | Giá trị | Yêu cầu |
|---|---|---|
| Kích thước mỗi tệp tải lên | 10 MB | NFR-11 |
| Loại tệp cho phép | Excel, CSV, JPG, PNG | NFR-12 |
| Số dòng mỗi lần nhập | 5.000 | NFR-13 |
| Số bản ghi mỗi lần xuất | 50.000 | NFR-14 |

### 6.4. Nguyên tắc

| # | Nguyên tắc |
|---|---|
| 1 | Đo trước khi sửa — không đoán chỗ nào chậm |
| 2 | Sửa chỗ chậm nhất trước |
| 3 | Không tối ưu sớm — viết đúng trước, nhanh sau |
| 4 | Tối ưu làm mã nguồn khó đọc hơn, chỉ làm khi có lý do đo được |

---

## 7. Bảo mật

| # | Yêu cầu | Cách làm |
|---|---|---|
| S1 | Mật khẩu lưu dạng đã băm | Dùng thuật toán băm hiện hành, không tự viết |
| S2 | Kết nối mã hoá bắt buộc khi truy cập từ ngoài | Cấu hình ở tầng máy chủ |
| S3 | Cookie phiên chỉ gửi qua kết nối mã hoá | Bật khi triển khai, tắt khi phát triển cục bộ |
| S4 | Chống giả mạo yêu cầu | Dùng cơ chế có sẵn của khung ứng dụng |
| S5 | Không ghi dữ liệu nhạy cảm vào nhật ký ứng dụng | Kiểm tra khi rà soát mã nguồn |
| S6 | Giới hạn số lần đăng nhập sai | 5 lần, khoá 15 phút — FR-1.2 |
| S7 | Tệp tải lên phải kiểm tra loại thật, không tin phần mở rộng | Đọc phần đầu tệp |

---

## 8. Sao lưu và phục hồi

| Mục | Cách làm | Yêu cầu |
|---|---|---|
| Tần suất | Mỗi ngày một lần, tự động | NFR-19 |
| Thời gian giữ | 30 ngày, tối đa 30 bản gần nhất | NFR-15 |
| Nơi lưu | Ít nhất một bản ở nơi khác máy chủ chính | NFR-20 |
| Mã hoá | Bản sao lưu mã hoá trước khi rời khỏi máy chủ | |
| Thử phục hồi | Ít nhất mỗi quý một lần, trên môi trường thử | NFR-10 |

**Bản sao lưu chưa từng được phục hồi thử thì chưa được tính là bản sao lưu.**

**Cách làm (Giai đoạn 7B):** `core/services/backup_service.py` chạy
`pg_dump --format=custom` lúc 02:00 qua Celery beat; mật khẩu đi qua
`PGPASSWORD`, không nằm trên dòng lệnh; ghi `.part` rồi đổi tên, kiểm chữ ký
`PGDMP` và cỡ tối thiểu; giữ 30 bản trong `BACKUP_DIR`. Mỗi lần chạy là một
`BackgroundJob` loại BACKUP và một dòng nhật ký BACKUP; thất bại → thư cho
`ADMINS`. Phục hồi bằng `pg_restore --clean` qua lệnh `phuc_hoi --toi-chac-chan`.
Mã hoá bản sao lưu khi chép ra ngoài máy chủ để Giai đoạn 8.

---

## 9. Dọn dẹp tự động

| Đối tượng | Giữ bao lâu | Yêu cầu |
|---|---|---|
| Bản sao lưu tự động | 30 ngày, tối đa 30 bản | NFR-15 |
| Tệp tạm sinh ra khi xuất dữ liệu | 24 giờ | NFR-16 |
| Tệp tải lên chờ nhập mà người dùng bỏ dở | 24 giờ, tác vụ đóng lại | NFR-16 |
| Tác vụ nền chờ quá 15 phút không ai nhận | Đánh dấu kẹt, báo người vận hành | kien-truc.md |
| Nhật ký hoạt động | 24 tháng | NFR-17 |
| Phiên đăng nhập đã hết hạn | Xoá hằng ngày | |

Tác vụ dọn dẹp chạy nền theo lịch, ghi lại kết quả mỗi lần chạy.

---

## 10. Nội dung chưa quyết định

| # | Nội dung | Ảnh hưởng tới thiết kế |
|---|---|---|
| 1 | Tạo biểu mẫu thì tự sinh bảng hay luôn chọn bảng có sẵn | Mục 4.3 |
| 2 | Danh sách nhãn ý nghĩa cuối cùng | Mục 2.5 |

Các quyết định này khi chốt sẽ được ghi vào `quyet-dinh/` kèm lý do.
