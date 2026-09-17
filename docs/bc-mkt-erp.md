# Báo cáo KNERP theo BC MKT — 09.09.2026

Nguồn: `CRM_ Tân.xlsx`, sheet `BC MKT`, B4:N5 (trường/công thức), B8:B11
(cách xem). Chủ dự án yêu cầu giữ đúng tên và công thức Excel.

## Hợp đồng chỉ tiêu

| Tên Excel | Công thức ERP |
|---|---|
| CPO | CPQC / Số đơn |
| Giá Mess | CPQC / Số Mess |
| CPQC/Doanh số | CPQC / Doanh số |
| Hóa đơn/Doanh thu | Giá Mess / CPO — đúng K5/J5 |
| AOV | Doanh số / Số đơn |

Cột M không đổi thành Hóa đơn / Doanh thu và không đổi tên thành tỷ lệ chốt.
Các tỷ số giữ dạng chia của Excel, không tự nhân 100. Tính từ tổng đầu vào;
không làm tròn trung gian. Mẫu số 0 hoặc đầu vào thiếu hiện `—`.
Doanh thu/Hóa đơn thiếu cấu hình thì hiện `—`, không lấy Doanh số thay Doanh thu.

Nhận diện bảng Marketing bằng các tên cột Marketer, Số Mess, CPQC, Số đơn,
Doanh số (chuẩn hóa khoảng trắng/hoa thường). Cột số đọc theo định nghĩa đã có;
không thay JSON hay ColumnDef. Bảng khác dùng thống kê hiện hành.
Chỉ ngày hoặc Marketer hoặc sản phẩm là cột nhóm trong mỗi tab tổng hợp;
không phải mỗi dòng tổng hợp đều chứa cả Ngày và Marketer.

## Luồng và quyền

Lịch sử lọc biểu mẫu/phòng ban từ báo cáo trong quyền, giữ ngày và người nộp.
Liên kết thống kê giữ nguồn và kỳ; thống kê vẫn theo phạm vi vai trò, không
mặc định giới hạn vào riêng người nộp của dòng vừa bấm.
Staff bản thân; Leader team và bản thân; Manager phòng ban; Admin toàn công ty.
URL báo cáo và xuất ngoài quyền bị từ chối; nguồn dashboard không hợp lệ không
rơi về một nguồn khác. Không có cấp bậc CEO riêng ở đợt này.

Tổng quan đọc một nguồn Marketing, mặc định đầu tháng tới hôm nay. Phân biệt
không có nguồn, không có dữ liệu, nguồn không hợp lệ và lỗi khối. Khối hỏng
không kéo trang Tổng quan xuống. Xuất Excel dùng cùng kết quả tính với màn hình.

## Giới hạn và kiểm chứng

Đã kiểm công thức, 4 cấp quyền, bộ lọc, xuất Excel, trường thiếu/0 và lỗi khối.
13 test mới đạt; hồi quy reports/culture/navigation và CRM đạt. Lịch sử và tổng
hợp giữ các test trần 10 truy vấn. Sau tách helper lịch sử, chạy lại reports đạt.
Trình duyệt local 1440x900 và 390x844: Tổng quan sang chi tiết, đổi nhóm,
lọc lịch sử sang báo cáo giữ nguồn/kỳ, mục thị trường chờ và Đánh giá nhân sự đạt.
Không ghi dữ liệu nghiệp vụ bằng trình duyệt; đăng nhập có nhật ký phiên bình thường.

Chưa làm thị trường, định nghĩa/nguồn Doanh thu-Hóa đơn, báo cáo muộn/trừ điểm,
thống kê Sale/Vận đơn/CSKH theo đặc tả mới. Không migration, seed hay dependency.
