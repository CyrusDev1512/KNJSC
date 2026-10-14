> Phần của [Kế hoạch kiểm thử toàn diện KNJSC](../08-ke-hoach-kiem-thu-toan-dien.md) — mục lục, lộ trình P0/P1/P2 và rủi ro còn lại nằm ở tệp đó.

### 3.8 Hiệu năng và tải

**Ngưỡng đang có trong mã** (`app/core/constants.py`, trừ chỗ ghi khác)

| Hằng số / mốc | Giá trị | Nguồn yêu cầu | Bài hoặc công cụ đang canh |
|---|---|---|---|
| `PERF_TABLE_ROWS` / `PERF_PAGE_SECONDS` | 50.000 dòng, trang đầu dưới 2 giây | NFR-1, AC-7.1 | `app/tests/test_hieu_nang.py` (dấu `cham`, chạy trong CI) |
| `PERF_LOAD_ROWS` / `PERF_LOAD_USERS` | 100.000 dòng vận đơn, 100 người ảo | NFR-2, AC-10.8 (Thủ công) | `app/tests/perf/locustfile_kn_crm.py` |
| `PERF_READ_P95_MS` | 1.000 ms (mở lưới, lọc, chuyển trang, sắp xếp, hộp lọc, trang chủ, thư mục) | ADR-016 | locustfile_kn_crm, `scripts/gom-p95-vps.py` |
| `PERF_WRITE_P95_MS` | 500 ms (lưu ô, dòng mới, định dạng) | ADR-016 | như trên |
| `PERF_POLL_P95_MS` | 300 ms (`moi-nhat/`, hỏi mỗi 8 giây) | ADR-016 | như trên |
| `PERF_RECOMPUTE_SECONDS` | 30 giây tính lại cột trên 100.000 dòng | ADR-016 | locustfile_kn_crm |
| `IMPORT_PERF_ROWS` / `IMPORT_PERF_SECONDS` | 2.000 dòng dưới 60 giây | NFR-3 | `forms_builder/tests/test_nhap_xuat.py` (có dùng hằng số; chưa đọc nội dung bài) |
| AC-10.1 | 50 người, không yêu cầu nào quá 3 giây | NFR-2 (Thủ công) | `app/tests/perf/locustfile.py` |
| AC-24.7, AC-27.8 | 100k/300k dòng × 10/20 người, làm nóng 60 giây + đo 300 giây. Đạt thì chạy bản cuối 300k/20 người/30 phút. Đọc/lọc/history p95 ≤ 1 giây, lưu ô ≤ 0,5 giây, 2.000 ô ≤ 5 giây; không sai, mất, trùng hay lộ dữ liệu | docs/04 | `locust_optimization.py`, `locust_optimization_endurance.py`, `scripts/kiem-tai-optimization.ps1` |
| Ngân sách truy vấn | ≤ 10 (AC-7.1, AC-42.4, AC-46.9, AC-50.8, AC-10.2); lưới 100 dòng ≤ 13; dán 500 ô ≤ 35; `moi-nhat/` ≤ 9 | AC-11.35, AC-11.36, AC-27.2 | `test_hieu_nang.py`, `crm/tests/test_kiem_tai.py` |
| `NGUONG_DO_MOT_KHOI_MS` | p95 ≤ 100 ms trên trình duyệt | AC-11.44 | `tests/e2e/test_ghi_chu_tu_gian_dong.py` bài 18 (TL-71 còn mở) |
| NFR-18 | Dung lượng lưu trữ tăng dưới 5 GB mỗi năm | `docs/02-yeu-cau-san-pham.md` | Chưa có bài hay công cụ nào đo |

**Công cụ có sẵn** (không cần thêm thư viện; `locust` đã có trong `app/requirements-dev.txt`)

| Công cụ | Dùng làm gì | Lưu ý an toàn |
|---|---|---|
| `manage.py seed_perf` | Sinh dòng `PERF-*` | Chỉ chặn bằng DEBUG (`seed_perf.py` `chan_khi_debug_tat`, vượt được bằng `--dong-y-chay-that`). Máy local có DEBUG bật nên chạy được trên DB thật. Khoá có bài từ #116 (`core/tests/test_seed_perf_xoa.py`) |
| `manage.py do_hieu_nang` | Đo từng thao tác, ghi ra `storage/perf/<ngày>-don-le*.md` | Có khoá DEBUG từ #116 (TL-98), như `seed_perf`. Lệnh ghi (ghi chú, tô đậm) chỉ trỏ vào dòng `PERF-*` trong phạm vi `vd.staff`; thiếu dòng giả thì dừng trước khi đo. Vẫn chạy `resync_table` cả bảng. Có bài `core/tests/test_do_hieu_nang.py` (HN-08) |
| `manage.py nap_khach_mau`, `delete_fake_records` | Nạp và xoá khách giả theo lô có `lock_timeout` | Có bài: AC-10.9, AC-10.10 |
| `app/tests/perf/locustfile_kn_crm.py` | 100 người, kiểm 4 ngưỡng, có `process_exit_code` | Bộ số dự phòng ở nhánh `except` chưa được so với constants |
| `app/tests/perf/locust_optimization.py`, `locust_optimization_endurance.py` + `scripts/kiem-tai-optimization.ps1` | Tải CRM theo AC-24.7/AC-27.8. Script nhận `-Users` 10 hoặc 20, `-Duration` 10–1860 giây; có `-Endurance` thì chạy bản bền (thêm lượt 2.000 ô trong lúc các vai vẫn làm việc, lấy mẫu `pg_stat_activity` và `core_backgroundjob` ra `*.telemetry.jsonl`) | Chạy qua `deploy/docker-compose.yml` (local), dùng DB manifest riêng `/runtime/ready.json`. Script PowerShell, chạy tay |
| `app/tests/perf/optimization_cache_outage.py` | Cắt kết nối Redis thật trong một process riêng, không ngắt cache của bài tải | Dùng `optimization_settings`. Chưa xác minh có biên bản chạy |
| `app/tests/perf/locust_order_entry.py`, `locust_order_hub.py` | Lên đơn (đọc form, xem trước Decimal, đọc đơn gốc) và đọc ERP/CRM; 10 giây làm nóng + 60 giây đo | Chỉ chạy trên fixture `test_order_hub_browser_server` |
| `app/tests/perf/locustfile_master.py` (AC-21), `locust_master_nine.py` | Tải JSON lưới trước/sau tối ưu | Chỉ nhận manifest DB test do pytest tạo |
| `app/tests/perf/locustfile_erp.py`, `locust_identity.py` | ERP: đăng nhập, nộp `/bao-cao/`; tìm kiếm/chi tiết chỉ đọc | `locustfile_erp.py` assert host thuộc danh sách máy test (`127.0.0.1:8134/8135`, `knjsc-erp-baseline-v1`, `knjsc-erp-final`), `locust_identity.py` chỉ nhận `knjsc-erp-final:8000`. Không chạy được vào cổng thật |
| `scripts/kiem-tai-kn-crm.sh/.bat` | Chuỗi gunicorn → seed_perf → do_hieu_nang → Locust → trả runserver | Thiếu `-e` và `trap` (TL-29, TL-30). Có gọi do_hieu_nang |
| `scripts/gom-p95-vps.py` | Gom p95 thật từ log `knjsc.request` trên VPS. Mã thoát: 0 đạt, 1 vượt ngưỡng, 2 thiếu mẫu | Có `app/tests/test_gom_p95.py` (13 bài) |
| `crm/tests/test_master_capacity.py`, `test_master_nine_capacity.py`, `test_optimization_capacity.py`, `test_scroll_fixture.py`… | Đo sức chứa | Chỉ chạy khi có biến môi trường. Trong CI luôn bỏ qua |
| `scripts/order-code-check/`, `scripts/crm-update-perf/`, `scripts/grid-flags-check/run.py` | Bộ đo cũ | Chạy gunicorn `--timeout 60`, khác mặc định 30 giây (lệnh gunicorn trong `deploy/production/compose.yml` không đặt `--timeout`; `compose.vps.yml` có ghi đè hay không thì chưa xác minh) |

**Đã đo ở đâu**

