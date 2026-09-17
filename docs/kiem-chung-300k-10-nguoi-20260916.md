# Vận đơn DB: 300.000 dòng và 10 người — 16.09.2026

## Mốc thực tế được chủ dự án xác nhận

Tối đa 10 người cùng sử dụng file Vận đơn; khoảng 100.000 đơn/năm, kiểm dự phòng 300.000 dòng. Đây là mốc kiểm thực tế mới, không lấy kết quả 20 người của lượt trước làm yêu cầu sản phẩm. Không tự đánh dấu AC khác đã đạt.

## Vì sao số cũ có lúc local chậm hơn

Lượt trước hai bên đều 10.000 dòng/26 cột, nên không do local có nhiều dòng hơn. Ở 10 người, API đọc local/VPS p95 148/432 ms và lưu 139/373 ms; chỉ một probe cuộn dưới tải cho local/VPS 351/245 ms. Mỗi probe chỉ 40 bước; CPU, mạng, thời điểm lưu và cache khác nhau. Code có đường 409 đọc -> invalidate toàn cache và log có 409, nhưng chưa có A/B cô lập để quy toàn bộ chênh lệch cho đường này. Không kết luận bản local chậm hơn toàn diện hoặc đã chứng minh tăng tốc frontend.

## Cách đo lần này

- Hai DB tổng hợp độc lập `test_concurrency_300k_20260916`, cùng 300.000 DataRecord và 300.000 phân công, 26 cột theo metadata Vận đơn DB. Không sao chép hồ sơ khách thật. Ngày trải 17/09/2023–16/09/2026; tháng 08/2026 có 8.496 dòng, gồm các dòng của người thử. Không tạo 300.000 Order/OrderLine; không đo tác vụ nhập/xuất, thống kê hoặc toàn bộ nghiệp vụ đặt hàng.
- 11 tài khoản Staff giả, quyền xem toàn bảng theo lựa chọn hệ thống; mỗi người ghi trên dòng được phân công riêng. Các lượt HTTP dùng 1 rồi 10 người; lượt browser dùng 9 Locust + 1 Chromium. Không mở quyền trên dữ liệu thật.
- VPS dùng nguyên image đang chạy `knjsc-app:da6e2c0-overview-20260916` trên chính VPS 2 vCPU/4 GB. Local dùng bản chụp cố định của working tree; hash lưu trong artifact, không dùng code đang bị task khác sửa. Docker local thấy 12 CPU/~7,63 GiB, có các ứng dụng khác đang chạy, gồm task kiểm cờ tối ưu riêng.
- Cả hai Gunicorn 1 worker × 4 thread, PostgreSQL 16 riêng; app 640 MiB, DB 1,25 GiB (khớp giới hạn DB production), CPU shares 256. DB của lượt 10k trước chỉ 512 MiB, nên không coi hai lượt là A/B chỉ thay số dòng. CRM_OPT_* tắt ở cả hai, theo cấu hình production.
- Cùng máy phát tải; VPS qua SSH tunnel/Internet, local qua host.docker.internal. Không qua nginx/TLS/nén production. Chênh lệch gồm phần cứng và mạng, không phải hiệu quả thuần của thay đổi code.
- 1 người: 45 giây, bỏ 10 giây đầu. 10 người: 90 giây, bỏ 15 giây đầu; tăng 2 người/giây, nghỉ 0,7–1,3 giây sau thao tác. Trọng số đọc 5/lọc mã 2/lưu 2; poll khoảng 8 giây theo chu kỳ đọc. Chờ tối đa 45 giây cho request kết thúc khi dừng.
- Đọc 100 dòng ở đầu, offset 100, 25%, 50% và cuối tập kết quả. Chế độ tháng áp bộ lọc ngày cho đọc khối/poll; tìm mã chính xác vẫn tìm toàn bảng. Lưu ghi chú từng dòng riêng, kiểm phản hồi và đọc lại giá trị cuối. 10 virtual user này không tương đương 10 Chrome với đầy đủ tải trước/poll.
- Dừng khi sai dữ liệu/HTTP bất thường, RAM VPS khả dụng <400 MB, hoặc 3 mẫu giám sát liên tiếp lỗi/domain đăng nhập >2 giây. Không thay cấu hình hoặc restart dịch vụ thật.

