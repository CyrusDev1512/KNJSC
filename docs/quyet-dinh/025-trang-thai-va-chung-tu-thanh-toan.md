# ADR-025 — Trạng thái và chứng từ thanh toán

> Thay thế một phần 14.09.2026: kho Chứng từ thanh toán tạm khóa mặc định bằng
> `PAYMENT_DOCUMENTS_ENABLED=0`. Sidebar, script/renderer kho ảnh và mọi URL kho
> trả 404 khi tắt; model, migration, file và code vẫn giữ để bật lại có chủ đích.
> Bill của cả `van_don` và `van_don_moi` trở lại text tự do qua lưới CRM. Chỉ
> chuỗi bắt đầu bằng `http://` hoặc `https://` được dựng thành liên kết tab mới;
> giao thức khác là chữ thường. Không tạo ảnh hay 100 chứng từ mẫu, không sửa các
> mã `BILL-MAU-*` hiện có. Quyết định sửa trực tiếp trạng thái thanh toán vẫn giữ.

Ngày 12.09.2026. Chủ dự án duyệt triển khai trên `codex/chung-tu-thanh-toan`.
Thay phần tự suy trạng thái từ tiền của ADR-018; không đổi đơn gốc hay quyền nhập tiền.

## Quyết định

- `van_don_moi.trang_thai_tt` sửa trực tiếp theo ba giá trị hiện hành, dùng quyền dòng,
  autosave, CAS, lịch sử và Undo. Sửa tiền/chi tiết không ghi đè trạng thái.
  Đơn mới giữ cách khởi tạo trước đây; nhập file có trạng thái rõ ràng thì giữ lựa chọn hợp lệ.
  Không cập nhật dữ liệu cũ, kể cả trạng thái trống.
- Module `orders`: `PaymentDocument` liên kết `DataRecord`, `PaymentImage` liên kết chứng từ.
  Một chứng từ thuộc một đơn, không chuyển đơn; một đơn có nhiều chứng từ và mỗi chứng từ có nhiều ảnh.
- Ref nhập thủ công, giữ số 0 đầu, bỏ khoảng trắng hai đầu, duy nhất không phân biệt
  hoa thường trong cùng đơn giữa chứng từ còn hiệu lực. Không duy nhất toàn hệ thống.
- Vận đơn thêm trong phạm vi được giao. Kế toán (`ke-toan`)/Admin quản lý toàn bộ
  chứng từ Vận đơn mới. Kế toán đọc toàn bộ bảng mới, không tự thêm quyền sửa ô,
  phân công hoặc đơn gốc. Người có quyền xem dòng được xem chứng từ còn hiệu lực.
- Thêm bộ phận Kế toán bằng migration, không tạo tài khoản hoặc đổi hồ sơ hiện có.
  Xóa/khôi phục chứng từ dùng xóa mềm và phiên bản, giữ file gốc.
- Không có trường tiền thứ hai, OCR, xác nhận đối soát hoặc tự đổi trạng thái từ ảnh.

## Lưu trữ và giao tiếp

- JPG/PNG, tối đa 5 ảnh/lượt và tổng 10 MB; kiểm đầu file theo tiện ích upload hiện có.
  UUID là tên file thật; Ref là tên hiển thị. Lưu ở `STORAGE_DIR/chung-tu-thanh-toan/`.
- Không có URL public. Đường ảnh kiểm quyền mỗi request, MIME ảnh, `private, no-store`.
  Kiểm file trước khi lưu; lỗi giao dịch dọn file mới của lượt đó.
- Tạo có operation UUID và fingerprint trong database. Replay cùng ID/nội dung
  nhận lại chứng từ đã lưu; cùng ID/nội dung khác bị từ chối.
- Sửa khóa dòng cha/chứng từ và kiểm phiên bản. Audit chỉ ghi ID/hành động.
  Ghi `updated_at` dòng và sự kiện `bill` trong journal cùng giao dịch; không bật cờ tối ưu.
- JSON lưới chỉ bổ sung count và tối đa hai Ref/dòng, một truy vấn metadata cả khối.
  Giữ Bill cũ; Excel liệt kê Ref và Bill cũ, không nhúng ảnh.
- Tìm/lọc Ref qua truy vấn dùng chung. Thứ tự: ngày chuyển khoản, nếu thiếu dùng
  ngày tải theo múi giờ hiển thị, rồi ID. Số lần không phải định danh chứng từ.

## UI, vận hành và giới hạn

Sidebar CRM có Chứng từ thanh toán, danh sách và Kho ảnh, phân trang 50.
Kho ảnh không tải ảnh sẵn. Bấm Ref trong Bill mở ảnh đầu; chọn ảnh tiếp theo mới tải.
Popup có X/Escape, phóng to/tải ảnh. Bill bị cắt có vùng đọc chứa liên kết.
Kiểm quyền lại khi mở/tải và polling popup; nháp lưới vẫn trong RAM.

Sao lưu gồm database **và** thư mục chứng từ; `pg_dump` không chứa ảnh.
Không bổ sung tự xóa file/lịch sử hoặc thay chính sách lưu giữ.

Kết quả và giới hạn: [biên bản](../kiem-chung-chung-tu-thanh-toan-20260912.md).
