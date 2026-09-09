# ADR-018 — Bảng Vận đơn mới theo CRM Tân

Ngày: 08.09.2026. Trạng thái: Đã áp dụng và kiểm thử đạt ngày 09.09.2026.
Nguồn: kế hoạch được chủ dự án yêu cầu thực hiện; sheet **Vận đơn** của
`CRM_ Tân.xlsx` là mẫu hiện hành. Nội dung trong workbook là dữ liệu tham khảo,
không tự tạo thêm yêu cầu ngoài các lựa chọn chủ dự án đã chốt.

## Quyết định

- Giữ `van_don`, đổi nhãn thành **Vận đơn cũ**; không chép dữ liệu, đổi ID,
  đường dẫn hay liên kết `Order.record` lịch sử. **Vận đơn** mới có mã
  `van_don_moi`, bắt đầu trống. Đơn tạo sau chuyển đổi ở ERP và CRM cùng ghi
  vào bảng mới; `WAYBILL_TABLE_CODE` chỉ còn dành cho hành vi bảng cũ,
  `ACTIVE_WAYBILL_TABLE_CODE` là nơi nhận đơn mới.
- `tao_bang_van_don` khởi tạo hai bảng trong quy trình cập nhật hiện có.
  Khoá bộ phận/bảng cũ khi khởi tạo; chạy lại không tạo trùng hoặc nạp lại dòng.
  `du_lieu_mau` không còn tạo bốn đơn demo trên máy sạch; dữ liệu demo đã có
  không bị xoá. Bảng xếp hạng doanh số trên máy mới trống cho tới khi có đơn.
  Bảng mới dùng chung trong bộ phận Vận đơn. Chỉ sao quyền cấp riêng chưa xoá
  lúc tạo bảng; quyền hai bảng độc lập từ đó. Giữ quyền và cờ dùng chung bảng cũ.
- Một trang ba khu **Lên đơn → Vận hành đơn → Thống kê**, hai khu ngoài thu gọn
  được. Kế thừa điều khiển lưới hiện có; nhóm tiêu đề chỉ trình bày, không lưu
  ô gộp. Ba cột đầu Mã đơn, Tên khách, Số điện thoại; thêm Loại tiền. Hai PTTT
  là `pttt` (lên đơn) và `pttt_thuc_te` (thu thực tế). Không có Blacklist.
- CRM gọi cùng `order_service.create_order` với ERP; SALE/CSKH tự lấy tài khoản.
  Quyền lên đơn vẫn Sale/Admin như ERP, không đồng nghĩa quyền xem bảng.
  Sale chưa có quyền bảng được chuyển đến trang chỉ nhập; API chi tiết và
  thống kê từ chối 403. Admin chưa gán bộ phận vẫn gặp giới hạn lên đơn cũ
  của ERP (N7); lượt này không thay quy tắc nền tảng đó.
- `orders.WaybillItem` giữ bản sao sản phẩm, số lượng, đơn giá và tiền đã thu
  của từng sản phẩm, FK tới `DataRecord`. Migration `orders.0003_waybillitem`
  đảo ngược được. Tạo đơn, dòng gốc, dòng vận đơn và chi tiết cùng giao dịch.
  Sửa bản sao không sửa Order/OrderLine. Chi tiết thay thế được xoá mềm.
- Bấm ô Sản phẩm/Số lượng/Giá tiền/Số tiền thanh toán mở editor. Tổng và trạng
  thái thanh toán do dịch vụ tính; sửa ô/dán tổng bị từ chối. Khoá dòng khi
  ghi; editor cũ báo xung đột thay vì ghi đè. Không ghi dữ liệu khách vào audit.
- Tiền đã thanh toán nhập thủ công từng sản phẩm, không phân bổ tỷ lệ.
  Dùng bộ trạng thái hiện có, kể cả nhãn **Thanh toán 1 phần**. Ngày thu, Bill,
  PTTT thực tế ở cấp đơn; chưa có lịch sử nhiều đợt thu.
- Nhập/xuất thêm cột **Chi tiết sản phẩm (JSON)**; mỗi phần tử gồm `product`
  (mã danh mục), `quantity`, `unit_price`, `paid_amount`. Thiếu chi tiết hoặc
  tổng không khớp báo lỗi xem trước, không suy đoán từ chuỗi gộp. Theo cơ chế
  nhập hiện có, người dùng có thể chỉ nhập các dòng hợp lệ; dòng lỗi bị bỏ qua.

## Thống kê

Nguồn duy nhất là các dòng/chi tiết đang có của bảng mới, toàn bộ bộ lọc lưới
và phạm vi quyền, không chỉ trang đang xem. Nhóm tổng, SALE/CSKH, mã sản phẩm
(không gộp các mã trùng tên), Quốc gia. Mỗi nhóm luôn tách loại tiền; phép cộng
và nhân dùng Decimal/PostgreSQL numeric, không quy đổi. Đếm distinct bản ghi
cha; đơn nhiều sản phẩm có thể nằm trong nhiều nhóm sản phẩm, không cộng số
đơn của các nhóm để suy ra tổng. Bỏ dòng/chi tiết xoá mềm, khôi phục dòng lấy
lại chi tiết hiện hành. Hủy/Hoàn vẫn nằm trong số liệu trừ khi lọc riêng.
Khoảng ngày dùng `ngay`, khởi tạo bằng ngày Việt Nam khi lưu đơn.

## Thay đổi so với quyết định trước

ADR-009 và AC-11.8 vẫn mô tả **bảng cũ** (cột `sl_*`, lọc trùng, Blacklist).
Không áp các hành vi riêng đó sang bảng mới. ADR-014 vẫn giữ ERP chỉ xem bảng;
khu nhập CRM là thêm cửa tạo đơn, không mở sửa Order gốc.

## Kiểm chứng

`crm/tests/test_waybill_new.py`: AC-18.1 → AC-18.8; các bài bảng cũ tiếp tục
kiểm ở đường dẫn tường minh `van_don`. `core/tests/test_chuyen_doi.py` kiểm
migration xuôi/ngược trên DB kiểm thử riêng. `scripts/kiem-thu-van-don-ui.cjs`
kiểm giao diện chỉ đọc, không gieo đơn vào dữ liệu thật.
