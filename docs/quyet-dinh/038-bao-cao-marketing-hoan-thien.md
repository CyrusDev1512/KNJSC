# ADR-038 — Hoàn thiện báo cáo Marketing: nộp tự do, Tệp khách hàng, Doanh thu suy ra từ vận đơn, Kế toán sửa, Chọn nhanh

| Mục | Nội dung |
|---|---|
| Trạng thái | Đã áp dụng local (chờ phát hành VPS) |
| Ngày | 18.09.2026 |
| Người quyết định | Chủ dự án (sheet MKT, Phân quyền của `Quản trị nội bộ.xlsx`; các câu hỏi chốt trong phiên Claude Code) |
| Thay thế cho | Khoá "một bản/người/ngày" của BR-2 (docs/02) và công thức K/J của Hóa đơn/Doanh thu xác nhận 09.09.2026 (`reports/marketing.py`); bổ sung ADR-022, ADR-032 |

## Bối cảnh

Sheet MKT mô tả trọn màn hình Marketing: INPUT (Báo cáo hiệu quả: Ngày, Marketer, Team,
Sản phẩm, Quốc gia, **Tệp Khách hàng**, Số Mess, CPQC, Số đơn, Doanh số, Hóa đơn; nhân viên
nộp giữa ca và sáng hôm sau) và OUTPUT (tổng hợp từ đầu tháng; cột Doanh thu, CPO, Giá
Mess, CPQC/Doanh số, Hóa đơn/Doanh thu, AOV; bộ lọc Chọn nhanh, Ngày, Sản phẩm, Quốc gia,
Tệp Khách hàng, MKT/Team cho admin; chú ý "Doanh thu: lấy dữ liệu từ file vận đơn, trạng
thái thu tiền"). Sheet Phân quyền: Kế toán – Kiểm soát nội bộ chỉnh sửa số liệu.

Mã tới 18.09: biểu mẫu MKT thiếu Tệp khách hàng; `DailyReport` chặn một bản/người/ngày;
Doanh thu là cột nhập tay; Hóa đơn/Doanh thu tính Giá Mess ÷ CPO (K/J của tệp cũ); Kế toán
không xem/sửa được báo cáo; không có Chọn nhanh.

## Các lựa chọn đã cân nhắc

| Việc | Lựa chọn | Chọn |
|---|---|---|
| Tệp khách hàng | (a) cột Chọn một với `ColumnDef.options`, Manager/Leader MKT thêm giá trị ngay ô chọn; (b) bảng danh mục mới + màn quản trị; (c) sổ theo nhãn ý nghĩa mới (phải mở rộng enum `Meaning`) | **(a)** — dùng cơ chế sẵn có của ADR-013, không bảng mới |
| Nộp trong ngày | giữ một bản/ngày; nộp tự do, mỗi lần một dòng; nộp đè bản cũ | **nộp tự do** — hệ thống tự ghi ai, lúc nào; sửa số qua Sửa báo cáo (ADR-032) |
| Doanh thu | nhập tay như cũ; suy ra từ vận đơn theo ngày thanh toán; suy ra theo ngày lên đơn | **suy ra theo ngày lên đơn** (`val_date`) — `ngay_tt` là chữ tự do trong JSON, không lọc tin cậy |
| Số Doanh thu | tổng tiền đã thu thực tế; giá trị đơn đã thanh toán đủ | **tổng tiền đã thu** (`WaybillItem.paid_amount`, chính là `so_tien_tt`) |
| Kế toán | chỉ xem; xem và sửa mọi báo cáo; xem và sửa + bỏ | **xem và sửa mọi báo cáo**, không bỏ báo cáo người khác |

## Quyết định

1. **Nộp không giới hạn số lần trong ngày.** Bỏ ràng buộc `report_unique_per_person_per_day`
   (migration `reports/0004`, chiều ngược thêm lại ràng buộc nên **thất bại nếu đã có trùng**
   — quay lui bằng backup). Màn nộp cho biết hôm nay đã nộp bao nhiêu lần. BR-2 đọc lại là:
   không xoá cứng, không sửa ngoài luồng sửa có lịch sử.
2. **Tệp khách hàng** là cột `tep_khach_hang` (Chọn một) của bảng báo cáo Marketing, do
   `configure_erp_reports` tạo với danh sách mặc định theo sheet (Filipino, Spanish,
   Portuguese, Vietnamese, Italian, French, English, Chinese, Indian); ánh xạ
   `ReportSource.columns["segment"]`; bộ lọc `tep` ở Báo cáo tổng hợp (giá trị lạ → 400,
   `__missing__` = chưa có). Quốc gia vẫn là trường nhập.
3. **Doanh thu suy ra** = tổng `paid_amount` chi tiết của vận đơn (`workflow = waybill`) có
   `WaybillAssignment.marketing` là marketer của dòng báo cáo, cùng kỳ (theo ngày lên đơn),
   cùng sản phẩm/quốc gia khi lọc; nhóm theo cùng khoá với báo cáo (ngày, nhân sự, sản
   phẩm, thị trường, phòng ban). Chỉ dòng báo cáo có tiền vận đơn tương ứng mới nhận số; tổng
   bằng tổng các dòng (AC-5.4). Vận đơn chưa phân công Marketing hoặc chưa có loại tiền không
   vào Doanh thu. Tiền vận đơn lẫn đơn vị với tiền báo cáo thì cảnh báo, để trống chỉ tiêu
   tiền như quy tắc hiện có. Cột nhập tay `doanh_thu` gỡ khỏi biểu mẫu (cột cũ giữ để đọc
   lịch sử); công thức từng dòng `hoa_don_doanh_thu` bỏ vì không tính được từ một dòng.
   Lọc theo Tệp khách hàng thì Doanh thu để trống: vận đơn không ghi tệp, không chia được.
4. **Hóa đơn/Doanh thu = Hóa đơn ÷ Doanh thu** theo đúng nhãn, thay xác nhận K/J ngày 09.09.
5. **Kế toán** (bộ phận `ke-toan`, hằng `ACCOUNTING_DEPARTMENT_CODE`) thấy mọi báo cáo ở
   Lịch sử, Báo cáo tổng hợp, Bảng dữ liệu chỉ đọc của bảng báo cáo, và sửa được qua Sửa báo
   cáo có lịch sử. Phạm vi mở ở đúng ba chỗ Custom Manager/service (`DailyReport`,
   `TableDef`/`DataRecord` với bảng có nguồn báo cáo, `activity_service.records`), không ở view.
6. **Chọn nhanh** kỳ: Hôm nay, Hôm qua, 7 ngày, Tháng này, Tháng trước — điền hai ô ngày rồi
   áp ngay.
7. **Báo cáo Nội dung** (CTR, CPM, video) làm đợt sau; không thêm nút "Loại báo cáo" chưa
   có tác dụng. Hạn nộp (giữa ca/9h) để mở (N1/H8).

## Lý do

Đúng sheet MKT mà không thêm bảng, thư viện hay màn quản trị mới; số tiền đã thu là số thật
của Vận đơn (ADR-018, 025) nên Doanh thu không cần ai gõ lại; mở phạm vi Kế toán ở Custom
Manager giữ quy tắc 11.

## Hệ quả

**Được gì:** Marketing nộp bao nhiêu lần cũng được, có Tệp khách hàng; Doanh thu và Hóa
đơn/Doanh thu tự đúng; Kế toán làm việc được trên số liệu; lọc kỳ nhanh.

**Mất gì:** báo cáo cũ có `doanh_thu` nhập tay không còn hiện số đó (Doanh thu nay suy
ra); nhóm theo sản phẩm chỉ khớp khi tên sản phẩm của báo cáo trùng danh mục (đúng như sổ
chọn PRODUCT đang ép).

**Chỗ cần cẩn thận về sau:** đổi cách tính ngày (thanh toán thay vì lên đơn) là quyết
định mới; muốn Doanh thu cho marketer không có dòng báo cáo thì phải thêm cách xem riêng.

## Điều kiện xem lại

Khi có cột ngày thanh toán chuẩn trên vận đơn; khi làm Báo cáo Nội dung; khi chốt hạn nộp.
