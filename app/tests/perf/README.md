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

## Kiểm tải KN CRM — 100 người trên 100 nghìn khách (AC-10.6, docs/06 tầng 9)

Ba bước, máy nào cũng vậy; trên Windows/Mac chỉ cần nháy đúp
`scripts/kiem-tai-kn-crm.bat` (hoặc chạy `scripts/kiem-tai-kn-crm.sh`):

```
python manage.py seed_perf --xoa-cu --so-dong 100000 --so-thang 24 --dien-day --bang-sale
python manage.py do_hieu_nang --giai-thich --nhan truoc        # một người, không tải → storage/perf/<ngày>-don-le-truoc.md
locust -f tests/perf/locustfile_kn_crm.py --host http://localhost:8021 \
       --users 100 --spawn-rate 10 --run-time 5m --headless   # → storage/perf/<ngày>-tai-100.md
```

Máy chủ phải chạy **gunicorn** (như Dockerfile, 3 worker), không đo trên
`runserver`. Kịch bản không bấm giao diện: mỗi người ảo là một tab lưới gọi
đúng HTTP mà trình duyệt gọi, kể cả hỏi `moi-nhat/` mỗi 8 giây. Bốn vai
70 / 20 / 7 / 3 (nhân viên vận đơn di qua di lại, Sale/Marketing, trưởng nhóm
dán và xoá, Manager thêm rồi sửa cột tính sẵn giữa phiên). Ngưỡng "như Excel
trên máy thường" ở `core/constants.py` (`PERF_READ_P95_MS` …); kịch bản in
ĐẠT / KHÔNG ĐẠT từng tiêu chí và thoát mã 1 nếu có dòng đỏ. Sale lên đơn ở
`ERP_HOST` (mặc định `http://localhost:8020`).
