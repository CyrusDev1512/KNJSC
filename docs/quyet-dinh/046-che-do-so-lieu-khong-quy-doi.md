# ADR-046 — Chế độ số liệu: không quy đổi tiền, mỗi dòng một loại tiền, Cộng theo ngày / Từng lần nộp

| Mục | Nội dung |
|---|---|
| Ngày | 28.09.2026 |
| Trạng thái | Xong local 28.09.2026, PR nháp vào `main`; chờ chủ dự án nghiệm thu và Codex phát hành VPS |
| Thay thế / bổ sung | **Thay quyết định 1 của ADR-042** (quy ₫ trong truy vấn rồi mới cộng). Bổ sung ADR-042 đợt 2 (bố cục khối), đợt 3 (ngưỡng màu), đợt 4 (Bảng dữ liệu); ADR-038 phần (TT) |

## Bối cảnh

Trên VPS, nhân viên nộp CPQC **13 250 000** mà Báo cáo tổng hợp và Bảng dữ liệu hiện một con số khổng lồ
khác. Nguyên nhân: loại tiền của báo cáo tự theo Thị trường (Canada → CAD), và ADR-042 quyết định 1 nhân mọi
cột tiền với tỉ giá của loại tiền đó rồi mới cộng — 13.250.000 "CAD" × 17.500 = 231.875.000.000 ₫.

Chủ dự án 28.09.2026: *"tôi cần con số giữ nguyên, đã có trường đơn vị ngay bên cạnh rồi, ai yêu cầu là quy
đổi tiền?"* — và *"nhân viên báo cáo số tiền là 8000 thì hiển thị là 8000, kể cả báo cáo 2 lần trong 1 ngày
thì lần 1 8000 lần 2 7000 thì cứ hiển thị ra như thế"*. Quy ₫ là lựa chọn của người viết ADR-042 khi chủ dự án
chỉ hỏi vì sao số để trống lúc lẫn loại tiền (23.09), không phải yêu cầu của chủ dự án.

Chủ dự án chọn "cách 3: xem được theo chế độ, chế độ nằm trong bộ lọc", duyệt mockup "Chế độ xem số liệu"
cùng ngày và trả lời ba câu: mặc định Cộng theo ngày; Loại tiền vẫn tự theo Thị trường; giữ dòng TỔNG CỘNG ở
chế độ Từng lần nộp.

## Quyết định

1. **Không quy đổi.** Số tiền hiện đúng như đã nhập, không nhân tỉ giá, không hậu tố ₫. Nguồn có cột Loại tiền
   thì **loại tiền là một chiều nhóm** (`aggregations.summarize(currency_expression=…)`, khoá `loai_tien` và
   hạng xếp `hang_tien`): mỗi dòng báo cáo một loại tiền, một người nộp USD và CAD trong ngày là hai dòng.
   Không bao giờ cộng hai loại tiền (quy tắc bắt buộc 6, BR-8).
2. **TỔNG CỘNG tách theo loại tiền** — mỗi loại tiền một dòng "TỔNG CỘNG · USD", ô Loại tiền riêng ở cột
   định danh cuối (sát cột số), ở mọi khối: toàn kỳ, từng ngày, Gộp, cách xem khác, Excel. Thứ tự loại tiền
   theo `Currency` (`core.money.currency_rank`), trống cuối. Tổng chung (`totals`) chỉ còn số đếm khi có hơn
   một loại tiền — cột tiền để trống (None) để không chỗ nào vô tình hiện số cộng lẫn.
3. **Dòng chưa có loại tiền** (báo cáo cũ) thành nhóm riêng "Chưa rõ", không vào loại tiền nào; cảnh báo nêu
   số dòng và cách sửa (Sửa báo cáo, chọn Thị trường — hệ thống tự điền loại tiền). KRW (chưa có tỉ giá) không
   còn là ngoại lệ vì không còn quy đổi.