| Ngày | Biên bản | Môi trường | Kết quả | Giới hạn |
|---|---|---|---|---|
| 11.09 | `docs/kiem-tai-30-sale-10-van-don-20260911.md` | Docker local, gunicorn 3×4, 100.000 đơn | Dừng ở giây 33 vì 3 lỗi HTTP 500 do trùng mã đơn | Không phải VPS. Chưa nghiệm thu |
| 16.09 | `docs/kiem-chung-tai-dong-thoi-20260916.md` | Local và bản sao trên VPS 2 vCPU/4 GB, 10.000 dòng, gunicorn **1×4** | Ở mức 5 người VPS còn trong ngưỡng | Không qua nginx/TLS/nén. Biên bản tự ghi là "không suy thành chứng nhận AC-10.8" |
| 16.09 | `docs/kiem-chung-300k-10-nguoi-20260916.md` | VPS, 300.000 dòng, 10 người, gunicorn 1×4 | Vượt cả ba ngưỡng: đọc 5.043 ms, lưu 2.341 ms, hỏi thăm 3.868 ms | Không qua nginx/TLS, không có cache Redis. Cấu hình worker có thể khác production (số worker thật nằm trong `compose.vps.yml`, không có trong kho, chưa xác minh) |
| 22.09 | `docs/kiem-chung-gom-p95-vps-20260922.md` | Máy ảo | Bộ gom chạy đúng | **Chưa có con số p95 thật nào của VPS** |
| 29.09 | `docs/kiem-chung-phat-hanh-vps-20260929.md` | VPS sau phát hành | p95 chỉ có 7–52 mẫu | Dưới 20 mẫu thì chưa kết luận được |
| Mỗi PR | `.github/workflows/ci.yml` | Runner GitHub | `test_hieu_nang.py` và ngân sách truy vấn chạy trong job `kiem-thu` | Runner dùng chung nên chỉ đo được một người dùng |

**Còn thiếu:**
1. p95 thật trên VPS với ít nhất 20 mẫu mỗi nhóm.
2. AC-10.8 (100 người, 100.000 dòng) và AC-10.1 (50 người) chưa có biên bản đạt.
3. Chưa có lượt kiểm tải nào chạy đúng cấu hình production. Số worker và giới hạn bộ nhớ thật của VPS (2 nhân/4 GB) nằm trong `compose.vps.yml`, tệp này không có trong kho, nên **chưa xác minh**. Không suy được từ `deploy/production/compose.yml`: theo `deploy/production/README.md` dòng 5-8, các giá trị ở đó (crm 3×4 `mem_limit 3g`, erp 2×2 `mem_limit 2g`) dành cho máy giả định 12 CPU/24 GB. Lượt kiểm phải có đủ nginx/TLS, cache Redis `crm`, worker và heavy chạy concurrency 1 (theo README dòng 59-60). Mọi biên bản và ca đo ở trên chỉ nhắm CRM; ERP chưa có ca tải nào.
4. Chưa có số đo cho timeout 30 giây.
5. Chưa đo định kỳ.
6. Chưa có biên bản chạy bền (soak) 30 phút theo AC-24.7/AC-27.8, dù công cụ đã có. Chưa xác minh có biên bản nào trong `docs/` cho lượt `-Endurance`.
7. Chưa ước mức tăng dung lượng theo NFR-18.
8. Chưa đo việc đổi kiểu cột trên bảng lớn. `_chuyen_kieu` (`app/forms_builder/services/table_service.py:157-190`) duyệt mọi dòng, kể cả dòng đã xoá (`DataRecord.all_objects`), và chạy đồng bộ trong request web. Biên bản `docs/kiem-chung-database-phan-quyen-20261006.md` dòng 77 ghi "chưa đo thời gian".

| Mã | Ca kiểm và kỳ vọng | Góc nhìn | Loại | Cách chạy | Ưu tiên | Tham chiếu |
|---|---|---|---|---|---|---|
| HN-01 | Gom p95 7 ngày trên VPS: `gom-p95-vps.py --compose compose.yml --compose compose.vps.yml --since 7d --json`. Đủ ít nhất 20 mẫu mỗi nhóm Đọc, Ghi, Hỏi thăm; mã thoát 0. Ghi biên bản | QA | Hiệu năng thật | Bán tự động | P0 | ADR-016, docs/06 "Việc còn thiếu" điều 2 |
| HN-02 | Kiểm tải 10 người trên DB tổng hợp riêng 300.000 dòng **tại VPS với cấu hình production thật** (số worker/threads và `mem_limit` chép từ `compose.vps.yml` trên VPS và ghi vào biên bản, đi qua nginx/TLS, có cache). So với biên bản 16.09. Dừng khi RAM khả dụng dưới 400 MB | Người dùng | Tải | Bán tự động | P1 | NFR-2, biên bản 16.09, README dòng 5-8 |
| HN-03 | Chạy `scripts/kiem-tai-kn-crm.sh` cho 100 người, 100.000 dòng ở local. Từng tiêu chí phải ĐẠT, 0 lỗi, tính lại xong trong 30 giây | QA | Tải | Bán tự động | P1 | AC-10.8, NFR-2 |
| HN-04 | Chạy `locustfile.py` 50 người, không yêu cầu nào quá 3 giây | QA | Tải | Bán tự động | P1 | AC-10.1 |
| HN-05 | Một yêu cầu dài hơn 30 giây (Thống kê trên 300.000 dòng) chạy song song với 3 tab đang lưu ô. Ghi nhận 502, `WORKER TIMEOUT`, các lần lưu bị đứt. Đo lại với `--timeout 60` | Người dùng | Sự cố hiệu năng | Bán tự động | P1 | K27, ADR-016, `deploy/Dockerfile` CMD |
| HN-06 | Một lượt xuất hay tính lại dài hơn 15 phút trên worker concurrency 1. Kiểm job nhập đứng sau có bị đánh STALE nhầm hay không | QA | Tích hợp Celery | Tự động + diễn tập | P1 | TL-23, AC-9.2 |
| HN-07 | So bộ số dự phòng trong `locustfile_kn_crm.py` (8, 1000, 500, 300, 30) với constants, theo cách `test_gom_p95.py` đang làm | QA | Đơn vị | Tự động | P2 | ADR-016 |
| HN-08 | `do_hieu_nang` và `seed_perf` phải từ chối khi DEBUG tắt. do_hieu_nang chỉ được ghi vào dòng `PERF-*`; hash của các dòng `DH-*` không đổi. Đã xanh từ #116 (`core/tests/test_do_hieu_nang.py`, `core/tests/test_seed_perf_xoa.py`) | QA | Đơn vị lệnh | Tự động | P0 | AC-10.10, quy tắc 6 |
| HN-09 | Biên bản đo cũ của TL-71: chạy lặp bài 18 và `test_sap_xep_khong_giat.py` 20 lần. 0/20 lần treo, p95 ≤ 100 ms | QA | Độ ổn định | Bán tự động | P1 | TL-71 |
| HN-10 | Bảng xếp hạng `/van-hoa/` khi bảng Order lớn. Hiện không có chỉ mục riêng cho `created_at`; dùng `do_hieu_nang --giai-thich` hoặc EXPLAIN | QA | Hiệu năng truy vấn | Bán tự động | P2 | `orders/models.py` dòng 224–226 |
| HN-11 | Khói import cho `app/tests/perf/*.py`: chạy `py_compile`, và mọi URL trong locustfile phải `resolve` được dưới urlconf tương ứng | QA | Bảo trì công cụ | Tự động | P2 | AC-10.1, AC-10.8 |
| HN-12 | Tải ERP ở đúng cấu hình production: dựng container ERP test (`knjsc-erp-final`) với số worker, threads và `mem_limit` chép từ `compose.vps.yml` thật (chủ dự án cung cấp; giá trị 2×2 gthread, `mem_limit 2g` trong `deploy/production/compose.yml` dòng 73-74 chỉ dành cho máy giả định nên không dùng làm chuẩn). Chạy `locustfile_erp.py` (đăng nhập, nộp `/bao-cao/`) cùng `locust_identity.py` và `locust_order_hub.py`. p95 đọc ≤ 1.000 ms, nộp báo cáo ≤ 500 ms, 0 lỗi 5xx. Ghi lại hàng đợi khi mọi luồng đều bận | Người dùng | Tải | Bán tự động | P1 | NFR-2, ADR-016, README dòng 5-8 |
| HN-13 | Chạy bền: `kiem-tai-optimization.ps1 -Rows 300000 -Users 20 -Endurance -Duration 1860` (60 giây làm nóng + 30 phút đo). Đạt khi giữ ngưỡng AC-27.8 suốt lượt, RSS của gunicorn và số kết nối trong `*.telemetry.jsonl` không tăng dần, không có job `pending` kẹt, không 5xx và oracle không thấy sai, mất hay trùng dữ liệu. Chỉ chạy bản cuối sau khi các nấc 100k/300k × 10/20 đã đạt | QA | Chạy bền (soak) | Bán tự động | P1 | AC-24.7, AC-27.8 |
| HN-14 | Mất Redis giữa tải: chạy `optimization_cache_outage.py` song song với `locust_optimization.py`. Lưới vẫn đọc và ghi đúng (rơi về DB), không 500, có lại Redis thì cache tự hồi phục | QA | Chịu lỗi | Bán tự động | P2 | ADR-016 |
| HN-15 | Ước dung lượng theo NFR-18: chụp `pg_database_size`, `du -s` của `storage/tai-lieu`, `storage/chung-tu-thanh-toan`, `BACKUP_DIR` (giữ `BACKUP_KEEP` = 30 bản), `storage/e2e`, `storage/perf` và log json-file của Docker. Đo hai lần cách nhau ít nhất 30 ngày rồi ngoại suy ra một năm. Đạt khi tổng < 5 GB/năm. Nếu `BACKUP_DIR` một mình đã vượt thì ghi nhận và đề xuất bớt số bản giữ | QA | Dung lượng | Thủ công | P2 | NFR-18, NFR-15, VH-20 |
| HN-16 | Đổi kiểu cột trên bảng 100.000 dòng (có cả dòng đã xoá), ví dụ Chữ → Số: bấm giờ request đổi kiểu với cấu hình gunicorn production (timeout 30 giây). Đạt khi xong dưới 30 giây, không 502/`WORKER TIMEOUT`, các tab khác vẫn lưu ô được (`select_for_update` theo lô `RECOMPUTE_BATCH`). Vượt thì ghi nhận và đề xuất chuyển sang job nền | Người dùng | Hiệu năng thao tác quản trị | Bán tự động | P1 | AC-8.11, `table_service.py:157-190`, biên bản 06.10 dòng 77 |

