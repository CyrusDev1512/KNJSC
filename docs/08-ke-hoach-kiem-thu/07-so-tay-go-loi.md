> Phần của [Kế hoạch kiểm thử toàn diện KNJSC](../08-ke-hoach-kiem-thu-toan-dien.md) — mục lục, lộ trình P0/P1/P2 và rủi ro còn lại nằm ở tệp đó.

## 7. Sổ tay gỡ lỗi

### 7.1 Quy trình năm bước

| Bước | Làm gì | Công cụ cụ thể | Đầu ra |
|---|---|---|---|
| 1. Tái hiện | Lặp lại lỗi với tài khoản mẫu, ghi URL, cổng, vai, các bước, giờ. Lỗi không đều thì thử nhiều lần, ghi tỉ lệ | Tài khoản trong docs/tai-khoan-mau.md; dữ liệu cỡ thật: `seed_perf`, `nap_du_lieu_van_don`, `nap_bao_cao_mau`; muốn hết phiên nhanh thì đặt `SESSION_IDLE_TIMEOUT_SECONDS` | Các bước tái hiện chắc chắn, hoặc tỉ lệ ra lỗi |
| 2. Khoanh tầng | Xác định lỗi nằm ở tầng nào trong 7.2. Bắt đầu từ Network: mã trả về và phản hồi | DevTools Network/Console, `X-Request-ID`, `Server-Timing` | Tầng nghi ngờ |
| 3. Đọc dấu vết | Theo bảng 7.3: log `knjsc.request`, nhật ký hoạt động, `GridCellHistory`, `BackgroundJob`, khoá Postgres | Lệnh và truy vấn ở 7.3, 7.4 | Nguyên nhân gốc kèm bằng chứng (dòng log, bản ghi) |
| 4. Sửa kèm bài hồi quy | Viết bài kiểm đỏ trước (skill test-driven-development), sau đó sửa cho xanh. Docstring ghi mã AC (`"""AC-x.y — …"""`) để `test_truy_vet` bắt được | `pytest -m "not cham" --lf -x`; bài HTTP bên CRM thì đặt urlconf (`crm/tests/conftest.py` tự đặt `urls_bangtinh`; trong `tests/e2e` phải tự đặt) | Bài đỏ trên mã cũ, xanh trên mã mới |
| 5. Ghi TL và tầng lẽ ra bắt | Thêm hoặc đóng TL trong `docs/test-log.md`, ghi **tầng nào trong chín tầng của docs/06 lẽ ra phải bắt** và vì sao chưa bắt | docs/06 mục "Chín tầng kiểm thử" | TL có trường "Tầng lẽ ra bắt" và bài hồi quy đặt ở đúng tầng đó |

Chín tầng để ghi ở bước 5 (docs/06):

| Tầng | Tên | Bài đại diện | Hợp với loại lỗi |
|---|---|---|---|
| 1 | Đơn vị | `tests/test_hop_trang.py`, rải trong module | Ép kiểu, đọc tiền (TL-03) |
| 2 | Tệp chuyển đổi | `core/tests/test_chuyen_doi.py` | Migration sai, thiếu cột (TL-76) |
| 3 | Kiểm khói | `tests/test_khoi.py` | 500 trên một đường dẫn hoặc một vai |
| 4 | Chức năng | Từng module, `tests/test_luong_ba_bo_phan.py` | Luồng HTTP sai kết quả |
| 5 | Hộp đen | `tests/test_ma_tran_phan_quyen.py` | Lệch ma trận quyền (TL-01) |
| 6 | Hộp trắng | `tests/test_hop_trang.py` | Nhánh lỗi, huỷ giao dịch |
| 7 | Giao diện | `core/tests/test_giao_dien.py` | Lớp CSS, nhãn ô nhập |
| 8 | Đầu-cuối trình duyệt | `tests/e2e/`, `scripts/kiem-thu-master-*.cjs` | Bàn phím, HTMX, mất mạng, JS lưới |
| 9 | Hiệu năng | `tests/test_hieu_nang.py` (dấu `cham`), Locust | Chậm, N+1, kiểm tải |

### 7.2 Khoanh tầng nhanh

