> Phần của [Kế hoạch kiểm thử toàn diện KNJSC](../08-ke-hoach-kiem-thu-toan-dien.md) — mục lục, lộ trình P0/P1/P2 và rủi ro còn lại nằm ở tệp đó.

## 8. Phân tích lọt lưới: các lỗi đã ghi nhận

### 8.1 Phạm vi và cách đếm

| Nhóm dữ liệu | Số mục | Ghi chú |
|---|---|---|
| Bảng cũ (TL-01 → TL-36) | 39 | Gồm 35 mã. Có 4 mục là "phần dư" tách khỏi mã gốc: TL-11-ERP, TL-31 (tài liệu), TL-33 (khoảng trống), TL-36 (phần còn lại) |
| Lỗi ghi theo ngày (TL-42 → TL-89) | 48 | Gồm 47 mã, vì TL-52 bị dùng hai lần (22.09 và 23.09). Dữ liệu không có TL-59 |
| **Tổng số mục đã phân tích** | **87** | Trạng thái hôm nay: 23 còn sống, 53 đã sửa, 11 hết (mã bị thay hoặc đóng mà không sửa mã) |
| Đợt săn lỗi 06.10.2026 (10 bước, **không mang mã TL**, không tính vào 87) | 23 lỗi ứng dụng + 2 lỗ hổng của bộ kiểm | Ghi ở `docs/backlog.md` (dòng 283–406) và 10 biên bản `docs/kiem-chung-san-loi-*-20261006.md`. `docs/test-log.md` không có mục nào ngày 06.10. Cả 23 lỗi đã sửa, mỗi lỗi có bài đỏ trên mã cũ. Phân tích riêng ở 8.3b. Số 23 là cách gom theo gốc của người tổng hợp |
| Biên bản "Dữ liệu đi từ A sang B" cùng ngày 06.10.2026 (**không mang mã TL**, không tính vào 87 và 23) | 11 lỗ hổng đã sửa + 3 ghi nhận chưa sửa + 3 điểm "Chưa kiểm" | `docs/kiem-chung-database-phan-quyen-20261006.md`, nhánh `claude/database-phan-quyen`, ghi ở `docs/backlog.md` (dòng 269–281). Biên bản ghi theo dạng "Trước / Sau", không đếm số lỗi. Số 11 là cách đếm của người tổng hợp, mỗi dòng "Trước" ở mục 1 và mục 2 tính là một. Phân tích ở 8.3b mục e |

Cách gán tầng ở 8.3: mỗi mục lấy tầng **nêu đầu tiên** trong `layer_should_catch` làm tầng chính. Đây là phân loại của người tổng hợp, không phải số liệu gốc.

### 8.2 Theo chặng phát hiện (found_by)

| Chặng | Bảng cũ | Ghi theo ngày | Tổng | Mã (ghi theo ngày) | Ghi chú |
|---|---|---|---|---|---|
| ra_ma (rà mã) | 39 | 7 | 46 | TL-50, 51, 54, 55, 56, 66, 75 | Dữ liệu ghi cả bảng cũ là ra_ma. Riêng mô tả TL-18, TL-19, TL-20 nói lỗi gốc đến từ ảnh/video chủ dự án gửi ngày 07.09. TL-54/55/56 là suy ra, chưa xác minh |
| nguoi_dung_vps (chủ dự án thử trên VPS) | 0 | 11 | 11 | TL-45, 46, 47, 49, 52 (22.09), 52 (23.09), 60, 61, 62, 65, 69 | Môi trường chưa xác minh với TL-45/46/47/49. TL-52 (cả hai bản), TL-61, TL-62 là suy ra |
| chu_du_an_local (Chặng 2, chủ dự án thử ở local) | 0 | 7 | 7 | TL-63, 64, 72, 73, 86, 87, 88 | Từ 28.09 đến 10.10. Môi trường chưa xác minh với TL-63/64/72 |
| dien_tap_vps (diễn tập phát hành VPS) | 0 | 7 | 7 | TL-79, 80, 81, 82, 83, 84, 85 | Cả 7 lỗi đến từ một lượt diễn tập ngày 08.10. TL-80 và TL-81 ở mức **cao** |
| kiem_staging (kiểm Staging) | 0 | 4 | 4 | TL-76, 77, 78, 89 | Ba lỗi ngày 08.10, một lỗi ngày 12.10 |
| ci | 0 | 4 | 4 | TL-53, 67, 70, 71 | TL-53 là pytest agent chạy ở local, không phải GitHub Actions. TL-67/70/71 là lỗi của chính bài kiểm hoặc hạ tầng kiểm thử |
| e2e | 0 | 2 | 2 | TL-57, 68 | TL-57: agent chụp Chromium. TL-68: bài e2e đã cũ, bị `--deselect` |
| khac (agent tự chạy tay, nguồn không rõ) | 0 | 6 | 6 | TL-42, 43, 44, 48, 58, 74 | TL-42/43/44: lượt pytest đầy đủ ngày 18.09, lúc chưa có CI. TL-58: chưa xác minh ai phát hiện |
| **Tổng** | **39** | **48** | **87** | | |

Ngoài bảng trên còn hai chặng không mang mã TL:
- **Săn lỗi có chủ đích** (agent chạy trên máy ảo ngày 06.10, chủ dự án duyệt 10 bước). Chặng này bắt 23 lỗi ứng dụng, trong đó 6 lỗi mức nghiêm trọng. Chi tiết ở 8.3b.
- **Rà dữ liệu và phân quyền theo yêu cầu chủ dự án** (cùng ngày 06.10, trên máy ảo, DB thử 10.033 vận đơn và 2.291 báo cáo MKT). Chặng này lấp 11 lỗ hổng về dữ liệu đi từ A sang B và đổi URL mất quyền, còn để lại 3 điểm chưa kiểm. Chi tiết ở 8.3b mục e.

### 8.3 Theo tầng lẽ ra phải bắt (layer_should_catch)

| Tầng chính | Bảng cũ | Ghi theo ngày | Tổng | Còn sống | Mã |
|---|---|---|---|---|---|
| Tích hợp / chức năng HTTP và dịch vụ (tầng 4) | 9 | 7 | **16** | 5 | TL-04, 07, **09**, **10**, **13**, 17, **18**, **25**, 35; 47, 54, 56, 57, 64, 76, 79 |
| E2E trình duyệt (tầng 8) | 7 | 9 | **16** | 1 | TL-02, 06, 08, 14, 19, 20, **36-dư**; 49, 62, 63, 69, 73, 74, 75, 77, 86 |
| Rà đặc tả / ADR / thiết kế (không có tầng tự động nào) | 1 | 12 | **13** | 1 | **TL-30**; 44, 45, 50, 52 (22.09), 53, 60, 61, 65, 72, 87, 88, 89 |
| Phân quyền hai chiều / ma trận quyền (tầng 5) | 5 | 2 | 7 | 2 | **TL-01**, 05, 11, **11-ERP**, 15; 55, 78 |
| Hiệu năng (tầng 9) | 4 | 3 | 7 | 4 | **TL-12**, **27**, 33, **33-dư**; 43, 48, **83** |
| Đơn vị / hộp trắng (tầng 6) | 3 | 3 | 6 | 2 | **TL-03**, **32**, 36; 52 (23.09), 58, 66 |
| Đồng thời / tác vụ nền | 5 | 0 | 5 | 2 | TL-16, 22, **23**, 24, **26** |
| Quy trình phát hành / cấu hình triển khai | 0 | 5 | 5 | 2 | 80, 81, **82**, 84, **85** |
| Hạ tầng kiểm thử / quy ước viết bài | 0 | 5 | 5 | 1 | 42, 67, 68, 70, **71** |
| Truy vết / rà tài liệu | 3 | 1 | 4 | 2 | **TL-28**, 31, **31-tài liệu**; 51 |
| Kiểm tay Chặng 2 / khói sau khởi động | 2 | 0 | 2 | 1 | TL-21, **29** |
| Giao diện tĩnh (tầng 7) | 0 | 1 | 1 | 0 | 46 |
| **Tổng** | **39** | **48** | **87** | **23** | (mã in đậm là lỗi còn sống) |

Đối chiếu tầng với chặng phát hiện, chỉ tính 48 lỗi ghi theo ngày:

| Chặng | Rà đặc tả/ADR | E2E | Tích hợp | Phát hành/cấu hình | Khác |
|---|---|---|---|---|---|
| Người dùng (VPS + local, 18 lỗi) | 8 (TL-45, 52, 60, 61, 65, 72, 87, 88) | 6 (TL-49, 62, 63, 69, 73, 86) | 2 (TL-47, 64) | 0 | 2 (TL-46 giao diện, TL-52 bản 23.09 đơn vị) |
| Diễn tập VPS (7 lỗi) | 0 | 0 | 1 (TL-79) | 5 (TL-80, 81, 82, 84, 85) | 1 (TL-83 hiệu năng) |
| Kiểm Staging (4 lỗi) | 1 (TL-89) | 1 (TL-77) | 1 (TL-76) | 0 | 1 (TL-78 phân quyền) |

### 8.3b Đợt săn lỗi 06.10.2026: lỗi không mang mã TL

