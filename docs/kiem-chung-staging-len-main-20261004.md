# Biên bản kiểm chứng — Kiểm toàn diện `Staging` trước khi gộp `main` (04.10.2026)

| Mục | Nội dung |
|---|---|
| Yêu cầu | Chủ dự án 04.10: "test kĩ functional, unit, e2e, UI UX testing trước khi gộp vào main, làm liên tục không ngừng lại, auto approve" |
| Phạm vi | `Staging` `b17d25c` hơn `main` `7f8fb82` 9 PR, 90 tệp: #79 xem trước chỉ số (AC-43.6) · #77 rà KNGUARD · #78 AGENTS (Staging) · #80 tạo sản phẩm ở Lên đơn chỉ Leader+ (AC-6.9) · #81 ba chỗ sửa Báo cáo tổng hợp (AC-22.24–26) · #83 báo cáo MKT bằng tiền Việt, ẩn Lần nộp/Loại tiền, bảng vừa màn hình, phân trang (ADR-047, AC-47.x, 42.15–16) · #84 form MKT bỏ bốn ô, Sale bỏ Ngày ra đơn (ADR-048, AC-48.x) · #82 Delete xoá ô Sản phẩm, Bỏ dòng (AC-36.9–10) · #85 `du_lieu_mau` bỏ qua tài khoản đã xoá |
| Môi trường | Máy ảo Claude Code trên web: Python 3.11, PostgreSQL 16, Redis, Celery worker, Chromium Playwright 1194 |
| Kết luận | **Đạt.** Không thấy lỗi mới do 9 PR này. Bốn chỗ lỗi có sẵn từ trước trên `main` được ghi ở cuối, không chặn việc gộp |

## 1. Unit và functional

| Kiểm | Lệnh (từ `app/`) | Kết quả |
|---|---|---|
| Toàn bộ trừ trình duyệt, gồm cả bài chậm | `python -m pytest -m "not trinh_duyet"` | **2.917 đạt, 7 bỏ qua, 0 đỏ** (80 bài trình duyệt để lượt e2e), 7 phút 57 giây |
| CI trên đầu `Staging` `b17d25c` | GitHub Actions | "pytest (bộ chính)" và "pytest e2e (Chromium)" đều xanh |

## 2. Tệp chuyển đổi cấu trúc

Chỉ có một tệp mới: `reports/0006_bao_cao_mkt_tien_viet`. Kiểm trên database riêng `knjsc_mig`:

| Bước | Kết quả |
|---|---|
| `migrate` từ trống, rồi `tao_bang_van_don`, `du_lieu_mau`, `configure_erp_reports` | Chạy hết, không lỗi |
| Chạy ngược về `0005` | Dòng MKT có Thị trường "Hoa Kỳ" trả về USD; dòng không có Thị trường trả về trống, đúng với ý đồ của tệp |
| Chạy xuôi lại `0006` | Mọi dòng MKT về VND, số giữ nguyên |
| `makemigrations --check --dry-run` | "No changes detected" |

## 3. E2E

| Kiểm | Lệnh | Kết quả |
|---|---|---|
| Lượt 1 của CI | `python -m pytest tests/e2e -m trinh_duyet` | 46 đạt, 2 bỏ qua (cả 2 bỏ qua có chủ ý), 9 đỏ — xem dòng dưới |
| 9 bài đỏ `tests/e2e/test_pha_luoi_ghi_chu.py` | Như trên | Đỏ vì Chromium của máy ảo không tải được phông Google qua proxy (`ERR_CERT_AUTHORITY_INVALID`), bài coi đó là lỗi console. Chạy lại với phông Google trả rỗng (vá `conftest` tạm, **không commit**): **9/9 đạt**. Trên CI có mạng thật thì xanh |
| Lượt 2 của CI | `python -m pytest -m trinh_duyet --ignore=tests/e2e` | 14 đạt, 9 bỏ qua (giá đỡ cho script Node, đòi biến môi trường riêng) |
| Bài e2e của đợt này, chạy 3 lần | `reports/tests/test_bo_cuc_bao_cao_e2e.py`, `reports/tests/test_o_nhap_so_e2e.py`, `tests/e2e/test_xoa_chi_tiet_san_pham_e2e.py` | **21/21 đạt cả 3 lần**, không chập chờn |

## 4. Bật hệ thống thật, đi đúng đường nâng cấp

Docker trên máy ảo không dựng được image vì `apt-get` trong container không đi qua proxy. `Dockerfile`, `entrypoint.sh` và
requirements đều không đổi giữa `main` và `Staging`. Vì vậy hệ thống chạy thẳng trên máy ảo: ERP `runserver` 8020, CRM
`knjsc.settings.bangtinh` 8021, Celery worker, Redis, database `knjsc_ht`. Chuỗi lệnh giống launcher: `migrate`,
`tao_bang_van_don`, `du_lieu_mau`, `configure_erp_reports`, `configure_delivery_daily_report`.

