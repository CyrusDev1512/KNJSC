# Biên bản kiểm chứng: Admin sửa lần nộp ngay trên Báo cáo tổng hợp (ADR-050), 10.10.2026

## Phạm vi

- **Yêu cầu của chủ dự án:** "tôi muốn quản trị có chức năng khi vào báo cáo tổng hợp có thể sửa dữ liệu".
- **Mockup tương tác đã duyệt:** https://claude.ai/artifact/AiyWUW9ycAGuRsdniXRWnN.
- **Chủ dự án đã chốt:**
  - chỉ Admin thấy nút ✎;
  - sửa trong hộp đè lên bảng, lưu xong bảng đổi tại chỗ;
  - dòng Toàn kỳ, TỔNG CỘNG và nguồn Vận đơn giữ nguyên.
- **Nhánh:** `claude/knerp-erp-chinh-sua-hfi7w8`, tách từ `Staging` `348a7da`.

## Môi trường

- **Máy ảo:** Claude Code trên web.
- **Bài kiểm tự động:** pytest chạy ngoài Docker trên Postgres 16 (cổng 5434) và Redis; Python 3.11; Chromium của
  Playwright.
- **Thử tay:** KN ERP `runserver` ở 8020, dữ liệu mẫu:
  - `du_lieu_mau`;
  - `nap_bao_cao_mau --nguoi 6 --lan 2` (Marketing, ngày 01.09 → 10.10);
  - 20 lần nộp Sale (08 → 10.10).

## Đã kiểm

| Mục | Lệnh / cách làm | Kết quả |
|---|---|---|
| Bài kiểm mới chạy đỏ trước khi viết mã | `pytest reports/tests/test_admin_sua_tong_hop.py` | 5 bài kiểm chức năng đỏ, 4 bài kiểm "không có ✎" đạt sẵn; bài thứ 10 (câu báo 409 không đổ cho người sửa từ trước) đỏ với mã cũ |
| Bài kiểm mới (AC-50.1 → 50.8) | như trên, sau khi viết mã | **10/10 đạt** |
| Trình duyệt (AC-50.9, 50.10) | `pytest reports/tests/test_admin_sua_tong_hop_e2e.py` | **2/2 đạt**: sửa, lưu, bảng đổi tại chỗ, 409 trong trình duyệt, Escape, 390 px, 0 lỗi console |
| Phần Báo cáo, không tính bài chậm | `pytest reports forms_builder/tests/test_man_hinh_bang.py -m "not cham"` | đạt hết; sửa một bài đọc tệp mẫu (AC-43.4) cho đọc cả include mới |
| Phần Báo cáo, bài chậm (trình duyệt) | `pytest reports -m cham` | **19/19 đạt**, gồm bố cục Báo cáo tổng hợp và ô nhập số (`report-entry.js` đổi sang gắn theo vùng) |
| Toàn bộ, không tính bài chậm | `pytest -m "not cham"` | xem mục "Toàn bộ" bên dưới |
| Thử tay trên 8020 | script Playwright, đăng nhập `quantri` và `mkt.manager` | **16/16 đạt** (bảng dưới) |

### Thử tay trên 8020

| Bước | Kết quả |
|---|---|
| Marketing 08 → 10.10: số nút ✎ | 36 = số lần nộp; khối Toàn kỳ và TỔNG CỘNG không có |
| Bấm ✎ | Hộp mở, con trỏ ở ô số đầu tiên |
| Sửa CPQC (+500.000) rồi Lưu | TỔNG CỘNG ngày 09.10 từ 130.745.000 thành 131.245.000; không tải lại trang; dòng sáng vàng; báo "Đã lưu chỉnh sửa · đã ghi lịch sử" |
| Hai người cùng sửa | Admin mở hộp, `mkt.manager` lưu Số đơn = 14 trước, Admin bấm Lưu: 409, hộp báo "TRANGDT vừa sửa báo cáo này lúc 10:43 …", ô Số đơn tô vàng và hiện 14; Lưu lại được |
| Gộp | 36 ✎ ở cột Ngày; khối Toàn kỳ không có; Escape đóng hộp, vẫn ở chế độ mở rộng ERP |
| Sale: đổi Thị trường sang Nhật Bản | Loại tiền tự thành JPY; lưu xong dòng sang JPY; TỔNG CỘNG của ngày có thêm dòng JPY (USD, CAD, JPY) |
| `mkt.manager` mở Báo cáo tổng hợp | không có ✎ |
| Admin mở Bảng dữ liệu `bao_cao_mkt` | không có ✎ (ADR-014) |
| 390 × 844 | trang không cuộn ngang; hộp sửa 390 × 844; không lỗi console |

Ảnh chụp các bước ở scratchpad của phiên, không đưa lên kho (CLAUDE.md: không commit ảnh review thiết kế). Bài kiểm
trình duyệt lưu ảnh ở `storage/e2e/admin-sua-*.png` khi chạy.

### Toàn bộ

`pytest -m "not cham"`: 3.154 bài. **3.140 đạt, 10 bỏ qua, 4 đỏ.** Cả bốn bài đỏ đã sửa:

- **Hai bài truy vết** (`tests/test_truy_vet.py`): mục 50 được thêm vào docs/04 khi bộ kiểm đang chạy, mà bài này đọc
  docs/04 lúc nạp tệp. Chạy lại thì lộ thêm một chỗ phải sửa: bộ đếm "đã có bài kiểm" ở docs/06, nay là 346 trên 369.
- **Hai bài quét lớp CSS** (`core/tests/test_giao_dien.py`):
  - `{% if sua_bao_cao %}` và `{% if xung_dot %}` nằm trong `class="…"` nên bị đọc nhầm thành tên lớp;
  - vùng báo lỗi `.report-sua-bao-loi` không có luật CSS.

  Đã đổi sang thuộc tính `data-sua`, `id="report-sua-loi"`, và tách thẻ mở theo điều kiện.

Sau khi sửa:
- bốn tệp liên quan (`tests/test_truy_vet.py`, `core/tests/test_giao_dien.py`, `reports/tests/test_admin_sua_tong_hop.py`,
  `reports/tests/test_form_nhap_bao_cao.py`): **744/744 đạt**;
- `pytest reports -m cham`: **19/19 đạt**.

Chưa chạy lại toàn bộ trên máy ảo sau lần sửa này. CI của PR chạy lại toàn bộ: bộ chính `-m "not trinh_duyet"` và e2e.

## Chưa kiểm

- Safari, Firefox và máy Windows thật: máy ảo chỉ có Chromium.
- Hộp sửa trên bảng lớn: khối trang 100 dòng, và đường chạm trần `MAX_GROUPS` khi dòng là queryset. Ở đường đó
  `report_id` cũng đi trong `values()`, nhưng chưa đo thời gian.
- VPS: chưa phát hành. Thay đổi này không có migration.