Đợt chạy trên máy ảo, với hệ thống thật (ERP 8020, CRM 8021, Celery, Redis, PostgreSQL 16) trên dữ liệu lượt 04.10 (khoảng 10.000 vận đơn, 2.040 báo cáo). Nhánh `claude/san-loi-dong-thoi`, `claude/san-loi-bao-mat`, `claude/san-loi-tiep`. Không thêm thư viện: chỉ dùng `requests`, Playwright, pytest. `docs/06-ke-hoach-kiem-thu.md` không nhắc tới fuzz, đột biến, diễn tập sự cố hay đối soát. Grep các từ đó trong tệp ra 0 kết quả, nghĩa là những kỹ thuật này không thuộc tầng nào trong chín tầng.

**a) Lỗi bắt được theo từng bước**

| Bước | Biên bản | Kỹ thuật | Lỗi bắt được (mức theo biên bản) | Số lỗi | Bài khoá (đỏ trên mã cũ) | AC | Còn chưa kiểm |
|---|---|---|---|---|---|---|---|
| 1 Đồng thời | `kiem-chung-san-loi-dong-thoi-20261006.md` | 20 luồng chờ chung một hiệu lệnh; Playwright `dblclick` | Gửi lặp một lần nộp → 3 báo cáo (doanh số cộng gấp ba); gửi lặp Lưu đơn → 2 đơn (**nghiêm trọng**) | 2 | `reports/tests/test_nop_mot_lan.py`, `crm/tests/test_len_don_mot_lan.py` (có bài hai luồng, hai kết nối DB) | AC-4.12, AC-6.11 | Chưa có lệnh dọn bảng `SubmissionReceipt` (đã ghi backlog) |
| 2 Bảo mật | `…-bao-mat-…` | Tệp Excel độc, bom nén, `pip-audit`, IDOR qua 28 mẫu URL, `check --deploy` | Ô `=HYPERLINK(…)` xuất ra thành công thức chạy được (**nghiêm trọng**); tệp .xlsx 220 KB ngốn 1,85 GB RAM (**nghiêm trọng**); Django 5.2.6 có 62 lỗ hổng, python-dotenv 1 lỗ hổng (đã nâng lên 5.2.17 và 1.2.2) | 3 | `forms_builder/tests/test_xuat_khong_cong_thuc.py`, `forms_builder/tests/test_nhap_tep_bom.py` | AC-7.14, AC-7.15 | nginx chưa có `server_tokens off` và CSP (grep `deploy/` không thấy `server_tokens`); chưa quét web tự động (ZAP, phải hỏi trước) |
| 3 Đường truyền | `…-duong-truyen-…` | Playwright `set_offline`, CDP giả lập 3G | Lưới báo "Failed to fetch"; Lên đơn lúc mất mạng không báo gì; HTMX gửi hỏng thì im lặng ở mọi trang (**vừa**) | 3 | `tests/e2e/test_mat_mang_e2e.py` | AC-10.12 | Nhập tệp lớn trên mạng chậm (timeout nginx VPS); Safari, Firefox |
| 4 Gõ tiếng Việt | `…-go-tieng-viet-…` | Giả lập sự kiện IME; gửi dữ liệu dạng NFD | Chữ dạng tổ hợp (Mac) lưu nguyên, máy Windows tìm ra 0 kết quả (**nghiêm trọng**) | 1 | `crm/tests/test_chu_viet_mot_dang.py` | AC-9.6 | Unikey, EVKey, Telex macOS thật; chưa đếm dữ liệu cũ trên VPS (biên bản có câu SQL chỉ đọc) |
| 5 Giờ, tiền, số | `…-gio-tien-so-…` | `requests` gửi thẳng form; đồng hồ máy chủ để giờ quốc tế | `NaN`, `Infinity`, `1e400`, số 24 chữ số → 500 (**vừa**); chip "Hôm nay" lệch ngày từ 0 đến 7 giờ sáng (**vừa**); tên tệp xuất lệch 7 giờ (**nhẹ**) | 3 | `core/tests/test_so_va_gio_bien.py` | AC-9.7, AC-9.8 | Máy người dùng đặt múi giờ khác; doanh số âm chờ chủ dự án chốt |
| 6 Sự cố, chạy dài | `…-su-co-…` | Tắt Redis; ổ tmpfs 1 MB đầy; restart Postgres dưới gunicorn cấu hình như VPS; chạy dài 110 phút | Tắt Redis: xuất treo 19,2 giây rồi 500, tác vụ kẹt mãi (**vừa**); đĩa đầy → 500 (**vừa**); thiếu `500.html`/`404.html`, trái NFR-6; restart Postgres: 8/16 yêu cầu lỗi 500 dù DB đã chạy lại (**vừa**). Chạy dài: 33.196 yêu cầu, 0 lỗi 5xx, RAM worker phẳng 99–100 MB | 4 | `crm/tests/test_hang_doi_chet.py`, `core/tests/test_trang_loi.py`, `core/tests/test_ket_noi_db.py` | AC-10.13 → AC-10.15 | Đầy ổ của chính Postgres; mất điện giữa lúc ghi; chạy nhiều ngày; VPS 4 GB thật |
| 7 Đột biến tay | `…-dot-bien-…` | 17 đột biến, mỗi lần hỏng một dòng (M1–M17, cộng M10b) | Không có lỗi ứng dụng. Có 2 lỗ hổng của bộ kiểm: **M10b** (đọc `1.234` thành 1,234 mà `core` và `forms_builder` vẫn xanh) và **M16** (bỏ dòng chặn CEO trong `grant_service.can_edit_visible_record` mà không bài nào đỏ) | 0 (+2 lỗ bài) | `core/tests/test_so_va_gio_bien.py::test_o_so_van_doc_dung_cach_viet_viet_nam`, `crm/tests/test_ceo_chi_doc_luoi.py::test_ceo_xem_duoc_nhung_khong_sua_duoc_o_luoi` | AC-21.17 | Đột biến JS lưới (`master-grid.js`); đột biến tự động (mutmut, cosmic-ray: thêm thư viện, phải hỏi) |
| 8 Đối soát | `…-doi-soat-…` | So một con số ở 6 nơi với DB tính qua `in_scope` | Mọi con số khớp. Thống kê CRM viết `48311822000`, không nhóm nghìn như ERP (**nhẹ**) | 1 | `crm/tests/test_thong_ke_cach_viet_so.py` | AC-22.27 | Excel ghi tỉ lệ chốt bằng số thực đủ chữ số (chờ chốt); chưa đối soát nhiều loại tiền ở Sale (mới có 3 lần nộp) |
| 9 Đăng nhập, nhật ký | `…-dang-nhap-nhat-ky-…` | 40 yêu cầu song song; quét log ứng dụng, nginx, AuditLog | 40 lần sai gửi cùng lúc đều được thử mật khẩu (**nghiêm trọng**). Log sạch | 1 | `org/tests/test_do_mat_khau.py` (bài 20 luồng thật) | AC-1.9 | Dò rải nhiều tài khoản theo IP; lời "đang bị khoá tạm" để lộ tài khoản có thật; chuỗi gõ nhầm vào `actor_label`; traceback 403 làm phình log (đều chờ chốt) |
| 10 Fuzz | `…-fuzz-…` | Bắn 12 kiểu dữ liệu lạ vào mọi GET/POST tìm thấy; 14 dạng JSON hỏng cho lưới | Lượt 1: 139 lỗi 500 ở ERP; lượt 2: 178 lỗi 500 ở CRM. Năm gốc: NUL lọt vào truy vấn; bộ lọc cột sai kiểu gây `ValidationError`; NUL trong JSON lưới; chuỗi dài hơn cột; `get_object_or_404` nhận mã chữ. Thêm: ô ghi chú nhận 200.000 ký tự, vượt trần 32.767 của Excel. Lượt 3 sau khi sửa: 0 lỗi 500 trên 30.475 yêu cầu | 5 | `core/tests/test_ky_tu_nul.py`, `crm/tests/test_o_chu_bien.py`, `forms_builder/tests/test_loc_sai_kieu.py` | AC-10.16, AC-21.16 | Fuzz nội dung tệp tải lên; fuzz theo độ phủ (hypothesis, atheris: thêm thư viện, phải hỏi) |
| **Tổng** | | | 6 nghiêm trọng, 8 vừa, 2 nhẹ, 7 không gắn mức | **23** | Đã kiểm sự có mặt của 16 tệp bài trên bằng `ls` | | |

**b) Kết quả đột biến tay (bước 7)**

| Nhóm | Đột biến | Ý nghĩa |
|---|---|---|
| Bài có sẵn bắt được | M1, M2, M3, M4, M7, M8, M9, M11, M12, M13, M15, M17 (12/17) | Các quy tắc nền (phạm vi quyền, CAS, xoá mềm, nhật ký, khoá đăng nhập, phiên, không cộng lẫn tiền) đã có bài canh |
| Chỉ bài mới của đợt bắt được | M5, M6, M10, M14 (4/17) | Trước đợt, các quy tắc này không có bài canh |
| Lọt | M10b (quy tắc `parse_money`), M16 (CEO sửa lưới khi hồ sơ gắn vào bộ phận Vận đơn) | Đã lấp. M16 chạy lại thì bị bắt |

