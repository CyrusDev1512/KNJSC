# ADR-044 — CEO, đặt lại mật khẩu và xóa mềm tài khoản

Ngày: 25.09.2026. Trạng thái: đã được chủ dự án duyệt; triển khai trên nhánh riêng,
chờ duyệt PR; chưa phát hành VPS. Bổ sung ADR-003 và thay giới hạn Admin-only
của **đặt lại mật khẩu/xóa tài khoản**, không thay quyền sửa hồ sơ/tạo/khóa.

## Quyền

| Người thao tác | Đặt lại mật khẩu và xóa |
|---|---|
| Staff | Không |
| Leader | Staff trong các team mình phụ trách |
| Manager | Leader/Staff trong phòng ban mình |
| CEO | Manager/Leader/Staff toàn công ty |
| Admin | Tài khoản khác, kể cả CEO/Admin |

Không tự xóa/đặt lại mật khẩu qua luồng quản lý; dùng đổi mật khẩu cá nhân.
Không xóa Admin hoạt động cuối. CEO không tự được gán cho ai; Admin chọn cấp
Giám đốc trong form tạo/sửa hiện có, không bắt buộc bộ phận cho CEO/Admin.

`Scope.all_departments` mô tả phạm vi đọc; `Scope.is_admin` chỉ đúng khi rank
Admin. CEO xem dữ liệu nghiệp vụ toàn công ty nhưng không được cấu hình, ghi
lưới/báo cáo, phân công vận đơn, quản lý tiền/chứng từ, xóa bảng hoặc ghi nhận
nhân sự nhờ cấp bậc. Quyền cá nhân trên nội dung nội bộ chung (ví dụ viết bài,
task của bản thân) vẫn theo luật hiện có; không kế thừa quyền quản lý của Leader.
CEO không có `is_staff/is_superuser`; tác vụ nền vẫn chỉ của mình, Admin thấy hết.

## Giao diện và dịch vụ

- Danh sách nhân sự tính nút bằng `AccountPolicy`, một lần lấy scope cho trang.
- Admin sửa hồ sơ như trước. Các quản lý khác xem thông tin chỉ đọc trong Sửa,
  có form Đặt lại mật khẩu riêng: nhập hai lần, dùng validator Django hiện có.
- POST đặt lại gọi service, băm mật khẩu, tăng mốc phiên; quyết định ban đầu
  buộc đổi lần sau đã được thay thế bởi bổ sung 25.09 bên dưới;
  không mở khóa tài khoản. Không hiện lại mật khẩu khi sai và không lưu mật khẩu
  rõ vào session/messages/audit/URL; phản hồi người đăng nhập không được cache.
- Xóa mở trang xác nhận có mã/họ tên, checkbox, nút Hủy và Xác nhận xóa.
  Chỉ POST có CSRF và xác nhận mới thay đổi dữ liệu.
- POST đọc lại actor/target; khóa User theo thứ tự ID (actor, target và các Admin),
  sau đó hồ sơ target, trong transaction. Kiểm lại quyền sau khóa; vô hiệu actor
  bị xóa khi đang chờ. Sửa hồ sơ/khóa tại màn nhân sự dùng cùng ranh giới khóa.
  Các primitive nội bộ cũng khóa User và từ chối hồ sơ đã xóa.

## Bảo toàn dữ liệu

### Bổ sung 25.09.2026 — đặt lại và hiện/ẩn mật khẩu mới

Chủ dự án chọn phương án 1: sau **đặt lại**, người dùng đăng nhập bằng mật khẩu
mới và không bị buộc đổi lần nữa. Service đặt `must_change_password=False` cho
tài khoản vừa được đặt lại; vẫn hủy phiên ERP/CRM cũ, giữ `is_active` của tài
khoản bị khóa. Không cập nhật hàng loạt cờ của các tài khoản đã có; việc tạo
tài khoản mới vẫn theo quy tắc buộc đổi lần đầu của AC-1.5.

Manager/CEO/Admin có nút hiện/ẩn ở từng ô mật khẩu mới của form đặt lại trong
phạm vi `AccountPolicy` hiện hành. Leader giữ quyền đặt lại nhưng không thêm
nút này. Đây chỉ là cách hiển thị nội dung người quản lý đang nhập, không phải
quyền đọc mật khẩu cũ. Sau gửi hoặc tải lại trang, ô nhập không chứa mật khẩu.
Giữ Django password hash; không có kho mật khẩu giải mã, API đọc mật khẩu,
migration, dependency hoặc mật khẩu trong session/log/audit.

Migration `org.0006_ceo_and_account_soft_delete` thêm `deleted_at`, `deleted_by`
và lựa chọn rank; không sửa dữ liệu cũ. Xóa mềm vô hiệu tài khoản, bỏ khả năng
dùng mật khẩu và tăng `session_epoch`. Backend từ chối hồ sơ đã xóa kể cả
`is_active` bị bật lại ngoài ý muốn.

Manager hồ sơ lịch sử vẫn bao gồm hồ sơ đã xóa; danh sách nhân sự/Tổng quan và
bộ chọn mới dùng `alive()`/điều kiện tương đương. Giữ User, mã nhân sự, username,
team, đơn/báo cáo/phân công/audit; không tự chuyển người hoặc tái sử dụng mã.
Django admin không cho xóa cứng User/UserProfile, không sửa đối tượng đã xóa.
Chưa có giao diện khôi phục tài khoản.

Migration đảo ngược **làm mất dấu xóa/người xóa**, giữ tài khoản bất hoạt và
mật khẩu không sử dụng được. Chỉ kiểm ngược trên database test; không dùng
đảo migration để quay lui trên dữ liệu đang vận hành.

## Kiểm chứng

Xem [biên bản](../kiem-chung-quan-ly-tai-khoan-20260925.md): ma trận năm cấp,
POST/CSRF, phiên ERP/CRM, bảo toàn lịch sử, hai kết nối đồng thời, migration,
ngân sách 10 truy vấn và Chrome 1440/390. PR nháp về main; không tự merge/VPS.
