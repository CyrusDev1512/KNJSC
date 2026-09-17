# ADR-026 — Chế độ xem Vận đơn mới

> **Đã bị thay thế toàn bộ** bởi [ADR-033](033-pham-vi-toi-toan-bo-va-quyen-sua-van-don.md), 17.09.2026: nhân viên Vận đơn xem và sửa toàn bảng, nút Tôi / Toàn bộ theo người dùng; trang Chế độ xem bảng, service và trường `delivery_view_all` đã xoá (giữ `delivery_view_version`). Thân tệp giữ nguyên làm lịch sử.

Ngày 12.09.2026. Chủ dự án duyệt triển khai; số 025 dành cho quyết định chứng
 từ thanh toán ở task đang chạy song song.

Thay thế riêng phần bắt buộc giới hạn quyền **xem** của Staff Vận đơn trong
ADR-020 và KNJSC_PROBLEM 02.4. Quyền sửa theo phân công (02.5) giữ nguyên.

- Chỉ áp dụng `van_don_moi`. Mặc định Chỉ dòng được phân công; lựa chọn còn
  lại Toàn bộ bảng, áp dụng mọi nhân viên Vận đơn được quyền truy cập bảng.
- Admin và Manager Vận đơn thuộc bộ phận sở hữu bảng đổi bất cứ lúc nào.
  Leader, Sale, Marketing, CSKH không được tự đổi chế độ.
- Phân công vẫn xác định trách nhiệm từng dòng. Mở rộng xem không cấp quyền
  sửa dòng người khác, không mở rộng quyền của các bộ phận khác hoặc đơn gốc.
- Cấu hình chính thuộc Cấp quyền → Cột & cấp quyền; có đường tắt Chế độ xem
  bảng từ menu lưới và hộp Phân công, ghi rõ áp dụng toàn bảng.
- Dùng service orders và hai trường TableDef với migration 0011, không dùng
  `is_shared` vì trường đó đang ảnh hưởng cả quyền sửa. Bản ghi phân công
  và dữ liệu lịch sử giữ nguyên. Chế độ và phiên bản lưu trong một transaction,
  thay đổi có audit; gửi lại cùng chế độ không tăng phiên bản.
- Query/token/cache dùng quyền hiện hành; quyền ghi kiểm riêng trước cả
  replay receipt. Không lấy khả năng đọc làm bằng chứng được sửa.
- Chủ dự án chấp nhận reload toàn trang: poll khoảng 8 giây phát hiện phiên
  bản mới và tải lại, bỏ cache/nháp. Tab ẩn cập nhật khi hoạt động trở lại.
  Không cần bảo toàn nháp qua reload, không buộc đăng nhập lại.

Bằng chứng, giới hạn và hướng dẫn tích hợp:
[kiểm chứng](../kiem-chung-che-do-xem-van-don-20260912.md).