| Dấu hiệu ở DevTools / màn hình | Tầng nghi | Bước kế |
|---|---|---|
| Không có request nào được gửi, Console có lỗi đỏ | JS phía trình duyệt | Kiểm static cũ (`?v=`), chạy script Node của tệp JS đó |
| Request 302 về `/dang-nhap/` (hoặc `responseURL` chứa `/dang-nhap/`) | Phiên / middleware | Xem `doi_quyen=1`, `session_epoch`, hết phiên |
| 403 / 404 có trang tiếng Việt | Quyền / phạm vi (`in_scope`, ADR-040) | Tra AuditLog DENIED, `get_user_scope` |
| 409 | CAS / đồng thời | So `old` hoặc `version` với DB |
| 400 có lời cụ thể | Kiểm dữ liệu vào (form, `parse_value`) | Đọc phản hồi; SQLSTATE 22001/22003 cũng ra 400. Lưới trả 400 `code='currency_confirmation'` là đang chờ xác nhận đổi/xoá Quốc gia (AC-33.8, ADR-046), không phải lỗi |
| 500 | View / dịch vụ / DB | Log `web`/`bangtinh`, `sqlstate` trong `knjsc.request` |
| 200 nhưng số sai | Dịch vụ / dữ liệu (JSON lệch `val_*`, đệm) | `kiem_tra_du_lieu`, xoá đệm `crm`, tính lại bằng shell |
| Tác vụ đứng ở "Chờ xử lý"/"Đang chạy" | Celery / Redis / worker | `core_backgroundjob`, `celery inspect` |
| Request chậm, treo | DB / khoá | `ms` so với `db_ms`, `pg_locks`, `pg_stat_activity` |

### 7.3 Triệu chứng → chỗ nhìn đầu tiên

