> Phần của [Kế hoạch kiểm thử toàn diện KNJSC](../08-ke-hoach-kiem-thu-toan-dien.md) — mục lục, lộ trình P0/P1/P2 và rủi ro còn lại nằm ở tệp đó.

## 1. Môi trường, dữ liệu, tài khoản và tiêu chí vào/ra từng chặng

### 1.1 Các chặng

CLAUDE.md quy định bốn chặng, theo đúng thứ tự: `claude/<tên-việc>` → `Staging` → kiểm tay ở local → `main` → VPS. Không được nhảy chặng, kể cả khi sửa nóng. Trong bảng dưới, CI và diễn tập là **bước con** của một chặng, không phải chặng riêng. Mọi chỗ khác trong tài liệu (kể cả mục 6.2) gọi "Chặng N" theo cách đánh số này.

| Chặng | Chạy gì | Ai chạy | Môi trường | Dữ liệu | Tiêu chí vào | Tiêu chí ra | Thời gian ước |
|---|---|---|---|---|---|---|---|
| **1. Nhánh việc → `Staging`** | Hai bước con 1a và 1b bên dưới | Claude/Codex mở PR nháp. Chủ dự án duyệt và gộp | — | — | — | PR xanh CI. Chủ dự án duyệt (CLAUDE.md) | — |
| 1a. Làm trên nhánh `claude/<tên-việc>` (tách từ `Staging`) | Viết bài mới hoặc sửa bài theo AC (đỏ trước, xanh sau). Chạy `pytest -m "not cham"` cho app bị đụng, cộng `tests/test_truy_vet.py`. Đụng JS lưới thì chạy `node scripts/kiem-thu-master-*-unit.cjs`. Đụng e2e thì chạy bài trình duyệt liên quan | Claude/Codex | Máy ảo Claude Code web hoặc Docker local (`deploy/docker-compose.yml`), settings `knjsc.settings.test` | DB pytest riêng (`test_*`), fixture `app/conftest.py` | Việc có AC trong docs/04, hoặc có mã TL/ADR. Nếu cần thêm thư viện thì đã hỏi chủ dự án (quy tắc 8) | Bài mới đã từng đỏ trước khi sửa. Không bài nào đỏ. `test_truy_vet` xanh, bộ đếm docs/06 đã cập nhật nếu thêm AC. Không có SKIPPED mới ngoài các lý do đã biết | Ước 5–30 phút mỗi lượt chạy (chưa đo) |
| 1b. CI trên PR về `Staging` | Job `kiem-thu`: `manage.py check --settings=knjsc.settings.test`, `pytest -m 'not trinh_duyet' -rs --durations=10` (gồm cả bài `cham`). Job `e2e`: `pytest tests/e2e -m trinh_duyet -vv -rs --durations=10 -o faulthandler_timeout=120`, rồi `pytest -m trinh_duyet --ignore=tests/e2e …`. Hai tiến trình chạy riêng vì Playwright xung đột vòng lặp asyncio. Sau đó tải artifact `anh-e2e` | GitHub Actions. Chủ dự án đọc kết quả | `ubuntu-24.04`, `postgres:16-alpine`, Python 3.12, Chromium của Playwright. **Không có Redis, không Node, không build Docker, không `check --deploy`, không `--cov`** | DB test của CI | Đã mở PR nháp về `Staging` (nhánh việc chỉ chạy CI khi có PR) | Hai job xanh. Log `-rs` cho thấy bộ `trinh_duyet` **không** bị bỏ qua vì thiếu Chromium (nếu bị bỏ qua thì CI vẫn xanh, tức ⚠️; xem lỗ hổng hạ tầng). Bước `tests/e2e` dưới 8 phút (80% hạn 10 phút) | Khoảng 9 phút mỗi lượt (lượt #239 ngày 13.10: bộ chính 5 phút 58 giây; e2e 5 phút 10 giây + 2 phút 50 giây) |
| **2. `Staging` → kiểm ở local** | Bật hệ thống thật bằng `KN JSC.bat` (Windows) hoặc `./scripts/cap-nhat-local.sh`. Bấm lại đúng các thao tác mà thay đổi đụng tới, ở cả 8020 và 8021, theo docs/07 (bỏ qua bước lỗi thời) và danh mục thủ công của từng phân hệ. **Chặng này không phải pytest** | Người (chủ dự án hoặc người kiểm), trên máy mình | Docker Compose local: `db` (5433), `redis`, `web` (8020, runserver, `knjsc.settings.dev`), `worker` (chỉ nghe hàng `celery`), `beat`, `bangtinh` (8021). **Khác production:** không có cache Redis `crm` (không đặt `CRM_CACHE_URL`), không có nginx/HTTPS, hai dịch vụ cùng host khác cổng | DB phát triển (volume `db_data`). Thứ tự: `du_lieu_mau` → `configure_erp_reports` → `configure_delivery_daily_report`. Thêm `nap_du_lieu_van_don`, `nap_bao_cao_mau` khi cần nhiều dòng | PR đã gộp vào `Staging` và CI xanh. Launcher in "Ma tren may khac lan chay truoc" rồi migrate xong. `logs web` không có `CANH BAO` | Làm hết các thao tác liên quan mà không thấy sai. Còn nghi ngờ thì **để lại ở `Staging`**. Lỗi tìm được thì ghi TL vào `docs/test-log.md` | Ước 30–60 phút tuỳ phạm vi thay đổi (chưa đo) |
| **3. `Staging` → `main`** | CI chạy lại khi push lên `main` (cùng hai job như 1b) | Chủ dự án bảo gộp. GitHub Actions chạy | Như 1b | DB test của CI | Đã kiểm ở chặng 2 và không thấy vấn đề | Commit HEAD của `main` có lượt CI `completed/success`, **không phải `cancelled`**. `concurrency cancel-in-progress` áp cả cho `main`, nên hai lần gộp liền nhau sẽ làm lượt trước bị huỷ | Khoảng 9 phút |
| **4. `main` → VPS** | Bước con 4a (tuỳ chọn) rồi 4b | Codex hoặc Claude Code CLI, khi được yêu cầu | — | — | Chỉ phát hành từ `main`, không từ nhánh khác | — | — |
| 4a. Diễn tập trên bản sao VPS (khi thay đổi đụng migration, settings, compose, nginx, static; không bắt buộc mỗi lần) | Chạy dãy phát hành và quay lui của `deploy/production/README.md` trên máy ảo, dùng `deploy/production/compose.yml` và `nginx.conf.template` y nguyên trong kho, cộng một `compose.vps.yml` tự viết. Kèm các ca sự cố: tắt broker hoặc cache, restart db, cửa sổ `up -d`. Không dùng `deploy/optimization-*.conf` thay cho nginx production | Codex/Claude Code | Máy ảo ghim 2 lõi, nginx 443 với chứng chỉ tự ký, tên miền `*.knjsc.test` (theo diễn tập 08.10) | Dữ liệu S0 dựng bằng service của bản đang chạy trên VPS. Không dùng dữ liệu thật | Có commit `main` (hoặc tree) cần phát hành | Có biên bản diễn tập. Mọi điểm D-x đã có cách xử lý | Chưa xác minh (biên bản 08.10 không ghi tổng thời gian) |
| 4b. Phát hành VPS | Theo README, lần lượt: backup rồi phục hồi thử vào DB tạm (`--exit-on-error`); `docker compose config --quiet`; `check --deploy --fail-level WARNING` trên **cả** `crm` và `erp` (TL-85, D9); `stop crm erp worker heavy beat` (TL-81); `run --rm --no-deps -e PGOPTIONS='-c lock_timeout=10s' crm python manage.py migrate --noinput` (thoát khác 0 thì DỪNG); `tao_bang_van_don`; `configure_erp_reports`; `configure_delivery_daily_report`; `collectstatic --noinput --clear` (TL-80); `up -d --no-deps crm erp worker heavy beat` (TL-84); `nginx -t && nginx -s reload`. Sau phát hành: kiểm `RestartCount`/`OOMKilled`; chạy `kiem_tra_du_lieu --bang van_don` bằng `run --rm` (TL-83); `VACUUM ANALYZE forms_builder_datarecord`; kiểm tên miền thật; gom p95 bằng `scripts/gom-p95-vps.py` | Codex hoặc Claude Code CLI trên máy có SSH, khi chủ dự án yêu cầu (Claude Code web không tới được VPS) | VPS 2 nhân 4 GB, project `knjsc-production`. Mọi lệnh kèm `-f compose.yml -f compose.vps.yml` | **Dữ liệu thật.** Cấm `du_lieu_mau`, `seed_perf`, `nap_*`, `do_hieu_nang` (lệnh này không có khoá DEBUG và ghi vào dòng thật; xem lỗ hổng vận hành). Không in nội dung ô (quy tắc 6) | Chặng 3 đạt. Bản sao lưu đã phục hồi thử được. Commit có trong `main` | Có biên bản `docs/kiem-chung-phat-hanh-vps-<ngày>.md` theo khuôn biên bản 29.09. Đã thêm mốc vào bảng README. Gom p95 phải có ít nhất 20 mẫu mỗi nhóm mới được kết luận (mã thoát 2 nghĩa là thiếu mẫu). Quay lui theo README: không đảo migration, không restore DB chỉ để quay lui mã | Chưa xác minh (các biên bản không ghi tổng thời gian) |

### 1.2 Dữ liệu kiểm thử

| Nguồn dữ liệu | Lệnh / vị trí | Dùng ở chặng | Lưu ý bắt buộc |
|---|---|---|---|
| DB pytest riêng | Tự tạo `test_*` theo `--ds=knjsc.settings.test` (`app/pytest.ini`). `STORAGE_DIR`, `BACKUP_DIR`, `EXPORT_DIR` nằm trong thư mục tạm `knjsc-kiem-thu-*`. Celery eager có lan lỗi. Email locmem. Hasher MD5 | 1a, 1b, 3 | **Không chạy hai pytest cùng lúc** trên một DB kiểm thử. Cache `crm` là RedisCache mà CI không có Redis, nên mọi bài không tự đè `CACHES` đều đi nhánh "Redis tắt". Chỉ ba tệp đè sang LocMem: `crm/tests/test_optimization.py`, `test_khoi_luoi_dem.py`, `test_thong_ke_lien_ket_nguon.py` |
| Fixture gốc | `app/conftest.py`: fixture `nguoi_dung` có 11 tài khoản (`staff_sale_1`, `staff_sale_1b`, `staff_sale_2`, `leader_sale_1`, `leader_sale_2`, `manager_sale`, `staff_mkt`, `manager_mkt`, `staff_vd`, `staff_kt`, `admin`), mật khẩu `matkhau-kiem-thu-1`. Kèm `departments`, `teams`, `probes` | 1a, 1b | **Thiếu** CEO, CSKH, Leader MKT, Leader/Manager VĐ, Leader/Manager Kế toán. CEO phải tự dựng ở 10 tệp. `leader_vd`/`manager_vd` tự dựng ở 6 tệp: `crm/tests/test_lien_ket_khong_cut.py`, `crm/tests/test_chi_admin_xoa_dong.py`, `forms_builder/tests/test_pham_vi_bang_nhanh.py`, `tests/test_hieu_nang.py`, `tests/e2e/test_dien_thoai.py`, `core/tests/test_ma_tran_quyen_hai_dich_vu.py` |
| Tài khoản mẫu và dữ liệu nền local | Chạy **đúng thứ tự**: 1) `migrate` → `tao_bang_van_don` (bảng động `van_don`, quyết định 001). 2) `du_lieu_mau`. 3) `configure_erp_reports`. 4) `configure_delivery_daily_report`. Nếu configure chạy trước `du_lieu_mau` thì nó bỏ qua bảng chưa có mà không báo lỗi, và Báo cáo tổng hợp lặng lẽ rơi về bản cũ (ADR-022, tệp `022-bao-cao-hoat-dong-erp.md`, chưa xác minh tệp nào trong hai tệp 022). Launcher và `cap-nhat-local.*` đã làm theo thứ tự này | 2, 4a | `du_lieu_mau` bị chặn khi DEBUG tắt (trừ khi có `--dong-y-chay-that`). Chạy lại thì **đặt lại mật khẩu và mở khoá** tài khoản mẫu. `cap_nhat_mat_khau_mau` bỏ qua khi DEBUG tắt |
| Vận đơn mẫu | `manage.py nap_du_lieu_van_don`: đúng 10.000 dòng mẫu `MAU-*`, có chi tiết, thanh toán, phân công. Có `--tong-so`, `--seed`, `--dry-run` | 2 | Bị chặn khi DEBUG tắt. Khoá này **chưa có bài kiểm** (`orders/tests/test_nap_du_lieu_van_don.py` chỉ chạy với DEBUG=True) |
| Khách mẫu khối lớn | `manage.py nap_khach_mau --so-khach 300000`: 375.000 dòng `KH-*`, 20% mua lại (AC-10.9). Xoá bằng `--xoa-cu`, xoá theo lô có `lock_timeout` (AC-10.10) | 2, 4a (đo tải) | Bị chặn khi DEBUG tắt. Có bài `orders/tests/test_nap_khach_mau.py` |
| Báo cáo MKT mẫu | `manage.py nap_bao_cao_mau --nguoi 20 --lan 3`: dữ liệu từ ngày 1 tháng trước tới hôm nay; tài khoản `mau_bc_mkt_*` bị khoá đăng nhập. Xoá bằng `--xoa-cu` | 2 | Bị chặn khi DEBUG tắt |
| Dữ liệu hiệu năng | `manage.py seed_perf --xoa-cu --so-dong 100000 --so-thang 24 --dien-day --bang-sale` (dòng `PERF-*`). Sau đó `do_hieu_nang --giai-thich` → `storage/perf/<ngày>-don-le*.md`. Locust qua `app/tests/perf/locustfile_kn_crm.py` hoặc `scripts/kiem-tai-kn-crm.sh/.bat` | 2 (máy riêng), 4a | `seed_perf` **chỉ** bị chặn khi DEBUG tắt. Máy local bật DEBUG nên lệnh chạy được trên DB đang làm việc, trái lời dặn ở docs/06. Khoá này chưa có bài kiểm. **`do_hieu_nang` không có khoá DEBUG**: nó ghi "đo tải N" vào 5.000 dòng mới nhất trong phạm vi `--nguoi` (mặc định `vd.staff`) và không lọc `PERF-*`. Chỉ chạy trên DB tổng hợp riêng |
| Bằng chứng đo đã lưu | `docs/verification/*.json` (ví dụ `crm-optimization-baseline.json`, `concurrency-300k-20260916.json`, `grid-*-20260916.json`), `docs/evidence/` | Đối chiếu khi đo lại ở 2, 4a | Chỉ đọc để so. Script `scripts/bao-cao-optimization-final.cjs` và `scripts/grid-flags-check/report.py` **ghi đè** vào `docs/verification/`, nên đo lại phải ra tệp mới có ngày, không ghi đè mốc cũ. Proxy đo là `deploy/optimization-nginx.conf` + `deploy/optimization-proxy.conf`, chỉ dùng cho localhost |
| Tệp nhập thật đã ẩn danh | `docs/tham-khao/vandon-mau.xlsx` (tạo qua `scripts/an-danh-vandon.py`, chỉ thay 4 cột). Tệp gốc là `MITA Vận đơn CSKH Nội bộ CANADA.xlsx` (docs/04 dòng 275–276) | 1a, 1b | Chưa có bài kiểm rằng các cột còn lại không mang dữ liệu khách (quy tắc 6). Bản ẩn danh không thay được điều kiện "tệp Excel thật, không chỉnh sửa" của docs/04 mục 18 (xem 1.5) |
| Rà toàn vẹn | `manage.py kiem_tra_du_lieu [--bang van_don] [--sua]` | 2, 4b | Trên VPS chạy bằng `run --rm`, không `exec` trong `crm` (TL-83) |

