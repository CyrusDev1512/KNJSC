# ADR-004 — CRM là module trong monolith, tách thành ứng dụng riêng khi đạt điều kiện

| Mục | Nội dung |
|---|---|
| Trạng thái | Đã áp dụng |
| Ngày | (điền ngày) |
| Người quyết định | (điền tên) |

---

## Bối cảnh

Phần bán hàng — khách hàng, đơn hàng, sản phẩm — là mảng có khả năng chịu tải nặng nhất trong hệ thống. Nó cũng là mảng có thể tách ra bán riêng cho khách hàng khác về sau.

Câu hỏi: tách thành ứng dụng riêng ngay từ đầu, hay để trong monolith rồi tách sau?

---

## Các lựa chọn đã cân nhắc

| Lựa chọn | Ưu | Nhược |
|---|---|---|
| **A — Tách ngay** | Cô lập tải · Triển khai riêng · Bán riêng được | Phát sinh đăng nhập chung · Nhân sự phải đồng bộ hai nơi · Báo cáo tổng hợp gọi API thay vì truy vấn thẳng · Triển khai và kiểm thử hai lần |
| **B — Module trong monolith** | Đơn giản nhất · Truy vấn thẳng · Một lần triển khai | Không cô lập tải · Không triển khai riêng |
| **C — Module bây giờ, chuẩn bị để tách sau** | Đơn giản như B · Tách được khi cần mà không viết lại | Tốn thêm ít công cho lớp trung gian |

---

## Quyết định

**Chọn C — module trong monolith, chuẩn bị sẵn để tách.**

### Ba việc chuẩn bị, làm ngay từ đầu

| Việc | Tốn thêm |
|---|---|
| `crm` không truy vấn trực tiếp bảng của module khác, đi qua tầng dịch vụ | 0 |
| Mọi truy vấn xuyên module đi qua một lớp trung gian | ít |
| Bảng của `crm` không có khoá ngoại cứng sang module khác | 0 |

Ba việc này khiến lần tách sau chỉ là đổi lời gọi hàm thành gọi API, không phải viết lại logic.

### Bốn điều kiện tách

Không tách theo lịch. Tách khi **đo được** một trong bốn dấu hiệu:

```
CPU máy chủ vượt 70% liên tục trong giờ làm việc
Thao tác của bộ phận khác chậm đi khi CRM chạy nặng
Tác vụ nền của CRM chiếm hết hàng đợi
CRM cần lịch cập nhật riêng, không cùng nhịp với phần còn lại
```

---

## Lý do

**Không chọn A vì tách sớm tốn hơn không tách.** Với khối lượng dữ liệu hiện tại, chưa có gì để cô lập. Tách ngay thì phải giải bốn bài toán phát sinh — đăng nhập chung, đồng bộ nhân sự, gọi API cho báo cáo, triển khai hai lần — mà không đổi lại lợi ích nào đo được.

**Không chọn B vì mất khả năng tách.** Nếu để module gọi chéo bảng của nhau thoải mái, thì tới lúc cần tách phải viết lại phần lớn.

**Chọn C vì chi phí chuẩn bị nhỏ hơn nhiều so với chi phí tách lại từ đầu.**

---

## Hai điều cần biết trước khi tách

**Cô lập lỗi không đến từ việc tách ứng dụng.** Tách cô lập được lỗi hạ tầng — CPU cao, ứng dụng sập, cần khởi động lại. Không cô lập được lỗi logic: sai phân quyền, sai dữ liệu, rò rỉ thông tin. Những lỗi đó theo mã nguồn, không theo tiến trình.

**Chịu tải là chuyện của cơ sở dữ liệu, không phải tầng ứng dụng.** Tách ứng dụng sang máy chủ khác mà vẫn dùng chung một cơ sở dữ liệu thì nút thắt không đổi. Muốn tách tải thật thì phải tách cả cơ sở dữ liệu — và lúc đó báo cáo tổng hợp phải gọi API thay vì truy vấn thẳng, đó là chỗ tốn nhất.

---

## Bảng tính trong CRM sau khi tách

Khi tách thành ứng dụng riêng, CRM có thêm màn hình bảng tính tự do:

```
crm/khach-hang     bảng cố định — nguồn dữ liệu chính
crm/don-hang       bảng cố định — nguồn dữ liệu chính
crm/bang-tinh      bảng tính tự do — nơi người dùng tự tính toán
```

**Ranh giới bắt buộc: bảng tính không phải nguồn dữ liệu.** Nó đọc từ bảng cố định, người dùng thao tác trên đó, kết quả không ghi ngược lại.

Nếu để bảng tính ghi ngược thì mất cấu trúc dữ liệu, và quay lại đúng vấn đề của cách làm bằng Excel hiện tại.

---

## Hệ quả

**Được gì**

- Triển khai đơn giản ở giai đoạn đầu
- Truy vấn thẳng, báo cáo tổng hợp không phải gọi API
- Tách được khi cần mà không viết lại logic

**Mất gì**

- Chưa cô lập được tải giữa CRM và phần còn lại
- Cập nhật hệ thống thì toàn bộ cùng dừng

**Chỗ cần cẩn thận về sau**

- Ba việc chuẩn bị phải làm ngay, không để sau — làm sau thì phải sửa lại nhiều chỗ
- Cần theo dõi bốn dấu hiệu để biết khi nào tách, không đợi tới lúc hệ thống chậm rõ rệt

---

## Điều kiện xem lại

Xem lại khi đạt một trong bốn dấu hiệu ở trên, hoặc khi có nhu cầu bán riêng phần bán hàng cho khách hàng khác.
