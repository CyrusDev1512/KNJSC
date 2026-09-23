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

## Đợt 3 — Ngưỡng màu ba bậc, form Ngưỡng cho quản lý, lọc nhiều sản phẩm, "Tuần này"

### Đã đo

**pytest** (Postgres 16 cổng 5434 trong máy ảo, `knjsc.settings.test`), lệnh
`pytest reports/tests dashboard tests/test_truy_vet.py core/tests/test_giao_dien.py core/tests/test_chuyen_doi.py
core/tests/test_permissions.py core/tests/test_scope.py org/tests/test_account.py`: **843 đạt, 0 đỏ**. Bài mới
AC-40.8 → AC-40.11 (`reports/tests/test_nguong_va_loc_san_pham.py`, gồm migration `reports/0005` xuôi và
ngược), AC-40.12 trong `test_date_presets.py`, AC-10.2 `test_phien_dang_nhap_lay_ho_so_cung_mot_lenh`
(`org/tests/test_account.py`). Bộ đầy đủ `-m "not cham"` từ `app/`: **2.567 đạt, 9 bỏ qua (bài trình duyệt
thiếu Chromium trong pytest), 31 bỏ chọn (`cham`), 0 đỏ** trong 4 phút 49 giây. Hai sửa sau lượt đó (form
hiện mốc theo cách người Việt gõ, CSS ô nhập rộng hơn) chạy lại bộ `reports/tests core/tests/test_giao_dien.py
tests/test_truy_vet.py org/tests/test_account.py dashboard`: **808 đạt, 0 đỏ**.

**Truy vấn.** Danh sách tick Sản phẩm là một truy vấn thêm trên mỗi màn (DISTINCT tên sản phẩm trong phạm vi
quyền; nguồn Vận đơn: mã kèm tên từ chi tiết đơn). Nguồn Vận đơn với Leader lên **11** —
`test_delivery_query_budget` đỏ (11 lệnh: phiên, người dùng, hồ sơ, team phụ trách, quyền cấp, bảng nguồn, cột,
danh sách nhân sự, **sản phẩm**, trạng thái giao hàng, dòng). Cắt ở chỗ dùng chung thay vì nới ngân sách:
`CaseInsensitiveModelBackend.get_user` lấy người dùng **kèm hồ sơ** trong một lệnh (`select_related("profile")`),
vì mọi yêu cầu đã đăng nhập đều đọc `user.profile` (mốc phiên ở `SessionTimeoutMiddleware`, phạm vi ở
`core.scope`). Kết quả: Vận đơn/Leader 11 → **10**; nguồn MKT thật (AC-40.4) vẫn ≤ 10; mọi màn hình đã đăng
nhập bớt một truy vấn. Ba bài `django_assert_num_queries` đúng số (1, 0, 1) nằm ở tầng dịch vụ nên không đổi.
Bài AC-10.2 mới kiểm: người có hồ sơ → 1 lệnh và `user.profile` không tốn thêm; tài khoản không hồ sơ vẫn vào,
`profile` báo thiếu như trước; tài khoản bị khoá vẫn bị đẩy ra.

**Hai lỗi bắt được khi chụp, sửa ngay trong đợt.** (1) Lưu ngưỡng hụt hai lần liên tiếp thì `next` đã mang
`nguong=1` lại được nối thêm `&nguong=1` — view bỏ khoá cũ trước khi thêm lại (AC-40.9 thêm khẳng định).
(2) Form hiện lại mốc đã lưu bằng chuỗi máy (`7.32`, `0.345`) trong khi `parse_money` đọc `0.345` thành 345
(ba chữ số sau dấu chấm là ngăn nghìn) — người mở form rồi bấm Lưu không đổi gì sẽ lưu sai. Form nay hiện
theo cách người Việt gõ (`7,32`, `84.526.646`, `0,345`), đúng thứ `parse_money` đọc lại; AC-40.9 kiểm vòng
hiện → gửi lại y nguyên → mốc không đổi.

