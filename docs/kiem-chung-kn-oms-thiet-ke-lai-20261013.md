# Biên bản kiểm chứng — KN OMS thiết kế lại theo Solarpunk Office, làm sâu sáu màn (13.10.2026)

| Mục | Nội dung |
|---|---|
| Yêu cầu | Chủ dự án 13.10: "dùng impeccable để design lại UI, sau đó nâng cấp tính năng". Chốt: chỉ KN OMS; theo Solarpunk Office như KN CRM; làm sâu sáu màn đang có; vẫn dữ liệu giả; nhánh riêng, PR riêng ([ADR-051 mục bổ sung](quyet-dinh/051-kn-oms-ban-demo.md)) |
| Phạm vi | Chỉ `templates/crm/kn_oms.html`, `static/css/oms.css`, `static/js/oms.js` và bài kiểm. **Không** đổi KN CRM, KN ERP, CSS dùng chung, model, migration, settings |
| Nhánh | `claude/kn-oms-thiet-ke-lai`, tách từ `claude/kn-oms-demo` (#112, `8832036`). Phải gộp #112 trước |
| Môi trường | Máy ảo Claude Code trên web: Python 3.11.15 (CI 3.12), Django 5.2.17, PostgreSQL 16.13, Chromium của Playwright 1.56. Hệ thống thật: ERP `runserver` 8020 và CRM 8021 trên DB `knjsc_ht`. Font Google bị chặn ở máy ảo nên ảnh chụp dùng font dự phòng (chữ mono tiếng Việt in hoa lệch dấu); máy có mạng tải đúng IBM Plex Mono |
| Kết luận | **Đạt.** Chặng 2 (chủ dự án thử ở máy mình) chưa làm |

## 1. Đã làm

| Mục | Trước | Sau |
|---|---|---|
| Diện mạo | Bảng màu chép tay trong `oms.css`; không ảnh nền, không kính, không thanh trên | Nạp bốn tệp CSS của KN CRM cùng thứ tự `base_crm.html`, rồi `oms.css`. Khung theo markup KN CRM: ảnh nền, thanh bên kính, thanh trên có đường dẫn, mặt đọc kem |
| Dải "DEMO" | Một hàng riêng ở đầu mọi màn | Nhãn "Dữ liệu giả" trên thanh trên, luôn thấy |
| Ô chỉ số | 22 ô KPI số to ở năm màn | Một dải phẳng ngăn vạch mảnh như trang chủ KN CRM, số 21 px, vẫn bấm để lọc |
| Đầu màn | Đoạn giới thiệu 182–290 ký tự | Một câu dưới 90 ký tự; giải thích dài vào khối "Cách tính" (Lãi, Kho, Khách rủi ro) |
| Viền trái | Thẻ rủi ro 4 px, khoản tiền về 3 px | Bỏ. Thẻ rủi ro nền nhạt theo mức, viền 1 px; khoản tiền về có chip "Chờ khớp" / "Đã khớp" |
| Ghi nhận tiền, Phiếu kho, Thêm kênh | Ba hộp thoại | Ba biểu mẫu trong ngăn kéo bên phải. Huỷ, Esc ở biểu mẫu mở từ ngăn kéo đơn thì quay về ngăn kéo đó |
| Lọc ngày | — | Báo đơn: chip Hôm nay, 7, 30 ngày, Tất cả và ô Từ–Đến DD/MM/YYYY (`date-inputs.js` dùng chung). Công nợ: ô Từ–Đến ngày giao |
| Xuất danh sách | — | Báo đơn, Công nợ: CSV các dòng đang lọc (mọi trang) |
| Công nợ chọn nhiều | — | Ô tích, ô chọn tất cả (chỉ các dòng đang lọc), thanh "Đã chọn N đơn · Nhắc N đơn · Xuất N đơn · Bỏ chọn" |
| Khách | Danh sách đơn | Thêm dòng thời gian gộp mọi đơn và mọi lần đánh dấu, mới nhất trước |
| Chặn lên đơn | Bấm là chặn | Phải ghi lý do ngay tại chỗ; lý do hiện ở thẻ cảnh báo, danh sách (gợi ý khi trỏ) và dòng thời gian |
| Kho | Tồn, giữ, có thể bán | Thêm "đủ bán N ngày" và "gợi ý nhập", tính riêng từng kho; Phiếu kho mở từ dòng điền sẵn số gợi ý và đúng kho |
| Kênh | Số 7 ngày | Thêm "So với 7 ngày trước": số đơn, phần trăm doanh số. Biểu đồ 14 ngày dừng được bằng Tab, có bảng số đối chiếu |
| Lãi theo page | Bảng và thác chi phí | Thêm biểu đồ lãi theo ngày: chọn page, phím ← → Home End, bảng số đối chiếu có dòng tổng |
| "7 ngày" | Kênh, Lãi lùi 7 × 24 giờ | 7 ngày lịch giờ Việt Nam ở Báo đơn, Kênh, Lãi. Tốc độ xuất ở Kho vẫn 7 × 24 giờ |

## 2. Bài kiểm tự động

| Kiểm | Kết quả |
|---|---|
| AC-51.9 (máy chủ): thứ tự bốn tệp CSS so với trang chủ KN CRM, markup khung, `oms.css` không khai lại 31 biến của KN CRM, không viền một bên quá 1 px, không hộp thoại | Đạt |
| AC-51.10 → 51.14: viết trước, chạy thấy **5/5 đỏ** đúng chỗ thiếu (không có `#bd-ngay`, `#cn-chon-het`, `#f-chan`, không có gợi ý nhập, không có biểu đồ) | Đỏ trước khi làm |
| `tests/e2e/test_kn_oms_e2e.py` sau khi làm: 5 bài cũ (sửa móc đổi có chủ ý: `.gia-tri`, `.o-so`, `.bang-cuon`, `#ngan` thay `#hop`, cột ô tích, chặn có lý do) + 6 bài mới AC-51.9 → 51.14 | **11/11 đạt, chạy 3 lần liền** |
| AC-51.9 (trình duyệt): so `getComputedStyle` giữa trang chủ KN CRM và KN OMS ở nền sáng và tối, 8 nhóm bộ chọn, 32 thuộc tính | Bằng nhau từng giá trị |
| `crm/tests/test_kn_oms.py` | **15/15 đạt** (thêm AC-51.9) |
| `core/tests/test_giao_dien.py` (soát lớp CSS theo năm tệp trang nạp), `tests/test_truy_vet.py` | Đạt. Bộ đếm docs/06: 398 tiêu chí, 362 trên 385 |
| `manage.py check` (test, bangtinh); `makemigrations --check` | Không lỗi; "No changes detected" |
| Toàn bộ trừ trình duyệt: `pytest -m "not trinh_duyet" -rf` | **3.207 đạt, 7 bỏ qua, 0 đỏ** (110 bài trình duyệt tách riêng); thêm đúng 1 bài so với 3.206 của #112 (AC-51.9 phía máy chủ) |

## 3. Rà kết thúc theo `craft-floor` (thủ công, không engine)

| Kiểm | Cách đo | Kết quả |
|---|---|---|
| Tràn ngang | Quét bề ngang 320 → 1440 px bước 16 (71 cỡ) × 6 màn: khung bảng và trang | **0 px ở cả 426 lần đo** |
| Tương phản chữ | Script trong trình duyệt: mọi nút chữ đang hiện, nền chồng các lớp cha lên `--plane` (bỏ qua ảnh dưới kính), WCAG 4,5:1 chữ thường, 3:1 chữ lớn; 6 màn + ngăn kéo đơn + ngăn kéo biểu mẫu, sáng và tối | Tối: 0 chỗ dưới ngưỡng. Sáng: 6 chỗ 4,48:1 (nhãn nhóm thanh bên, "Bản demo", đường dẫn) — token `--ink-3` trên kính của KN CRM, trang chủ KN CRM đo ra y hệt; không sửa trong việc này |
| Trạng thái | Bảng trống, ngày sai, số lượng sai, Từ sau Đến, chặn không lý do | Bảng trống nói rõ và có nút "Bỏ lọc"; lỗi nằm ngay dưới ô, nêu cách sửa; ô sai có `aria-invalid` |
| Bàn phím | Tab qua thanh bên, thanh trên, dòng bảng; Enter mở dòng; Esc đóng; biểu đồ ← → Home End | Vòng focus 2 px màu chính ở mọi điểm dừng; ngăn kéo mở thì phía sau `inert` |
| Bề mặt trình duyệt | Màu chọn chữ, con trỏ gõ, thanh cuộn, gạch chân liên kết | Theo `solarpunk.css` của KN CRM; số trong bảng dạng tabular |
| Chuyển động | Ngăn kéo 180 ms, thông báo 200 ms | Tắt khi `prefers-reduced-motion` (luật chung của `main.css`) |
| Điện thoại | ☰ mở thanh bên; chọn màn, Esc hay bấm ra ngoài thì đóng | Đạt; `aria-expanded` đúng |

## 4. Vấn đề tìm ra khi làm, đã sửa

| # | Thấy gì | Sửa |
|---|---|---|
| 1 | Bảng KN CRM (ô 16 px, tiêu đề mono chữ hoa) rộng hơn bảng cũ: lượt quét đầu tràn ở 75/426 lần đo, Công nợ tới 201 px | Đo bề rộng tối thiểu từng cột rồi đặt mốc ẩn cột theo số đo (1100 / 940 / 700 / 520 px khung); gộp PTTT, Đã thu vào cột khác; Kho một nút "Phiếu kho" thay hai nút |
| 2 | Lưới `.luoi-2` của KN CRM tối thiểu 320 px: trang tràn 19 px ở màn 320 | Riêng KN OMS: `minmax(min(100%,320px),1fr)` |
| 3 | Chữ phụ trên nền vàng của mục đang chọn 4,26:1 (sáng), 3,95:1 (tối) | Dùng `--ink-2` trên nền đó |
| 4 | Xem tất cả kho thì gợi ý nhập bị tồn của kho khác che (không sản phẩm nào cần nhập), và dòng đủ bán nói kho khác với nhãn trạng thái | Tính riêng từng kho; dòng nêu kho cần nhập nhiều nhất, không thì đúng kho nhãn trạng thái đang nói |
| 5 | Bảng số đối chiếu 14 ngày ở Kênh rộng 780 px | Dưới 940 px chỉ còn Ngày, Tổng |
| 6 | Nhãn thanh toán dưới số tiền bẻ đôi ở màn 390 | Một dòng; chỉ bẻ khi khung bảng dưới 310 px |
| 7 | Nhãn số ở hai mép biểu đồ lòi ra ngoài | Neo trái ở điểm đầu, neo phải ở điểm cuối; nhãn số âm đặt dưới điểm |
| 8 | Mã vận đơn toàn số (USPS 22 chữ số) mở bằng Excel thành số mũ | CSV thêm `'` trước dãy số từ 12 chữ số, như ô mở đầu bằng `= + - @` |

## 5. Hệ thống thật, đi thử bằng trình duyệt

Chromium 1366 × 900, đồng hồ thật. **16/16 đạt**, không lỗi JS:

1. Thanh bên KN CRM có "KN OMS", mở tab mới.
2. KN OMS mang khung Solarpunk như KN CRM, có nhãn "Dữ liệu giả".
3. Báo đơn lọc "Hôm nay": 10 đơn, đều ngày 13/10.
4. Xuất danh sách: `kn-oms-bao-don-20261013.csv`, có BOM, 10 dòng.
5. Công nợ: nhóm trên 30 ngày, chọn tất cả (2 đơn), "Nhắc 2 đơn".
6. Ghi nhận tiền mở trong ngăn kéo, không hộp thoại.
7. Huỷ biểu mẫu thì về ngăn kéo đơn.
8. Chặn lên đơn không ghi lý do thì báo lỗi.
9. Dòng thời gian khách có lý do chặn ở dòng đầu.
10. Kho có đủ bán và gợi ý nhập (71, kho HN).
11. Thẻ kênh có "So với 7 ngày trước".
12. Lãi theo page: biểu đồ 30 điểm, vẫn đúng hai page lỗ (Japan, LazMall).
13. Không lỗi JS.
14. `sale.staff` gọi `/oms/`: 403.
15. Thanh bên `sale.staff` không có KN OMS.
16. KN ERP `/oms/`: 404.

Ảnh trước/sau (6 màn × sáng/tối × 1366/390) gửi chủ dự án trong phiên làm việc, không đưa lên kho.

## 6. Chưa kiểm, giới hạn

- Chặng 2: chủ dự án thử ở máy mình (font thật, màn thật).
- Bộ e2e toàn phần như CI chạy ở CI của PR; trên máy ảo, 9 bài của `test_pha_luoi_ghi_chu.py` đỏ sẵn vì phông Google qua proxy (đã ghi ở biên bản 13.10 trước).
- Nhãn nhóm thanh bên, đường dẫn 4,48:1 ở nền sáng là token chung KN CRM; muốn sửa thì làm ở `solarpunk.css` cho cả KN CRM, việc riêng.
- Mọi ngưỡng, phí, giá vốn, cước, quảng cáo, tỉ giá vẫn là số minh hoạ (ADR-051).