**Đưa một bài khói hiệu năng nhẹ vào CI.** Không cần thêm thư viện. Sửa `ci.yml` phải hỏi chủ dự án trước.
1. **Giữ nguyên** `test_hieu_nang.py` và các ngân sách truy vấn đang chạy.
2. Thêm một bài `cham` trong `crm/tests/` dùng lại dữ liệu 50.000 dòng. Gọi `du-lieu/`, `moi-nhat/` và `luu-json/` (1 ô), mỗi đường 20 lần bằng test client. Tính p95 theo cách của `gom-p95-vps.py`. Assert theo `PERF_*_P95_MS` × hệ số an toàn cho runner dùng chung (đề xuất ×3, cần chủ dự án chốt). In số thật ra log.
3. Tuỳ chọn: thêm một job `workflow_dispatch` chạy `locust --headless -u 10 --run-time 60s` vào live server với `locustfile_kn_crm.py`. Job chỉ báo cáo, không chặn gộp, vì runner dùng chung làm số dao động.

### 3.9 Bảo mật

**Hiện trạng theo mục**

| Mục | Đã có | Còn hở |
|---|---|---|
| CSRF | `hx-headers X-CSRFToken` ở `templates/base.html`, `crm/base_crm.html` và `crm/base_bang_tinh.html`. Có bài `core/tests/test_giao_dien.py::test_moi_bieu_mau_gui_di_deu_co_the_chong_gia_mao`, `crm/tests/test_shared_integrity.py::test_csrf_required_for_lifecycle_and_grid`, `org/tests/test_account_management.py::test_delete_requires_confirmation_and_csrf`, `core/tests/test_shared_login.py` | Chưa quét mọi route POST với `enforce_csrf_checks`. Lỗi CSRF hiện trang chữ Anh (thiếu `403_csrf.html`) |
| XSS | Autoescape bật mặc định. `|urlize` (Bảng tin) chạy trong ngữ cảnh autoescape. `|safe` chỉ áp lên BoundField và `help_text` của form trong mã (`password_change.html`, `nhan_su_form.html`). Lưới dựng ô bằng `textContent` (hàm `element()`, `master-grid.js:257`). `innerHTML` trong JS chỉ chép HTML máy chủ đã render, hoặc chuỗi cố định. Lưới đã có ca khoá: `tests/e2e/test_pha_luoi_ghi_chu.py::test_noi_dung_doc` (dòng 205, chuỗi "giống thẻ HTML" `<script>alert(1)</script><b>đậm</b>` phải hiện thành chữ, AC-11.44) | Năm app Nội bộ (Bảng tin, Công việc, Tài liệu, Văn hoá, Tài nguyên) và hộp Lịch sử ô chưa có bài nào (grep `<script`, `onerror` trong test của năm app này không ra kết quả). Chưa xác minh hết là không `help_text` nào lấy từ dữ liệu người dùng |
| SQL injection | Lọc qua ORM. SQL thô dùng tham số hoặc từ điển trắng: `statistics_profiles._waybill_dimensions` (granularity tra từ dict), `payment_service.filter_options` (`prep_for_like_query`), `waybill_service` (`int(max_groups)`) | Chưa có bài gửi chuỗi độc vào `?tim=`, `?sort`, mã cột và tham số granularity/kind. Giá trị ngoài dict có thể gây KeyError, tức 500 thay vì 400 (chưa xác minh view có kiểm trước) |
| IDOR | Có bài AC-3.6 với đối tượng thật ở 8 tệp. Ngày 06.10 đã kiểm tay 28 mẫu đường dẫn có id: Đạt (`docs/kiem-chung-san-loi-bao-mat-20261006.md`) | `app/tests/test_khoi.py` chỉ dùng `pk=999999` và chấp nhận mã 200. Không có CEO, Kế toán, CSKH |
| Tải tệp lên | `core/excel.sniff_kind`, `UPLOAD_MAX_BYTES`, chặn bom nén `XLSX_MAX_UNCOMPRESSED_BYTES` (AC-7.15, `test_nhap_tep_bom.py`), `neutralise_formulas` (AC-7.14). Tài liệu tải về qua `FileResponse(as_attachment=True)`. `LINK_SCHEMES` chỉ cho http/https (`resources/tests/test_tai_nguyen.py` có ca `javascript:`) | Chưa có bài khẳng định header `nosniff` / `private, no-store` của ảnh chứng từ (AC-26.4). Tên tệp bị cắt `[:200]` nên mất đuôi, NFD chưa chuẩn hoá. nginx `client_max_body_size 11m` trả trang 413 chữ Anh. **Yêu cầu và mã lệch nhau:** NFR-12 (`docs/02-yeu-cau-san-pham.md` dòng 263) chỉ cho "Excel, CSV, ảnh JPG và PNG", trong khi FR-9.2 (dòng 168) và mã của Tài liệu nhận cả PDF và Word theo chữ ký tệp (`core/tests/test_excel.py::test_word_va_pdf_nhan_theo_chu_ky_va_duoi`). Chủ dự án cần chốt sửa NFR-12 hay sửa mã (BM-24) |
| Cấu hình prod | `prod.py` có SSL redirect, cookie Secure, HSTS 31.536.000 + preload, nosniff, X-Frame DENY. Ngày 06.10 `check --deploy` cho 0 cảnh báo. Có `core.E001` (AC-1.11) | Không bài nào nạp `knjsc.settings.prod`. `BANGTINH_GOC` gõ sai thì CRM rơi về dev (TL-85). Chưa có `server_tokens off` và CSP |
| Xác thực | Khoá 5 lần sai ở `/dang-nhap/`. Lỗi 40 lần sai gửi cùng lúc đều được thử đã sửa ngày 06.10 (`auth_service.reserve_attempt` giữ chỗ bằng `select_for_update`), có `org/tests/test_do_mat_khau.py` (3 bài, gồm bài 20 luồng thật) (`docs/kiem-chung-san-loi-dang-nhap-nhat-ky-20261006.md`) | `/quan-tri/login/` từng đi vòng qua khoá, nhật ký và `auth_epoch` (FR-1.2); đã sửa ở #121, nay chuyển về `/dang-nhap/`. `X-Forwarded-For` giả gây 500 và giả được IP trong AuditLog (`core/audit.py::_client_ip`). Theo biên bản 06.10: (a) dò rải nhiều tài khoản từ một địa chỉ (password spraying) **chưa kiểm**, vì khoá theo tài khoản không chặn được kiểu này và chặn theo IP cần chủ dự án chốt (cả văn phòng chung một IP); (b) tài khoản có thật sau 5 lần sai báo "đang bị khoá tạm", nên dò được tài khoản nào có thật (**ghi lại, chưa sửa**). NFR-4 (mật khẩu được băm) chưa có bài: `settings/test.py` dòng 30 đặt `PASSWORD_HASHERS = [MD5PasswordHasher]` nên toàn bộ pytest chạy với MD5. `prod.py`/`bangtinh.py` không đặt `PASSWORD_HASHERS` (grep chỉ thấy ở `test.py`) nên dùng mặc định của Django, nhưng không bài nào khẳng định điều này (BM-23) |
| Bí mật | Mật khẩu chỉ đi qua `PGPASSWORD` (có bài trong `test_sao_luu.py`). `core/audit.py::_scrub` | `.gitignore` không chặn `deploy/.env`, `deploy/production/.env`, `compose.vps.yml`, `app/.env` (đã kiểm bằng `git check-ignore`). Không có `.dockerignore`. Tệp `/opt/knjsc-runtime/initial-admin.txt` còn trên VPS. Địa chỉ và cổng SSH nằm trong `scripts/grid-flags-check/vps-smoke.cjs` và `docs/kiem-chung-phat-hanh-vps-*.md` |
| Log và thư | `nginx log_format` không ghi query. Postgres đặt `log_statement=none`. AuditLog 5.001 dòng: 0 dòng chứa SĐT hay mật khẩu (biên bản 06.10) | TL-82: thiếu `-c log_min_error_statement=panic`. Handler `mail_admins` mặc định có thể gửi POST trong thư lỗi 500 (chưa xác minh). `EMAIL_HOST*` không đọc từ env. Mỗi lần trả 403 Django ghi **nguyên traceback** mức WARNING, nên ai dò đường dẫn thì log VPS phình nhanh (biên bản 06.10, **chưa sửa**). Mật khẩu gõ nhầm vào ô Tên đăng nhập lọt vào `actor_label` của dòng "Đăng nhập thất bại" (chủ dự án chọn có che hay không) |
| Phụ thuộc | `pip-audit` chạy tay ngày 06.10: nâng Django lên 5.2.17 và python-dotenv lên 1.2.2 | Không có Dependabot (`.github/` chỉ có `workflows/ci.yml`). Không có bandit. Phụ thuộc bắc cầu không được ghim |