**Điều cấm về dữ liệu:**
- Không chạy `migrate <app> zero` trên DB phát triển, vì lệnh này xoá bảng thật. Bài `cham` trong `core/tests/test_chuyen_doi.py` tự làm việc này, nhưng trên DB kiểm thử riêng.
- Không chạy lệnh dữ liệu giả hay `do_hieu_nang` trên VPS.
- Khi gỡ lỗi trên dữ liệu thật: không bật `log_statement=all`, không in nội dung ô; đếm số lượng thay vì in giá trị.
- Mật khẩu DB chỉ đi qua `PGPASSWORD` (điều cấm 6).

### 1.3 Tài khoản theo vai

Ở local, tài khoản do `du_lieu_mau` tạo, theo `docs/tai-khoan-mau.md`. Địa chỉ `http://127.0.0.1:8020/`, mật khẩu chung `matkhaucuatoi`. Mật khẩu này công khai trong mã và chỉ dùng trên máy cá nhân.

| Vai (bộ phận × cấp bậc) | Tài khoản local (`du_lieu_mau`) | Fixture pytest (`app/conftest.py`) | Dùng để kiểm |
|---|---|---|---|
| Admin | `quantri` (VIENQT). Vào được `/quan-tri/` | `admin` | `/tac-vu/`, ô "Sao lưu đêm qua", Nhân sự, Nhật ký, xoá dòng (ADR-049), sửa Báo cáo tổng hợp (ADR-050) |
| Sale Manager | `sale.manager` | `manager_sale` | Phạm vi cả bộ phận, nhập/xuất Excel |
| Sale Leader | `sale.leader` (Sale 1), `sale.leader2` (Sale 2) | `leader_sale_1`, `leader_sale_2` | Phạm vi theo team. Trong CRM, Leader như Manager trong bộ phận mình |
| Sale Staff | `sale.staff` (Sale 1), `sale.staff2` (Sale 2) | `staff_sale_1`, `staff_sale_1b`, `staff_sale_2` | Hai người khác team không thấy báo cáo của nhau |
| Sale Staff mới | `sale.moi`, bị buộc đổi mật khẩu ở lần đầu | `make_user(..., must_change_password=True)` | ForcePasswordChangeMiddleware, AC-1.5 |
| MKT Manager / Leader / Staff | `mkt.manager`, `mkt.leader` (MKT 1), `mkt.staff` (MKT 1) | `manager_mkt`, `staff_mkt` (fixture không có Leader MKT) | Nộp báo cáo, ADR-043, ADR-047 |
| VĐ Manager / Staff | `vd.manager`, `vd.staff` | `staff_vd` (fixture không có Manager hay Leader VĐ) | Lưới `van_don` ở 8021, CAS 409, phân công |
| VĐ Leader | **Không có** | Không có (6 tệp tự dựng, xem 1.2) | ❌ thiếu cho kiểm tay |
| Kế toán | **Không có** | `staff_kt` (chỉ Staff) | ❌ thiếu cho kiểm tay ADR-038 |
| CSKH | **Không có**. Fixture `departments` cũng không có bộ phận `cskh` | Không có | ❌ thiếu cho AC-33.6 |
| CEO | **Không có** | Không có (10 tệp tự dựng `Rank.CEO`) | ❌ thiếu cho kiểm tay ADR-044 (CEO chỉ đọc lưới) |
| Người chưa đăng nhập | — | client không đăng nhập | Chuyển về `/dang-nhap/` (AC-1.1) |

