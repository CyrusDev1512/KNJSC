# Kiểm chứng — Rà lại 27 mã lỗi cũ TL-04 → TL-33 trên mã hiện tại (15.10.2026)

Chủ dự án: "rà lại 27 mã cũ đi". 27 mã ghi ngày 05–07.09.2026, phần lớn trên lưới HTMX cũ (`bang-tinh.js`,
`bang-tinh-o.js`, `_o.html`). Lưới đó đã thay hẳn (ADR-021, 027), nên biên bản tổng hợp 15.10 xếp chúng là "Cần rà lại".
Lượt này trả lời một câu cho từng mã: **hậu quả mà mã mô tả còn xảy ra trên mã hiện tại không**. Chỉ rà, **không sửa mã
nào**; cách sửa đề xuất ở mục 5 chờ chủ dự án duyệt (AGENTS.md mục 1).

| Mục | Giá trị |
|---|---|
| Mã nguồn | `Staging` `2d5fb04` (sau khi gộp #132 → #135) |
| Môi trường | Máy ảo web: PostgreSQL 16, venv dự án, Chromium qua Playwright 1.56; 4 nhân. Không có VPS, không có Windows |
| Cách làm | Workflow 15 agent: 7 nhóm theo vùng mã, mỗi nhóm một agent rà và một agent phản biện cố bác từng kết luận, rồi một agent soát đủ 27 mã, gỡ chỗ bất đồng và kiểm lại lỗi mới. 979 lượt dùng công cụ, 1 giờ 52 phút |
| Bằng chứng | Bài nháp pytest và Playwright chạy thật, mỗi agent một CSDL kiểm thử riêng. Bài nháp nằm ở `app/_ra_soat_tmp/` (loại khỏi git) và ảnh ở `storage/ra27/` (không vào git). Không tệp nào được git theo dõi bị sửa (`git status` sạch) |
| Tự kiểm lại sau workflow | Ba kết luận nặng nhất, chạy lại bằng tay ở mục 6 |

## 1. Tóm tắt

| Kết luận | Số mã | Mã |
|---|---|---|
| Hết trên lưới mới, **đóng** | 7 | TL-05, TL-07, TL-15, TL-16, TL-17, TL-21, TL-22 |
| Còn một phần, **mở** | 12 | TL-04, TL-06, TL-08, TL-09, TL-11, TL-14, TL-19, TL-20, TL-24, TL-26, TL-31, TL-33 |
| Còn nguyên, **mở** | 8 | TL-10, TL-12, TL-25, TL-27, TL-28, TL-29, TL-30, TL-32 |
| Lỗi mới bắt gặp khi rà (có bằng chứng chạy) | 12 | TL-113 → TL-124 |

Hai điều quan trọng nhất:
- **TL-113 (S1, mới):** dán một vùng vắt qua ranh giới khối 100 dòng có thể **mất một giá trị mà lưới vẫn báo "Đã lưu"**.
  Điều kiện: vừa tự lưu xong và người khác vừa đổi thứ tự dòng. Đây cũng là phần còn lại của TL-14.
- **TL-22 (S1 cũ) đã hết:** vòng "làm lại sau deadlock" của PR #21 không có trên `Staging`. Hiện `luu-json/` gặp deadlock
  thì huỷ trọn lượt, lưới tự gửi lại cùng mã thao tác và máy chủ ghi thật.

## 2. Từng mã

Mức theo thang của `docs/test-log.md`: S1 lộ quyền hay mất/sai dữ liệu âm thầm · S2 gặp thường xuyên hay trang trắng ·
S3 khó chịu, có đường vòng · S4 kỹ thuật, người dùng không thấy.

### 2.1 Đóng: hết trên lưới mới (7)

| Mã | Mức cũ | Vì sao hết | Bằng chứng chạy |
|---|---|---|---|
| TL-05 | S2 | Đường cũ `khoi-phuc-dong/` còn định tuyến (`crm/urls.py:66`) nhưng chỉ trả 409, không ghi gì. Khôi phục giờ là `restore_rows` qua `luu-json/`, chỉ Admin (`crm/services/row_mutations.py:21,35`), có kiểm thêm `all_objects.in_scope` và `can_delete_record` | 11 vai không phải Admin đều nhận 403, mỗi lần một dòng Từ chối, dòng vẫn ở trạng thái đã xoá. Đường cũ 12/12 lượt trả 409. Admin khôi phục dòng của bảng khác: 403. Admin chiều được phép: 200 |
| TL-07 | S3 | Hoàn tác đi qua `working.travel` rồi `luu-json/`, có so CAS theo giá trị cũ. Ô đã bị người khác đổi thì máy chủ trả 409 và lưới mở hộp Đối chiếu. Lượt hỏi đã kéo giá trị mới về thì trình duyệt chặn ngay (`master-working-copy.js:62-67`) | Hai tab Playwright. Ctrl+Z trước lượt hỏi: 409, CSDL giữ `B-sua`, hộp ghi "Hiện tại: B-sua". Ctrl+Z sau lượt hỏi: báo "Không thể hoàn tác…", không gửi gì. Hoàn tác định dạng và lượt 2 ô cũng 409 |
| TL-15 | S3 | `dinh-dang/` cũ chỉ trả 409. Định dạng ô đi qua `luu-json/`, kiểm phạm vi và quyền sửa cho cả lượt: một ô ngoài phạm vi là cả lượt 403, có nhật ký, không ô nào đổi | Lượt hỗn hợp (trong và ngoài phạm vi, dòng chăm sóc không sửa được, CEO): 403, thêm 1 dòng Từ chối, kiểu ô không đổi. Chromium: lưới hiện "Lỗi lưu" kèm Thử lại và Bỏ bản nháp |
| TL-16 | S3 | Mọi lượt ghi lưới khoá dòng bằng `SELECT … ORDER BY pk FOR UPDATE` rồi đọc lại dưới khoá (`master_grid_service.py:253-260`). `record_service.update_cell` cũ vẫn ghi cả dòng, nhưng ngoài bài kiểm không còn chỗ nào gọi | Hai luồng POST `luu-json/` thật vào hai ô của cùng dòng: luồng sau chờ 1,58 s, dòng giữ cả hai ô. Hộp Chi tiết xen kẽ `luu-json/`: giữ đủ `ghi_chu`, `so_luong` và kiểu ô |
| TL-17 | S3 | Phản hồi `luu-json/` đọc lại dòng từ CSDL sau khi ghi và trả cả dòng, gồm cột tính sẵn và Loại tiền (`master_grid_service.py:315,340`). Lưới vẽ lại ngay | Chromium: `gia_dv` đổi `25.00` → `75.00` 13–18 ms sau phản hồi, không cần lượt hỏi. Đổi Quốc gia thì phản hồi mang Loại tiền CAD. (Ô Trùng của *dòng khác* không vẽ lại: lỗi khác, ghi thành TL-115) |
| TL-21 | S3 | Không còn tiêu đề cột nào màu `#b8952b`. Bảng ngoài vận đơn 404 ở CRM (ADR-040); lưới vận đơn dùng tiêu đề kem theo DESIGN.md; ERP dùng xanh | `getComputedStyle` trên mọi bảng mẫu ERP và lưới `van_don`: 0 tiêu đề có nền, chữ hay viền `#b8952b`. `/bang-tinh/bao_cao_mkt/` 404 |
| TL-22 | S1 | Vòng `luu()` làm lại sau deadlock của PR #21 (`9989188`, chỉ có trên `UI-SOLAR-PUNK`) không có trên `Staging`; `luu-o/` chỉ trả 409. `luu-json/` là một giao dịch atomic không có vòng thử; phản hồi vẽ từ dữ liệu đọc lại | Ép deadlock lần đầu: 500, 0 biên nhận. Gửi lại cùng mã thao tác: 200, `changed=2`. Lần ba: `replayed`. Chromium: `luu-json` [500, 200], không báo "Đã lưu" sau lượt 500. Chạy song song 14 s với tính lại nền: 0 deadlock, 0 dòng lệch |

### 2.2 Mở: còn một phần (12)

| Mã | Mức mới | Phần đã hết | Phần còn | Bằng chứng chạy |
|---|---|---|---|---|
| TL-04 | S3 (cũ S2) | Lỗi 500: commit `0c15ecf` (06.10, AC-10.16) bắt thêm `ValidationError` (`forms_builder/query.py:159`) | Gõ `1.000.000`, `1,5` hay ngày `DD/MM/YYYY` thì **bộ lọc bị bỏ qua lặng lẽ**: chip và ô lọc vẫn hiện chữ đã gõ, Xuất tệp ra cả bảng. Ô nhập đọc được `1.000.000` (`parse_money`) nhưng ô lọc thì không | Chromium, lưới `van_don`: Từ = `1.000.000` ra "3 dòng khớp bộ lọc" (đúng là 1), chip "Giá tiền ≥ 1.000.000". ERP lọc Doanh thu `2.000.000` ra 2 dòng (đúng là 1). Gõ không dấu chấm thì đúng |
| TL-06 | S3 (cũ S2) | Một lỗi 403 hay 500 đơn lẻ không còn làm kẹt: `busy` gỡ trong `finally`, thanh trên "Lỗi lưu", lượt hỏi vẫn chạy, Thử lại lưu được, 500 tự thử lại 4 lần. Lưới không còn dòng trống | **Lỗi kép:** `luu-json` 403, rồi lượt kiểm `quyen-dong/` hỏng một lần (500 hay đứt mạng). Khi đó `catch` gọi `clearAccess` (`master-grid.js:892`), lưới đặt `unavailable` vĩnh viễn: không hỏi, không lưu, bỏ cả nháp trên dòng còn quyền, tới khi tải lại trang | `quyen-dong/` hỏng một lần rồi máy chủ lành: sau 18 s có 0 lượt `moi-nhat/`, Ctrl+S gửi 0 lượt `luu-json`, nháp dòng còn quyền mất |
| TL-08 | S4 (cũ S3) | Toast "Có dữ liệu mới" và tải lại cả bảng sau khi tự lưu: sửa 18.09 (`luu-json` trả `latest`, AC-11.40). Giá trị bị 400 vẫn giữ | Nhánh `moi-nhat/` không kiểm `busy` hay thế hệ sau `await` (`master-grid.js:1410-1430`). Lượt hỏi đọc mốc trước khi lượt lưu commit mà về sau thì ghi đè mốc mới, gây hai lần nạp nhẹ thừa. Không có toast | Tự lưu rồi chờ 18 s: 2 lượt `moi-nhat/`, 0 lượt `du-lieu/`. Ép `moi-nhat/` trễ 2,5 s: `quyen-dong/` và `du-lieu/?offset=0` chạy lúc 2,5 s và 8,0 s |
| TL-09 | S3 | Lưới CRM: `query.build` thêm `pk` cho bảng vận đơn (`query.py:248-252`) và khối 100 dòng luôn có `pk` | **Bảng dữ liệu ERP** (`/bang/<mã>/`, kể cả `?dang=tho`) với bảng ngoài vận đơn vẫn chỉ `order_by` một cột (`query.py:225-233`) rồi phân trang OFFSET: dòng lặp hoặc thiếu khi lật trang | 200 dòng cùng giá trị: sắp Trạng thái lặp 2 thiếu 2; sắp cột số JSON lặp 43 thiếu 43; SQL `ORDER BY val_status LIMIT 25 OFFSET 25` không có `pk`. CRM 252 dòng qua 3 khối: 0 lặp, 0 thiếu |
| TL-11 | S3 | KN CRM (`4b19814`, AC-10.24): trang chủ, thư mục, Nhập tệp, Cấp quyền đều đếm bằng `in_scope` | **KN ERP** vẫn đếm bằng `record_count_scope` (`forms_builder/managers.py:104`): bảng thường đếm cả dòng đã xoá và dòng ngoài phạm vi. Trên cùng khối Tổng quan hai số lệch nhau, lộ số dòng ngoài phạm vi | Tổng quan ERP: cột Số dòng ghi 4 với Staff, Leader và Manager, trong khi phạm vi thật là 1, 2, 3 và đầu khối ghi "1 dòng". `/bang/` của Manager ghi 3, thật là 2 |
| TL-14 | S1 (theo TL-113) | Cơ chế cũ (trang 100 dòng, dán vượt trang tạo dòng mới) đã hết: dán 150 dòng từ dòng 60 ghi đúng dòng 60–209 trong một lượt, dán vượt cuối bảng bị chặn kèm lời báo | Dán vắt ranh giới khối có thể ghi sai khi các khối đệm lệch nhau. Gốc lỗi ghi thành **TL-113**; sửa TL-113 là đóng TL-14 | Xem TL-113 |
| TL-19 | S4 (cũ S2) | Đường lưu ô: 400 thật khi gõ hay dán sai kiểu cho ra "Lỗi lưu", CSDL không đổi | Hai đường khác của lưới bị máy chủ từ chối mà thanh trên vẫn "Đã lưu": Bỏ chi tiết (`clearDetails`, `master-grid.js:1003-1013`) và Admin xoá dòng (`travelDeleted`). Lời báo đỏ vẫn hiện trên lưới và dữ liệu giữ nguyên, nên chỉ là chữ trạng thái sai | Chromium, lỗi thật của máy chủ: `bo-chi-tiet` 409/403 cho chuỗi "Đang lưu" → "Đã lưu", chi tiết vẫn 2 dòng; xoá dòng 409 cũng ra "Đã lưu", dòng còn trên lưới |
| TL-20 | S3 (cũ S2) | Lời báo không còn bị giấu: `#mg-message` đỏ nằm trong khung nhìn ở chế độ thường, toàn màn hình và 390 px | Ô sai không được đánh dấu (không lớp, không `aria-invalid`, không `title`). Lời báo chỉ chỗ bằng mã CSDL ("Dòng #11" trong khi ô ở hàng 5) và mã cột. Chữ "Lỗi lưu" không đổi màu và bị ẩn ở màn ≤ 720 px (`crm-frame.css:301`) | Chromium: ô sai có nền `rgb(255,253,248)` giống ô bên cạnh, `aria-invalid` null. Lời báo "Dòng #11, cột mua_lai" |
| TL-24 | S4 (cũ S3) | Lỗi 500 rời rạc khi trùng lúc tính lại: mọi đường ghi lưới qua `luu-json/`, khoá theo `pk` tăng dần cùng chiều với `resync_table` | (1) Chú thích `forms_builder/models.py:601-603` sai: `UPDATE … FROM VALUES` khoá theo thứ tự heap, không theo `pk`; vô hại vì mọi chỗ gọi đều khoá trước. (2) `luu-json/` không bắt `OperationalError`: deadlock thật ra 500 HTML (ghi thêm ở TL-119) | `EXPLAIN` cho Hash Join + Seq Scan. Ép deadlock thật: 500 `text/html` sau 1,05 s. Chạy song song tính lại: định dạng, dán, xoá chỉ ra 200 hoặc 409 |
| TL-26 | S4 | Khi các lô đều nhau và không chờ khoá, lô lỗi đầu tiên chỉ để thừa khoảng một lô mỗi luồng (4/10 lô, 0,37 s) | `Executor.map` nộp mọi lô từ đầu (`table_service.py:424-432`). Lô trước chậm (chờ khoá dòng) thì luồng rảnh chạy hết các lô sau dù một lô đã lỗi | Giữ khoá dòng đầu 3 s, lô #1 ném lỗi: 10/10 lô bắt đầu, 9 lô commit, tác vụ FAILED sau 3,17 s |
| TL-31 | S4 | Docstring lệch mất cùng hàm `cell_url` | AC-11.36 (`docs/04:320`) và ADR-016 (dòng 41–44) còn nhắc `cell_html`, `reverse('bang_tinh_o')`, ngân sách 25 truy vấn. Bài `test_url_o_ghep_chuoi_khop_reverse` giữ tên cũ, kiểm `saveUrl`, không có docstring mã AC (trái quy tắc bắt buộc 10) | `grid_service` không còn `cell_url`/`cell_html`; docstring bài tên cũ là `None` |
| TL-33 | S4 | `xfail` đã bỏ ở `d85315e` (K24); hai bài đạt trên 50.000 dòng | Nửa CRM của `test_bang_tinh_50000_dong_co_loc_duoi_2_giay` chỉ đo khung trang (6 truy vấn, 0 lệnh đọc dữ liệu); đường đọc thật `du-lieu/` tốn 14 truy vấn, không được bấm giờ. test-log và kanban còn ghi `xfail` | `/bang-tinh/` có lọc và `?trung=1`: 6 truy vấn, 27–49 ms; `du-lieu/` 14 truy vấn, 151–303 ms |

### 2.3 Mở: còn nguyên (8)

| Mã | Mức mới | Còn gì | Bằng chứng chạy |
|---|---|---|---|
| TL-10 | S3 | Tiền và số thập phân lưu trong JSON dạng chuỗi (`record_service.parse_value`; `waybill_service.totals` ghi `str`). `apply_sort` dùng `order_by('data__<cột>')` nên so theo chuỗi; `JSON_RANGE_TYPES` (`query.py:46`) không có tiền/số thập phân nên lọc Từ/Đến bị đổi thành so bằng. Có ở cả lưới CRM lẫn ERP. Bài có sẵn dùng giá trị cùng độ dài nên che lỗi | Chromium, `van_don`: sắp tăng "Số tiền thanh toán" ra `['1234.5','50','999']`; lọc Từ 100 ra "0 dòng khớp bộ lọc". ERP CPQC sắp `['1234.50','50','999']`, ≥ 100 rơi về so bằng |
| TL-12 | S3 (cũ S4) | `delete_rows` qua `luu-json/` (chỉ Admin) vẫn lặp `delete_record` từng dòng: khoảng 19 truy vấn mỗi dòng (`row_mutations.py:52-53`); khôi phục khoảng 18. Lượt 2.000 dòng giữ khoá khoảng 50 s; nginx VPS không đặt `proxy_read_timeout` (mặc định 60 s) nên VPS 2 nhân dễ trả 504. Không mất dữ liệu: Thử lại phát lại theo biên nhận | Xoá 2.000 dòng: 38.027 truy vấn, 51–52 s. Khôi phục 2.000 dòng: 36.025 truy vấn, 48 s |
| TL-25 | S3 | `schedule_resync` (`table_service.py:472`) tạo một tác vụ mỗi lần gọi, không gộp với tác vụ đang chờ. Bỏ 5 cột ra 5 tác vụ; bảng nhỏ thì tính lại 5 lần ngay trong yêu cầu. Giá trị cũ chỉ xảy ra khi worker có hơn một tiến trình (compose local có, VPS concurrency 1 không) | `xoa-cot/` 5 cột: 5 tác vụ. ERP bỏ 5 cột: 5 tác vụ chờ. 3 lần sửa công thức: 3 tác vụ chờ. Hai worker, tác vụ cũ thử lại sau deadlock: 6/8 dòng giữ công thức cũ dù cả hai tác vụ Xong |
| TL-27 | S4 | Bước tính lại của `do_hieu_nang` chạy trên dữ liệu đã đồng bộ nên không ghi dòng nào; cột truy vấn chỉ đếm 3 lệnh vì lô chạy ở luồng khác. Chạy thật trên mã hiện tại thì lệnh dừng ở `CommandError` 409 tại `luu-o/` trước khi tới bước tính lại, không ra báo cáo | 2.400 dòng: 0 dòng đổi `updated_at`, `n_tup_upd` +0, 3 truy vấn (chạy tuần tự thì 2.418). `call_command`: "POST /bang-tinh/van_don/luu-o/ trả 409" |
| TL-28 | S4 | Mốc `moi-nhat/` tính trên cả bảng là cố ý (AC-10.21, `70fe0db`), phản hồi không có giá trị ô. Nhưng docstring view (`crm/views.py:353`), docstring bài `test_moi_nhat_tra_moc_trong_pham_vi`, AC-11.26 (`docs/04:310`) và `docs/test-log.md` vẫn ghi "trong phạm vi". Chỉ lệch tài liệu | Mốc của `staff_sale_1` tăng khi dòng ngoài phạm vi đổi; phản hồi chỉ có 4 khoá; `staff_mkt` 404 |
| TL-29 | S4 | Chạy `scripts/kiem-tai-kn-crm.*` (gunicorn) thì không ai phục vụ tệp tĩnh ở local: không whitenoise, không `staticfiles_urlpatterns()`, không nginx. Lưới mới chạy hoàn toàn bằng JS nên trong lúc đó lưới không dùng được. Nginx VPS có, nhưng không chạm bước tái hiện này | gunicorn đúng chuỗi lệnh `kiem-tai-kn-crm.sh:17`: lưới 18/18 tệp tĩnh 404, ERP 11/11 tệp 404; runserver tất cả 200 |
| TL-30 | S4 | Script kiểm tải chạy `du_lieu_mau >/dev/null` mọi lần, kể cả với `--giu-du-lieu`: đặt lại mật khẩu, mở khoá và huỷ phiên 16 tài khoản mẫu, kể cả `quantri`. Rồi `seed_perf --xoa-cu` xoá cứng `PERF-*` và cả dòng gõ tay trong `perf_sale`. Không có cảnh báo; khoá DEBUG của P0-16 không chặn vì compose local chạy dev | Sau `du_lieu_mau`: GET `/` 302 về đăng nhập, mật khẩu riêng hết dùng được, `failed_login_count` về 0. `seed_perf --xoa-cu` xoá cứng dòng `GO-TAY-1` |
| TL-32 | S2 (cũ S4) | `_normalise` (`forms_builder/models.py:695`) đưa nguyên chuỗi vào `val_date`. Cột Ngày đã chặn giờ ở `parse_value`, nhưng `ALLOWED_TYPES` (`meaning.py:68`) cho **cột Ngày giờ mang nhãn Ngày** và màn Sửa cột nhận cấu hình đó. Từ đó: điền biểu mẫu có giờ ra 500; tạo hàng loạt hỏng cả lô; đổi kiểu cột ra 500; gán nhãn cho bảng lớn thì tác vụ FAILED. Không cấu hình mặc định nào như vậy, nhưng Manager tự dựng được qua giao diện | `POST /bang/lich_goi/cot/` (Ngày giờ, nhãn Ngày) 302; điền `2026-09-01T10:00` ra 500 `ValidationError`, 0 dòng; 6 dòng có 1 dòng kèm giờ thì 0 dòng vào; bảng lớn: tác vụ FAILED, 0/5 dòng có `val_date` |

## 3. Lỗi mới (TL-113 → TL-124)

Mỗi mã có bằng chứng chạy của ít nhất một nhóm và được agent soát kiểm lại; các lỗi trùng giữa nhóm đã gộp.

| Mã | Mức | Lỗi | Ở đâu | Tái hiện, số đo |
|---|---|---|---|---|
| TL-113 | **S1** | Sau khi tự lưu, lưới bỏ so phiên bản khối (`state.version=''` ở giao thức 1, tức mặc định vì cờ `CRM_OPT_READ` tắt). Khối tải sau không được so với khối đã đệm. Người khác đổi thứ tự dòng (sửa cột đang sắp hay lọc, xoá dòng) thì một dòng hiện hai lần; dán vắt khối ghi hai giá trị vào dòng đó, **mất một giá trị mà vẫn "Đã lưu"**. Sao chép và Xoá nội dung vắt khối dùng cùng `rowAt` (phần này chỉ đọc mã) | `static/js/master-grid.js:835` (`updateRows`), `:188` (chỉ gửi `version` khi khác rỗng), `:964-969` (dán theo `rowAt`); `master-working-copy.js` gộp ô trùng khoá `id:cột` không báo | `van_don` 600 dòng sắp theo Tên khách. Ngay sau một lượt hỏi, người khác đổi tên dòng thứ 550 cho nó lên đầu; A sửa một ô rồi tự lưu, chờ 9 s, cuộn tới dòng 250, dán 100 dòng. Kết quả: khối `offset=300` tải không kèm `version`, id 301 hiện hai lần, `luu-json` 200 với 99 ô, mất `K-049`, trạng thái "Đã lưu". Đối chứng không tự lưu: 409 "Dữ liệu đã đổi, chọn lại vùng dán.", 0 ô bị ghi. Chạy 3 lần (2 lần agent soát, 1 lần tự kiểm) |
| TL-114 | S3 | Phản hồi `luu-json` trả mốc của **cả bảng** làm "mốc của mình". Sửa của người khác xảy ra ngay trước lượt lưu của mình bị nuốt: lưới không bao giờ nạp, tới khi tải lại trang. CAS vẫn chặn ghi đè (409), không mất dữ liệu đã lưu | `crm/services/master_grid_service.py:342`; `master-grid.js:869`, `:1009`, `:1430` | Hai nhóm tái hiện độc lập, mỗi nhóm 2 lần: ô do B sửa vẫn giá trị cũ ở tab A sau 2 vòng hỏi (18–20 s), không có `du-lieu/` nào; A không tự lưu thì thấy trong ≤ 8 s |
| TL-115 | S3 | Sửa SĐT dòng A cho trùng (hay hết trùng) dòng B: ô Trùng của B trên lưới người sửa không cập nhật tới khi tải lại; phản hồi chỉ chứa dòng vừa sửa | `master_grid_service.py:315-340`; `crm/services/waybill_grid.py`; `master-grid.js:831-837` | Trùng (A, B) ngay sau lưu là `('2','')`, sau 17 s vẫn `('2','')`, tải lại `('2','2')`. Lưới người khác thì thấy đúng |
| TL-116 | S3 | Manager Sale thấy **ít dòng vận đơn hơn** chính Leader Sale của mình. Dòng vận đơn mang bộ phận `van-don`, nên vế "phạm vi bảng cũ" của Manager (lọc theo bộ phận `sale`) không khớp dòng nào, còn của Leader (lọc theo team người tạo) thì khớp. Thiếu phạm vi, không lộ. **Cần chủ dự án chốt ý định** | `orders/services/assignment_service.py:80-83`; `forms_builder/managers.py` (`in_scope`, `apply_scope`) | 4 đơn của 3 nhân viên Sale (2 team): `leader_sale_1` thấy [1, 3], `leader_sale_2` thấy [2, 4], `manager_sale` thấy [] (0 dòng), CEO thấy cả 4. Tự kiểm lại: đúng |
| TL-117 | S3 | Sale Leader/Manager chưa tự lên đơn: trang chủ KN CRM ghi "Bảng trong phạm vi 0" mà "Tổng số dòng" > 0; `/thu-muc/` 404, lưới 302, `du-lieu/` 403. Phạm vi *bảng* của Sale chỉ tính đơn hay chăm sóc của chính mình, phạm vi *dòng* thì có cả dòng của team. Cùng gốc TL-116 | `crm/services/tong_quan_service.py:59-74`; `forms_builder/managers.py:67-90` | `leader_sale_1` chưa có đơn riêng: ba ô số `['1','0','1']`; `TableDef.in_scope` không chứa `van_don` dù có dòng trong phạm vi |
| TL-118 | S3 | `resync_table` nạp lười `TableDef` theo từng dòng (N+1): tính lại cột chậm khoảng 14 lần | `forms_builder/models.py:583`; `table_service.py:393-397`, `197-202` (có từ `e14370e`) | 1.800 dòng: 1.813 truy vấn (1.800 lệnh đọc `tabledef`), 1.671 ms; gắn sẵn bảng thì 13 truy vấn, 104 ms. 10.000 dòng, 2 luồng: 9,3 s so với 0,67 s |
| TL-119 | S4 | Lưu gặp 5xx hay phản hồi không phải JSON thì lời báo là "Không tải được dữ liệu. Kiểm tra kết nối hoặc quyền truy cập." (lời của đường đọc). `luu-json/` không bắt `OperationalError` nên deadlock hay lock timeout ra 500 HTML. Lưới tự gửi lại và lưu được, không mất dữ liệu | `master-grid.js:64`; `crm/master_views.py:52-71` | Ép `luu-json` 500 HTML rồi sửa một ô: `#mg-message` như trên trong lúc "Lỗi lưu" (3 nhóm thấy) |
| TL-120 | S4 | Lọc khoảng với số mũ cực lớn (`1e200000`): `du-lieu/` và Xuất tệp trả 400 HTML; lưới đứng "Đang tải…" và báo sai lý do. Không còn đường nào ra 500 | `forms_builder/query.py:153-161` → `core/middleware.py` `DataLimitMiddleware` → `master-grid.js` `json()` | `?f_gia_tien__lon_bang=1e200000`: `#mg-count` "Đang tải…", `#mg-message` "Không tải được dữ liệu…". Số 16–17 chữ số vẫn 200 |
| TL-121 | S4 | `moi-nhat/` trả `tinh_lai.total` là số dòng của cả bảng (kể cả dòng đã xoá và ngoài phạm vi) cho mọi người thấy bảng; JS không dùng trường này | `master_grid_service.py:366-371`; `table_service.py:476-485` | Tác vụ tính lại đang chạy, `staff_sale_1` hỏi: `{'total': 3}` trong khi phạm vi là 1 |
| TL-122 | S4 | Endpoint cũ `bang-tinh/<mã>/xoa-cot/` và `them-cot/` còn định tuyến dù lưới mới không gọi; `xoa-cot` tính lại một lần cho mỗi cột | `crm/urls.py:67-68`; `crm/views.py:298-348` | Admin POST `xoa-cot/` với 5 cột: 200, sinh 5 tác vụ. Không file JS hay template nào gọi hai đường này |
| TL-123 | S4 | Bỏ một cột chữ thường (không nhãn, không công thức) vẫn tính lại cả bảng; bảng trên 2.000 dòng thì mỗi lần bỏ sinh một tác vụ nền | `table_service.py:227` (`add_column` ở dòng 108 thì có điều kiện) | Bỏ lần lượt 5 cột chữ không nhãn: 5 tác vụ chờ, không dòng nào đổi |
| TL-124 | S4 | Bộ kiểm tải AC-10.8 không chạy được trên lưới mới: `locustfile_kn_crm.py` gọi đường cũ (`/o/<pk>/`, `luu-o/`, `dinh-dang/`, `dong-moi/`) và bảng Sale/MKT bị ADR-040 chặn; `kiem-tai-kn-crm.sh` thiếu `set -e`. Cùng tệp với TL-112 | `tests/perf/locustfile_kn_crm.py:138-185, 246, 277-297`; `scripts/kiem-tai-kn-crm.sh:14` | HTML lưới có 0 liên kết `/o/<pk>/`; năm POST cũ đều 409; `perf_sale` 404. Phần Locust chỉ đọc mã (máy không cài locust) |

## 4. Cần chủ dự án

1. **Phạm vi vận đơn của Sale Leader và Sale Manager (TL-116, TL-117).** Hôm nay Manager Sale thấy 0 dòng vận đơn nếu tự
   mình chưa lên đơn, ít hơn Leader của mình. Leader hay Manager chưa lên đơn thì không mở được lưới dù trang chủ đếm có
   dòng. Ý định nên là gì: Manager thấy mọi đơn do người bộ phận Sale lên? Leader thấy đơn của team? ADR-020 ghi
   "Leader/Manager Sale giữ phạm vi hiện có"; ADR-033 bổ sung 10.10 cho họ giữ nút Tôi / Toàn bộ. Đây là đổi phân quyền
   nên không tự quyết.
2. **Duyệt cách sửa** ở mục 5 trước khi làm (AGENTS.md mục 1).

## 5. Cách sửa đề xuất (chưa làm)

Mỗi lỗi: bài đỏ trên mã hiện tại trước, sửa tối thiểu sau. Bài nháp của lượt rà dùng lại được làm bài đỏ. Không đổi
quyền hay nghiệp vụ ngoài TL-116/117 (chờ quyết), không migration, không thư viện mới.

**Đợt A: sai hay mất dữ liệu (S1, S2, và S3 sai số)**

| Mã | Cách sửa |
|---|---|
| TL-113 (+ TL-14) | Sau khi tự lưu, không xoá `state.version` ở giao thức 1. Hoặc giữ phiên bản mới do máy chủ trả, hoặc dọn bộ đệm khối và nạp lại cùng lúc, như lượt hỏi đang làm. Khối tải về mà phiên bản lệch thì từ chối lượt dán vắt khối bằng đúng lời đối chứng đang có ("Dữ liệu đã đổi, chọn lại vùng dán."). `working.stage` gặp hai ô trùng `id:cột` trong một lượt thì báo, không gộp lặng lẽ. Bài đỏ: Playwright dán vắt khối như mục 3 |
| TL-32 | `_normalise` cho `val_date`: nhận `date`/`datetime` và chuỗi ISO kèm giờ, lấy phần ngày; không đọc được thì `None`, không để `DateField` ném lỗi. Bài: cột Ngày giờ nhãn Ngày, gồm điền biểu mẫu, tạo hàng loạt, đổi kiểu, gán nhãn bảng lớn |
| TL-114 | Lưới gửi mốc hiện có kèm lượt lưu. Máy chủ chỉ trả `latest` khi ngoài các dòng vừa ghi không dòng nào đổi sau mốc đó; ngược lại trả rỗng, để lượt hỏi kế tiếp nạp |
| TL-10 | Sắp và lọc khoảng cột tiền/số thập phân trong JSON bằng biểu thức ép kiểu số có rào (chuỗi lạ ra NULL). Bỏ việc đổi phép khoảng thành so bằng cho hai kiểu này (`query.py:151`). Sửa bài có sẵn sang giá trị khác độ dài (`'999'`, `'1234.50'`, `'50'`) |
| TL-04 | Ô lọc tiền đọc bằng `core.money.parse_money` như ô nhập; ô lọc ngày nhận `DD/MM/YYYY` (ADR-032). Không đọc được thì chip ghi "(không hợp lệ, đã bỏ qua)" thay vì bỏ lặng lẽ |

**Đợt B: S3 còn lại**

| Mã | Cách sửa |
|---|---|
| TL-09 | `query.build` gắn khoá phụ `pk` cho mọi bảng, không riêng vận đơn |
| TL-11 | `record_count_scope` của ERP đếm theo `in_scope` cho mọi bảng (theo khuôn `tree_service.table_stats` của CRM) |
| TL-12 | Xoá và khôi phục mềm hàng loạt: một lệnh `UPDATE`, nhật ký `bulk_create` (mỗi dòng vẫn một bản ghi), đơn gốc theo lô. Bài: N = 10 và N = 100 cùng số truy vấn |
| TL-25, TL-122, TL-123 | `schedule_resync` trả tác vụ đang chờ của bảng nếu có; tác vụ giữ khoá advisory theo bảng. `remove_column` chỉ tính lại khi cột có nhãn hay công thức. Gỡ route `xoa-cot/`, `them-cot/` (lưới không dùng) |
| TL-06 | `catch` của `retainReadableDrafts` chỉ gọi `clearAccess` khi `quyen-dong/` trả 403 thật; lỗi khác thì giữ nháp và để "Lỗi lưu" kèm Thử lại |
| TL-20 | Ô bị từ chối có lớp lỗi, `aria-invalid`, `title`; lời báo dùng số hàng đang hiện (hay Mã đơn) và tên cột; chữ trạng thái gắn lớp màu có sẵn trong `crm-frame.css` |
| TL-115 | Phản hồi `luu-json` kèm các dòng có Trùng đổi (cùng SĐT cũ hay mới với dòng vừa sửa) |
| TL-118 | Gắn sẵn `table` cho mọi dòng trong lô tính lại (và ở đường đổi kiểu cột) |

**Đợt C: S4, công cụ, tài liệu**

TL-08 (bỏ kết quả `moi-nhat/` cũ hơn lượt lưu), TL-19 (Bỏ chi tiết và xoá dòng bị từ chối thì trạng thái "Lỗi lưu"),
TL-24 và TL-119 (bắt `OperationalError` 40P01/40001/55P03 trả JSON 503 lời tiếng Việt; lời báo riêng cho đường lưu; sửa chú thích
`bulk_save`), TL-26 (dừng nộp lô khi có lô lỗi), TL-120 (từ chối số vượt cỡ cột ngay khi đọc bộ lọc, middleware trả JSON
cho lưới), TL-121 (bỏ `total` khỏi `tinh_lai`), TL-27 (`do_hieu_nang` đổi sang `luu-json/` và `du-lieu/`, làm lệch dữ liệu
trước bước tính lại), TL-29 (`staticfiles_urlpatterns()` chỉ có tác dụng khi DEBUG bật), TL-30 (cảnh báo đầu script, bỏ
`du_lieu_mau` khi `--giu-du-lieu`), TL-112 và TL-124 (viết lại `locustfile_kn_crm.py` theo `luu-json/` và `du-lieu/`, chỉ
dòng `PERF-*`; thêm `set -e`), TL-28 và TL-31 (sửa docstring, AC-11.26, AC-11.36, ADR-016), TL-33 (bài đo `du-lieu/` thật
có ngân sách riêng).

## 6. Tự kiểm lại sau workflow

| Lệnh | Kết quả |
|---|---|
| `pytest _ra_soat_tmp/soat/test_khoi_lech.py` (Chromium, DB riêng) | Bài TL-113 **đỏ đúng lý do**: "chỉ 99/100 giá trị dán còn trong DB — mất giá trị dán âm thầm" |
| `pytest _ra_soat_tmp/soat/test_pham_vi_sale.py -s` | `manager_sale` thấy [], `leader_sale_1` [1, 3], `leader_sale_2` [2, 4], CEO cả 4; Leader và Manager không thấy bảng `van_don` (TL-116, TL-117) |
| `pytest _ra_soat_tmp/g6v/test_tl32.py` | 5 đạt: các bài khẳng định lỗi TL-32 còn (điền biểu mẫu 500, tác vụ FAILED) |
| Đọc `master-grid.js:835` và `master_views.py:222` | `state.version=''` khi giao thức khác 2; giao thức 2 chỉ bật khi có cờ `CRM_OPT_READ` (đang tắt ở local và VPS). Vậy TL-113 áp cho mọi máy hôm nay |
| `git status` trong worktree | Sạch: không tệp nào được git theo dõi bị sửa |

## 7. Nhật ký hoạt động

| # | Việc | Kết quả |
|---|---|---|
| 1 | Chủ dự án xoá 25 nhánh đã gộp; máy ảo `git fetch --prune` | Trên GitHub còn `main`, `Staging`, `PHASE-1`, `UI-SOLAR-PUNK` |
| 2 | Gỡ 19 worktree cũ đã gộp (kiểm từng cái không có thay đổi chưa commit); đặt lại nhánh `claude/knguard-project-review-9o3mqb` tại `origin/Staging` `2d5fb04` | Một worktree sạch để rà |
| 3 | Bật PostgreSQL; dựng `pt.sh` (mỗi lượt pytest một CSDL riêng); thư mục nháp `app/_ra_soat_tmp/` loại khỏi git, có `conftest.py` mượn fixture trình duyệt | Bài khói pytest 31 đạt; bài khói Chromium đạt |
| 4 | Lấy 27 dòng gốc từ `docs/test-log.md`, chia 7 nhóm theo vùng mã (lọc/sắp xếp; phạm vi quyền; ghi ô và deadlock; lưới JS báo lỗi; hoàn tác/dán/màu; tính lại nền; công cụ đo) | 7 nhóm, 3–5 mã mỗi nhóm |
| 5 | Workflow `wf_d06d4190-451`: mỗi nhóm một agent rà rồi một agent phản biện; cuối cùng một agent soát sót | 15 agent, 979 lượt dùng công cụ, 1 giờ 52 phút (máy 4 nhân chỉ chạy song song được 2 agent) |
| 6 | Phản biện đổi 5 kết luận: TL-06, TL-14, TL-19, TL-26 từ "hết" sang "còn một phần"; TL-29 sang "còn nguyên" | Soát chốt cả 5 theo phản biện; TL-19 hạ xuống S4 |
| 7 | Soát gộp lỗi mới trùng giữa các nhóm, chạy lại 3 bài của mình | 12 lỗi mới có bằng chứng: TL-113 → TL-124 |
| 8 | Tự chạy lại ba kết luận nặng nhất (mục 6) | TL-113 đỏ đúng lý do (99/100); TL-116 đúng; TL-32 đúng |
| 9 | Ghi biên bản này; cập nhật `docs/test-log.md` (mục mới đầu tệp, cột trạng thái của 27 dòng), biên bản tổng hợp, backlog, kanban | Chỉ tài liệu; không tệp mã nào đổi |
| 10 | Commit, push nhánh `claude/knguard-project-review-9o3mqb`, mở PR nháp về `Staging` | Xem mô tả PR |

## 8. Chưa kiểm

- Phần Locust của TL-124 chỉ đọc mã: máy ảo không cài `locust`.
- TL-12 trên VPS thật (504 sau 60 s) là suy ra từ số đo máy ảo và cấu hình nginx, chưa đo trên VPS.
- TL-118 ở 100.000 dòng là suy ra, chưa đo.
- Sao chép và Xoá nội dung vắt khối của TL-113: chỉ đọc mã, chưa chạy.
- Chặng 2 kiểm tay: không thuộc lượt rà này.
