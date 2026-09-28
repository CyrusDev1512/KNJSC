# Kiểm chứng — Chế độ số liệu: không quy đổi, mỗi dòng một loại tiền (ADR-046, TL-65) — 28.09.2026

Nhánh `claude/che-do-so-lieu-bao-cao` tách từ `main` (`85f7fc1`), máy ảo Claude Code, PostgreSQL 16 cục bộ,
Chromium không màn hình (Playwright). Không migration, không thư viện mới.

Chủ dự án báo trên VPS: CPQC nhập **13 250 000** mà Báo cáo tổng hợp và Bảng dữ liệu hiện số khổng lồ; muốn thấy
**13.250.000**; nộp hai lần 8000 và 7000 thì hiện đúng như thế. Duyệt mockup "Chế độ xem số liệu" (cách 3, chế độ
nằm trong bộ lọc) và ba câu: mặc định Cộng theo ngày; Loại tiền vẫn tự theo Thị trường; giữ TỔNG CỘNG ở Từng
lần nộp.

## Nguyên nhân (tái hiện local)

Báo cáo Canada → loại tiền CAD (tự theo Thị trường, ADR-031). ADR-042 quyết định 1 nhân mọi cột tiền với tỉ giá
của loại tiền dòng rồi mới cộng: 13.250.000 × 17.500 = **231.875.000.000 ₫**. Không phải lỗi nhập, không phải
lỗi lưu (dòng lưu đúng `"13250000"`), mà là cách hiện.

## Đã làm

| Phần | Thay đổi |
|---|---|
| Lõi (`aggregations`, `activity_service`) | Bỏ nhân tỉ giá. Loại tiền là một chiều nhóm (`loai_tien`, hạng xếp `hang_tien`); tổng theo loại tiền (`currency_sums` → `currency_totals`, `total_rows`); tổng chung chỉ giữ số đếm khi có hơn một loại tiền. (TT) khoá thêm loại tiền của đơn, không `to_vnd` |
| Chế độ | `che_do=cong` / `tung-lan`; Báo cáo tổng hợp mặc định Cộng theo ngày, Bảng dữ liệu mặc định Từng lần nộp. Từng lần nộp: khoá nhóm thêm id dòng và giờ nộp, "Lần N" bằng `ROW_NUMBER() OVER (PARTITION BY ngày, người ORDER BY giờ nộp)` |
| Bố cục (`layout`, `_bang_khoi.html`, CSS) | Cột ghim Loại tiền (cuối, sát cột số) và Lần nộp; mỗi loại tiền một dòng TỔNG CỘNG, các dòng tổng dính xếp chồng dưới hàng tiêu đề (`--total-i` × `--total-h`, JS đo lại chiều cao); khối Gộp của Từng lần nộp |
| Bộ lọc | Ô Chế độ (thẻ radio như mockup) ở panel lọc và thanh lọc Bảng dữ liệu; chip Chế độ không ×; JS ẩn ô khi đổi Cách xem khác Tổng hợp; nguồn Vận đơn không có ô |
| Excel | Mọi cách xem xuất theo khối như màn hình (dòng Tổng đứng đầu, cột Loại tiền), phụ đề ghi Chế độ |
| Tổng quan | Thẻ báo cáo: mỗi chỉ tiêu một hàng, mỗi loại tiền một cột (bảng nhỏ cuộn ngang, số không bẻ) |
| Màu | So tương đối với TỔNG CỘNG cùng loại tiền; ngưỡng tiền ₫ chỉ tô dòng VND (form Ngưỡng màu ghi rõ) |
| Hiện số | Bảng dữ liệu xem thô: `13.250.000`, giữ số lẻ đã lưu (`core.money.format_decimal`) |
| Ô nhập số (`report-entry.js`) | Gõ chữ số → chấm tự chèn; tự gõ "." hay "," → bỏ các chấm tự chèn trước đó, rời ô thì viết lại theo luật `parse_money`; phần lẻ giữ khi gõ tiếp; số nguyên bỏ dấu như máy chủ |
| Lỗi ngầm TL-66 | Theo nhân viên quá trần `MAX_GROUPS` gắn `team_name` hai lần → 500; Từng lần nộp quá trần không đánh dấu khoá (TT) dùng chung — cả hai sửa |

## Kiểm bằng pytest

PostgreSQL 16 cục bộ cổng 5434, settings test, không Docker.

