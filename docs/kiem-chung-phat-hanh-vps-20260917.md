# 17.09.2026 — Phát hành ADR-033 lên VPS: `knjsc-app:0907cdd-grid` → `knjsc-app:9949062-adr033`

Làm từ máy Windows có SSH tới VPS (`deploy@103.57.221.52:24700`), theo bản bàn giao
trong `docs/daily-tasks.md` và `deploy/production/README.md`. Chủ dự án duyệt kế
hoạch trước, gật một lần trước khi động vào production, không hỏi từng bước.
Mã phát hành: `9949062` (ADR-033); kho trên VPS tới `406c544` (thêm hai commit
chỉ tài liệu). Thời điểm chuyển container: 23:26 giờ Việt Nam.

## Trước khi phát hành — chỉ đọc

| Mục | Giá trị đo được |
|---|---|
| Kho `/opt/knjsc` | HEAD `1df5a70`, cây sạch, là tổ tiên của `406c544` (cách 16 commit) |
| Image đang chạy | `knjsc-app:0907cdd-grid` trên crm, erp, worker, heavy, beat (Up 31 giờ) |
| Migration | `forms_builder` dừng ở 0012, `reports` ở 0002 |
| Cờ | 7 cờ `CRM_OPT_*` = 0 |
| DB | 31 MB (tài liệu trước ghi 1,25 GB — số đó không còn đúng) |
| Đĩa, RAM | 50 GB trống; 3,9 GB RAM, 2,6 GB khả dụng |

## Backup kiểm phục hồi

Thư mục `/opt/knjsc-runtime/release-adr033-20260917-232356/` (quyền 700):
`commit.before`, `env.before` (0600), `images.before`, `database.dump`
(860.607 byte, sha256 `33672fc8…d190670`), `database.list` (733 dòng danh mục).

**Restore thật** vào DB tạm `knjsc_restore_check` bằng `pg_restore --no-owner
--no-privileges`, không lỗi; đếm dòng theo bảng khớp DB thật rồi `DROP DATABASE`:

| Bảng | Dòng (DB tạm = DB thật) |
|---|---|
| `bao_cao_mkt` | 51 |
| `bao_cao_sale` | 50 |
| `van_don_db` | 6.667 |
| `van_don_moi` | 1 |
| `van_don` | 1 |

## Dãy lệnh đã chạy (tại `/opt/knjsc-runtime`, `docker compose -f compose.yml -f compose.vps.yml`)

```
git fetch origin codex/crm-update-solar-ui && git merge --ff-only 406c544   # tại /opt/knjsc
docker build -f deploy/Dockerfile --build-arg INSTALL_DEV=0 -t knjsc-app:9949062-adr033 .
KNJSC_IMAGE=knjsc-app:9949062-adr033 …
  config --quiet                                   → OK
  run --rm --no-deps crm manage.py check --deploy  → 0 issues
  run --rm --no-deps erp manage.py check --deploy  → 0 issues
  run --rm --no-deps crm manage.py migrate --noinput
      Applying forms_builder.0013_remove_tabledef_delivery_view_all... OK
      Applying reports.0003_report_revision... OK
  run --rm --no-deps crm manage.py tao_bang_van_don          → van_don 32 cột, van_don_db 26 cột
  run --rm --no-deps crm manage.py configure_erp_reports     → bao_cao_sale, bao_cao_mkt, van_don_moi
  run --rm --no-deps crm manage.py configure_delivery_daily_report
  run --rm --no-deps crm manage.py collectstatic --noinput   → 7 tệp mới, 148 giữ nguyên
sed -i 's#^KNJSC_IMAGE=.*#KNJSC_IMAGE=knjsc-app:9949062-adr033#' .env   # diff với env.before: chỉ dòng này
up -d --no-deps erp crm worker heavy beat
docker exec knjsc-production-proxy-1 nginx -t && nginx -s reload
```

Image `knjsc-app:9949062-adr033`, ID `3e0804907b9e`, 397 MB, build tại VPS.
Không bật cờ `CRM_OPT_*`, không đổi `receives_orders` (vẫn rỗng), không sửa dữ liệu.

## Sau phát hành

- `images.after`: 5 service cùng `knjsc-app:9949062-adr033`; giới hạn bộ nhớ
  không đổi (crm 640 MB, erp 512 MB, worker 384 MB, heavy 512 MB, beat 192 MB);
  restart count 0; không OOM; log 5 service không có traceback/error.