**Chromium** trên `knjsc_mkt`, `mkt.manager`, kỳ 01–23.09.2026 (script `scratchpad/chup-dot3.py`,
`chup-dot3b.py`, `chup-dot3c.py`):

| Ảnh | Thấy gì |
|---|---|
| `08-dot3-form-nguong-1440.png` | Nút "Ngưỡng màu" dưới phụ đề; `?nguong=1` mở form sáu chỉ tiêu (Tỉ lệ chốt, Tỉ lệ chốt (TT), Giá Mess, CPO, CPQC/DS Chốt, AOV) với chiều tốt và dấu ≥ / < hay ≤ / > |
| `09-dot3-ba-bac-mau-1440-sang.png`, `10-dot3-ba-bac-mau-1440-toi.png` | Sau Lưu: thông báo "Đã lưu ngưỡng màu.", trang về đúng URL cũ (không còn `nguong=1`) |
| `13-dot3-cot-chi-so-ba-mau-1440-sang.png`, `14-dot3-cot-chi-so-ba-mau-1440-toi.png` | Bộ lọc thu gọn, form mở lại hiện mốc đã lưu dạng `7,32`, `84.526.646` |
| `15-dot3-o-ba-mau-1440-sang.png`, `16-dot3-o-ba-mau-1440-toi.png` | Khung bảng cuộn tới cột chỉ số: ô xanh / vàng / đỏ theo mốc tuyệt đối, dòng TỔNG CỘNG cũng tô |
| `11-dot3-loc-nhieu-san-pham-1440.png` | Sản phẩm: hộp tick mở, tick 2/4 mục, tóm tắt "2 sản phẩm", chip "Sản phẩm Kem Chống Nắng, Máy massage cầm tay HM-200 ×", URL `sp=…&sp=…`, các bảng chỉ còn dòng khớp |
| `12-dot3-bo-loc-390.png` | 390 px: ngăn kéo bộ lọc, Chọn nhanh sáu mốc gồm "Tuần này" |

Số đếm từ DOM: mốc đặt quanh dòng TỔNG CỘNG toàn kỳ (Tốt = tổng ±10 %, Kém = tổng ∓10 % theo chiều; Tỉ lệ
chốt (TT) giữ mốc 0,38 / 0,31 đặt ở lượt chụp đầu — DB mẫu chưa có vận đơn đối soát nên cột này 0 % và đỏ
toàn bộ, đúng chiều; AOV để trống nên tô tương đối) → **trước** khi đặt: `o-tot` 14,
`o-canh-bao` 17, `o-xau` 0 (cách tương đối ±10 %, không có đỏ); **sau** khi đặt: `o-tot` 14, `o-canh-bao` 25,
`o-xau` 28, dòng TỔNG CỘNG mang lớp `o-canh-bao` / `o-xau`. Ô tìm nhanh gõ "x" ẩn 4/4 mục; "Không tick mục nào
(Tất cả)" trả về Tất cả; Chọn nhanh: Hôm nay · Hôm qua · 7 ngày · **Tuần này** · Tháng này · Tháng trước.

### Chưa kiểm

- Ngưỡng cho nguồn Sale (cùng mã chỉ tiêu, nhãn "Doanh số") chỉ qua bài kiểm, chưa chụp.
- Hộp tick Sản phẩm với hàng trăm sản phẩm (ô tìm nhanh) chưa đo bằng dữ liệu lớn.
- Excel khi lọc nhiều sản phẩm: phụ đề "Sản phẩm: …" chỉ qua bài kiểm, chưa mở bằng Excel thật.
- Hai script `.cjs` (`kiem-thu-erp-browser-perf`, `kiem-thu-erp-delivery-ui`) đã đổi sang hộp tick nhưng chỉ
  chạy tay khi có Docker — chưa chạy lại.

