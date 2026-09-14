# Kiểm tải hỗn hợp 30 Sale + 10 Vận đơn — 11.09.2026

**Kết luận: chưa nghiệm thu tải hỗn hợp. Phát hiện lỗi trùng mã đơn gây HTTP 500; chưa sửa code ứng dụng.**

## Phạm vi và môi trường

- Yêu cầu: mô phỏng 30 Sale lên đơn trong khi 10 nhân sự Vận đơn thao tác bảng tính.
- Snapshot checkout chính `vandonmoi`, HEAD `3c3fd09` cộng thay đổi chưa commit lúc bắt đầu. Không dùng nhánh `CRM-Optimization`. SHA256 từng file tại `storage/mixed-sale30-delivery10-20260911/source-manifest.json`.
- Database PostgreSQL 16 riêng `test_knjsc_mixed40`, container/network riêng `knjsc-mixed40-*`; không seed, migrate, kiểm tải hoặc restart dịch vụ nghiệp vụ đang dùng.
- 100.000 Order/Customer/DataRecord mẫu, 200.000 OrderLine và 200.000 WaybillItem; 30 tài khoản Sale + 10 tài khoản Vận đơn Staff riêng. Mỗi Vận đơn được giao 10.000 dòng. Ngày nghiệp vụ phân bố năm 2026; dữ liệu hoàn toàn tổng hợp. Chưa mô phỏng kho lịch sử nhiều năm.
- Gunicorn 3 worker × 4 thread, keep-alive 5s; dùng code thật, kiểm quyền/CSRF/giao dịch thật. Phiên đăng nhập test chuẩn bị trước, không đo chi phí đăng nhập. Static phục vụ bởi Django StaticFilesHandler cho Chrome; chưa có reverse proxy/CDN/nén production.
- Docker local báo 12 CPU và 8.192.139.264 byte RAM (~7,63 GiB). Nhiều ứng dụng khác vẫn chạy trên máy; không kết luận năng lực VPS 24 GB hoặc đường truyền WAN.

## Kịch bản và cách đo

1. Smoke 1 Sale + 1 Vận đơn: 35s; 33 request, không lỗi; một đơn ghi đúng cả Order và vận đơn. Kiểm Chrome riêng trước lượt chính.
2. Baseline: 9 Vận đơn Locust + 1 Vận đơn Chrome; 60s làm nóng, 299,55s đo. 2.190 request Locust trong cửa sổ đo, 0 lỗi; 2.596 request cả lượt.
3. Hỗn hợp: thêm 30 Sale, ramp 2 người/s; Locust có 30 Sale + 9 Vận đơn, Chrome là Vận đơn thứ 10. Dự kiến 60s làm nóng + 300s đo, nhưng **dừng ở 33,33s vì 3 HTTP 500**. Đủ 39 user Locust sau ~19s; chỉ khoảng 14s ở đủ số người, chưa có cửa sổ đo ổn định.

Sale kiểm khách → xem trước hai sản phẩm (tổng Decimal 40,40 USD) → POST tạo đơn; nghỉ 20–40s giữa chu kỳ. Có lần nghỉ ngẫu nhiên đầu phiên. Vận đơn mô phỏng đổi vùng đọc, lọc trạng thái, tìm kiếm rộng, kiểm phiên bản/phạm vi khoảng 8s và lưu một ô sau mỗi ba chu kỳ (nghỉ 1–3s). Đây là mô hình HTTP có nhịp đặt trước, không mô phỏng chính xác cache/hủy request và mọi request HTML điều khiển bộ lọc của chín trình duyệt; không dùng nó làm chứng nhận năng lực.

Chrome thật headless 1440×900 cuộn, chọn ô, đổi tìm kiếm, sửa ghi chú và chờ autosave. Phiên này dùng JS/cache/poll thực tế. Đo từ thao tác đến dữ liệu sẵn sàng bằng Playwright; số đo này có chi phí automation, không phải INP thực địa. Instrument render và PerformanceObserver, không thay thuật toán ứng dụng. Chưa chạy 390px, máy yếu, 10 Chrome thật hoặc mạng Internet.

Đơn mới giữ đúng nghiệp vụ **chưa phân công**; không tự gán cho Vận đơn trong harness. Do đó chưa mô phỏng bước Leader phân công đơn mới. Phạm vi mỗi Staff vẫn 10.000 dòng, không giả định đơn chưa giao làm thay đổi tập dòng của họ.

## Lỗi tạo đơn đồng thời — ưu tiên xử lý

