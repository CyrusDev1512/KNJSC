# 19.09.2026 (18:39–18:47 giờ VN) — Phát hành gộp ADR-039, AC-22.14/15/16, TL-46/47, lọc cột, nhắc khách lên VPS: `knjsc-app:ea8942c-adr036` → `knjsc-app:72af235-gop`

Làm từ máy Windows có SSH (khuôn 17.09, cùng khoá và cổng như đêm 19.09), trong phiên Claude Code CLI theo yêu cầu
"kết nối với repo github và triển khai lên vps". Gộp 10 commit `1e09cfd..220fd22` của nhánh `codex/crm-update-solar-ui`
(ADR-039 ẩn cột với cả công ty; Báo cáo tổng hợp mỗi người một hàng, khối theo ngày, tô màu chỉ tiêu — AC-22.14/15/16;
TL-46 hộp lọc cột, TL-47 tên khách đơn thứ hai; hộp lọc cột theo số giá trị AC-11.42/43; chắn gõ nhầm số AC-6.10) cộng
biên bản phát hành đêm trước `a039387` rebase thành `72af235`.

## Đồng bộ GitHub trước khi phát hành

Máy này còn commit `a039387` (biên bản phát hành `ea8942c` đêm 19.09) **chưa push**, trong khi GitHub đã có 10 commit
mới tới `220fd22`, trong đó `3c61e86` "Đính chính trạng thái VPS" kết luận "không có biên bản phát hành" — vì biên bản
nằm ở máy này. Rebase `a039387` lên `220fd22`: xung đột ở `docs/backlog.md` và `docs/backlog-kanban.md` (cùng thêm mục
19.09 ở đầu), giải bằng giữ cả hai; push `72af235`. Cây làm việc sạch so với GitHub sau push.

**Không chạy pytest ở máy này** (Docker Desktop tắt, không có Postgres ngoài Docker). Số gần nhất ghi trong biên bản
trên nhánh: `pytest -m "not trinh_duyet and not cham"` **2.527 đạt, 1 bỏ qua, 0 đỏ** ở `220fd22`
(`kiem-chung-loc-cot-va-nhac-khach-20260919.md`). Commit `72af235` chỉ thêm tài liệu. Ghi nợ như đêm trước.

## Hiện trạng trước (chỉ ghi nhận)

| Mục | Giá trị |
|---|---|
| Image đang chạy | `knjsc-app:ea8942c-adr036` trên crm, erp, worker, heavy, beat (Up 18 giờ); db Up 18 giờ, broker/cache/proxy Up 4 ngày |
| Kho `/opt/knjsc` | `ea8942c`, cây sạch |
| Migration cao nhất | `forms_builder 0014`, `org 0005`, `orders 0010`, `reports 0004` |
| DB | 31 MB; `DataRecord` theo bảng: `van_don` 15 (14 sống), `bao_cao_mkt` 52, `bao_cao_sale` 50, `bao_cao_van_don_ngay` 0; 4 `TableDef`, `van_don` 34 cột |
| Tài khoản | 2 hoạt động; 21/21 hồ sơ có mã nhân sự |
| Máy | đĩa trống 50 GB, RAM available 2,6 GB |

## Backup — `/opt/knjsc-runtime/release-gop-20260919-183900/` (700)

`commit.before`, `env.before` (600), `images.before`, `database.dump` 340.104 byte (sha256 `fbebdca118636b7b…`, 600),
`database.list` 743 dòng. Phục hồi thật vào `knjsc_release_check` bằng `pg_restore --no-owner`: bốn bảng động
15 / 52 / 50 / 0 dòng và 51 bảng `public` khớp DB thật; đã xoá DB tạm. Không có DỪNG 1: đợt này không xoá cứng gì.

## Dãy lệnh (tại `/opt/knjsc-runtime`, `docker compose -f compose.yml -f compose.vps.yml`, `KNJSC_IMAGE` mới đặt qua biến môi trường cho các lệnh `run`)

