# 18.09.2026 (chiều) — Phát hành lưới như Excel lên VPS: `knjsc-app:0d970f8-gopy` → `knjsc-app:5b7922f-excel`

Làm từ máy Windows có SSH (`deploy@103.57.221.52:24700`), theo khuôn 17.09 và 18.09 sáng. Mã `5b7922f`
(một commit: lưới như Excel, xoá Quốc gia thì Loại tiền trống, ADR-033/031 bổ sung). Không có migration.
Chủ dự án duyệt kế hoạch và hai điểm riêng: tạo tạm tài khoản Vận đơn `kiem.vd` rồi vô hiệu hoá; kiểm xoá
Quốc gia trên một dòng mới, không đụng 11 dòng thật.

## Trước — chỉ đọc

5 service trên `knjsc-app:0d970f8-gopy` (Up ~1 giờ), kho `/opt/knjsc` sạch ở `8c78471`; đĩa 50 GB trống,
RAM 2,6 GB khả dụng. Dòng đang hoạt động: `van_don` 11, `van_don_moi` 2, `van_don_db` 6.667, `bao_cao_mkt` 51,
`bao_cao_sale` 50, `bao_cao_van_don_ngay` 0; 22 tài khoản.

## Backup kiểm phục hồi

`/opt/knjsc-runtime/release-excel-20260918-122038/` (700): `commit.before`, `env.before` (0600), `images.before`,
`database.dump` 870.107 byte (sha256 `2122e38f…`), `database.list` 742 dòng. Restore thật vào
`knjsc_release_check` bằng `pg_restore --no-owner --no-privileges`: 6 bảng động và số tài khoản khớp DB thật,
xoá DB tạm sau khi so.

## Dãy lệnh (tại `/opt/knjsc-runtime`, `docker compose -f compose.yml -f compose.vps.yml`)

```
git merge --ff-only 5b7922f                                       # tại /opt/knjsc, 8c78471 → 5b7922f
docker build -f deploy/Dockerfile --build-arg INSTALL_DEV=0 -t knjsc-app:5b7922f-excel .   # ID 7c8772fc9254, 397 MB
config --quiet → OK; check --deploy crm và erp → 0 issues; migrate → No migrations to apply
tao_bang_van_don (van_don 36 cột, van_don_db 26); configure_erp_reports (3 bảng, dòng cũ giữ nguyên);
configure_delivery_daily_report; collectstatic → 1 tệp mới, 154 giữ
.env chỉ đổi KNJSC_IMAGE (diff với env.before); up -d --no-deps erp crm worker heavy beat   # 05:22:44 UTC
nginx -t → OK; nginx -s reload; curl /dang-nhap/ erp 200 (lần 2), crm 200 (lần 1)
```

`images.after`: 5 service cùng image mới, restart 0, không OOM. Log 40 phút sau phát hành: crm, worker, heavy,
beat 0 dòng lỗi; **erp 46 traceback đều là `DisallowedHost` do bot gọi thẳng IP `103.57.221.52`** lúc 12:29
giờ máy chủ, ngoài ra 0 — không phải lỗi mã.

Lưu ý kỹ thuật: `docker compose run` nuốt stdin của script SSH, phải thêm `-T` và `</dev/null`; cột Ngày
qua `record_service.create_record` nhận ISO `YYYY-MM-DD`, không nhận `DD/MM/YYYY`.

## Kiểm trên domain thật — Chromium (Playwright, kênh Chrome, 1440×900), tài khoản Vận đơn Staff `kiem.vd`

`kiem.vd` tạo bằng `account_service.create_account` (bộ phận Vận đơn, Staff, mật khẩu ngẫu nhiên trong tệp
0600 trên VPS, không ghi vào đâu). Vận đơn **không tạo được dòng trên lưới `van_don`** (profile vận đơn
`protect_table = True`, dòng chỉ sinh từ Lên đơn), nên dòng kiểm `KIEM-VD-1809` (id 6782, Canada → CAD, một
chi tiết `sda` ×1 giá 12) tạo bằng `record_service.create_record` với actor `kiem.vd`.

| Kiểm | Kết quả |
|---|---|
| Đăng nhập CRM, mở `/bang-tinh/van_don/` | 11 dòng khớp bộ lọc, có nút Tôi / Toàn bộ, 37 cột (cả Trùng), Quốc gia = Hoa Kỳ/Canada/Philippines, Loại tiền = VND/USD/CAD/PHP; **không** có "dòng trống để nhập" (đúng, xem trên) |
| Bấm ô Tên khách dòng 1 | chỉ chọn: `#mg-editor` ẩn, "1 ô được chọn" |
| Gõ `x` | ô nhập mở với đúng `x`; Esc → không lưu, trạng thái vẫn "Đã lưu" |
| Ctrl+A | `A1:AK11 · 407 ô được chọn` (với dòng kiểm: `A1:AK12 · 444 ô`); **không bấm Delete** |
| Dòng kiểm: chọn Thành phố → Quốc gia (`D12:F12 · 3 ô`), Delete | hộp xác nhận "Đổi hoặc xoá quốc gia sẽ đổi loại tiền của 1 dòng đã có tiền…" hiện **một lần**; chấp nhận → "Đã lưu" |
| DB sau đó | `quoc_gia` None, `bang`/`thanh_pho` None, `loai_tien` `''`, `gia_tien` giữ `12`; `GridCellHistory` ghi hai ô `quoc_gia` Canada → None và `loai_tien` CAD → '' lúc 05:29:17 UTC |
| Console | 0 lỗi JS ở cả hai lượt chạy |

Ảnh `storage/phat-hanh-excel/vps/01…04.png` (không đưa lên kho). Script ở scratchpad của phiên, không đưa
vào kho (Playwright cài riêng ngoài dự án, không thêm phụ thuộc).

## Dọn sau kiểm

Dòng 6782 **đánh dấu xoá** bằng `record_service.delete_record` (BR-4; `van_don` còn 11 dòng hoạt động);
`kiem.vd` khoá bằng `account_service.lock_account` (`is_active = False`, phiên huỷ); tệp mật khẩu tạm đã xoá.
Hai lượt này có nhật ký hoạt động với actor `kiem.vd`.

## Còn nợ

- Chưa kiểm vai Sale/CSKH trên domain thật; chưa lên đơn thật trên production.
- TL-41 (cột Đơn vị tiền của báo cáo Marketing/Sale chỉ có VND) chưa sửa — chờ chủ dự án chọn cách.
- Không kiểm ở 390 px, không đo hiệu năng đợt này.

## Quay lui

`cp release-excel-20260918-122038/env.before .env` (về `0d970f8-gopy`), `collectstatic`,
`up -d --no-deps erp crm worker heavy beat`, `nginx -t` + reload. Không migration, không đổi dữ liệu nghiệp vụ.
