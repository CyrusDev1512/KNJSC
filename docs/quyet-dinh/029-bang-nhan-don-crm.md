# ADR-029 — Bảng nhận đơn cấu hình tại CRM

> **Đã bị thay thế toàn bộ** bởi [ADR-036](036-mot-bang-van-don-duy-nhat.md), 18.09.2026: một bảng vận đơn duy nhất, trang Bảng nhận đơn và `receives_orders` đã xoá.

Ngày 15.09.2026. Chủ dự án duyệt triển khai local từ đề xuất chọn bảng đích mặc định cho Admin.
Thay phần đích cố định trong ADR-018/023; giữ kiến trúc Django/service và database dùng chung.

## Quyết định

- Admin cấu hình tại `/cau-hinh/nhan-don/`, mục **Bảng nhận đơn** của CRM. Sale không chọn bảng mỗi đơn.
- `TableDef.receives_orders` chọn một đích; unique constraint chỉ cho tối đa một bảng được đánh dấu.
  Chưa cấu hình thì dùng `van_don_moi`. Đích đã chọn không khả dụng thì báo lỗi và rollback;
  không tự ghi nhầm sang bảng mặc định.
- `TableDef.workflow=waybill` giữ capability của bảng đã tiếp nhận nghiệp vụ. Đổi đích không đổi ID,
  không chuyển dòng, không sửa Order/OrderLine, không bỏ profile của bảng trước đó.
- Chỉ nhận bảng thuộc Vận đơn đang hoạt động, đủ 25 cột chuẩn đúng kiểu/meaning và lựa chọn.
  Vận đơn DB gồm các cột này và cột đối soát riêng; giữ thứ tự và không tự bổ sung cột.
  Bảng chưa có profile nhưng đã có dữ liệu (kể cả xóa mềm) phải chuyển đổi riêng, chưa được chọn.
  Bảng cũ `van_don` không được dùng làm đích mới.
- Khi tiếp nhận bảng trống: bật cùng cấu hình hàng đợi `is_shared` như bảng master gốc, đăng ký
  profile và tăng phiên bản để tab đang mở tải lại. Phạm vi Vận đơn vẫn theo phân công/chế độ xem;
  xem toàn bảng không mở quyền sửa ô người khác (*câu này thay bởi ADR-033, 17.09.2026: nhân viên Vận đơn xem và sửa toàn bảng*). Giữ các ngoại lệ Sale/CSKH/Kế toán và chứng từ
  như các service hiện có. Quyền thêm chứng từ vẫn dựa trên phạm vi xem theo ADR-025.
- Registry chính sách hỗ trợ workflow; dùng chung kiểm quyền, lưới JSON, chi tiết sản phẩm,
  phân công, lọc/xuất, chứng từ, thống kê và bảo vệ vòng đời bảng. Không suy profile từ mã cột.
  Bảng có profile Vận đơn được bảo vệ khỏi xóa bảng như master gốc, kể cả khi ngừng nhận đơn.
- Khóa giao dịch PostgreSQL chia sẻ bảo vệ lựa chọn đích trong toàn bộ giao dịch lên đơn;
  đổi cấu hình lấy khóa độc quyền cùng namespace rồi khóa vòng đời bảng. Bảng được chọn
  và đơn–bản sao vận đơn commit/rollback nguyên tử; giữ khóa cấp mã đơn hiện có.

## Migration và giới hạn

Migration `forms_builder.0012_order_destination` chỉ thêm metadata và unique constraint.
Không di chuyển dữ liệu. Rollback bỏ cấu hình, trở lại đích mặc định; dòng/đơn đã lưu vẫn còn.
Cần sao lưu cấu hình trước rollback và triển khai cùng phiên bản cho mọi process ghi.
Không tự chọn Vận đơn DB trên dữ liệu đang vận hành. Không triển khai VPS trong tác vụ này.

[Bằng chứng](../kiem-chung-bang-nhan-don-20260915.md).

## Bổ sung 15.09.2026 — Vận đơn DB có placeholder

Chủ dự án xác nhận 6.667 dòng Vận đơn DB là placeholder, duyệt chuẩn bị bảng
để có thể chọn nhận đơn và phát hành VPS. Bổ sung lệnh vận hành
`chuan_bi_bang_nhan_don --table van_don_db --actor <ma-admin> --expected-rows 6667`.

Lệnh gọi service có kiểm quyền Admin, khóa lựa chọn đích và vòng đời bảng;
kiểm đủ cấu trúc/lựa chọn chuẩn và số dòng đã xác nhận (gồm xóa mềm).
Chỉ gắn workflow Vận đơn, bật cấu hình hàng đợi và tăng phiên bản quyền;
không sửa dòng/cột, không tạo Order/WaybillItem hoặc phân công giả từ chuỗi tên.
Dòng chưa phân công tuân theo phạm vi Vận đơn hiện có sau chuyển đổi.

Không tự đổi bảng nhận đơn hiện hành. Admin chọn trên màn hình cũ sau khi bảng
đã sẵn sàng. Bảng bất kỳ đã có dữ liệu vẫn bị chặn nếu chưa được duyệt chuyển
đổi riêng; không tự nhận diện placeholder hoặc chạy chuyển đổi trong seed.
Không thêm dependency/migration. [Kiểm chứng](../kiem-chung-chuan-bi-bang-nhan-don-20260915.md).