| Triệu chứng | Chỗ nhìn đầu tiên | Lệnh / dấu hiệu cụ thể | Nguồn |
|---|---|---|---|
| Request chậm hoặc 500 không rõ lý do | Log `knjsc.request` | Bật `CRM_REQUEST_METRICS=1` (production luôn bật), chạy `docker compose logs bangtinh \| grep knjsc.request`; tìm theo `request_id` lấy từ header `X-Request-ID`. `ms` ≈ `db_ms` là nghẽn DB; `queries` tăng vọt là nghi N+1; `sqlstate` 40001/40P01/55P03 là xung đột/khoá | `core/request_metrics.py`, `knjsc/settings/base.py:131` |
| Cần p95 của một dịch vụ | Gom log | `python3 scripts/gom-p95-vps.py --compose compose.yml --compose compose.vps.yml --since 24h [--dich-vu erp]`; mã 0 đạt, 1 vượt ngưỡng, 2 thiếu mẫu (ít hơn 20 mẫu) | `scripts/gom-p95-vps.py` |
| Lưới chậm hoặc lạ phía trình duyệt | Chẩn đoán JS | `window.KNJSC_MASTER.diagnostics()`; khi bật metrics: `window.KNJSC_MASTER.requestDiagnostics()` (100 request gần nhất kèm `X-Request-ID`) | `static/js/master-grid.js` |
| Ô lưới bị đổi, không biết ai đổi | `crm_gridcellhistory` | Lọc theo `record_id`, `column`; xem `before`/`after`; `column='__row__'` là xoá/khôi phục dòng. Tra một lượt ghi bằng UUID ở `crm_gridmutationreceipt` (8 ký tự đầu hiện trong hộp Lịch sử) | Model `GridCellHistory` |
| 409 "Có ô vừa được thay đổi" | So giá trị gửi lên với DB | So `old` với `forms_builder_datarecord.data->>'<cột>'`, nhớ dạng NFD/NFC (`record_service.same_value`, TL-79). "Mã thao tác đã được dùng với nội dung khác" là cùng UUID khác fingerprint; 400 `schema_changed` là cấu trúc cột đổi giữa chừng | crm |
| Xoá/đổi Quốc gia trên lưới không ghi, hoặc Loại tiền không trống theo | Luồng xác nhận loại tiền | Phản hồi 400 `currency_confirmation` kèm `currency_confirmations`; JS phải gửi lại cùng thay đổi kèm danh sách đó. Đối chiếu với `crm/tests/test_market_currency.py::test_clearing_country_clears_currency_and_asks_when_row_has_money` (AC-33.8); lên đơn/nhập tệp bỏ trống Quốc gia bị chặn ở `orders.services.currency_service.for_label` | crm, orders |
| Tab khác không thấy thay đổi | Bảng đồng bộ | `crm_gridpendingchange` phải RỖNG sau mỗi commit; còn dòng là trigger hỏng. Xem `crm_gridrevision`, `crm_gridchange` (`reset=true` khi hơn 2000 ID) | crm |
| Số đếm/thống kê cũ | Đệm Redis `crm` (luôn bật, kể cả khi cờ `CRM_OPT_*` tắt) | `from django.core.cache import caches; caches['crm'].clear()`; Thống kê thêm `?lam_moi=1` | `knjsc/settings/base.py` |
| Lưới "thiếu cột" khó hiểu với một người | localStorage | Xoá khoá `kn-master:<user id>:<mã bảng>` | `master-grid.js` |
| Ai đó bị chặn hoặc kêu bị chặn | Nhật ký hoạt động `core_auditlog` | `AuditLog.objects.filter(action='denied')…`; dòng DENIED có `target_type='path'`, `target_id` là URL bị chặn. CEO bị chặn ở tầng dịch vụ Tài nguyên/Tài liệu thì **không** có dòng DENIED. Không update/delete được (RuntimeError, BR-6) | `core.models.AuditLog` |
| Không đăng nhập được, bị khoá | `org_userprofile` | `failed_login_count`, `locked_until` (UTC), `must_change_password`, `deleted_at`; mật khẩu bắt đầu bằng `!` là đã xoá mềm. Gỡ khoá **chỉ trên local**: `UserProfile.objects.filter(user__username='x').update(failed_login_count=0, locked_until=None)` | org |
| Bị đẩy ra liên tục với `?doi_quyen=1` | Phiên | So `session['auth_epoch']` với `profile.session_epoch`; `Session.objects.get(pk=<cookie>).get_decoded()`. Cookie tên `knjsc_session_v2` trên VPS, `sessionid` ở local (ADR-030) | core |
| Phiên chung ERP↔CRM hỏng trên VPS | Cấu hình | `check --deploy` bắt `core.E001`; với CRM kiểm `BANGTINH_GOC`; `python -c "…print(settings.DEBUG, settings.SESSION_COOKIE_DOMAIN)"` | `knjsc/settings/` |
| Thấy/không thấy dữ liệu sai phạm vi | Phạm vi | `from core.scope import get_user_scope; get_user_scope(u)`. Tạo `u` mới mỗi lần đo vì kết quả đệm ở `_knjsc_scope`. Leader chỉ có team mà `Team.leader_id` = chính mình. So với `Model.objects.in_scope(u).count()` | `core/scope.py` |
| Nút quản lý tài khoản không hiện | Chính sách tài khoản | `AccountPolicy(actor).can_manage(target.profile)` | `org/services/account_management.py` |
| Quyền bảng lạ, quyền đã thu vẫn hiện | Grant | `grant_service.clear_cache(user)` rồi `_grants_of(user)`; `Grant.objects.filter(table=t).values('id','user_id','team_id','action','deleted_at')`. `grants_of_table` không lọc `deleted_at` | forms_builder |
| URL `/bang/…` trả 404 ở 8021 nhưng 200 ở 8020 | Thiết kế ADR-040 | Đúng thiết kế: CRM bọc `_chi_bang_van_don`. Lỗi "không sửa được" ở 8021 thì kiểm `DJANGO_SETTINGS_MODULE` của container và `GRID_ONLY_TABLES` | `knjsc/settings/bangtinh.py` |
| Lọc/báo cáo sai mà màn hình đúng | JSON lệch cột tách `val_*` | `manage.py kiem_tra_du_lieu --bang <mã>` (`--sua` để tính lại; mã thoát 1 khi còn lệch). SQL: `SELECT id, data->>'<cot>', val_revenue, val_date, val_phone_key FROM forms_builder_datarecord WHERE table_id=<id> AND deleted_at IS NULL …` | `orders/services/integrity_service.py` |
| Tiền sai nghìn lần hoặc trăm lần | `parse_money` | `from core.money import parse_money; parse_money('0.125')` → `Decimal('125')` (TL-03); `parse_value` với cột integer và `'1500.0'` → 15000 | `core/money.py`, `record_service.py` |
| Báo cáo tổng hợp hiện bản cũ (có tab "Theo sản phẩm", không có "· Tiền: ₫") | `ReportSource` | `ReportSource.objects.values('table__code','kind','columns')`; thiếu thì chạy `configure_erp_reports` và `configure_delivery_daily_report`; tìm "CANH BAO: configure_erp_reports loi" trong log `web` (từ `deploy/entrypoint.sh`) | reports |
| Số Báo cáo tổng hợp sai | Tính lại bằng shell | `activity_service.select_source(user,'bao_cao_mkt')` → `build(...)` → `aggregations.total_rows(r)`, `r.currency_warning` | `reports/services/activity_service.py` |
| 409 khi sửa báo cáo | `version` của form | So `record.updated_at.isoformat()` với ô ẩn `version`; hộp ✎ gửi `goc-<mã trường>`, header `X-Bao-Cao-Doi`; 204 là đã lưu | reports |
| Màu ô báo cáo sai | `aggregations.cell_class` | Có `thresholds` thì ba bậc tuyệt đối, ngưỡng tiền chỉ áp dòng VND; không có thì ±10% (`THRESHOLD_BAND`) so với TỔNG CỘNG cùng loại tiền | reports |
| Tổng quan một khối báo "Không tải được số liệu" | Log `web` | `logger.exception("Khối Tổng quan '%s' lỗi")` (`dashboard.services.dashboard_service._khoi`), kể cả `OutOfScopeError` | dashboard |
| Trang chủ CRM hoặc Thống kê lỗi một khối | Log `bangtinh` | "Khối Trang chủ KN CRM '%s' lỗi" (`tong_quan_service`); "Không dựng được thống kê profile …" (`statistics_service._unavailable`) | crm |
| Gộp/Không gộp tự tải lại cả trang | Fetch nhận 403/302 | `report-filters.js` hàm `doiCheDo`; đặt breakpoint ở `location.assign(url)` | `static/js/report-filters.js` |
| Ngày hiện lệch | Múi giờ | `TIME_ZONE='Asia/Ho_Chi_Minh'`, `submitted_at` lưu UTC; `SELECT submitted_at AT TIME ZONE 'Asia/Ho_Chi_Minh'`; ô ngày: `window.KNDate.canonical('03/09/2026')` | reports |
| Tác vụ nền đứng, không xong | `core_backgroundjob` | `status` (`draft`, `pending`, `running`, `done`, `failed`, `stale`), `error`, `summary`, `updated_at`; trang `/tac-vu/?trang_thai=stale`. RUNNING mà `updated_at` đứng yên là worker chết; TL-23 chưa tự xử lý, `danh_dau_tac_vu_ket` chỉ xử lý PENDING. Chỉ đổi tay sang `failed` sau khi xác nhận worker không chạy | `core/constants.py` `JobStatus` |
| Celery không nhận việc | Worker / hàng đợi | `docker compose exec worker celery -A knjsc inspect active\|reserved\|registered\|active_queues` (worker nghe `celery`, heavy nghe `crm_heavy`); `redis-cli LLEN celery` / `LLEN crm_heavy`. Redis tắt thì job FAILED với `HANG_DOI_CHET` | knjsc |
| Không có gì tự chạy theo lịch | Beat | `logs beat`, phải có "Scheduler: Sending due task …"; tệp lịch `/storage/celerybeat-schedule`. Thiệp sinh nhật 06:00, thưởng sao ngày 1 lúc 01:00. VPS đặt `RUN_MIGRATIONS '0'` nên chạy bù phải chạy tay | feed, culture |
| Thiệp sinh nhật / sao thiếu hoặc thừa | Bảng nghiệp vụ | `SELECT subject_id, birthday_on, deleted_at FROM feed_post WHERE kind='sinh_nhat' …`; `culture_staraward` theo `period`; chạy tay `thiep_sinh_nhat --ngay <ngày quá khứ>`, `thuong_sao_thang --thang YYYY-MM` | feed, culture |
| Bảng xếp hạng trống, báo "Chưa có tỉ giá cho XXX" | Tỉ giá | `settings.EXCHANGE_RATES_VND`, `core.money.rates_label()`; biến chỉ nhận dạng `USD=25400` | culture |
| Sao lưu hỏng | Tệp và tác vụ | Có `.part` sót lại là lần chạy bị cắt; `pg_restore --list <tệp> \| head`; lý do chi tiết ở `BackgroundJob.error` (nhật ký chỉ ghi "THẤT BẠI — xem tác vụ #") | `BACKUP_DIR` |
| Tải tệp xuất báo "Quyền xem các dòng trong tệp đã thay đổi" | `check_download` | Phạm vi người dùng đổi, tệp không hỏng; xem `exported_row_ids` trong `job.summary` | forms_builder |
| "Tệp không còn trên máy chủ" (Tài liệu) | Đĩa | So `documents_document.file_path` với `STORAGE_DIR/tai-lieu/` (uid 1000); đĩa đầy trả 507 kèm thư cảnh báo | documents |
| Lưới treo khi đang nhập Excel; mã đơn "đang bận" | Khoá tư vấn Postgres | `SELECT * FROM pg_locks WHERE locktype='advisory'`: `classid=1263424578` là khoá bảng (worker nhập giữ suốt lượt, theo mã hiện tại là bình thường); khoá mã đơn `0x4B4E4F52`, timeout 5 giây (`ORDER_CODE_LOCK_TIMEOUT`); harness `scripts/order-code-check/` | forms_builder, orders |
| Migrate treo hoặc dừng | Khoá / dữ liệu trùng | `SELECT pid, wait_event_type, state, query_start FROM pg_stat_activity WHERE wait_event_type='Lock'` (không in cột `query` trên dữ liệu thật); dừng vì mã trùng thì `kiem_tra_du_lieu --sua` bằng `run --rm` (TL-76, TL-83) | deploy |
| JS lỗi, panel Bộ lọc 404 sau phát hành hoặc quay lui | Static cũ | `collectstatic --noinput --clear`, kiểm `?v=` (`core.context_processors.phien_ban_hien_tai`, khi DEBUG tắt chỉ tính lúc khởi động nên phải restart crm/erp) (TL-80) | core |
| Container tự khởi động lại | OOM | `docker inspect -f "{{.RestartCount}} {{.State.OOMKilled}}"`, `docker stats --no-stream`; lệnh nặng chạy `docker compose run --rm` (VPS 4 GB, TL-83) | deploy |
| 500 có DataError | `sqlstate` | 22001/22003 đã đổi thành 400; mã khác (ví dụ 22P02 do inet hỏng từ X-Forwarded-For) vẫn ra 500 | core |
| HTMX bấm không phản hồi | Hộp báo lỗi chung | `base.html` `htmx:beforeSwap` chặn mọi mã ≥400 và hiện hộp báo; lỗi mạng hiện ô ở đáy màn hình (`static/js/loi-mang.js`) | templates |
| Lệch quyền giữa ERP và CRM | Bài ma trận | `pytest core/tests/test_ma_tran_quyen_hai_dich_vu.py` (`test_duong_dan_chung_deu_da_ra_quyen` đỏ khi có URL chung chưa khai) | core |
| Bài e2e treo trên CI | `faulthandler_timeout` | Bước e2e chạy `-vv -o faulthandler_timeout=120`: dòng cuối là bài vừa xong, bài treo là bài kế. Hook ở `app/conftest.py` in ngăn xếp greenlet có dấu `== TL-71: … ngăn xếp các greenlet ==` | `app/conftest.py` |
| Bài trình duyệt chạy JS dài bị treo | `_chay_co_han` | Dùng `_chay_co_han(trang, ham_js, doi_so, han_ms, capsys)` của `tests/e2e/test_ghi_chu_tu_gian_dong.py`: kết quả qua `console.log`, hạn đếm trong Python, quá hạn thì in chẩn đoán (tab sập, CPU, ngăn xếp JS) rồi `pytest.fail`. Biên bản `docs/kiem-chung-bai-18-khong-treo-20261001.md` | tests/e2e |
| Bài e2e đỏ, cần xem màn hình | Ảnh chụp | Local: `storage/e2e/` (hàm `chup()`); CI: artifact `anh-e2e` (giữ 7 ngày); `-rs` liệt kê bài bị bỏ qua | `app/tests/e2e/conftest.py` |
| "Database test_knjsc_db couldn't be flushed", "deadlock detected" | Máy chủ thử còn request dở | Xem cảnh báo TL-67; `SELECT pid, state, query FROM pg_stat_activity`, `SELECT * FROM pg_locks WHERE NOT granted` (DB test); biên bản `docs/kiem-chung-e2e-cho-may-chu-20260928.md` | `app/conftest.py` |
| Log Postgres CI có "duplicate key … core_submission_actor_key", "record_ma_don_unique", "lock timeout" | Thường là bài cố ý gây ra | Bài gửi lặp hoặc chạy đồng thời sinh ra các dòng này, không phải lỗi | CI |
| `test_truy_vet` đỏ | Docstring AC | Thông điệp liệt kê mã; tra `grep -rn '"""AC-x.y' app --include=test_*.py`; AC hoãn nằm trong `HOAN` | `app/tests/test_truy_vet.py` |
| Bài CRM nhận 404/403 bất ngờ | Urlconf / bảng | Kiểm `settings.ROOT_URLCONF`, bảng có phải `van_don` (`crm/services/catalog.chi_van_don`), `GRID_ONLY_TABLES` (mặc định `{'van_don'}` ở settings test) | crm/tests |
| Bài lệ thuộc ngày đỏ thất thường | Đồng hồ thật | Truyền `system_day` hoặc cố định "hôm nay" (TL-70) | tests |
| Script Node hỏng sau khi sửa `master-grid.js` | Chuỗi neo trong script | Kiểm các chuỗi `indexOf` (ví dụ `'  async function loadBlock('`) còn khớp mã nguồn | `scripts/kiem-thu-*.cjs` |
| Nhánh cache trúng không tái hiện được trong bài kiểm | CI không có Redis | Đè `CACHES['crm']` sang `LocMemCache` như `crm/tests/test_optimization.py` | crm/tests |
| Tác vụ nền trong bài kiểm không chạy nhánh `on_commit` | Eager | Đặt `settings.CELERY_TASK_ALWAYS_EAGER=False` như `crm/tests/test_hang_doi_chet.py`; thử ngoài bài kiểm thì gọi thẳng `feed.tasks.thiep_sinh_nhat()` trong shell | tests |

