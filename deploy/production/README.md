# Cấu hình VPS KNJSC

**Đang chạy thật.** Không dùng file này với project/volume local.

VPS thật có **2 nhân, 4 GB RAM**, chạy năm container `crm`, `erp`, `worker`, `heavy`,
`beat` cùng một image tag bất biến, nginx đứng trước hai hostname ERP và CRM. Con số
"12 CPU / 24 GB" ở bản đầu là máy giả định lúc chưa có VPS, **không phải máy đang chạy** —
mọi giới hạn bộ nhớ và `work_mem` phải tính lại theo 4 GB, chừa phần cho OS và page cache.
`work_mem` tính theo mỗi phép sort/hash và tác vụ song song, không phải 8 MB cố định mỗi
connection. Kiểm RSS thực trước khi nâng giới hạn. Service Thống kê hiện có
`SET LOCAL work_mem='64MB'` cho một số aggregate; 8 MB ở cấu hình PostgreSQL không ghi đè
lựa chọn trong transaction này. Tính cả chi phí đó khi kiểm nhiều người mở Thống kê cùng lúc.

**Các mốc phát hành đã ghi nhận** (biên bản tại `docs/`):

| # | Ngày | Image |
|---|---|---|
| 1 | 17.09.2026 | `0907cdd-grid` → `9949062-adr033` |
| 2 | 18.09.2026 | `9949062-adr033` → `0d970f8-gopy` |
| 3 | 18.09.2026 (chiều) | `0d970f8-gopy` → `5b7922f-excel` |
| 4 | 18.09.2026 (chiều, lần hai) | `5b7922f-excel` → `5b68dce-tl41` |
| 5 | 19.09.2026 (00:15) | `5b68dce-tl41` → `ea8942c-adr036` |
| 6 | 19.09.2026 (18:39) | `ea8942c-adr036` → `72af235-gop` |
| — | Mốc 25.09, kiểm lại trực tiếp 29.09 | Runtime `97bff53-main`; chưa có đủ biên bản để khôi phục toàn bộ các lần chuyển image trung gian |
| 7 | 29.09.2026 (23:40) | `97bff53-main` → `c7065fe-adr046` |
| 8 | 09.10.2026 (11:06 VN) | `c7065fe-adr046` → `e979323-main-r2` |

Lượt 09.10: [biên bản phát hành và giới hạn nghiệm thu](../../docs/kiem-chung-phat-hanh-vps-20261009.md).
Runtime đã chuyển sang main `e979323`; tag `e979323-main` đầu tiên lỗi quyền đóng gói
và không được phát hành. Dùng tag r2 đã kiểm, không ghi đè tag bất biến.

Lượt 29.09: [biên bản phát hành](../../docs/kiem-chung-phat-hanh-vps-20260929.md).
Số thứ tự chỉ đếm các lượt có biên bản trong bảng; không suy ra ngày 25.09 chỉ có
một lần phát hành. Bản bàn giao ghi VPS ở `85227ee` đã được thay bằng kiểm trực tiếp
`97bff53-main`; dùng mốc runtime thực tế làm image quay lui.

Xem `docs/kiem-chung-phat-hanh-vps-*.md`; `docs/kiem-chung-dien-tap-vps-20260917.md` là
diễn tập trên bản sao, không phải lần phát hành.

## Chuẩn bị riêng trên VPS

- Build image từ nhánh đã nghiệm thu, đặt tag bất biến hoặc digest vào `KNJSC_IMAGE`.
  Dùng `deploy/Dockerfile` hiện có với `--build-arg INSTALL_DEV=0`;
  không build kèm dependency dev/Locust vào image production.
