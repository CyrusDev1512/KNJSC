# Kiểm chứng — Form Nộp báo cáo ngày (ADR-041), 24.09.2026

Nhánh `claude/bao-cao-nhu-anh-mau` (cùng PR nháp #36 với ADR-040). Máy ảo Claude Code trên web: Postgres 16
cổng 5434, Redis 6379, `knjsc.settings.test` cho pytest; máy chủ dev 8020 với `knjsc.settings.dev` trên DB mẫu
`knjsc_mkt` (đã chạy lại `du_lieu_mau` rồi `configure_erp_reports`), Playwright Python + Chromium.

## Đã đo

**pytest.** Bộ `reports/tests forms_builder/tests core/tests/test_giao_dien.py tests/test_du_lieu_mau.py
tests/test_truy_vet.py tests/test_luong_ba_bo_phan.py org/tests`: 1.028 đạt + 3 đỏ lượt đầu (một khẳng định
của AC-41.2 viết cho ô chọn trong khi bảng của bài kiểm có Sản phẩm kiểu chữ; hai bộ đếm docs/06 cũ) →
sửa → `test_form_nhap_bao_cao.py` + `test_truy_vet.py` xanh. Bộ đầy đủ `-m "not cham"` từ `app/` sau mọi sửa:
**2.581 đạt, 9 bỏ qua (bài trình duyệt), 31 bỏ chọn (`cham`), 0 đỏ** trong 5 phút 7 giây.

Bài mới `reports/tests/test_form_nhap_bao_cao.py`: AC-41.1 (team hai chiều: Leader team được chọn thấy và sửa,
Leader team khác 403/404; team bộ phận khác, id lạ bị từ chối; để trống về hồ sơ; bộ phận không team → không ô),
AC-41.2 (MKT bốn trường, Sale ba trường qua `call_command("configure_erp_reports")`; trường đã có bị ép; thiếu
CPQC → "Chưa điền các trường bắt buộc: CPQC", không tạo dòng; "0" hợp lệ; `required` đúng ô), AC-41.3 (gỡ Hóa
đơn, chạy lại không tạo lại, cột/ánh xạ/chỉ tiêu giữ, `hoa_don` gửi thẳng bị bỏ), AC-41.4 (template, CSS,
chip). Bài cũ đổi: `test_new_marketing_report_derives_currency_and_keeps_zero` (dòng mới không có `hoa_don`),
`test_marketing_configure_adds_inputs_and_confirmed_formulas` (form không có Hóa đơn), `test_du_lieu_mau`
(ba team). `test_man_hinh_dien_va_bao_cao_ngay_it_truy_van` (≤ 12 truy vấn, thêm một lệnh lấy team) vẫn xanh.

**Chromium** (`scratchpad/chup-form.py`), ảnh ở `docs/kiem-thu/form-nhap-bao-cao-2026-09-24/`:

| Ảnh | Thấy gì |
|---|---|
| `01-mkt-1440-sang.png`, `02-mkt-1440-toi.png` | `mkt.staff`: một thẻ trải hết chiều rộng; hàng Biểu mẫu · Team (MKT 1) · Báo cáo cho ngày; lưới 9 ô trên hai hàng **6 + 3**, ô cao **34 px**; Marketer và Loại tiền chỉ đọc trong lưới; dòng chip "Hệ thống tự tính khi nộp: CPO = cpqc ÷ so_don …" (5 chip); không còn ô Hóa đơn |
| `03-mkt-390.png` | 390 px: hai cột (2·2·2·2·1), không tràn ngang |
| `01-sale-1440-sang.png`, `02-sale-1440-toi.png`, `03-sale-390.png` | `sale.staff`: Team có Sale 1 / Sale 2; 8 ô (6 + 2); ba trường số bắt buộc; không chip (bảng Sale không có cột tính) |
| `04-mkt-thieu-cpqc-1440.png` | Bấm Nộp khi thiếu CPQC: trình duyệt giữ nguyên trang, `checkValidity()` false, ô CPQC báo "Please fill out this field" |
| `05-mkt-lich-su-sau-nop-1440.png` | Nộp đủ với team MKT 1 → về Lịch sử báo cáo, dòng mang "MKT 1" |

Số đếm từ DOM: thuộc tính `required` đúng trên `so_mess, cpqc, so_don, doanh_so, san_pham, thi_truong` (MKT) và
`san_pham, so_mess, so_don, doanh_so, thi_truong` (Sale); `[name*=hoa_don]` = 0; tràn ngang = false ở cả ba
khung. Bảng dữ liệu `/bang/bao_cao_mkt/` ngày 24.09: ô Team của dòng vừa nộp = "MKT 1" (trước đây "Chưa có team").

**Impeccable (thủ công).** Đã đọc DESIGN.md, `design.json`, craft-floor, operate/polish; không chạy engine, hook
hay tạo `.impeccable`. Một lượt soát ảnh 1440 sáng: không thẻ lồng thẻ, nhãn 13 px/600, ô 34 px cùng bo góc 8 px
và halo focus như bộ điều khiển chung, số tabular; tối: chip dùng token `--accent-soft/--accent` nên vẫn đọc được.

## Chưa kiểm

- Form Vận đơn (ba ô chữ dài chiếm trọn hàng) chỉ qua đọc mã và CSS `:has(textarea)`, chưa chụp.
- Hai script `.cjs` (`kiem-thu-erp-ui`, `kiem-thu-erp-identity`) đã điền đủ bốn trường số từ trước nên không đổi,
  nhưng chỉ chạy tay khi có Docker — chưa chạy lại.
- Màn Sửa báo cáo (`bao_cao_sua`) cùng lưới `bm-ngang` chỉ qua bài AC-41.4 (tệp), chưa chụp.
- Trên máy chủ dự án: `configure_erp_reports` chạy ở `deploy/entrypoint.sh` mỗi lần bật, nên form thật tự mất
  Hóa đơn và có bắt buộc; `du_lieu_mau` không chạy lại trên máy đã có dữ liệu — tài khoản thật đã có team riêng.