Đột biến tay **đã chạy rồi**, không phải việc mới. Đề xuất đột biến ở phần khác của kế hoạch chỉ nên nhắm tới phần chưa làm: JS lưới và đột biến tự động (phải hỏi thư viện theo quy tắc 8).

**c) Bài học lọt lưới rút từ đợt này**

| Quan sát | Bằng chứng | Hệ quả cho kế hoạch |
|---|---|---|
| Cả 23 lỗi đều tồn tại lúc CI xanh | Mọi bài khoá đều đỏ trên mã cũ (theo từng biên bản) | Có năm loại lỗi mà lưới tự động trước đó không nhìn thấy: đồng thời thật với nhiều kết nối, sự cố hạ tầng, đầu vào lạ, đối soát chéo màn hình, môi trường người dùng (mạng, bộ gõ, múi giờ) |
| Bản sửa ở cửa vào gây lỗi mới mà CI không bắt | Bản sửa bước 4 (`UnicodeNFCMiddleware`) sinh ra **TL-79**: mọi lần sửa ô cũ dạng NFD đều bị 409. Diễn tập 08.10 bắt được, nay có bài `crm/tests/test_chu_viet_mot_dang.py::test_o_cu_dang_to_hop_van_sua_duoc_tren_luoi` | Sửa middleware hay chuẩn hoá dữ liệu thì phải kiểm thêm trên **dữ liệu cũ đã lưu**, không chỉ dữ liệu mới |
| Bản sửa bước 1 và 6 được diễn tập xác nhận lại | `kiem-chung-dien-tap-phat-hanh-staging-20261008.md` mục 6: `stop broker` báo lỗi sau 0,69 giây; `restart db` 20/20 đạt; nộp MKT bấm đúp ra đúng 1 bản ghi | Nên giữ các bước diễn tập sự cố này trong mỗi lượt phát hành |
| Bước 5 khoá chặt thêm luật "dấu chấm theo sau ba chữ số là ngăn nghìn" | `test_o_so_van_doc_dung_cach_viet_viet_nam` có ca `1.234`, `-5.000` | Đây cũng là gốc của **TL-03** (còn sống, xem 8.5). Sửa TL-03 sẽ đụng bài này |

**d) Kịch bản kiểm ngoài máy ảo (`docs/kich-ban-kiem-ngoai-may-ao-20261006.md`): trạng thái**

| Mục | Nội dung | Trạng thái |
|---|---|---|
| 1 | Chạy migration của nhánh (`core/0007_submission_receipt`) xuôi, ngược, rồi xuôi lại trên bản sao dữ liệu VPS | Chưa xác minh. Biên bản phát hành VPS mới nhất trong `docs/` là ngày 29.09. Nên gộp thêm `forms_builder/0017` (ràng buộc mã đơn, xem mục e) vào lượt này |
| 2 | Diễn tập sự cố trên VPS: restart db, stop/start broker, stop cache | Đã chạy trên **máy ảo giống VPS** ngày 08.10 (biên bản diễn tập mục 6). Trên VPS thật: chưa xác minh |
| 3 | Trang 404 tiếng Việt; `df -h` cho volume `storage` và `postgres`; `OPERATOR_EMAILS` | Diễn tập 08.10 đã thấy trang 404 tiếng Việt ở cả hai host, và có `df -h` trong checklist. Trên VPS thật và `OPERATOR_EMAILS`: chưa xác minh |
| 4 | Gom p95 thật bằng `scripts/gom-p95-vps.py --since 24h`, so với lượt trước phát hành | Chưa xác minh |
| 5 | Khôi phục bản sao lưu đêm, đo RTO và RPO | Chưa xác minh |
| 6 | Trình duyệt và bộ gõ thật (Unikey, EVKey, Telex macOS, Safari, Firefox, 4G yếu) | Chưa xác minh |
| 7 | Bốn điểm chờ chủ dự án chốt: doanh số âm; lộ tài khoản qua lời khoá tạm, `actor_label`, chặn theo IP; `server_tokens off` và CSP; tỉ lệ trong Excel | Chưa thấy quyết định trong `docs/` (chưa xác minh hết). `server_tokens` vẫn chưa có trong `deploy/` |

**e) Biên bản cùng ngày: dữ liệu đi từ A sang B, đổi URL mất quyền (`docs/kiem-chung-database-phan-quyen-20261006.md`)**

Biên bản này không thuộc 10 bước săn lỗi. Chủ dự án yêu cầu tập trung vào cơ sở dữ liệu, dữ liệu đi từ hệ thống cũ sang DB mới, nâng cấp phiên bản, ERP ↔ CRM, và lỗi "vào URL khác là mất quyền". Nhánh `claude/database-phan-quyen` từ `Staging` `b19b109`. Môi trường: máy ảo, Postgres 16, ERP 8020 / CRM 8021 chạy `runserver`, DB thử 10.033 vận đơn + 2.291 báo cáo MKT. AC: AC-1.10 → 1.12, AC-6.12, AC-7.16, AC-8.11, AC-36.11 → 36.14 (đã thấy cả 10 mã trong `docs/04-tieu-chi-nghiem-thu.md`).

*Lỗ hổng đã lấp (mục 1 và 2 của biên bản)*

| Nhóm | Trước khi sửa | Sau khi sửa | Bài khoá (đỏ trên mã cũ; đã kiểm có mặt bằng `ls`) | AC |
|---|---|---|---|---|
| Đổi URL | Mở ERP bằng `127.0.0.1:8020` rồi bấm KN CRM thì sang `localhost:8021`, mất cookie phiên, phải đăng nhập lại | Liên kết giữ host đang mở, chỉ đổi cổng, cả hai chiều | `core/tests/test_lien_ket_dich_vu.py` | AC-1.10 |
| Cấu hình VPS | ERP, CRM ở hai tên miền mà chưa đặt `SESSION_COOKIE_DOMAIN`/`CSRF_COOKIE_DOMAIN` thì không ai báo. CRM thiếu `BANGTINH_GOC=prod` thì chạy cấu hình dev | `check --deploy` dừng với `core.E001`. CRM ở tên miền thật mà thiếu biến thì dừng khởi động | `core/tests/test_kiem_cau_hinh.py` | AC-1.11 |
| Cùng URL ở hai dịch vụ | Chưa có bài nào khoá | Dò mọi đường dẫn **GET** × 8 vai × 2 dịch vụ (105 dòng). Khác biệt đều có chủ ý (ADR-015, ADR-045) | `core/tests/test_ma_tran_quyen_hai_dich_vu.py` | AC-1.12 |
| Mã đơn trùng | Chỉ bước kiểm tệp nhập so mã. Lưới, Lên đơn, khôi phục dòng, hai lượt nhập cùng lúc đều để lọt hai dòng cùng mã | Cột `val_order_code` + ràng buộc duy nhất một phần `record_ma_don_unique`. Lên đơn nhảy qua mã đã có (4,0 ms/lần) | `crm/tests/test_ma_don_khong_trung.py` | AC-36.11 |
| Migration trên dữ liệu bẩn | — | `forms_builder/0017` gặp mã trùng thì dừng, liệt kê mã, quay lui cả migration | Tệp bài cụ thể chưa xác minh | AC-36.12 |
| Xoá dòng vận đơn | Đơn gốc còn sống, thành mồ côi | Bỏ luôn đơn (xoá mềm, nhật ký); khôi phục dòng thì khôi phục đơn | `orders/tests/test_xoa_dong_huy_don.py` | AC-6.12 |
| Đổi kiểu cột | Giá trị cũ nằm nguyên: "1.500" trong cột Số nguyên, "abc" trong cột số | Thử chuyển mọi giá trị, kể cả dòng đã xoá. Hỏng thì từ chối, nêu số dòng và ví dụ | `forms_builder/tests/test_doi_kieu_cot.py` | AC-8.11 |
| Lệnh nâng cấp cấu trúc | `tao_bang_van_don`, `configure_erp_reports` sửa cột thẳng trong DB, không tính lại dòng cũ. Bằng chứng: 5 dòng MKT mẫu lệch `cpqc_doanh_so`, `aov`, `cpo`, `gia_mess` | Chụp cấu trúc trước và sau; đổi thì `schedule_resync` | `orders/tests/test_nang_cap_tinh_lai.py` | AC-36.13 |
| Không biết dữ liệu lệch | — | Lệnh chỉ đọc `kiem_tra_du_lieu` (`--sua` để tính lại). DB thử: 4,5 giây cho 12.327 dòng | `orders/tests/test_kiem_tra_du_lieu.py` | AC-36.14 |
| Ô ngày dạng số trong Excel | Ô 45000 làm cả dòng bị từ chối | Đổi thành 15/03/2023; chữ "45000" vẫn bị từ chối | `forms_builder/tests/test_ngay_so_excel.py` | AC-7.16 |
| `resync_table` | So lệch không gồm khoá số điện thoại | So đủ mọi cột tách (`DERIVED_FIELDS`) | Tệp bài cụ thể chưa xác minh | — |

