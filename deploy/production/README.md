# Cấu hình ứng viên VPS KNJSC

**Chưa triển khai/đo trên VPS.** Không dùng file này với project/volume local.
Khởi điểm 12 CPU/24 GB; tổng giới hạn bộ nhớ container chừa phần còn lại cho
OS/page cache. `work_mem` tính theo mỗi phép sort/hash và tác vụ song song,
không phải 8 MB cố định mỗi connection. Kiểm RSS thực trước khi nâng giới hạn.
Service Thống kê hiện có `SET LOCAL work_mem='64MB'` cho một số aggregate;
8 MB ở cấu hình PostgreSQL không ghi đè lựa chọn trong transaction này.
Tính cả chi phí đó khi kiểm nhiều người mở Thống kê cùng lúc.

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

Lệnh dự kiến tại `deploy/production` (chỉ chạy khi được phép triển khai):

```sh
docker compose config --quiet
docker compose up -d db broker cache
docker compose --profile maintenance run --rm static-owner
docker compose run --rm crm python manage.py migrate --noinput
docker compose run --rm crm python manage.py collectstatic --noinput
docker compose up -d crm erp worker heavy beat proxy
```

Migration không seed dữ liệu dev. Chưa tự chạy các lệnh này trên VPS.
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
