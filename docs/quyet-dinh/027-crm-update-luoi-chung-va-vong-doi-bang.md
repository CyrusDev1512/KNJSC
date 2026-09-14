# ADR-027 — Bộ lưới chung và vòng đời bảng CRM

Ngày: 12.09.2026. Quyết định đã được chủ dự án duyệt trong kế hoạch CRM-UPDATE.
Trạng thái 14.09: đã kiểm chứng trong worktree riêng; chưa triển khai vào môi trường người dùng.

## Phạm vi thay thế

Thay phần renderer/endpoint ghi tương tác của ADR-009/010/011 trên Marketing,
Sale, Vận đơn cũ bằng lõi JSON/cuộn ảo hiện có. Giữ dữ liệu, mã bảng, ID,
người tạo, lịch sử, quyền và URL đọc. ERP vẫn chỉ đọc. Vận đơn mới giữ nghiệp vụ
Lên đơn, bất biến đơn gốc, phân công, Bill/chứng từ theo ADR-018/021/023/025.
Tạo bảng trắng và duplicate cấu trúc được hoãn; quyền tạo bảng hiện có giữ nguyên.

## Thành phần và dữ liệu

- Một template master, một controller JavaScript, WorkingCopy và RowGeometry.
  `grid_service` giữ truy vấn/lọc/định dạng/xuất, không dựng HTML từng ô.
- Registry `record_policies` có phần trình bày tùy chọn (`grid_for`); quy tắc
  ghi vẫn qua `for_table`. Điều này giữ luật nhập/ghi của các bảng cũ.
  Không bật Bill/phân công/chi tiết chỉ vì cột có cùng mã.
- Metadata gồm kiểu, danh sách chọn, quyền, renderer, ghim và phiên bản cấu trúc.
  Vận đơn cũ có cột Trùng/màu trạng thái riêng, cùng một lõi hiển thị.
- 100 dòng/khối, cache tối đa 10 khối, inline, autosave 500 ms/tối đa 2 giây,
  CAS, biên nhận và 100 bước Undo. Nháp chỉ trong RAM; localStorage chỉ lưu
  tùy chọn bố cục theo tài khoản/bảng/ID dòng, không lưu dữ liệu khách hàng.
- Công thức theo cột vẫn tính tại server, cùng giao dịch với đầu vào. Ghi nhiều
  ô khóa theo ID trước khi đọc/so giá trị cũ. Ô khóa/sai kiểu làm hủy cả lượt.
  Quy tắc đọc dấu phân cách số hiện hành được giữ.
- Bổ sung kiểm tải 14.09: khi caller đã xác định một bảng không phải Vận đơn
  mới, manager ghép trực tiếp phạm vi cấp bậc và cấp thêm/dùng chung. Không
  dựng truy vấn con ID và nhánh JOIN nghiệp vụ Vận đơn mới cho bảng đó.
  Điều kiện dùng chung vẫn đọc trong SQL; không dùng metadata bảng cũ để
  cấp quyền. Truy vấn toàn hệ thống và ngoại lệ Vận đơn mới giữ nguyên.

## Dòng mới

Các bảng chuyển đổi hiện dòng nháp cho người có quyền tạo dòng. Vận đơn mới
không tạo dòng bằng cách này. Negative ID tồn tại trong RAM; server trả ánh xạ
ID sau commit. Không lấy bộ lọc làm giá trị đầu vào. Thông báo sau lưu giải
thích dòng được xếp lại hoặc ra ngoài bộ lọc.

Tái sử dụng lõi kiểm kiểu/tính cột của nhập hàng loạt, đặt trong giao dịch ngoài
để paste tạo/cập nhật được cả hoặc không gì. Callback trả ID theo đúng thứ tự;
biên nhận chống tạo trùng khi mất phản hồi. Lỗi chỉ đúng ID tạm và mã cột.

Undo tạo dòng phải có biên nhận nguồn cùng người dùng, phiên bản dòng và không
có chỉnh sửa từ người khác. Xung đột hủy toàn lượt, kể cả sửa ô cũ đi kèm. Undo
xóa mềm; Redo khôi phục cùng ID. Retry lượt Undo dùng lại mã thao tác.

## Xóa và khôi phục bảng

Manager phòng ban sở hữu/Admin được xóa; Staff, Leader hoặc chỉ có Grant không
được xóa/khôi phục. Vận đơn mới được bảo vệ. Người dùng nhập đúng tên bảng,
được thông báo giữ dữ liệu để khôi phục. Mục Đã xóa nằm ở trang thư mục.

Chỉ xóa mềm TableDef, không xóa lần lượt hàng/cột. Chặn nếu có biểu mẫu đang
hoạt động hoặc tác vụ nhập/tính lại cột Pending/Running. Khôi phục không đổi ID,
mã hoặc dữ liệu; thư mục bị xóa thì bảng về ngoài thư mục. Mã bảng không tái dùng.

Khóa advisory PostgreSQL giao dịch có namespace riêng theo table ID: sửa dùng
shared lock; xóa/khôi phục dùng exclusive lock. Sau khi lấy khóa mới kiểm bảng
còn khả dụng. Khóa chia sẻ cho phép hai giao dịch sửa dòng khác nhau cùng chạy;
khóa hàng/CAS vẫn giải quyết xung đột dữ liệu. Nhập/tính lại nền kiểm ở từng lô,
không biến cả công việc dài thành một transaction lớn. Tạo/kích hoạt biểu mẫu và
xác nhận job cũng phối hợp với khóa, tránh xuất hiện phụ thuộc sau khi đã xóa.

Request kế tiếp của tab đang mở bị từ chối thì xóa nội dung/cache/nháp khỏi UI
và dừng polling/lưu. Tải file xuất kiểm lại bảng và ID dòng hiện hành. File nền
cũ không có danh sách ID phải xuất lại, vì không thể chứng minh còn đúng quyền.

## Tương thích và vận hành

URL ghi HTMX cũ trả 409 yêu cầu giữ nội dung chưa lưu và tải lại; không ghi vòng
qua CAS. Giữ endpoint quản lý cấu trúc và nhập/xuất đang được sử dụng.
`crm-frame.css` giữ khung/thư mục; `grid-formats.css` giữ định dạng đã lưu.
Không thêm dependency, model hoặc migration trong chiến dịch này.

Các cờ tối ưu vẫn giữ mặc định; đường READ/SYNC v2 của bảng chuyển đổi chỉ mở
sau hồi quy tương ứng. Không coi tốc độ HTTP là bằng chứng cuộn/nhập mượt.

Khi được duyệt triển khai, cập nhật đồng bộ các process ghi cùng codebase,
không chạy lẫn worker phục vụ giao thức ghi cũ. Phiên này không tự triển khai.

## Kiểm chứng

Xem [biên bản CRM-UPDATE](../kiem-chung-crm-update-20260912.md). Chỉ ghi hoàn tất
sau các lớp functional, Chrome và kiểm tải tương ứng; lỗi nền/skip ghi riêng.