## Kết quả HTTP

Đơn vị ms; p95 là mốc 95% mẫu không vượt quá. Baseline 1 người có ít mẫu nên không suy thành năng lực bền vững.

| Bản | Người | Góc nhìn | Mẫu đọc | Đọc p95 | Tìm mã p95 | Mẫu lưu | Lưu p95 | Poll p95 | Kiểm giá trị cuối |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| local | 1 | 300.000 dòng | 16 | 615.43 | 233.66 | 3 | 93.5 | 208.38 | 1 |
| local | 1 | Tháng: 8.496 dòng | 16 | 468.43 | 257.4 | 5 | 64.58 | 244.78 | 1 |
| local | 10 | 300.000 dòng | 259 | 1374.48 | 780.35 | 98 | 485.86 | 944.43 | 10 |
| local | 10 | Tháng: 8.496 dòng | 290 | 826.74 | 640.45 | 107 | 306.62 | 588.56 | 10 |
| vps | 1 | 300.000 dòng | 12 | 1944.74 | 464.67 | 5 | 125.51 | 533.68 | 1 |
| vps | 1 | Tháng: 8.496 dòng | 7 | 976.32 | 552.83 | 8 | 105.22 | 572.21 | 1 |
| vps | 10 | 300.000 dòng | 92 | 5043.86 | 3236.92 | 37 | 2341.01 | 3868.59 | 10 |
| vps | 10 | Tháng: 8.496 dòng | 136 | 3087.1 | 2249.89 | 50 | 1568.27 | 2424.43 | 10 |

Tổng 1740 mẫu trong cửa sổ đo của 8 lượt hợp lệ; không lỗi HTTP hoặc mismatch lưu. Kiểm sau lượt xác nhận đúng giá trị cuối của 1/10 dòng tương ứng. Không diễn giải thành đã kiểm đầy đủ xung đột cùng ô, paste lớn hoặc Undo trong lần này.

Ngưỡng đối chiếu hiện có: đọc p95 <=1.000 ms, lưu <=500 ms, poll <=300 ms. VPS 300k/10 người vượt cả ba ở cả hai góc nhìn; local toàn bảng vượt đọc/poll, local lọc tháng vượt poll. Chưa đạt trải nghiệm mượt ở mốc này.

## Tài nguyên và điểm nghẽn