Đi như máy của chủ dự án đang dùng:

1. Bật bản **`main`**. Nộp bằng giao diện 3 báo cáo MKT kiểu cũ (Hoa Kỳ → USD, Canada → CAD, Philippines → PHP) và 2 báo
   cáo Sale (USD, CAD). Xoá mềm `mkt.leader`.
2. Chạy lại `du_lieu_mau` trên `main`: dừng ở `BusinessError: Tài khoản đã xóa không thể sửa hoặc mở khóa.` Đây đúng là
   lỗi trên máy chủ dự án.
3. Nâng lên **`Staging`** và chạy lại chuỗi lệnh. `migrate` áp `0006`. `du_lieu_mau` in "Bo qua tai khoan mau da xoa
   (khong mo lai): mkt.leader" và chạy hết. Ba báo cáo MKT cũ thành VND, số giữ nguyên. Báo cáo Sale vẫn USD/CAD.
4. Nạp dữ liệu cỡ thật: `nap_bao_cao_mau --nguoi 20 --lan 3` tạo 2.040 báo cáo từ 01.09 tới 04.10 trong 29 giây;
   `nap_du_lieu_van_don` tạo 10.000 vận đơn trong 9 giây.

## 5. UI/UX — đóng vai người dùng bằng Playwright

Tài nguyên ngoài (phông Google) bị chặn có chủ ý, nên các lỗi console của chúng không tính. Mọi kịch bản dưới đây
**không có lỗi JS và không có trả lời 5xx**.