Muốn thêm tài khoản CEO, Kế toán, CSKH, VĐ Leader vào `du_lieu_mau` và `docs/tai-khoan-mau.md` thì chủ dự án phải chốt trước. Hiện chưa xác minh có cách nào khác để tạo các vai này ngoài màn hình Nhân sự.

### 1.4 Lệnh chạy

| Mục đích | Lệnh | Ghi chú |
|---|---|---|
| Toàn bộ pytest (local, Docker) | `docker compose -f deploy/docker-compose.yml run --rm -e RUN_MIGRATIONS=0 web pytest` | Không có `-m` mặc định nên chạy cả bài `cham`. Container `web` mount chỉ đọc `../docs`, `../scripts`, `../.agents`, `../.claude`, `AGENTS.md`/`CLAUDE.md`/… để phục vụ `test_truy_vet.py`, `test_dong_bo_skill.py`, `test_gom_p95.py`. Thiếu mount thì có thể xanh ở CI mà đỏ ở local |
| Ngoài Docker | Từ `app/`: `python -m pytest --ds=knjsc.settings.test` | Cần Postgres đang chạy |
| Bỏ bài chậm (vòng nhanh) | `… pytest -m "not cham"`, hoặc `pytest -m "not cham" --lf -x` | Dùng ở bước 1a |
| Giống job chính của CI | `pytest -m "not trinh_duyet" -rs --durations=10` | `-rs` liệt kê bài bị bỏ qua. Bị bỏ qua không có nghĩa là đã kiểm |
| Bài trình duyệt, tiến trình 1 | `pytest tests/e2e -m trinh_duyet -vv -rs --durations=10 -o faulthandler_timeout=120` | Cần Playwright 1.56.0 cùng Chromium (`playwright install --with-deps chromium`). Thiếu thì bài tự bỏ qua |
| Bài trình duyệt, tiến trình 2 | `pytest -m trinh_duyet --ignore=tests/e2e -vv -rs` | **Phải tách khỏi tiến trình 1** vì `crm/tests/test_luoi_dong_trong_va_ghim_e2e.py` và `reports/tests/test_bo_cuc_bao_cao_e2e.py` tự mở `sync_playwright`. 9 tệp `*_browser*.py` sẽ bị bỏ qua nếu thiếu biến môi trường riêng |
| Bài treo | Thêm `-vv -o faulthandler_timeout=120` | Dòng cuối trong log là bài vừa chạy xong; bài treo là bài kế tiếp. Hook trong `app/conftest.py` in ngăn xếp greenlet sau 121 giây (TL-71) |
| Truy vết AC | `pytest tests/test_truy_vet.py` | Thêm AC thì cập nhật bộ đếm docs/06 theo thông báo của bài |
| Kèm bao phủ | Thêm `--cov` | `pytest-cov` có sẵn trong requirements-dev, `app/.coveragerc` có sẵn. CI chưa đo |
| Script JS không cần trình duyệt | `node scripts/kiem-thu-master-autosave-unit.cjs` (tương tự cho queue, scope, conflict, working-copy, row-geometry, grid-jump, grid-interaction, optimization-unit) | Cần Node ≥ 22, không có trong CI. Thoát mã 0 là đạt |
| Kiểm cấu hình phát hành (mô phỏng ở local) | `DJANGO_SETTINGS_MODULE=knjsc.settings.bangtinh BANGTINH_GOC=prod … python manage.py check --deploy --fail-level WARNING` | Danh sách biến đầy đủ xem ở danh mục thủ công của phân hệ vận hành. Bỏ `SESSION_COOKIE_DOMAIN` thì phải ra lỗi `core.E001` |
| Sao lưu / phục hồi (local hoặc môi trường thử) | `scripts/backup.sh`; `scripts/restore.sh` (chỉ liệt kê); `scripts/restore.sh <tệp>.dump --toi-chac-chan` | Theo docs/05 B8. Không có `--toi-chac-chan` thì script không ghi gì. Script dừng worker, beat và Bảng tính trong lúc phục hồi. `storage/tai-lieu/` phải chép riêng (K30) |