- `curl https://erp.thnsolution.io.vn/dang-nhap/` và `crm.…/dang-nhap/` = 200; trang gốc 302 về đăng nhập.
- **502 thoáng qua**: chủ dự án thấy 502 ở CRM ngay lúc phát hành. Log proxy có đúng
  2 dòng 502 trên một kết nối, rơi vào 8 giây container CRM đang được thay (gunicorn
  lên 16:26:02 UTC, proxy nạp lại 16:26:10). Sau đó mọi request 200/302. Không phải lỗi mã.
- Chromium headless (Playwright, 1440×900) trên domain thật, tài khoản admin trong
  `initial-admin.txt`, không lỗi JS, không gõ vào ô dữ liệu thật:
  - CRM `/bang-tinh/van_don_moi/`: 1 dòng; **không** có nút Tôi / Toàn bộ (đúng, admin
    không có cột phụ trách); không còn "Chế độ: Xem"; bấm ô Tên khách mở ô nhập ngay.
  - CRM `/bang-tinh/van_don_db/`: 6.667 dòng, vẽ đúng.
  - ERP `/bao-cao/tong-hop/`: bản mới, có nút "Toàn màn hình"; Báo cáo Marketing hiện
    "Đơn vị tiền: VND" và **có số** ở cột tiền. Đăng nhập CRM rồi sang ERP không hỏi lại.
  - Ảnh: `storage/adr033-verification/vps/` (không đưa lên kho).
- Hai điều dự báo từ diễn tập, số đếm thật:
  - `bao_cao_mkt`: 51 dòng, **0 dòng thiếu `loai_tien`** — dải vàng không xuất hiện, không cần điền gì.
  - `bao_cao_sale` đã có sẵn 50 dòng (không phải bảng rỗng mới); `bao_cao_van_don_ngay`
    xuất hiện **rỗng 0 dòng** như dự báo. Chỉ báo, không xoá.
- Quan sát thêm, không do đợt này: ở Vận đơn DB với tài khoản admin, ba cột ghim
  (Số điện thoại, Mã đơn, Tên khách) đứng ở đầu và để lại một ô trống ở vị trí gốc của
  cột G giữa Zipcode và Sản phẩm. Mã ghim cột không đổi giữa `0907cdd` và `9949062`
  (`git diff` không có dòng pin/sticky); local với quantri không ghim thì không có ô trống.

## Kiểm trên máy local trước đó (cùng ngày)

`pull --ff-only` tới `406c544`; local đã áp 0013 từ lần dựng container trước
(`migrate` báo "No migrations to apply", `showmigrations` có `[X] 0013`, `[X] reports 0003`);
`tao_bang_van_don`, hai `configure_*`, restart worker/beat đạt. Chromium 8021:
`vd.staff` có nút Tôi / Toàn bộ, bấm Tôi → `?cua_toi=1`, 10.000 → 3.333 dòng, bấm ô
Tên khách gõ được ngay, Esc xong DB không đổi; `quantri` không có nút. Ảnh
`storage/adr033-verification/local/`.

## Chưa kiểm — ghi nợ

- Chưa kiểm trên VPS bằng tài khoản Vận đơn, Sale (hai người) và CSKH: chủ dự án chưa
  đặt tệp tài khoản kiểm (`/opt/knjsc-runtime/tai-khoan-kiem.txt`). Nên nút Tôi / Toàn bộ,
  lọc `cua_toi=1`, "Sale bấm ô của Sale khác không sửa được", "CSKH chỉ xem" **chỉ mới
  kiểm trên local**, chưa kiểm trên domain thật.
- Chưa kiểm ở 390 px trên domain thật; chưa đo hiệu năng sau phát hành.
- `van_don` cũ trên VPS có 32 cột (local 42) — bảng cũ giữ nguyên, không thuộc đợt này.

## Quay lui nếu cần

`cp release-adr033-20260917-232356/env.before .env` (về `knjsc-app:0907cdd-grid`),
`migrate forms_builder 0012` rồi `migrate reports 0002`, `collectstatic`,
`up -d --no-deps erp crm worker heavy beat`, `nginx -t` + reload. Không restore DB để lùi mã.