- 38 POST tạo đơn: **35 thành công, 3 HTTP 500** (7,89% trong mẫu khởi động này; không ngoại suy thành tỷ lệ lỗi vận hành).
- Cả ba lỗi SQLSTATE `23505`, constraint `orders_order_code_key`.
- `app/orders/services/order_service.py::_sinh_ma_don()` đọc mã lớn nhất theo tiền tố ngày rồi cộng 1. Hai giao dịch có thể đọc cùng mã trước khi bên kia commit; `full_clean()` không làm bước cấp mã trở thành nguyên tử. Ràng buộc unique chặn bản ghi thứ hai, lỗi IntegrityError đi ra HTTP 500.
- Đối chiếu sau tải: đủ 35 đơn được xác nhận, đúng Sale, tổng 40,40 USD, hai dòng sản phẩm và liên kết/bản sao Vận đơn. Ba yêu cầu lỗi không để lại đơn hoàn chỉnh hay bản ghi đơn–vận đơn lưu dở. Không có đơn đã commit nhưng không nhận phản hồi thành công trong mẫu.
- Không giảm tải giả tạo, bỏ ràng buộc unique hoặc sửa nghiệp vụ để tiếp tục chạy. Cần duyệt/sửa cơ chế cấp mã đồng thời trên nhánh fix riêng, rồi chạy lại kịch bản đủ cửa sổ đo.

## Độ trễ baseline — 10 Vận đơn

| Thao tác HTTP | Mẫu | p50 ms | p95 ms | p99 ms | Lỗi |
|---|---:|---:|---:|---:|---:|
| grid/scroll | 859 | 101.85 | 160.64 | 201.51 | 0 |
| grid/filter | 263 | 92.59 | 145.99 | 195.63 | 0 |
| grid/search | 130 | 190.77 | 268.16 | 319.62 | 0 |
| grid/poll | 293 | 70.06 | 121.13 | 186.72 | 0 |
| grid/scope | 268 | 24.99 | 48.76 | 67.92 | 0 |
| grid/save | 377 | 51.45 | 115.33 | 146.56 | 0 |

Tất cả HTTP đọc trong kịch bản baseline có p95 dưới 1s; lưu ô dưới 0,5s. Nhưng đường đọc khối đang có trung vị 12 truy vấn HTTP, vượt mục tiêu trần 10; không coi toàn bộ tiêu chí đã đạt.

| Chrome baseline | Mẫu | p50 ms | p95 ms |
|---|---:|---:|---:|
| scroll-ready | 84 | 313 | 834 |
| select-paint | 84 | 63 | 80 |
| edit-to-save | 21 | 603 | 648 |
| filter-ready | 16 | 221 | 353 |

Render p95 16ms, max 31,2ms; không ghi nhận long task ≥50ms trong cửa sổ đo. Mở bảng đến khối đầu 1.280ms là **một mẫu**, nằm ngoài cửa sổ đo ổn định. `edit-to-save` bao gồm chờ autosave khoảng 500ms, không phải toàn bộ là server chậm. Playwright tự đợi selector có thể làm thời gian scroll-ready lớn hơn thời gian API; chưa quy toàn bộ 834ms cho server.

## Nơi tốn thời gian đã quan sát

- Tìm kiếm rộng là API chậm nhất trong các thao tác đã đo ổn định: p95 ~268ms. Read-block có ~70% tổng thời gian trong SQL; poll ~84% (từ log kỹ thuật hợp lệ, không suy ra toàn bộ là CPU database).
- COUNT kết quả, COUNT/MAX để xác định phiên bản và truy vấn lấy ID chiếm nhiều thời gian. EXPLAIN sau tải cho thấy COUNT/MAX có thể đi qua ~100.036 mục index của DataRecord rồi nối với 10.000 phân công; trả 100 dòng không có nghĩa chỉ đọc 100 dòng.
- Tìm kiếm rộng dùng scan song song DataRecord và kiểm phân công; COUNT và truy vấn lấy ID riêng đều ~52ms trong lần EXPLAIN không tải. OFFSET sâu còn sắp xếp 10.000 ID trước khi lấy 100 dòng. Các phép EXPLAIN là mẫu chẩn đoán sau tải, không phải p95 dưới tải.
- Baseline: CPU ứng dụng p95 ~47,82% của **một core**, PostgreSQL ~140,95% (khoảng 1,41 core); RAM mẫu cuối ~228MiB app, ~326MiB DB. Đây là số container, không phải toàn máy. Chưa thấy hai container bão hòa tài nguyên trong các mẫu.
- Lượt hỗn hợp quá ngắn để so sánh tăng/giảm hiệu năng hợp lệ. Trong 33s đầu, API cuộn max ~203ms, tìm kiếm max ~233ms (8 mẫu), lưu ô max ~124ms; vấn đề chặn nghiệm thu là tạo đơn lỗi, không phải đã chứng minh nghẽn CPU/mạng/render.
- Chưa kiểm partition, chưa thể kết luận chia quý giúp bao nhiêu. Partition không sửa lỗi cấp mã đơn.