| Mã | Ca kiểm và kỳ vọng | Góc nhìn | Loại | Cách chạy | Ưu tiên | Tham chiếu |
|---|---|---|---|---|---|---|
| BM-01 | `/quan-tri/login/`: tài khoản đang bị khoá đăng nhập bằng mật khẩu đúng thì không được tạo phiên. Từ #121 trang này chỉ chuyển về `/dang-nhap/`, không kiểm mật khẩu; sai 6 lần ở `/dang-nhap/` thì tăng `failed_login_count`, đặt `locked_until` và ghi `LOGIN_FAILED`. Đã xanh (`core/tests/test_quan_tri_dang_nhap.py`) | QA | Bảo mật HTTP | Tự động | P0 | FR-1.2, AC-1.3, AC-1.9 |
| BM-02 | Nạp `knjsc.settings.prod` trong tiến trình con: DEBUG False, đủ các cờ SECURE_*, HSTS, X_FRAME_OPTIONS. Thiếu `DJANGO_SECRET_KEY` thì thoát mã khác 0 | QA | Đơn vị cấu hình | Tự động | P0 | NFR-5, AC-1.11 |
| BM-03 | Các giá trị `BANGTINH_GOC` = `production`, `Prod`, ` prod` trên tên miền thật phải dừng khởi động. Đỏ trên mã hiện tại | QA | Đơn vị cấu hình | Tự động | P0 | TL-85, D9 |
| BM-04 | Thêm bước CI chạy `check --deploy --fail-level WARNING` cho cả prod và bangtinh (`BANGTINH_GOC=prod`) với cookie domain cha | QA | CI cấu hình | Tự động | P0 | AC-1.11, TL-85 |
| BM-05 | Kiểm khói CSRF: duyệt resolver của cả hai urlconf, POST rỗng không token bằng `Client(enforce_csrf_checks=True)` → 403, không bao giờ 500 hay 200 | QA | Bảo mật HTTP | Tự động | P1 | NFR-6 |
| BM-06 | XSS cho phần chưa có bài: chèn `<script>alert(1)</script>`, `<img src=x onerror=…>` và `javascript:` vào tên khách, bài và bình luận Bảng tin, tiêu đề tài liệu và việc, lời nhắn Văn hoá, tên nhân sự, tài nguyên. HTML trả về phải có `&lt;script`. Hộp Lịch sử ô (giá trị cũ/mới chứa chuỗi độc) không thực thi (e2e có `page.on('dialog')`). Ô lưới đã có `test_pha_luoi_ghi_chu.py::test_noi_dung_doc`, giữ làm hồi quy | QA | Bảo mật giao diện | Tự động | P1 | FR-10.1, AC-21.13, AC-11.44 |
| BM-07 | SQL injection: `?tim=' OR 1=1--`, `?tim=%_`, sort và mã cột chứa `'`/`"`, granularity và kind lạ trên Thống kê, `filter_options` của chứng từ. Không có 500, số dòng không vượt phạm vi | QA | Bảo mật HTTP | Tự động | P1 | ADR-033, `statistics_profiles.py` |
| BM-08 | IDOR: dựng bản ghi thật cho từng loại (báo cáo, DataRecord, Order, tài liệu, việc, tác vụ, chứng từ, ảnh chứng từ). Vai khác bộ phận cùng CEO, Kế toán, CSKH gọi GET/POST theo pk → 403/404; nếu 200 thì không được chứa mã hay tên của bản ghi | QA | Phân quyền | Tự động | P0 | AC-3.6, ADR-044, ADR-038 |
| BM-09 | Tải lên: tệp .exe đổi đuôi .xlsx, PDF đổi đuôi .xlsx, tên tệp `../../a.pdf`, tên chứa CRLF, tên NFD dài 250 ký tự. Phải bị từ chối, hoặc khi tải về `Content-Disposition` an toàn và vẫn giữ đuôi | QA | Bảo mật tệp | Tự động | P1 | AC-7.15, NFR-11 |
| BM-10 | Ảnh chứng từ: header có `Cache-Control: private, no-store` và `X-Content-Type-Options: nosniff`. Người ngoài phạm vi nhận 404 | QA | Bảo mật HTTP | Tự động | P1 | AC-26.4 |
| BM-11 | `X-Forwarded-For: khong-phai-ip` khi đăng nhập sai không được ra 500. Qua nginx trên VPS, AuditLog ghi IP thật | QA | Bảo mật / toàn vẹn nhật ký | Tự động + Thủ công | P1 | BR-6, NFR-6 |
| BM-12 | Thư lỗi 500 và log không chứa SĐT, tên khách, `sessionid`, mật khẩu (dùng `mail.outbox` và `caplog`). Ghi nhận hành vi của mẫu thư mặc định | QA | Bảo mật dữ liệu | Tự động | P1 | quy tắc 6, D12 |
| BM-13 | `RequestMetricsMiddleware`: dòng log có `route` là mẫu đường dẫn, không chứa query. `X-Request-ID` chứa CRLF hoặc dài 65 ký tự thì bị thay | QA | Đơn vị middleware | Tự động | P1 | quy tắc 6 |
| BM-14 | Kiểm tĩnh `deploy/production/compose.yml` (có `log_min_error_statement=panic`, chỉ proxy có `ports`) và `git check-ignore` các tệp `.env`. Hiện đỏ | QA | Kiểm tĩnh | Tự động | P0 | TL-82 |
| BM-15 | Phiên chung qua HTTPS thật: cookie Secure, HttpOnly, Lax, domain cha. Đăng xuất ở ERP thì tab CRM lưu ô nhận 403, DB không đổi | Người dùng | Bảo mật phiên | Thủ công | P0 | AC-1.4, AC-1.10, AC-1.11 |
| BM-16 | VPS: quyền tệp `initial-admin.txt` là 600 hoặc tệp đã bị xoá, và mật khẩu Admin ban đầu đã đổi. Chủ dự án quyết có gỡ thông tin SSH khỏi kho hay không | QA | Bảo mật vận hành | Thủ công | P1 | điều cấm 6 |
| BM-17 | `curl -I` trên hai tên miền: có HSTS, nosniff, X-Frame DENY. Header `Server` không lộ phiên bản (sau khi có `server_tokens off`) | QA | Cấu hình | Bán tự động | P2 | D18 |
| BM-18 | Hỏi thăm 8 giây giữ phiên sống mãi: patch thời gian quá 60 phút trong khi chỉ có yêu cầu `moi-nhat/`. Chủ dự án chốt kỳ vọng | QA | Phân quyền phiên | Tự động | P1 | FR-1.3, AC-1.4 |
| BM-19 | Phục hồi bản sao lưu cũ làm sống lại phiên và quyền đã thu hồi. Quy trình phục hồi phải có bước thu hồi phiên | QA | Diễn tập bảo mật | Thủ công | P1 | AC-10.5, FR-1.3 |
| BM-20 | Dò rải (password spraying): từ một địa chỉ, thử 1 mật khẩu phổ biến trên 30 tài khoản mẫu, mỗi tài khoản dưới 5 lần. Ghi nhận hiện không có gì chặn (không tài khoản nào bị khoá, không cảnh báo). Chủ dự án chốt cách chặn (theo IP có ngưỡng cao vì cả văn phòng chung IP, hay cảnh báo Admin khi một IP sai trên N tài khoản), rồi mới đổi thành bài khẳng định | QA | Bảo mật xác thực | Tự động (bài ghi nhận) | P1 | FR-1.2, biên bản 06.10 mục "Chưa kiểm" |
| BM-21 | Dò tài khoản có thật: sai 6 lần với một tài khoản có thật và một tên không tồn tại, so lời báo và mã HTTP. Hiện tài khoản có thật báo "đang bị khoá tạm" còn tên không tồn tại thì không, nên dò được tài khoản. Ghi nhận; nếu chủ dự án chọn sửa thì cả hai phải nhận cùng một lời và cùng thời gian đáp tương đương | QA | Bảo mật xác thực | Tự động | P2 | AC-1.1, AC-1.2, biên bản 06.10 |
| BM-22 | Log khi bị dò đường dẫn: gọi 100 lần một URL bị từ chối quyền, đếm dòng log mức WARNING bằng `caplog`. Mỗi 403 chỉ được ghi một dòng gọn (không traceback), không lộ dữ liệu. Đỏ trên mã hiện tại. Trên VPS, đo dung lượng log container sau loạt dò | QA | Bảo mật vận hành / log | Tự động + Thủ công | P2 | biên bản 06.10 "Ghi lại, chưa sửa", VH-20 |
| BM-23 | Mật khẩu được băm mạnh: nạp `knjsc.settings.prod` và `knjsc.settings.bangtinh` trong tiến trình con, khẳng định hasher đầu tiên của `PASSWORD_HASHERS` là PBKDF2 hoặc Argon2 và danh sách không có `MD5PasswordHasher`. Thêm một bài tạo người dùng thật dưới cấu hình prod: `password` trong DB bắt đầu bằng `pbkdf2_` (hoặc `argon2`), không chứa mật khẩu gốc. MD5 trong `settings/test.py` dòng 30 chỉ được dùng cho pytest | QA | Đơn vị cấu hình | Tự động | P1 | NFR-4, `app/knjsc/settings/test.py:30` |
| BM-24 | Loại tệp được phép theo kết quả chủ dự án chốt giữa NFR-12 (chỉ Excel, CSV, JPG, PNG) và FR-9.2 cùng mã hiện tại (Tài liệu nhận thêm PDF, Word). Nếu giữ mã: sửa NFR-12 trong docs/02, và bài `test_word_va_pdf_nhan_theo_chu_ky_va_duoi` là bài khẳng định. Nếu theo NFR-12: Tài liệu phải từ chối PDF/Word bằng lời tiếng Việt. Mọi trường hợp: từng điểm tải lên (nhập lưới, Tài liệu, ảnh chứng từ) chỉ nhận đúng danh sách đã chốt cho điểm đó | QA | Bảo mật tệp / truy vết yêu cầu | Tự động (sau khi chốt) | P1 | NFR-12, FR-9.2, `app/core/tests/test_excel.py` |

