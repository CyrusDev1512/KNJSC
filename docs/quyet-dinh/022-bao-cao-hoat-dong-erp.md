# ADR-022 — Ánh xạ báo cáo hoạt động tại KNERP

- Ngày: 10.09.2026.
- Trạng thái: quyết định triển khai theo kế hoạch chủ dự án đã duyệt;
  nghiệm thu theo test-log, không suy từ trạng thái ADR.
- Liên quan: KNJSC_PROBLEM 05.1–3, 05.8 và một phần 06.2; ADR-001, ADR-018.

## Bối cảnh

Marketing, Sale và Vận đơn cần cách tổng hợp khác nhau. Tổng số đơn Vận đơn
phải dựa vào bản ghi và người được phân công, không dựa vào người tạo đơn hoặc
tên tự nhập. Thị trường báo cáo Sale/Marketing nay do người nộp chọn; dữ liệu
cũ thiếu trường không được suy diễn. Trách nhiệm tiền thuộc Kế toán/Kho,
không nằm trong báo cáo hoạt động dành cho Vận đơn.

## Quyết định

1. Giữ dữ liệu ở bảng động và tái sử dụng `reports/aggregations`, `Metric`,
   `SummaryResult`, phân trang, Excel và quyền `apply_scope` hiện có.
2. Thêm `ReportSource` OneToOne với TableDef: loại báo cáo và ánh xạ các cột.
   Đây là metadata của module reports, không phải kho dữ liệu thống kê mới.
   Migration 0002 không sửa bản ghi nghiệp vụ; cấu hình biểu mẫu là lệnh
   quản trị tường minh chạy nguyên tử, lặp lại được.
3. `activity_service` lấy bản ghi đã lọc quyền, áp bộ lọc, tổng hợp rồi tính
   chỉ tiêu. Ngày dùng val_date; thị trường dùng khóa JSON đã ánh xạ.
   Không đọc dữ liệu qua HTTP/HTML hoặc gọi service thống kê của CRM.
4. `DeliveryResult` bổ sung trạng thái vào SummaryResult; đơn đếm DISTINCT ID,
   lượng hàng cộng từ WaybillItem chưa xóa. Tổng từ các trạng thái được tái
   sử dụng cho màn hình, Excel và Tổng quan để tránh truy vấn tổng dư thừa.
5. **Chốt bổ sung 10.09.2026, thay hướng chuyển trang ban đầu:** chỉ giữ menu
   Báo cáo tổng hợp, URL `/bao-cao/tong-hop/` và `/bao-cao/tong-hop/xuat/` mở trực tiếp.
   URL hoạt động cũ chuyển về tổng hợp và giữ toàn bộ query; nguồn chưa cấu hình
   tiếp tục tổng hợp tổng quát như trước. Không đổi phép tính, dữ liệu hoặc quyền.
6. Tổng quan gọi từng khối độc lập, không cộng chồng các nguồn. Hiệu suất là
   các nhóm số liệu thực tế; không đưa thêm luật KPI/chấm điểm.

## Hệ quả và giới hạn

- Vẫn modular monolith; không dependency, API công khai, đồng bộ hoặc bảng
  vật lý theo tháng/bộ phận mới. Không sửa quyền hoặc màn hình tiền của CRM.
- Mỗi nguồn mới khác schema phải có ánh xạ được xác nhận. Không tự quét nội
  dung sản phẩm/họ tên để suy thị trường hoặc danh tính.
- Khi rollback migration, metadata ReportSource bị bỏ; báo cáo/đơn còn nguyên.
  Cần lưu cấu hình riêng nếu đã tùy biến trước khi rollback rồi cấu hình lại
  sau khi tiến tới. Kiểm migration chỉ chạy trên database pytest riêng.
- Giữ ràng buộc nộp báo cáo hiện có; chưa tự mở nhiều lần nộp/người/form/ngày.
- Doanh thu/Hóa đơn, quy tắc muộn, KPI, tuyển dụng và CSKH còn hoãn.

Kiểm chứng: [báo cáo triển khai](../bao-cao-hoat-dong-erp.md),
[test-log](../test-log.md), bộ test reports/tests/test_activity*.py và script
trình duyệt/Locust ERP. Chỉ đánh dấu vấn đề hoàn thành khi cả ba lớp kiểm đạt.

## Quyết định thay thế 16/09/2026

[ADR-032](032-ngay-he-thong-va-sua-bao-cao.md) bổ sung đầu vào Doanh thu/Hóa đơn Marketing,
ngày/nhân sự/tiền hệ thống và quyền sửa nội dung báo cáo có lịch sử. Các mục
muộn/KPI/tuyển dụng/CSKH còn hoãn như cũ.