**Quy tắc chạy:**
- Không chạy hai pytest cùng lúc trên một DB kiểm thử.
- Không chạy `scripts/kiem-thu-*.cjs` vào cổng 8020/8021 của máy đang chứa dữ liệu thật: script mặc định trỏ `127.0.0.1:8020/8021` và không có chốt chặn host.
- Đo tải xong thì trả container `web` về runserver. Bấm Ctrl+C giữa chừng có thể để container kẹt ở gunicorn (TL-29).

### 1.5 Điều kiện xong phase 1 (docs/04 mục 17–18) và runbook docs/05

Đây là tiêu chí ra ở cấp dự án, không gắn với một thay đổi riêng lẻ. Cột "Hiện trạng" chỉ ghi những gì đã thấy trong kho.

**docs/04 mục 18 — điều kiện coi là hoàn thành phase 1**

| # | Điều kiện | Ánh xạ chặng / ca | Hiện trạng | Góc nhìn | Loại | Cách chạy | Ưu tiên |
|---|---|---|---|---|---|---|---|
| 18.1 | Mọi AC **Tự động** có bài và đạt | Bước 1b, chặng 3; `app/tests/test_truy_vet.py` | ⚠️ docs/06 ghi 348/371 có bài, 23 hoãn (`HOAN`). Có AC "đếm là có bài" nhưng bài luôn bị bỏ qua (AC-20.6) | QA | Nghiệm thu, truy vết | Tự động | P0 |
| 18.2 | Ma trận phân quyền mục 3 kiểm đủ cả cho phép và từ chối | Bước 1b; `app/tests/test_ma_tran_phan_quyen.py`, `app/core/tests/test_ma_tran_quyen_hai_dich_vu.py` | ⚠️ Lệch docs/04 ở 2/50 ô (dòng 120, 122; commit 5e710ed) | QA | Chức năng, phân quyền | Tự động | P0 |
| 18.3 | Làm và đạt đủ 7 việc thủ công của mục 17 | Chặng 2 (trên dữ liệu mẫu), chặng 4 (trên dữ liệu thật) | Chưa xác minh (chưa thấy biên bản tổng hợp cả 7 việc) | Người dùng | Nghiệm thu | Thủ công | P0 |
| 18.4 | Đã phục hồi thành công ít nhất một lần từ bản sao lưu | Bước 4a/4b; AC-10.5 (Thủ công); docs/05 B4, B8 | ⚠️ Đã phục hồi thật vào DB tạm với `--exit-on-error` (`docs/kiem-chung-phat-hanh-vps-20260929.md` dòng 23; diễn tập 08.10 dòng 46: số dòng 51 bảng khớp). Chưa thấy biên bản phục hồi đè bằng `scripts/restore.sh --toi-chac-chan` theo B8 ("sửa một ô, phục hồi, kiểm ô trở về giá trị cũ") | QA | Nghiệm thu, độ tin cậy | Thủ công | P0 |
| 18.5 | Tệp Excel thật của công ty nhập được mà không cần chỉnh sửa thủ công | Chặng 2 (người kiểm có tệp thật trên máy mình), không đưa tệp vào kho (quy tắc 6) | ⚠️ Kho chỉ có bản ẩn danh `docs/tham-khao/vandon-mau.xlsx`. AC-7.15 đòi "tệp thật vài chục cột × 10.000 dòng vẫn nhập được". Việc nhập tệp gốc chưa xác minh | Người dùng | Nghiệm thu | Thủ công | P0 |
| 18.6 | Ba vai Sale, MKT, VĐ chạy trọn quy trình trên dữ liệu thật | Sau bước 4b, theo docs/07 mục 3.1–3.3 (bỏ bước lỗi thời ở 0.2) | Chưa xác minh | Người dùng | Nghiệm thu | Thủ công | P0 |
| 18.7 | Đã bàn giao tài liệu hướng dẫn sử dụng và vận hành | `docs/05-huong-dan-va-van-hanh.md`; ca rà hướng dẫn sử dụng (phần A) và ca kiểm runbook (phần B) ở hai bảng cuối mục này | ⚠️ Có tài liệu, nhưng B1 chưa điền tên người chịu trách nhiệm. Phần A lệch ADR-040 (A8, dòng 315 và 337) và lệch AC-44.3/ADR-045 (A4, dòng 157) | Người dùng | Nghiệm thu, vận hành | Thủ công | P1 |

