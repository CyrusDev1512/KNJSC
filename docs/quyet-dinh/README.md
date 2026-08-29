# Nhật ký quyết định kiến trúc

Thư mục này ghi lại các quyết định kỹ thuật quan trọng kèm lý do.

---

## Vì sao cần

Mã nguồn cho biết **đã làm gì**. Thư mục này cho biết **vì sao không làm cách khác**.

Sáu tháng sau, khi có người hỏi *"sao không dùng thư viện X cho nhanh"*, câu trả lời
nằm ở đây thay vì phải nhớ lại hoặc tranh luận lại từ đầu.

---

## Quy tắc

| # | Quy tắc |
|---|---|
| 1 | **Không sửa mục đã ghi.** Đổi ý thì ghi mục mới, đánh dấu mục cũ là đã được thay thế |
| 2 | Mỗi mục một tệp, đánh số tăng dần |
| 3 | Tên tệp: `số-thứ-tự-mô-tả-ngắn.md`, ví dụ `001-chon-co-so-du-lieu.md` |
| 4 | Ghi ngay khi quyết định, không để sau |

Giá trị của tài liệu này nằm ở chỗ nó cho thấy **suy nghĩ tại thời điểm quyết định**,
không phải ở chỗ nó luôn đúng.

---

## Khi nào cần ghi một quyết định

Ghi khi có ít nhất một trong ba dấu hiệu:

| Dấu hiệu | Ví dụ |
|---|---|
| Khó đảo ngược | Chọn cơ sở dữ liệu, chọn cách tổ chức phân quyền |
| Có nhiều lựa chọn hợp lý | Tự viết hay dùng thư viện có sẵn |
| Sau này sẽ có người hỏi vì sao | Vì sao không dùng công cụ phổ biến hơn |

**Không cần ghi** những quyết định nhỏ, dễ đổi, hoặc chỉ có một cách làm.

---

## Mẫu

Sao chép nội dung dưới đây khi tạo mục mới.

```markdown
# ADR-00x — Tiêu đề ngắn nêu quyết định

| Mục | Nội dung |
|---|---|
| Trạng thái | Đề xuất / Đã áp dụng / Cần xem lại / Đã bị thay thế |
| Ngày | |
| Người quyết định | |
| Thay thế cho | ADR-00y (nếu có) |

## Bối cảnh

Tình huống dẫn tới việc phải quyết định. Nêu ràng buộc và thông tin
đã có tại thời điểm đó.

## Các lựa chọn đã cân nhắc

| Lựa chọn | Ưu | Nhược |
|---|---|---|
| A | | |
| B | | |
| C | | |

## Quyết định

Chọn phương án nào.

## Lý do

Vì sao chọn phương án đó, và vì sao loại các phương án khác.

## Hệ quả

**Được gì:**

**Mất gì:**

**Chỗ cần cẩn thận về sau:**

## Điều kiện xem lại

Trong tình huống nào thì nên xem lại quyết định này.
```

---

## Danh sách quyết định

| Số | Tiêu đề | Trạng thái | Ngày |
|---|---|---|---|
| 001 | Bảng động lưu dạng JSON, cộng cột tách cho nhãn ý nghĩa | Đã áp dụng | (điền) |
| 002 | Không nhúng thư viện bảng tính bên ngoài | Đã áp dụng | (điền) |
| 003 | Cấp bậc và bộ phận là hai cột riêng | Đã áp dụng | (điền) |
| 004 | CRM là module trong monolith, tách thành ứng dụng riêng khi đạt điều kiện | Đã áp dụng | (điền) |
| 005 | Chọn Django làm khung ứng dụng | Đã áp dụng | (điền) |
| 006 | Bảng dữ liệu chỉ có cột tính sẵn, công thức tự do tách sang Bảng tính | Đã áp dụng | 29.08.2026 |
| 007 | Biểu mẫu luôn chọn bảng có sẵn, và chốt bảy nhãn ý nghĩa | Đã áp dụng | 29.08.2026 |
| 008 | Báo cáo hằng ngày bọc quanh biểu mẫu, không tự giữ nội dung | Đã áp dụng | 29.08.2026 |

---

## Quyết định đang chờ

Những điểm sẽ cần ghi lại khi chốt. Chi tiết ở `../backlog.md`.

| Nội dung | Mã trong backlog |
|---|---|
| Cách triển khai bảng dữ liệu và công thức | K1 |
| Tạo biểu mẫu thì tự sinh bảng hay chọn bảng có sẵn | K2 |
| Danh sách nhãn ý nghĩa cho cột | K3 |
| Khung ứng dụng | K4 |