```
git fetch origin codex/crm-update-solar-ui && git merge --ff-only 72af235        # /opt/knjsc, ea8942c → 72af235
docker build -f deploy/Dockerfile --build-arg INSTALL_DEV=0 -t knjsc-app:72af235-gop .   # ID 6b3e4de4bb15, 370 MB
config --quiet → up -d db broker cache → static-owner → check --deploy (0 issue)
migrate --noinput        # forms_builder.0015_columndef_is_hidden OK — đúng một migration mới
tao_bang_van_don         # van_don 37 cột, bộ phận Vận đơn (nâng cấp tại chỗ)
configure_erp_reports    # bao_cao_sale, bao_cao_mkt, van_don — existing rows unchanged
configure_delivery_daily_report
collectstatic --noinput  # 132 copied, 24 unmodified
gan_ma_nhan_su_cu        # xem trước: 0 hồ sơ chưa mã, 0 ô danh tính đổi → không có DỪNG 2, không chạy --xac-nhan
sed KNJSC_IMAGE=knjsc-app:72af235-gop .env    # diff với env.before: chỉ dòng này
up -d --no-deps erp crm worker heavy beat      # 11:44:05 UTC = 18:44 VN
nginx -t OK, nginx -s reload (11:44:32 UTC)
```

`xoa_bang_van_don_cu` **không chạy**: hai bảng cũ đã xoá cứng đêm 19.09 (biên bản `-adr036-mkt.md`), đúng đính chính
trong prompt.

## Sau phát hành

- 5 service cùng `knjsc-app:72af235-gop`, restart 0, log 3 phút 0 dòng error/traceback ở cả 5; RAM available 2,5 GB.
- `erp.thnsolution.io.vn` và `crm.thnsolution.io.vn` `/dang-nhap/` 200 (0,25 s từ ngoài); `/bao-cao/tong-hop/`,
  `/thu-muc/`, `/bang-tinh/van_don/` 302 về đăng nhập khi chưa đăng nhập.
- Tệp tĩnh trên domain thật đã là bản mới: `solarpunk.css` có `.report-subtotal`/`--w-stt` (7 khớp, AC-22.15);
  `crm-frame.css` có 25 luật `.loc-cot-*` (TL-46 — trước đó bị chú thích nuốt); `order-entry.js` có khối `nhac-khach`
  (AC-6.10).
- `forms_builder_columndef.is_hidden`: 0/72 cột đang ẩn — đúng kỳ vọng, ẩn là trạng thái trong DB, chờ Admin bấm (Việc 5).

## Chưa kiểm — ghi nợ (chủ dự án tự kiểm trên domain thật)

Không có tài khoản kiểm nên chưa mở trang có đăng nhập. Mục 7 của prompt (ADR-037/038, bố cục Báo cáo tổng hợp, ô
Nhân sự chỉ mã) từ đêm trước vẫn chờ; thêm đợt này:
- **Việc 5 (ADR-039):** Admin mở `/bang-tinh/van_don/` → nút **Cột** → "Ẩn cột số lượng theo sản phẩm với cả công ty";
  kiểm cột biến khỏi lưới, tệp Excel xuất và Bảng dữ liệu ERP; báo nhân viên đang đối chiếu bằng tệp xuất.
- Báo cáo tổng hợp `?nguon=bao_cao_mkt&nhom=day`: ngày nhiều người ra nhiều hàng, dòng Tổng ngày và cột STT, ô tỉ lệ tô
  màu theo chiều tốt so với dòng Tổng (AC-22.14/15/16).
- Lưới: hộp lọc cột có nền/khung/cuộn (TL-46); cột nhiều giá trị mở sẵn ô gõ chữ (AC-11.43); đổi cột không sót mục.
- Lên đơn: gõ số đã có trong danh bạ → tên tự điền khi ô trống, sửa tên thì hiện khối vàng nêu hai tên (AC-6.10);
  đơn thứ hai cùng số ghi tên vừa gõ (TL-47).
- `pytest` toàn bộ ở máy này chưa chạy (Docker Desktop tắt).

## Quay lui

`cp release-gop-20260919-183900/env.before .env`, `migrate forms_builder 0014` (0015 chỉ thêm một cờ, không mất dữ liệu),
`collectstatic`, `up -d --no-deps erp crm worker heavy beat`, `nginx -t` + reload. Image cũ `knjsc-app:ea8942c-adr036`
còn trên máy. `database.dump` chỉ dùng khi hỏng dữ liệu, không dùng để quay lui mã.