Ràng buộc mới làm đỏ 12 bài cũ có helper tự sinh mã đơn trùng. Biên bản ghi: đã sửa helper, không nới ràng buộc.

*Ghi nhận chưa sửa và điểm "Chưa kiểm"*

| Mục | Nội dung theo biên bản | Trạng thái hôm nay | Ca kiểm đề xuất | Góc nhìn | Loại | Hình thức | Ưu tiên |
|---|---|---|---|---|---|---|---|
| Chưa kiểm 1 | Chạy `manage.py kiem_tra_du_lieu --bang van_don` trên VPS **trước** khi phát hành. Còn mã trùng thì migration `0017` sẽ dừng, phải dọn trước | Chưa xác minh đã chạy. Lệnh có trong `deploy/production/README.md` (dòng 102, 116). Biên bản phát hành VPS mới nhất là 29.09, trước ngày có `0017` (suy ra: `0017` chưa lên VPS). Nguy cơ chồng: **TL-83** (còn sống) cho thấy lệnh này bị diệt vì hết RAM ở 100.000 dòng trong container crm 640 MiB | Đưa lệnh vào dãy phát hành, chạy trên bản sao dữ liệu VPS trước, ghi thời gian, đỉnh RAM, mã thoát vào biên bản phát hành. Phải sửa TL-83 trước hoặc chạy với giới hạn bộ nhớ cao hơn (chưa xác minh cách nào được chọn) | QA | Di trú dữ liệu / phát hành | Thủ công | P0 |
| Chưa kiểm 2 | Tên miền cha thật cho `SESSION_COOKIE_DOMAIN`/`CSRF_COOKIE_DOMAIN` trong `.env` VPS. Chủ dự án đặt, không ghi vào kho | Chưa xác minh. `core.E001` chỉ bắt trường hợp **thiếu** biến; giá trị đặt sai (không phải tên miền cha chung) có bài hay không: chưa xác minh | Sau phát hành, đi ERP → CRM → ERP trên tên miền thật với một tài khoản mỗi vai, phải còn đăng nhập; chạy `check --deploy` trên VPS | Người dùng + QA | Khói sau phát hành | Thủ công | P1 |
| Chưa kiểm 3 | Đổi kiểu cột trên bảng 100.000 dòng: chuyển trong cùng request web, chưa đo thời gian | Chưa đo. Ngưỡng timeout gunicorn/nginx trên VPS: chưa xác minh | Bài dấu `cham` trên DB `seed_perf` 100.000 dòng: bấm giờ POST đổi kiểu cột (đường AC-8.11), so với timeout của VPS. Vượt ngưỡng thì phải chuyển sang tác vụ nền | QA | Hiệu năng | Bán tự động | P1 |
| Ghi nhận 1 | `/bang-da-xoa/` của CRM trả danh sách rỗng cho Staff thay vì 403 (trái quy tắc "ngoài phạm vi phải từ chối"). Biên bản: ảnh hưởng thấp | **Còn**. `app/crm/lifecycle_views.py` `deleted` (dòng 12-14) chỉ lọc `service.manageable(request.user)`, không gọi `PermissionDenied`. Cũng ghi "Còn nợ" ở `docs/backlog.md` dòng 279 | Staff của từng bộ phận GET `/bang-da-xoa/` ở 8021 → 403, có nhật ký từ chối. Bài ma trận AC-1.12 có đang khoá hành vi trả rỗng hay không: chưa xác minh (grep `bang-da-xoa` trong `test_ma_tran_quyen_hai_dich_vu.py` không thấy) | QA | Phân quyền hai chiều | Tự động | P2 |
| Ghi nhận 2 | `/van-don/thong-ke/` trả 403 cho Sale, trong khi `/thong-ke/` mở cho mọi vai | Hai route vẫn còn (`app/crm/urls.py` dòng 30, 40). Hành vi hôm nay và ý đồ: chưa xác minh | Chủ dự án chốt ý đồ, rồi khoá bằng một dòng trong ma trận AC-1.12 | QA | Phân quyền / rà đặc tả | Thủ công rồi Tự động | P2 |
| Ghi nhận 3 | `sl_*` lệch Chi tiết sản phẩm ở 9.999 dòng (nhãn BIẾT, không tính vào mã thoát) | Còn nợ (`docs/backlog.md` dòng 279) | Chờ chủ dự án quyết có cần đồng bộ không | QA | Toàn vẹn dữ liệu | Thủ công | P2 |

*Bài học lọt lưới từ biên bản này*

| Quan sát | Bằng chứng | Hệ quả cho kế hoạch |
|---|---|---|
| Bản sửa ngày 06.10 lại sinh lỗi mới, lần này ở tầng hạ tầng | Ràng buộc `record_ma_don_unique` ra đời ở biên bản này. Diễn tập 08.10 bắt **TL-82**: log Postgres ghi nguyên câu UPDATE kèm dữ liệu khách khi vi phạm đúng ràng buộc đó | Cùng kiểu với TL-79. Mỗi ràng buộc DB mới phải kiểm cả "khi vi phạm thì cái gì được ghi ra log" |
| Bản sửa cấu hình chỉ chặn trường hợp thiếu biến | AC-1.11 chặn `BANGTINH_GOC` thiếu ở tên miền thật. **TL-85** (còn sống) là trường hợp gõ sai giá trị, vẫn lặng lẽ chạy dev | Bài cấu hình nên thử cả giá trị thiếu, sai chính tả và rỗng |
| Ma trận URL mới khoá GET | 105 dòng chỉ là GET. Hai URL POST `cap-quyen`/`thu-quyen` vẫn nằm trong `CHUNG_KHONG_GET`, đó là chỗ **TL-01** (S1, còn sống) lọt | Mở rộng ma trận sang POST, xem bài đề xuất của TL-01 ở 8.5 |
| Lệnh kiểm dữ liệu chỉ mới đo trên DB thử 12.327 dòng | Biên bản: 4,5 giây. Diễn tập 08.10: lệnh hết RAM ở 100.000 dòng (TL-83) | Công cụ dùng trong phát hành cũng phải qua kiểm hiệu năng ở cỡ dữ liệu VPS |

### 8.4 Bảng cũ TL-01 → TL-41: trạng thái trong mã hôm nay

| Trạng thái | Số mã | Mã |
|---|---|---|
| Còn sống trong mã | 15 mã (thêm 4 phần dư tách riêng, tổng 19 mục) | TL-01, 03, 09, 10, 12, 13, 18, 23, 25, 26, 27, 28, 29, 30, 32 · phần dư: TL-11-ERP, TL-31 (tài liệu), TL-33 (khoảng trống), TL-36 (phần còn lại) |
| Hết vì mã bị thay (lưới master-grid, ADR-021/027/040/049) | 10 | TL-05, 06, 08, 14, 19, 20, 21, 22, 24, 31 |
| Đã sửa | 10 | TL-02, 04, 07, 11, 15, 16, 17, 33, 35, 36 |
| Không rõ (nằm ngoài dữ liệu phân tích) | 6 | **TL-34**: test-log dòng 1222 ghi "Đã sửa ở PR21, chưa gộp"; PR21 nay đã vào main (theo bằng chứng của TL-26), nhưng chưa kiểm chứng trên mã. **TL-41**: test-log dòng 826 ghi đã sửa ở `5b68dce`, chưa kiểm chứng. **TL-37, 38, 39, 40**: grep `docs/test-log.md` không thấy, chưa xác minh chúng có được dùng hay không |

### 8.5 Danh sách đầy đủ lỗi còn sống, bằng chứng và bài hồi quy đề xuất

**a) Bảng cũ (19 mục)**

