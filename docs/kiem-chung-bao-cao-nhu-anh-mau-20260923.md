# Kiểm chứng — Báo cáo tổng hợp như ảnh mẫu (ADR-040), 23.09.2026

| Mục | Nội dung |
|---|---|
| Yêu cầu | Chủ dự án: Báo cáo tổng hợp giữ mọi chức năng, nâng cấp giống ảnh LUMI OMS; trước hết cột tiền phải **có số** dù lẫn loại tiền; thêm cột (TT) đối soát từ vận đơn |
| Nhánh | `claude/bao-cao-nhu-anh-mau` tách từ `codex/crm-update-solar-ui` `b43b20e` |
| Môi trường | Máy ảo Claude Code trên web: PostgreSQL 16 cổng 5434, Redis, Chromium (Playwright bản Python). DB kiểm `knjsc_db` (pytest tự dựng), DB xem tay `knjsc_mkt` (dữ liệu mẫu 19.09 + sửa tay loại tiền: 5 CAD, 1 USD, 1 EUR, 3 VND, 2 trống) |
| Không tới được | VPS và máy chủ dự án — không phát hành, không đo trên dữ liệu thật |

## Đợt 1 — Số liệu: quy ₫, cột (TT), Tỉ lệ chốt MKT, hai lỗi

### Đã đo

**pytest** (từ `app/`, `--ds=knjsc.settings.test`):

| Bộ | Kết quả |
|---|---|
| `reports/tests dashboard culture/tests tests/test_ti_gia.py tests/test_truy_vet.py` | **199 đạt, 0 đỏ** (1 bỏ qua có chủ ý: bài trình duyệt) |
| Bộ đầy đủ `-m "not cham and not trinh_duyet"` | **2.532 đạt, 1 bỏ qua, 0 đỏ** — 5 phút 03 giây |

Bài mới `reports/tests/test_quy_vnd_va_tt.py` — AC-40.1 → AC-40.5. Bài phải đổi theo hành vi mới:
`test_markets_currencies` (EUR + JPY giờ có tổng, KRW → cảnh báo), `test_mkt_derived_revenue`
(số × 17.500, nhãn "DS Chốt (TT)", USD lẫn CAD không còn trống), `test_report_amendments`
(đổi tên `test_summary_converts_currencies_to_vnd_before_adding`), `test_activity` (tỉ lệ ×100, nhãn
MKT, chuỗi "₫"). Truy vết `docs/04` mục 40 + bộ đếm `docs/06` 244 / 231 / 207 — `test_truy_vet` xanh.

**Ngân sách truy vấn** nguồn Marketing cấu hình thật, cách xem Tổng hợp: **12 → ≤ 10** (AC-40.4).
Ba lệnh bỏ đi: aggregate dòng Tổng và lệnh tra khoá đối soát (dòng nhóm đã vào bộ nhớ,
`summarize_in_memory`), lệnh tìm cột Tệp khách hàng (`segment_options` tra cột đã prefetch).
Bài `test_query_budget` (nguồn Sale) và `test_delivery_query_budget` vẫn ≤ 10.

**Chromium** trên `knjsc_mkt`, `mkt.manager`, kỳ 01–23.09.2026, ảnh ở
`docs/kiem-thu/bao-cao-nhu-anh-mau-2026-09-23/`:

| Ảnh | Thấy gì |
|---|---|
| `01-dot1-1440-sang.png` | Dải vàng "2 dòng chưa quy đổi được (loại tiền: trống)…" ngay trên bảng; mọi cột tiền có số ₫ ở dòng Tổng, Tổng ngày và từng người; 14 cột chỉ tiêu đúng thứ tự ADR-040 (… Số đơn (TT), DS Chốt, DS Chốt (TT), Tỉ lệ chốt, Tỉ lệ chốt (TT), Giá Mess, CPO, CPQC/DS Chốt, AOV, Hóa đơn, Hóa đơn/DS Chốt (TT)); Tỉ lệ chốt "6,65%"; chip Kỳ ở kỳ này **có** × (khác mặc định "Tháng này") |
| `02-dot1-1440-toi.png` | Cùng trang ở chế độ tối (`data-theme=dark`): dải cảnh báo và số vẫn đọc được |
| `03-dot1-390.png` | 390 px: cột Ngày · STT · Nhân sự · Leader vẫn ghim khi bảng cuộn ngang |

