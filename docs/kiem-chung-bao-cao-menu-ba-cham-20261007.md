# Biên bản kiểm chứng — Báo cáo tổng hợp: đầu trang gọn, menu ⋯ (07.10.2026)

| Mục | Nội dung |
|---|---|
| Yêu cầu | Chủ dự án 07.10.2026: "tôi muốn sửa cái view bảng kéo dài lên trên chỗ xuất excel, ngoài ra mấy cái kiểu xuất excel, gộp với không gộp cho thành 1 dấu 3 chấm, bấm vào thì rơi ra drop down"; xem mockup lần một: "cho view bảng cao đến đoạn này luôn, mấy cái chức năng cho bên trong"; duyệt mockup v2: "ok làm đi, bảng dữ liệu chưa cần, lập plan làm cẩn thận, không break hay conflict với những thứ hiện có" |
| Quyết định | [ADR-042 bổ sung 07.10](quyet-dinh/042-bao-cao-tong-hop-nhu-anh-mau.md) |
| Tiêu chí | AC-42.18 → 42.21 (mới); AC-22.13, AC-22.24, AC-22.26, AC-42.5, AC-48.4 đổi chữ |
| Lỗi | TL-74 (bảng hụt 96 px khi thanh menu dưới đã thu), TL-75 (Escape không thoát toàn màn hình khi đang lọc sản phẩm) — [test-log](test-log.md) |
| Nhánh | `claude/bao-cao-menu-ba-cham` từ `Staging` `6a266b2`; PR nháp về `Staging` |
| Môi trường | Máy ảo Claude Code trên web: Python 3.11.15, Django 5.2.17, PostgreSQL 16.13 cục bộ, Redis, Chromium của Playwright 1.56 |

## Đã đo

### Khung bảng trước và sau

Máy chủ thử 8020, CSDL nháp có báo cáo Marketing mẫu (425 lần nộp 01/10 – 07/10/2026), tài khoản `quantri`. Kịch bản
Playwright mở trang rồi đo ngay, không đổi cỡ cửa sổ. Cùng dữ liệu, cùng kịch bản trên `Staging` `6a266b2` (trước) và
nhánh này (sau).

| Cảnh | Trước: đỉnh khung · cao · dòng thấy trọn · hụt đáy | Sau |
|---|---|---|
| 1366×768, Mở rộng ERP, thanh menu thu, bộ lọc thanh dọc (cảnh của ảnh chủ dự án) | 232 px · 342 px · 5 · **96 px** | 92 px · **578 px** · 9 · 0 |
| 1366×768 mặc định (thanh menu mở, bộ lọc mở) | 260 · 310 · 4 · 0 | 120 · 450 · 7 · 0 |
| 1440×900 mặc định | 260 · 442 · 7 · 0 | 120 · 582 · 9 · 0 |
| 1024×768 mặc định | 304 · 266 · 3 · 0 | 120 · 450 · 7 · 0 |
| 390×844 (điện thoại) | 392 · 447 · 6 · trang cuộn thêm 252 px | 142 · 445 · 6 · trang không cuộn |

Thanh trên cùng giữ chiều cao cũ: 66 px ở mọi cỡ ≥ 701 px; 108 px (hai hàng) ở 390 px. Không cảnh nào tràn ngang.

### Bài kiểm

| Kiểm | Lệnh (từ `app/`) | Kết quả |
|---|---|---|
| Bài mới trên mã `Staging` (chưa sửa mã) | `pytest reports/tests/test_bo_cuc_bao_cao.py reports/tests/test_bo_cuc_bao_cao_e2e.py -k "…bài mới…"` | 7 bài máy chủ AC-42.18 đỏ đúng lý do (thanh trên chưa có tên báo cáo, kỳ, menu); bài canh Bảng dữ liệu xanh như mong; 3 bài trình duyệt đỏ: AC-42.19, 42.20 không có menu ⋯, AC-42.21 hụt 96 px, khung 342 px |
| Bài mới sau sửa | cùng lệnh | 11/11 đạt |
| Cả tệp bố cục trình duyệt | `pytest reports/tests/test_bo_cuc_bao_cao_e2e.py` | 14/14 đạt |
| Toàn bộ phía máy chủ | `pytest -m "not trinh_duyet"` | 3.071 bài, thoát mã 0, không bài nào đỏ (các bài kiểm tải tự bỏ qua như mọi lượt) |
| Bước trình duyệt 2 như CI | `pytest -m trinh_duyet --ignore=tests/e2e -vv -rs --durations=10 -o faulthandler_timeout=120` | **19 đạt, 9 bỏ qua, 0 đỏ** (3 phút 40 giây); bỏ qua là chín tệp `*_browser*.py` cần biến môi trường riêng, như mọi lượt |
| Bước trình duyệt 1 như CI (lưới KN CRM, mã lượt này không đụng) | `pytest tests/e2e -m trinh_duyet -vv -rs --durations=10 -o faulthandler_timeout=120` | 48 đạt, 2 bỏ qua, **10 đỏ, đều không do lượt này**: 9 bài `test_pha_luoi_ghi_chu.py` đỏ vì proxy của máy ảo chặn phông Google (`ERR_CERT_AUTHORITY_INVALID`) — chạy trên `Staging` gốc (git worktree) đỏ y hệt, CI không gặp; bài `test_do_hieu_nang_1000_dong_ghi_chu_400` quá hạn 75 giây khi chạy trong cả lượt (máy ảo đang chạy song song máy chủ thử 8020), chạy riêng trên nhánh này 2 lần đều đạt (22 giây), trên `Staging` gốc cũng đạt — chờ CI xác nhận |