- local / all: CPU cực đại theo mẫu {'knjsc-bench-300k-20260916-app-1': 33.21, 'knjsc-bench-300k-20260916-db-1': 342.36}; RAM cuối {'knjsc-bench-300k-20260916-app-1': '92.02MiB / 640MiB', 'knjsc-bench-300k-20260916-db-1': '622.7MiB / 1.25GiB'}; RAM VPS khả dụng nhỏ nhất None KB; health domain cao nhất None giây, trạng thái không áp dụng. CPU 100% = một core; đây là mẫu định kỳ, có thể bỏ lỡ spike.
- local / month: CPU cực đại theo mẫu {'knjsc-bench-300k-20260916-app-1': 37.97, 'knjsc-bench-300k-20260916-db-1': 282.19}; RAM cuối {'knjsc-bench-300k-20260916-app-1': '91.77MiB / 640MiB', 'knjsc-bench-300k-20260916-db-1': '604.9MiB / 1.25GiB'}; RAM VPS khả dụng nhỏ nhất None KB; health domain cao nhất None giây, trạng thái không áp dụng. CPU 100% = một core; đây là mẫu định kỳ, có thể bỏ lỡ spike.
- vps / all: CPU cực đại theo mẫu {'knjsc-bench-300k-20260916-app-1': 20.9, 'knjsc-bench-300k-20260916-db-1': 189.59, 'knjsc-production-crm-1': 0.03, 'knjsc-production-db-1': 5.3}; RAM cuối {'knjsc-bench-300k-20260916-app-1': '88.8MiB / 640MiB', 'knjsc-bench-300k-20260916-db-1': '346.2MiB / 1.25GiB', 'knjsc-production-crm-1': '74.11MiB / 640MiB', 'knjsc-production-db-1': '56.43MiB / 1.25GiB'}; RAM VPS khả dụng nhỏ nhất 2434112 KB; health domain cao nhất 0.191577 giây, trạng thái ['200']. CPU 100% = một core; đây là mẫu định kỳ, có thể bỏ lỡ spike.
- vps / month: CPU cực đại theo mẫu {'knjsc-bench-300k-20260916-app-1': 31.01, 'knjsc-bench-300k-20260916-db-1': 175.72, 'knjsc-production-crm-1': 0.03, 'knjsc-production-db-1': 4.21}; RAM cuối {'knjsc-bench-300k-20260916-app-1': '90.02MiB / 640MiB', 'knjsc-bench-300k-20260916-db-1': '366.6MiB / 1.25GiB', 'knjsc-production-crm-1': '74.12MiB / 640MiB', 'knjsc-production-db-1': '60.76MiB / 1.25GiB'}; RAM VPS khả dụng nhỏ nhất 2432016 KB; health domain cao nhất 0.214495 giây, trạng thái ['200']. CPU 100% = một core; đây là mẫu định kỳ, có thể bỏ lỡ spike.

Profile đọc một khối gần cuối sau khi ngừng tải (Django test Client trong app test, không bao gồm mạng) có EXPLAIN ANALYZE cho các truy vấn chậm:

| Bản | Góc nhìn | Tổng request ms | SQL ms | Số SQL |
|---|---|---:|---:|---:|
| local | all | 916 | 605 | 13 |
| local | month | 217 | 187 | 12 |
| vps | all | 1577 | 1328 | 13 |
| vps | month | 552 | 481 | 12 |

Truy vấn phiên bản `COUNT(*) + MAX(updated_at)` nối DataRecord với bảng và phân công, vẫn đọc 300.000 dòng kể cả khi lọc một tháng. EXPLAIN local ghi nhận Hash Join 300.000 dòng, Index Only Scan DataRecord và Seq Scan bảng phân công. Đường đọc còn đếm kết quả và lấy ID với offset; các phần này đáng kể khi mở toàn lịch sử. SQL là điểm nghẽn đã đo; chưa triển khai sửa hoặc bật cờ tối ưu.

## Trình duyệt

Chromium 1280×720, renderer thật, thêm nút đo chỉ ở WSGI test. 40 bước cuộn 560px, chờ dữ liệu vùng nhìn rồi một rAF; 30 bước qua lại gần vùng vừa tải; 30 lần chọn bằng pointer tổng hợp/hai rAF. Thêm ba lần nhảy đến dòng 10.000/150.000/299.950. Timeout chờ dữ liệu mỗi bước 10 giây. Đây không phải số đo INP thực địa hoặc wheel liên tục. Nhãn cached không bảo đảm không phát sinh request khi cache bị vô hiệu hóa.

| Bản/lượt | Cuộn p50 | Cuộn p95 | Vùng vừa tải p95 | Chọn ô p95 | Hoàn tất |
|---|---:|---:|---:|---:|---|
| local-browser-concurrent | 24.1 | 1487.2 | 34.3 | 33.7 | True  |
| local-browser-repeat | 23.6 | 1212.1 | 35.7 | 34.4 | True  |
| vps-browser-concurrent | 32.1 | 8119 | 45.5 | 35.7 | False Data timeout |

