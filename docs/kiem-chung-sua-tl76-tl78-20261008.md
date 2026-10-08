# Biên bản — Sửa TL-76, TL-77, TL-78 (08.10.2026)

| Mục | Nội dung |
|---|---|
| Yêu cầu | Chủ dự án 08.10: "sửa luôn TL-76 TL-77 TL-78" — ba lỗi tìm ra ở lượt kiểm `Staging` trước khi gộp `main` ([biên bản](kiem-chung-staging-len-main-20261008.md), PR #101) |
| Nhánh | `claude/sua-tl-76-77-78`, xếp trên `claude/kiem-staging-len-main` (#101), PR nháp về `Staging` |
| Tiêu chí | AC-36.15, AC-36.16 (TL-76) · AC-21.20 (TL-77) · AC-40.8 (TL-78) |
| Môi trường | Máy ảo: Python 3.11, Django 5.2.17, PostgreSQL 16, Redis, Chromium Playwright 1194 |

## 1. Đã sửa gì

| Lỗi | Gốc | Sửa |
|---|---|---|
| TL-76 — dữ liệu có mã đơn trùng thì cập nhật lên `0017` kẹt | `kiem_tra_du_lieu` nạp cả dòng `DataRecord` (có cột `val_order_code` chưa có) nên đổ trên DB cũ; lời báo của `0017` bảo sửa trên lưới, mà lưới 500 khi chưa có cột | `orders/services/integrity_service.py`: DB chưa có khoá thì chỉ rà mã trùng bằng SQL đọc `data`, cùng điều kiện với `0017`; `--sua` giữ dòng gắn đơn gốc (không có thì dòng tạo trước), đổi mã dòng thừa thành `TRUNG-<số dòng>-<mã cũ>`, ghi nhật ký từng dòng. `pre_migrate` (nối ở `orders/apps.py`) dừng `migrate` **trước khi áp migration nào**, nêu mã trùng và lệnh gỡ. `0017` giữ nguyên (quy tắc 5). `deploy/production/README.md` ghi bước gỡ cạnh `migrate` |
| TL-77 — Ctrl+Z sau khi xoá dòng duy nhất đang lọc, lưới không hiện lại | `master-grid.js` `loadViewport` trả về ngay khi `state.total === 0`; bảng vận đơn không có dòng nháp nên vùng xem rỗng không bao giờ đọc lại khối đầu sau `invalidate()` | Vùng xem rỗng thì `loadViewport` đọc lại khối đầu (khối đã đệm thì trả ngay, không lặp tải). Cùng một chỗ, chữa luôn lượt hỏi "có gì mới", `refresh()`, nút tải lại vùng xem khi vùng rỗng |
| TL-78 — nút "Cột" của `van_don` hiện cho `sale.manager`, bấm 403 | Danh sách `/bang/` hiện nút theo cấp bậc chung, trang Cột kiểm theo từng bảng | `forms_builder/views.py` `bang()` gắn `duoc_sua_cot = can_manage_columns(user, b)` cho từng bảng của trang; `bang.html` dùng cờ đó. Không thêm truy vấn. Nút "Tạo bảng" giữ quyền chung |

## 2. Bài kiểm mới — đỏ trên mã cũ, xanh sau sửa

| Bài | Trên mã cũ | Sau sửa |
|---|---|---|
| AC-36.15 `crm/tests/test_ma_don_khong_trung.py::test_kiem_tra_du_lieu_truoc_0017_liet_ke_va_doi_ma_trung` | `ProgrammingError: column … val_order_code does not exist` | Đạt |
| AC-36.16 `…::test_migrate_dung_truoc_khi_ap_khi_con_ma_trung` | `migrate` không dừng sớm, đổ giữa chừng ở `0017` | Đạt |
| AC-21.20 `tests/e2e/test_admin_xoa_dong.py::test_xoa_het_dong_dang_loc_roi_hoan_tac_hien_lai` | Quá 6 giây vẫn "0 dòng" | Đạt |
| AC-40.8 `forms_builder/tests/test_man_hinh_bang.py::test_danh_sach_bang_chi_hien_nut_cot_cho_bang_quan_ly_duoc` | `manager_mkt` (được cấp quyền xem) thấy nút "Cột" | Đạt |

## 3. Đi lại trên dữ liệu thật hoá

**TL-76** (DB `knjsc_tl76`: dựng bằng mã `main`, 10.000 dòng vận đơn, sửa dòng #7 cho trùng mã dòng #6, rồi chuyển sang
mã đã sửa):

| Bước | Kết quả |
|---|---|
| `kiem_tra_du_lieu` | "chưa chạy migration forms_builder 0017: chỉ rà mã đơn trùng" — `MAU-20260910-0001 (2 dòng)`, chỉ lệnh `--sua`; thoát mã 1 |
| `migrate` | `CommandError` nêu mã trùng, "Chưa áp migration nào", lệnh `--sua` kèm cách chạy ở máy local. Kiểm `django_migrations`: `core/0007` và `forms_builder/0017` đều **chưa** áp |
| `kiem_tra_du_lieu --sua` | Dòng #7 → `TRUNG-7-MAU-20260910-0001`, giữ dòng #6; nhật ký "Đổi mã đơn trùng … giữ dòng #6 (trước migration 0017)"; "Dữ liệu khớp." |
| `migrate` | Áp `core/0007`, `forms_builder/0017`; khoá của dòng #7 là mã mới |
| Lưới CRM `du-lieu/` | 200 |
| `kiem_tra_du_lieu --bang van_don` (chế độ thường) | Mã đơn trùng 0, "Dữ liệu khớp." |

**TL-78** (DB `knjsc_ht`, có dòng vận đơn gán cho Sale):

| Vai | Thấy `van_don` ở `/bang/` | Nút "Cột" | `/bang/van_don/cot/` |
|---|---|---|---|
| `sale.manager` | Có | **Không** (trước sửa: có) | 403 |
| `vd.manager` | Có | Có | 200 |
| `quantri` | Có | Có | 200 |
| `mkt.manager` | Không | Không | 404 |

**TL-77:** đi bằng trình duyệt thật ở bài AC-21.20 (lọc `?tim=` một dòng → xoá → Ctrl+Z → hiện lại trong 6 giây, trang
không tải lại).

## 4. Kiểm toàn phần

| Lượt | Kết quả |
|---|---|
| `pytest -m "not trinh_duyet"` | **3.127 đạt, 7 bỏ qua, 0 đỏ** (thêm 3 bài so với 3.124), 10 phút 51 giây |
| `tests/test_truy_vet.py` (docs/04 ↔ docstring, bộ đếm docs/06: 371 / 358 tự động / 335 có bài) | Đạt |
| E2E lượt 1 (`tests/e2e`) | 56 đạt, 2 bỏ qua có chủ ý, 9 đỏ — đúng 9 bài `test_pha_luoi_ghi_chu` lỗi phông Google của máy ảo (`ERR_CERT_AUTHORITY_INVALID`), như lượt 08.10 trước |
| 9 bài đó, vá phông tạm (không commit, đã gỡ) | 9/9 đạt |
| E2E lượt 2 (bài trình duyệt còn lại) | 19 đạt, 9 bỏ qua (giá đỡ script Node) |
| `tests/e2e/test_admin_xoa_dong.py` chạy 3 lần | 3/3 đạt cả 3 lần |

## 5. Ngoài phạm vi — chỉ báo, không sửa

Lúc dò TL-78, đọc mã thấy vài chỗ có thể sai quyền, **chưa chạy thử**:
- `bang_cap_quyen` / `bang_thu_quyen` chỉ kiểm cấp Manager và bảng nằm trong phạm vi thấy, không kiểm có quản lý bảng
  đó không: Manager bộ phận khác thấy được bảng có thể cấp hay thu quyền trên bảng đó.
- `bieu_mau_sua` cho Manager bộ phận khác sửa cấu trúc biểu mẫu mà họ được điền.
- Nút "Điền" của biểu mẫu ngừng dùng dẫn tới 403.
- Form "Cấp quyền" hiện cho Leader trên CRM nhưng gửi đi bị 403.

## Chưa kiểm

- Máy Windows: `KN JSC.bat` gặp `migrate` dừng thì in lỗi như cũ (giờ là lời chỉ đúng); chưa chạy thật trên Windows.
- VPS: chưa phát hành.
