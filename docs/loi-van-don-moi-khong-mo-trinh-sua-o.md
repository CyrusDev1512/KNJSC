# Lỗi Vận đơn mới: Admin không mở được trình sửa ô

**Bổ sung 11.09 — Rung ba cột ghim khi cuộn:** đây là lỗi hiển thị riêng,
không phải lỗi quyền/không mở input. Đã bỏ bù scrollLeft/scrollTop, dùng vùng
sticky và giữ node ô/tiêu đề; hồi quy bấm đúp/inline/kéo hàng-cột đạt.
[Biên bản trước/sau, số đo và giới hạn](kiem-chung-ghim-cot-20260911.md).

Ngày ghi nhận: 11.09.2026

Nhánh: `vandonmoi`

Trạng thái: Đã sửa và kiểm trên Chrome/database test ngày 11.09.2026;
chưa quan sát lại chính phiên trình duyệt gặp lỗi của người dùng.

## Kết quả điều tra và sửa ngày 11.09.2026

Chủ dự án xác nhận lỗi xảy ra lúc được lúc không, có lúc không bấm sửa được
bất kỳ ô nào; đồng thời duyệt nhập ngay trong ô để bỏ khung che dữ liệu.

Hai đường lỗi đã tái hiện được:

1. `metadata()` gọi `grid_service.choice_list`, chỉ tra sổ theo bảng/cột.
   Vận đơn mới có cột chọn lấy danh sách từ `ColumnDef.options`; API trả
   `options=null` dù server cho sửa. `edit()` lặp qua giá trị này gây
   `c.options is not iterable`. Do draft được đặt trước khi tạo input,
   lỗi còn để lại draft không có input, khiến bước kết thúc nhập chặn ô sau.
2. Pointer di chuyển hơn 5px nhưng vẫn trong một ô bị xem là kéo vùng,
   nên không mở sửa. Hồi quy với rê 7px trong cùng ô thất bại trước sửa.

Đã dùng `choice_registry.for_column()` giống dịch vụ kiểm kiểu khi ghi;
trả danh sách JSON kể cả rỗng. Trình sửa chỉ tạo draft sau khi input sẵn sàng;
metadata không hợp lệ báo lỗi cột đó, không khóa ô khác. Click được phân biệt
bằng việc có đi qua ô khác hay không, giữ Shift/kéo chọn vùng.

Trình nhập nằm trong kích thước ô, bám cột ghim/cuộn/zoom; Tab/Enter và dán
vùng dùng autosave/CAS hiện có. Không đổi quyền Admin hoặc mở khóa các ô tổng.
Chrome đã kiểm sửa/lưu trạng thái và ngày, bấm đúp 120ms/F2, Tab, dán giữ số 0,
metadata lỗi không chặn ô khác, 1440/1280/390px và CSS zoom 125%.
Kết quả chi tiết: [kiểm chứng Admin và chạy bền](kiem-chung-master-admin-20260911.md).

Chưa có bằng chứng lỗi do PC. Các mục dưới đây giữ nguyên ghi nhận ban đầu,
không dùng suy đoán ban đầu thay cho nguyên nhân đã tái hiện ở trên.

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
