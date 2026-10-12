# Biên bản kiểm chứng — Kiểm `Staging` trước khi gộp `main` (12.10.2026)

| Mục | Nội dung |
|---|---|
| Yêu cầu | Chủ dự án 12.10: "test kĩ rồi gộp staging vào main đi" (chặng 3) |
| Phạm vi | `Staging` `cc26520` hơn `main` `e979323` đúng 2 PR, 34 tệp (+1.563 / −197): **#106** ẩn nút Tôi / Toàn bộ với Sale staff và CSKH, tóm tắt Lên đơn báo rõ từng lỗi (AC-33.6, AC-6.14, TL-86 → TL-88) · **#107** Admin sửa lần nộp ngay trên Báo cáo tổng hợp (ADR-050, AC-50.1 → 50.11) |
| Migration mới | Không có |
| Gộp thử | `main` không có nội dung riêng, chỉ có các commit gộp #87, #90, #104, #105. `git merge-tree --write-tree origin/main origin/Staging` ra đúng tree `4a11b71` của `Staging`, không xung đột |
| Môi trường | Máy ảo Claude Code trên web: Python 3.11.15 (CI 3.12), Django 5.2.17, PostgreSQL 16, Redis, Chromium Playwright 1194. Kiểm trên worktree đúng `cc26520`, mỗi loại kiểm một DB riêng |
| Kết luận | **Đạt để gộp `main`.** Có một lỗi nhẹ mới ghi lại, **TL-89**: liên kết chết ở Thống kê KN CRM. Lỗi có từ trước hai PR này, `main` cũng có, không chặn. **Chặng 2** (người thử ở máy mình): chủ dự án bảo gộp sau khi kiểm kỹ, nên lượt này đóng vai trên hệ thống thật ở máy ảo thay cho chặng 2 (mục 5). Chưa phát hành VPS |

## 1. Unit, functional, backend

| Kiểm | Lệnh (từ `app/`) | Kết quả |
|---|---|---|
| Toàn bộ trừ trình duyệt, gồm bài chậm, có Redis | `pytest -m "not trinh_duyet" -rs` | **3.161 đạt, 7 bỏ qua, 0 đỏ**, 7 phút 53 giây |
| 7 bài bỏ qua | `-rs` | Như mọi lượt: bài kiểm tải hay đo dung lượng, đòi DB thử riêng |
| Cấu hình Django | `manage.py check` với `test`, `dev`, `bangtinh` | Không có vấn đề |
| `makemigrations --check --dry-run` | | "No changes detected" |
| Cấu hình phát hành, một tên miền | `check --deploy --fail-level WARNING --settings=knjsc.settings.prod` (khoá và tên máy giả) | Không có vấn đề |
| Cấu hình phát hành, hai tên miền ERP và CRM | Như trên, `MAIN_APP_URL`, `BANGTINH_URL` khác tên miền | Thiếu `SESSION_COOKIE_DOMAIN`, `CSRF_COOKIE_DOMAIN` thì dừng ở `core.E001`, đúng như lượt 08.10. Đặt `.vidu.test`: không có vấn đề |
| CI trên `9dcac0f` (cùng tree `4a11b71` với `Staging`) | GitHub Actions | "pytest (bộ chính)" và "pytest e2e (Chromium)" đều xanh |

## 2. Migration và cập nhật như máy chủ dự án (`main` → `Staging`)

**Dựng DB `knjsc_nc12` bằng mã `main` (worktree `e979323`):**
- chạy `migrate`, `tao_bang_van_don`, `du_lieu_mau`, `configure_erp_reports`, `configure_delivery_daily_report`,
  `nap_du_lieu_van_don`, `nap_bao_cao_mau --nguoi 10 --lan 2`;
- kết quả: 10.000 dòng vận đơn, 845 dòng `bao_cao_mkt`, 840 báo cáo ngày.

**Sau đó đổi sang mã `Staging` và chạy đúng chuỗi lệnh của launcher:**

| Lệnh (mã `Staging`) | Kết quả |
|---|---|
| `migrate --noinput` | "No migrations to apply.", 0,8 s |
| `tao_bang_van_don`, `du_lieu_mau`, `configure_erp_reports`, `configure_delivery_daily_report` | Đều rc 0 |
| `kiem_tra_du_lieu` | "Dữ liệu khớp." |
| So mã băm `data` (kèm `deleted_at`) của mọi dòng theo bảng, khoá báo cáo ngày, cấu hình nguồn báo cáo, số migration — trước và sau | **Y nguyên**: `van_don` 10.000, `bao_cao_mkt` 845, báo cáo ngày 840, nguồn báo cáo 3, migration 78 |

## 3. Smoke trên hệ thống thật

ERP `runserver` 8020 (`knjsc.settings.dev`) và CRM 8021 (`knjsc.settings.bangtinh`) chạy mã `Staging`, trên DB `knjsc_nc12`
vừa cập nhật từ `main`.

