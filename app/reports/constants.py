"""Giá trị cố định của báo cáo Marketing — ADR-038. Khai một chỗ (quy tắc 7)."""

#: Cột "Tệp khách hàng" của bảng báo cáo Marketing (Chọn một, `ColumnDef.options`);
#: ánh xạ `ReportSource.columns["segment"]`, tham số lọc `tep` ở Báo cáo tổng hợp.
CUSTOMER_SEGMENT_COLUMN = "tep_khach_hang"
CUSTOMER_SEGMENT_LABEL = "Tệp khách hàng"
#: Danh sách mặc định theo cột "Tệp Khách hàng" của sheet MKT (`Quản trị nội bộ.xlsx`);
#: Leader/Manager Marketing thêm giá trị ngay ô chọn, Admin sửa ở Cột & cấp quyền.
CUSTOMER_SEGMENT_DEFAULTS = (
    "Filipino", "Spanish", "Portuguese", "Vietnamese", "Italian",
    "French", "English", "Chinese", "Indian",
)

#: Cột nhập tay "Doanh thu" của mẫu cũ (ADR-032): không còn trên biểu mẫu vì Doanh thu
#: nay suy ra từ vận đơn; cột giữ lại để đọc báo cáo lịch sử.
LEGACY_REVENUE_INPUT = "doanh_thu"
#: Cột tính từng dòng "Hóa đơn/Doanh thu" của mẫu cũ — bỏ, vì chỉ tính được ở mức báo cáo.
LEGACY_ROW_FORMULA = "hoa_don_doanh_thu"

#: Giá trị lọc "chưa có" cho Thị trường / Tệp khách hàng (`__missing__` trên URL)
MISSING_FILTER = "__missing__"
