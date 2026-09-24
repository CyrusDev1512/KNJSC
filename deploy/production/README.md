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

**VPS đã chạy `main` tại `9c4d285` từ 24.09.2026.** Merge không tự phát hành;
chốt SHA có CI đạt, diễn tập, backup và kiểm chứng trước mỗi lần cập nhật.
Luôn giữ cả `/opt/knjsc-runtime/compose.yml` và `compose.vps.yml` với giới hạn 4 GB.

**Đã phát hành 7 lần**, mỗi lần một biên bản ở `docs/`:

| # | Ngày | Image |
|---|---|---|
| 1 | 17.09.2026 | `0907cdd-grid` → `9949062-adr033` |
| 2 | 18.09.2026 | `9949062-adr033` → `0d970f8-gopy` |
| 3 | 18.09.2026 (chiều) | `0d970f8-gopy` → `5b7922f-excel` |
| 4 | 18.09.2026 (chiều, lần hai) | `5b7922f-excel` → `5b68dce-tl41` |
| 5 | 19.09.2026 (00:15) | `5b68dce-tl41` → `ea8942c-adr036` |
| 6 | 19.09.2026 (18:39) | `ea8942c-adr036` → `72af235-gop` |
| 7 | 24.09.2026 (17:33–17:35) | `72af235-gop` → `9c4d285-main` — [biên bản](../../docs/kiem-chung-phat-hanh-vps-main-20260924.md) |

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

Dãy lệnh phát hành tại `deploy/production`, đã chạy thật 6 lần (chỉ chạy khi được phép):

```sh
docker compose config --quiet
docker compose up -d db broker cache
docker compose --profile maintenance run --rm static-owner
docker compose run --rm crm python manage.py migrate --noinput
docker compose run --rm crm python manage.py tao_bang_van_don
# ĐÃ CHẠY một lần khi phát hành ADR-036 (19.09.2026, lần 5) sau backup đã kiểm phục hồi.
# Chạy lại chỉ in "không có gì để xoá" — đúng, không phải lỗi:
# docker compose run --rm crm python manage.py xoa_bang_van_don_cu --dong-y-xoa-cung --backup-da-lam
docker compose run --rm crm python manage.py configure_erp_reports
docker compose run --rm crm python manage.py configure_delivery_daily_report
docker compose run --rm crm python manage.py collectstatic --noinput
docker compose run --rm crm python manage.py gan_ma_nhan_su_cu            # ADR-037: xem trước, gửi bảng mã cho chủ dự án
docker compose run --rm crm python manage.py gan_ma_nhan_su_cu --xac-nhan # rồi mới ghi; chạy lại không đổi thêm
docker compose up -d crm erp worker heavy beat proxy
```

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