## Kiểm toàn vẹn và giới hạn bộ đo

Baseline đối chiếu 58 ô cuối cùng; mixed đối chiếu 21 ô; không sai dữ liệu. Tất cả kết quả HTTP đọc được kiểm mã nhân viên được giao đúng tài khoản. Chrome không có pageerror hoặc lỗi thao tác ở hai lượt chính.

Hai smoke Chrome đầu bị timeout vì harness cố bấm nút Xong đang ẩn trong chế độ nhập tại ô; đổi harness sang Ctrl+Enter đúng thao tác hiện có, không sửa UI. Một số lần harness đọc data-id của placeholder trước khi ô sẵn sàng; đã đối chiếu lại qua GridCellHistory và sửa harness lấy ID từ phản hồi lưu. Không đánh tráo lỗi harness thành lỗi sản phẩm.

Log chi tiết SQL baseline trên bind mount Windows có 33 dòng JSON không đọc được trong tổng 3385 dòng của toàn bộ file kỹ thuật; loại chúng khỏi tổng hợp chẩn đoán. Độ trễ/p95 HTTP lấy từ Locust và Server-Timing, không phụ thuộc file hỏng. Mixed chuyển sang file riêng từng worker/thread; đủ ba lỗi constraint được ghi nhận.

Trong raw `mixed.json`, `measured_seconds=0.001` là giá trị tránh chia cho 0 của harness, **không phải cửa sổ đo thật**: thời gian đo sau warm-up thực tế bằng 0. `analysis.json` ghi `diagnostic_only=true`, chỉ phân tích 33,33s khởi động. Không lấy percentile mẫu này thay cho kiểm tải 5 phút.

## Bằng chứng và chạy lại

Thư mục local (gitignore): `storage/mixed-sale30-delivery10-20260911/`.
- `results/baseline.json`, `mixed.json`, `*-browser.json`, `*-resources.jsonl`, `*-integrity.json`, `analysis.json`, `query-plans.json`, log kỹ thuật từng thread.
- `harness/seed.py`, `setup.py`, `mixed_settings.py`, `mixed_wsgi.py`, `mixed_metrics.py`, `locust_mixed.py`, `browser.cjs`, `resources.py`, `verify.py`, `profile.py`, `analyze.py`.
- Snapshot code và manifest giữ để đối chiếu. Phiên và mật khẩu test chỉ dùng local; không đưa vào Git/tài liệu. Không sao chép dữ liệu thật.

Các lệnh chính (chạy trong container test riêng đã gắn snapshot và harness; không chạy setup bằng cấu hình database thật):

```text
python /harness/setup.py
gunicorn mixed_wsgi:application --bind 0.0.0.0:8000 --workers 3 --threads 4 --worker-class gthread --keep-alive 5
# Baseline: MIXED=0 PHASE=baseline WARMUP=60
locust -f /harness/locust_mixed.py --headless --host http://knjsc-mixed40-app:8000 --users 9 --spawn-rate 2 --run-time 360s --stop-timeout 35 --only-summary
# Mixed: MIXED=1 PHASE=mixed WARMUP=60; Chrome là Vận đơn thứ 10
locust -f /harness/locust_mixed.py --headless --host http://knjsc-mixed40-app:8000 --users 39 --spawn-rate 2 --run-time 360s --stop-timeout 35 --only-summary
node storage/mixed-sale30-delivery10-20260911/harness/browser.cjs
python /harness/verify.py
python /harness/profile.py
python storage/mixed-sale30-delivery10-20260911/harness/analyze.py baseline mixed
```

Chỉ cập nhật phát hiện và kết quả kiểm thử. Chưa sửa ứng dụng, chưa commit/push; không đánh dấu yêu cầu nghiệp vụ `-> đã làm` từ lần kiểm tải này.

## Dọn môi trường sau kiểm chứng

Đã dừng và gỡ đúng ba container `knjsc-mixed40-app/db/redis`, volume tạm của chúng và network `knjsc-mixed40-test`. Đã xóa file môi trường chứa mật khẩu và manifest chứa phiên đăng nhập test. Các dịch vụ nghiệp vụ và worktree khác giữ nguyên. Snapshot và bằng chứng còn khoảng 8,3 MiB; SHA256 snapshot kiểm lại khớp. Muốn chạy lại phải tạo fixture/session mới bằng harness trên môi trường test riêng.
