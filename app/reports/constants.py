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

# ── Tô màu Báo cáo tổng hợp (AC-22.16, chủ dự án 19.09 theo ảnh mẫu) ──────────
#
# Nhận diện theo **nhãn cột** vì mã chỉ tiêu khác nhau giữa hai đường dựng cột
# (`activity_service.project_metrics` dùng khoá FORMULAS, `marketing.adapt` dùng
# `__mkt_metric_*`), còn nhãn thì cố định.

#: Chỉ số quan trọng — tô nền cả cột để mắt bắt ngay, như ảnh mẫu.
FOCUS_METRICS = ("Tỉ lệ chốt", "CPO", "Giá Mess", "CPQC/Doanh số")

#: Chiều tốt của từng chỉ tiêu: "cao" = càng cao càng tốt, "thap" = càng thấp càng tốt.
#: **Chỉ chỉ tiêu tỉ lệ.** Cột cộng (Số Mess, Số đơn, Doanh số, Doanh thu, CPQC, Hóa đơn)
#: cố ý không có mặt: mốc là tổng của mọi dòng nên dòng nào cũng nhỏ hơn, tô màu là vô nghĩa.
#: Hóa đơn/Doanh thu cũng để trống vì chưa rõ cao hay thấp mới là tốt — chờ chủ dự án chốt.
METRIC_DIRECTION = {
    "Tỉ lệ chốt": "cao", "AOV": "cao",
    "CPO": "thap", "Giá Mess": "thap", "CPQC/Doanh số": "thap",
}

#: Mốc so sánh là dòng "Tổng trong bộ lọc" của chính bộ lọc đang xem — không có con số
#: tuyệt đối nào bịa ra. Hơn mốc 10 % về phía tốt là đạt, kém mốc 10 % là cảnh báo;
#: ở giữa để trơn. Chủ dự án chốt ngưỡng tuyệt đối thì thay chỗ này.
THRESHOLD_BAND = "0.10"