**docs/04 mục 17 — kiểm thủ công trước bàn giao**

| # | Việc | Ánh xạ chặng / bài sẵn có | Góc nhìn | Cách chạy | Ưu tiên |
|---|---|---|---|---|---|
| 17.1 | Cài từ đầu trên máy sạch, chạy tới màn hình đăng nhập | Chặng 2 bằng `KN JSC.bat` / `scripts/cap-nhat-local.*` (docs/05 B6) trên máy chưa có volume `db_data` | Người dùng | Thủ công | P1 |
| 17.2 | Ba vai đăng nhập và chạy trọn quy trình | Chặng 2 với `sale.*`, `mkt.*`, `vd.*` (1.3); docs/07 mục 3.1–3.3 | Người dùng | Thủ công | P0 |
| 17.3 | Nhập tệp Excel thật, không chỉnh sửa trước | Như 18.5 | Người dùng | Thủ công | P0 |
| 17.4 | Xuất báo cáo, mở bằng Excel, đối chiếu số liệu | Chặng 2; docs/05 A5 "Xuất báo cáo". Tiền không cộng lẫn loại tiền (BR-8, ADR-046) | Người dùng | Thủ công | P1 |
| 17.5 | Thử trên điện thoại và máy tính bảng thật | Chặng 2. `app/tests/e2e/test_dien_thoai.py` chỉ giả lập trình duyệt, không thay được thiết bị thật | Người dùng | Thủ công (giả lập là Tự động ⚠️) | P1 |
| 17.6 | Phục hồi từ bản sao lưu trên môi trường thử | Như 18.4; AC-10.5 | QA | Thủ công | P0 |
| 17.7 | Ngắt mạng giữa chừng, kiểm thông báo lỗi | `app/tests/e2e/test_mat_mang_e2e.py` (AC-10.12) cộng kiểm tay ở chặng 2 | Người dùng | Tự động ⚠️ (chỉ chạy khi có Chromium) + Thủ công | P1 |

