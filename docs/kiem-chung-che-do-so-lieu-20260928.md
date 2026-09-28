# Kiểm chứng — Chế độ số liệu: không quy đổi, mỗi dòng một loại tiền (ADR-046, TL-65) — 28.09.2026

Nhánh `claude/che-do-so-lieu-bao-cao` tách từ `main` (`85f7fc1`), đặt lại lên `309b447` (sau #59) trước khi đẩy,
rồi gộp `main` hai lần khi PR bị xung đột tài liệu (`e63e286` sau #63, `f783001` sau #64); máy ảo Claude Code, PostgreSQL 16 cục bộ,
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
| `tests/test_truy_vet.py` | Đạt — 293 tiêu chí, 280 tự động, 257 có bài (AC-46.1 → 46.10 đủ, AC-42.1/42.2 rút; tính cả tiêu chí của PR #59, AC-21.14 của #63 và AC-21.15 của #64 gộp trước) |
| `pytest -m "not trinh_duyet" --ignore=tests/perf` — bộ đầy đủ kể cả bài chậm (`cham`) | **2.835 đạt**, 7 bỏ qua (thiếu điều kiện ngoài, như trước), 54 bài trình duyệt để chạy riêng — 7 phút |
| Bài trình duyệt, lượt 1 như CI: `pytest tests/e2e -m trinh_duyet` (sau khi gộp `main` #63) | 33 đạt, 2 bỏ qua (bảng không có dòng trống; kiểm tải 300k cần biến riêng), **9 đỏ — không do PR này**: cả 9 ở `test_pha_luoi_ghi_chu.py` (lưới CRM, PR không đụng), mọi khẳng định giao diện đạt, chỉ trượt ở `assert not loi_js` vì lỗi console `ERR_CERT_AUTHORITY_INVALID` — phông Google bị proxy của máy ảo chặn (như biên bản cuộn báo cáo 28.09). Chạy chính tệp đó trên `main` `e63e286`: đỏ y hệt 9 bài, cùng lỗi. CI GitHub không qua proxy này (CI #88 của `main` xanh cả hai việc) |
| Bài trình duyệt, lượt 2 như CI: `pytest -m trinh_duyet --ignore=tests/e2e --deselect crm/tests/test_luoi_dong_trong_va_ghim_e2e.py` | **4 đạt** — ba bài `test_bo_cuc_bao_cao_e2e.py` (bộ lọc ba trạng thái, lăn chuột trên bảng, thẻ Tổng quan) và `test_o_nhap_so_e2e.py` (AC-46.10: gõ, xoá lùi, 8000.50 → 8.000,5, kiểu Việt Nam, phần lẻ, dán, số nguyên, nộp thật lưu 13250000 CAD); 9 bỏ qua (giá đỡ script Node cần Chrome host, như CI) |
| `pytest -m "not trinh_duyet" --ignore=tests/perf` sau khi gộp `main` #63 (commit `5874fb3`), bộ đầy đủ kể cả bài chậm | **2.845 đạt**, 7 bỏ qua (thiếu điều kiện ngoài, như trước), 60 bài trình duyệt chạy riêng ở hai dòng trên — 7 phút 48 |
| Sau khi bỏ hai import thừa: `org/tests/test_org_scope.py`, `reports/tests/test_che_do_so_lieu.py`, `test_activity.py`, `test_mkt_excel.py`, `test_nguong_va_loc_san_pham.py`, `core/tests/test_ra_soat.py` | 118 đạt |

Một lượt trình duyệt chạy chung một tiến trình bị bỏ, không tính: tôi lỡ chạy song song một pytest khác trên cùng database
kiểm thử (sai quy tắc "không chạy hai pytest cùng lúc"), database bị xoá giữa chừng nên 42 bài lỗi kết nối. Hai lượt
trên chạy lại tuần tự, không có gì chạy song song.

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
- Ngưỡng tiền theo từng loại tiền không làm — chủ dự án 28.09: chưa cần (ngưỡng ₫ nay chỉ tô dòng VND; tô
  tương đối và ngưỡng tỉ lệ vẫn chạy).
- Khối toàn kỳ đứng đầu ở chế độ Từng lần nộp (mockup không vẽ; Bảng dữ liệu đang có) — chủ dự án 28.09: giữ.
- Màn dưới 480 px: sáu cột ghim ở Từng lần nộp chiếm gần hết bề ngang.
