# ADR-030 — Phiên đăng nhập chung ERP/CRM

Ngày: 15.09.2026. Trạng thái: chủ dự án đã duyệt.

## Bối cảnh

ERP và CRM trên VPS dùng chung database, SECRET_KEY và Django database session.
Cookie host-only khiến hai hostname giữ hai phiên khác nhau. Chủ dự án xác nhận
domain mẹ và toàn bộ subdomain thuộc phạm vi tin cậy.

## Quyết định

- Cấu hình tên/domain cookie qua môi trường, dùng chung trên mọi process.
- VPS: `SESSION_COOKIE_DOMAIN=thnsolution.io.vn`,
  `SESSION_COOKIE_NAME=knjsc_session_v2`,
  `CSRF_COOKIE_DOMAIN=thnsolution.io.vn`, `CSRF_COOKIE_NAME=knjsc_csrf_v2`.
- Giữ Path=/, Secure ở production, session HttpOnly, SameSite=Lax;
  trusted origins chỉ `https://erp.thnsolution.io.vn` và
  `https://crm.thnsolution.io.vn`. Không wildcard, không bỏ CSRF.
- Cookie tên mới không đọc lại sessionid/csrftoken cũ. Sau phát hành, mỗi người
  đăng nhập lại một lần ở một trong hai ứng dụng. Không tự chọn tài khoản từ hai
  phiên cũ có danh tính khác nhau.
- Local để domain trống, giữ tên mặc định. Settings test và Solarpunk preview
  cưỡng chế domain=None để không kế thừa domain vận hành; preview giữ tên riêng.
- Đăng xuất một bên vô hiệu phiên chung tại request tiếp theo bên kia. Đổi tài
  khoản phải đăng xuất trước. Form cũ sau đăng nhập lại có CSRF cũ bị từ chối;
  không tự gửi lại thao tác ghi.
- Giữ timeout không hoạt động 60 phút, mốc hoạt động dùng chung, auth epoch,
  tài khoản bị khóa, đổi mật khẩu và bắt đổi mật khẩu lần đầu như hiện tại.
- Không đổi quyền nghiệp vụ, URL, form đăng nhập, schema hoặc dependency;
  không truyền session qua URL/localStorage, không thêm middleware/truy vấn.

## Vận hành và quay lui

Phát hành ERP/CRM/worker/heavy/beat cùng image trong một đợt, RUN_MIGRATIONS=0.
Trước phát hành lưu image, bản .env riêng tư, hai compose override, hash/diff
hotfix sidebar; pg_dump định dạng custom và kiểm pg_restore --list đọc được.
Giữ nguyên giới hạn CPU/RAM và hotfix khi dựng image từ working tree VPS.

Nếu vòng lặp đăng nhập, CSRF bất thường hoặc sai tài khoản: khôi phục image và
bốn giá trị cookie trước phát hành, cập nhật lại các process. Không phục hồi
đè database. Phiên cũ có thể còn hiệu lực khi quay về cấu hình cũ; nếu xảy ra
sự cố danh tính cần đánh giá và vô hiệu phiên theo quy trình sự cố riêng.

## Kiểm chứng

[Báo cáo kiểm chứng và phát hành](../kiem-chung-dang-nhap-chung-20260915.md).
Không suy khả năng chịu tải toàn CRM từ thay đổi cấu hình này.
