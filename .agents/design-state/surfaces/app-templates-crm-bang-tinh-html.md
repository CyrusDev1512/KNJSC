---
version: 2
slug: "app-templates-crm-bang-tinh-html"
primary_target: "app/templates/crm/master_grid.html"
related_targets: ["app/templates/crm/statistics.html","app/static/css/master-grid.css","app/static/js/master-grid.js","app/static/css/bang-tinh.css"]
---

# Vận đơn mới — file master, Operate

ADR-021 thay hợp đồng bố cục cũ ngày 10.09.2026. Chỉ van_don_moi; lưới cũ giữ nguyên.

## Direction contract

THESIS: File master giúp cuộn kiểm tình trạng giao và đọc/sửa nội dung nhanh, bằng thao tác cơ bản quen từ Excel.

OWN-WORLD: Giữ khung KN CRM và lưới kem của bảng cũ; header chữ/tên cột, số dòng, hàng mặc định 28px, tay nắm ở số hàng kéo 28–400px và xuống dòng (ADR-021 bổ sung). Không tiêu đề nhóm xanh, Vận hành đơn, thanh công thức hoặc thống kê nhúng.

STORY: Chọn ô → đọc chữ dài trong vùng nổi → F2/bấm đúp sửa nếu có quyền → trạng thái lưu rõ. Phân công và chi tiết dùng hộp chuyên dụng. Thống kê là trang riêng có bộ lọc chuyển qua lại.

FIRST VIEWPORT: Topbar hiện có, toolbar gọn, toàn bộ phần còn lại cho lưới cuộn ảo. Chỉ DOM vùng nhìn; popup không đổi kích thước hàng/cột. Mobile cuộn trong lưới, không làm tràn trang.

FORM: Trang Thống kê dùng token neutral/indigo của KN CRM, hai donut và hai biểu đồ cột SVG. Nhãn/chú giải và bảng đối chiếu có phân trang. Tiền tệ tách riêng, thiếu chi tiết được giải thích.

FINISH: Kiểm desktop/mobile, bàn phím, chữ dài và ảnh chụp thực tế. Evidence local tại `.agents/design-state/review/master`; kết quả và giới hạn ở `docs/test-log.md`. Không thêm raster hoặc dependency.