**Công cụ mới, phải chủ dự án duyệt trước** (quy tắc 8)

| Công cụ | Đề xuất | Cách dùng không thêm vào requirements |
|---|---|---|
| pip-audit | Chạy mỗi lần đổi `requirements*.txt` và trước mỗi phát hành | Chạy ngoài dự án như ngày 06.10 (`pipx run pip-audit -r app/requirements.txt`). Ghi kết quả vào biên bản phát hành |
| Dependabot | Tệp `.github/dependabot.yml` cho pip và npm | Là cấu hình GitHub, không phải thư viện. Mỗi PR nâng bản vẫn phải chạy toàn bộ CI |
| bandit | Quét tĩnh `app/` (trừ thư mục tests) | Chạy ngoài dự án. Kết quả cần người đọc, không đặt làm cổng chặn |
| npm audit | Quét `package.json` (playwright) | Có sẵn trong npm |
| OWASP ZAP | Quét web tự động, theo mục "Chưa kiểm" của biên bản 06.10 | Chỉ chạy trên Staging hoặc bản sao, không chạy trên VPS thật |
| CSP, `server_tokens off` | Sửa cấu hình nginx | CSP cần rà mọi script nội dòng trước khi bật |

### 3.10 Giao diện: responsive, hồi quy hình ảnh, khả năng tiếp cận

**Responsive 390px.** Đã có các bài sau:

| Màn | Bài | Khung |
|---|---|---|
| ERP: `/`, `/bang/van_don/`, `/bao-cao/`, `/bang/van_don/nhap/` | `app/tests/e2e/test_dien_thoai.py` (fixture `trang_dien_thoai`, `is_mobile`, danh sách `MAN_HINH`), đo `scrollWidth ≤ innerWidth` | 390×844 |
| Lưới CRM 8021 | `app/tests/e2e/test_pha_luoi_ghi_chu.py::test_dien_thoai_390`; `test_ghi_chu_tu_gian_dong.py` dòng 802 | 390×844 (cả 1440×900) |
| Báo cáo tổng hợp | `reports/tests/test_bo_cuc_bao_cao_e2e.py` (nhiều bài 390×844; dòng 852 thêm 768×1024 dạng máy tính bảng) | 390×844, 768×1024 |
| Hộp ✎ sửa tổng hợp của Admin | `reports/tests/test_admin_sua_tong_hop_e2e.py::test_hop_sua_tren_dien_thoai` | điện thoại |

AC-10.4, AC-11.11 và AC-13.6 vẫn ghi Thủ công. **Còn thiếu thật:** Lên đơn, Thống kê (CRM 8021) và năm màn Nội bộ (Bảng tin, Công việc, Tài liệu, Văn hoá, Tài nguyên). Hướng làm: mở rộng `MAN_HINH` bằng fixture sẵn có, không cần thư viện.

**Hồi quy hình ảnh.** Hàm `chup()` (`tests/e2e/conftest.py:81`) chỉ lưu ảnh vào `storage/e2e/` (artifact `anh-e2e`, giữ 7 ngày) và **không so ảnh**. Các lựa chọn:

| Lựa chọn | Thêm thư viện? | Ưu | Nhược |
|---|---|---|---|
| A. So hình học DOM: lưu `boundingBox` của các phần tử mốc (thanh công cụ, cột ghim, ô đầu, hộp lọc) thành JSON vàng, lệch quá 1 px thì đỏ | Không | Ổn định giữa các máy. Đúng kiểu lỗi đã gặp: TL-69, TL-74, AC-24.5 | Không bắt được lỗi màu hay phông |
| B. So PNG: chụp bằng Playwright Python, giải nén PNG bằng `zlib` của thư viện chuẩn, đếm điểm ảnh lệch | Không, nhưng phải tự viết bộ giải mã PNG | Bắt được lỗi màu | Phông và antialias khác nhau giữa các runner, dễ báo đỏ giả. Phải tự bảo trì mã |
| C. `@playwright/test` với `toHaveScreenshot` | **Có** (package Node mới, hiện chỉ có `playwright`) | Có sẵn ngưỡng và cập nhật ảnh vàng | Phải duyệt quy tắc 8 và thêm Node vào CI |
| D. Ảnh để người xem, như hiện nay | Không | Rẻ | Không có hồi quy |

Đề xuất A cho CI, giữ D để soát tay. B và C chỉ làm khi chủ dự án duyệt.

**Khả năng tiếp cận (a11y).** `core/tests/test_giao_dien.py` kiểm tĩnh trên template: ô nhập có nhãn, bảng có tiêu đề cột, mỗi trang có tiêu đề riêng, nút không hoàn tác được thì có màu báo, lớp CSS có thật. Không có axe-core và không có kiểm bàn phím hay tương phản trên trình duyệt. Lựa chọn không thêm thư viện: kiểm bằng Playwright (Tab đi đúng thứ tự, `:focus-visible` có viền, Escape đóng `<dialog>`, có `role="alert"`/`status`, `aria-expanded` đổi theo trạng thái), cộng kiểm tĩnh thuộc tính `alt`/`aria-label` cho nút chỉ có biểu tượng. Lựa chọn có thêm thư viện: axe-core (JS) chèn qua `page.add_script_tag`, cần duyệt.

