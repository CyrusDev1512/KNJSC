# ADR-028 — Solarpunk Office và chế độ tập trung lưới

Ngày: 14.09.2026. Chủ dự án duyệt toàn bộ kế hoạch triển khai trong task UI.
Phạm vi: nhánh thử nghiệm `codex/ui-solarpunk`, chưa đưa vào bản đang vận hành.

## Quyết định thay thế

Trong nhánh UI, thay phần nhận diện/khung của ADR-005, ADR-011 và ADR-015
bằng Solarpunk Office sáng mặc định: xanh rừng, sage, kem, vàng nhạt.
Giữ lựa chọn sáng/tối đã lưu. Không thay phạm vi dữ liệu, quyền, nghiệp vụ,
cây thư mục CRM, đường quay lại lưới hoặc quy tắc lưu của ADR-021.
Django Admin `/quan-tri/` không nằm trong thay đổi.

ERP dùng header gọn và dock nhóm phía dưới. Dock có phần bố cục riêng;
nội dung cuộn trong vùng đọc, không nằm dưới dock. Nhóm dùng `details/summary`
nguyên bản, hỗ trợ bàn phím, Esc và đóng khi bấm ngoài. Mọi liên kết vẫn lấy
từ `nav_groups` có kiểm quyền. CRM giữ cây điều hướng bên trái thu gọn được.

Lịch sử báo cáo có vùng đọc trái và danh sách phải trên desktop. Màn hình
hẹp xếp danh sách trước vùng đọc. HTMX lấy đúng trang chi tiết hiện có,
chỉ chọn vùng `sp-report-content`; URL chi tiết vẫn hoạt động khi không có JS.
Không tạo endpoint mới hoặc truy vấn báo cáo ngoài phạm vi hiện hành.

## Chế độ tập trung

Nút Toàn màn hình trên cả hai lưới bật chế độ trong tab, không phụ thuộc
Fullscreen API. Header, toolbar, chip, footer và thanh công thức lưới thường
ẩn đi. Lưới master không có thanh công thức.

Cụm Công cụ / trạng thái lưu / Thoát chiếm một hàng 36px riêng. Công cụ
mở lại chính DOM toolbar đang có. Trạng thái lưu là cùng một node được
chuyển giữa header và cụm tập trung; không sao chép logic hoặc nội dung.
Ẩn thanh trình duyệt là lựa chọn riêng, vẫn dùng API nguyên bản nếu hỗ trợ.

Esc ưu tiên trình sửa ô, popup, menu hay thao tác hiện có. Nếu không còn lớp
đó, Esc đóng công cụ đang mở; Esc tiếp theo thoát tập trung. Không tải lại,
thay lưới, xóa vùng chọn, nháp RAM, hoàn tác, bộ lọc hoặc hàng đợi lưu.
Thông báo lỗi/xung đột giữ vùng hiển thị riêng.

## Chất liệu và ranh giới

Ảnh nền kiến trúc/cây xanh không chứa UI/chữ/logo: WebP 158.796 byte,
lưu tại `app/static/img/solarpunk-office.webp`. Logo dùng tài nguyên hiện có.
Kính mờ giới hạn ở khung, dock và sidebar; không chạy blur trên ô bảng.
Màu/định dạng ô do người dùng đặt và kích thước hàng/cột không bị ghi đè.

## Kiểm chứng

Xem [hồ sơ triển khai và kiểm chứng](../kiem-chung-solarpunk-20260914.md).
Preview dùng Compose riêng, database/volume/cookie riêng, ERP 18020, CRM 18021.
Không commit/push/merge hoặc thay dịch vụ 8020/8021 trong tác vụ này.
