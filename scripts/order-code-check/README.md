# Kiểm chứng cấp mã đơn đồng thời

Harness của đợt sửa `fix/trung-ma-don-dong-thoi`, nền `a81decd`.
Chỉ dùng trên database/container kiểm thử riêng, không chạy trên Compose dev.
Không đưa session, mật khẩu hoặc `runtime.env` vào Git.

## Bố trí để chạy lại

1. Tạo `storage/order-code-verification/{harness,results}` trong checkout fix.
   Chép các file ở đây vào `harness/`. Các script suy đường dẫn từ vị trí này.
2. Xuất `app/` của commit `a81decd` vào `before-app/` trong runtime đó.
3. Chuẩn bị network Docker riêng `knjsc-code-test`, PostgreSQL 16
   `knjsc-code-db`, Redis `knjsc-code-redis`, user test `code_test`.
   Không expose PostgreSQL ra host; app chỉ bind localhost cổng 8851.
4. Tạo `runtime.env` với mật khẩu/secret ngẫu nhiên và các biến:
   `POSTGRES_HOST=knjsc-code-db`, `POSTGRES_PORT=5432`,
   `POSTGRES_USER=code_test`, `POSTGRES_DB=knjsc_code_regression`,
   `RUN_MIGRATIONS=0`, `PYTHONPATH=/harness:/app`,
   `REDIS_URL=redis://knjsc-code-redis:6379/0`.
5. Tạo database rỗng `test_knjsc_code_load`. Container seed dùng image
   `knjsc-web` sẵn có, mount checkout `app:/app`, runtime `:/runtime`,
   harness `:/harness`, env file ở trên và hai biến ghi đè
   `POSTGRES_DB=test_knjsc_code_load`, `DJANGO_SETTINGS_MODULE=mixed_settings`.
   Chạy `python /harness/setup.py`: migrate database test rồi seed 100k đơn.
   Script từ chối tên/host database khác và database đã có đơn.
6. Khi seed đã thoát, dùng `createdb -T test_knjsc_code_load` tạo bản gốc
   `test_knjsc_code_pristine`. `start_app.py` thay thế **database test load**
   từ bản gốc trước mỗi lượt chính; không dùng với dữ liệu cần giữ.

`start_app.py` cần container app test đã tồn tại trên đúng network. Lần đầu
tạo app bằng các mount/env ở bước 5, cổng `127.0.0.1:8851:8000`, lệnh
`gunicorn mixed_wsgi:application --bind 0.0.0.0:8000 --workers 3 --threads 4
--timeout 60 --keep-alive 5`. Các bước sau tự thay app test.

## Trình tự

- Chạy hồi quy pytest trên DB riêng trước; `pytest.ini` dùng settings test.
- `python harness/start_app.py before`, rồi `python harness/run_phase.py before-delivery`.
- Kiểm `PHASE=before-delivery python /harness/verify.py` trong app **trước khi reset DB**.
- `python harness/start_app.py after`; chạy `e2e.cjs` bằng Node + Playwright
  và Chrome sẵn có; trong app chạy `e2e_verify.py`, `startup_check.py`.
- Reset lại bằng `start_app.py after`, chạy `run_phase.py after-delivery`,
  đối chiếu `verify.py` trước reset.
- Reset lại bằng `start_app.py after`, chạy `run_phase.py after-mixed mixed`,
  đối chiếu `verify.py`. Chín Vận đơn Locust + một Chrome = tổng 10;
  30 Sale nghỉ 20–40 giây giữa các đơn. Mỗi lượt chính 362 giây cấu hình,
  bỏ 60 giây làm nóng; nghiệm thu yêu cầu thực đo ít nhất 300 giây.
- Trong app chạy `burst.py`, rồi `PHASE=burst python /harness/verify.py`.
- `start_app.py compat` giữ DB test, chỉ bật READ/SYNC/RECEIPTS/RENDER;
  chạy `run_phase.py compat-smoke mixed`, đối chiếu `verify.py`.
  Đây là kiểm tương thích ngắn, không thay lượt nghiệm thu cờ tắt.
- `analyze.py before-delivery after-delivery after-mixed compat-smoke`
  tổng hợp HTTP, SQL, thời gian câu lấy khóa, Chrome và Docker stats.

`run_phase.py` dùng đường dẫn Node của máy kiểm chứng; chỉnh **harness local**
nếu runtime Node nằm nơi khác. Không cài dependency chỉ để chạy các script này.
`browser.cjs` hỗ trợ `WIDTH=390`; mặc định 1440. Chỉ số `edit-to-save` có
500 ms debounce phía client; thời gian HTTP `grid/save` được ghi riêng.

## Bằng chứng và dọn dẹp

- Kết quả ở `results/`; log SQL riêng từng process/thread, không ghi tham số SQL.
- `lock_ms` đo thời gian thực thi câu lấy advisory lock, gồm roundtrip tới PG;
  là xấp xỉ thời gian chờ, không phải phép đo CPU riêng bên trong PostgreSQL.
- ID ghi ô lấy từ phản hồi lưu, sau đó đối chiếu DB/lịch sử. Đơn đối chiếu mã,
  Sale, hai sản phẩm, Decimal, bản sao Vận đơn và phản hồi thành công.
- Dừng nếu sai phạm vi dữ liệu, sai xác nhận ghi hoặc ba lỗi server bất ngờ.
  Báo riêng warm-up, timeout dự kiến và mọi lỗi; không coi lượt ngắn là đủ tải.
- Sau khi giữ kết quả, gỡ đúng container `knjsc-code-*` do lần chạy tạo,
  volume database test và network; xóa env/session tạm (`ready.json`).
  Không dùng `docker system prune`, xóa volume Compose hoặc database khác.

Biên bản kết quả: [kiểm chứng](../../docs/kiem-chung-trung-ma-don-20260911.md).