- Tạo `.env` bên cạnh Compose, hạn chế quyền đọc. Cần có `KNJSC_IMAGE`,
  `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `POSTGRES_DB`, `POSTGRES_USER`,
  `POSTGRES_PASSWORD`, `CRM_HOST`, `ERP_HOST`, `CSRF_TRUSTED_ORIGINS`.
  Điền `BANGTINH_URL`/`MAIN_APP_URL` bằng URL HTTPS thực, cùng cấu hình email
  và operator theo hướng dẫn vận hành. Không copy secret từ máy dev.
- **Đăng nhập chung hai tên miền:** đặt `SESSION_COOKIE_DOMAIN` và `CSRF_COOKIE_DOMAIN`
  là tên miền cha chung của `ERP_HOST` và `CRM_HOST` (dạng `.ten-mien.vn`). Thiếu thì
  sang dịch vụ kia phải đăng nhập lại; `manage.py check --deploy` báo lỗi `core.E001`
  và dừng phát hành (AC-1.11). Dịch vụ `crm` phải có `BANGTINH_GOC=prod` (đã đặt trong
  `compose.yml`); thiếu thì container dừng khởi động thay vì chạy cấu hình dev.
- Đặt chứng chỉ hợp lệ cho cả hai hostname tại `certificates/fullchain.pem`
  và `certificates/privkey.pem`. Chứng chỉ/private key không đưa vào Git.
  Quy trình cấp/gia hạn chứng chỉ cần được cấu hình trên máy chủ thực.
- Chỉ proxy mở cổng 80/443. PostgreSQL và hai Redis không publish port.
  Cache 512 MB dùng LRU; broker/result riêng dùng persistence/noeviction.
  Giám sát dung lượng broker: noeviction trả lỗi khi đầy, không tự làm mất job.
- Các cờ tối ưu mặc định `0`. Chỉ bật từng nhóm đã nghiệm thu. Tắt cờ không
  xóa nhật ký, biên nhận hoặc dừng ghi revision. Không bật `SYNC` trước `READ`.
- Bật `CRM_OPT_QUEUES=1` khi cả worker `heavy` và `worker` đã sẵn sàng;
  không bỏ consumer hàng đợi cũ khi vẫn còn tác vụ đang chờ. Mỗi worker
  concurrency 1, prefetch 1. Không auto-retry import có nguy cơ tạo trùng.

Dãy lệnh phát hành chuẩn (chỉ chạy khi được phép). VPS dùng thư mục
`/opt/knjsc-runtime` và phải truyền đủ `-f compose.yml -f compose.vps.yml` cho mọi
lệnh dưới đây; không áp nguyên cấu hình tài nguyên mặc định của kho mã lên VPS:

Dãy dưới đây đã diễn tập ngày 08.10.2026 trên bản sao giống VPS (2 lõi, RAM như VPS, nginx HTTPS hai tên
miền). Biên bản [kiem-chung-dien-tap-phat-hanh-staging-20261008](../../docs/kiem-chung-dien-tap-phat-hanh-staging-20261008.md)
ghi số đo và lý do từng bước.

```sh
# 0. Chỉ đọc: tree của main đúng bản đã kiểm; .env đủ hai cookie domain, *_URL https; không còn việc nền đang chạy.
#    Chạy SQL kiểm mã đơn trùng và ô chữ NFD trong biên bản 08.10 — chỉ in số đếm.
docker compose config --quiet
docker compose up -d db broker cache
# 1. Backup + phục hồi thử vào DB tạm (khuôn biên bản 29.09).
# 2. Image mới: kiểm cấu hình phát hành trên CẢ HAI dịch vụ. --fail-level WARNING bắt được BANGTINH_GOC gõ sai (DEBUG bật)
KNJSC_IMAGE=<mới> docker compose run --rm --no-deps crm python manage.py check --deploy --fail-level WARNING
KNJSC_IMAGE=<mới> docker compose run --rm --no-deps erp python manage.py check --deploy --fail-level WARNING
# 3. Dừng mọi dịch vụ ghi: code cũ chạy trên schema mới sẽ để lọt mã đơn trùng và ghi sai loại tiền MKT
docker compose stop crm erp worker heavy beat
docker compose --profile maintenance run --rm static-owner
# 4. Migrate có lock_timeout. Thoát khác 0 thì DỪNG, không đổi image. Do khoá: chạy lại.
#    Do "mã đơn trùng" (lần đầu lên bản có forms_builder/0017): migrate dừng trước khi áp migration nào (TL-76). Bật lại
#    bản cũ rồi sửa mã trên lưới, hoặc dùng image mới chạy lệnh dưới — đổi mã các dòng thừa thành
#    TRUNG-<số dòng>-<mã cũ>, giữ dòng gắn đơn gốc — rồi chạy lại:
#    KNJSC_IMAGE=<mới> docker compose run --rm --no-deps crm python manage.py kiem_tra_du_lieu --sua
KNJSC_IMAGE=<mới> docker compose run --rm --no-deps -e PGOPTIONS='-c lock_timeout=10s' crm python manage.py migrate --noinput
KNJSC_IMAGE=<mới> docker compose run --rm --no-deps crm python manage.py tao_bang_van_don
# ĐÃ CHẠY một lần khi phát hành ADR-036 (19.09.2026, lần 5) sau backup đã kiểm phục hồi.
# Chạy lại chỉ in "không có gì để xoá" — đúng, không phải lỗi:
# docker compose run --rm crm python manage.py xoa_bang_van_don_cu --dong-y-xoa-cung --backup-da-lam
KNJSC_IMAGE=<mới> docker compose run --rm --no-deps crm python manage.py configure_erp_reports
KNJSC_IMAGE=<mới> docker compose run --rm --no-deps crm python manage.py configure_delivery_daily_report
# 5. --clear: collectstatic so theo giờ sửa tệp, bỏ sót tệp đã đổi sau mỗi lần quay lui
KNJSC_IMAGE=<mới> docker compose run --rm --no-deps crm python manage.py collectstatic --noinput --clear
KNJSC_IMAGE=<mới> docker compose run --rm --no-deps crm python manage.py gan_ma_nhan_su_cu            # ADR-037: xem trước
# KNJSC_IMAGE=<mới> docker compose run --rm --no-deps crm python manage.py gan_ma_nhan_su_cu --xac-nhan  # rồi mới ghi
# 6. Đổi KNJSC_IMAGE trong .env rồi bật lại. --no-deps: không có thì Compose tạo lại cả db vì .env đổi
docker compose up -d --no-deps crm erp worker heavy beat
docker compose exec proxy nginx -t && docker compose exec proxy nginx -s reload
# 7. Sau: RestartCount/OOMKilled; rà dữ liệu bằng `run --rm` (exec trong crm có thể hết RAM khi bảng lớn); VACUUM ANALYZE
docker compose run --rm crm python manage.py kiem_tra_du_lieu --bang van_don
docker compose exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c 'VACUUM ANALYZE forms_builder_datarecord'
```

Lệnh `db` nên có thêm `-c log_min_error_statement=panic`. Không có thì mỗi lần vi phạm ràng buộc (ví dụ mã đơn trùng),
Postgres ghi nguyên câu SQL kèm dữ liệu ô vào log, vì Django gửi giá trị nằm luôn trong câu.

**Quay lui** (đã diễn tập 08.10.2026), làm theo thứ tự:
1. `stop crm erp worker heavy beat`.
2. Dùng image cũ chạy `configure_erp_reports`, `configure_delivery_daily_report` và
   `collectstatic --noinput --clear`. Thiếu `configure` cũ thì nộp báo cáo MKT hỏng; thiếu `--clear` thì JS mới chạy trên
   server cũ.
3. Đổi `.env` về image cũ, `up -d --no-deps crm erp worker heavy beat`, reload nginx.
4. Không đảo migration nào: đảo `reports/0006` làm mất dữ liệu.
5. Trước khi tiến lại: `kiem_tra_du_lieu`, sửa mã trùng trên lưới, rồi `kiem_tra_du_lieu --sua`.

Từ 18.09.2026 (ADR-031 bổ sung) `.env` có thể thêm `EXCHANGE_RATES_VND` cho EUR/JPY/AUD
và, khi kế toán chốt, KRW (`USD=25500,CAD=17500,PHP=440,EUR=28500,JPY=155,AUD=17000,KRW=…`);
thiếu biến thì dùng bảng mặc định trong mã, KRW chưa có nên bảng xếp hạng báo rõ.

Migration không seed dữ liệu dev.
`tao_bang_van_don` và hai lệnh `configure_*` là **metadata của bảng động**
(quyết định 001, ADR-022): `migrate` chỉ tạo bảng rỗng, không sinh định nghĩa
cột hay ánh xạ nguồn báo cáo. Bỏ chúng thì Bảng tính trả 404 và màn hình Báo
cáo tổng hợp **lặng lẽ** rơi về bản tổng quát cũ, không báo lỗi gì. Cả ba chạy
lại nhiều lần được, chỉ ghi cấu hình, không tạo dòng nghiệp vụ. `RUN_MIGRATIONS`
ở đây là `0` nên `entrypoint.sh` không chạy giúp — phải gọi tay đúng thứ tự trên.
Trước nâng cấp phải có backup kiểm phục hồi, ghi phiên bản image và cấu hình.
Quay lui ứng dụng bằng cờ/image đã kiểm; không restore DB hoặc xóa lịch sử
chỉ để quay lui mã. Named volume giữ dữ liệu qua lần thay container.

## Kiểm vận hành

- Đo CPU steal, RAM/swap, I/O wait, độ trễ đĩa, connection DB, lock wait,
  RTT và băng thông thực. Không suy từ thông số gói VPS ra năng lực ứng dụng.
- Theo dõi request ID proxy → Django; Django log thời gian tổng, SQL,
  thiết lập connection và PID. `db_ms` gồm thời gian SQL/network/lock; không
  gọi nó là thời gian chờ pool. `connect_ms` là thời gian mở connection.
  Lưới khi bật số đo giữ tối đa 100 mục kỹ thuật trong RAM qua
  `KNJSC_MASTER.requestDiagnostics()`, chỉ gồm mã request/trạng thái/thời gian;
  không lưu nội dung ô, URL truy vấn hoặc bản nháp vào localStorage.
- Proxy log `seconds`/`upstream_seconds`; Django log dùng millisecond.
  Không bật access log chứa query string, body, cookie, token hoặc nội dung ô.
  Không bật PostgreSQL log toàn câu SQL/parameter trên dữ liệu khách hàng.
- Proxy giữ buffering upload/download; không tăng timeout để che lỗi API.
  Kết nối proxy–Gunicorn đóng sau phản hồi, tránh tái dùng kết nối ở ranh giới
  idle timeout. Client vẫn dùng keep-alive tới proxy. Chi phí thêm connection
  nội bộ phải đối chiếu trong bộ đo, không coi cơ chế này là miễn phí.
- Kiểm cache hit/expiry, hàng đợi/độ trễ export, dung lượng file xuất và job
  lỗi; kiểm worker và đường tải vẫn xác nhận quyền người dùng hiện hành.
- Chỉ nghiệm thu sau ma trận local và phép đo lặp lại trên VPS. Có sai dữ
  liệu/quyền/ghi trùng thì tắt nhóm liên quan và điều tra trước khi phát hành.

## Gom p95 thật của KN CRM từ log — `scripts/gom-p95-vps.py`

Đóng khoản nợ "chưa đo trên VPS, chưa gom p95 thật" (backlog, kanban Far plan).

**Không phải đo mới.** `CRM_REQUEST_METRICS: '1'` đã bật trong `compose.yml` từ
đầu, nên `core/request_metrics.py` ghi **một dòng JSON mỗi yêu cầu** ra stdout
container và Docker giữ lại. Số đã nằm đó nhiều ngày; việc còn thiếu là gom.
Chạy lần đầu là có ngay lịch sử, không cần chờ hứng.

Trên VPS, sau khi SSH vào. Máy chủ này dùng **hai tệp compose** — `compose.yml`
của kho mã cộng `compose.vps.yml` riêng của máy (không đưa lên kho, xem các biên
bản phát hành) — nên phải kể đủ cả hai, y như dãy lệnh phát hành:

```sh
cd /opt/knjsc-runtime
GOM="python3 /opt/knjsc/scripts/gom-p95-vps.py --compose compose.yml --compose compose.vps.yml"
$GOM --since 24h
$GOM --since 7d --json /opt/knjsc-runtime/p95-$(date +%Y%m%d).json
$GOM --since 24h --dich-vu erp          # KN ERP
```

**Nếu `docker compose` đòi `KNJSC_IMAGE`** (biến này chỉ đặt lúc phát hành),
bỏ qua compose và đọc thẳng container — kết quả y hệt:

```sh
docker logs --since 24h knjsc-production-crm-1 2>&1 \
  | python3 /opt/knjsc/scripts/gom-p95-vps.py --tep -
