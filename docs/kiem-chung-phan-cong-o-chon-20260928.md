# Kiểm chứng — Phân công ngay trong ô bằng ô chọn (AC-21.15) — 28.09.2026

Nhánh `claude/phan-cong-o-chon` tách từ `main` (`05f8f4f`), máy ảo Claude Code, PostgreSQL 16, Chromium.

## Yêu cầu

Chủ dự án: "phân công nhân viên bằng bảng chọn (giống trạng thái vận chuyển)". Trước đó bấm đúp ô
"Phụ trách …" mở hộp Phân công giữa màn hình.

## Sửa

- `waybill_service.grid_column`: cờ `assignment` của cột phụ trách là tên trường phân công
  (`delivery`/`care`/`marketing`, lấy từ `assignment_service.COLUMNS`) thay cho `True`.
- `crm/assignment_views.assignment` (GET): thêm `current_id` mỗi dòng để ô chọn chọn sẵn người đang giao.
- `master-grid.js`: bấm đúp/Enter/F2 ô phụ trách phát `master-assignment-cell` thay cho mở hộp.
- `waybill-feedback.js` + `_assignment.html`: ô chọn `#vd-assign-cell` đè đúng ô (chỉ có khi được phân
  công), khoá tới khi tải xong; chuột chọn là lưu, phím di chuyển không lưu, Enter lưu, Esc/bấm ra ngoài
  đóng; lưu bằng POST `van-don/phan-cong/` (CAS, nhật ký như cũ) rồi làm mới lưới; lỗi hiện ngay dưới ô.
- `master-grid.css`: kiểu ô chọn như ô nhập tại chỗ.

Không migration, không đổi quyền, nút "Phân công" nhiều dòng giữ nguyên.

## Kiểm

| Kiểm | Trước sửa | Sau sửa |
|---|---|---|
| `crm/tests/test_waybill_feedback.py::test_phan_cong_trong_o_doc_nguoi_dang_giao_theo_id` (AC-21.15) | **đỏ**: `KeyError: 'current_id'` | đạt; nhân viên Vận đơn thường vẫn 403 |
| `…::test_cot_phu_trach_mang_ten_truong_phan_cong` (AC-21.15) | **đỏ**: `True == 'delivery'` | đạt |
| `tests/e2e/test_phan_cong_o_chon.py` (AC-21.15, Chromium) | **đỏ**: không có ô chọn | 2 đạt: Leader bấm đúp → ô chọn đè đúng ô, có "Chưa gán" và mã nhân viên; Esc không đổi; chọn chuột → lưu, ô hiện mã; Enter mở, Home chưa lưu, Enter lưu "Chưa gán"; nhân viên thường không có ô chọn |
| `test_waybill_feedback`, `test_mot_bang_van_don`, `test_shared_grid`, `test_master_grid`, `test_truy_vet`, `test_giao_dien` (docs/06 → 280 / 267 / 244) | — | đạt |
| Suite đầy đủ `-m "not trinh_duyet and not cham"` | — | **2.806 đạt, 1 bỏ qua, 0 đỏ** (371 s) |
| `tests/e2e/test_phan_cong_o_chon.py` chạy lặp | — | ERROR chập chờn ở **teardown** (4/6 lần): lưới vừa lưu còn làm mới máy chủ khi pytest TRUNCATE dọn bảng → `DeadlockDetected`, rồi bài sau hỏng setup vì dữ liệu chưa dọn. Không phải khẳng định đỏ. Sửa bài kiểm: rời lưới (`about:blank`) và đợi 1 s trước khi dọn → **6/6 lần đạt** |

Ảnh: `docs/kiem-thu/phan-cong-o-chon-2026-09-28/phan-cong-o-chon.png`.

## Chưa kiểm

- Hai người cùng đổi một ô phụ trách: dựa vào CAS có sẵn của endpoint (đã có bài `test_two_assigners_do_not_silently_overwrite`), chưa thử bằng hai trình duyệt.
- Chưa phát hành VPS.

## Bổ sung 28.09.2026 — bỏ nút và hộp "Phân công" nhiều dòng

Chủ dự án mở "…" → Phân công khi chưa bôi đen dòng nào, thấy hộp báo "Chọn ít nhất một dòng…" và bảo bỏ
nút này. Nhánh `claude/bo-nut-phan-cong`: bỏ `#mg-assign`, hộp `#vd-assignment` (mẫu `_assignment.html` chỉ
còn ô chọn `#vd-assign-cell` kèm CSRF), phần JS hộp trong `waybill-feedback.js`, các chỗ `master-grid.js`
còn đóng hộp, kiểu `.vd-assignment-fields` trong `waybill.css`. Endpoint và quyền không đổi.

| Kiểm | Trước sửa | Sau sửa |
|---|---|---|
| `tests/e2e/test_phan_cong_o_chon.py::test_leader_chon_nguoi_ngay_trong_o_phu_trach` thêm khẳng định không còn `#mg-assign`/`#vd-assignment` | **đỏ** (dòng 54) | 2 đạt |
| `crm/tests/test_waybill_feedback.py::test_grid_ui_and_filtered_url` (ghim nút cũ) sửa thành: có `#vd-assign-cell`, không có `#mg-assign` | — | đạt |
| `test_waybill_feedback`, `test_master_grid`, `test_mot_bang_van_don`, `test_giao_dien`, `test_truy_vet` | — | đạt |
