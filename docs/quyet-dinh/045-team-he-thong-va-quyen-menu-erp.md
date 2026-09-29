# ADR-045 — Team hệ thống và quyền menu ERP

- Ngày chốt: 25.09.2026.
- Chủ dự án duyệt: Team tự điền theo hồ sơ; Quản trị chỉ Admin; Staff/Leader không
  mở Bảng dữ liệu ERP. Cho phép theo dõi/tải tác vụ cá nhân từ luồng xuất file.
- Thay thế phần chọn Team cho mọi vai trò của ADR-043 và quyền truy cập các màn
  ERP tương ứng trong hướng dẫn cũ. Không thay phạm vi dữ liệu dùng chung của CRM.

## Team báo cáo

Staff, Leader và Manager nộp báo cáo bằng team trong hồ sơ, một ô chỉ đọc giống
Marketer. Server bỏ qua team do client gửi khác hồ sơ, kể cả tên trong cột mẫu
`team_mau`; cả `DailyReport.team`, `DataRecord.team` và cột mẫu này ghi cùng team.
Admin giữ dropdown các team hợp lệ trong bộ phận của biểu mẫu.

Không có team: hiện “Chưa được gán Team”, vẫn nộp được với team rỗng như trước.
Không suy team từ bộ phận hoặc từ các team Leader quản lý. Team trong hồ sơ là
nguồn cho báo cáo cá nhân; phạm vi Leader có thể gồm nhiều team là khái niệm khác.

Ẩn ô nhập `team_mau` trùng trên form nộp, không xóa cột hay dữ liệu lịch sử.
Khi sửa báo cáo cũ, giữ team và tên team đã lưu; đổi team hồ sơ sau này không
viết lại báo cáo cũ. Bốn số bắt buộc, công thức, ngày và danh tính giữ nguyên.

## Menu và đường dẫn

| Chức năng ERP | Staff | Leader | Manager | CEO | Admin |
|---|---|---|---|---|---|
| Nhóm Quản trị | Ẩn | Ẩn | Ẩn | Ẩn | Hiện |
| Nhật ký / Ma trận quyền / danh sách Tác vụ nền | 403 | 403 | 403 | 403 | Cho phép |
| Bảng dữ liệu và các URL bảng ERP | 403 | 403 | Trong phạm vi | Toàn công ty | Cho phép |
| Biểu mẫu & tài liệu | Giữ quyền cũ | Giữ quyền cũ | Giữ quyền cũ | Theo định nghĩa CEO chung | Giữ quyền cũ |
| Tiến độ / tải một tác vụ cá nhân | Của mình | Của mình | Của mình | Của mình | Tất cả |

CEO xem dữ liệu theo chế độ chỉ đọc ERP. Phạm vi toàn công ty không đồng nghĩa
quyền Admin: kiểm đúng vai trò ở menu, endpoint Quản trị và truy vấn tác vụ nền.
Định nghĩa CEO lấy nguyên từ task **FIX EROR**, nhánh
`claude/phan-quyen-mat-khau-xoa-tai-khoan`, code `cd7e7a1`, đầu nhánh `604910c`.
Chủ dự án chốt bổ sung: **CEO chỉ xem, không nộp/sửa báo cáo**. Không hiển thị
luồng nộp cho CEO; gọi thẳng đường nộp/điền cũng bị chặn. CEO vẫn xem lịch sử,
báo cáo tổng hợp và xuất dữ liệu trong quyền; không đổi ngoại lệ quản lý tài
khoản của [ADR-044](044-ceo-va-quan-ly-tai-khoan.md).

Quyền bảng được cấp riêng không vượt qua giới hạn cấp bậc của màn ERP. Giữ kiểm
phạm vi sau kiểm cấp bậc. Chặn tại URLconf ERP để các view quản lý bảng dùng chung
ở CRM không bị siết quyền theo. Liên kết phụ dẫn đến trang bị cấm cũng được ẩn.
Tác vụ ngoài chủ sở hữu vẫn 404; tải file vẫn kiểm lại phạm vi dữ liệu hiện hành.

## Phạm vi không thực hiện

Chủ dự án đã **hoãn** yêu cầu ẩn KN CRM/cấm CRM với Sale và Marketing trong cùng
phiên. Giữ nút KN CRM, lên đơn Sale, lưới, quyền quản lý bảng và tác vụ của CRM.
Phần Team/menu không thêm migration hoặc dependency. Migration
`org.0006_ceo_and_account_soft_delete` được kế thừa nguyên trạng từ nhánh CEO,
đã áp dụng trên database preview riêng. Không seed vào dữ liệu đang dùng hoặc
phát hành VPS trong tác vụ local này.
