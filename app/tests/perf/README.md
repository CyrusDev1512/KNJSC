# Đo tải — AC-10.1

Công cụ: **Locust** (backlog Q44), chỉ có trong `requirements-dev.txt`.

## Chuẩn bị

```
docker compose -f deploy/docker-compose.yml exec web python manage.py du_lieu_mau
docker compose -f deploy/docker-compose.yml exec web python manage.py seed_perf
```

Lệnh thứ hai sinh 50.000 dòng vận đơn giả (mã `PERF-*`), xoá bằng `seed_perf --xoa-cu`.

## Chạy

Từ thư mục `app/` trên máy có Python và đã `pip install -r requirements-dev.txt`:

```
locust -f tests/perf/locustfile.py --host http://localhost:8020 \
       --users 50 --spawn-rate 5 --run-time 1m --headless
```

Kịch bản tự chấm khi dừng: in `ĐẠT` hoặc `KHÔNG ĐẠT` và thoát mã 1 nếu p99
quá 3 giây hoặc có yêu cầu hỏng. Bỏ `--headless` để xem biểu đồ trực tiếp tại
`http://localhost:8089`.

Vai Vận đơn gọi dịch vụ Bảng tính ở `BANGTINH_HOST` (mặc định `http://localhost:8021`).
