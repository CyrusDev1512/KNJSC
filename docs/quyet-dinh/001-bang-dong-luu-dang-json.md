# ADR-001 — Bảng động lưu dạng JSON, tách cột riêng cho trường có nhãn ý nghĩa

| Mục | Nội dung |
|---|---|
| Trạng thái | Đã áp dụng |
| Ngày | (điền ngày) |
| Người quyết định | (điền tên) |

---

## Bối cảnh

Kim Ngân bán ở nhiều thị trường, mỗi thị trường cần trường dữ liệu khác nhau. Quản lý phải tự tạo được biểu mẫu và bảng cho thị trường mới mà không cần người phát triển can thiệp.

Nghĩa là cấu trúc dữ liệu không biết trước lúc viết mã.

Nhưng hệ thống vẫn phải thống kê được — báo cáo tổng hợp theo bốn cách nhóm là yêu cầu chính của khách hàng.

Hai yêu cầu này chống nhau: linh hoạt thì hệ thống không hiểu dữ liệu, hệ thống hiểu dữ liệu thì phải cố định cấu trúc.

---

## Các lựa chọn đã cân nhắc

| Lựa chọn | Ưu | Nhược |
|---|---|---|
| **A — Lưu trong cột JSON** | Không đổi cấu trúc cơ sở dữ liệu · Thêm cột là ghi thêm khoá · Không cần chuyển đổi cấu trúc | Truy vấn chậm hơn bảng cố định · Không có ràng buộc kiểu ở tầng dữ liệu |
| **B — Sinh bảng thật lúc chạy** | Truy vấn nhanh nhất · Có ràng buộc kiểu | **Người dùng bấm nút thì cấu trúc cơ sở dữ liệu thay đổi** · Chuyển đổi cấu trúc phức tạp · Rủi ro cao với hệ thống một người vận hành |
| **C — Bảng khoá và giá trị** | Linh hoạt tuyệt đối | Mỗi ô là một dòng · Truy vấn rất chậm · Đọc một bản ghi cần nối bảng nhiều lần |

---

## Quyết định

**Chọn A — lưu trong cột JSON**, kèm một bổ sung: mỗi cột do người dùng tạo có thể gán một **nhãn ý nghĩa**, và cột có nhãn được tách ra cột riêng có chỉ mục.

```
Cột "Giá bán"       →  nhãn: Doanh thu     →  tách ra cột riêng, cộng tổng được
Cột "Số điện thoại" →  nhãn: Điện thoại    →  tách ra cột riêng, tìm khách cũ được
Cột "Ghi chú riêng" →  không nhãn          →  ở trong JSON, chỉ lưu và hiện
```

Bảy nhãn ý nghĩa: Ngày · Khách hàng · Số điện thoại · Doanh thu · Người bán · Sản phẩm · Trạng thái.

---

## Lý do

**Không chọn B vì rủi ro không tương xứng với lợi ích.** Người dùng bấm nút thì hệ thống chạy lệnh đổi cấu trúc cơ sở dữ liệu. Với hệ thống mà một người vận hành, một lệnh sai là hỏng dữ liệu và không có ai xử lý ngay. Airtable và NocoDB làm cách này, nhưng họ có đội vận hành riêng.

**Không chọn C vì quá chậm.** Đọc một bản ghi hai mươi cột cần hai mươi dòng, và mọi truy vấn đều phải nối bảng. Với 5.000 bản ghi mới mỗi tháng thì nó hỏng nhanh.

**Chọn A vì quy mô cho phép.** Với khối lượng dữ liệu dự kiến, JSON không phải nút thắt. Và phần nhãn ý nghĩa giải được vấn đề thống kê — cột quan trọng vẫn có chỉ mục riêng.

---

## Hệ quả

**Được gì**

- Người dùng tự tạo bảng và cột, không cần người phát triển
- Cấu trúc cơ sở dữ liệu không đổi khi người dùng thao tác
- Báo cáo tổng hợp vẫn chạy được trên cột có nhãn ý nghĩa
- Không cần chuyển đổi cấu trúc khi thêm hoặc bỏ cột

**Mất gì**

- Truy vấn trên cột không có nhãn chậm hơn bảng cố định
- Không có ràng buộc kiểu ở tầng cơ sở dữ liệu, phải kiểm ở tầng ứng dụng
- Cột không có nhãn thì không thống kê tự động được

**Chỗ cần cẩn thận về sau**

- Danh sách nhãn ý nghĩa phải cố định trong mã nguồn, không cho người dùng tự thêm nhãn mới
- Khi cột được gán nhãn, phải chuyển dữ liệu cũ từ JSON sang cột tách ra
- Cần chỉ mục GIN trên cột JSON để lọc theo cột không có nhãn không quá chậm

---

## Điều kiện xem lại

Xem lại quyết định này khi có một trong ba dấu hiệu:

- Truy vấn trên bảng động vượt 2 giây với dưới 50.000 bản ghi
- Người dùng cần hơn mười lăm nhãn ý nghĩa
- Số lượng bảng động vượt năm mươi bảng
