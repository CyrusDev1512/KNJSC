# Kiểm chứng — Dòng TỔNG CỘNG dính: lộ chữ mờ và lệch khỏi tiêu đề (TL-69) — 30.09.2026

Nhánh `claude/sua-dong-tong-dinh-mo` tách từ `main` (`c7065fe`), rồi đặt lại lên `b1d081d` (sau PR #70) trước
khi đẩy. Chạy trên máy ảo Claude Code với PostgreSQL 16
cục bộ (cổng 5434) và Chromium không màn hình (Playwright). Proxy của máy ảo chặn phông Google nên chữ dùng
phông thay thế: số px dưới đây lệch máy thật vài px, cơ chế thì như nhau. Không migration, không thêm thư viện,
không đổi nghiệp vụ hay quyền.

## Lỗi

Chủ dự án gửi video VPS 30.09: Báo cáo Marketing 01–30.09, Không gộp, Cộng theo ngày, Toàn màn hình. Cuộn bảng
thì năm cột có số chồng lên số, "bị mờ và đau mắt"; dưới hàng tiêu đề có một dải trắng khoảng 29 px cho dòng
đang cuộn lọt qua.

## Nguyên nhân

| # | Chỗ | Vì sao |
|---|---|---|
| 1 | `solarpunk.css`, `.report-table .o-chi-so` (19.09, AC-22.16) | Nền `color-mix(… 45%, transparent)` cùng độ ưu tiên và đứng sau nền đặc của `.report-total>*`, nên ô dòng tổng ở 5 cột chỉ số (Tỉ lệ chốt, Tỉ lệ chốt (TT), Giá Mess, CPO, CPQC/DS Chốt) chỉ đục 0,45. Trước ADR-046 chỉ có một dòng tổng dính nên ít thấy; từ ADR-046 mỗi loại tiền một dòng, bốn dòng dính chồng nên lộ rõ |
| 2 | `report-filters.js`, `headHeight()` | Đo hàng tiêu đề của **bảng đầu** ngay lúc bấm Toàn màn hình hay thu bộ lọc, khi lưới còn chuyển cột trong 0,2 s; chỉ đo lại khi đổi cỡ cửa sổ. Số gán cho cả khung nên bảng các ngày khác cũng dùng số của bảng đầu |
| 3 | Bảng dữ liệu dạng báo cáo (`forms_builder/bang_xem.html`) | Cùng `reports/_bang_khoi.html` nhưng `<div class="report-view">` không có id, nên cả khối điều khiển trong `report-filters.js`, kể cả phần đo, bị bỏ qua. Dòng tổng luôn dính ở 41 px mặc định, tiêu đề cao hơn thì bị đè. Chưa ai báo; lộ ra khi đọc mã lúc sửa |

## Mockup đã duyệt

Trước khi sửa mã, dựng một trang HTML: bảng dựng lại từ video, chạy nguyên CSS và JS của `main`, có nút đổi
"Bản đang chạy / Bản sửa", số đo trực tiếp và nút tự kiểm 9 độ rộng cửa sổ. Trên Chromium: bản đang chạy lộ
chữ ở 9/9 độ rộng, dòng tổng lệch ở 1/9 (hở 15 px ở 1920); bản sửa 0/9 cả hai. Chủ dự án thử và duyệt ngày
30.09: "ổn rồi, sửa vào mã thật đi". Mockup không vào kho mã.

## Sửa

| Tệp | Thay đổi |
|---|---|
| `app/static/css/solarpunk.css` | `.report-table .o-chi-so` pha với `var(--surface)` thay vì `transparent`. Độ ưu tiên giữ nguyên nên màu ngưỡng, nền cột ở tiêu đề, sọc và hover không đổi; lúc đứng yên nhìn y như cũ vì dưới ô vốn là nền `--surface` của khung bảng |
| `app/static/js/report-filters.js` | Bỏ `headHeight()`. `measureTable` đặt `--head-h` (chiều cao `thead`, không làm tròn) và `--total-h` lên **từng bảng**; đo lúc tải trang, rồi `ResizeObserver` đo lại mỗi khi bảng đổi cỡ (trình duyệt không có thì dùng `resize`). Đoạn này nằm ngoài khối điều khiển bố cục nên chạy cả ở Bảng dữ liệu |
| `app/reports/tests/test_bo_cuc_bao_cao_e2e.py` | Bài trình duyệt `test_dong_tong_dinh_nen_dac_va_sat_tieu_de` (AC-22.21) |
| `docs/04`, `docs/06`, `test-log`, `backlog`, `backlog-kanban` | AC-22.21; bộ đếm 295 — 282 tự động, 13 thủ công; 259 trên 282; TL-69 |

## Kiểm

**Bài AC-22.21.** Dữ liệu: sáu ngày, hai marketer, ba loại tiền, nên mỗi khối có ba dòng TỔNG CỘNG. Bài kiểm:

- **Báo cáo tổng hợp 2400 px:**
  - mọi ô dòng tổng có nền đặc, ô chỉ số có màu bằng 45 % `--accent-soft` phủ trên `--surface` (lệch ≤ 1,5/255);
  - nới bộ lọc ra 1100 px rồi bấm Toàn màn hình. Tiền đề: tiêu đề thật sự thấp đi. Mỗi bảng có `--head-h` và
    `--total-h` khớp chiều cao thật (±1 px);
  - cuộn thì dòng tổng đầu sát đáy tiêu đề, các dòng tổng liền nhau;
  - nền tối: nền đặc, màu đúng như trên.
- **390 px:** nền đặc, số đo khớp, sát tiêu đề, trang không tràn ngang.
- **Bảng dữ liệu 1440 px:** nền đặc, số đo khớp, sát tiêu đề.

Làm đỏ trước, cùng máy:

| Mã | Kết quả |
|---|---|
| `c7065fe`, chưa sửa | Đỏ ở bước đầu: ô `o-chi-so` của dòng tổng nền trong suốt, màu lệch 17/255 |
| Chỉ sửa CSS | Đỏ ở bước Toàn màn hình: cả 7 bảng có tiêu đề cao 31,4 px mà dòng tổng dính ở 75 px |
| Sửa CSS và JS, tạm tắt phần đo ở Bảng dữ liệu | Đỏ ở Bảng dữ liệu: tiêu đề 74,6 px, dòng tổng dính ở 41 px |
| Bản sửa đủ | Đạt |

**Đo trên dữ liệu giả cỡ thật** (CSDL `knjsc_bc_perf`, Báo cáo Marketing 01–30.09; máy chủ 8030 chạy
`main`, 8031 chạy nhánh này; Chromium, cùng thao tác):

| Chỗ | Trước | Sau |
|---|---|---|
| Báo cáo 1960 px, bấm Toàn màn hình, cuộn 150 px | Tiêu đề 60 px, dòng tổng dính ở 75 px: hở 15 px. Ô chỉ số đục 0,45 | Dính ở 60,2 px: hở 0. Đục 1 |
| Báo cáo 1920 px, cùng thao tác | Tiêu đề 75 px, dính ở 75 px (bảng tràn ngang ở cả hai trạng thái nên tiêu đề không đổi). Đục 0,45 | Hở 0. Đục 1 |
| Bảng dữ liệu 1440 px, cuộn 150 px | Tiêu đề 75 px, dòng tổng dính ở 41 px: đè 34 px, che tên cột. Đục 0,45 | Hở 0. Đục 1 |

Ảnh trước và sau lưu ngoài kho mã; ảnh của bài kiểm nằm ở `storage/e2e/` (`bao-cao-dong-tong-dinh-2400`,
`bao-cao-dong-tong-dinh-toi`, `bao-cao-dong-tong-dinh-390`, `bang-du-lieu-dong-tong-dinh`).

**pytest**, chạy tuần tự, không có pytest nào chạy song song:

| Lệnh | Kết quả |
|---|---|
| `pytest tests/test_truy_vet.py` | 36 đạt, bộ đếm mới khớp `docs/04` |
| `pytest -m trinh_duyet --ignore=tests/e2e -rs` (lượt 2 của CI) | 7 đạt, 9 bỏ qua như CI (giá đỡ cho script Node). Có cảnh báo "database đang có phiên khác" lúc xoá DB cuối phiên; cảnh báo này có từ trước (TL-67) |
| `pytest tests/e2e -m trinh_duyet -rs` (lượt 1 của CI) | 37 đạt, 2 bỏ qua. 9 bài đỏ, đều trong `test_pha_luoi_ghi_chu.py`, cùng một lỗi console `ERR_CERT_AUTHORITY_INVALID` do proxy máy ảo chặn phông Google. Lỗi này có sẵn trên `main` ở máy ảo, CI GitHub không gặp (TL-67). Không có `deadlock` |
| `pytest -m "not trinh_duyet" --ignore=tests/perf -rs`, bộ đầy đủ kể cả bài chậm | **2.854 đạt**, 7 bỏ qua (thiếu điều kiện ngoài, như trước), 5 phút 49 giây |
| `pytest reports/tests/test_bo_cuc_bao_cao_e2e.py -m trinh_duyet` (chạy lại sau lần gọn cuối) | 4 đạt |
| `node --check app/static/js/report-filters.js` | Ổn |

**Sau khi đặt lại lên `b1d081d`.** PR #70 (cách xem "Hiệu suất theo team") gộp vào `main` trong lúc làm và đã lấy
mã AC-22.20, nên tiêu chí của việc này đổi thành **AC-22.21**. Bộ đếm sau cả hai việc: 295 tiêu chí, 282 tự động,
13 thủ công; 259 trên 282. #70 chỉ đổi mã Python của báo cáo, không đụng CSS, JS hay khối bảng. Chạy lại trên
nền mới:

| Lệnh | Kết quả |
|---|---|
| `pytest tests/test_truy_vet.py` | 36 đạt |
| `pytest -m trinh_duyet --ignore=tests/e2e -rs` (lượt 2 của CI, có bài AC-22.21) | 7 đạt, 9 bỏ qua như trên |
| `pytest reports -m "not trinh_duyet"` | 229 đạt |

Lượt `tests/e2e` và bộ đầy đủ ở trên chạy trên `c7065fe` cộng bản sửa, trước khi đặt lại; CI của PR chạy lại cả
hai trên nền mới.

## Chưa kiểm / để lại

- Chrome thật với phông Be Vietnam Pro: CI GitHub có phông; kiểm tay trên VPS sau khi Codex phát hành.
- Nhánh dự phòng cho trình duyệt không có `ResizeObserver` chưa chạy; mọi trình duyệt còn được hỗ trợ đều có.
- Khung hình đầu tiên, trước khi JS chạy, dòng tổng vẫn dùng số mặc định 41/35 px như trước. Chỉ thấy khi cuộn
  ngay trong khung hình đó.
- VPS: cần phát hành lại để có bản sửa.
