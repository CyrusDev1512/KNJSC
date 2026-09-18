# 18.09.2026 (tối) — Báo cáo tổng hợp: cột Nhân sự chỉ mã, bảng không tràn ở Toàn màn hình

Chủ dự án so ảnh local (127.0.0.1:8020) với VPS, chọn bố cục local và yêu cầu hai điều: ô Nhân sự
chỉ hiện mã nhân sự (không họ tên) và bảng ở Toàn màn hình phải có thanh kéo ngang thay vì tràn.
Đã chốt phạm vi trong phiên: chỉ bảng + Excel; ô chọn và chip giữ `MÃ · Họ tên`; chưa có mã thì hiện
tên đăng nhập. Làm trên máy Windows, Compose local, đầu nhánh `d138be1`.

## Sửa gì

- `reports/services/activity_service.py`: `label_expression` → `code_expression` ở `person_expressions`
  (Nhân sự, Leader), `group_expression` (Theo nhân viên) và khoá `person` của `marketing_revenue`
  (phải đổi cùng, vì `attach_derived` nối doanh thu suy ra bằng chuỗi nhóm). Excel dùng cùng annotation.
  `people_choices` (ô chọn) và `filter_chips` không đổi.
- `static/css/solarpunk.css`: `--w-nhan-su` 190 → 130px, `--w-leader` 150 → 120px (≤900px: 110px;
  ≤480px: 100px); `.sp-report-focus .report-workspace` thêm `grid-template-rows:minmax(0,1fr)`.
  Nguyên nhân tràn: hàng grid ngầm `auto` cao bằng nội dung nên khung `.report-table-scroll`
  (`max-height:none` ở Toàn màn hình) cao bằng cả bảng, thanh kéo ngang nằm dưới đáy viewport và bị
  `.noi-dung{overflow:hidden}` cắt.
- Bài kiểm: `test_activity.py` AC-22.10 (so `employee_code`, khẳng định họ tên không có trong ô bảng
  và ô Excel, ô chọn vẫn có `identity_label`), `test_mkt_derived_revenue.py` (khoá Theo nhân viên),
  `test_bo_cuc_bao_cao_e2e.py` (Toàn màn hình ở viewport 1440×240: đáy khung cuộn và phân trang ≤
  `innerHeight`, khung cuộn dọc bên trong; ảnh `bao-cao-toan-man-hinh-thap`).
- Tài liệu: docs/04 AC-22.10, AC-22.13, mục 37; ADR-037 mục "Bổ sung 18.09 (tối)".

## Kiểm

Lệnh: `docker compose -f deploy/docker-compose.yml run --rm -e RUN_MIGRATIONS=0 web pytest reports/tests tests/test_truy_vet.py core/tests/test_giao_dien.py -q`

Kết quả: **751 đạt, 1 bỏ qua, 0 đỏ** trong 2 phút 11 giây. Bỏ qua là `test_bo_cuc_bao_cao_e2e.py`
(container `web` không có Chromium và thiếu thư viện hệ thống — `playwright install chromium` báo thiếu
libglib, libnss3, libX11…; không cài vào image). Lần chạy đầu có **1 đỏ**:
`test_duplicate_names_remain_separate_accounts` khẳng định họ tên có trong nhãn dòng; sửa thành "bốn mã
khác nhau, không có họ tên" — ý bài (trùng tên vẫn tách tài khoản) giữ nguyên.

**Trang thật 8020** (Django test client trong container `web`, tài khoản `quantri`, nguồn Báo cáo
Marketing 01–18.09): ô Nhân sự ba dòng đều `mkt.staff`; ô chọn Nhân sự `mkt.staff · Phạm Minh Anh`;
cách xem Theo nhân viên dòng `mkt.staff`, Leader `—`; Excel cột Nhân sự `mkt.staff`.

**Chromium thật trên host** — host không có thư viện Playwright nhưng có Chromium của Playwright, nên viết
`scripts/kiem-thu-bao-cao-chi-ma.mjs` (Node thuần, CDP qua `fetch` + `WebSocket` sẵn có, không thêm phụ
thuộc), chạy `node scripts/kiem-thu-bao-cao-chi-ma.mjs storage/e2e`; ảnh `storage/e2e/bao-cao-chi-ma-*.png`:

| Ngữ cảnh | Số đo |
|---|---|
| 1440×900 thường | ô Nhân sự `mkt.staff`, cột rộng 130px, dòng cao 35px, trang không tràn ngang |
| 1440×900 Toàn màn hình | khung bảng đáy 372px, phân trang đáy 437px (trong 900), bảng 1392px vừa khung |
| 1440×300 Toàn màn hình | khung co lại: đáy 235px, cuộn dọc bên trong, phân trang đáy 300px = đúng mép cửa sổ |
| 960×1000 Toàn màn hình (nửa màn như ảnh chủ dự án) | bảng 1194px trong khung 912px → **có thanh kéo ngang**, khung đáy 401px, phân trang 466px |
| Lỗi JS | 0 |

Lưu ý: khi cài Chromium thử, một lệnh `compose run` không có `RUN_MIGRATIONS=0` đã chạy entrypoint trên DB
dev (migrate: không có gì mới; `tao_bang_van_don`, `configure_*`: "existing rows unchanged") — không đổi dữ liệu.

## Chưa kiểm — ghi nợ

- Chưa phát hành VPS; đi cùng đợt phát hành ADR-036/037/038 (`collectstatic` là đủ, không migration).
- Extension Claude in Chrome không kết nối trong phiên nên chưa chụp bằng Chrome thật; dùng ảnh Chromium
  của bài e2e và đối chiếu tay trên 8020.
