# 18.09.2026 — Phát hành bốn góp ý sau ADR-033 lên VPS: `knjsc-app:9949062-adr033` → `knjsc-app:0d970f8-gopy`

Làm từ máy Windows có SSH (`deploy@103.57.221.52:24700`), theo khuôn 17.09. Mã `0d970f8`
(hai commit `a181943`, `0d970f8`). Không có migration. Chủ dự án yêu cầu "test kỹ trước khi cập nhật".

## Trước — chỉ đọc

5 service trên `knjsc-app:9949062-adr033`; kho `/opt/knjsc` sạch ở `406c544`; DB thật đã có
dữ liệu người dùng từ hôm qua: Vận đơn mới (`van_don`) 11 dòng, crmThuận 2, Vận đơn DB 6.667,
MKT 51, Sale 50, `bao_cao_van_don_ngay` 0.

## Backup kiểm phục hồi

`/opt/knjsc-runtime/release-gopy-20260918-103824/`: `commit.before`, `env.before` (0600),
`images.before`, `database.dump` 868.996 byte (sha256 `70142333…`), `database.list` 742 dòng.
Restore thật vào `knjsc_release_check` bằng `pg_restore --no-owner --no-privileges`, số dòng
từng bảng khớp DB thật.

## Diễn tập bước chuẩn bị `van_don` trên bản sao dữ liệu thật

Chạy image mới với `POSTGRES_DB=knjsc_release_check`: `check` sạch; `van_don` trước có **33 cột**,
lý do "Cột Loại tiền chưa có hoặc không đúng cấu trúc"; `chuan_bi_bang_nhan_don --table van_don
--actor <admin> --expected-rows 11` → **36 cột** (thêm `pttt_thuc_te`, `phu_trach_vd`,
`phu_trach_mkt`; `loai_tien` thành danh sách VND/USD/CAD/PHP, `pttt` thành Zelle/PayPal), 11 dòng
nguyên, đủ điều kiện, `configure()` chọn được (`current() == van_don`). Xoá DB tạm sau khi xong.

## Dãy lệnh phát hành (tại `/opt/knjsc-runtime`, hai tệp compose)

```
git merge --ff-only 0d970f8                                      # tại /opt/knjsc
docker build -f deploy/Dockerfile --build-arg INSTALL_DEV=0 -t knjsc-app:0d970f8-gopy .
config --quiet → OK; check --deploy crm/erp → 0 issues; migrate → No migrations to apply
tao_bang_van_don (van_don 33 cột, van_don_db 26); configure_erp_reports; configure_delivery_daily_report
collectstatic → 3 tệp mới, 152 giữ
.env chỉ đổi KNJSC_IMAGE (diff với env.before); up -d --no-deps erp crm worker heavy beat
nginx -t → OK; nginx -s reload; curl /dang-nhap/ hai domain → 200
```

Image `knjsc-app:0d970f8-gopy` ID `3795d8d76afa` 397 MB. `images.after`: 5 service cùng image,
giới hạn tài nguyên không đổi, restart 0, log 5 service 0 dòng lỗi.

## Kiểm Chrome domain thật (admin, 1440×900, không lỗi JS)

- Lưới Vận đơn DB 6.667 dòng: ba cột ghim (SĐT, Mã đơn, Tên khách) đứng đầu, sau đó Ngày, Chi
  tiết số nhà… — **hết ô trống và hết che cột** (ảnh `storage/gop-y-adr033/vps/luoi-van_don_db.png`).
- Lưới Vận đơn mới và crmThuận mở được.
- Báo cáo tổng hợp: header `Ngày · Nhân sự · Leader · Số Mess · CPQC`, 6 dòng (mỗi ngày một dòng).
- Trang Bảng nhận đơn hiện đủ ba bảng (ảnh `bang-nhan-don.png` chụp trước bước dữ liệu).

## Bước dữ liệu thật: Vận đơn mới thành bảng nhận đơn duy nhất

Chủ dự án xác nhận bảng cần chọn là **"Vận đơn mới"** (mã `van_don`, có cột Trùng rồi Ngày).
Chạy `chuan_bi_bang_nhan_don --table van_don --actor <admin> --expected-rows 11` rồi
`destination_service.configure()` trên production: 33 → **36 cột**, `workflow = waybill`, đủ điều
kiện, 11 dòng nguyên, `receives_orders` chỉ còn `van_don`. Chrome domain thật sau đó: trang Bảng nhận
đơn "Hiện tại: Vận đơn mới", ba lựa chọn đều chọn được, Vận đơn mới đang chọn; lưới Vận đơn mới 11
dòng, cột Trùng rồi Ngày, không lỗi JS (ảnh `bang-nhan-don-sau.png`, `luoi-van-don-moi-sau.png`).
Lệnh này lúc đầu bị bộ phân loại auto mode chặn ("Production Deploy"), chạy được sau khi chủ dự án
xác nhận lại bảng.

## Còn nợ

- Chưa lên đơn thử trên production (không tạo đơn giả trên dữ liệu thật); đơn thật tiếp theo sẽ ghi
  vào Vận đơn mới — người dùng Lên đơn kiểm giúp.
- Chưa kiểm bằng tài khoản Vận đơn/Sale/CSKH trên domain thật (chưa có tệp tài khoản kiểm).
- Ảnh không đưa lên kho.

## Quay lui

`cp release-gopy-20260918-103824/env.before .env` (về `9949062-adr033`), `collectstatic`, `up -d`,
`nginx -t` + reload. Không migration nên không có gì để lùi ở DB; nếu đã chạy bước chuẩn bị `van_don`
thì cột thêm giữ nguyên (không hại), đổi lại bảng nhận đơn trên trang cấu hình nếu cần.
