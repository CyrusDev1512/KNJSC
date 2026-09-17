# ADR-022 — Bàn điều hành KN CRM theo nguồn dữ liệu

| Mục | Nội dung |
|---|---|
| Trạng thái | Đã triển khai và kiểm chứng local; xem test-log |
| Ngày | 11.09.2026 |
| Phạm vi | `GET /thong-ke/` của KN CRM, liên kết từ KN ERP và Trang chủ CRM |
| Thay thế | Đích hiển thị Thống kê Vận đơn riêng trong ADR-021; không thay hợp đồng lưới master, quyền hoặc Báo cáo tổng hợp KN ERP |

## Bối cảnh

Trang Thống kê theo ADR-021 chỉ phục vụ `van_don_moi`. Chủ sở hữu cần một nơi
nhìn nhanh nhịp Marketing → Sale → Vận đơn nhưng dữ liệu vẫn nằm trong các bảng
động, khác nhau theo bộ phận và quyền người xem. Hệ thống chưa có khóa nối từng
đơn Sale với Vận đơn và chưa có tỷ giá dùng chung cho báo cáo này, nên không được
suy diễn thất thoát đơn, cộng lẫn tiền tệ hoặc gọi nhận định theo quy tắc là AI.

## Quyết định

1. `/thong-ke/` không có `nguon` là góc nhìn tổng hợp; có
   `nguon=<mã bảng>` là góc nhìn chuyên sâu một bảng. Mọi bảng đang hoạt động
   trong `TableDef.objects.in_scope` đều có trong danh sách. Nguồn ngoài phạm vi,
   đã xóa hoặc ngừng hoạt động trả 403 và ghi audit từ chối.
2. Khoảng mặc định là đầu tháng đến hôm nay theo giờ Việt Nam. `tu`, `den` sai
   hoặc đảo thứ tự chỉ hiện lỗi biểu mẫu, không chạy aggregate. Góc tổng hợp dùng
   tối đa một nguồn Marketing, một Sale và một Vận đơn; mặc định lấy nguồn có
   dòng cập nhật gần nhất, riêng Vận đơn ưu tiên `van_don_moi`.
3. Profile được nhận diện một lần theo thứ tự Vận đơn mới → Marketing → Sale →
   Chung. `van_don` cũ là nguồn lịch sử ở chế độ chung. Bảng thiếu nhãn Ngày nêu
   rõ phần thiếu, không đoán cột. Không tạo bảng hoặc biểu mẫu Sale mới.
4. Marketing tái sử dụng nhận diện/công thức hiện có; CPO, AOV và tỷ lệ lấy tổng
   tử số chia tổng mẫu số. Sale tổng hợp theo ngày/người bán; AOV bằng tổng doanh
   thu chia tổng đơn. Kỳ trước là khoảng liền trước có cùng số ngày; mẫu số kỳ
   trước bằng 0 dùng câu “mới xuất hiện” hoặc “chưa có cơ sở so sánh”.
5. Tiền tách theo Loại tiền; thiếu cột này ghi “Đơn vị theo bảng”. Không quy đổi
   hoặc cộng tiền khác loại. Sale–Vận đơn chỉ đối chiếu tổng đơn cùng kỳ và gọi
   chênh lệch là “cần đối chiếu”, không kết luận đơn thất lạc.
6. Tối đa ba nhận định theo thứ tự: thiếu dữ liệu/không đối soát, vượt ngưỡng đã
   cấu hình, trạng thái Vận đơn cần kiểm tra, biến động lớn nhất, rồi thiếu dữ
   liệu. Mỗi nhận định có tình hình, bằng chứng, tên nguồn và liên kết mở bảng với
   đúng bộ lọc ngày/trạng thái. Hệ thống không tạo việc, gửi thông báo hay sửa dữ
   liệu.
7. `EXECUTIVE_OWNER_USERNAMES` chỉ đổi nhãn sang “Bàn điều hành chủ sở hữu” khi
   username thuộc danh sách, tài khoản hoạt động và cấp Admin. Cấu hình không cấp
   thêm quyền dữ liệu.

## Hiển thị và khả năng truy cập

Thiết kế theo “Disciplined Operations Desk”: nền trung tính, indigo tiết chế,
xanh/vàng/đỏ chỉ báo trạng thái, mật độ thông tin cao nhưng mỗi KPI chỉ có một
vị trí chuẩn. Cột SVG có mặt trước đúng tỷ lệ và chiều sâu trang trí cố định 6px;
đường SVG giữ phẳng. Mỗi biểu đồ hiển thị tối đa 10 nhóm, bảng đối chiếu vẫn phân
trang toàn bộ nhóm. Khoảng không quá 45 ngày nhóm ngày, 46–180 ngày nhóm tuần,
dài hơn nhóm tháng. SVG có `title`, nhãn số, bảng thay thế, focus bàn phím và tôn
trọng `prefers-reduced-motion`. Không thêm thư viện biểu đồ hoặc dependency.

## Kiến trúc, quyền và giới hạn

View chỉ kiểm tham số, chọn nguồn và render. Bộ điều phối gọi profile, bộ sinh
insight và bộ chuẩn bị biểu đồ. Tất cả aggregate bắt đầu từ
`TableDef.objects.in_scope` và `DataRecord.objects.in_scope`; chi tiết Vận đơn
dùng `WaybillItem.objects.for_records`. Tổng hợp không nạp toàn bộ dòng vào
Python và không tăng số truy vấn theo số dòng hoặc số bảng ngoài ba nguồn chọn.
Một profile lỗi hiện “tạm chưa khả dụng” mà không làm mất phần còn lại.
Snapshot Vận đơn đặt `work_mem` cục bộ 64MiB trong đúng transaction aggregate
để CTE 300.000 dòng không tràn ra đĩa; giá trị tự hoàn nguyên sau truy vấn và
không đổi cấu hình PostgreSQL toàn hệ thống.

Không có realtime, polling, cache, worker hoặc hành động AI trong quyết định này.
KN ERP giữ `/bao-cao/tong-hop/` và xuất Excel làm nơi đối chiếu, chỉ thêm nút mở
Bàn điều hành. Trang chủ CRM chỉ thêm liên kết. Bộ lọc `f_*`, `group`, phân trang
biểu đồ và chuyển hướng Thống kê Vận đơn cũ tiếp tục tương thích.

## Kiểm chứng

Tiêu chí tại [AC-22](../04-tieu-chi-nghiem-thu.md), lệnh và ma trận tại
[kế hoạch kiểm thử](../06-ke-hoach-kiem-thu.md), kết quả thực chạy tại
[test-log](../test-log.md). Phép đo riêng 20 request sau warmup đạt p95 89,07ms
trên 20.000 dòng Sale, 333,72ms trên 100.000 dòng Vận đơn, 893,26ms trên
300.000 dòng Vận đơn và 733,64ms ở góc tổng hợp hai nguồn lớn. Số query của Vận
đơn giữ 12 ở cả hai cỡ; đỉnh cấp phát Python cùng 0,25MiB. Kết quả local không
thay thế phép kiểm tải đồng thời trên máy chủ thật.