| Mã | Mức | Lỗi | Bằng chứng chính | Bài hồi quy đề xuất | Góc nhìn | Loại | Hình thức | Ưu tiên |
|---|---|---|---|---|---|---|---|---|
| TL-01 | S1 | Manager bộ phận khác chỉ cần thấy bảng (nhờ Grant Xem, nhờ là Kế toán với van_don, hoặc là Sale có dòng vận đơn) là POST thẳng được để tự cấp quyền Sửa và thu quyền do bộ phận chủ cấp | `app/forms_builder/views.py` `bang_cap_quyen` (486-507) và `bang_thu_quyen` (510-520) không gọi `_kiem_sua_cau_truc`/`can_manage_columns`. `grant_service.grant()` (278) và `revoke()` (301) không kiểm bộ phận. Đường vào: `forms_builder/urls.py` 35-36 và `knjsc/urls_bangtinh.py` 50-51 | Parametrize theo vai × cổng 8020/8021: Manager MKT có Grant Xem bảng Sale, Manager Kế toán với van_don, Manager Sale có dòng vận đơn. Gửi POST `/bang/<mã>/cap-quyen/` (user=chính mình, action=edit) và `thu-quyen/<pk>/`. Kỳ vọng 403, có nhật ký từ chối, số Grant không đổi. Đưa hai URL này ra khỏi `CHUNG_KHONG_GET` trong `app/core/tests/test_ma_tran_quyen_hai_dich_vu.py` | QA | Phân quyền hai chiều (HTTP) | Tự động | P0 |
| TL-03 | S1 | `parse_money('0.125')` ra 125. Dán, hoàn tác hay sửa trên chuỗi máy ở cột MONEY/DECIMAL làm giá trị nhân nghìn lần mà không báo gì | `app/core/money.py` `parse_money` (86-90). `record_service.parse_value` (106-114) → `_dat_o` (358-392). `master-grid.js` gửi `cell.value` thô (524, 715) | Đơn vị khứ hồi: với mọi Decimal d (kể cả từ 3 chữ số lẻ), `parse_value(str(d)) == d`. Tích hợp: POST `luu-json` với '0.125' (paste/undo) giữ nguyên giá trị. E2e: copy-dán và Ctrl+Z trên cột thập phân. **Cần chốt luật trước**, vì có hai bài đang khoá '1.234' → 1234: `app/tests/test_hop_trang.py::test_doc_lai_duoc_so_tien_nguoi_dung_go` và `app/core/tests/test_so_va_gio_bien.py::test_o_so_van_doc_dung_cach_viet_viet_nam` (bài lấp lỗ M10b của đợt săn lỗi 06.10, có ca `1.234`, `-5.000`). Cách chữa có thể là tách chuỗi máy khỏi chuỗi người gõ, chứ không đổi luật đọc chữ người gõ (chưa xác minh) | QA + Người dùng | Đơn vị + tích hợp + e2e | Tự động | P0 |
| TL-09 | S3 | Bảng dữ liệu ERP (bảng ngoài vận đơn) sắp theo một cột mà không có khoá phụ, nên lật trang bị lặp hoặc thiếu dòng | `forms_builder/query.py` `apply_sort` (225-233); `build` (248-252) chỉ thêm 'pk' khi `is_waybill_table` | Trong `app/forms_builder/tests/test_man_hinh_bang.py`: tạo hơn 25 dòng cùng giá trị cột sắp, GET `?sap=<cột>&trang=1` và `trang=2`, kiểm hai trang hợp lại đủ mọi pk và không trùng. Thêm bài đơn vị: 'pk' có trong `order_by` | QA | Tích hợp (Postgres) | Tự động | P1 |
| TL-10 | S3 | Cột tiền/thập phân không nhãn (ví dụ `so_tien_tt`) bị sắp theo chuỗi; lọc khoảng lặng lẽ thành so bằng | `query.py` `apply_sort` gọi `order_by('data__<code>')`; `apply_filters` (149-152) có `JSON_RANGE_TYPES` chỉ gồm integer/date/datetime | Dùng giá trị khác độ dài '999', '1234.50', '50': `?sap=so_tien_tt` phải ra thứ tự số, `?f_so_tien_tt__lon_bang=100` phải ra đúng tập dòng. Sửa `test_bang_dong.py::test_cot_tinh_san_luu_lai_nen_sap_xep_duoc` sang giá trị khác độ dài | QA | Tích hợp | Tự động | P1 |
| TL-11-ERP | S3 | Tổng quan ERP và /bang/: bảng thường đếm cả dòng xoá mềm và dòng ngoài phạm vi | `forms_builder/managers.py` `record_count_scope` (vế `~waybill_condition("")`); `dashboard_service._bang_dong`; `forms_builder/views.py` `bang` | Fixture Staff Sale gồm dòng của mình, dòng của Staff khác và một dòng xoá mềm trên bảng thường. Số từng bảng ở Tổng quan và /bang/ phải bằng `in_scope(...).count()`. Thêm dòng xoá mềm vào fixture `app/crm/tests/test_trang_chu_bang_lon.py`. Tệp kiểm dashboard cụ thể chưa xác minh | QA | Phân quyền hai chiều + tích hợp | Tự động | P1 |
| TL-12 | S4 | Xoá nhiều dòng (delete_rows, tối đa 2.000 dòng) chạy từng dòng; ước tính 10–12 truy vấn mỗi dòng (chưa đo) | `crm/services/row_mutations.py` `remove` → `record_service.delete_record` → `SoftDeleteModel.delete` → `DataRecord.save` | Trong `app/crm/tests/test_chi_admin_xoa_dong.py`: đếm truy vấn khi xoá 10 và 100 dòng, trần cố định, không được tăng tuyến tính | QA | Hiệu năng (ngân sách truy vấn) | Tự động | P2 |
| TL-13 | S2 | Màn Sửa cột `bang/<mã>/cot/<pk>/bo/` bỏ được cột EXTRA, `sl_*`, cột khoá, vế cột tính sẵn; với cột chuẩn thì ra trang 500 | `forms_builder/views.py` `bang_xoa_cot` không gọi `table_service.removable_reason`; BusinessError từ `waybill_service.assert_column_change` không ai bắt | Một bài "cùng luật cho mọi cửa": `bang-tinh/van_don/xoa-cot/` và `bang/van_don/cot/<pk>/bo/` × (cột chuẩn, EXTRA, sl_, khoá, vế tính sẵn), chạy ở cả 8020 và 8021. Kỳ vọng 400 có lời báo, không 500, cột còn nguyên. Thêm vào `app/crm/tests/test_bang_tinh_dong_cot.py` | QA | Tích hợp HTTP | Tự động + kiểm tay Chặng 2 | P1 |
| TL-18 | S2 | Phiên đã mất từ trước thì HTMX ở khung CRM nhận 302 và swap trang đăng nhập vào `#vd-entry`, `#vd-detail-body`, `#mg-column-filter-body`. Cùng gốc với TL-02: lưu đúng lúc hết phiên thì `clearAccess` bỏ nháp; poll báo "Quyền xem đã thay đổi."; poll 8 giây giữ phiên sống mãi | `core/middleware.py` `_ve_dang_nhap` chỉ chạy khi người dùng còn authenticated. `templates/crm/base_bang_tinh.html` và `base_crm.html` thiếu handler responseURL như `templates/base.html`. `master-grid.js` `json()`, `retainReadableDrafts`, `clearAccess` (1291-1303), `setInterval(poll,8000)` (1359) | (1) `app/core/tests/test_ra_soat.py`: yêu cầu HX-Request ẩn danh ở dịch vụ bangtinh phải nhận HX-Redirect hoặc 401, không nhận 302. (2) E2e: xoá sessionid rồi bấm Lưu đơn hoặc mở hộp lọc cột, không được swap. (3) E2e lưới: hết phiên giữa lượt dán thì không báo "Đã lưu", nháp còn, có lời báo hết phiên. (4) Bài chứng minh `moi-nhat/` không gia hạn `last_seen_at`. (5) Kiểm tay: để yên 61 phút | Người dùng + QA | HTTP + e2e | Tự động + Thủ công | P0 |
| TL-23 | S2 | Worker chết giữa lúc tính lại thì job RECOMPUTE nằm RUNNING mãi: chặn xoá bảng, đếm sai, không ai được báo | `core/tasks.py` `danh_dau_tac_vu_ket` (28-56) chỉ lọc PENDING; `table_service.recompute_job_of` (465-472); `lifecycle_service.delete` (73-78) | Trong `app/core/tests/test_sao_luu.py`: job RUNNING có `updated_at` cũ phải chuyển sang STALE/FAILED, có nhật ký và thư báo, xoá bảng hết bị chặn. Kiểm tay: `docker compose restart worker` (hoặc heavy) đúng lúc đang tính lại. Đợt săn lỗi 06.10 mới tắt Redis và restart Postgres, chưa giết worker giữa tác vụ | QA | Tích hợp tác vụ nền + chịu lỗi | Tự động + Thủ công | P1 |
| TL-25 | S3 | Không gộp job tính lại: bỏ 5 cột tạo 5 job. Worker dev chạy concurrency mặc định nên có thể ghi giá trị cũ (chưa xác minh) | `table_service.py` `schedule_resync` (443-462), `remove_column` (206); `deploy/docker-compose.yml:94` | POST xoa-cot/ với 5 cột trên bảng vượt `RECOMPUTE_SYNC_MAX_ROWS` thì chỉ có 1 job. Phải sửa kỳ vọng `count()==3` ở `app/crm/tests/test_kiem_tai.py::test_tinh_lai_cot_bang_lon_chay_nen` | QA | Tích hợp dịch vụ | Tự động | P2 |
| TL-26 | S4 | Một lô tính lại hỏng thì các lô sau vẫn chạy và commit; job bị đánh FAILED muộn | `table_service.py` `resync_table` (396-404): `ThreadPoolExecutor.map`, không có `cancel_futures` | Bài `transactional_db` (ngoài atomic, để đi vào nhánh luồng), monkeypatch `mot_lo` ném lỗi ở lô đầu. Kỳ vọng các lô sau không ghi, job FAILED ngay | QA | Đơn vị/tích hợp worker | Tự động | P2 |
| TL-27 | S4 | `do_hieu_nang` đo bước "tính lại" trên dữ liệu đã đồng bộ nên không ghi dòng nào; ghi chú sai; đếm thiếu truy vấn ở luồng phụ. Có thể dừng ở `/bang-tinh/perf_sale/` 404 (chưa xác minh) | `core/management/commands/do_hieu_nang.py` `handle` (225-233) | Bài khói chạy lệnh trên dữ liệu nhỏ: làm lệch dữ liệu trước, kiểm số dòng đổi > 0, đếm truy vấn cả luồng phụ hoặc ép chạy tuần tự | QA | Hiệu năng (công cụ đo) | Tự động | P2 |
| TL-28 | S4 | Docstring, AC-11.26 và mục "Đã kiểm" trong test-log vẫn ghi moi-nhat "trong phạm vi người xem", trong khi mã tính trên cả bảng (AC-10.21) | `crm/views.py` `bang_tinh_moi_nhat` (353); `crm/tests/test_bang_tinh_dong_cot.py::test_moi_nhat_tra_moc_trong_pham_vi`; docs/04 AC-11.26 | Sửa docstring và AC-11.26 cho khớp AC-10.21 | QA | Rà tài liệu | Thủ công | P2 |
| TL-29 | S4 | Chạy gunicorn ở local (script kiểm tải) thì không có gì phục vụ /static/ | `deploy/docker-compose.yml`; `scripts/kiem-tai-kn-crm.sh`, `.bat:27`; không có whitenoise, không có `static()` | Thêm bước curl `/static/css/...` phải trả 200 sau khi bật gunicorn trong `scripts/kiem-tai-kn-crm.*` | QA | Khói sau khởi động | Bán tự động | P2 |
| TL-30 | S4 | Script kiểm tải luôn chạy du_lieu_mau, đặt lại mật khẩu các tài khoản mẫu (16 từ #118); `seed_perf --xoa-cu` xoá cứng dòng PERF-* | `scripts/kiem-tai-kn-crm.sh`, `.bat:43`; `du_lieu_mau.py` (279-298) | Thêm cảnh báo ở đầu script và trong `docs/tai-khoan-mau.md`. Nếu đổi hành vi thì bỏ du_lieu_mau khi có `--giu-du-lieu` | QA | Rà script | Thủ công | P2 |
| TL-31 (tài liệu) | S4 | AC-11.36 và ADR-016 quyết định 1 vẫn nhắc `cell_html`/`cell_url`, `reverse('bang_tinh_o')`, ngân sách 25/8 truy vấn; bài thực tế dùng 35/9 | docs/04 dòng 320; `docs/quyet-dinh/016-…md` 41-44; `test_kiem_tai.py::test_dan_500_o_va_moi_nhat_ngan_sach_truy_van` | Sửa AC-11.36 và ADR-016. Mở rộng `app/tests/test_truy_vet.py` để kiểm tên hàm, tên bài trích trong docs có tồn tại thật | QA | Truy vết | Tự động + Thủ công | P2 |
| TL-32 | S4 | Cột DATETIME mang nhãn Ngày: chuỗi có giờ đi vào `val_date` thì ném ValidationError, hỏng cả lô | `forms_builder/models.py` `_normalise` (688-696); `meaning.py:68` | Đơn vị: `sync_indexed_columns` + `bulk_save` với '2026-09-01T10:00:00'. Tích hợp: đổi kiểu DATE → DATETIME trên bảng có dữ liệu; nhập tệp có cột ngày giờ | QA | Đơn vị + tích hợp | Tự động | P2 |
| TL-33 (khoảng trống) | S3 | Bài 50.000 dòng của CRM chỉ bấm giờ trang khung HTML, không đo `du-lieu/` (lọc, `?trung=1`), nên AC-7.1 chưa được đo | `app/tests/test_hieu_nang.py::test_bang_tinh_50000_dong_co_loc_duoi_2_giay`; `crm/master_views.py` `shell` | Thêm vào `test_hieu_nang.py` (dấu cham): bấm giờ và đếm truy vấn `/bang-tinh/van_don/du-lieu/` có lọc và `trung=1` | QA | Hiệu năng | Tự động | P1 |
| TL-36 (phần còn lại) | S3 | Cột Trùng không lọc được, không tô màu, không bấm xem dòng kia; số đếm bỏ qua phạm vi quyền. Chưa xác minh đây có phải chủ ý | `crm/services/waybill_grid.py` `grid_columns` đặt `filterable: False`; `grid_service.attach_duplicate_counts` và `duplicate_phones` không qua `in_scope` | Chốt ý đồ với chủ dự án trước. Sau đó: e2e (tô màu khi > 1, nút lọc chỉ số trùng, bấm mở các dòng cùng khoá) và phân quyền (số Trùng và `?trung=1` cho Sale staff/CSKH) | Người dùng + QA | E2e + phân quyền | Tự động + Thủ công | P1 |

**b) Lỗi ghi theo ngày còn sống (4 mục)**

