# Biên bản kiểm chứng — Gộp 16 PR đợt P0 vào `Staging` (14.10.2026)

| Mục | Nội dung |
|---|---|
| Yêu cầu | Chủ dự án 14.10, sau khi xem tình hình nhánh trên GitHub, chọn: "Gộp các PR P0 theo thứ tự" (kiểm kỹ trước, mỗi PR chờ CI xanh) và "Sửa CLAUDE.md nhánh nền" |
| PR đã gộp | 16 PR, theo thứ tự phụ thuộc ghi trong tiêu đề từng PR: #118, #117, #113, #115, #116, #119, #120, #121, #124, #126, #122, #125, #123, #127, #129, #130 |
| Trước gộp | `Staging` `b2b0198` (KN OMS #112, #114 và AC-10.12 #128) |
| Sau gộp | `Staging` `03e5d99`, cây `43aaaee`. Trùng đúng cây gộp thử đã kiểm ở mục 1 |
| Môi trường | Máy ảo Claude Code trên web: Python 3.11.15 (CI 3.12), Django 5.2.17, PostgreSQL 16.13, Chromium của Playwright 1.56. Hệ thống thật: ERP `runserver` 8020, CRM 8021 trên DB `knjsc_ht` |
| Kết luận | **Đạt, đã gộp.** Chặng 2 (chủ dự án thử ở máy mình) chưa làm |

## 1. Kiểm trên cây gộp thử, trước khi gộp

Gộp thử ở máy, bằng `--no-ff`: `Staging` `b2b0198`, rồi lần lượt 16 PR theo đúng thứ tự trên.

| Kiểm | Kết quả |
|---|---|
| Gộp thử theo thứ tự | **Không PR nào xung đột** |
| Phạm vi | 135 tệp, +8.955 −393. Không migration, không thư viện mới. `settings/base.py` thêm `core.middleware.PageOwnerMiddleware` và `CSRF_FAILURE_VIEW` (ADR-053, #129). Launcher `KN JSC.bat`, `scripts/cap-nhat-local.bat` đổi (#115) |
| `check` với settings test, dev, bangtinh. `check --deploy --fail-level WARNING` cho ERP (`prod`) và CRM (`bangtinh` với `BANGTINH_GOC=prod`), dùng biến môi trường giả. `makemigrations --check`, `migrate --check` trên `knjsc_ht`. `git diff --check`, `node --check` các tệp JS đổi, `dong-bo-skill.py --check`. Rà diff tìm khoá hay token | 0 lỗi. "No changes detected". Đủ migration |
| 6 script kiểm JS chạy bằng Node mà P0 đổi: `kiem-thu-het-phien-unit`, `master-conflict-unit`, `master-het-phien-unit`, `master-queue-unit`, `master-working-copy`, `optimization-unit` | **PASS cả 6** |
| `pytest -m "not trinh_duyet" -rs` | **3.852 đạt, 7 bỏ qua, 0 đỏ** (16 phút 18 giây). Trước P0 là 3.207 bài |
| e2e lượt 1 như CI: `pytest tests/e2e -m trinh_duyet` | 70 đạt, 2 bỏ qua, 9 đỏ. 9 bài đỏ đúng là 9 bài font Google có sẵn của máy ảo ở `test_pha_luoi_ghi_chu.py`; `Staging` gốc cũng đỏ đúng 9 bài đó. Không có lỗi nào khác |
| e2e lượt 2 như CI: `pytest -m trinh_duyet --ignore=tests/e2e` | **30 đạt, 9 bỏ qua, 0 đỏ**. Có 8 bài trình duyệt hết phiên của ADR-053 trong `crm/tests/test_het_phien_e2e.py` |

## 2. Hệ thống thật, chạy trên cây gộp thử

Trước khi kiểm, chạy `du_lieu_mau`, `configure_erp_reports`, `configure_delivery_daily_report` trên `knjsc_ht`. Có thêm
4 vai mới: `giamdoc` (Giám đốc), `vd.leader`, `kt.staff`, `cskh.staff`.

| Kiểm | Kết quả |
|---|---|
| Kịch bản KN OMS 16 bước (`quantri`, `sale.staff`, KN ERP) | **16/16** |
| Dựng lại cuộc đua AC-10.12 (lời báo mất mạng không bị tra khách xoá) | Lời báo còn |
| Quyền `/oms/`, 18 tài khoản, ở cả KN CRM và KN ERP | `quantri`: 200. Mọi vai khác, kể cả `giamdoc`: 403. KN ERP: 404. `sale.moi` bị buộc đổi mật khẩu trước, đúng thiết kế |
| ADR-053 trên hệ thống thật: tab A của `sale.staff` đang điền Lên đơn; tab B cùng trình duyệt đăng nhập `sale.staff2`; tab A bấm Lưu | Máy chủ trả **409**; không ra đơn dưới tên người khác; tab A không chuyển trang, dữ liệu đã điền còn (4/4) |
| Quét liên kết không tham số, 8 vai (`quantri`, `giamdoc`, `sale.manager`, `sale.staff`, `vd.leader`, `vd.staff`, `cskh.staff`, `kt.staff`) | KN CRM 56 trang, KN ERP 368 trang: 0 lỗi 5xx, 0 lỗi JS. Nhật ký máy chủ chỉ có các lần 403 ở `/oms/` của ma trận quyền |

**Quan sát, không chặn gộp:** khi máy quét mở liền nhiều trang, `kt.staff` gặp "Navigation interrupted" ở
`/bao-cao/<số>/sua/`. Trên `Staging` chưa có P0 cũng bị y vậy, thậm chí nhiều hơn (12 lượt so với 3). Mở thẳng trang thì
mã 200, không tự chuyển trang, không lỗi JS.

## 3. Gộp

- Ngay trước khi gộp: `Staging` vẫn là `b2b0198`, và đầu nhánh của cả 16 PR vẫn đúng như lúc kiểm.
- 13 PR đầu gộp thẳng bằng merge commit. Sau #123, cây `Staging` `ec4ba15` trùng đúng cây gộp thử ở bước đó.
- **#127, #129, #130:** GitHub báo "Pull Request has merge conflicts", trong khi `git merge-tree` báo sạch.
  - Gốc: ba nhánh này đã tự gộp nhánh P0 khác hay `Staging` vào mình, nên có 2–3 điểm gốc chung với `Staging`
    (merge-base chéo). Cách ghép của GitHub coi đó là xung đột.
  - Cách xử lý, theo quy tắc: gộp `Staging` vào chính nhánh PR bằng merge commit, không rebase, không force.
  - Kiểm cây sau gộp: trùng đúng cây gộp thử ở bước tương ứng (#127 `13d5577`, #129 `1d0a9e2`, #130 `43aaaee`).
  - Đẩy lên, chờ CI của PR xanh cả hai việc, rồi mới gộp.
- Sau khi gộp hết: `Staging` `03e5d99` có cây `43aaaee`, đúng cây đã kiểm ở mục 1 và 2. Không còn PR nào mở.
- CI của lần đẩy cuối lên `Staging` chạy sau khi biên bản này viết xong; kết quả ghi ở mô tả PR tài liệu đi kèm.

## 4. Nhánh

- **17 nhánh đã nằm trọn trong `Staging`:** 16 nhánh P0 và `claude/sua-loi-mang-ac-10-12`. Máy ảo bị chặn xoá nhánh
  (403), nên chủ dự án xoá bằng một lệnh.
- **`claude/phat-hanh-vps-e979323`:** có 2 commit tài liệu về lần phát hành VPS e979323 (09.10), chưa vào `Staging`. Giữ
  lại, chờ chủ dự án quyết.

## 5. Chưa kiểm

- **Docker và `KN JSC.bat`:** máy ảo không dựng được image. Đợt này đổi launcher (#115), nên chặng 2 nên bật bằng chính
  `KN JSC.bat`.
- **Firefox, Safari:** máy ảo chỉ có Chromium.
- **Chặng 2:** chủ dự án thử ở máy mình, theo `docs/08-ke-hoach-kiem-thu/06-kiem-tay-chang-2.md`.