**Rà hướng dẫn sử dụng `docs/05-huong-dan-va-van-hanh.md` phần A với ADR/AC**

| Mục | Ca kiểm | Tiêu chí đạt | Góc nhìn | Cách chạy | Ưu tiên |
|---|---|---|---|---|---|
| A4 (dòng 157) | Đối chiếu tiêu đề "Bảng dữ liệu — dành cho Marketing và Vận đơn" với AC-44.3 (ADR-045): đăng nhập `mkt.staff`, `vd.staff`, `mkt.leader` ở 8020 và kiểm mục Bảng dữ liệu ERP | A4 ghi đúng: Staff/Leader không thấy mục và bị chặn đọc/xuất/quản lý; Manager trong phạm vi; CEO/Admin toàn công ty. Hiện tại tài liệu lệch: ❌ | Người dùng | Thủ công (rà tài liệu + bấm thử) | P1 |
| A8 (dòng 315, 337) | Đối chiếu "lưới kiểu Excel cho mọi bảng" và "Bảng tính: Bộ phận ▸ Quý ▸ Tháng ▸ bảng" với ADR-040: mở 8021 bằng `vd.staff`, `sale.staff`, `mkt.staff` | A8 chỉ mô tả bảng vận đơn, không còn cây Bộ phận ▸ Quý ▸ Tháng. Hiện tại tài liệu lệch: ❌ | Người dùng | Thủ công (rà tài liệu + bấm thử) | P1 |
| A1–A13 còn lại | Rà với ADR-044 (CEO chỉ đọc lưới) và ADR-049, ADR-050 | Không còn mô tả trái ADR. Chưa xác minh | QA | Thủ công (rà tài liệu) | P2 |

