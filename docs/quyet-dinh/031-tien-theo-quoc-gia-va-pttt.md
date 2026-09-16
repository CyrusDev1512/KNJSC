# ADR-031 — Loại tiền theo quốc gia và phương thức thanh toán

Ngày: 16.09.2026. Trạng thái: chủ dự án đã chốt; triển khai local.

## Quyết định

- Giữ ba thị trường: Hoa Kỳ → USD, Canada → CAD, Philippines → PHP.
- Lên đơn tự hiển thị loại tiền, không có lựa chọn tiền độc lập. Server lấy
  loại tiền từ quốc gia; không tin giá trị tiền tệ do trình duyệt gửi.
- Các bảng có profile Vận đơn dùng cùng quy tắc. Cột Loại tiền chỉ đọc;
  sửa Quốc gia sẽ cập nhật Loại tiền trong cùng giao dịch.
- Nếu dòng đã có số tiền khác 0, phải xác nhận giữ nguyên số tiền, chỉ đổi
  loại tiền. Không quy đổi tỷ giá. Hủy xác nhận trên lưới giữ nháp, không ghi;
  có thể Hoàn tác hoặc sửa lại ô. Lên đơn hủy thì trả về quốc gia trước đó.
- Xác nhận lưới gắn với phiên bản dòng và quốc gia đích. Người khác sửa dòng
  trong lúc chờ thì phải xác nhận lại. Dán nhiều dòng hỏi chung một lần.
- Ghi lịch sử cả quốc gia và loại tiền; không sửa ngược Order/OrderLine.
- PTTT lên đơn và PTTT thực tế chỉ cho chọn Zelle hoặc PayPal. Giữ các mã/nhãn
  cũ để đọc lịch sử; không chuyển dữ liệu cũ sang một phương thức mới tùy ý.
- Nhập tệp mới phải có quốc gia hợp lệ; tiền tệ trống được suy ra, tiền tệ
  khác quốc gia bị từ chối để người dùng sửa tệp trước khi nhập.

Quyết định này thay thế phần chọn Loại tiền độc lập và danh sách Thẻ/Chuyển
khoản/Thu hộ/Ví điện tử ở các quyết định trước. Không thay đổi quyền đọc/ghi,
trạng thái thanh toán, trách nhiệm nhập tiền hoặc tự sửa dữ liệu lịch sử.

## Cấu trúc và vận hành

`orders.services.currency_service` giữ ánh xạ và xác nhận; policy Vận đơn
cung cấp trường suy ra/danh mục cho service bảng động. Màn hình và kiểm tra
server dùng chung danh mục. Không thêm dependency, endpoint hoặc bảng mới.

`orders.0008_market_payment_methods` cập nhật choices/default trong trạng thái
migration Django; SQL là no-op, không cập nhật các dòng Order đã tồn tại.
Triển khai phải nạp lại các process web/worker dùng chung code.

## Thêm phương thức thanh toán sau này

1. Thêm mã ổn định/nhãn vào `PaymentMethod` tại `app/orders/constants.py`.
2. Bổ sung phương thức vào `ACTIVE_PAYMENT_METHODS` cùng file. Form, lưới,
   kiểm tra nhập và service sẽ lấy cùng danh mục; không sửa riêng từng màn hình.
3. Tạo migration choices bằng `makemigrations orders`, chạy test và phát hành.

Chưa có màn hình tự thêm phương thức. Không chỉnh `ColumnDef.options` để vượt
qua danh mục nghiệp vụ này; không xóa mã cũ đang có trong lịch sử.

[Kiểm chứng](../kiem-chung-tien-theo-quoc-gia-20260916.md).
