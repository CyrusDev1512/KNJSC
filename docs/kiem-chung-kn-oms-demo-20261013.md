# Biên bản kiểm chứng — KN OMS: bản demo dữ liệu giả trong KN CRM (13.10.2026)

| Mục | Nội dung |
|---|---|
| Yêu cầu | Chủ dự án 13.10: "mockup + 1 2 3 làm sang một site khác từ KN CRM có thể mở KN OMS để có mockup + 1 2 3". Chốt: đường dẫn riêng `/oms/` trong KN CRM, chỉ Admin, toàn bộ dữ liệu giả ([ADR-051](quyet-dinh/051-kn-oms-ban-demo.md)) |
| Phạm vi | Mã: 1 view mới, 1 đường dẫn, 1 mục thanh bên, 1 thuộc tính `title` ở `base_crm.html`. Giao diện: template, `oms.css`, `oms.js` mới. Bài kiểm: 2 tệp mới, bảng `CSS_RIENG` ở bài soát lớp CSS. **Không** model, migration, settings, container, nginx |
| Môi trường | Máy ảo Claude Code trên web: Python 3.11.15 (CI 3.12), Django 5.2.17, PostgreSQL 16.13, Redis, Chromium của Playwright 1.56. Hệ thống thật: ERP `runserver` 8020 (`settings.dev`) và CRM 8021 (`settings.bangtinh`) chạy mã nhánh trên DB `knjsc_ht` (24 tài khoản mẫu) |
| Kết luận | **Đạt.** Chặng 2 (chủ dự án thử ở máy mình) chưa làm |

## 1. Đã làm

| Mục | Trước | Sau |
|---|---|---|
| Mockup Báo đơn, Kho, Kênh bán & Page | Một trang artifact riêng, ngoài hệ thống | Ba màn trong KN OMS, dữ liệu y như mockup (cùng hạt giống, cùng thứ tự sinh) |
| Đề xuất 1, 2, 3 | Chỉ là danh sách đề xuất | Ba màn Công nợ & đối soát, Khách rủi ro, Lãi theo page (ADR-051 mục 4) |
| Lối vào | — | Mục "KN OMS" cuối thanh bên KN CRM, chỉ Admin, mở tab mới. `/oms/` chỉ có ở KN CRM |
| Vai khác Admin gọi `/oms/` | — | 403 "Bạn không có quyền truy cập", một dòng nhật ký từ chối |
| KN ERP `/oms/` | — | 404 |
| Bài soát lớp CSS | Mọi template soát theo bộ CSS dùng chung | Template đứng riêng soát theo đúng tệp nó nạp (`CSS_RIENG`) |

## 2. Bài kiểm tự động

| Kiểm | Kết quả |
|---|---|
| `crm/tests/test_kn_oms.py` (AC-51.1 → 51.4) trước khi có view, template, tệp tĩnh | Đỏ, đúng chỗ thiếu |
| Cùng tệp sau khi làm | **14/14 đạt.** 10 vai khác Admin (gồm Leader, Manager Vận đơn, CEO) mỗi vai một bài 403 + nhật ký; chưa đăng nhập về `/dang-nhap/?next=/oms/`; POST 405; thanh bên; ERP 404 |
| `tests/e2e/test_kn_oms_e2e.py` (AC-51.5 → 51.8), đồng hồ trình duyệt đóng băng, font Google chặn | **5/5 đạt, chạy 3 lần liền** (30,8 s · 30,9 s · 32,3 s); lần 4 sau ba sửa trình bày cuối: xem mục 6 |
| `core/tests/test_giao_dien.py` | Đỏ 1 bài (`kn_oms.html` dùng lớp không có trong CSS chung) trước `CSS_RIENG`; sau đó đạt hết, kể cả bài chú thích CSS chạy thêm trên `oms.css` |
| Bài canh: `test_khoi`, `test_ma_tran_quyen_hai_dich_vu`, `test_lien_ket_khong_cut`, `test_khung_crm`, `test_truy_vet` | Đạt hết. `test_truy_vet` khớp bộ đếm mới: 392 tiêu chí, 356 trên 379 |
| `manage.py check` (test, bangtinh); `makemigrations --check` | Không lỗi; "No changes detected" |
| Toàn bộ trừ trình duyệt: `pytest -m "not trinh_duyet" -rs` | **3.206 đạt, 7 bỏ qua, 0 đỏ** (mục 6) |

