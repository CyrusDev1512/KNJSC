# 19.09.2026 (00:15–00:25 giờ VN) — Phát hành ADR-036 + bảy PTTT + ADR-037/038 + bố cục Báo cáo tổng hợp lên VPS: `knjsc-app:5b68dce-tl41` → `knjsc-app:ea8942c-adr036`

Theo `docs/prompt-cli-phat-hanh-adr036-mkt-20260918.md`, làm từ máy Windows có SSH
(`deploy@103.57.221.52:24700`, khoá `knjsc_vps_ed25519`), khuôn 17.09. Chủ dự án gật hai điểm DỪNG trong
phiên Claude Code CLI. Gộp chín commit `d05293d..ea8942c`, trong đó Việc 4 (ô Nhân sự chỉ mã) là commit
`ea8942c` cùng đêm.

## Hiện trạng trước (chỉ ghi nhận)

| Mục | Giá trị |
|---|---|
| Image đang chạy | `knjsc-app:5b68dce-tl41` trên crm, erp, worker, heavy, beat (Up 10 giờ); db, broker, cache, proxy Up 3 ngày |
| Kho `/opt/knjsc` | `5b68dce`, cây sạch, nhánh codex |
| Migration cao nhất | `forms_builder 0013`, `org 0004`, `orders 0008`, `reports 0003` |
| DB | 31 MB; `van_don` 12 dòng (11 sống), `van_don_db` 6.667, `van_don_moi` 2 — khớp biên bản ADR-036 |
| Tài khoản | 2 hoạt động (`admin`, `quantri`, chưa có hồ sơ), 21 tài khoản mẫu đã khoá |
| Máy | đĩa trống 50 GB, RAM trống 2,5 GB |

Local trước khi động VPS: `makemigrations --check --dry-run` = "No changes detected"; `reports/tests` +
`test_truy_vet` + `test_giao_dien` 751 đạt (biên bản `kiem-chung-bao-cao-chi-ma-20260918.md`). **Chưa chạy**
`pytest -m "not cham"` toàn bộ ở máy này trong đêm (máy báo thiếu bộ nhớ khi chạy nền); bản đầy đủ gần nhất do
Codex đo trên `49068b7`/`3748ea9` (2.384 đạt) — ghi nợ.

## Backup — `/opt/knjsc-runtime/release-adr036-mkt-20260919-001551/` (700)

`commit.before`, `env.before` (600), `images.before`, `database.dump` 874.056 byte (sha256 `134855a057bf41cf…`),
`database.list` 742 dòng. Phục hồi thật vào `knjsc_release_check`: ba bảng 12 / 6.667 / 2 dòng và 51 bảng khớp
DB thật; đã xoá DB tạm và tệp dump tạm trong container. **DỪNG 1:** chủ dự án đồng ý xoá cứng.

## Dãy lệnh (tại `/opt/knjsc-runtime`, `docker compose -f compose.yml -f compose.vps.yml`, `KNJSC_IMAGE` mới đặt qua biến môi trường cho các lệnh `run`)

```
git fetch origin codex/crm-update-solar-ui && git merge --ff-only ea8942c           # /opt/knjsc, 5b68dce → ea8942c
docker build -f deploy/Dockerfile --build-arg INSTALL_DEV=0 -t knjsc-app:ea8942c-adr036 .   # ID bbe611ce6d22, 397 MB
config --quiet → up -d db broker cache → static-owner → check --deploy (crm, 0 issue)
migrate --noinput        # forms_builder 0014, orders 0009, orders 0010, org 0005, reports 0004 — đúng 5, đều OK
tao_bang_van_don         # van_don 36 cột, bộ phận Vận đơn (nâng cấp tại chỗ)
xoa_bang_van_don_cu --dong-y-xoa-cung --backup-da-lam
configure_erp_reports    # bao_cao_sale, bao_cao_mkt, van_don — existing rows unchanged
configure_delivery_daily_report
collectstatic --noinput  # 3 tệp mới, 153 giữ
gan_ma_nhan_su_cu        # xem trước: 21 hồ sơ chưa mã (toàn tài khoản mẫu + kiem.vd), 0 ô danh tính đổi
sed KNJSC_IMAGE=knjsc-app:ea8942c-adr036 .env   # diff với env.before: chỉ dòng này
up -d --no-deps erp crm worker heavy beat       # 17:19:28 UTC 18.09 = 00:19 19.09 VN
nginx -t OK, nginx -s reload
gan_ma_nhan_su_cu --xac-nhan                    # DỪNG 2 được gật: ghi 21 mã; chạy lại: 0 hồ sơ chưa mã, 0 dòng đổi
```

