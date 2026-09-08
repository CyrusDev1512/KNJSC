---
version: 1
slug: "app-templates-base-html"
primary_target: "app/templates/base.html"
related_targets: ["app/templates/crm/base_bang_tinh.html","app/static/css/tokens.css","app/static/css/main.css","app/static/css/bang-tinh.css"]
---

# KNJSC — vỏ ứng dụng (KN ERP + KN CRM)

Phạm vi: toàn bộ khung và thành phần giao diện của hai app, chế độ Operate. Người dùng: nhân viên ba bộ phận, cả ngày trên máy tính ở văn phòng; điện thoại phụ.

## Direction contract

THESIS: Chuẩn ngành theo Google Workspace và Google Sheets, chơi thẳng, không cài chất riêng: một công cụ nội bộ quen tay như Sheets nhưng gọn và nhất quán hơn tệp Excel đang dùng. Từ chối: khung tối viền vàng của KN Demo, gradient, kính mờ, thẻ nổi.

OWN-WORLD: nền trắng và xám #f8f9fa, chữ #202124 / #5f6368, một xanh #1a73e8 với nền chọn #e8f0fe, viền #dadce0, bo 8px cho thẻ và 4px cho nút, Roboto 13–14px, số tabular; chip trạng thái nền nhạt chữ đậm; lưới KN CRM trắng, viền #e2e3e3, chọn ô xanh 2px có tay kéo, tiêu đề cột xám nhạt, tab trang kiểu Sheets.

STORY: mở lên là biết chỗ nào để làm việc hôm nay, mọi thứ ở đúng chỗ của Google; số liệu và trạng thái đọc ngay, không phải học.

FIRST VIEWPORT: thanh bên trắng 256px mục bo tròn có biểu tượng, thanh trên trắng có ô tìm xám, tiêu đề trang 22px, bốn ô số trắng viền xám, bảng đơn hàng viền ngang mảnh; nút chính xanh góc phải.

FORM: canon (lối ra chuẩn ngành), người dùng chọn 07.09.2026 trên bàn chọn sau hai vòng gieo; seed 3cfcb7ed.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance.