4. **Chế độ số liệu nằm trong bộ lọc** (`che_do`, ô Chế độ ở panel lọc, chip "Chế độ" luôn hiện, không ×):
   - **Cộng theo ngày** (`cong`): mỗi người mỗi ngày một dòng cho mỗi loại tiền; nộp nhiều lần thì cộng, chỉ
     cộng cùng loại tiền. Mặc định của Báo cáo tổng hợp (như trước).
   - **Từng lần nộp** (`tung-lan`): mỗi lần nộp một dòng, số đúng như nhập; cột **Lần nộp** "Lần 2 · 16:40" —
     số thứ tự trong ngày của người đó theo giờ nộp (hàm cửa sổ `ROW_NUMBER` trong SQL nên đúng cả khi phân
     trang), kèm ngày nộp nếu khác ngày báo cáo. Mặc định của **Bảng dữ liệu dạng báo cáo** (giữ đúng "mỗi lần
     nộp một dòng" của ADR-042 đợt 4). Khối toàn kỳ theo nhân sự vẫn đứng đầu (Bảng dữ liệu có từ đợt 4); Gộp
     thì một khối "Mọi lần nộp trong kỳ" (Ngày · Nhân sự · Lần nộp · Loại tiền).
   - Chỉ cách xem Tổng hợp của nguồn Sale/MKT có chế độ (`activity_service.has_modes`); cách xem khác và nguồn
     Vận đơn bỏ qua `che_do`, ô Chế độ ẩn (JS khi đổi Cách xem; Vận đơn không render).
5. **(TT) đối soát theo loại tiền của đơn** (`marketing_actuals`): khoá có loại tiền của vận đơn, không
   `to_vnd`. Đơn USD của marketer vào dòng USD của marketer đó; marketer không có báo cáo USD trong ngày thì đơn
   USD không hiện ở đâu — cùng nguyên tắc "báo cáo là của dòng báo cáo" của ADR-038. Nguồn không ánh xạ Loại
   tiền thì (TT) chỉ còn số đơn.
6. **Màu:** so tương đối (±10 %) với dòng TỔNG CỘNG **cùng loại tiền**. Ngưỡng tuyệt đối của chỉ tiêu tiền (CPO,
   Giá Mess, AOV — `ReportColumn.money`) đặt theo ₫ nên **chỉ tô dòng VND**; dòng loại tiền khác không tô theo
   ngưỡng đó (mockup đã ghi). Ngưỡng tỉ lệ (Tỉ lệ chốt, CPQC/DS Chốt) tô mọi loại tiền.
7. **Thẻ Tổng quan:** mỗi chỉ tiêu một hàng (TL-60), mỗi loại tiền một cột có tiêu đề mã tiền.
8. **Hiện số có dấu chấm:** Bảng dữ liệu xem thô in số `13.250.000`, giữ nguyên số lẻ đã lưu
   (`core.money.format_decimal`, `styling.list_cells`). Ô số trên form Nộp báo cáo, Sửa báo cáo, điền biểu mẫu
   (`report-entry.js`): gõ toàn chữ số thì dấu chấm tự chèn ngay khi gõ; người dùng tự gõ "." hay "," thì để
   nguyên đến khi rời ô rồi viết lại theo đúng luật `parse_money` của máy chủ — "8000.50" thành "8.000,5",
   không thành 800.050. Số nguyên bỏ mọi dấu như máy chủ.
9. **Excel theo khối cho mọi cách xem** (cả Theo nhân viên/sản phẩm/thị trường/phòng ban): dòng Tổng đứng đầu
   như màn hình (trước đây ở cuối), cột Loại tiền, phụ đề ghi Chế độ.

## Hệ quả

- `SummaryResult.converted/unconverted`, `core.money.vnd_rate_expression` bị xoá. `to_vnd`, `rates_label` và
  `EXCHANGE_RATES_VND` chỉ còn cho Bảng xếp hạng doanh số (Q71).
- AC-42.1, AC-42.2 rút (gạch trong docs/04), thay bằng AC-46.1 → AC-46.10. AC-38.1/38.2/38.3, AC-42.8, AC-42.13,
  AC-22.18 đổi chữ theo.
- Dữ liệu đã lưu **không đổi**; chỉ cách hiện đổi, nên số cũ tự hiện đúng như lúc nhập.
- Truy vấn: đường trong bộ nhớ không thêm lệnh (≤ 10 như AC-42.4); đường quá trần `MAX_GROUPS` thêm một lệnh
  nhóm theo loại tiền.

## Giới hạn và việc để lại

- **Ngưỡng tiền theo từng loại tiền** (CPO ≤ 5 USD, ≤ 7 CAD…) chưa có: ngưỡng tiền hiện đặt theo ₫ nên gần như
  không tô dòng nào (dòng VND chỉ còn ở báo cáo cũ). Cần form ngưỡng theo loại tiền — chờ chủ dự án.
- Đơn vận đơn khác loại tiền với mọi báo cáo của marketer trong ngày không hiện ở (TT).
- Người nộp báo cáo cho ngày khác (nộp bù) có "Lần N" tính theo giờ nộp, kèm ngày nộp để phân biệt.
- Cột ghim trái nhiều hơn (tới sáu cột ở Từng lần nộp): màn hẹp dưới 480 px còn ít chỗ cho cột số.