```

Chỉ đọc log, **không chạm vào dữ liệu, không khởi động lại gì**. Chạy được
trong giờ làm việc.

| Nhóm | Gồm | Ngưỡng p95 |
|---|---|---|
| Hỏi thăm | tuyến kết thúc `moi-nhat/` | 300 ms |
| Ghi | mọi POST/PUT/PATCH/DELETE | 500 ms |
| Đọc | phần còn lại | 1000 ms |

Ngưỡng theo `app/core/constants.py` (ADR-016). Nhập tệp, xuất tệp và đăng nhập
chậm theo bản chất nên **vẫn in ra nhưng không tính vào phán quyết nhóm**.

Mã thoát 0 đạt, 1 có nhóm vượt ngưỡng, 2 thiếu mẫu — cắm được vào cron.

**Đọc kết quả.** Cột `db p95` gần bằng `p95` nghĩa là nghẽn ở cơ sở dữ liệu;
chênh nhau nhiều nghĩa là nghẽn ở Python hoặc ở hàng đợi gunicorn. Cột `TV` là
số truy vấn; tuyến nào vọt lên là chỗ nghi N+1 trước tiên.

**Dưới 20 mẫu thì script nói "ít mẫu" và không kết luận chắc.** p95 trên một
nhúm nhỏ chỉ là giá trị lớn nhất. Nới `--since`, hoặc đo lại sau một ngày làm
việc thật.

**Cần biết trước khi tin con số:** `compose.yml` chưa đặt `logging:` nên Docker
dùng `json-file` không giới hạn. Nghĩa là (a) log còn đủ để gom ngược nhiều
ngày, và (b) nó lớn dần không có trần trên VPS 2 nhân. Kiểm dung lượng bằng
`docker system df` trước khi đặt giới hạn xoay vòng — đặt giới hạn là **xoá mất
phần lịch sử chưa gom**, nên gom và lưu `--json` trước đã.