**Kiểm runbook `docs/05-huong-dan-va-van-hanh.md` phần B**

| Mục | Ca kiểm | Tiêu chí đạt | Góc nhìn | Cách chạy | Ưu tiên |
|---|---|---|---|---|---|
| B3 | Đăng nhập `quantri`, đọc ô "Sao lưu đêm qua" và ô "Tác vụ nền" | Chip xanh "Thành công" kèm giờ. Sao lưu hỏng thì có chip đỏ và thư tới `OPERATOR_EMAILS` | Người dùng | Thủ công (chặng 2, sau 4b) | P1 |
| B4, B8 | Thử phục hồi hằng quý: sao lưu → sửa một ô → `scripts/restore.sh <tệp> --toi-chac-chan` → kiểm ô trở về giá trị cũ; Nhật ký có một dòng phục hồi | Ô trở về giá trị cũ. worker/beat/Bảng tính được bật lại. Ghi ngày thực hiện | QA | Thủ công | P0 |
| B8 | Bản sao lưu không kèm `storage/tai-lieu/` (K30) | Tài liệu tải lên sau mốc sao lưu vẫn mở được sau khi chép thư mục lại. Chưa có quy trình tự động: ❌ | QA | Thủ công | P1 |
| B6 | Cập nhật máy chủ thật | B6 chỉ có 7 bước chung, chưa dẫn tới `deploy/production/README.md`. Cần đối chiếu và thống nhất với bước 4b | QA | Thủ công (rà tài liệu) | P1 |
| B9 | Kiểm bàn giao | Người tiếp nhận tự phục hồi được một lần trên môi trường thử mà không cần hỏi ai | Người dùng | Thủ công | P1 |
| B1 | Điền tên người chịu trách nhiệm | Ba dòng không còn "(điền tên)" | Người dùng | Thủ công | P2 |