## 3. Vấn đề tìm ra khi kiểm, đã sửa

| # | Thấy gì | Sửa |
|---|---|---|
| 1 | Lãi theo page: 8/11 page lỗ ở kỳ 30 ngày, 5/11 ở kỳ 7 ngày. Tiền quảng cáo giả tính theo trọng số cố định, không theo doanh số | Quảng cáo mỗi page là một tỉ lệ doanh số của chính page đó ở từng kỳ (page Facebook 22–32 %, website 15–22 %, sàn 10–16 %). Kết quả: **đúng 2 page lỗ** (Japan, LazMall) ở cả hai kỳ; toàn bộ lãi, biên 23,2 % (30 ngày) và 18,4 % (7 ngày) |
| 2 | Bảng tràn trong khung cuộn. Công nợ tràn 98 px ngay ở 1366, nút "Ghi nhận" bị khuất; 179 px ở 1280. Báo đơn tràn 26–41 px ở 768–1024, Kho 80–95 px. Ở 390 px: Công nợ 206, Rủi ro 68, Lãi 39, Sổ kho 12 px | Công nợ gộp "Giao ngày" vào ô Trễ; "Đã thu" chỉ hiện khi rộng; trên điện thoại số ngày trễ và trạng thái thanh toán xuống dòng phụ. Báo đơn, Kho ẩn cột phụ khi khung dưới 860 px. Tiêu đề cột được xuống dòng trên điện thoại. **0 px ở 6 màn × 6 cỡ** (1920, 1366, 1280, 1024, 768, 390) |
| 3 | Chip tiền trong ô KPI Công nợ bẻ giữa số và loại tiền ("1.478,79 / CAD") | Chip không xuống dòng giữa chừng |
| 4 | "Cập nhật từ hãng" lần đầu: 43 đơn có tin mới nhưng 0 đơn giao xong, nên đường "giao xong → vào Công nợ" khó thấy khi demo. Đơn vừa "Đang phát" phải đợi lần hỏi sau | Hàng đã ra phát thì cùng một lần hỏi có thể nhận luôn kết quả (xác suất 0,5). Đồng hồ thật: lần đầu 6 đơn giao xong, 3 đơn vào Công nợ |
| 5 | Thác chi phí ghi "−0 ₫" khi khoản bằng 0; nhãn "1 USD =" ở bảng tỉ giá bẻ ba dòng; phần trăm âm dùng gạch nối "-" trong khi tiền dùng dấu trừ "−" | Khoản 0 ghi "0 ₫"; nhãn tỉ giá một dòng; phần trăm âm dùng "−" |

## 4. Hệ thống thật, đi thử bằng trình duyệt

Chromium 1366 × 768, ngôn ngữ vi-VN, đồng hồ thật. Không có lỗi JS ở bước nào.