Kiểm bằng script (`scratchpad/chup-dot1.py`): **0 ô tràn chữ** (`scrollWidth > clientWidth`) trên
toàn bảng 1440. Số đơn (TT) = 0 và DS Chốt (TT) = "—" ở mọi dòng vì DB này chưa phân công Marketing
cho vận đơn nào — đúng quy tắc "không có đơn thì 0, không có tiền thì trống".

### Chưa kiểm

- Tệp Excel mở bằng Excel thật (chỉ đọc lại bằng openpyxl trong bài kiểm).
- Tổng quan (dashboard) chỉ qua bài kiểm, chưa chụp.
- Dữ liệu thật trên VPS; số ₫ với tỉ giá thật do kế toán chốt (`EXCHANGE_RATES_VND` trên `.env`).

## Đợt 2 — Bố cục khối như ảnh: toàn kỳ theo nhân sự, mỗi ngày một bảng, Gộp, Excel

### Đã đo

**pytest** `reports/tests dashboard tests/test_truy_vet.py`: **192 đạt, 0 đỏ**. Bài mới
`reports/tests/test_bo_cuc_khoi.py` — AC-40.6 (khối toàn kỳ + mỗi ngày một bảng, ngày tách trang ghi
"(tiếp)" và lặp TỔNG CỘNG đủ cả ngày, Excel hai sheet) và AC-40.7 (Gộp). Bài phải đổi theo bố cục:
AC-22.10/22.14/22.15 (vị trí hàng trong Excel, dòng `report-subtotal` cũ), AC-22.13 (cột định danh
Tổng hợp nay là STT · Team · Nhân sự · Leader), AC-38.2 và `test_sale_scope_and_dashboard` (tìm dòng
TỔNG CỘNG thay vì dòng cuối), xuất Vận đơn (sheet "Trạng thái giao hàng" tra theo tên). Bộ đếm
`docs/06` 246 / 233 / 209. Bộ đầy đủ: xem cuối mục.

**Truy vấn:** khối toàn kỳ cộng trong bộ nhớ (`aggregations.subtotals(key="person_name")`), cột Team
là thêm một cột GROUP BY — bài AC-40.4 (≤ 10) vẫn xanh; chỉ khi vượt `MAX_GROUPS` mới thêm một lượt
`build(group="person")`.

**Chromium** trên `knjsc_mkt`, `mkt.manager`, kỳ 01–23.09.2026:

| Ảnh | Thấy gì |
|---|---|
| `04-dot2-khoi-1440-sang.png` | Khối "Toàn kỳ 01/09 – 23/09/2026 · theo nhân sự · 2 nhân sự": STT · Team · Nhân sự · Leader, TỔNG CỘNG · toàn kỳ ngay dưới hàng tiêu đề cột, hai người ANHPM/NAMVH cộng cả kỳ; dưới là khối "18.09.2026" rồi từng ngày; nút "Không gộp" đang bật |
| `05-dot2-khoi-1440-toi.png` | Cùng trang chế độ tối |
| `06-dot2-gop-1440.png` | Gộp: chip "Gộp mỗi ngày một dòng ×", khối "Theo ngày · 5 ngày" mỗi ngày một dòng, khối toàn kỳ vẫn đứng đầu |
| `07-dot2-khoi-390.png` | 390 px: khối toàn kỳ, cột định danh ghim khi cuộn ngang |

Script `scratchpad/chup-dot2.py`: 6 khối ở trang thường (1 toàn kỳ + 5 ngày), 2 khối khi Gộp; **0 ô tràn
chữ**; cột định danh **trượt 0 px** khi cuộn ngang 300 px (ghim đúng) ở cả hai trang.

### Chưa kiểm

- Người đổi team giữa kỳ (sẽ thành hai dòng ở khối toàn kỳ) — chưa có dữ liệu để chụp.
- Trên 2.000 cặp ngày × người (đường chạm trần) chỉ qua đọc mã, chưa dựng dữ liệu.
- Excel mở bằng Excel thật; nút Gộp trên điện thoại chưa chụp riêng.
