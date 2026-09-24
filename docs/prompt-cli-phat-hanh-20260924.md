# Prompt dán vào Claude Code CLI (máy chủ dự án, có SSH tới VPS) — phát hành 24.09.2026

Toàn bộ phần dưới đây là **một prompt**, chép nguyên vào CLI. Mọi việc đã làm xong, đã kiểm
và đã gộp vào **`main`** (từ 24.09 `main` là nhánh chuẩn — xem CLAUDE.md mục "Nhánh và nơi
mã đang chạy"); **chỉ còn phát hành**. VPS đang chạy `knjsc-app:72af235-gop` (19.09). Lần
này gộp **13 PR** (#31→#43, #47): ADR-040 (CRM một bảng, bỏ Quý/Tháng), ADR-041 (bỏ & khôi
phục báo cáo cấp dưới + ma trận phân quyền), ADR-042 (Báo cáo tổng hợp như ảnh mẫu + Bảng
dữ liệu dạng báo cáo), Ngày lên đầu bảng vận đơn, khoá trùng SĐT 9 số cuối, lọc cột ẩn có
nhắc, ghi chú tự giãn dòng, cột sản phẩm mặc định ẩn, cắt 3 truy vấn thừa (K24), xoá dữ
liệu giả theo lô, script gom p95, gọn form tạo tài khoản (AC-1.8).

---

Đọc `CLAUDE.md` và `AGENTS.md` trước. Nhánh phát hành là **`main`**; `git fetch` rồi
`git checkout main && git pull`, HEAD phải từ `1729fde` trở lên ("Merge pull request #47").
Máy này có SSH tới VPS; Claude Code trên web không tới được. Làm theo AGENTS.md: trình kế
hoạch ngắn (mục tiêu, phạm vi, cách làm, cách kiểm) để tôi gật rồi tự làm trọn; chỉ commit,
push khi tôi bảo; không dán mật khẩu, khoá, IP vào chat. Thông tin SSH và đường dẫn kho
trên VPS: `<tôi điền>`.

## Đọc trước, không kiểm lại những gì biên bản đã ghi

- `docs/backlog.md` các mục 24.09 ở đầu tệp (13 việc của lần phát hành này, mỗi việc có
  biên bản riêng `docs/kiem-chung-*-2026092?.md`).
- Lỗi E2E ghi chú từng chặn phát hành **đã sửa** ở PR #43 (mục "Hai lỗi E2E ghi chú chặn
  phát hành `main`" trong backlog) — không còn blocker.
- Khuôn phát hành các lần trước: `deploy/production/README.md` (bảng 6 lần phát hành +
  dãy lệnh), `docs/kiem-chung-phat-hanh-vps-20260919-gop.md`.
- ADR mới: `docs/quyet-dinh/040-crm-chi-mot-bang-van-don.md`, `041-xoa-khoi-phuc-bao-cao.md`,
  `042-bao-cao-tong-hop-nhu-anh-mau.md` (ADR-042 là bản đánh số lại của "ADR-040 báo cáo"
  để khỏi trùng — đừng thắc mắc hai tệp 040).

## Việc 1 — Kiểm trên máy này trước khi động vào VPS

1. `pytest -m "not trinh_duyet and not cham"` từ `app/` — kỳ vọng **2.679 đạt, 1 bỏ qua,
   0 đỏ** (số đo máy ảo web tại `1729fde`, ~300 s). Chạy thêm bộ đầy đủ gồm `trinh_duyet`
   nếu máy có Chromium; bài nào đỏ do môi trường thì ghi biên bản, **không sửa test cho qua**.
2. `python manage.py makemigrations --check --dry-run` phải "No changes detected".
3. `docker compose -f deploy/production/compose.yml config --quiet` (chạy trên VPS ở Việc 2,
   trên máy này chỉ cần đọc để biết dãy lệnh).

## Việc 2 — Phát hành VPS

Theo đúng dãy lệnh `deploy/production/README.md`, các điểm riêng của lần này:

1. **Build image từ `main`**: `deploy/Dockerfile` với `--build-arg INSTALL_DEV=0`, tag bất
   biến gợi ý `knjsc-app:<commit7>-gop24`; điền vào `KNJSC_IMAGE` trong `.env`.
2. **Backup trước, kiểm phục hồi** như mọi lần — lần này có migration đổi dữ liệu nên
   không bỏ bước này.
3. `docker compose config --quiet` → `up -d db broker cache` → `--profile maintenance run
   --rm static-owner` → `run --rm crm python manage.py check`.
4. `run --rm crm python manage.py migrate --noinput` — **ba migration mới**:
   - `forms_builder/0016` (cột `val_phone_key` + backfill một lệnh UPDATE): trên DB dev
     120 nghìn dòng mất ~112 s; DB VPS 1,25 GB có thể **vài phút, đừng ngắt giữa chừng**;
   - `reports/0005` (cột `thresholds`, AddField thường);
   - `orders/0011` (ẩn cột `sl_*` đang hiện — chỉ đổi cờ hiển thị, không đụng ô nào).
5. `run --rm crm python manage.py tao_bang_van_don` (nâng cấp tại chỗ) →
   `configure_erp_reports` → `configure_delivery_daily_report` (ADR-042 đổi nhãn/cột nguồn
   MKT nên **bắt buộc chạy lại**, chạy nhiều lần vô hại) → `collectstatic --noinput`.
6. `up -d crm erp worker heavy beat proxy` → `docker compose exec proxy nginx -t` rồi reload.
7. **Quay lui nếu hỏng**: đổi `KNJSC_IMAGE` về `72af235-gop`, `up -d`. Ba migration đều
   lành với mã cũ (0016 có `db_default` nên bản cũ vẫn ghi được; 0005 cột mới không ai đọc;
   0011 chỉ là cờ ẩn) — quay lui image **không cần** đảo migration, không restore DB chỉ để
   quay lui mã.

## Việc 3 — Kiểm sau phát hành trên domain thật (Chrome)

Mỗi dòng một phút, theo đúng biên bản từng việc:

1. Lưới Vận đơn: cột **Ngày đứng đầu**, 5 cột ghim đứng yên khi cuộn ngang; ghi chú dài
   **tự giãn dòng**, kéo tay vẫn thắng; cột `sl_*` sản phẩm gõ thử **biến khỏi lưới**
   (bật lại được ở hộp Cột → "Đang ẩn với cả công ty").
2. Cột **Trùng**: hai đơn cùng khách SĐT gõ kiểu khác nhau đếm là một; `?trung=1` đúng.
3. Bookmark cũ lọc theo cột ẩn: **vẫn lọc, có chip vàng nhắc**; Bảng dữ liệu ERP có dòng nhắc.
4. KN CRM: trang chủ + thư mục **chỉ còn Vận đơn**, hết cấp Quý/Tháng; `/bang-tinh/bao_cao_mkt/`
   404 kể cả Admin; ERP `/bang/bao_cao_mkt/` vẫn 200 nguyên dữ liệu.
5. Báo cáo tổng hợp: số tiền **ra ₫** (hết ô "—" vì lẫn tiền), khối toàn kỳ + mỗi ngày một
   bảng, Gộp/Không gộp, ngưỡng màu (form Ngưỡng cho manager), lọc nhiều sản phẩm; Bảng dữ
   liệu của bảng có nguồn là báo cáo chi tiết theo ngày, `?dang=tho` về liệt kê thô.
6. Báo cáo ngày: manager bỏ báo cáo cấp dưới → mục **"Đã bỏ"** → Khôi phục; Kế toán có Sửa
   nhưng không có Bỏ.
7. Nhân sự: form **Tạo tài khoản không còn ô Email/Ngày sinh**; Sửa hồ sơ còn Ngày sinh.
8. **Lần đầu chạy bộ gom p95**: `python3 scripts/gom-p95-vps.py --since 7d --json` (chỉ đọc
   log, chạy giờ làm việc được) — lưu JSON và điền vào chỗ trống của
   `docs/kiem-chung-gom-p95-vps-20260922.md`. Kiểm `docker system df` trước; **gom xong mới**
   bàn chuyện đặt `logging:` xoay vòng.

## Việc 4 — Giấy tờ

- Biên bản `docs/kiem-chung-phat-hanh-vps-20260924.md`: image cũ → mới, giờ chạy migrate,
  kết quả từng mục Việc 3, phần chưa kiểm.
- `deploy/production/README.md`: thêm dòng **lần 7** vào bảng phát hành.
- `docs/backlog.md`: mục ngày mới "Phát hành VPS lần 7".
- Từ nay máy chủ dự án **đứng ở `main`** (đây chính là bước "Codex checkout main" mà
  CLAUDE.md nhắc); nhánh `codex/crm-update-solar-ui` không dùng để phát hành nữa.