| Mã | Ca kiểm và kỳ vọng | Góc nhìn | Loại | Cách chạy | Ưu tiên | Tham chiếu |
|---|---|---|---|---|---|---|
| GD-01 | Mở rộng `MAN_HINH` thêm Lên đơn (`sale.staff`, urlconf CRM), Thống kê (urlconf CRM), Bảng tin, Công việc, Tài liệu, Văn hoá, Tài nguyên. Không tràn ngang. Thanh bên Bảng tin xếp xuống dưới. Lưới CRM và Báo cáo tổng hợp đã có bài 390px (xem bảng trên), không làm lại | Người dùng | E2E responsive | Tự động | P1 | AC-10.4, AC-11.11, AC-13.6 |
| GD-02 | Trên điện thoại thật hoặc DevTools 390px, `vd.staff` mở lưới, sửa một ô, lưu. `sale.staff` Lên đơn đủ hai sản phẩm. Thao tác chạm được, chữ đọc được | Người dùng | Nghiệm thu | Thủ công | P1 | AC-10.4, AC-11.11 |
| GD-03 | Lựa chọn A: tạo JSON vàng cho hình học lưới (cột ghim lệch ≤ 1 px, dòng TỔNG CỘNG dính đúng chỗ, bảng vừa màn hình khi thu thanh menu) ở 1366×800 và 390×844 | QA | Hồi quy hình ảnh | Tự động | P1 | AC-11.38, AC-22.21, AC-42.21, TL-69, TL-74 |
| GD-04 | Bàn phím trên lưới: mũi tên, Tab, Enter, Escape, Ctrl+Z/Y, nút ↶, giới hạn 100 bước hoàn tác | Người dùng | E2E a11y | Tự động | P1 | AC-11.10, AC-11.20 (đang HOAN) |
| GD-05 | Thứ tự focus và Escape theo lớp: hộp ✎ Admin, hộp Chi tiết sản phẩm, hộp lọc cột, chế độ tập trung (`grid-focus.js`, `erp-table-focus.js`). Đóng hộp xong focus quay về đúng ô. `grid-focus.js` được nạp ở `crm/base_bang_tinh.html` dòng 105 nhưng hiện không có bài nào; nơi duy nhất nhắc tới nó là `scripts/kiem-thu-solarpunk.cjs`, script đã lỗi thời | Người dùng | E2E a11y | Tự động | P2 | AC-50.11, TL-75 |
| GD-06 | Kiểm tĩnh: mọi `<button>` chỉ có SVG đều có `aria-label` hoặc `title`, mọi `<img>` có `alt`, mọi `<dialog>` có tiêu đề | QA | Kiểm tĩnh template | Tự động | P2 | `test_giao_dien.py` |
| GD-07 | Thông báo lỗi và lưu (`loi-mang.js`, `report-sua.js`, lưới) nằm trong vùng `role="alert"`/`status` để trình đọc màn hình đọc được | QA | E2E a11y | Tự động | P2 | AC-10.12, NFR-6 |
| GD-08 | Tương phản màu ngưỡng (ALERT_HIT/OK, ±10%) và chip lọc trên nền sáng: soát tay bằng DevTools | Người dùng | A11y | Thủ công | P2 | AC-42.8, AC-22.16 |
| GD-09 | Tệp tĩnh thiếu `?v=` ở `crm/master_grid.html` dòng 62–63, `crm/payments.html` dòng 4 và 39, `crm/waybill_entry.html` dòng 5 và 7. Thêm bài quét mọi `{% static '….js|css' %}` trong template phải có `?v=` | QA | Hồi quy cấu hình | Tự động | P1 | AC-10.11, TL-80 |
| GD-10 | Chromium hỏng thì CI phải đỏ: khi có `KN_E2E_BAT_BUOC=1` thì gọi `pytest.fail` thay cho `pytest.skip` | QA | Hạ tầng CI | Tự động | P0 | `tests/e2e/conftest.py:33-39`, 24 AC chỉ có bài trình duyệt |

### 3.11 Kiểm thử đơn vị JavaScript

**Hiện trạng.**
- `app/static/js/` có 19 tệp, tổng 3.477 dòng (tính cả `htmx.min.js`). CI không có bài đơn vị JS và không có bước Node (`ci.yml`: "Không cần Node ở đây").
- 9 script `scripts/kiem-thu-*-unit.cjs`, `-working-copy.cjs`, `-row-geometry.cjs` chỉ dùng `assert`/`vm`/`fs` và chạy tay. Script cắt mã `master-grid.js` bằng `source.indexOf('  async function loadBlock(')` mà không assert mốc tìm thấy.
- Máy có Node v22.22.0, nên `node:test` và `node --test` dùng được ngay, không cần thêm thư viện.
- Hai tệp đã xuất được qua `module.exports`: `master-working-copy.js` (dòng 100) và `master-row-geometry.js` (dòng 34). `date-inputs.js` chỉ gắn `window.KNDate = {enhance, canonical, display}` (dòng 134). Các hàm còn lại nằm trong closure, phải tách mới kiểm được.
- Một số tệp đã có bài e2e/pytest phủ qua trình duyệt: `report-sua.js` có `reports/tests/test_admin_sua_tong_hop_e2e.py` (3 bài) và đã kiểm `tra.redirected` ở dòng 81, 173, 179; `solarpunk-shell.js` có `core/tests/test_giao_dien.py`. `report-filters.js` **chưa có bài nào chạy hành vi JS**: `reports/tests/test_date_presets.py` là bài HTTP/Python, về JS chỉ khẳng định `"report-filters.js" in html` (dòng 58), không chạy `doiCheDo` hay chọn nhanh kỳ trên trình duyệt. `grid-focus.js` chưa có bài (xem GD-05).

**Đề xuất** (cần chủ dự án duyệt vì thêm thư mục và bước CI):
- Thư mục `tests-js/` gồm các tệp `*.test.cjs` dùng `node:test` và `node:assert/strict`. Chạy bằng `node --test tests-js/`.
- Tách logic thuần thành module UMD cùng khuôn với `master-working-copy.js`, dùng được ở cả trình duyệt lẫn Node. Ví dụ `knjsc-so.js` chứa `docSo`, `vietSo`, `lamTron`, `vietKetQua`, `tinh`, `nhom`.
- **Tệp ca dùng chung** (JSON) để kiểm chéo: pytest đọc tệp và gọi `core.money.parse_money` / `record_service.parse_value`; node:test đọc cùng tệp và gọi `docSo`. Hai phía lệch nhau thì đỏ.
- Phần cần DOM thật (lưới ảo, HTMX, dialog, focus, fetch có hết phiên) để e2e Playwright làm.
- Thêm `actions/setup-node` và `node --test` vào `ci.yml`. Đưa 9 script cũ vào CI và sửa chúng để thoát mã khác 0 khi không tìm thấy mốc `indexOf`.

| Mã | Tệp:hàm (dòng) | Cần tách? | Ca kiểm chính | Ưu tiên | Tham chiếu |
|---|---|---|---|---|---|
| JS-01 | `master-working-copy.js` (MasterWorkingCopy) | Không | Nháp chỉ giữ trong RAM. Tối đa 2.000 ô chưa lưu. Hoàn tác 100 bước. Mất quyền thì gỡ nháp đúng dòng, giữ nháp còn quyền | P0 | AC-11.20, AC-21.4 |
| JS-02 | `master-row-geometry.js` (cây Fenwick) | Không | Dòng cao 28–2.000 px. `at(pixel)` và vị trí cộng dồn đúng sau khi đổi chiều cao, xoá hay chèn dòng. Biên 0 và cuối | P0 | AC-11.44 |
| JS-03 | `date-inputs.js`: `canonical` (8), `display` (18), `autoSlash` (31) | Nạp qua `vm` với `window` giả, hoặc tách | 29/02/2025 không hợp lệ, 29/02/2028 hợp lệ. Gõ 8 số liền thành DD/MM/YYYY. `display` đổi `Z`/`+00:00` sang giờ Việt Nam (+7 cố định). Đầu vào giờ trên ô ngày thì trả null | P1 | ADR-032, AC-32.1 |
| JS-04 | `report-entry.js`: `docSo` (29), `vietSo` (53) | Có | Bộ ca dùng chung với `parse_money`: `1.234`, `1,5`, `1.2345`, `12,345,678`, `-5`, `₫ 1.000`, số nguyên bỏ dấu `.,`. Ghi nhận các ca đang khớp sai giữa hai phía (lỗ hổng "1.2345 → 12345", nhánh INTEGER) | P0 | ADR-046, AC-46.10, TL-03 |
| JS-05 | `report-entry.js`: `lamTron` (122), `vietKetQua` (127), `tinh` (132) | Có | Làm tròn nửa về chẵn khớp Decimal của máy chủ. Chia cho 0 ra NaN thì ô để trống. Số lớn hơn 2^53. Phần trăm | P1 | AC-43.6 |
| JS-06 | `master-grid.js`: `parseTSV` (915) | Có | Ô có ngoặc kép, `""` lồng, xuống dòng CRLF/LF trong ô, tab cuối dòng, chuỗi rỗng. Dán 2.000 ô (`GRID_PASTE_CELLS_MAX`) | P0 | AC-11.x dán |
| JS-07 | `master-grid.js`: `json` (54) | Có (nhận `Response` giả) | 4xx có `error`/`code`/`conflicts`. Bị chuyển về `/dang-nhap/` thì `status=403`. Content-Type không phải JSON thì báo lời tiếng Việt | P0 | AC-10.12, TL-18 |
| JS-08 | `master-grid.js`: `columnLetter` (413), `historyValue` (1201), `khoaDo` (562) | Có | A…Z, AA, AZ, BA. Giá trị trống hiện `(trống)`. Ngày đi qua `KNDate.display`. Object thì `JSON.stringify` | P2 | AC-21.13 |
| JS-09 | `master-grid.js`: `cellValue` (619) | Có (phụ thuộc `working`, `config`) | Lớp style `fs`/`c`/`bg` được thay chứ không cộng dồn. Ô bẩn hiện giá trị nháp. Ô datetime cắt còn 16 ký tự | P1 | ADR-021 |
| JS-10 | `waybill-feedback.js`: `responseJSON` (5); `payments.js`: `json` (16) | Có | Gặp redirect hết phiên thì phải báo lỗi, không coi là lưu thành công. Hiện **thiếu** kiểm `response.redirected`. Làm theo mẫu đã có của `report-sua.js` (dòng 81, 173, 179) | P0 | AC-1.4, AC-21.15, AC-26.x |
| JS-11 | `order-entry.js`: `summaryText` (41), luật loại tiền theo quốc gia (28) | Có | Lời riêng cho hết phiên, 403, 5xx và lỗi nhập. Quốc gia đổi thì loại tiền đổi theo `MARKET_CURRENCIES` | P1 | AC-6.14, ADR-031 |
| JS-12 | `staff-code.js` cờ `manual`; `chon.js` `ADD_SENTINEL '__them__'` | Có | Chỉ điền khi ô mã trống. Chọn `__them__` thì mở hộp thêm và không gửi chuỗi sentinel lên máy chủ | P2 | ADR-037, ADR-013 |
| JS-13 | Cụm hàm của `master-grid.js` mà script cũ cắt bằng `indexOf` (`loadBlock`, `saveAll`, `poll`, `retainReadableDrafts`) | Có (tách dần) | Thứ tự thử lại 1-2-4-8 giây, tối đa 4 lần. Gộp lưu 500 ms, tối đa 2 giây. Nhánh 403 khi lưu không được xoá nháp (lỗ hổng hết phiên) | P1 | AC-10.12, AC-21.4 |

