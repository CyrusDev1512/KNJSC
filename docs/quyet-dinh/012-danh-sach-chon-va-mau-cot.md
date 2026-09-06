# ADR-012 — Danh sách chọn và màu cột là thuộc tính của cột, Manager quản lý; danh tính người điền do hệ thống ghi

| Mục | Nội dung |
|---|---|
| Trạng thái | Đã áp dụng |
| Ngày | 06.09.2026 |
| Người quyết định | Anh/chị chủ dự án, qua bốn câu hỏi ngày 06.09.2026 |
| Liên quan | ADR-001 · ADR-007 · ADR-009 (sổ danh sách) · ADR-010 (định dạng từng ô) · FR-4.6 · FR-6.8 · FR-8.7 → FR-8.9 · backlog Q54 → Q57, K22 |

---

## Bối cảnh

Sau khi Bảng tính (KN CRM) tách thành thread riêng, anh/chị yêu cầu bốn chỉnh
sửa cho hệ thống chính (KNERP), kèm ảnh bảng "Dữ liệu chi phí Ads":

> *Mọi chỗ chọn lựa phải là dropdown có tuỳ chọn thêm; sản phẩm chọn từ danh
> mục, Manager thêm. Chỗ cần danh tính người điền thì hệ thống tự chọn tài
> khoản. Bảng dữ liệu tô vàng, đỏ các chỉ số quan trọng như ảnh, tiêu đề xanh.
> Bảng dữ liệu phải có viền ô.*

Ba chỗ hở trong mã lúc đó: cột *Chọn một* của bảng tự tạo không có chỗ lưu
danh sách (backlog K22) nên ai gõ gì cũng nhận; trường Marketer là ô chữ tự do,
dữ liệu mẫu ghi tên không trùng tài khoản nào; Bảng dữ liệu chỉ có viền ngang,
không có cách nào tô màu theo cột.

Bốn câu hỏi được chốt cùng ngày:

| Câu hỏi | Chốt |
|---|---|
| Ai thêm giá trị vào danh sách chọn | **Manager quản lý, Staff chỉ chọn** |
| Danh tính ghi dạng gì | **Họ tên**, thiếu thì tên đăng nhập — cùng luật với bảng vận đơn |
| Tô màu theo cách nào | **Màu cột + ngưỡng cảnh báo** (đỏ khi lớn hơn / nhỏ hơn X, còn lại xanh lá) |
| Tiêu đề mặc định | **Xanh lá cố định** |

---

## Quyết định

1. **Danh sách chọn ba tầng, phân giải ở một chỗ** — `choice_registry.for_column`:
   sổ `(bảng, cột)` do `crm` đăng ký (ADR-009) luôn thắng → sổ theo **nhãn ý
   nghĩa** (Sản phẩm = danh mục sản phẩm, chặt, có thêm — `orders` đăng ký;
   Người bán = nhân sự bộ phận sở hữu bảng, gợi ý — `forms_builder` tự đăng ký)
   → `ColumnDef.options` (chặt, Manager gõ trong Sửa cột). Hai tầng sau chỉ áp
   cho kiểu *Chọn một*, nên cột kiểu chữ mang nhãn (như `san_pham` trên bảng vận
   đơn) không đổi. Cột *Chọn một* chưa có danh sách **không nhận giá trị nào**.
2. **"＋ Thêm mới…" là một mục trong chính ô chọn**, chỉ hiện cho Admin và Manager
   bộ phận sở hữu bảng. Máy chủ thêm giá trị (vào cột, hoặc vào danh mục sản phẩm
   qua `product_service`) rồi trả về các `<option>`; trình duyệt chép vào mọi ô
   cùng nhóm. Người được cấp quyền Sửa vẫn chỉ chọn.
3. **Danh tính người điền ép ở tầng dịch vụ** (`form_service.fill`), không tin
   yêu cầu gửi lên; giá trị là `core.identity.display_name`. Chỉ áp cho đường
   điền biểu mẫu và nộp báo cáo; nhập tệp và lên đơn giữ nguyên.
4. **Màu cột và ngưỡng là thuộc tính của cột** (`highlight`, `alert_op`,
   `alert_value`), khác cơ chế định dạng từng ô của ADR-010 (vốn là việc của
   người dùng trên Bảng tính). Lớp CSS tính trong Python từ sổ đóng
   (`forms_builder/styling.py`). Tiêu đề xanh lá; viền mọi ô; cả hai chỉ ở bảng
   mang lớp `bang-luoi` để không lan sang danh sách khác và crm.
5. **Manager bất kỳ bộ phận thêm được sản phẩm**; mã tự sinh từ tên (bỏ dấu,
   xử lý chữ Đ), đồng bộ cột `sl_` trên bảng vận đơn ngay trong giao dịch.

---

## Đã cân nhắc và bỏ

| Cách | Vì sao bỏ |
|---|---|
| Ai điền cũng thêm được giá trị | Sinh dữ liệu lộn xộn ("Đã TT", "đã thanh toán", "Đã Thanh Toán") — đúng thứ ô chọn phải ngăn |
| Danh sách trên `FieldDef` thay vì `ColumnDef` | Kiểm khi ghi là theo cột bảng; hai chỗ lưu là hai sổ lệch nhau |
| Ghi tên đăng nhập làm danh tính | Không trùng, nhưng báo cáo hiện mã và lệch với bảng vận đơn đang ghi họ tên |
| Chỉ màu cột, không ngưỡng | Cột CPS trong ảnh đỏ hay xanh tuỳ giá trị — không làm được |
| Ngưỡng lưu như định dạng từng ô (ADR-010) | Ngưỡng là quy tắc cho cả cột, đổi số là đổi màu; định dạng ô là tay người tô |
| Viền cho mọi `table.bang` | Danh sách nhân sự, nhật ký không cần; crm có viền riêng |

---

## Hệ quả

| Được | Mất |
|---|---|
| Nhập liệu thống nhất: trạng thái, kênh, sản phẩm chỉ có một cách viết | Cột Chọn một cũ chưa có danh sách nay từ chối giá trị gõ tay cho tới khi Manager thêm |
| Báo cáo tổng hợp nhóm theo nhân viên đúng người, không theo chuỗi gõ tay | Manager gõ hộ nhân viên thì dòng đó mang tên Manager |
| Bảng dữ liệu đọc như bảng Excel quen thuộc: viền, tiêu đề màu, ô cảnh báo | Thêm bốn cột trên định nghĩa cột (migration 0008) và một module CSS lớp đóng |
| Sản phẩm mới có ngay ở mọi ô chọn và bảng vận đơn | Chưa có màn hình sửa, ngừng bán sản phẩm (S11); Bảng tính chưa đọc sổ mới (K25) |

Tiêu chí nghiệm thu: AC-4.6, AC-6.9, AC-8.7 → AC-8.10. Xem lại khi: có cột cần
danh sách phụ thuộc cột khác; có yêu cầu nhiều hơn bốn màu hay hai ngưỡng; hoặc
người dùng muốn Staff tự thêm giá trị ở một cột cụ thể (thêm cờ trên cột).
