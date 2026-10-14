# Biên bản kiểm chứng — Kiểm cây sau gộp, gộp KN OMS (#112, #114) vào `Staging` (14.10.2026)

| Mục | Nội dung |
|---|---|
| Yêu cầu | Chủ dự án 14.10: "kiểm thử kĩ tất cả rồi gộp PR 112 + 114 + oms vào staging". "oms" là chính hai PR KN OMS: #112 bản demo, #114 thiết kế lại (chứa trọn #112). Rà 15 PR đang mở (gồm #112, #114) và 25 nhánh: không có PR hay nhánh OMS thứ ba |
| Cây đem kiểm | Gộp thử ở máy, bằng `--no-ff`: `Staging` `ca56f10` + #112 `8832036` + #114 `69d467b`. Cây kết quả `8cfd3fa` trùng đúng cây của #114, nên kiểm #114 là kiểm đúng thứ sẽ nằm trên `Staging`. Commit chứa biên bản này chỉ đổi tệp trong `docs/` |
| Đổi so với `Staging` | 20 tệp, +3.719 −10, chưa tính commit biên bản này. Mã chung bị đụng: `crm/navigation.py` (mục KN OMS, chỉ Admin), `crm/urls.py` (`/oms/`), `templates/crm/base_crm.html` (title "Mở trong tab mới"), `core/tests/test_giao_dien.py`. Còn lại là tệp mới của KN OMS và tài liệu. Không model, không migration; không đổi Dockerfile, requirements, entrypoint, settings |
| Môi trường | Máy ảo Claude Code trên web: Python 3.11.15 (CI 3.12), Django 5.2.17, PostgreSQL 16.13, Chromium của Playwright 1.56. Hệ thống thật: ERP `runserver` 8020, CRM 8021, DB `knjsc_ht` |
| Kết luận | **Đạt, gộp.** Chặng 2 (chủ dự án thử trên `Staging` ở máy mình) chưa làm |

## 1. Cấu hình, migration, tệp tĩnh, diff

| Kiểm | Kết quả |
|---|---|
| `manage.py check` với settings test, dev, bangtinh | 0 lỗi |
| `check --deploy --fail-level WARNING` như bước phát hành: ERP `knjsc.settings.prod`, CRM `knjsc.settings.bangtinh` với `BANGTINH_GOC=prod`. Biến môi trường giả, tên miền `*.vi-du.test`, không ghi vào kho | 0 lỗi cả hai dịch vụ, trên cây gộp và trên `Staging` gốc. Lượt đầu thiếu `SESSION_COOKIE_DOMAIN` giả thì `core.E001` báo đúng như mong đợi, ở cả hai cây |
| `makemigrations --check --dry-run`; `migrate --check` trên `knjsc_ht` | "No changes detected"; đủ migration |
| `node --check static/js/oms.js`; `findstatic` cho 7 tệp `kn_oms.html` nạp | Đạt; 7/7 tìm thấy |
| `scripts/dong-bo-skill.py --check` | PASS |
| `git diff --check Staging..#114` | 1 chỗ: dòng trống thừa cuối `docs/quyet-dinh/051-kn-oms-ban-demo.md`. Đã sửa trong commit này |
| Rà các dòng thêm: IP ngoài 127.0.0.1, khoá riêng, token, `password =`, mật khẩu ngoài mật khẩu mẫu; tệp phụ thuộc, migration, deploy, settings | 0 |

## 2. Bài kiểm tự động

| Kiểm | Kết quả |
|---|---|
| Bộ chính như CI: `pytest -m "not trinh_duyet" -rs --durations=10` | **3.207 đạt, 7 bỏ qua, 0 đỏ** (110 bài trình duyệt tách riêng), 8 phút 52 giây. Bằng đúng số của #114 ngày 13.10. 7 bài bỏ qua là bài kiểm tải cần DB hay fixture riêng |
| e2e lượt 1 như CI: `pytest tests/e2e -m trinh_duyet -vv -rs -o faulthandler_timeout=120` | 68 đạt, 2 bỏ qua, 9 đỏ, 6 phút 48 giây. Cả 9 bài đỏ đều ở `test_pha_luoi_ghi_chu.py`, cùng một lỗi: console báo `net::ERR_CERT_AUTHORITY_INVALID` khi tải font Google qua proxy máy ảo, không có lỗi nào khác. `test_kn_oms_e2e.py` 11/11 đạt. Hai bài bỏ qua: bảng không có dòng trống, và bài 300.000 dòng cần cờ riêng |
| `tests/e2e/test_pha_luoi_ghi_chu.py` trên `Staging` gốc `ca56f10` (worktree riêng, DB riêng) | 9 đỏ, **đúng 9 bài đó**, cùng lỗi `ERR_CERT_AUTHORITY_INVALID`. Vậy 9 bài đỏ không do KN OMS. Trên CI có mạng thật, chúng đạt |
| e2e lượt 2 như CI: `pytest -m trinh_duyet --ignore=tests/e2e -vv -rs -o faulthandler_timeout=120` | **22 đạt, 9 bỏ qua, 0 đỏ**, 3 phút 16 giây. Chín bài bỏ qua là giá đỡ cho script Node chạy tay, đòi Chrome host hay server riêng, giống CI. Có 1 cảnh báo lúc dọn: DB thử chưa xoá được vì còn một kết nối, kết nối đóng ngay sau đó |
| Độ ổn định: `crm/tests/test_kn_oms.py` và `tests/e2e/test_kn_oms_e2e.py`, 3 lần | 3 lần liền, mỗi lần **15/15 và 11/11** (phần trình duyệt 43–45 giây) |