### 7.4 Bảng DB hay tra

| Phân hệ | Bảng | Ghi chú |
|---|---|---|
| Lõi | `core_auditlog`, `core_backgroundjob`, `core_submissionreceipt` | AuditLog chỉ ghi thêm (BR-6); `submissionreceipt` chống gửi lặp (AC-6.11) |
| Tổ chức | `org_userprofile`, `auth_user`, `django_session` | `session_epoch`, `locked_until` |
| Bảng động | `forms_builder_datarecord`, `forms_builder_columndef`, `forms_builder_grant` | `data` JSONB cùng các cột `val_*`; `updated_at` là phiên bản CAS |
| Lưới CRM | `crm_gridcellhistory`, `crm_gridmutationreceipt`, `crm_gridrevision`, `crm_gridchange`, `crm_gridpendingchange` | `pendingchange` phải rỗng sau commit |
| Đơn | `orders_order`, `orders_orderline`, `orders_customer`, `orders_product`, `orders_waybillitem`, `orders_waybillassignment`, `orders_paymentdocument`, `orders_paymentimage` | Tra một đơn: JOIN `orders_order.record_id` với `forms_builder_datarecord.id` |
| Báo cáo | `reports_dailyreport`, `reports_reportrevision`, `reports_reportsource` | `reportrevision` chỉ ghi thêm |
| Nội bộ | `documents_document(category)`, `feed_post`, `feed_comment`, `feed_like`, `taskboard_task`, `culture_recognition`, `culture_staraward`, `resources_resource(category)` | Xoá mềm: `deleted_at`; xem cả bản ghi đã gỡ bằng `Model.all_objects` |