- local-browser-concurrent: nhảy xa [{'row': 10000, 'ms': 1016.8000000119209}, {'row': 150000, 'ms': 1216.1000000238419}, {'row': 299950, 'ms': 1220.5999999642372}]; long task >=50ms: 0. Lượt lặp local là kiểm bổ sung cùng cửa sổ tải 120 giây, không dùng để khẳng định mức tăng tốc.

- local-browser-repeat: nhảy xa [{'row': 10000, 'ms': 4249.099999964237}, {'row': 150000, 'ms': 1100.7000000476837}, {'row': 299950, 'ms': 849.8999999761581}]; long task >=50ms: 0. Lượt lặp local là kiểm bổ sung cùng cửa sổ tải 120 giây, không dùng để khẳng định mức tăng tốc.

- vps-browser-concurrent: nhảy xa [{'row': 10000, 'ms': 4850}]; long task >=50ms: 0. Lượt lặp local là kiểm bổ sung cùng cửa sổ tải 120 giây, không dùng để khẳng định mức tăng tốc.

## Sự cố harness và giới hạn

Lượt VPS baseline đầu có request hoàn tất không lỗi nhưng ba mẫu giám sát SSH không thu được; guard dừng tiến trình đo trước khi tăng tải. Kiểm lại thấy production vẫn chạy, domain HTTP 200. Giữ artifact `vps-all-1-monitor-aborted.*`, không đưa vào bảng chính. Sửa harness lưu từng mẫu giám sát ngay và giảm tần suất kết nối SSH từ 8 lên 15 giây; chạy lại toàn bộ VPS từ baseline. Không gọi sự cố thu giám sát là lỗi ứng dụng.

## Bằng chứng, lệnh chạy và bàn giao

- Raw/harness/hash snapshot/SQL profile: `storage/concurrency-300k-20260916/` (gitignore). Các manifest chứa phiên tài khoản giả chỉ giữ ở khu kiểm thử, không đưa vào Git.
- Tóm tắt sạch: `docs/verification/concurrency-300k-20260916.json`. Harness: `python storage/concurrency-300k-20260916/harness/run_stages.py local` hoặc `vps`; chỉ chạy sau khi kiểm DB/tunnel và đọc script. Không dùng seed trên dữ liệu thật.
- Compose project riêng: `knjsc-bench-300k-20260916`, cổng test local/VPS loopback 18731, tunnel 18732. Snapshot local là bản chụp code lúc bắt đầu, không bao gồm thay đổi task khác sau thời điểm đó.
- Mốc triển khai tiếp cần duyệt riêng: xử lý truy vấn phiên bản/đếm và lấy khối trên tập lớn, phối hợp cache/sync khi có người khác lưu, rồi đo lại cùng bộ dữ liệu. Giữ quyền và kiểm toàn vẹn; không đổi sang tải hết 300k dòng vào trình duyệt.
- Tác vụ này chỉ đo và cập nhật hồ sơ; không sửa ứng dụng, không commit/push/phát hành.

## Kết thúc phiên kiểm thử

Hai app/DB kiểm thử đã dừng, giữ volume dữ liệu giả để tái lập. Tab đo đã đóng. Production CRM/ERP vẫn running trên image cũ; checkout VPS vẫn `3e5b9a4`; health đăng nhập sau kiểm HTTP 200 trong 0,131 giây. Không restart/reload production.

Lượt browser VPS hoàn tất 40 bước cuộn, 30 bước vùng vừa tải và 30 lượt chọn; nhảy dòng 10.000 mất 4,85 giây, bước dòng 150.000 vượt timeout 10 giây, nên không đạt toàn bài. HTTP nền 9 người vẫn kiểm lại đúng 9 giá trị cuối, không lỗi. Lượt browser local nền cũng đúng 9 giá trị. Log app trong các cửa sổ browser có GET 409: local 12, VPS 11; cửa sổ/nhịp không bằng nhau, không dùng làm tỷ lệ lỗi hay bằng chứng mọi timeout do 409. Không có lỗi ghi trong log này.
