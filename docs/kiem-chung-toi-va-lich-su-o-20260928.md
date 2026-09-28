# Kiểm chứng — Nút "Tôi" theo tài khoản (TL-64) và lịch sử từng ô (AC-21.13) — 28.09.2026

Nhánh `claude/toi-va-lich-su-o` tách từ `main` (`a0313be`), máy ảo Claude Code, PostgreSQL 16, Chromium.
Chủ dự án yêu cầu "bộ lọc cá nhân theo tài khoản CRM" (làm rõ: chính là nút Tôi / Toàn bộ đang sai) và
"lịch sử chỉnh sửa trực tiếp trên bảng Vận đơn" (chọn kiểu: lịch sử từng ô).

## 1. Nút "Tôi" (TL-64)

**Nguyên nhân.** `grid_service.build_grid` lọc "Tôi" theo **cột phụ trách của bộ phận mình**
(`assignment_service.field_for`: Vận đơn → delivery, Sale/CSKH → care, Marketing → marketing), mà Lên
đơn không điền ai vào các cột đó. Đo trên dữ liệu thử (bài tạm, đã xoá):

| Tài khoản | Toàn bộ | Tôi (trước) |
|---|---|---|
| Sale tự lên 1 đơn | 1 | **0** |
| Nhân viên Vận đơn (chưa được giao) | 2 | **0** |
| Admin | 2 | không có nút |

**Sửa (chốt "Của tôi + giao tôi").** `assignment_service.mine_condition(user)`: dòng tôi tạo hoặc tôi là
Sale đứng đơn (`order__seller`), cộng dòng tôi được giao ở cột Vận đơn / CSKH / Marketing. Nút hiện
với mọi tài khoản trên bảng Vận đơn (`pham_vi_toi`, `config.myScope`). "Tôi" chỉ thu hẹp trong phạm vi
quyền: Marketing vẫn không xem bảng vận đơn. Excel và Thống kê đi theo cùng tham số `cua_toi`.

## 2. Lịch sử từng ô (AC-21.13)

- Chuột phải một ô (hay phím Menu khi đang đứng ở ô) → khung `#mg-cell-history` ngay cạnh ô: mã + tên
  người sửa, giờ Việt Nam, giá trị trước → sau (ngày hiện DD/MM/YYYY), "Cũ hơn" xem tiếp. Dùng lại API
  `lich-su/?record=&column=` đã kiểm quyền dòng. Esc, bấm ra ngoài, cuộn thì đóng.
- Ô bị **người khác** sửa giá trị trong 24 giờ (`core.constants.GRID_RECENT_EDIT_HOURS`) có dấu góc cam:
  `master_grid_service.recent_edits` thêm `recent` (mã cột) vào mỗi dòng của khối — **một truy vấn**
  cho cả khối theo chỉ mục (record, -id); chính mình sửa hay sửa định dạng thì không đánh dấu.
- Chân lưới thêm gợi ý "Chuột phải: lịch sử ô". Không migration, không đổi cách ghi lịch sử (chỉ ghi thêm).

## Kiểm (TDD: đỏ trước khi sửa, xanh sau)

| Bài | Trước sửa | Sau sửa |
|---|---|---|
| `crm/tests/test_pham_vi_toi_toan_bo.py::test_cua_toi_la_dong_cua_toi_hoac_giao_toi` (AC-33.3) | **đỏ**: Sale "Tôi" ra rỗng | xanh: Sale thấy đơn mình lên (+ đơn được giao CSKH); Vận đơn, CSKH theo phân công; Admin/Kế toán có nút, không dòng nào; Marketing vẫn không thấy bảng |
| `…::test_shell_renders_scope_toggle_by_role` (AC-33.6) | **đỏ**: Admin không có nút | xanh: mọi vai có nút, `myScope: true` |
| `crm/tests/test_pham_vi_toi_toan_bo.py` trọn tệp (gồm AC-33.4 Excel/Thống kê, trần 22 truy vấn) | — | 8 đạt |
| `crm/tests/test_lich_su_o.py` (AC-21.13) | **đỏ**: khối không có `recent` | xanh: người khác sửa → dấu 2 ô; chính mình → không; sửa 25 giờ trước → không; lịch sử theo ô đúng cột, có mã người sửa; người ngoài phạm vi 403 và không thấy dòng |
| `tests/e2e/test_lich_su_o_tren_luoi.py` (AC-21.13, Chromium) | **đỏ**: ô không có dấu góc | xanh: dấu góc đúng ô, chuột phải mở khung cạnh ô với "Khách 0 → Khách Đã Sửa" và mã người sửa, Esc đóng |
| `tests/test_truy_vet.py` + `core/tests/test_giao_dien.py` (docs/06 → 278 / 265 / 242) | — | 659 đạt |
| Suite đầy đủ `-m "not trinh_duyet and not cham"` | — | **2.802 đạt, 1 bỏ qua, 0 đỏ** (361 s) |

Ảnh: `docs/kiem-thu/toi-va-lich-su-o-2026-09-28/lich-su-o-tren-luoi.png`.

## Chưa kiểm

- Chuột phải không còn mở menu mặc định của trình duyệt trên ô lưới (chép/dán vẫn bằng Ctrl+C/V).
- Bảng lớn thật: truy vấn dấu góc chạy theo chỉ mục (record, -id) trên 100 dòng/khối; chưa đo trên
  300.000 dòng.
- Chưa phát hành VPS.