| Lệnh | Kết quả |
|---|---|
| `pytest reports/tests forms_builder/tests core/tests tests/test_truy_vet.py -m "not trinh_duyet"` | 1.204 đạt |
| `pytest reports/tests forms_builder/tests tests/test_truy_vet.py -m "not trinh_duyet"` (sau hai sửa cuối: khoá (TT) dùng chung ở đường quá trần, chip Gộp) | 415 đạt |
| `tests/test_truy_vet.py` | Đạt — 291 tiêu chí, 278 tự động, 255 có bài (AC-46.1 → 46.10 đủ, AC-42.1/42.2 rút; tính cả tiêu chí của PR #59 gộp trước) |
| `pytest -m "not trinh_duyet" --ignore=tests/perf` — bộ đầy đủ kể cả bài chậm (`cham`) | **2.835 đạt**, 7 bỏ qua (thiếu điều kiện ngoài, như trước), 54 bài trình duyệt để chạy riêng — 7 phút |
| Bài trình duyệt (`trinh_duyet`) | Chạy sau commit đầu — ghi ở commit sau |

Bài cũ sửa theo số giữ nguyên (không còn × tỉ giá): `test_quy_vnd_va_tt` (AC-42.1/42.2 thành AC-46.1/46.2),
`test_mkt_derived_revenue`, `test_markets_currencies`, `test_nguong_va_loc_san_pham`, `test_bo_cuc_khoi`,
`test_bang_du_lieu_chi_tiet`, `test_activity`, `test_report_amendments`, `test_people_filters` (Excel cách xem một
khối: dòng Tổng đứng đầu như màn hình), `test_bo_cuc_bao_cao` (chip Chế độ). Bài mới: `test_che_do_so_lieu.py`
(AC-46.3 → 46.10), `test_o_nhap_so_e2e.py` (AC-46.10, Chromium).

## Kiểm bằng Chromium trên máy chạy thử

Cơ sở dữ liệu riêng `knjsc_bc_perf` (dữ liệu giả cỡ thật đã nạp cho TL-63: 20 marketer, 4 team, 30 ngày, khoảng
20 % người–ngày nộp hai lần, 1.819 vận đơn; bốn loại tiền USD, CAD, PHP, AUD và 5 dòng mẫu cũ trống loại tiền),
`runserver` settings dev, tài khoản `quantri`. Ảnh ở máy ảo (không commit).

| Kiểm | Kết quả |
|---|---|
| Khối toàn kỳ và khối ngày có cột Loại tiền, mỗi loại tiền một dòng TỔNG CỘNG ("TỔNG CỘNG · USD" …, "Chưa rõ" cuối) | Đạt, 1440 sáng/tối và 390 |
| Dòng TỔNG CỘNG dính khi cuộn khung bảng: 5 dòng xếp liền nhau ngay dưới hàng tiêu đề, không chồng | Đạt — 1440: tiêu đề 75 px, tổng ở 76/112/148/185/221 px, mỗi dòng 36 px; 390: 73 px, tổng 74/108/142/177/211 px, 34 px |
| Từng lần nộp: cột Lần nộp "Lần 1 · 11:32", "Lần 2 · 11:32"; CPQC 13.250.000 hiện đúng như nhập | Đạt |
| Gộp ở Từng lần nộp: một khối "Mọi lần nộp trong kỳ · 49 lần nộp"; chip "Gộp · mọi lần nộp một bảng" | Đạt (chip sửa trong lượt này, trước ghi "mỗi ngày một dòng") |
| Ô Chế độ ẩn khi đổi Cách xem sang Theo nhân viên, hiện lại khi về Tổng hợp | Đạt |
| Bảng dữ liệu dạng báo cáo mặc định Từng lần nộp; xem thô in 13.250.000, 4.800.000, CPO 1.104.166,6667 | Đạt |
| Thẻ Tổng quan: năm cột loại tiền, số không bẻ giữa chữ số, thẻ hẹp thì cuộn ngang, trang không tràn | Đạt 1440 và 390 (lần đầu bẻ số như TL-60 — đổi sang bảng nhỏ cuộn ngang) |
| Ô CPQC: gõ 13250000 → 13.250.000; gõ 8000.50 → giữ 8000.50 khi gõ, rời ô 8.000,5; gõ 13.250.000 kiểu Việt Nam giữ đúng; 1234,5 rồi gõ thêm 0 → 1.234,50; Số Mess 12345 → 12.345, 12,5 → 125 | Đạt (lần đầu 8000.50 thành 800.050 — sửa trước khi đóng) |
| Nhãn cột Lần nộp và STT trên hàng tiêu đề nền xanh đọc được | Đạt sau sửa (chữ nhạt chỉ áp ở thân bảng) |

Thời gian máy chủ trả trang kỳ 30 ngày (5 lần, trung vị / lớn nhất): Cộng theo ngày 184 / 219 ms, Từng lần nộp
164 / 196 ms, Gộp 178 / 191 và 154 / 210 ms, Theo nhân viên 86 / 107 ms; xuất Excel 544 / 614 ms — dưới ngưỡng
p95 đọc 1 s.

## Chưa kiểm / để lại

- Chưa chạy trên VPS; chưa đo máy thật của chủ dự án.
- Ngưỡng tiền theo từng loại tiền chưa có: ngưỡng ₫ nay chỉ tô dòng VND (gần như chỉ báo cáo cũ) — chờ chủ dự án.
- Khối toàn kỳ vẫn đứng đầu ở chế độ Từng lần nộp (mockup không vẽ; Bảng dữ liệu đang có) — chờ chủ dự án xác
  nhận giữ hay bỏ.
- Màn dưới 480 px: sáu cột ghim ở Từng lần nộp chiếm gần hết bề ngang.