### 7.5 Quy tắc an toàn khi gỡ lỗi

| Quy tắc | Lý do / nguồn |
|---|---|
| Chỉ dùng lệnh ghi (`update`, `--sua`, `du_lieu_mau`, `seed_perf --xoa-cu`) trên DB local hoặc DB test. Trên VPS phải sao lưu trước và được chủ dự án đồng ý | `du_lieu_mau` huỷ phiên (TL-30); `--sua` sửa dữ liệu |
| Không bật `log_statement=all`, không in nội dung ô hay cột `query` trên dữ liệu thật; chỉ đếm số lượng | Quy tắc 6, biên bản 08.10 |
| Không cố sửa hay xoá `AuditLog`; cũng không làm được | BR-6 |
| Mỗi lỗi sửa xong phải có bài hồi quy mang mã AC và TL ghi "tầng lẽ ra bắt" | 7.1 bước 4–5 |
| Không thêm thư viện gỡ lỗi mới khi chưa hỏi | Quy tắc 8 |

### Critical Files for Implementation
- /home/user/KNJSC/docs/test-log.md
- /home/user/KNJSC/docs/04-tieu-chi-nghiem-thu.md
- /home/user/KNJSC/docs/07-kich-ban-nghiem-thu.md
- /home/user/KNJSC/docs/backlog.md
- /home/user/KNJSC/app/crm/tests/test_market_currency.py