| Mã | Mức | Lỗi | Bằng chứng | Bài hồi quy đề xuất | Góc nhìn | Loại | Hình thức | Ưu tiên |
|---|---|---|---|---|---|---|---|---|
| TL-82 | vừa | Log Postgres ghi nguyên câu UPDATE kèm dữ liệu khách khi vi phạm `record_ma_don_unique` (quy tắc 6) | `deploy/production/compose.yml:41` thiếu `log_min_error_statement=panic` | Trong `app/core/tests/test_kiem_cau_hinh.py`: đọc compose.yml, khẳng định lệnh db có cờ này. Chưa xác minh `compose.vps.yml` trên VPS. Lượt quét log ở săn lỗi bước 9 chỉ quét log ứng dụng, nginx và AuditLog, không quét log Postgres, nên không bắt được lỗi này. Ràng buộc này mới có từ biên bản database-phan-quyen 06.10 (xem 8.3b mục e) | QA | Kiểm cấu hình tĩnh | Tự động | P0 |
| TL-85 | vừa | `BANGTINH_GOC` gõ sai (khác 'prod') thì CRM lặng lẽ chạy cấu hình dev (DEBUG=True) | `app/knjsc/settings/bangtinh.py:30` | Trong `test_kiem_cau_hinh.py`: giá trị 'production' phải gây ImproperlyConfigured. Giữ bước `check --deploy --fail-level WARNING` trong README. Bản sửa AC-1.11 ngày 06.10 chỉ chặn trường hợp thiếu biến ở tên miền thật | QA | Đơn vị cấu hình | Tự động | P1 |
| TL-83 | vừa | `kiem_tra_du_lieu` ở 100.000 dòng bị diệt vì hết RAM trong container crm 640 MiB | `orders/services/integrity_service.py` `lech_cot_tach` (55, `list(...)`), `so_luong_lech` (94-101, không dùng `.iterator()`) | Bài dấu cham đo đỉnh bộ nhớ bằng tracemalloc, theo mẫu `app/crm/tests/test_executive_statistics_capacity.py`. Chạy trên DB seed_perf với giới hạn bộ nhớ. Lỗi này chặn điểm "Chưa kiểm 1" của biên bản database-phan-quyen (chạy lệnh trên VPS trước phát hành) | QA | Hiệu năng (bộ nhớ) | Tự động + Bán tự động | P1 |
| TL-71 | trung bình | Bài 18 e2e treo; gốc lỗi (tab sập hoặc luồng chính kẹt khi cuộn 1.000 dòng) chưa biết | `app/tests/e2e/test_ghi_chu_tu_gian_dong.py::test_do_hieu_nang_1000_dong_ghi_chu_400`; `.github/workflows/ci.yml:169-170` | Chạy lặp bài 18 N lần (job chạy tay) để tái hiện và giữ ngăn xếp. Tìm ra gốc thì thêm bài khoá | QA | E2e / hiệu năng trình duyệt | Bán tự động | P1 |

### 8.6 Lỗi đã đóng nhưng chưa có bài hồi quy, hoặc bài chỉ phủ một phần

