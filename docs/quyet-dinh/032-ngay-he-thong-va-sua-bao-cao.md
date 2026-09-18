# ADR-032 — Ngày hệ thống, sửa báo cáo và mẫu Marketing

Ngày chốt: **16/09/2026**. Chủ dự án duyệt triển khai local trong task báo cáo ERP.

## Quyết định thay thế

- Thay khóa nội dung tuyệt đối tại FR-4.4/BR-2: Staff không sửa báo cáo đã nộp;
  Leader sửa trong team phụ trách, Manager trong bộ phận, Admin toàn hệ thống.
  Ngày báo cáo, người nộp, team/bộ phận sở hữu và thời điểm nộp gốc vẫn bất biến.
- Mở báo cáo cũ trong Lịch sử → Sửa báo cáo → Lưu chỉnh sửa. Mọi lần thay đổi
  nội dung lưu `ReportRevision` chỉ nối thêm, với người sửa, thời điểm và bản
  trước/sau; chỉ người có quyền xem báo cáo mới xem được lịch sử này.
- Service kiểm lại phạm vi trong giao dịch, khóa dòng và so `updated_at` với
  phiên bản người sửa đã mở. Bản cũ trả 409, giữ nội dung nhập để đối chiếu;
  không âm thầm ghi đè. Lưới CRM không phải đường sửa vòng qua khóa báo cáo.
- Luồng bỏ báo cáo/xóa mềm có sẵn không được mở rộng quyền trong tác vụ này.

## Ngày, nhân sự và quốc gia

- Ô nhập ngày của ERP/CRM hiển thị `DD/MM/YYYY`, ngày giờ có thêm `HH:mm`;
  vẫn có lịch chọn ngày. Dữ liệu gửi form/HTMX/lưới giữ ISO; giờ hiển thị Việt Nam.
  Django Admin `/quan-tri/` không thuộc phạm vi thay giao diện này.
- Báo cáo mới tự lấy hôm nay theo giờ Việt Nam và người đang đăng nhập ở server.
  Ngày sinh, hạn công việc, ngày chuyển khoản và khoảng lọc vẫn được chọn.
- Biểu mẫu và lưới của nguồn báo cáo Sale/Marketing dùng danh mục quốc gia
  hệ thống, tiền theo ADR-031: Hoa Kỳ/USD, Canada/CAD, Philippines/PHP (từ 18.09.2026 thêm
  Châu Âu/EUR, Hàn Quốc/KRW, Nhật Bản/JPY, Úc/AUD — ADR-031 bổ sung).
  Người dùng không tự sửa loại tiền, ngày báo cáo hoặc danh tính trên lưới.
- Không tự quy đổi tỷ giá hoặc gán lại tiền tệ cho báo cáo lịch sử. Báo cáo
  tổng hợp/Excel/Tổng quan không công bố tổng tiền khi phạm vi lẫn đơn vị hoặc
  có dòng chưa rõ loại tiền; vẫn hiện số lượng và giải thích cách xử lý.
- `daily_service.submit_current` là đường nộp tương tác; `submit(report_date=...)`
  và `system_day` chỉ là API Python nội bộ cho khởi tạo/nhập lịch sử đã được phép,
  không nhận cờ bỏ khóa từ HTTP. Bộ mẫu local giữ ngày 14–16/09/2026.

## Mẫu Marketing

Thay phần hoãn Doanh thu/Hóa đơn của ADR-022: bổ sung hai đầu vào số tiền,
giữ Sản phẩm/Thị trường và trường phụ để phục vụ nghiệp vụ/lọc. Dữ liệu cũ
chưa có hai giá trị này tiếp tục để trống, không giả lập bằng 0.

| Chỉ tiêu | Công thức đã được chủ dự án xác nhận |
|---|---|
| CPO | CPQC / Số đơn |
| Giá Mess | CPQC / Số Mess |
| CPQC/Doanh số | CPQC / Doanh số |
| Hóa đơn/Doanh thu | **Giá Mess / CPO**, không suy lại theo tên cột |
| AOV | Doanh số / Số đơn |

Không nhân 100 các tỷ số này. Thiếu đầu vào hoặc chia 0 thì để trống. Các
trung gian không được làm tròn trước khi tính Hóa đơn/Doanh thu; chỉ làm
tròn kết quả hiển thị/lưu cuối. Tổng hợp tính lại từ đầu vào tổng, không cộng tỷ lệ.

## Vận hành và kiểm chứng

Local đã áp dụng `reports.0003_report_revision` và `configure_erp_reports`.
Chưa phát hành phạm vi báo cáo này lên VPS. Khi được duyệt phát hành cần chạy
migration và command metadata; không chỉ chép template. Rollback migration
0003 bỏ bảng lịch sử chỉnh sửa, vì vậy không rollback trên dữ liệu thật đã có
lịch sử nếu chưa sao lưu và duyệt riêng. Kiểm xuôi/ngược chỉ trên database test.

[Bằng chứng](../kiem-chung-bao-cao-erp-20260916.md). Lỗi 404 thêm sản phẩm trên
domain là hạng mục riêng còn mở, không được tuyên bố đã sửa trong ADR này.
