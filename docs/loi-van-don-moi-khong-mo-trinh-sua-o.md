# Lỗi Vận đơn mới: Admin không mở được trình sửa ô

Ngày ghi nhận: 11.09.2026  
Nhánh: `vandonmoi`  
Trạng thái: Chưa sửa — tiếp tục tái hiện bằng trình duyệt ngày mai

## Hiện tượng người dùng báo

- Đăng nhập bằng tài khoản Admin.
- Đã chuyển lưới sang **Chế độ: Chỉnh sửa**.
- Bấm vào `Trạng thái vận chuyển`, `Ngày thanh toán` và nhiều trường khác nhưng
  không mở được trình sửa như Excel/Google Sheets.
- Người dùng nhớ rằng trước đây bấm đúp vào cột lựa chọn sẽ mở dropdown; sau
  commit buổi chiều, chế độ Chỉnh sửa phải cho bấm một lần để sửa ngay.

Chưa chốt ở lượt ghi nhận này việc giao diện hoàn toàn không phản ứng, báo
“Ô này chỉ đọc”, hay mở trình sửa nhưng không lưu được. Cần quan sát trực tiếp
trên phiên đăng nhập của người dùng để tách ba trường hợp.

## Hành vi đúng đã có trong mã

Commit `8db7401` ngày 10.09.2026 lúc 18:16 thêm lưới master và quy định:

- Chế độ Xem: F2 hoặc bấm đúp để mở trình sửa.
- Chế độ Chỉnh sửa: bấm một lần vào ô được phép sửa để mở ngay.
- Cột `choice` dùng dropdown.
- Cột `date` dùng ô chọn ngày.

Commit `08d1c2a` chỉ thay bố cục cột ghim và CSS của Vận đơn mới; không loại bỏ
nhánh xử lý mở trình sửa nói trên.

## Bằng chứng phía máy chủ

Đã kiểm tra trực tiếp với cấu hình `knjsc.settings.bangtinh`, bảng
`van_don_moi`, một dòng mẫu và tài khoản Admin đang hoạt động:

- Bảng không thuộc cấu hình chỉ đọc (`grid_only=False`).
- Admin có quyền sửa dòng (`row_edit=True`).
- Máy chủ trả `editable=True` cho `trang_thai_vc`, `ngay_tt`, `bill`,
  `pttt_thuc_te` và `ghi_chu`.
- Các cột trên trong database không bị đánh dấu `is_computed`.

Vì vậy lỗi của `Trạng thái vận chuyển` và `Ngày thanh toán` nhiều khả năng nằm
ở trạng thái/sự kiện JavaScript phía trình duyệt, cache tệp tĩnh, hoặc bước mở
editor; không phải do quyền Admin hay cấu hình KN CRM chỉ đọc.

## Ngoại lệ cần phân biệt: Trạng thái thanh toán

`trang_thai_tt` hiện nằm trong `waybill_service.PROTECTED` từ commit `0651330`.
Theo quyết định Vận đơn mới đã duyệt, trạng thái thanh toán được tính tự động từ
tổng `paid_amount` của chi tiết sản phẩm; người dùng sửa tiền từng sản phẩm rồi hệ
thống xác định Chưa thanh toán/Thanh toán một phần/Đã thanh toán.

Người dùng nhớ cột này từng mở dropdown. Trước khi thay đổi cần chốt lại một trong
hai quy tắc, vì cho chọn thủ công có thể làm trạng thái lệch tổng tiền:

1. Giữ tự động và làm rõ trên giao diện vì sao ô bị khóa.
2. Cho Admin chọn thủ công, đồng thời định nghĩa cách xử lý khi lựa chọn mâu thuẫn
   với tiền đã nhập.

Không tự mở khóa `trang_thai_tt` cho tới khi chủ dự án chốt quy tắc thay thế.

## Việc cần làm ngày mai

1. Tái hiện trên đúng trình duyệt/tài khoản của người dùng; ghi URL, trạng thái
   trên thanh lưu và phản ứng khi bấm một lần, bấm đúp, F2.
2. Kiểm Network/Console và payload `/bang-tinh/van_don_moi/du-lieu/` để xác nhận
   ô nhận `editable=true` ở chính phiên lỗi.
3. Viết test trình duyệt hồi quy: Admin bật Chỉnh sửa, bấm một lần vào
   `trang_thai_vc` phải thấy `select`; bấm `ngay_tt` phải thấy `input[type=date]`.
   Kiểm thêm bấm đúp/F2 ở chế độ Xem.
4. Sửa tối thiểu luồng sự kiện/cache/editor gây lỗi, rồi kiểm autosave, lỗi 409,
   cuộn ảo và các cột ghim không bị hồi quy.
5. Chỉ xử lý `trang_thai_tt` sau khi có quyết định nghiệp vụ ở mục trên.

## Điều kiện đóng lỗi

- Admin sửa được `Trạng thái vận chuyển` bằng dropdown và `Ngày thanh toán` bằng
  bộ chọn ngày theo cả thao tác được quy định cho hai chế độ.
- Lưu thành công, tải lại vẫn giữ dữ liệu và lịch sử ô có thay đổi tương ứng.
- Các trường tổng/chi tiết/phân công vẫn khóa hoặc mở đúng cơ chế riêng.
- Có test trình duyệt hồi quy và kiểm trên trình duyệt thực tế của người dùng.
