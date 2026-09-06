# ADR-014 — Bảng dữ liệu ở KN ERP chỉ để xem với mọi bảng; sửa số liệu là việc của KN CRM

| Mục | Nội dung |
|---|---|
| Trạng thái | Đã áp dụng |
| Ngày | 06.09.2026 |
| Người quyết định | Anh/chị chủ dự án, qua hai câu hỏi ngày 06.09.2026 |
| Thay thế cho | **ADR-009 mục 4** ("các bảng khác vẫn sửa ô như cũ") · **ADR-010 mục 1** phần "bảng khác sửa được ở cả hai" · **ADR-013 mục 2** phần ô chọn và "Thêm mới…" trong ô Bảng dữ liệu · **ADR-005** câu "HTMX làm được… sửa từng ô" |
| Liên quan | ADR-012 (KN CRM là app riêng) · FR-7.4 · FR-7.13 · AC-7.4 · AC-11.7 · backlog Q26, Q42, Q62, K26 · `CLAUDE.md` luật 13 |

---

## Bối cảnh

Từ Giai đoạn 3 (FR-7.4) Bảng dữ liệu của KN ERP cho sửa ô tại chỗ: bấm vào ô,
gõ, Enter là lưu. Khi làm Bảng tính vận đơn (ADR-009, Q42) chỉ **bảng vận đơn**
được chốt là chỉ xem ở Bảng dữ liệu — bằng danh sách `GRID_ONLY_TABLES` trong
settings — vì lúc đó chỉ bảng này có lưới. ADR-010 mở lưới cho mọi bảng nhưng
mục 1 vẫn ghi "bảng khác sửa được ở cả hai"; ADR-012 tách KN CRM thành app riêng
và nói "Bảng dữ liệu trong ERP từ đầu chỉ để xem nhanh" nhưng không gỡ đường sửa
ô; ADR-013 còn đặt ô chọn có "＋ Thêm mới…" ngay trong ô Bảng dữ liệu.

Ngày 06.09.2026 anh/chị thấy Báo cáo Marketing sửa được ô trên Bảng dữ liệu và
hỏi: *"chẳng phải đã nói trước đó bảng dữ liệu chỉ để xem thôi sao? edit số là
để bên KN CRM, ghi cái này vào chỗ nào đó của project để sau này đừng mắc lại
nữa"*, rồi: *"với vận đơn thì không bị chỉnh sửa nhưng với báo cáo marketing thì
có?"*. Câu trả lời thật: hai luật sống song song vì mỗi quyết định trước chỉ sửa
một phần, và đợt KNERP đầu tiên không nêu mâu thuẫn ra. Anh/chị hỏi thêm gỡ hết
dấu vết sửa ô có làm hệ thống nhẹ đi không — trả lời: không bớt dữ liệu, tính
toán khi ghi vẫn chạy ở KN CRM bằng cùng bộ mã; chỉ nhẹ ở mã và ở trang bảng có
cột chọn. Lý do đúng để gỡ là **một cửa ghi duy nhất**: bớt một đường ghi phải
bảo vệ và kiểm thử, ERP và KN CRM không còn hai cách sửa lệch nhau. Anh/chị chọn
**gỡ hết**.

## Quyết định

1. **Bảng dữ liệu ở KN ERP chỉ để xem, với mọi bảng và mọi cấp bậc** — kể cả
   người tạo dòng, người được cấp quyền Sửa và Admin. Không phụ thuộc danh sách
   bảng nào: không có ô sửa, không có đường sửa ô. Đầu mỗi bảng có dòng báo
   "Bảng này chỉ để xem" và nút **Mở trong KN CRM** trỏ đúng bảng đó.
2. **Sửa số liệu là việc của KN CRM** (lưới ở dịch vụ `bangtinh`, cổng 8021).
   Tầng dịch vụ dùng chung không đổi: `record_service.update_cell`,
   `update_cells`, `parse_value`, `grant_service.can_edit_record`, sổ danh sách
   `choice_registry`. Mọi quy tắc nghiệp vụ khi ghi (kiểu, danh sách chọn, cột
   tính sẵn, nhật ký BR-5) vẫn kiểm ở đó.
3. **Gỡ hẳn phía ERP**, không chỉ ẩn nút: view `bang_sua_o` và đường dẫn
   `bang/<mã>/o/<pk>/<cột>/` (gọi vào trả 404), template `_o.html`, khối script
   sửa ô trong `bang_xem.html`, tham số `editable` của `styling.cell_class`,
   `choice_service.attach_lists`, handler cho phép HTMX thay ô 400 trong
   `chon.js`, CSS `o-loi-ly-do`. `bang_xem` không còn tính quyền sửa từng dòng.
4. **`GRID_ONLY_TABLES` và `is_grid_only` giữ lại cho KN CRM** — lưới dùng để
   báo chỉ xem và bảy tệp kiểm thử của `crm` dựa vào nó; ở dịch vụ `bangtinh`
   danh sách đã rỗng. KN ERP không đọc nó nữa. Bỏ hẳn hay không là việc của
   thread KN CRM (K26).
5. **Ghi thành luật** để không lặp lại: `CLAUDE.md` mục "Không được làm" dòng 13;
   FR-7.4, AC-7.4, AC-11.7 viết lại theo luật mới; `docs/05` mục A4 và `docs/07`
   theo đó.

## Đã cân nhắc và bỏ

| Phương án | Vì sao bỏ |
|---|---|
| Giữ sửa ô cho các bảng không phải vận đơn, chỉ ghi chú | Chính là tình trạng gây nhầm; hai cửa ghi cho cùng dữ liệu |
| Thêm mọi bảng vào `GRID_ONLY_TABLES` (chỉ xem bằng cấu hình) | Đường sửa ô vẫn tồn tại, một dòng cấu hình đổi là mở lại; trái ý "gỡ hết dấu vết" |
| Ẩn nút, giữ đường dẫn trả 403 | Vẫn là mã phải bảo vệ và kiểm thử; không ai cần nó |
| Bỏ luôn `GRID_ONLY_TABLES` ở lượt này | Phải sửa `app/crm/` và bảy tệp kiểm thử của thread KN CRM — ghi K26 cho thread đó |
| Chuyển khối CSS `.o-sua` từ `main.css` sang `bang-tinh.css` | Đổi thứ tự cascade của lưới KN CRM; giữ nguyên chỗ, chỉ đổi chú thích |

## Hệ quả

| Được | Mất hoặc phải làm |
|---|---|
| Một cửa ghi duy nhất; ERP và KN CRM không lệch nhau về quyền sửa | Người quen sửa nhanh trên Bảng dữ liệu phải sang KN CRM (một cú bấm) |
| Bớt một view, một template, một đường dẫn, một khối script, một nhánh CSS phải kiểm | 14 bài kiểm thử viết lại thành bài chỉ xem và bài gọi thẳng `update_cell` |
| Trang bảng gọn hơn ở bảng có cột chọn (không lặp hộp chọn mỗi dòng) | Hiệu năng không đổi đáng kể — đây không phải lý do của quyết định |
| Luật ghi ở `CLAUDE.md`, FR, AC, ADR — phiên sau không mắc lại | ADR-009, 010, 013, 005 mang dấu "đã được thay" |