Bài cũ đổi theo cấu trúc mới (cùng mã AC, chỉ đổi chỗ bấm, không nới điều kiện): AC-22.13, 22.21, 22.24, 22.26, 42.7.
Bài AC-22.19 sửa phần dựng: trước đây trang chỉ cuộn được nhờ lệch 1 px tình cờ ở đáy, nay lệch còn 0,14 px nên bài chèn
300 px dưới khung báo cáo cho trang có chỗ cuộn (ghi ở TL-74 trong test-log).

### Thử tay trên máy chủ thử (kịch bản Playwright, `quantri`)

| Thử | Kết quả |
|---|---|
| Bảng dữ liệu dạng báo cáo: còn hàng nút Không gộp / Gộp và hàng chip, không có ⋯, không đặt `--report-nhuong` | Đạt |
| Bảng dữ liệu bấm Gộp: tải cả trang như cũ | Đạt |
| Bàn phím: focus ⋯, Enter mở menu, Tab vào "Không gộp", Escape đóng và về ⋯ | Đạt |
| Lưu Ngưỡng màu từ panel mở bằng menu: form gửi được, về lại đúng báo cáo | Đạt |
| Xuất Excel từ menu: tải `bao-cao-tong-hop.xlsx` (52 KB), menu đóng | Đạt |
| Chọn nhanh "Hôm qua": gửi bộ lọc, kỳ trên thanh trên cùng đổi thành "06/10 – 06/10/2026 · Tiền: ₫" | Đạt |
| Lỗi console (trừ phông Google bị proxy của máy ảo chặn) | 0 |

Ảnh đã xem bằng mắt, so với mockup v2:

- menu mở; panel Giải thích số liệu; panel Ngưỡng màu; Gộp; Toàn màn hình kèm menu ("Thoát toàn màn hình");
- lọc nhiều (chip bị cắt, mờ ở mép, tên báo cáo đủ chữ);
- 390 px, menu ở 390 px, 768, 1024, 1920 px;
- nền tối.

### Lỗi tự gây trong lượt, đã sửa trước khi đẩy

| Lỗi | Thấy ở đâu | Sửa |
|---|---|---|
| Chú thích `{# … #}` viết hai dòng: Django in nó thành chữ, đẩy bảng xuống 60 px (khung 518 thay vì 578 px) | Bài AC-42.21 đỏ ở "khung ≥ 570"; ảnh chụp thấy dòng chữ | Đổi sang `{% comment %}`; bài AC-42.18 thêm kiểm cú pháp template không lọt ra trang |
| Nhiều chip thì tên báo cáo cũng bị co (chip co theo trọng số, tên co một phần nhỏ của 1 px là đủ hiện "…") | Ảnh lọc nhiều ở 1366 px | ⋯ đứng trước chip; chip gốc 0, chỉ lấy chỗ còn thừa |
| 390 px: tên báo cáo còn "Báo …" | Ảnh 390 px | Nút lọc ghi "Lọc" / "Lọc (n)"; ≤ 900 px logo không kèm chữ "KN JSC" |

## Khác mockup

- ⋯ đứng ngay sau kỳ, chip đứng sau ⋯ (mockup để chip trước ⋯). Lý do ở bảng trên: tên báo cáo không bị cắt khi nhiều
  chip, ⋯ không nhảy chỗ khi bấm Gộp làm chip đổi.
- Màn ≤ 900 px ẩn cả kỳ (mockup chỉ nói chip gom vào nút "Lọc (n)"): thiếu chỗ cho tên báo cáo; kỳ vẫn ở ô Từ ngày /
  Đến ngày trong ngăn bộ lọc.

## Chưa kiểm / để lại

- Safari, Firefox: chưa thử. Mã dùng `:has()`, `display:contents`, `mask-image`, `ResizeObserver` — có từ Safari 15.4,
  Firefox 121; dự án đã dùng `:has()` từ trước.
- Bảng dữ liệu dạng báo cáo giữ hàng nút cũ, và vẫn chưa đo lại khi thu/mở thanh menu. Lúc mở trang thì đúng vì nó nạp
  script sau shell. Để nguyên theo lời chủ dự án "bảng dữ liệu chưa cần".
- Chưa chạy trên máy chủ dự án, Windows thật và VPS. Không migration; phát hành chỉ cần mã mới.
