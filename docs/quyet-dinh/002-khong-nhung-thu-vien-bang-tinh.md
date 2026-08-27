# ADR-002 — Không nhúng thư viện bảng tính, dùng bảng dữ liệu có cột tính

| Mục | Nội dung |
|---|---|
| Trạng thái | Đã áp dụng |
| Ngày | (điền ngày) |
| Người quyết định | (điền tên) |
| Liên quan | ADR-001 |

---

## Bối cảnh

Marketing và Vận đơn hiện làm việc trên Google Sheet và Excel. Khi chuyển sang hệ thống mới, câu hỏi là màn hình bảng nên là bảng tính đầy đủ hay bảng dữ liệu có cấu trúc.

Người dùng quen Excel, nên trực giác ban đầu là nhúng một thư viện bảng tính để họ không phải đổi thói quen.

---

## Bằng chứng từ dữ liệu thật

Đọc hai tệp của công ty:

| Tệp | Số cột có công thức | Loại công thức |
|---|---|---|
| `CRM_Tân.xlsx` — sheet BC MKT | 5 | Phép chia: CPO, giá Mess, tỉ lệ, AOV |
| `CRM_Tân.xlsx` — sheet BC SALE | 1 | Phép chia: tỉ lệ chốt |
| `CRM_Tân.xlsx` — sheet CSKH | 1 | Phép chia: tỉ lệ chốt |
| Tệp vận đơn — 2.099 dòng, 44 cột | 4 | Đếm trùng, đếm dòng, lấy dữ liệu từ tệp khác |

**Mười một công thức trong toàn bộ hệ thống hiện tại.** Không có phép tính theo nhiều điều kiện, không có tra cứu chéo bảng, không có công thức lồng nhau.

Bốn công thức trong tệp vận đơn thì ba cái hệ thống tính sẵn được, một cái không cần vì dữ liệu sẽ nằm cùng một cơ sở dữ liệu.

---

## Các lựa chọn đã cân nhắc

| Lựa chọn | Ưu | Nhược |
|---|---|---|
| **A — Nhúng thư viện bảng tính** | Giao diện quen thuộc · Hàng trăm hàm công thức · Thao tác quen tay | **Dữ liệu lưu dạng JSON không cấu trúc** · Không thống kê tự động · Không phân quyền theo dòng · Không kiểm được kiểu dữ liệu · Nặng vài MB · Khó tuỳ chỉnh |
| **B — Bảng dữ liệu thuần** | Nhẹ · Dữ liệu có cấu trúc · Phân quyền tới từng dòng và cột · Toàn quyền tuỳ chỉnh | Không gõ được công thức |
| **C — Bảng dữ liệu có cột tính** | Như B, thêm khả năng người dùng tự tạo cột tính bằng cách chọn phép tính từ danh sách | Không gõ được cú pháp Excel |

---

## Quyết định

**Chọn C — bảng dữ liệu có cột tính.**

Người dùng thêm cột mới bằng cách chọn phép tính từ danh sách, không gõ cú pháp:

```
Tên cột      Doanh thu trung bình mỗi đơn
Phép tính    [ Chia ▾ ]
Cột 1        [ Doanh thu ▾ ]
Cột 2        [ Số đơn ▾ ]
```

Danh sách khoảng mười hai phép tính: cộng, trừ, nhân, chia, đếm, tổng, trung bình, lớn nhất, nhỏ nhất, đếm trùng, số ngày giữa hai cột, điều kiện nếu-thì.

---

## Ba nấc khi phát sinh phép tính mới

| Nấc | Cách xử lý | Ai làm |
|---|---|---|
| 1 | Bộ lọc có sẵn cộng dòng tổng | Người dùng |
| 2 | Thêm cột tính, chọn phép tính từ danh sách | Quản lý |
| 3 | Xuất tệp Excel rồi tự tính | Người dùng |

Nấc 3 là van xả cuối. **Điều kiện: nút xuất phải xuất đúng dữ liệu đang hiện, kèm bộ lọc đang bật.** Nếu luôn xuất toàn bộ thì van xả mất tác dụng.

---

## Lý do

**Không chọn A vì mất cấu trúc dữ liệu.** Thư viện bảng tính lưu toàn bộ nội dung trong một khối JSON. Nghĩa là không truy vấn được, không thống kê tự động được, không phân quyền theo dòng được. Mà báo cáo tổng hợp theo bốn cách nhóm là yêu cầu chính của khách hàng.

**Không chọn B vì thiếu van xả.** Người dùng cần tạo được cột tính riêng khi phát sinh nhu cầu mới, không phải gọi người phát triển mỗi lần.

**Chọn C vì phù hợp với dữ liệu thật.** Mười một công thức hiện có đều là phép chia và phép đếm — nằm trong danh sách mười hai phép tính. Và hệ thống vẫn hiểu cột đó là gì, nên thống kê vẫn chạy.

---

## Hệ quả

**Được gì**

- Dữ liệu có cấu trúc, truy vấn và thống kê được
- Phân quyền tới từng dòng và từng cột
- Toàn quyền tuỳ chỉnh giao diện và hành vi
- Nhẹ, không phụ thuộc thư viện lớn bên ngoài

**Mất gì**

- Người dùng không gõ được cú pháp Excel
- Không có thao tác quen tay như kéo góc ô, gộp ô, định dạng màu
- Phép tính lồng nhau nhiều tầng không làm được

**Chỗ cần cẩn thận về sau**

- Nút xuất Excel phải xuất đúng dữ liệu đang hiện kèm bộ lọc
- Danh sách mười hai phép tính cần đủ, thiếu thì người dùng phải xuất ra Excel liên tục
- Cột tính phải tính lại khi cột nguồn thay đổi

---

## Điều kiện xem lại

Xem lại khi có một trong ba dấu hiệu:

- Người dùng xuất tệp Excel nhiều hơn hai lần mỗi ngày để tự tính
- Có nhu cầu phép tính lồng nhau hoặc tra cứu chéo bảng
- Người dùng yêu cầu thao tác quen tay của Excel nhiều lần

Nếu xem lại và thấy cần công thức tự do, cân nhắc thư viện engine công thức thuần thay vì thư viện bảng tính đầy đủ — vì nó chỉ lo phần tính toán, không đụng tới cách lưu dữ liệu.