| Vai | Thao tác | Kết quả |
|---|---|---|
| `quantri` | KN CRM, thanh bên | Có mục "KN OMS", `title` "Mở trong tab mới". Bấm → tab mới `/oms/` |
| `quantri` | Đi đủ sáu màn bằng thanh bên KN OMS | Mỗi màn đổi địa chỉ `#…`, vẽ đủ bảng |
| `quantri` | Báo đơn → "Cập nhật từ hãng" | "Đã hỏi hãng 84 đơn đang đi: 41 đơn có tin mới, 6 đơn vừa giao xong (3 đơn vào Công nợ), 1 đơn đứng lại vì kho thiếu hàng." Ô "Đã giao, chưa thu đủ" 32 → 35 |
| `quantri` | Khách rủi ro → chip "Khách hoàn 2 lần" | Thẻ Cao: "Đã nhận 1/3 đơn · Hoàn / không nhận 2 lần · Khách vắng 1 lần", nên làm "Yêu cầu chuyển khoản trước…, Cần Manager duyệt" |
| `quantri` | Công nợ → "Ghi nhận" ở dòng đầu | Hộp "Ghi nhận tiền · DH-…", ô số tiền theo đúng loại tiền của đơn |
| `quantri` | Lãi theo page, nền tối → bấm KN Beauty Japan | Thác chi phí 6 bước, quảng cáo 103,6 % doanh số, lãi âm |
| `sale.staff` | Gọi thẳng `/oms/` ở KN CRM | Trang 403 "Không có quyền truy cập"; nhật ký từ chối `/oms/` trong DB **0 → 1** |
| `sale.staff` | Trang chủ KN CRM | Không có liên kết `/oms/` |
| `quantri` | KN ERP `/oms/` | 404; trang ERP không có liên kết `/oms/` |
| `quantri` | Điện thoại 390 px: Công nợ, Lãi theo page | Không tràn ngang; thanh bên KN OMS thành khối trên đầu trang |

Ảnh chụp ở thư mục nháp của phiên (không đưa vào kho, theo CLAUDE.md), đã gửi chủ dự án trong phiên.

## 5. Kiểm thêm trên dữ liệu

- **Dữ liệu cố định:** đồng hồ trình duyệt đóng băng thì "Đặt lại demo" ra lại đúng từng chữ của bảng Báo đơn và ô Tồn
  trong kho (AC-51.5).
- **Móc dữ liệu của ba màn mới** (đồng hồ thật, 13.10):
  - Tiền về: 5 khoản, đủ bốn cách khớp — 2 khớp mã đơn, 1 khớp tên người gửi, 1 trả một phần, 1 phải chọn tay.
  - Tuổi nợ: 0–7 ngày 18 đơn · 8–14 ngày 8 · 15–30 ngày 4 · trên 30 ngày 2.
  - Tiền sàn: 4 dòng, tách theo sàn và loại tiền (PHP, USD).
- **Không gọi máy chủ:** trong cả bài AC-51.5, ngoài trang `/oms/` và tệp `/static/`, tab KN OMS không gửi request nào.
  Font Google bị chặn trong bài.
- **Lớp CSS:** mọi lớp mà `oms.js` gắn vào trang (133 lớp) đều có trong `oms.css`.

## 6. Lượt cuối

| Kiểm | Kết quả |
|---|---|
| Toàn bộ trừ trình duyệt, có Redis: `pytest -m "not trinh_duyet" -rs` | **3.206 đạt, 7 bỏ qua, 0 đỏ**, 12 phút 25 giây. Lượt 12.10 là 3.177; thêm 29 bài: 14 bài KN OMS, 8 bài giao diện tự sinh cho template mới và `oms.css`, 7 bài `test_khoi` tự sinh cho đường dẫn mới (6 vai và người chưa đăng nhập). 7 bài bỏ qua là bài kiểm tải như mọi lượt |
| `tests/e2e/test_kn_oms_e2e.py` lần 4, trên mã cuối | **5/5 đạt**, 32,7 s |

## 7. Chưa kiểm

- **Chặng 2:** chủ dự án thử ở máy mình.
  - Bật `KN JSC.bat`, đăng nhập `quantri` ở KN CRM `127.0.0.1:8021`.
  - Bấm "KN OMS" cuối thanh bên, đi sáu màn.
  - Thử "Cập nhật từ hãng", khớp tiền về, chip khách mẫu, đổi tỉ giá.
- **Trình duyệt khác:** chỉ thử Chromium; Safari và Firefox chưa thử.
- **Trình đọc màn hình:** có nhãn `aria`, Esc đóng ngăn kéo và hộp, phần sau bị `inert`, con trỏ trả về chỗ cũ. Chưa thử
  với trình đọc thật.
- **VPS:** chưa phát hành. Không có migration; phát hành chỉ cần `collectstatic` như mọi lần.
