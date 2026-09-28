# Kiểm chứng — Bấm đảo thứ tự không làm trang giật (TL-62) — 28.09.2026

Nhánh `claude/sap-xep-khong-giat` tách từ `main` (`a0313be`), máy ảo Claude Code, PostgreSQL 16, Chromium.
Chủ dự án báo: bấm sắp xếp theo Quốc gia thì "cả trang bị load".

## Nguyên nhân (đọc mã, đã đo lại bằng bài kiểm)

**Lưới KN CRM** không tải lại trang thật, nhưng `navigate()` xử lý đổi thứ tự như mở bảng mới:

1. cuộn về dòng đầu **và cột đầu** (`scrollLeft = 0`) — đang ở cột Quốc gia bị kéo về cột Ngày;
2. `state.ready = false` nên `render()` dừng: màn hình đứng hình, mũi tên ↑↓ trên tiêu đề chưa đổi
   tới khi dữ liệu về (không hiện ô "…" như em nói ban đầu — đã đính chính với chủ dự án);
3. `invalidate(true)` đặt lại chiều cao mọi dòng về 28 px (`geometry.reset`);
4. tải lại **cả trang HTML** (`X-Master-Filters`) chỉ để lấy khung lọc, rồi thay khung lọc và chip.

**Bảng dữ liệu ERP**: tiêu đề cột là liên kết thường, bấm là trình duyệt tải lại cả trang.

## Sửa

- `static/js/master-grid.js`: `navigate(params, push, onlyOrder)` — nút tiêu đề cột gọi với
  `onlyOrder=true`: chỉ đưa về dòng đầu, giữ cuộn ngang, bỏ vùng chọn, đi `refreshSoft()` (giữ dòng
  đang hiện trong `state.stale` tới khi khối mới về, giữ chiều cao dòng, `ready` vẫn đúng nên tiêu đề
  vẽ lại ngay), không tải trang HTML. Bấm "×" trên chip lọc lấy `sap`/`chieu` đang dùng (chip dựng sẵn
  lúc tải trang mang thứ tự cũ).
- `templates/forms_builder/_bang_xem_bang.html` (mới, tách từ `bang_xem.html`, không đổi nội dung):
  khối bảng thô + phân trang trong `#bang-du-lieu`; tiêu đề cột thêm `hx-get`, `hx-target`,
  `hx-push-url`. `forms_builder/views.py` `bang_xem`: yêu cầu HTMX thì trả riêng tệp này.
- Không đổi cách máy chủ sắp xếp, phân quyền, dạng báo cáo của Bảng dữ liệu; phân trang ERP vẫn tải trang.

## Kiểm (TDD: đỏ trên mã cũ, xanh sau sửa)

| Bài | Trước sửa | Sau sửa |
|---|---|---|
| `tests/e2e/test_sap_xep_khong_giat.py::test_luoi_sap_xep_theo_quoc_gia_khong_giat` (AC-21.12; cuộn ngang 150 px, hoãn phản hồi `du-lieu/` 400 ms như mạng VPS, đếm từng khung hình) | **đỏ**: tải lại trang HTML 1 lần, cuộn ngang 150 → 0, mũi tên chưa đổi sau 200 ms | xanh: mũi tên đổi < 200 ms, 0 khung hình "…", 0 lần tải HTML, cuộn ngang giữ 150, dòng Canada lên đầu |
| `…::test_bo_chip_loc_sau_khi_sap_xep_giu_thu_tu_moi` (AC-21.12) | **đỏ** (đối chứng tạm bỏ dòng sửa chip): thứ tự mất sau khi bỏ chip | xanh: còn `sap=ten_khach&chieu=tang` |
| `…::test_bang_du_lieu_sap_xep_khong_tai_lai_trang` (AC-7.13, ERP) | **đỏ**: trang tải lại khi bấm tiêu đề | xanh: không tải lại, URL mang `sap`, thứ tự An → Bảo, bấm lần hai `chieu=giam` |
| `forms_builder/tests/test_man_hinh_bang.py::test_sap_xep_bang_htmx_chi_tra_khoi_bang_va_van_chan_quyen` (AC-7.13) | — | xanh: HTMX trả riêng khối bảng đúng thứ tự; không HTMX vẫn cả trang; Staff 403, bảng bộ phận khác 404 |
| `forms_builder/tests/test_man_hinh_bang.py` trọn tệp | — | 29 đạt |
| `tests/test_truy_vet.py` + `core/tests/test_giao_dien.py` (docs/06 → 279 / 266 / 243) | — | 666 đạt |
| Suite đầy đủ `-m "not trinh_duyet and not cham"` | — | **2.808 đạt, 1 bỏ qua, 0 đỏ** (341 s) |

## Chưa kiểm

- Bảng lớn thật (hàng chục nghìn dòng trên VPS): mới đo bằng hoãn mạng giả lập; cảm nhận thật cần anh
  thử trên máy.
- Dòng ghi chú tự giãn: giữ chiều cao cũ theo vị trí tới khi đo lại, có thể nhảy một nhịp khi dòng đổi chỗ.
- Chưa phát hành VPS.