Điều chỉnh so với prompt: `up -d` image mới chạy **trước** DỪNG 2 (ngay sau `collectstatic`), vì migration
`forms_builder 0014` bỏ cột `receives_orders` mà mã cũ còn đọc — không để mã cũ chạy trên schema mới trong lúc
chờ. `gan_ma_nhan_su_cu` chỉ xem trước tới khi được gật.

Kết quả xoá cứng: `van_don_moi` — dòng 2, chi tiết 4, đơn bỏ liên kết 2, cột 25; `van_don_db` — dòng 6.667,
lịch sử ô 1, biên nhận 1, cột 26. Sau lệnh `forms_builder_tabledef` chỉ còn `van_don` "Vận đơn mới".

## Sau phát hành

- 5 service cùng `knjsc-app:ea8942c-adr036`, restart 0, OOM không, log 3 phút 0 dòng lỗi.
- `erp.thnsolution.io.vn` và `crm.thnsolution.io.vn` `/dang-nhap/` 200 (qua proxy nội bộ và từ ngoài);
  `/bao-cao/tong-hop/`, `/thu-muc/`, `/bang-tinh/van_don/` 302 về đăng nhập khi chưa đăng nhập.
- `static/css/solarpunk.css` trên domain thật đã là bản mới: có rule `grid-template-rows:minmax(0,1fr)`,
  `--w-nhan-su:130px`.
- `org_userprofile`: 21/21 hồ sơ có mã.

## Chưa kiểm — ghi nợ (chủ dự án tự kiểm trên domain thật, mục 7 của prompt)

Không có tài khoản kiểm nên chưa mở trang có đăng nhập. Cần chủ dự án xem: thư mục Vận đơn chỉ còn một bảng,
sidebar không còn Bảng nhận đơn, `/bang-tinh/van_don/` có cột Trùng và nút Tôi/Toàn bộ; Lên đơn có bảy PTTT và
thử một đơn Western Union; tạo tài khoản thử thấy mã gợi ý và đăng nhập bằng mã; Marketing nộp hai lần/ngày với
Tệp khách hàng; Kế toán sửa báo cáo; Báo cáo tổng hợp nguồn Marketing: ô Nhân sự/Leader **chỉ mã**, ô chọn
`MÃ · Họ tên`, Doanh thu suy ra, Toàn màn hình ở cửa sổ hẹp có thanh kéo ngang. Hai tài khoản thật `admin`,
`quantri` chưa có hồ sơ nên chưa có mã — tạo hồ sơ ở Nhân sự thì mã tự gán. Thông báo nhân viên (mục 8) do chủ
dự án làm.

## Quay lui

`cp release-adr036-mkt-20260919-001551/env.before .env`, `migrate reports 0003`, `migrate org 0004`,
`migrate orders 0008`, `migrate forms_builder 0013`, `collectstatic`, `up -d --no-deps erp crm worker heavy beat`,
`nginx -t` + reload. Hai bảng cũ đã xoá cứng chỉ lấy lại bằng `database.dump` (phục hồi cả DB, mất dữ liệu nhập
sau 00:15 19.09). `org/0005` quay lui mất 21 mã mẫu; `reports/0004` quay lui thất bại nếu đã có người nộp nhiều
lần/ngày.