| Mã | Trạng thái | Bài hiện có | Phần chưa được khoá | Bài đề xuất | Loại | Hình thức | Ưu tiên |
|---|---|---|---|---|---|---|---|
| TL-80 | đã sửa ở tài liệu; test-log vẫn ghi "mở" | không có | Dãy quay lui `collectstatic --clear` chưa chạy trên VPS thật | Sau collectstatic, so hash static với image đang chạy; diễn tập quay lui | Quy trình phát hành | Bán tự động | P0 |
| TL-81 | đã sửa ở tài liệu; test-log vẫn ghi "mở" | không có | Dừng các dịch vụ ghi trước migrate | Checklist expand/contract cho mọi PR có migration; bài CI chạy mã cũ trên lược đồ mới (hiện chưa có). Gộp với mục 1 của kịch bản ngoài máy ảo (migrate xuôi/ngược trên bản sao dữ liệu VPS, chưa xác minh đã chạy) | Quy trình phát hành | Bán tự động | P0 |
| TL-84 | đã sửa ở tài liệu; test-log vẫn ghi "mở" | không có | Dịch vụ `db` vẫn dùng `env_file: .env` (compose.yml:40) | Kiểm cấu hình tĩnh, hoặc `docker compose up --dry-run` trong dãy phát hành (chưa xác minh trên phiên bản Compose của VPS) | Quy trình phát hành | Bán tự động | P1 |
| TL-14 | hết | chỉ có `scripts/kiem-thu-master-ui.cjs` (chạy tay) | Dán xuyên biên khối 100 dòng | E2e: dán 150 dòng từ dòng 50 → ghi đúng dòng 50–199, tổng số dòng không đổi; dán quá cuối van_don → báo lỗi, không ô nào bị ghi | E2e | Tự động | P1 |
| TL-19 | hết | `scripts/kiem-thu-master-queue-unit.cjs` (chạy tay) | Chưa có bài trình duyệt trong CI cho lỗi 400 | Chặn route `luu-json` trả 400 → thanh trên hiện "Lỗi lưu" kèm lời báo; hoặc đưa script này vào CI | E2e / đơn vị JS | Tự động | P1 |
| TL-20 | hết | không có | `#mg-message` hiện khi lưu bị 400; ô sai không tô đỏ; lời báo hiện pk/mã cột thay vì số dòng/tên cột | E2e locator visible + ảnh chụp | E2e | Tự động | P1 |
| TL-15 | đã sửa | `test_bang_tinh_dinh_dang.py::test_dinh_dang_theo_quyen_sua_o` | Lượt hỗn hợp một pk trong, một pk ngoài phạm vi; nhánh 403 không gọi `record_denied` (chưa xác minh quy tắc có đòi hay không) | Lượt hỗn hợp → 403, không ô nào đổi style | Phân quyền hai chiều | Tự động | P1 |
| TL-46 | đã sửa | `core/tests/test_giao_dien.py::test_khong_chu_thich_css_nao_nuot_luat` | `CAC_TEP_CSS` thiếu `master-grid.css`, `payments.css` và các khối `<style>` trong template | Mở rộng danh sách tệp được quét | Giao diện tĩnh | Tự động | P1 |
| TL-08 (a) | hết | không có | Chính mình lưu xong thì lưới không được nạp lại | E2e: đếm request `du-lieu/` trong 10 giây sau khi lưu phải bằng 0; tích hợp: `latest` của luu-json bằng phản hồi `moi-nhat/` | E2e + tích hợp | Tự động | P2 |
| TL-21 | hết | không có (AC-8.10 ghi Thủ công) | Màu tiêu đề lưới | E2e đọc getComputedStyle nền tiêu đề ở nền sáng và tối, cả CRM lẫn `/bang/<mã>/` | E2e + kiểm tay docs/07 | Tự động + Thủ công | P2 |
| TL-24, TL-22 | hết | gián tiếp | Lượt ghi chạy song song `resync_table`; ép deadlock rồi gửi lại | Tích hợp `transaction=True`; Locust ghi ô trong lúc job tính lại chạy, đếm phản hồi 5xx | Đồng thời + tải | Tự động / Bán tự động | P2 |
| TL-31 | hết | không có | — | Gộp vào bài truy vết mở rộng (xem TL-31 tài liệu) | Truy vết | Tự động | P2 |
| TL-88 | đóng, không sửa mã | gián tiếp (`test_chi_admin_xoa_dong.py`) | Phím Delete để lại dòng trống vẫn được đếm | Bước kịch bản docs/07: xoá trắng một dòng rồi đối chiếu số dòng ở thư mục | Nghiệm thu theo vai | Thủ công | P2 |
| TL-02 | đã sửa | phía máy chủ có (`test_ra_soat.py`) | Toàn bộ phía JS | Đã gộp vào bài đề xuất của TL-18 | E2e | Tự động | P0 |
| TL-04 | đã sửa | `test_loc_sai_kieu.py` (mở rộng ở săn lỗi bước 10: 7 bộ lọc sai kiểu → 200) | Gõ '1.000.000' / '1,5' thì bộ lọc bị bỏ lặng lẽ | Đơn vị `apply_filters` với số kiểu Việt; chạy qua `du-lieu/` của CRM | Đơn vị + HTTP | Tự động | P2 |
| TL-06 | hết | `test_mat_mang_e2e.py` (chỉ mất mạng) | Phản hồi 500; poll vẫn chạy sau lỗi lưu | Chặn route trả 500, khẳng định poll vẫn thấy sửa đổi của người khác | E2e | Tự động | P2 |
| TL-07 | đã sửa | `test_master_grid.py::test_undo_rejects_changed_cell_and_limits` (cùng một tài khoản) | Hai người thật | E2e hai trình duyệt: A dán, B sửa, A Ctrl+Z → 409 | E2e | Tự động | P2 |
| TL-11 | đã sửa | `test_trang_chu_bang_lon.py` | Fixture có dòng xoá mềm; số ở /nhap-tep/, /cap-quyen/ so với trang chủ | Thêm fixture dòng xoá mềm, so các con số | Phân quyền + tích hợp | Tự động | P2 |
| TL-16 | đã sửa | `test_concurrent_cells_and_receipt` | `record_service.update_cell` (395-425) vẫn còn kiểu lỗi cũ, chỉ có tests gọi | Xoá hàm này, hoặc thêm khoá kèm bài đồng thời | Đơn vị / đồng thời | Tự động | P2 |
| TL-17 | đã sửa | `test_formula_atomic_and_style_preserved` | Protocol 2 (`render_cells`); trình duyệt | Bài cho protocol 2; e2e: ô tính sẵn đổi ngay sau Enter | Tích hợp + e2e | Tự động | P2 |
| TL-42 | đã sửa | gián tiếp | Lỗi "xfail nuốt teardown" có thể quay lại | Khai `xfail_strict` trong `app/pytest.ini` | Hạ tầng kiểm thử | Tự động | P2 |
| TL-48 | đã sửa | `test_hop_loc_cot_chon_cong_cu_theo_so_gia_tri` | Thời gian mở hộp lọc cột nhiều giá trị | Bấm giờ hộp lọc cột `ten_khach` trên bảng lớn | Hiệu năng | Tự động | P2 |
| TL-51 | đã sửa | `test_moi_ma_tieu_chi_chi_xuat_hien_mot_lan` (chỉ mã AC) | Mã TL bị trùng | Bài chặn trùng mã TL trong `docs/test-log.md` | Truy vết | Tự động | P2 |
| TL-63 | đã sửa | `test_lan_chuot_tren_bang_khong_ket` | Rớt khung hình khi cuộn (mới chỉ đo tay) | Đo khung hình trong Playwright | E2e hiệu năng | Bán tự động | P2 |
| TL-66 | đã sửa | gián tiếp (AC-46.9) | Gọi riêng group='person' khi quá trần (chưa xác minh đã có bài) | Ép `MAX_GROUPS` nhỏ cho từng cách xem day/team/person | Đơn vị biên | Tự động | P2 |
| TL-74 | đã sửa | `test_bang_vua_khi_thu_mo_thanh_menu` | Bảng dữ liệu dạng báo cáo không đo lại khi thu/mở thanh menu (chưa làm theo lời chủ dự án) | Sửa mã, rồi thêm bài tương tự cho `/bang/<mã>/` | E2e | Tự động | P2 |
| Săn lỗi 06.10 (các phần "chưa kiểm") | đã sửa phần lỗi; phần còn lại mở | 16 tệp bài ở 8.3b | Đầy ổ Postgres; mất điện; chạy nhiều ngày; bộ gõ và trình duyệt thật; fuzz nội dung tệp tải lên; dò rải theo IP; đột biến JS lưới | Chạy mục 1–6 của `docs/kich-ban-kiem-ngoai-may-ao-20261006.md` và ghi kết quả vào biên bản phát hành VPS; mục 7 phải để chủ dự án chốt | Chịu lỗi + bảo mật + môi trường thật | Thủ công / Bán tự động | P1 |
| Biên bản database-phan-quyen 06.10 ("Chưa kiểm" và ghi nhận chưa sửa) | đã sửa 11 lỗ hổng; 3 điểm chưa kiểm và 3 ghi nhận còn mở | 9 tệp bài ở 8.3b mục e | `kiem_tra_du_lieu --bang van_don` chưa chạy trên VPS (vướng TL-83); cookie domain thật chưa kiểm; đổi kiểu cột 100.000 dòng trong request web chưa đo; `/bang-da-xoa/` trả rỗng cho Staff thay vì 403 | Xem bảng "Ghi nhận chưa sửa và điểm Chưa kiểm" ở 8.3b mục e | Di trú dữ liệu + phát hành + hiệu năng + phân quyền | Thủ công / Bán tự động / Tự động | P0 (mục chạy lệnh trên VPS), còn lại P1–P2 |

Rủi ro sót trong lỗi đã đóng, chưa thành lỗi: TL-35 (bảng có workflow='waybill' mà mã khác 'van_don' sẽ không có cột Trùng); TL-50 (chỉ cảnh báo, chủ dự án đã chấp nhận); TL-08 (poll không kiểm generation sau await); TL-24 (chú thích `bulk_save` 601-603 sai; `nap_du_lieu_van_don` chưa xác minh có khoá trước hay không).

### 8.7 Kết luận

