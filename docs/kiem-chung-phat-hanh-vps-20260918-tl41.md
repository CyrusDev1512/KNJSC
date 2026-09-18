# 18.09.2026 (chiều, lần hai) — Phát hành TL-41 lên VPS: `knjsc-app:5b7922f-excel` → `knjsc-app:5b68dce-tl41`

Chủ dự án gặp lại "Giá trị CAD không có trong danh sách của cột Đơn vị tiền. Chọn: VND" trên domain thật và
chọn **sửa toàn bộ**. Hai bước, cùng máy Windows có SSH (`deploy@103.57.221.52:24700`), khuôn 17.09.

## Bước 1 — sửa tay ngay trên VPS (14:2x giờ máy chủ, trước khi phát hành)

Shell Django trong container `crm`: hai cột `loai_tien` của `bao_cao_mkt`, `bao_cao_sale` từ `["VND"]` thành
`["VND","USD","CAD","PHP"]` (nối thêm, giữ VND và nhãn "Đơn vị tiền"); 51 + 50 dòng cũ giữ `VND`, không đụng
dữ liệu dòng. Người dùng nộp lại được ngay sau bước này.

## Bước 2 — mã và phát hành

Phiên Claude Code trên web đẩy `5b68dce` (cùng cách: `configure_erp_reports` nối thêm mã tiền từ
`MARKET_CURRENCIES` vào cột có sẵn, bài `test_configure_currency_options.py` AC-22.12) song song với bản sửa
tại máy này; bản tại máy này (AC-22.13, cùng nội dung) **đã bỏ** để không trùng, phát hành `5b68dce`.

- Backup `/opt/knjsc-runtime/release-tl41-20260918-142704/`: `database.dump` 872.871 byte (sha256 `ec13a732…`),
  `database.list` 742 dòng, `env.before`, `images.before`; restore thật vào `knjsc_release_check`, 6 bảng động khớp,
  xoá DB tạm.
- `/opt/knjsc` `5b7922f` → `5b68dce` (ff), kho sạch; build `knjsc-app:5b68dce-tl41` (ID `25e0ea95ce78`, 397 MB).
- `config --quiet` OK; `check --deploy` crm/erp 0 issues; `migrate` không có gì; `tao_bang_van_don` (36/26 cột);
  `configure_erp_reports` 3 bảng (cột đã đủ bốn mã từ bước 1 nên không đổi thêm — chạy lại không đổi, đúng
  thiết kế); `configure_delivery_daily_report`; `collectstatic` 0 mới, 155 giữ.
- `.env` chỉ đổi `KNJSC_IMAGE`; `up -d --no-deps erp crm worker heavy beat` lúc 07:27:52 UTC; `nginx -t` OK, reload;
  `/dang-nhap/` erp 200 (lần 2), crm 200 (lần 1). 5 service cùng image, restart 0, không OOM, log 0 lỗi.
- DB sau phát hành: hai cột `loai_tien` = `["VND","USD","CAD","PHP"]`, dòng cũ 51/50 vẫn `VND`.

## Chưa kiểm

- Chưa nộp thử báo cáo Marketing/Sale trên domain thật (tránh tạo báo cáo giả trên dữ liệu thật); chủ dự án nộp
  lại báo cáo Canada để xác nhận.
- Bài `test_configure_currency_options.py` chưa chạy lại ở máy này (cây làm việc local đang có sửa đổi dở của phiên
  khác); bản tương đương tại máy này (`reports/tests` + `test_truy_vet` 175 bài, 0 đỏ) đã chạy trước khi bỏ.

## Quay lui

`cp release-tl41-20260918-142704/env.before .env` (về `5b7922f-excel`), `collectstatic`, `up -d --no-deps erp crm
worker heavy beat`, `nginx -t` + reload. Không migration; cột đã nối thêm mã tiền giữ nguyên (không hại).