## 3. Hệ thống thật

| Kiểm | Kết quả |
|---|---|
| Kịch bản KN OMS 16 bước: `quantri` (khung, lọc, xuất CSV, chọn nhiều, ngăn kéo, chặn có lý do, kho, kênh, biểu đồ lãi, lỗi JS), `sale.staff`, KN ERP | **16/16 đạt** |
| Quyền `/oms/`: 14 tài khoản đang hoạt động, cả KN CRM và KN ERP | `quantri`: 200, POST 405, có mục trên thanh bên. 12 vai khác (Manager, Leader, Staff của Sale, MKT, Vận đơn; CSKH; Kế toán): 403, không có mục; nhật ký từ chối tăng đúng 12 dòng. `sale.moi` (buộc đổi mật khẩu lần đầu) về `/doi-mat-khau/` ở mọi trang, đúng thiết kế. Chưa đăng nhập: về `/dang-nhap/?next=/oms/`. KN ERP `/oms/`: 404 với mọi tài khoản |
| Quét liên kết không tham số (tối đa 70 trang mỗi vai): KN CRM và KN ERP × `quantri`, `sale.manager`, `sale.staff`, `vd.staff`. Cần vì thanh bên KN CRM là mã chung | KN CRM 35 trang (17 · 9 · 5 · 4), KN ERP 174 trang (70 · 49 · 28 · 27): 0 lỗi 5xx, 0 lỗi JS. Sáu lượt mở không phải trang: `mau-nhap.xlsx` là tệp tải về; năm lượt `/tai-lieu/N/tai/` chuyển sang Google Docs của tài liệu mẫu, máy ảo chặn mạng ngoài. Nhật ký máy chủ: 13 lần 403 ở `/oms/` (12 của ma trận quyền, 1 của kịch bản), không lỗi nào khác |
| Tràn ngang: 320 → 1440 px bước 16 × 6 màn | 0 px ở cả 426 lần đo |
| Tương phản chữ: 6 màn, ngăn kéo đơn, ngăn kéo biểu mẫu; sáng và tối | Tối: 0 chỗ dưới 4,5:1. Sáng: 6 chỗ 4,48:1 (nhãn nhóm thanh bên, "Bản demo", đường dẫn), y như 13.10. Đó là token chung `--ink-3` của KN CRM |

Ghi chú: `cskh.thu`, `kt.thu` là tài khoản thử vai tạo ngày 10.10 trên DB máy ảo, không phải tài khoản mẫu. Để đưa vào ma
trận quyền, hai tài khoản này được đặt lại mật khẩu mẫu, chỉ trên DB máy ảo.

## 4. Gộp

Sau khi CI của commit này xanh: bỏ nháp #112 và #114, gộp #112 rồi #114 vào `Staging` bằng merge commit. Kiểm sau gộp:

- cây `Staging` phải trùng đầu #114;
- CI của lần đẩy lên `Staging` phải xanh.

Kết quả hai bước này báo trong phiên.

## 5. PR đang mở khác

Dự báo bằng `git merge-tree`, lấy đầu #114 (gồm cả commit biên bản này) thay cho `Staging` sau gộp. Hai bên cùng gốc
chung `ca56f10`. Kết quả với 13 PR đang mở khác:

| PR | Gộp với `Staging` sau gộp |
|---|---|
| #113 Kế hoạch kiểm thử toàn diện (docs/08) | Xung đột ở `CLAUDE.md`, `docs/backlog.md` |
| #126 P0-10 khoá kho chứng từ | Xung đột ở `docs/06-ke-hoach-kiem-thu.md` |
| #115 → #125 (11 PR P0) | Gộp sạch |

Phiên của từng PR tự giải xung đột. Phiên này không sửa PR của phiên khác.

## 6. Chưa kiểm

- **Docker và `KN JSC.bat`:** máy ảo không dựng được image, vì lệnh apt trong lúc build không qua proxy (đã thử ngày 04.10).
  Hai PR không đổi Dockerfile, requirements, entrypoint, nên image không đổi.
- **Firefox, Safari:** máy ảo chỉ có Chromium.
- **Font thật:** font Google bị chặn ở máy ảo.
- **Chặng 2:** chủ dự án thử trên `Staging` ở máy mình, theo kịch bản 16 bước đã gửi ngày 13.10.