| Vai | Thao tác | Kết quả |
|---|---|---|
| `mkt.staff` | Mở form Nộp báo cáo | Không còn Sản phẩm, Thị trường, Tệp khách hàng, Loại tiền. CPQC và Doanh số ghi "(₫)". Team và Marketer do hệ thống tự ghi |
| `mkt.staff` | Bấm Nộp khi để trống | Không gửi đi; bốn ô bắt buộc báo thiếu |
| `mkt.staff` | Gõ 15000000, 45000000 | Ô tự hiện "15.000.000", "45.000.000". Xem trước chỉ số: CPO 1.250.000 VND, Giá Mess 50.000 VND |
| `mkt.staff` | Gõ chữ "abc" vào Số Mess | Ô không nhận chữ |
| `mkt.staff` | Nộp | Sang Lịch sử, báo "Đã nộp báo cáo cho ngày 04.10.2026" |
| `mkt.staff` | Điện thoại 390 px | Không tràn ngang; nút Nộp bấm trúng |
| `sale.staff`, `sale.leader` | Form Sale | Không còn Ngày ra đơn. Nộp "1.200" được 1200; Thị trường Úc ra AUD |
| `mkt.manager` | Báo cáo tổng hợp MKT ở 1366×768, 1920×1080, 390×844 | Không có tiêu đề trang, không có cột Lần nộp/Loại tiền; đầu bảng ghi "Tiền: ₫"; trang không cuộn; khung bảng 1366: 260→570 px, phân trang 589–617 px nằm trọn trong màn hình |
| `mkt.manager` | Bấm trang 2 | Điểm bấm trúng số "2"; sang "Hiện 101–200 trên 248 lần nộp" |
| `mkt.manager` | Gộp, rồi Không gộp | Đường dẫn đổi `gop=1` rồi bỏ; vẫn ở trang 2 |
| `mkt.manager` | Kéo ngang 613 px | STT và Nhân sự đứng yên; các cột khác trôi |
| `mkt.manager` | Cuộn bộ lọc | Bộ lọc cuộn riêng (717/495 px), trang không cuộn theo |
| `mkt.manager` | Xuất Excel | `bao-cao-tong-hop.xlsx`: dòng 2 ghi "Mọi số tiền là tiền Việt (₫), không quy đổi"; không có cột Lần nộp, Loại tiền; TỔNG CỘNG ghi "· VND" |
| `mkt.manager` | Sửa báo cáo cũ (#1, Hoa Kỳ) và mới (#2046) | Form sửa chỉ có bốn ô số; lưu được; Thị trường và Sản phẩm cũ giữ trong dữ liệu; CPO, AOV tự tính lại |
| `mkt.staff` | Mở thẳng trang sửa | Bị chặn (404) |
| `sale.manager` | Báo cáo tổng hợp Sale | Không đổi: còn Loại tiền, Lần nộp; TỔNG CỘNG tách USD/CAD |
| 6 vai | Mở Báo cáo tổng hợp, gõ thẳng `?nguon=` sang nguồn khác | `mkt.staff` → Sale, `sale.staff` → MKT, `vd.staff` → MKT: **403** "Bạn không có quyền truy cập". `mkt.staff` chỉ thấy số của mình |
| `vd.staff` | Lưới Vận đơn 10.000 dòng | Mở trong 0,6 giây. Delete ô Sản phẩm → hộp hỏi, con trỏ ở Huỷ. Enter thì không mất gì. "Bỏ chi tiết và xoá" → ô trống, báo "Đã bỏ chi tiết sản phẩm của 1 dòng". Ctrl+Z không trả lại, đúng như hộp đã báo |
| `vd.staff` | Mở Chi tiết đơn vừa bỏ | Có sẵn một dòng trống; chọn Retinol Serum ×2 rồi Lưu → ô "Retinol Serum ×2" |
| `vd.staff` | Đơn hai sản phẩm: Bỏ dòng ×2 rồi Lưu | Còn nút Thêm dòng; lưu được; ô Sản phẩm trống |
| `sale.staff` / `sale.leader` / `sale.manager` / `mkt.staff` | Lên đơn | Staff không có hộp "Tạo sản phẩm"; gửi thẳng thì **403**. Leader tạo được, sản phẩm có ngay trong danh sách; tạo trùng thì bị từ chối. Manager có hộp. MKT bị **403** ở Lên đơn |
| `sale.staff` | Lên đơn hai dòng | Lưu trống thì báo thiếu 5 ô; Hoa Kỳ tự ra USD; tóm tắt "2 dòng · 4 sản phẩm · Tổng 138.5 USD"; lưu `DH-0410-0001` đúng vào `van_don` |
| `mkt.manager`, `sale.manager` | Thống kê CRM | Nguồn MKT không còn biểu đồ theo sản phẩm; "Doanh số · VND" |
| `mkt.manager` | Bảng dữ liệu `/bang/bao_cao_mkt/` và `?dang=tho` | Chỉ đọc, phân trang 25 dòng; các ô nhập duy nhất trên trang thuộc form Ngưỡng màu |
| 6 vai × ERP, 6 vai × CRM | Bấm lần lượt mọi liên kết trong trang (tối đa 70 trang mỗi vai) | ERP không lỗi (riêng "tải tài liệu" mẫu chuyển ra Google Docs, máy ảo chặn). CRM: xem mục 6 |

## 6. Lỗi có sẵn trên `main`, không do đợt này

Các tệp liên quan không đổi giữa `main` và `Staging`, nên những lỗi này **không chặn việc gộp**. Đã gửi chủ dự án một
việc đề xuất để sửa riêng:

1. CRM, thanh bên: mục "Nhật ký" hiện cho mọi Manager, nhưng `vd.manager` và `mkt.manager` bấm vào thì bị 403.
2. CRM, `mkt.manager`: có liên kết tới `/thu-muc/` và `/danh-sach-bang/`, cả hai trả 404 (ADR-040: CRM chỉ phục vụ vận đơn).
3. ERP, `/bang/bao_cao_mkt/`: nút "Mở trong KN CRM" dẫn tới trang CRM 404 (ADR-040).
4. ERP, Lịch sử báo cáo: "Doanh số: 45000000,00" không có dấu chấm ngăn nghìn, không có đơn vị tiền.

**Đã sửa cùng ngày** (nhánh `claude/sua-lien-ket-cut`, AC-40.5 → 40.7, AC-4.11). Bài kiểm mới đỏ trên mã cũ, xanh sau
khi sửa. Quét lại 8 vai trên hệ thống thật: không còn liên kết 403/404 nào. Riêng tệp mẫu Excel là tải tệp, không
phải lỗi. Khi sửa còn tìm thêm hai chỗ cùng loại: nút ← của Lên đơn và nút "Quay lại" của đơn gốc dẫn Sale chưa có
đơn tới `/thu-muc/` 404.

Ghi chú UX, chưa coi là lỗi: ở Báo cáo tổng hợp, mở "Giải thích số liệu" hay "Ngưỡng màu" thì bảng bị đẩy xuống và
thanh phân trang ra khỏi màn hình. Lăn chuột thì thấy lại và bấm trúng.

## 7. Chưa kiểm được

- **Docker image**: máy ảo không dựng được vì proxy, nên chưa chạy đúng `KN JSC.bat` / `cap-nhat-local.sh`. Dockerfile,
  entrypoint và requirements không đổi trong đợt này.
- **Windows thật** và **VPS**: không tới được từ máy ảo. Đợt này không phát hành VPS.
- 7 bài bỏ qua ở lượt unit: chưa xem lý do từng bài.
- Celery beat: không bật. Hai tác vụ định kỳ không đổi trong đợt này.
