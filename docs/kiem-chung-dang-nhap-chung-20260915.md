# Đăng nhập chung ERP/CRM — 15.09.2026

## Phạm vi

Theo [ADR-030](quyet-dinh/030-dang-nhap-chung-erp-crm.md), chỉ thêm đọc bốn biến
môi trường cookie, cô lập test/preview. Không sửa middleware, quyền, DB hoặc UI.
Nền triển khai: `f971683`, nhánh `codex/crm-update-solar-ui`.

## Kết quả local

PostgreSQL 16 riêng: container `knjsc-shared-login-db`, network riêng, dữ liệu
tmpfs; pytest dùng database tên test_. Không seed hoặc kiểm tải database sử dụng.

- TDD: test hợp đồng biến môi trường thất bại trước sửa (bốn giá trị None).
- `pytest core/tests org/tests reports/tests crm/tests/test_delivery_view_mode.py
  crm/tests/test_order_destination.py crm/tests/test_dich_vu_bangtinh.py`:
  **868 passed, 1 failed, 1 skipped**, 47,67 giây.
- Lỗi: `core/tests/test_giao_dien.py::test_moi_lop_css_dung_trong_template_deu_ton_tai[order_destination.html]`:
  thiếu định nghĩa lớp `loi`, `thong-bao`. Chạy riêng trên archive HEAD f971683
  cũng lỗi y hệt (1 failed, 6 passed, 570 deselected); đây là lỗi nền, chưa sửa
  trong tác vụ xác thực. Không kết luận toàn bộ suite đạt.
- `pytest forms_builder/tests crm/tests/test_waybill_feedback.py crm/tests/test_master_grid.py`:
  **213 passed**, 42,66 giây. Bao gồm quyền đọc/ghi lưới, grant và xuất.
- 15 test xác thực mới đều đạt trong nhóm core: hai chiều × bốn cấp quyền,
  logout, timeout, khóa tài khoản, auth epoch, đổi mật khẩu, bắt đổi lần đầu,
  cookie cũ, CSRF thiếu/cũ và chặn next ra domain ngoài.
- Bài Chrome bị skip có chủ ý trong lần chạy không bật SHARED_LOGIN_BROWSER;
  đã chạy riêng thành công dưới đây. Không coi skip là đạt.

## Chrome HTTPS hai hostname trên database test

`SHARED_LOGIN_BROWSER=1 pytest core/tests/test_shared_login_browser.py
--liveserver=0.0.0.0:8863` + `node scripts/kiem-thu-shared-login.cjs`:
**1 passed**, 70,85 giây; **16 kịch bản Chrome đạt**, không có pageerror.

- Host `erp.shared.test` và `crm.shared.test`, HTTPS proxy 8445 tới Django test
  server 8863, cookie domain shared.test; chứng chỉ test chỉ cho phiên Chrome.
- 1440px/390px × bắt đầu ERP/CRM × Staff/Leader/Manager/Admin, context riêng.
- Bấm liên kết ứng dụng thật, mỗi lượt đăng nhập một lần; tạo đơn test và
  kiểm lại 16 đơn trong DB, đúng tài khoản và tổng Decimal=25.
- Cấu hình nhận đơn trả 200 cho Admin, 403 cho ba cấp còn lại. Đăng xuất CRM
  khiến request tiếp theo không còn phiên; đăng nhập tài khoản B thì ERP/CRM
  cùng nhận B. Cookie mới có domain chung, Secure/HttpOnly/Lax.
- Các lượt 390px có cookie sessionid cũ hợp lệ của tài khoản khác ở cả hai
  hostname: không tự đăng nhập nhầm từ cookie cũ.
- Những lần thiết lập harness lỗi (cú pháp Node, khởi tạo middleware sau server)
  đã sửa trong harness, không sửa ứng dụng để né kiểm chứng.

Script cần Playwright/Chrome sẵn có và chứng chỉ test ở
`storage/shared-login/tls-key.pem`, `tls-cert.pem`, `tls-spki.txt` (SHA256 SPKI
base64), SAN đúng hai host trên. Không cài dependency vào ứng dụng, không thêm
chứng chỉ vào kho tin cậy hệ điều hành. Bằng chứng chỉ lưu cờ/kết quả, không ghi
mật khẩu/cookie vào ảnh, trace hoặc log. Không đo tải mới: đường xử lý và truy
vấn phiên giữ nguyên; không tuyên bố tăng tốc.

## Phát hành VPS

Đang chuẩn bị phát hành; chưa dùng kết quả local để kết luận VPS đạt.
Đã sao lưu ở `/opt/knjsc-runtime/backups/shared-login-20260915/`:

- Database dump 853.803 byte, đọc được danh mục bằng pg_restore --list;
  SHA256 `66395c127c7b4edd63b7a0eb95a1cc63c20c0a81b9d92d46f1014ae9c4de82bf`.
- Image trước: `knjsc-app:f971683-crm-sidebar-20260915`.
- Hotfix `app/static/css/crm-frame.css`:
  SHA256 `123d7f0073d13af7ee0d2db539f1b9ea159ba6f06f1f31543deddb0b58782d89`.
- .env trước và compose.yml/compose.vps.yml lưu riêng tư trên VPS.
  Chỉ kiểm đọc archive, chưa thử phục hồi DB cho tác vụ này.