| Kiểm | Kết quả |
|---|---|
| Quét liên kết: 12 tài khoản mẫu × ERP và CRM, đăng nhập, đi theo mọi liên kết cùng gốc, tối đa 60 trang mỗi dịch vụ mỗi người | **945 lượt mở trang** (162 đường dẫn ERP, 86 đường dẫn CRM). **0 trả lời 5xx.** 404 duy nhất: liên kết "xem bảng" ở Thống kê CRM nguồn Sale/MKT (**TL-89**), có ở 9 tài khoản thấy nguồn đó |
| `collectstatic --noinput --clear` | 159 tệp, 0,7 s |

## 4. E2E

| Kiểm | Kết quả |
|---|---|
| CI cả hai lượt e2e trên tree `4a11b71` | Xanh |
| #106 trên máy ảo: `tests/e2e/test_tom_tat_len_don_e2e.py`, `crm/tests/test_pham_vi_toi_toan_bo.py`, chạy 2 lần | **9/9 đạt cả 2 lần** |
| #107 trên máy ảo: `pytest reports -m cham`, gồm 3 bài trình duyệt của hộp sửa, chạy 2 lần | **20/20 đạt cả 2 lần** |

## 5. Đóng vai trên hệ thống thật, thay cho chặng 2

Mọi bước dưới **không có lỗi JS và không có trả lời 5xx**. Phông Google bị chặn có chủ ý.

| PR | Vai | Thao tác | Kết quả |
|---|---|---|---|
| #106 | `sale.staff` | Mở lưới `van_don` | Không có nút Tôi / Toàn bộ, URL không tự lọc |
| #106 | `vd.staff` | Mở lưới `van_don`, bấm Tôi | Vẫn có hai nút. Bấm Tôi thì URL thêm `cua_toi=1` |
| #106 | `sale.staff` | Lên đơn: chọn thị trường, sản phẩm, đơn giá | Tóm tắt "1 dòng…". Giả lập máy chủ trả 403, 500, mất mạng, hết phiên: mỗi trường hợp ra đúng một câu ("không lên đơn được", "Máy chủ đang lỗi", "Mất kết nối mạng", "Phiên đăng nhập đã hết") |
| #107 | `quantri` và các vai khác | Kịch bản 47 mục của lượt kiểm kỹ 10.10 (`kiem-chung-admin-sua-bao-cao-20261010.md`), chạy lại trên mã `Staging`, DB thử `knjsc_bc_perf` | **47/47 đạt** |
| Bố cục | `quantri`, `mkt.manager`, `sale.staff`, `vd.staff` | Các trang trong thanh điều hướng (4 → 7 trang mỗi dịch vụ) × 1366, 768, 390 px, cả ERP lẫn CRM | **24/24 đạt**: không tràn ngang, không 5xx, không lỗi JS |

Tổng các mục đóng vai #106 và bố cục: **33/33 đạt**.

## 6. Hiệu năng

- **#107** đã đo 10.10 trên DB 2.400 lần nộp, cùng tiến trình:
  - trang Admin có ✎ chậm thêm 5,9 ms (+4,8 %) tháng 9 và 3,4 ms (+1,4 %) cả kỳ, thêm đúng 1 truy vấn;
  - Manager và Bảng dữ liệu giữ đúng như trước.
- **#106** chỉ ẩn một nút theo vai, không đổi truy vấn: không đo lại.

## 7. Lỗi mới ghi lại

**TL-89 (mở) — mức nhẹ, Thống kê KN CRM:**
- **Lỗi:** với nguồn Sale/MKT, trang Thống kê có liên kết "xem bảng" mở `/bang-tinh/bao_cao_*/?f_ngay__lon_bang=…`. Từ
  ADR-040, KN CRM chỉ phục vụ bảng vận đơn, nên liên kết đó luôn 404.
- **Nguồn:** `crm/services/statistics_profiles.source_url`.
- **Có từ trước:** hai PR của lượt này không đụng tệp đó, `main` cũng có.
- **Cách sửa đề xuất:** với nguồn không phải vận đơn, trỏ sang Bảng dữ liệu của ERP (`/bang/<mã>/?tu=…&den=…`, báo cáo chi
  tiết theo ngày), hoặc ẩn liên kết.
- Chưa sửa trong lượt kiểm này.

## 8. Chưa kiểm

- Safari, Firefox và máy Windows thật: máy ảo chỉ có Chromium.
- Chặng 2 do người dùng thật ở máy local: thay bằng mục 5 theo lệnh của chủ dự án.
- Phát hành VPS (chặng 4): chưa làm. Cần chủ dự án bảo riêng, và do phiên có SSH làm theo `deploy/production/README.md`.
  Lượt này không có migration và không đổi cấu hình.
