# Biên bản kiểm thử tổng hợp — 15.10.2026

Biên bản này gộp sổ lỗi `docs/test-log.md` và các đợt kiểm thử trước đây vào một chỗ: tiến độ kiểm thử toàn hệ thống,
lượt sửa 15.10, sổ lỗi đầy đủ TL-01 → TL-124 kèm mức và trạng thái, các việc còn lại. `docs/test-log.md` vẫn giữ làm
sổ chi tiết (cách tái hiện, chỗ sai, lệnh đã chạy của từng mã), vì CLAUDE.md, `docs/08` và các biên bản dẫn tới đó.

| Mục | Giá trị |
|---|---|
| Người làm | Claude Code (máy ảo trên web), chủ dự án yêu cầu 15.10.2026 |
| Nhánh | `claude/sua-tl105-111` ([#133](https://github.com/CyrusDev1512/KNJSC/pull/133)), đã gộp `Staging` 15.10.2026 cùng #132 và #134 |
| Môi trường | Máy ảo: PostgreSQL 16, Python venv của dự án, Chromium qua Playwright 1.56, `pg_dump`/`pg_restore` 16. Không có VPS, không có máy Windows |
| Mức nghiêm trọng | S1 sai tiền, mất dữ liệu, lộ quyền · S2 sai số liệu hay chặn việc · S3 sai nhưng có đường vòng · S4 nhẹ. Các mã TL-41 → TL-89 ghi theo mức cũ Cao / Vừa / Nhẹ |

## 1. Tiến độ kiểm thử toàn hệ thống

| Phần | Progress | Đạt / tổng | Ghi chú |
|---|---|---|---|
| Bộ kiểm tự động (không trình duyệt) | `██████████` 100% | 3.880 đạt, 0 đỏ | Chạy trên nhánh này 15.10 |
| Kiểm trình duyệt (e2e), hai lượt như CI | `██████████` 100% | 81 + 30 đạt, 0 đỏ | |
| Sao lưu và phục hồi thật (`-m cham`) | `██████████` 100% | 4/4 đạt | Gồm bài mới phục hồi đè lên chính CSDL |
| Script Node đơn vị của lưới | `██████████` 100% | 13/13 đạt | |
| AC tự động đã có bài kiểm | `█████████░` 95% | 367/385 | Còn 18 AC hoãn (`HOAN` trong `test_truy_vet.py`) |
| AC phải kiểm tay | `░░░░░░░░░░` 0% | 0/13 | Chưa ai kiểm tay |
| Lộ trình P0 (`docs/08` mục 9.1) | `████████░░` 76% | 13/17 | P0-5, P0-6, P0-11, P0-12 chờ chủ dự án quyết (`docs/08` mục 9.5) |
| Lộ trình P1 | `░░░░░░░░░░` 0% | 0/29 | Chưa làm |
| Lộ trình P2 | `░░░░░░░░░░` 0% | 0/19 | Chưa làm |
| Lỗi đã ghi (TL-01 → TL-124) đã đóng | `███████░░░` 70% | 83/119 | 76 đã sửa (60 trước 15.10, 11 của #133, TL-80/81/82/84/85 ở lượt phát hành 09.10) + 7 hết trên lưới mới (rà 15.10). 27 mã cũ đã rà xong, thêm 12 mã mới |
| Chặng 2 kiểm tay ở local | `░░░░░░░░░░` 0% | — | Phần của chủ dự án; diễn tập bằng máy 14.10 (40 bước) đã đạt |
| Chặng 3 (`main`) và chặng 4 (VPS) | `░░░░░░░░░░` 0% | — | Chờ chặng 2 |

## 2. Kết quả chạy lần cuối trên nhánh này

Mã ở commit `cbe3b50` (sau đó chỉ thêm `3ec1783` sửa chú thích và commit tài liệu này), máy ảo, mỗi lượt pytest một cơ sở dữ liệu kiểm thử riêng.

| Lệnh | Kết quả |
|---|---|
| `pytest -m "not trinh_duyet"` | 3.880 đạt, 7 bỏ qua (kiểm tải riêng, cần cấu hình riêng), 0 đỏ; 13 phút 50 giây. Trước lượt sửa (cây gộp thử 14.10) là 3.852: thêm 28 bài |
| `pytest tests/e2e -m trinh_duyet -o faulthandler_timeout=120` | 81 đạt, 2 bỏ qua (một bài cần dòng trống, một bài kiểm tải 300.000 dòng chỉ chạy khi bật cờ), 0 đỏ; 7 phút 29 giây |
| `pytest -m trinh_duyet --ignore=tests/e2e` (lượt 2 như CI) | 30 đạt, 9 bỏ qua (cần Chrome máy chủ, proxy hay DB riêng), 0 đỏ; 4 phút 32 giây |
| `pytest core/tests/test_sao_luu.py -m cham -rs` | 4/4 đạt với `pg_dump`/`pg_restore` thật (3 bài cũ + 1 bài mới; chạy riêng và trong bộ chính), gồm bài mới phục hồi đè lên chính CSDL kiểm thử |
| `pytest tests/test_truy_vet.py tests/test_dong_bo_skill.py` | Đạt (chạy trong bộ chính). Không thêm mã AC mới nên bộ đếm `docs/06` giữ 367/385, hoãn 18 |
| `manage.py check` (ERP và CRM), `makemigrations --check --dry-run` | Không có vấn đề; không có migration mới |
| `node scripts/kiem-thu-*-unit.cjs` | 13/13 đạt: 10 script `*-unit.cjs` (có script mới của TL-109), `master-working-copy`, `master-row-geometry`, `date-inputs` |
| Rà đối kháng (Workflow, 4 hướng, mỗi phát hiện có người kiểm lại cố bác) | 4 hướng (quyền và nhật ký, hành vi ngoài phạm vi, bài kiểm, JS và template), 7 agent: 3 phát hiện, cả 3 bị người kiểm lại bác vì có từ trước và nằm ngoài 11 lỗi (ghi ở mục 7). Một câu docstring của `handler403` nói quá phạm vi đã sửa (`3ec1783`). Không lỗi nào do diff gây ra |

## 3. Lượt sửa 15.10.2026: 11 lỗi

Mỗi lỗi: viết bài kiểm trước, chạy để chắc **đỏ** đúng vì lỗi trên mã cũ, rồi sửa tối thiểu cho **xanh**. Không đổi
quyền, nghiệp vụ, cấu trúc dữ liệu; không migration; không thư viện mới. Cách sửa TL-105 → TL-111 chủ dự án duyệt
15.10 (sau workflow thiết kế 4 agent và phản biện 4 agent); TL-101 → TL-104 duyệt cùng kế hoạch "sửa nốt".

| Mã | Mức | Lỗi | Sửa | Bài kiểm (đỏ trước → xanh sau) | Commit |
|---|---|---|---|---|---|
| TL-109 | S2 | Lưới Vận đơn: sau Tôi/Tìm/lọc, nút Thống kê mất `nguon` và mở bảng tổng hợp; người đã nhớ lựa chọn Tôi gặp ngay khi mở lưới | Link khai `data-query-base`, JS ghép bộ lọc vào phần riêng (`hrefTruyVan`) | Node `kiem-thu-master-query-link-unit.cjs`, e2e `test_thong_ke_tu_luoi.py`, bài máy chủ: 3 đỏ → xanh | `a37ac24` |
| TL-110 | S2 | Thống kê: bấm Áp dụng thì mất Tôi, Tìm, lọc cột; số nhảy sang toàn bảng mà không báo | Ô ẩn mang trạng thái lưới kèm `loc_nguon`; đổi nguồn thì bỏ lọc bảng cũ; dòng "Đang lọc theo lưới" có × từng nhãn và "Bỏ lọc lưới" | `test_thong_ke_giu_bo_loc.py` + e2e: 8 đỏ → xanh | `211d41d` |
| TL-106 | S3 | Manager mất bộ phận: 3 dòng ERROR ở trang chủ CRM, 403 không có nhật ký, lưới nhận trang HTML, trang 403 không có lối ra | `handler403` chung hai dịch vụ: riêng lỗi chưa gán bộ phận ghi một dòng Từ chối và trả JSON cho lưới; trang chủ CRM hỏi phạm vi trước; trang 403 có nút Đăng xuất | `test_tu_choi_chua_gan_bo_phan.py`: 5 đỏ → xanh | `b6893aa` |
| TL-105 | S3 | Phục hồi sao lưu xong thì báo "tác vụ kẹt" và gửi thư nhầm | Phục hồi xong đóng đúng tác vụ sao lưu sinh ra tệp (Xong, giờ ghi tệp, không thư, không mở đường tải tệp) | `test_sao_luu.py` 4 bài, có bài phục hồi thật đè lên chính CSDL: 3 đỏ → xanh | `ffcdc99` |
| TL-107 | S3 | Bỏ cột bị từ chối thì đứng ở địa chỉ POST, mở lại ra 405 trắng | Post/Redirect/Get: lời đỏ hiện ở màn Cột | `test_bang_tinh_dong_cot.py`: 14 ca đỏ → xanh | `ad58859` |
| TL-101 | S3 | Đổi kiểu cột còn giá trị không chuyển được (ERP) hay đổi cấu trúc cột chuẩn Vận đơn (CRM) ra 500 | Báo trong khung "Chưa lưu được" (400), giữ chữ đã gõ, cột không đổi | `test_doi_kieu_cot.py`: 2 đỏ (500) → xanh | `fc938a7` |
| TL-108 | S3 | Dòng "Khoá tạm" bị lược chữ vì có chữ "mật khẩu", và ghi lặp mỗi lần thử trong lúc khoá | Chữ mới "Khoá tạm 15 phút do đăng nhập sai 5 lần", chỉ ghi ở lần thử đặt khoá | `test_do_mat_khau.py`, `test_quan_tri_dang_nhap.py`: 3 đỏ → xanh | `cd0f39c` |
| TL-111 | S4 | Kho chứng từ (cờ đang tắt): 403 không có nhật ký | Ghi một dòng Từ chối ở một chỗ cho cả sáu đường | `test_payment_documents.py`: 1 đỏ → xanh, thêm bài chiều được phép | `36f8b4d` |
| TL-103 | S3 | Danh sách quyền còn hiện quyền đã thu; thu lần hai ghi đè mốc thu và thêm nhật ký | Đọc quyền còn hiệu lực ở 4 chỗ; thu lần hai 404 | `test_man_hinh_bang.py`: 1 đỏ → xanh | `3e48a8c` |
| TL-104 | S3 | Gửi form thường vào phân công vận đơn và 4 đường JSON của lưới ra 500 | `core.views.json_body`: thân không phải JSON thì 400 | `test_waybill_feedback.py`: 1 đỏ (500) → xanh | `64ca888` |
| TL-102 | S3 | Kịch bản kiểm tải `locustfile.py` sửa vận đơn thật, lên đơn thật | Chỉ mở và sửa dòng `PERF-*`; lên đơn chỉ khi đặt `KNJSC_TAI_LEN_DON=1` | `test_locust_chi_dong_perf.py`: 2 đỏ → xanh | `cbe3b50` |

Phát hiện thêm khi sửa: `tests/perf/locustfile_kn_crm.py` cũng sửa ô trên dòng thật — ghi thành **TL-112** (mục 5),
chưa sửa vì ngoài phạm vi đã duyệt.

## 4. Sổ lỗi đầy đủ

TL-37 → TL-40 và TL-59 không được dùng. Trạng thái: **Đã sửa** (đã gộp `Staging`, hay đã áp trên VPS với mã quy trình),
**Hết trên lưới mới** (rà 15.10: hậu quả không còn trên mã hiện tại, đóng), **Mở**, **Không sửa**. 27 mã "Cần rà lại" đã
rà xong 15.10: `docs/kiem-chung-ra-27-ma-cu-20261015.md`.

| Trạng thái | Số mã |
|---|---|
| Đã sửa (đã gộp `Staging` hay đã áp trên VPS) | 76 |
| Hết trên lưới mới (rà 15.10) | 7 |
| Mở | 35 (3 cũ + 20 sau rà + 12 mới) |
| Không sửa | 1 |
| **Tổng** | **119** |

### 4.1 TL-01 → TL-36: rà lưới HTMX cũ (05–07.09.2026)

| Mã | Mức | Lỗi | Trạng thái |
|---|---|---|---|
| TL-01 | S1 | Manager bộ phận khác tự cấp quyền Sửa cho mình trên bảng chỉ được Xem | Đã sửa #122 (P0-1) |
| TL-02 | S1 | Hết phiên 60 phút mà lưới vẫn báo "Đã lưu", mất nháp | Đã sửa #129 (P0-14, ADR-053) |
| TL-03 | S1 | Số có từ 3 chữ số lẻ bị nhân nghìn (`0.125` thành `125`) | Đã sửa bước 1 #124 (P0-3, ADR-052) |
| TL-04 | S2 | Lọc khoảng cột tiền/ngày với chuỗi lạ ra 500 | Mở — còn một phần, S3 (rà 15.10) |
| TL-05 | S2 | Khôi phục dòng bỏ qua phạm vi quyền | Hết trên lưới mới (rà 15.10) |
| TL-06 | S2 | Ô gặp 403/500 kẹt "đang lưu", tự cập nhật dừng | Mở — còn một phần, S3 (rà 15.10) |
| TL-07 | S3 | Hoàn tác ghi đè sửa của người khác không cảnh báo | Hết trên lưới mới (rà 15.10) |
| TL-08 | S3 | Tự lưu xong lưới nạp lại cả bảng, báo "có dữ liệu mới" nhầm | Mở — còn một phần, S4 (rà 15.10) |
| TL-09 | S3 | Sắp xếp không ổn định giữa các trang | Mở — còn một phần (Bảng dữ liệu ERP), S3 (rà 15.10) |
| TL-10 | S3 | Cột tiền không nhãn sắp xếp và lọc theo chuỗi | Mở — còn nguyên, S3 (rà 15.10) |
| TL-11 | S3 | Trang chủ đếm cả dòng ngoài phạm vi và dòng đã xoá | Mở — còn một phần (ERP), S3 (rà 15.10) |
| TL-12 | S4 | Xoá 2.000 dòng tốn khoảng 6.000 truy vấn | Mở — còn nguyên, nâng S3 (rà 15.10) |
| TL-13 | S2 | Màn Sửa cột cho bỏ cột hệ thống của bảng vận đơn | Đã sửa #120 (P0-7) |
| TL-14 | S3 | Dán vượt trang tạo dòng mới thay vì ghi tiếp | Mở — phần còn lại là TL-113 (rà 15.10) |
| TL-15 | S3 | Định dạng ô ngoài phạm vi bị bỏ qua lặng lẽ thay vì 403 | Hết trên lưới mới (rà 15.10) |
| TL-16 | S3 | Sửa một ô ghi cả dòng, hai người cùng dòng ghi đè nhau | Hết trên lưới mới (rà 15.10) |
| TL-17 | S3 | Sửa một ô không vẽ lại cột tính sẵn của dòng | Hết trên lưới mới (rà 15.10) |
| TL-18 | S2 | Hết phiên, HTMX dán cả trang đăng nhập vào ô đang sửa | Đã sửa #129 (P0-14) |
| TL-19 | S2 | Máy chủ trả 400 mà lưới báo "Đã lưu" | Mở — còn một phần, S4 (rà 15.10) |
| TL-20 | S2 | Lời báo lỗi của ô bị giấu dưới ô | Mở — còn một phần, S3 (rà 15.10) |
| TL-21 | S3 | Tiêu đề bảng ngoài vận đơn màu vàng đồng | Hết trên lưới mới (rà 15.10) |
| TL-22 | S1 | Làm lại giao dịch sau deadlock không ghi gì mà vẫn trả 200 | Hết trên lưới mới (rà 15.10) |
| TL-23 | S2 | Tác vụ "Tính lại cột" kẹt Đang chạy khi worker chết | Đã sửa #117 (P0-13) |
| TL-24 | S3 | Chỉ lưu ô có làm lại khi deadlock; thao tác khác có thể 500 | Mở — còn một phần, S4 (rà 15.10) |
| TL-25 | S3 | Không gộp tác vụ tính lại; sửa công thức hai lần có thể để lô cũ | Mở — còn nguyên, S3 (rà 15.10) |
| TL-26 | S4 | Lỗi ở một lô tính lại không dừng các lô còn lại | Mở — còn một phần, S4 (rà 15.10) |
| TL-27 | S4 | `do_hieu_nang` đo tính lại trên dữ liệu đã đồng bộ | Mở — còn nguyên, S4 (rà 15.10) |
| TL-28 | S4 | `moi-nhat/` không lọc theo phạm vi từng người | Mở — còn nguyên (chỉ tài liệu), S4 (rà 15.10) |
| TL-29 | S4 | Tệp tĩnh không phục vụ khi chạy gunicorn trong kiểm tải | Mở — còn nguyên, S4 (rà 15.10) |
| TL-30 | S4 | Script kiểm tải đặt lại mật khẩu mẫu, xoá cứng dòng PERF | Mở — còn nguyên, S4 (rà 15.10) |
| TL-31 | S4 | Docstring nhắc bài kiểm không tồn tại | Mở — còn một phần (tài liệu), S4 (rà 15.10) |
| TL-32 | S4 | JSON ngày có giờ làm hỏng cả lô `bulk_save` | Mở — còn nguyên, nâng S2 (rà 15.10) |
| TL-33 | S4 | `test_hieu_nang` xfail vì ngân sách truy vấn | Mở — còn một phần, S4 (rà 15.10) |
| TL-34 | S2 | Đổi cột tính sẵn trên bảng lớn chạy đồng bộ trong yêu cầu | Đã sửa ở PR21 (ADR-016; sổ còn ghi "chưa gộp" từ 07.09) |
| TL-35 | S2 | Cột Trùng chỉ có ở bảng vận đơn cũ | Đã sửa (đóng 18.09, ADR-036 một bảng) |
| TL-36 | S2 | Trùng đếm theo số điện thoại đúng như gõ | Đã sửa (đóng 22.09) |

### 4.2 TL-41 → TL-89: các đợt 16.09 → 12.10.2026

| Mã | Mức | Lỗi | Trạng thái |
|---|---|---|---|
| TL-41 | Cao | Nộp báo cáo MKT/Sale trên VPS báo lỗi loại tiền CAD | Đã sửa |
| TL-42 | — | Bài `test_hieu_nang` dọn dẹp lỗi, rò bộ phận sang bài khác | Đã sửa |
| TL-43 | — | Xoá 50.000 dòng giả treo im lặng | Đã sửa (đóng phần hậu quả 22.09) |
| TL-44 | — | Tệp thật có PTTT "Cheque" bị từ chối | Đã sửa (bảy PTTT, 18.09) |
| TL-45 | — | Cách xem Tổng hợp gộp mọi người | Đã sửa |
| TL-46 | — | Hộp lọc cột không nền, chữ đè lên lưới | Đã sửa |
| TL-47 | — | Đơn thứ hai cùng số điện thoại lấy tên khách của đơn đầu | Đã sửa |
| TL-48 | — | Hộp lọc nhiều giá trị chưa có ô gõ, số đếm sai | Đã sửa |
| TL-49 | — | Đổi cột thì hộp lọc sót mục của cột trước | Đã sửa |
| TL-50 | — | Gõ nhầm số điện thoại làm danh bạ đổi tên âm thầm | Đã sửa |
| TL-51 | — | Hai mã AC bị dùng hai lần | Đã sửa |
| TL-52 | — | Chip "Kỳ" có dấu × sai lúc | Đã sửa |
| TL-53 | — | Cột đã ẩn mà lưới vẫn đọc bộ lọc của nó | Đã sửa (AC-39.9) |
| TL-54 | — | Phân trang Bảng dữ liệu mất tìm kiếm | Đã sửa |
| TL-55 | — | Nút Sửa cột hiện với quản lý bộ phận khác | Đã sửa |
| TL-56 | — | Ô Đúng/sai in True/False | Đã sửa |
| TL-57 | — | Form Ngưỡng màu hiện chuỗi máy `0.345` | Đã sửa |
| TL-58 | — | Báo cáo tổng hợp từ trang 2 không sang trang khác được | Đã sửa |
| TL-60 | — | Thẻ Tổng quan ERP xếp chật, số tiền bẻ dòng | Đã sửa |
| TL-61 | — | Lên đơn báo "Khách mua lại" sai số đơn | Đã sửa |
| TL-62 | — | Bấm sắp xếp tải lại cả trang | Đã sửa |
| TL-63 | — | Gộp/Không gộp rồi lăn chuột bị chậm | Đã sửa |
| TL-64 | — | Nút Tôi không ra dòng của tài khoản | Đã sửa |
| TL-65 | — | CPQC 13 250 000 hiện thành số khổng lồ | Đã sửa |
| TL-66 | — | Cách xem Theo nhân viên quá trần nhóm gắn sai | Đã sửa |
| TL-67 | — | CI `main` đỏ vì kẹt khoá khi dọn bảng | Đã sửa |
| TL-68 | — | 3 bài trình duyệt đỏ trước phát hành VPS | Đã sửa |
| TL-69 | — | Báo cáo cuộn thì số chồng mờ (VPS) | Đã sửa |
| TL-70 | — | CI `main` đỏ 2 bài vì ngầm coi hôm nay là tháng 9 | Đã sửa |
| TL-71 | — | CI e2e thỉnh thoảng treo hay đỏ, chưa rõ gốc | **Mở** |
| TL-72 | — | "Staff Sale tạo được sản phẩm" là nhầm nút thêm dòng | Đã sửa (đóng, không phải lỗi quyền) |
| TL-73 | Vừa | Bộ lọc không kéo tới được nút Áp dụng | Đã sửa |
| TL-74 | Vừa | Bảng hụt 96 px khi thu thanh menu | Đã sửa |
| TL-75 | Nhẹ | Escape không thoát toàn màn hình khi đang lọc sản phẩm | Đã sửa |
| TL-76 | Vừa | Cập nhật lên mã có `forms_builder/0017` lỗi | Đã sửa |
| TL-77 | Nhẹ | Admin xoá dòng khi lưới lọc còn đúng dòng đó | Đã sửa |
| TL-78 | Nhẹ | Manager Sale thấy nút Cột của bảng vận đơn | Đã sửa |
| TL-79 | Vừa | Ô chữ dạng tổ hợp (NFD) bị báo xung đột 409 | Đã sửa |
| TL-80 | Cao | Quay lui VPS: static mới chạy trên server cũ | Đã sửa quy trình: `collectstatic --clear`; quay lui và tiến lại đạt ở lượt phát hành 09.10 (#134) |
| TL-81 | Cao | Phát hành: code cũ chạy trên schema mới cho tới `up -d` | Đã sửa quy trình: dừng mọi app trước `migrate`; áp ở lượt phát hành 09.10 (#134) |
| TL-82 | Vừa | Postgres trên VPS ghi nguyên câu UPDATE khi trùng mã đơn | Đã sửa cấu hình VPS 09.10: `log_min_error_statement=panic` (#134) |
| TL-83 | Vừa | `kiem_tra_du_lieu` tốn bộ nhớ ở 100.000 dòng | **Mở** — tạm chạy trong container riêng (đã dùng 09.10); chưa đọc theo lô |
| TL-84 | Vừa | `up -d` theo README tạo lại container DB khi `.env` đổi | Đã sửa quy trình: `up -d --no-deps`; áp ở lượt phát hành 09.10 (#134) |
| TL-85 | Vừa | `BANGTINH_GOC` gõ sai thì CRM chạy DEBUG=True | Đã sửa quy trình: `check --deploy --fail-level WARNING` cho CRM và ERP; áp ở lượt phát hành 09.10 (#134) |
| TL-86 | Nhẹ | Tóm tắt Lên đơn chỉ có một câu lỗi chung | Đã sửa |
| TL-87 | Nhẹ | Sale staff bấm "Toàn bộ" vẫn chỉ thấy đơn của mình | Đã sửa |
| TL-88 | Vừa | Số dòng ở thư mục CRM lớn hơn số dòng có nội dung | Không sửa mã |
| TL-89 | Nhẹ | Nút Thống kê KN CRM của nguồn Sale/MKT | Đã sửa |

### 4.3 TL-90 → TL-112: đợt P0, rà sau gộp, lượt sửa 15.10

| Mã | Mức | Lỗi | Trạng thái |
|---|---|---|---|
| TL-90 | Hạ tầng | Fixture và dữ liệu mẫu thiếu 4 vai (Giám đốc, CSKH, Leader/Manager Vận đơn) | Đã sửa #118 |
| TL-91 | S2 | Giám đốc, Kế toán gọi thẳng đường ghi: 403 không có nhật ký; Giám đốc vào được form Tài liệu | Đã sửa #127 (P0-2) |
| TL-92 | S2 | Báo cáo tổng hợp bản cũ cộng lẫn USD với CAD | Đã sửa #119 (P0-4) |
| TL-93 | S2 | `/quan-tri/` không bị khoá sau 5 lần sai | Đã sửa #121 (P0-8) |
| TL-94 | S1 | Admin duy nhất tự hạ cấp được, hệ thống mất hết Admin | Đã sửa #125 (P0-9) |
| TL-95 | S2 | Chọn được trưởng nhóm bộ phận khác | Đã sửa #125 |
| TL-96 | S2 | Manager mất bộ phận nhận danh sách rỗng thay vì 403 | Đã sửa #125 |
| TL-97 | S2 | Phục hồi hỏng giữa chừng để dở dữ liệu | Đã sửa #123 (P0-15) |
| TL-98 | S2 | `do_hieu_nang` chạy được khi DEBUG tắt và ghi dòng thật | Đã sửa #116 (P0-16) |
| TL-99 | S2 | Launcher vẫn mở trình duyệt khi `migrate` lỗi | Đã sửa #115 (P0-17); kiểm tay trên Windows chưa làm |
| TL-100 | Vừa | Lời báo mất mạng ở Lên đơn bị tra khách xoá oan | Đã sửa #128 |
| TL-101 | S3 | Màn Cột đổi kiểu cột bị từ chối ra 500 | Đã sửa #133 (`fc938a7`) |
| TL-102 | S3 | `locustfile.py` sửa vận đơn thật, lên đơn thật | Đã sửa #133 (`cbe3b50`) |
| TL-103 | S3 | Danh sách quyền hiện quyền đã thu; thu lần hai ghi đè | Đã sửa #133 (`3e48a8c`) |
| TL-104 | S3 | Gửi form thường vào đường JSON ra 500 | Đã sửa #133 (`64ca888`) |
| TL-105 | S3 | Phục hồi xong báo "tác vụ kẹt" nhầm | Đã sửa #133 (`ffcdc99`) |
| TL-106 | S3 | Manager mất bộ phận: log ERROR, 403 không nhật ký, lưới nhận HTML, không có Đăng xuất | Đã sửa #133 (`b6893aa`) |
| TL-107 | S3 | Bỏ cột bị từ chối, mở lại ra 405 | Đã sửa #133 (`ad58859`) |
| TL-108 | S3 | Nhật ký khoá tạm bị lược chữ, ghi lặp | Đã sửa #133 (`cd0f39c`) |
| TL-109 | S2 | Nút Thống kê trên lưới mất `nguon` | Đã sửa #133 (`a37ac24`) |
| TL-110 | S2 | Áp dụng ở Thống kê mất bộ lọc lưới | Đã sửa #133 (`211d41d`) |
| TL-111 | S4 | Kho chứng từ 403 không có nhật ký | Đã sửa #133 (`36f8b4d`) |
| TL-112 | S3 | `locustfile_kn_crm.py` sửa ô, định dạng, dán, xoá trên dòng thật (chỉ thêm dòng là `PERF-*`) | **Mở** (mới 15.10) |

### 4.4 TL-113 → TL-124: rà lại 27 mã cũ (15.10.2026)

Chi tiết, bằng chứng chạy và cách sửa đề xuất: `docs/kiem-chung-ra-27-ma-cu-20261015.md` mục 3, 5.

| Mã | Mức | Lỗi | Trạng thái |
|---|---|---|---|
| TL-113 | S1 | Sau khi tự lưu, lưới bỏ so phiên bản khối: dán vắt khối mất một giá trị mà vẫn "Đã lưu" | **Mở** |
| TL-114 | S3 | Mốc trả về khi lưu là mốc cả bảng: sửa của người khác ngay trước lượt lưu bị nuốt tới khi tải lại | **Mở** |
| TL-115 | S3 | Sửa SĐT cho trùng dòng khác: ô Trùng của dòng kia không cập nhật | **Mở** |
| TL-116 | S3 | Manager Sale thấy ít dòng vận đơn hơn Leader Sale (0 nếu tự chưa lên đơn) | **Mở** — chờ chủ dự án chốt phạm vi |
| TL-117 | S3 | Sale Leader/Manager chưa lên đơn: trang chủ "Bảng 0" mà có dòng, không mở được lưới | **Mở** — cùng gốc TL-116 |
| TL-118 | S3 | Tính lại cột N+1 `TableDef`, chậm khoảng 14 lần | **Mở** |
| TL-119 | S4 | Lưu gặp 5xx thì lời báo của đường đọc; deadlock ra 500 HTML | **Mở** |
| TL-120 | S4 | Lọc `1e200000` ra 400 HTML, lưới đứng "Đang tải…" | **Mở** |
| TL-121 | S4 | `moi-nhat/` trả `tinh_lai.total` của cả bảng | **Mở** |
| TL-122 | S4 | Route `xoa-cot/`, `them-cot/` cũ còn sống | **Mở** |
| TL-123 | S4 | Bỏ cột chữ thường vẫn tính lại cả bảng | **Mở** |
| TL-124 | S4 | Bộ kiểm tải AC-10.8 gọi đường cũ, không chạy được trên lưới mới | **Mở** — cùng tệp TL-112 |

## 5. Lỗi chưa xong theo mức nghiêm trọng

| Mức | Mã | Trạng thái | Việc tiếp theo |
|---|---|---|---|
| S1 | TL-113 (+ phần còn lại TL-14) | Mở | Đợt sửa A: giữ so phiên bản khối sau khi tự lưu |
| S2 | TL-32 | Mở | Đợt sửa A: `_normalise` nhận ngày kèm giờ |
| Vừa | TL-83 | Mở | Sửa `kiem_tra_du_lieu` đọc theo lô; làm được ở máy ảo. Tạm thời chạy bằng `docker compose run --rm` |
| S3 | TL-04, TL-10, TL-114 | Mở | Đợt sửa A (sai số liệu) |
| S3 | TL-06, TL-09, TL-11, TL-12, TL-20, TL-25, TL-115, TL-118, TL-112 | Mở | Đợt sửa B |
| S3 | TL-116, TL-117 | Mở | Chờ chủ dự án chốt phạm vi vận đơn của Sale Leader/Manager |
| S4 | TL-08, TL-19, TL-24, TL-26 → TL-31, TL-33, TL-119 → TL-124 | Mở | Đợt sửa C (công cụ, tài liệu) |
| — | TL-71 | Mở | Bài e2e chập chờn: chẩn đoán đã có trong bài, chờ lần tái diễn có ngăn xếp |
| Vừa | TL-88 | Không sửa | Sổ lỗi ghi "không sửa mã" (10.10); xem lại nếu chủ dự án muốn đổi cách đếm |

## 6. Các đợt kiểm thử trước đây

| Ngày | Đợt | Lỗi ghi | Biên bản |
|---|---|---|---|
| 05–07.09 | Rà lưới HTMX cũ: phân quyền, đồng thời, tiền, hết phiên | TL-01 → TL-36 | `docs/test-log.md` mục "Lỗi theo thứ tự nghiêm trọng" |
| 16.09 | Kiểm tải 300.000 dòng, 10 người | — | `docs/kiem-chung-300k-10-nguoi-20260916.md` |
| 18–22.09 | VPS đầu tiên, lọc cột, Báo cáo tổng hợp, dữ liệu giả | TL-41 → TL-58 | `docs/test-log.md` các mục 18.09 → 22.09 |
| 23.09–07.10 | Phản hồi chủ dự án, CI, Báo cáo tổng hợp | TL-60 → TL-75 | `docs/test-log.md`; `docs/kiem-chung-*-202609*.md`, `-202610*.md` |
| 06.10 | Săn lỗi 10 hướng (bảo mật, đồng thời, đột biến, fuzz, tiền, gõ tiếng Việt…) | Ghi ở từng biên bản | `docs/kiem-chung-san-loi-*-20261006.md` |
| 08.10 | Kiểm toàn diện `Staging` `450b6da`; diễn tập phát hành VPS | TL-76 → TL-85 | `docs/kiem-chung-staging-len-main-20261008.md`, `docs/kiem-chung-dien-tap-phat-hanh-staging-20261008.md` |
| 09.10 | Phát hành `e979323-main-r2` lên VPS: diễn tập trên dữ liệu phục hồi, quay lui rồi tiến lại, 15 phút theo dõi | Đóng TL-80/81/82/84/85 | `docs/kiem-chung-phat-hanh-vps-20261009.md` (#134) |
| 10–12.10 | Phản hồi local; Thống kê CRM | TL-86 → TL-89 | `docs/kiem-chung-tl89-thong-ke-lien-ket-20261012.md` |
| 13.10 | Kế hoạch kiểm thử toàn diện (lộ trình P0/P1/P2) | — | `docs/08-ke-hoach-kiem-thu-toan-dien.md` (#113) |
| 14.10 | CI `Staging` sau gộp KN OMS; đợt P0: 16 PR, bài đỏ trước sửa sau, gộp `Staging` | TL-90 → TL-104, TL-100 | `docs/kiem-chung-gop-kn-oms-staging-20261014.md`, `docs/kiem-chung-p0-14-het-phien-20261014.md`, `docs/kiem-chung-gop-p0-staging-20261014.md` |
| 14.10 | Rà sau gộp: gộp thử 16 PR, rà ngữ nghĩa, diễn tập chặng 2 bằng máy | TL-105 → TL-111 | `docs/kiem-chung-p0-ra-soat-sau-gop-20261014.md` |
| 15.10 | Lượt sửa 11 lỗi và biên bản tổng hợp này | TL-101 → TL-112 | Tệp này |
| 15.10 | Rà lại 27 mã cũ trên mã hiện tại: 7 hết, 20 còn, 12 lỗi mới | TL-113 → TL-124 | `docs/kiem-chung-ra-27-ma-cu-20261015.md` |

## 7. Việc ghi lại, chưa cấp mã

Thấy khi làm lượt 15.10, ngoài phạm vi đã duyệt; không đổi hành vi hôm nay:
- CORE-20: tên đăng nhập có khoảng trắng thì dòng "Đăng nhập thất bại" không gắn được người (dòng khoá thì đã gắn đúng
  từ TL-108).
- Vài đường 403 không có dòng Từ chối (có từ trước, rà đối kháng 15.10 chỉ ra): các đường JSON chỉ đọc của lưới
  (`du-lieu`, `lich-su`, `quyen-dong`, `dong-bo`; đã ghi ở P1-22 của `docs/08`); `GET /van-don/phan-cong/?row=` với dòng
  ngoài phạm vi; Sale/CSKH mở `/van-don/chi-tiet/<pk>/` của dòng không được giao. Sửa gốc: mỗi chỗ gọi
  `record_denied` trước khi ném, kèm bài "đúng một dòng".
- Hai lượt thu cùng một quyền chạy song song trong vài mili giây vẫn thu được hai lần (lượt thứ hai tuần tự thì đã 404
  từ TL-103). Sửa gốc: `revoke` khoá dòng rồi kiểm lại trong giao dịch.
- Lượt hỏi 8 giây của lưới gặp lỗi "chưa gán bộ phận" vẫn báo "Quyền xem đã thay đổi." (lời đúng hiện khi cuộn hay lưu).
- Kho chứng từ (cờ tắt): vai bị cấm gửi thân hỏng nhận 400 trước khi kiểm quyền.
- Trường hợp hiếm: khung CRM đang mở trang tiến độ tác vụ, người bị gỡ bộ phận đăng nhập lại ở tab khác, thì lượt hỏi
  2 giây của trang tiến độ ghi một dòng Từ chối mỗi lần.

## 8. Chưa kiểm

- Chặng 2 kiểm tay ở local (`KN JSC.bat` hay `./scripts/cap-nhat-local.sh`): chưa ai làm cho đợt P0 lẫn lượt này.
- 13 AC kiểm tay (`docs/04` cột "Thủ công") và 18 AC đang hoãn.
- Phần cần VPS hay Windows: kiểm tay launcher TC-1 → TC-6 (TL-99); diễn tập tắt worker giữa chừng. TL-80 → TL-85 đã
  đóng ở lượt phát hành 09.10 trừ TL-83 (biên bản `docs/kiem-chung-phat-hanh-vps-20261009.md`).
- `scripts/kiem-thu-statistics-labels.cjs` và các script trình duyệt khác chạy tay, không chạy ở lượt này.

## 9. Chặng 2 cho lượt sửa này

Bật bằng `KN JSC.bat`, mở KN ERP `127.0.0.1:8020` và KN CRM `127.0.0.1:8021`:

| Bước | Tài khoản | Làm | Kỳ vọng |
|---|---|---|---|
| 1 | `vd.staff` | Mở lưới Vận đơn, bấm Tôi, gõ Tìm, bấm Thống kê | Mở thống kê Vận đơn, vẫn lọc Tôi và Tìm (TL-109) |
| 2 | `vd.staff` | Ở Thống kê đổi Từ ngày, bấm Áp dụng; rồi chọn nguồn Tổng hợp, Áp dụng | Lần đầu giữ lọc, có dòng "Đang lọc theo lưới"; lần hai bỏ lọc (TL-110) |
| 3 | `sale.manager` | Màn Cột của một bảng Sale: bỏ cột khoá, rồi F5 | Lời đỏ ở màn Cột, F5 không ra 405 (TL-107) |
| 4 | `sale.manager` | Sửa một cột chữ có giá trị "abc" sang Số nguyên | Lời đỏ trong khung "Chưa lưu được", cột không đổi (TL-101) |
| 5 | `sale.staff`, `quantri` | Sai mật khẩu 5 lần, thử thêm 2 lần; `quantri` mở Nhật ký, lọc "Đổi quyền", tìm `sale.staff` | Đúng một dòng "Khoá tạm 15 phút do đăng nhập sai 5 lần" (TL-108) |
| 6 | `quantri` | Ở `/quan-tri/` gỡ bộ phận của `vd.manager`; `vd.manager` đăng nhập, mở CRM `/` | Trang 403 có nút Đăng xuất, bấm được; Nhật ký có dòng Từ chối (TL-106). Gán lại bộ phận sau khi thử |
| 7 | `sale.manager` | Cấp rồi thu một quyền bảng, nhìn danh sách quyền | Quyền đã thu không còn trong danh sách (TL-103) |
