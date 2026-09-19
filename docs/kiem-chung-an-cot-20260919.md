# Kiểm chứng ẩn cột với cả công ty (ADR-039) — 19.09.2026

Nền `ea8942c`, nhánh `codex/crm-update-solar-ui`, máy ảo Claude Code trên web
(PostgreSQL 16 local, Chromium headless qua Playwright). Quyết định:
[ADR-039](quyet-dinh/039-an-cot-voi-ca-cong-ty.md). Chưa phát hành VPS.

## Phạm vi

Chủ dự án muốn tắt nhóm cột số lượng theo sản phẩm (`sl_*`) trên bảng Vận đơn mới.
Cách đã chốt: quản lý bảng ẩn cột cho **cả công ty** ngay trong hộp "Cột" sẵn có, áp
dụng cho lưới KN CRM, tệp Excel xuất ra và Bảng dữ liệu bên KN ERP. Không xoá cột,
không xoá dữ liệu.

## Rà trước khi sửa

Đã đo trên DB dev: 10 sản phẩm đang bán ↔ đúng 10 cột `sl_*`, không thừa không thiếu.
Thêm sản phẩm qua giao diện thì cột hiện ngay; tạo thẳng bằng lệnh thì phải đợi
`tao_bang_van_don` (chạy mỗi lần bật hệ thống); sản phẩm ngừng bán vẫn giữ cột. Nút
"Cột" cũ chỉ ghi `localStorage`, không dùng để tắt cho cả công ty được — đó là lý do
phải sửa mã thay vì hướng dẫn người dùng tự ẩn.

## pytest

Chạy từ `app/`, `--ds=knjsc.settings.test`, không chạy hai pytest cùng lúc.

| Lượt | Kết quả |
|---|---|
| `crm/tests/test_an_cot.py` (AC-39.1 → 39.7) | 7 đạt |
| `crm/tests orders/tests forms_builder/tests reports/tests core/tests tests -m "not trinh_duyet and not cham"` | 2.416 đạt, 1 bỏ qua, 0 đỏ, mã thoát 0 |
| `tests/test_truy_vet.py` sau khi thêm mục 39 vào docs/04 | Đạt; docs/06 lên 232 AC, 219 tự động, 195 đã có bài |
| `manage.py makemigrations --check --dry-run` | Không có thay đổi |
| `python scripts/dong-bo-skill.py --check`, `node --check master-grid.js` | PASS |

Một bài đỏ giữa chừng: `test_truy_vet` báo AC-39.x là mã bịa vì `docs/04` chưa có mục
39 — thêm mục rồi hết. Bài migration lúc đầu vướng `cannot ALTER TABLE ... pending
trigger events` do trigger `crm_capture_*` treo trên bảng cột; xả bằng
`SET CONSTRAINTS ALL IMMEDIATE` trước khi chạy migration.

## DB dev

| Việc | Kết quả |
|---|---|
| `migrate` | `forms_builder.0015_columndef_is_hidden... OK` |
| Migration xuôi rồi ngược trên DB kiểm thử | Cột `is_hidden` mất rồi có lại, `ColumnDef` giữ nguyên (AC-39.7) |
| `manage.py check` | Không có vấn đề |

## Chromium (headless, 1440×900, `scratchpad/kiem_39.py`)

| Điểm kiểm | Kết quả |
|---|---|
| Admin mở hộp "Cột" | Có nút gộp "Ẩn cột số lượng theo sản phẩm", có nút "Ẩn cho cả công ty" ở từng dòng |
| Bấm nút gộp | 11 cột sản phẩm biến khỏi lưới; hộp "Cột" hiện mục "Đang ẩn với cả công ty" kèm nút "Hiện lại" |
| Nhân viên Vận đơn (`vd.staff`) | Không thấy cột sản phẩm, không thấy nút ẩn, không thấy mục "đang ẩn" |
| Bảng dữ liệu bên ERP `/bang/van_don/` | Không còn cột sản phẩm |
| Manager Sale tạo sản phẩm "San Pham Test 19" ở Lên đơn | Tạo được; cột `sl_san_pham_test_19` sinh ra ở **trạng thái ẩn**, không tự hiện lại (12 dòng trong mục đang ẩn) |
| Admin bấm "Hiện lại" một cột | Còn 11 dòng ẩn, cột về đúng chỗ cũ trên lưới |

Sau khi kiểm đã dọn DB dev: xoá sản phẩm thử và cột của nó, bỏ ẩn mọi cột, bảng về
45 cột như trước.

## Chưa kiểm

- Xuất Excel từ trình duyệt: bảng dev có 100.522 dòng nên tải quá lâu, bỏ qua ở
  Chromium. Bài AC-39.1 đã kiểm tiêu đề tệp Excel không còn cột ẩn.
- Bài `trinh_duyet` trong pytest không chạy ở lượt này.
- VPS: chưa phát hành. Sau khi phát hành, **cột sản phẩm vẫn hiện cho tới khi Admin
  bấm nút ẩn một lần** — ẩn là trạng thái trong cơ sở dữ liệu, không phải mặc định
  của mã nguồn.