**Để e2e làm (cần DOM):** cuộn ảo và ghim cột, contextmenu mở Lịch sử ô (`master-grid.js:1228`), HTMX swap và `htmx:beforeSwap` của khung CRM (thiếu bộ chặn `/dang-nhap/`), focus và Escape, `crypto.randomUUID` khi không ở secure context (chưa xác minh), `report-filters.js::doiCheDo` (fetch rồi DOMParser) và chọn nhanh kỳ trên trình duyệt: **chưa có bài nào**, vì `reports/tests/test_date_presets.py` chỉ kiểm phía máy chủ và sự có mặt của thẻ script, `phan-trang.js` trên Lịch sử, Đã bỏ và Tổng hợp kiểu cũ.

### 3.12 Vận hành: phát hành, sao lưu, quay lui, launcher

**Dãy phát hành chuẩn** (`deploy/production/README.md` dòng 62-104, đã diễn tập ngày 08.10). Mọi lệnh trên VPS phải truyền đủ `-f compose.yml -f compose.vps.yml` (README dòng 63-64). Mỗi bước cần kiểm như sau.

| Bước | Lệnh / điểm kiểm | Đạt khi | Tham chiếu |
|---|---|---|---|
| 0 | Chỉ đọc: tree của main đúng bản đã kiểm; `.env` đủ hai cookie domain, `*_URL` https; không còn việc nền đang chạy. Chạy SQL đếm mã đơn trùng và ô chữ NFD (khuôn trong biên bản 08.10), chỉ in số đếm. Rồi `up -d db broker cache` | Biết trước số mã trùng/NFD (khác 0 thì chuẩn bị `kiem_tra_du_lieu --sua` ở bước 5). db, broker, cache chạy | README bước 0 (dòng 71-74), TL-76, TL-79 |
| 1 | `docker compose -f compose.yml -f compose.vps.yml config --quiet` | Thoát mã 0 | README (nội dung `compose.vps.yml` không có trong kho, chưa xác minh) |
| 2 | `check --deploy --fail-level WARNING` chạy trên **cả** crm và erp | Thoát mã 0 | TL-85, D9 |
| 3 | Sao lưu bằng `pg_dump` tay vào `/opt/knjsc-runtime/release-*/database.dump`, rồi phục hồi thử vào DB tạm với `--exit-on-error` | Phục hồi thử đạt. Bản chưa phục hồi thử thì chưa được tính | NFR-9 |
| 4 | `stop crm erp worker heavy beat` | Không còn yêu cầu ghi nào lọt vào | TL-81, D2 |
| 4b | `docker compose --profile maintenance run --rm static-owner` (chạy `chown 1000:1000 /staticfiles` bằng user 0 trên volume `static`) | Thoát mã 0. Volume `static` thuộc `1000:1000`, để `collectstatic --clear` ở bước 7 không lỗi quyền | README dòng 81, `deploy/production/compose.yml` dòng 31-36 (`profiles: [maintenance]`) |
| 5 | `run --rm --no-deps -e PGOPTIONS='-c lock_timeout=10s' crm python manage.py migrate --noinput` | Thoát mã 0. Thoát khác 0 thì **DỪNG**, không đổi image. Gặp mã trùng thì chạy `kiem_tra_du_lieu [--sua]` | TL-76, D6 |
| 6 | `tao_bang_van_don`, `configure_erp_reports`, `configure_delivery_daily_report` | Chạy lại không làm đổi gì (đã có bài idempotent ở `reports/tests/test_activity.py`) | Quyết định 001, ADR-022 |
| 7 | `collectstatic --noinput --clear` | sha256 của `master-grid.js` do domain trả về khớp tệp trong image | TL-80, D1 |
| 7b | `gan_ma_nhan_su_cu` chạy xem trước (không cờ), đọc kết quả, rồi mới chạy `gan_ma_nhan_su_cu --xac-nhan` | Lượt xem trước không ghi gì vào DB. Lượt `--xac-nhan` chỉ gán mã cho nhân sự đã liệt kê ở lượt xem trước; chạy lại lần nữa không đổi gì | README dòng 96-97, ADR-037 |
| 8 | `up -d --no-deps crm erp worker heavy beat`, rồi `nginx -t && nginx -s reload` | Container db không khởi động lại (`StartedAt` không đổi) | TL-84, D3 |
| 9 | Sau phát hành: `RestartCount`/`OOMKilled`, `kiem_tra_du_lieu --bang van_don` chạy bằng `run --rm`, `VACUUM ANALYZE` | 0 lần OOM, 0 chỗ lệch | TL-83 |

**Quay lui:** dừng dịch vụ, chạy `configure_*` và `collectstatic --clear` **bằng image cũ**, đổi `.env`, rồi `up -d --no-deps`. Không đảo migration (đảo `reports/0006` làm mất dữ liệu). Không restore DB chỉ để quay lui mã.