| Câu hỏi | Trả lời từ số liệu | Ý nghĩa cho chỗ cần đầu tư |
|---|---|---|
| Tầng nào rò nhiều nhất? | Tích hợp/chức năng HTTP (16) và E2E trình duyệt (16), kế đến rà đặc tả/ADR (13). Chỉ tính lỗi ghi theo ngày thì **rà đặc tả/ADR đứng đầu (12/48)** | Nhiều lỗi lọt qua vì bài kiểm làm đúng một đặc tả sai: TL-44, 64, 65, 87 (CI xanh suốt thời gian lỗi tồn tại). Tự động hoá không bắt được loại này. Cần cổng duyệt mockup/ADR với chủ dự án và kịch bản theo vai trong docs/07, đặc biệt cho vai only_own_rows, dữ liệu loại tiền khác VND, xoá trắng dòng |
| Chặng nào bắt nhiều lỗi nhất? | Trong 48 lỗi mang mã: chủ dự án (VPS 11 + local 7) bắt **18/48 (38 %)**. Cộng diễn tập VPS (7) và kiểm Staging (4) là **29/48 (60 %) bị bắt sau CI**. CI và e2e tự động chỉ bắt 6/48, trong đó chỉ khoảng 2 là lỗi thật của ứng dụng (TL-53, TL-57). Nếu tính cả lỗi không mang mã thì đợt săn lỗi 06.10 là nguồn lớn nhất: **23 lỗi trong một ngày**, 6 lỗi nghiêm trọng | Lưới tự động hiện chủ yếu khoá lỗi đã biết, ít khi chặn được lỗi mới. Lỗi người dùng thấy rơi vào hai loại: sai đặc tả (8) và trạng thái biên trên trình duyệt (6: TL-49, 62, 63, 69, 73, 86) |
| Đợt săn lỗi có chủ đích nói gì? | Năm loại kỹ thuật không nằm trong chín tầng của docs/06 (đồng thời thật nhiều kết nối, diễn tập sự cố, fuzz, đối soát chéo, giả lập mạng/bộ gõ/múi giờ) bắt 23 lỗi mà CI để lọt. Đột biến tay: bài có sẵn bắt 12/17, còn 2 lỗ (M10b, M16) đã lấp. Hai bản sửa ngày 06.10 gây lỗi mới mà diễn tập 08.10 mới bắt: TL-79 (middleware NFC của săn lỗi bước 4) và TL-82 (ràng buộc `record_ma_don_unique` của biên bản database-phan-quyen) | Lặp lại đợt săn lỗi trước mỗi mốc phát hành; giữ các bài khoá (đã có) trong CI. Sửa ở middleware, cửa vào hay ràng buộc DB thì kiểm cả dữ liệu cũ và log. Việc đột biến còn lại chỉ là JS lưới và đột biến tự động (phải hỏi thư viện). Mục 1, 4, 5, 6 của kịch bản ngoài máy ảo và ba điểm "Chưa kiểm" của biên bản database-phan-quyen chưa có kết quả ghi lại |
| Chủ dự án thử ở local nói gì? | 7 lỗi trong khoảng 28.09–10.10, chủ yếu về UX/đặc tả (TL-72, 87, 88) và bố cục (TL-63, 73) | Chặng 2 có giá trị; nên chuẩn hoá thành checklist có ghi kết quả, không để tuỳ hứng |
| Diễn tập VPS nói gì? | Một lượt bắt 7 lỗi; 2 mức cao (TL-80, 81); 3 lỗi còn sống (TL-82, 83, 85). 5/7 lỗi thuộc quy trình/cấu hình phát hành, tầng mà **không có bài tự động nào**. Lượt này cũng xác nhận lại các bản sửa của săn lỗi bước 1 và 6 | Đầu tư: (1) kiểm cấu hình tĩnh trong CI (compose.yml, settings, cờ log); (2) mỗi PR có migration phải diễn tập nâng cấp trên dữ liệu bẩn và chạy mã cũ trên lược đồ mới (TL-76, TL-81); (3) đưa dãy lệnh README thành script có kiểm tra (TL-80, 84), trong đó có bước `kiem_tra_du_lieu --bang van_don` trước migrate (sau khi sửa TL-83) |
| Mã bị thay đã dọn được gì? | 10/35 mã bảng cũ hết nhờ thay lưới master-grid | Lưới mới chưa có bài JS trong CI: nhiều bài hồi quy chỉ có ở `scripts/kiem-thu-*.cjs` chạy tay (TL-06, 14, 19). Cần đưa vào CI |
| Lỗi nặng còn sống | TL-01 (S1, phân quyền), TL-03 (S1, tiền, cùng gốc TL-57), TL-18 (S2, mất nháp/hết phiên), TL-82 (lộ dữ liệu ở log) | Đây là bốn mục P0 phải đóng trước phát hành. TL-03 cần chủ dự án chốt luật số trước khi viết bài, vì luật hiện hành đang bị hai bài khoá (có bài lấp lỗ M10b). Thêm một việc P0 của quy trình: chạy `kiem_tra_du_lieu --bang van_don` trên VPS trước khi đưa `forms_builder/0017` lên |

### 8.8 Đề xuất dọn docs/test-log.md

| Việc | Chi tiết |
|---|---|
| Thêm cột cho bảng cũ | "Trạng thái mã hôm nay" (Còn sống / Hết – mã bị thay / Đã sửa), "Bài hồi quy" (đường dẫn::tên bài hoặc "chưa có"), "Ngày rà" (13.10.2026) |
| Đổi trạng thái thành **Đã sửa** | TL-02, 04, 07, 11, 15, 16 (dòng 1220), 17 (dòng 1221), 33, 35, 36 |
| Đổi trạng thái thành **Hết – mã bị thay** | TL-05, 06, 08, 14, 19 (dòng 1206), 20 (dòng 1207), 21 (dòng 1208), 22, 24, 31 |
| Giữ **Mới/mở**, viết lại mô tả theo mã hiện tại | TL-01, 03, 09, 10, 12, 13, 18 (dòng 1205; ghi rõ phần đã sửa), 23, 25, 26, 27, 28, 29, 30, 32 |
| Tách phần dư thành mục riêng | TL-11-ERP, TL-31 (tài liệu), TL-33 (khoảng trống), TL-36 (phần còn lại). Cấp mã mới hoặc hậu tố, kèm tham chiếu mã gốc |
| Kiểm chứng rồi ghi trạng thái | TL-34 (dòng 1222 "chưa gộp", PR21 nay đã trên main), TL-41 (dòng 826). Ghi rõ TL-37–40 và TL-59 không được dùng, hoặc chỉ chỗ đang ghi (chưa xác minh) |
| Đưa các lỗi ngày 06.10 vào test-log | (1) Đợt săn lỗi: 23 lỗi và 2 lỗ bài hiện chỉ có ở `docs/backlog.md` (dòng 283–406) và 10 biên bản `docs/kiem-chung-san-loi-*-20261006.md`. (2) Biên bản `docs/kiem-chung-database-phan-quyen-20261006.md`: 11 lỗ hổng đã sửa, chỉ có ở `docs/backlog.md` (dòng 269–281). Test-log không có mục nào ngày 06.10. Cấp mã TL (đóng, kèm tệp bài khoá) hoặc thêm một bảng trỏ tới các biên bản. Ghi các điểm "chưa kiểm" của cả hai nguồn, bốn điểm chờ chốt (mục 7 của `docs/kich-ban-kiem-ngoai-may-ao-20261006.md`) và ghi nhận `/bang-da-xoa/` trả rỗng cho Staff thành mục mở. Ghi trong TL-79 rằng gốc là bản sửa săn lỗi bước 4, và trong TL-82 rằng ràng buộc gây lỗi ra đời từ biên bản database-phan-quyen |
| Sửa nhãn lỗi ghi theo ngày | TL-80, 81, 84: đổi "mở, quy trình" thành "đã sửa ở README, chờ chạy trên VPS thật". TL-83, 82, 85: giữ mở |
| Gỡ mã trùng và mã sai | TL-52 dùng hai lần: đổi bản 23.09 sang hậu tố hoặc mã mới. Sửa chú thích trong mã: `app/reports/screen.py:222` ghi TL-46 (đúng là TL-52 bản 23.09); `app/reports/activity_views.py:31` ghi TL-47 (đúng là TL-58); `app/forms_builder/views.py:256` ghi TL-58 (đúng là TL-54). Ghi chú commit 9612463 gọi TL-58 là "TL-53". Sửa mã AC cũ ở dòng 772-773 (AC-11.40 → AC-11.41, AC-6.9 → AC-6.10) |
| Sửa mục "Đã kiểm, không thấy lỗi" | Dòng khoảng 1238: bỏ câu "moi-nhat … đều có phạm vi" (TL-28) |
| Đồng bộ tài liệu lệch khác | `docs/backlog-kanban.md` (các dòng 711-737 của TL-01…TL-33, dòng 717 TL-35); `docs/handoff/project-brief.md` dòng 347/349/351 (TL-48, 43, 24); ADR-016 mục 5 (TL-22) và quyết định 1 (TL-31); docs/04 AC-11.26, AC-11.36. Thêm vào `docs/06-ke-hoach-kiem-thu.md` các kỹ thuật của đợt săn lỗi (hiện tệp không nhắc tới) |
| Chặn tái phát | Mở rộng `app/tests/test_truy_vet.py`: kiểm mã TL không trùng trong `docs/test-log.md`, và mã TL trích trong chú thích mã có tồn tại thật (TL-51) |
