# ADR-019 — Gỡ Lên đơn nhúng khỏi bảng Vận đơn

> Bổ sung 10.09.2026: [ADR-021](021-luoi-master-va-thong-ke-crm.md) thay phần bố cục/renderer và thống kê nhúng của Vận đơn mới. Quyền, dữ liệu và nghiệp vụ không đổi.


Ngày: 09.09.2026. Trạng thái: Đã áp dụng.

## Lý do

Chủ dự án xác nhận form Lên đơn trong bảng Vận đơn là thừa vì KN CRM và
KN ERP đều đã có trang Lên đơn riêng. Giữ phần thống kê trong bảng.

## Quyết định

- `/bang-tinh/van_don_moi/` chỉ có lưới Vận hành đơn và Thống kê; không chứa
  form, vùng giữ chỗ hoặc yêu cầu HTMX tải form Lên đơn.
- Giữ trang Lên đơn riêng CRM `/van-don/len-don/` và trang ERP `/len-don/`.
  Cả hai vẫn tạo đơn qua cùng service và ghi bản sao vào `van_don_moi`.
- Bỏ tín hiệu tạo đơn yêu cầu tải lại bảng; giữ tín hiệu sửa chi tiết cập nhật
  lưới/thống kê. Template và điều khiển sản phẩm dùng chung vẫn được giữ.
- Không đổi quyền: Sale chưa có quyền xem bảng vẫn được chuyển đến trang
  Lên đơn riêng; các endpoint tiếp tục kiểm quyền phía server.
- Không đổi dữ liệu, cấu trúc lưu đơn, bảng đích hoặc khả năng sửa chi tiết.
  Yêu cầu giới hạn Vận đơn chỉ cập nhật giao hàng/thu tiền là đầu việc riêng.

## Thay thế và kiểm chứng

Thay thế riêng bố cục ba khu trong ADR-018 và Q79; các quyết định khác giữ
nguyên. AC-18.8 được cập nhật để kiểm lưới/thống kê không có form nhúng.
Kiểm hồi quy bằng `pytest crm/tests orders/tests`; kiểm trình duyệt đọc local
bằng `node scripts/kiem-thu-van-don-ui.cjs`, không ghi đơn vào database local.

Kết quả: 135 bài đạt; Chrome desktop 1440px/mobile 390px đạt. Script dùng GET
để thay form, mô phỏng tín hiệu lưu chi tiết để kiểm lưới/thống kê; thao tác ghi
thật được kiểm trên database test. Dữ liệu mẫu local không thay đổi.