| Mã | Ca kiểm và kỳ vọng | Góc nhìn | Loại | Cách chạy | Ưu tiên | Tham chiếu |
|---|---|---|---|---|---|---|
| VH-01 | Cửa sổ phát hành: probe đọc lưới 5 lượt mỗi giây và một tab `vd.staff` gõ liên tục. Trong khoảng gián đoạn chừng 20 giây lưới báo lỗi tiếng Việt; có mạng lại thì lưu đúng một lần, không ghi trùng | Người dùng | Diễn tập phát hành | Bán tự động | P0 | TL-81, TL-84, AC-10.12 |
| VH-02 | Migrate gặp khoá: một giao dịch dài đang giữ `forms_builder_datarecord` thì migrate thoát sau khoảng 10 giây với `lock timeout`. Chạy lại sau đó thì đạt | QA | Diễn tập migration | Bán tự động | P1 | README bước 4 |
| VH-03 | Mã đơn trùng (kể cả cặp chỉ khác NBSP và ô NFD) làm migrate dừng trước khi áp. `kiem_tra_du_lieu --sua` đổi thành `TRUNG-<số dòng>-<mã cũ>`, chạy lại migrate đạt. Số đếm ở bước 0 khớp số dòng `--sua` đã đổi | Người dùng | Migration + lệnh | Bán tự động | P0 | TL-76, TL-79, D10, D11 |
| VH-04 | Quay lui rồi tiến lại trên bản sao: ở mỗi mốc so sha256 static, panel Bộ lọc không lỗi JS, đếm báo cáo MKT có currency khác VND nộp trong cửa sổ quay lui | QA | Diễn tập | Bán tự động | P1 | TL-80, D1, ADR-047 |
| VH-05 | Kiểm tĩnh: mọi `collectstatic` trong `scripts/**` và `deploy/**` có `--clear`; mọi `manage.py check` trong script phát hành có `--deploy --fail-level WARNING`. Hiện đỏ ở `scripts/grid-flags-check/deploy.sh` dòng 37 và 61 | QA | Kiểm tĩnh | Tự động | P2 | TL-80, TL-85 |
| VH-06 | Dựng image `INSTALL_DEV=0` trong CI: không có pytest, locust, playwright; có `pg_dump`. Chạy entrypoint với Postgres trống và `RUN_MIGRATIONS=1`: có bảng `van_don`, log không có `CANH BAO`, entrypoint có CRLF vẫn chạy | QA | Smoke container | Tự động | P1 | Q44, K21, quyết định 001 |
| VH-07 | Sao lưu rồi phục hồi thật vào DB tạm: đếm số dòng từng bảng `public` và md5 của `DataRecord.data` khớp, Decimal giữ nguyên số lẻ. Bỏ qua kèm lý do khi máy thiếu `pg_restore` | QA | Tích hợp DB (`cham`) | Tự động | P0 | AC-10.5, NFR-10, BR-8 |
| VH-08 | `run_restore` gặp `TimeoutExpired`/`FileNotFoundError` phải ném `BackupError` tiếng Việt kèm audit "THẤT BẠI". `run_backup` gặp `RuntimeError` thì job FAILED, tệp `.part` bị xoá | QA | Đơn vị (runner giả) | Tự động | P1 | NFR-10, NFR-19, TL-23 |
| VH-09 | Kiểm tương thích: client 17 trong image ghi bản dump, `pg_restore --list` trong container db 16 có đọc được không (chưa xác minh) | QA | Diễn tập | Thủ công | P1 | AC-10.5 |
| VH-10 | Runbook phục hồi bản sao lưu đêm trên VPS chạy qua `run --rm crm` (vì `scripts/backup.sh` và `restore.sh` chỉ hợp với dịch vụ `web` local). Bấm giờ từ sự cố tới lúc đăng nhập lại: dưới 4 giờ | QA | Diễn tập vận hành | Thủ công | P1 | NFR-10, AC-10.5 |
| VH-11 | Có ít nhất một bản sao lưu không quá 24 giờ nằm ngoài VPS (hiện `BACKUP_DIR` nằm trong volume `storage`). Giả lập mất volume rồi phục hồi được | QA | Vận hành | Thủ công | P1 | NFR-20, NFR-9 |
| VH-12 | Sao lưu không gồm `storage/tai-lieu`: phục hồi xong thì tài liệu báo "Tệp không còn trên máy chủ". Ghi nhận và đề xuất sao lưu tệp | Người dùng | Sao lưu | Thủ công | P1 | K30 |
| VH-13 | Lịch beat: mỗi mục `CELERY_BEAT_SCHEDULE` trỏ tới task đã đăng ký, đúng giờ (02:00 sao lưu, 03:00 dọn tệp, `*/15` canh kẹt, ngày 1 lúc 01:00 thưởng sao, 06:00 thiệp), múi giờ `Asia/Ho_Chi_Minh` | QA | Đơn vị cấu hình | Tự động | P1 | NFR-19, NFR-16, FR-10.4, FR-12.4 |
| VH-14 | Entrypoint chạy bù: tắt máy qua mốc 06:00 và ngày 1, bật lại thì container web chạy `thiep_sinh_nhat` và `thuong_sao_thang` đúng một lần, khởi động lại lần nữa không nhân đôi. Lệnh hỏng chỉ in `CANH BAO`, web vẫn lên | Người dùng | Tích hợp + thủ công | Bán tự động | P1 | ADR-017, FR-10.4, FR-12.4 (`culture/tests/test_van_hoa.py`, `feed/tests/test_bang_tin.py`, chưa đọc hết) |
| VH-15 | `cap-nhat-local.bat` và `KN JSC.bat`: sau `migrate` **và** sau `tao_bang_van_don` phải có `if errorlevel 1 goto :loi` trước dòng ghi `storage\.kn-jsc-lan-truoc`. Kiểm tĩnh bằng pytest đọc tệp. Thủ công: migration lỗi giả thì không ghi dấu vết | QA | Kiểm tĩnh + thủ công Windows | Bán tự động | P0 | sự cố 06.09.2026, TL-76 |
| VH-16 | Máy sạch: chạy `scripts/Cai dat KN JSC.bat` từ Downloads → tìm thấy kho, tạo lối tắt (cả khi Desktop nằm trong OneDrive), `du_lieu_mau` chạy trước `configure_*`, Báo cáo tổng hợp đủ ba nguồn, `quantri` đăng nhập được. Lần mở thứ hai mất vài giây và không migrate | Người dùng | Thủ công Windows | Thủ công | P1 | docs/04 mục 17.1, ADR-022 |
| VH-17 | Máy cũ: kéo nhánh có migration mới → màn hình in "Ma tren may khac lan chay truoc", migrate chạy, `restart worker beat`. Requirements đổi thì có "dang dung lai image", kể cả khi `LAN_TRUOC` trỏ tới SHA không còn (hiện `git diff` lỗi bị nuốt) | Người dùng | Thủ công Windows | Thủ công | P1 | `KN JSC.bat` bước 4 |
| VH-18 | Kéo mã thất bại: (a) đang gộp dở → báo "dang do dang mot lan gop"; (b) rút mạng → "KHONG KEO DUOC MA MOI"; (c) không ở nhánh main → nhắc. Cả ba trường hợp hệ thống vẫn mở bằng bản đang có | Người dùng | Thủ công Windows | Thủ công | P1 | sự cố 06.09.2026 |
| VH-19 | Hai bản clone dùng chung project compose `knjsc`: clone cũ không migrate trong khi DB đã ở schema mới. Ghi nhận lỗi | Người dùng | Thủ công Windows | Thủ công | P2 | `KN JSC.bat` |
| VH-20 | Thiếu healthcheck cho crm và erp, log json-file không giới hạn: theo dõi dung lượng đĩa và `docker inspect` sau 7 ngày. Đề xuất healthcheck gửi kèm `X-Forwarded-Proto` | QA | Vận hành | Thủ công | P2 | README "chưa đặt logging:" |
| VH-21 | Mọi commit sắp phát hành có lượt CI `success`, không phải `cancelled` (`cancel-in-progress` đang áp cả cho push lên main) | QA | Quy trình | Bán tự động | P2 | `.github/workflows/ci.yml` |
| VH-22 | crm và erp dùng chung `SECRET_KEY` (chỉ so 8 ký tự đầu của sha256), chung `SESSION_COOKIE_NAME` và `DOMAIN`, chung `DJANGO_SETTINGS_MODULE` đúng loại cho worker | QA | Kiểm cấu hình | Bán tự động | P2 | AC-1.10, AC-1.11, NFR-8 |
| VH-23 | Service `static-owner`: (a) kiểm tĩnh `deploy/production/compose.yml`: có `profiles: [maintenance]` (để `up -d` thường không chạy nó), `user: '0'`, chỉ gắn volume `static`, không có `ports`; (b) kiểm tĩnh README: lệnh `--profile maintenance run --rm static-owner` nằm sau `stop` và trước `collectstatic`; (c) diễn tập trên bản sao: làm volume `static` thuộc root, bỏ bước 4b thì `collectstatic --clear` lỗi quyền, chạy bước 4b thì đạt | QA | Kiểm tĩnh + diễn tập | Bán tự động | P1 | `deploy/production/compose.yml` dòng 31-36, README dòng 81 |
| VH-24 | Cấu hình tài nguyên VPS 4 GB: dựng `docker compose -f compose.yml -f compose.vps.yml config` trên VPS, cộng `mem_limit` mọi service chạy thường trực và so với RAM. Đạt khi tổng `mem_limit` không vượt RAM VPS sau khi chừa phần cho hệ điều hành và page cache (mức chừa do chủ dự án chốt), `shared_buffers` của db nhỏ hơn hẳn `mem_limit` của db, và `work_mem` đã tính cả `SET LOCAL work_mem='64MB'` của Thống kê (README dòng 9-12). Trong kho, `compose.yml` riêng lẻ cộng lại khoảng 19,75 GB (db `8g` kèm `shared_buffers=4GB` dòng 41/45, broker `1536m` dòng 57, cache `768m`, crm `3g` dòng 70, erp `2g` dòng 74, worker `1536m` dòng 78, heavy `2g` dòng 82, beat `512m`, proxy `512m`), nên chạy thiếu `compose.vps.yml` là sai. `compose.vps.yml` không có trong kho, giá trị thật chưa xác minh | QA | Kiểm tĩnh cấu hình | Bán tự động | P0 | README dòng 5-12 và 63-64, TL-83 |

### Critical Files for Implementation
- /home/user/KNJSC/deploy/production/README.md
- /home/user/KNJSC/deploy/production/compose.yml
- /home/user/KNJSC/app/core/constants.py
- /home/user/KNJSC/app/forms_builder/services/table_service.py
- /home/user/KNJSC/app/knjsc/settings/test.py
