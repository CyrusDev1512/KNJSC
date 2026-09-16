# Đo đồng thời Vận đơn DB — 16.09.2026

## Môi trường và giới hạn so sánh

- VPS: image đang phát hành `knjsc-app:da6e2c0-overview-20260916`, máy 2 vCPU / 4 GB RAM; chạy bản sao kiểm thử trên chính VPS, không đánh tải vào database nghiệp vụ.
- Local: working tree hiện tại gồm tối ưu cuộn/chọn ô và các sửa báo cáo chưa phát hành; Docker thấy 12 CPU / khoảng 7,63 GiB RAM. Không đo bằng Django runserver.
- Cả hai: Gunicorn 1 worker × 4 thread, PostgreSQL 16 riêng, app giới hạn 640 MiB, DB test 512 MiB, CPU shares 256 để nhường dịch vụ thật. DB production đang có giới hạn 1,25 GiB; DB kiểm thử chỉ chứa bộ dữ liệu nhỏ.
- Cấu trúc 26 cột lấy từ metadata Vận đơn DB thực tế; 10.000 dòng hoàn toàn tổng hợp. 41 Staff thử, xem toàn bảng qua lựa chọn hệ thống và chỉ sửa dòng được phân công. Không copy dữ liệu khách hàng.
- Schema thực tế có workflow `waybill`; các cờ CRM_OPT_* vẫn tắt. Không dựa vào nhận định profile trong daily task cũ.
- Dùng Locust có sẵn, cùng máy phát tải. Local đi qua host.docker.internal; VPS qua Internet/SSH tunnel tới app test. Bỏ qua nginx/TLS/nén production. Chênh lệch bao gồm máy và mạng, không phải A/B chỉ đổi code.
- Mỗi mức: 15 giây khởi động, khoảng 60 giây đo; tăng 2 người/giây. Mỗi người nghỉ ngẫu nhiên 0,7–1,3 giây, trọng số đọc 5 / lọc 2 / sửa 2, poll khoảng 8 giây khi đến chu kỳ đọc. Đọc khối 100 dòng ở offset 0/100/1000/5000/9900; lọc mã chính xác; ghi một ô ghi chú trên dòng riêng.
- Các con số người ở bảng HTTP là virtual user với nhịp trên, không phải cùng số Chrome đầy đủ, không phải số tài khoản đăng nhập để yên.
- Ngưỡng đối chiếu core/constants.py: p95 đọc <=1000 ms, lưu <=500 ms, poll <=300 ms, không lỗi. Không suy thành chứng nhận AC-10.8 vì chưa 100.000 dòng/100 người/5 phút hoặc chạy bền.
- Dừng khi sai dữ liệu/quyền/HTTP bất thường, RAM khả dụng VPS dưới 400 MB hoặc domain thật lỗi/chậm trên 2 giây trong 3 mẫu. Không restart dịch vụ thật.

## HTTP — kết quả từng thao tác

p95: 95% mẫu nhanh hơn hoặc bằng số này. Mốc 1 người có ít mẫu ghi nên chỉ là baseline ngắn.

| Bản | Người | Mẫu đọc | Đọc p95 ms | Lọc p95 ms | Mẫu lưu | Lưu p95 ms | Poll p95 ms | Lỗi HTTP | Dòng cuối kiểm lại |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| local | 1 | 35 | 127.39 | 56.1 | 6 | 97.63 | 49.51 | 0 | Chỉ phản hồi lưu |
| vps | 1 | 26 | 226.79 | 103.0 | 13 | 126.61 | 104.75 | 0 | 1 |
| local | 5 | 154 | 142.29 | 93.59 | 62 | 125.45 | 69.7 | 0 | 5 |
| vps | 5 | 127 | 299.88 | 222.24 | 61 | 261.88 | 209.01 | 0 | 5 |
| local | 10 | 313 | 147.56 | 98.35 | 121 | 139.09 | 75.43 | 0 | 10 |
| vps | 10 | 238 | 432.01 | 325.75 | 122 | 373.18 | 236.92 | 0 | 10 |
| local | 20 | 570 | 287.72 | 225.96 | 211 | 272.37 | 199.21 | 0 | 20 |
| vps | 20 | 419 | 965.36 | 757.82 | 157 | 848.2 | 803.88 | 0 | 20 |

## Toàn vẹn và tải máy

- Kiểm từng phản hồi lưu đúng giá trị, đọc lại ô sau khi kết thúc; mốc local 1 người chạy trước khi bổ sung bước đọc lại cuối lượt, không gán kiểm này cho lượt đó.
- Hai môi trường kiểm riêng: ghi đầu HTTP 200, sửa bằng dữ liệu cũ HTTP 409, replay cùng operation HTTP 200, giá trị đúng, người chưa được phân công sửa HTTP 403.
- Lượt local 20 đầu tiên bị bộ đo cắt một request đang lưu khi hết giờ: audit xác nhận giá trị cuối mới hơn giá trị đã nhận trước đó, cùng tác giả, thời điểm đúng lúc dừng. Giữ raw `local-20-interrupted*`; không gọi đây là mất dữ liệu, không tính lượt đó là đạt. Thêm --stop-timeout 15 để chờ request kết thúc và đo lại local 20. Không sửa code ứng dụng để làm phép đo đạt.
- Lượt kiểm quyền đầu của harness dùng chung cookie jar khi đổi tài khoản nên gửi phiên cũ; sửa harness dùng client/cookie tách riêng, kiểm lại thành 403. Đây là lỗi harness, không phải kết luận mở quyền ứng dụng.

- local 20 người: CPU cực đại theo mẫu {'knjsc-bench-20260916-app-1': 79.08, 'knjsc-bench-20260916-db-1': 65.05}; RAM mẫu cuối {'knjsc-bench-20260916-app-1': '91.35MiB / 640MiB', 'knjsc-bench-20260916-db-1': '102MiB / 512MiB'}; RPS 19.45; cửa sổ đo 59.650658792998 giây. CPU 100% tương ứng một core; mẫu khoảng 8 giây/lần nên có thể bỏ lỡ spike.
- vps 20 người: CPU cực đại theo mẫu {'knjsc-bench-20260916-app-1': 82.67, 'knjsc-bench-20260916-db-1': 91.09, 'knjsc-production-crm-1': 0.04, 'knjsc-production-db-1': 5.58}; RAM mẫu cuối {'knjsc-bench-20260916-app-1': '90.13MiB / 640MiB', 'knjsc-bench-20260916-db-1': '85.66MiB / 512MiB', 'knjsc-production-crm-1': '74.08MiB / 640MiB', 'knjsc-production-db-1': '56.43MiB / 1.25GiB'}; RPS 13.86; cửa sổ đo 60.04232566399878 giây. CPU 100% tương ứng một core; mẫu khoảng 8 giây/lần nên có thể bỏ lỡ spike.
- Domain CRM thật trả 200 ở các mẫu giám sát, thời gian lớn nhất 0.459 giây. Đây là trang đăng nhập, không thay thế kiểm luồng nghiệp vụ production.

## Bằng chứng và tái lập

- Raw log, JSON từng request, CPU/RAM, manifest mã và harness: `storage/concurrency-20260916/` (gitignore; manifest phiên thử không đưa vào Git).
- Tóm tắt sạch: `docs/verification/concurrency-20260916.json`.
- Harness Locust: `storage/concurrency-20260916/harness/locust_bench.py`; tham số --users N --spawn-rate 2 --run-time 75s --stop-timeout 15 --headless. Chỉ dùng manifest có database test_concurrency_20260916.
- Mọi seed/migration/ghi chỉ ở DB test riêng. Không commit, push, triển khai bản local hoặc bật cờ tối ưu trên production trong tác vụ đo này.

## Trình duyệt thật dưới tải nền

Chromium Codex 1280×720 trên cùng PC. Trang Django thật với renderer thật; thêm nút đo chỉ trong WSGI kiểm thử, không sửa ứng dụng. Bấm nút qua giao diện. 40 bước cuộn 560px, nghỉ 70ms sau khi vùng nhìn có dữ liệu; 30 lần cuộn qua lại gần vùng cuối; 30 lần chọn ô qua sự kiện pointer tổng hợp và hai rAF. Không phải wheel liên tục, INP thực địa hoặc 10 Chrome thật. So sánh 1 trình duyệt với 9 Locust + 1 trình duyệt, cùng phân công/dữ liệu. Tải nền có cả lưu ô và poll thật.

| Bản | Tải | Cuộn p95 ms | Qua lại vùng vừa tải p95 ms | Chọn ô p95 ms | Long task >=50ms |
|---|---|---:|---:|---:|---:|
| local | idle | 43.4 | 39.9 | 34 | 0 |
| local | concurrent | 350.9 | 34.1 | 33.5 | 0 |
| vps | idle | 125.7 | 42.2 | 33.5 | 0 |
| vps | concurrent | 244.8 | 43.9 | 40.2 | 0 |

Từng probe là một lượt ngắn (40/30/30 mẫu). Khi có ghi nền, cache có thể mất hiệu lực; nhãn cached chỉ mô tả thao tác quay lại gần vùng vừa tải, không bảo đảm không có request mạng. Tất cả probe hoàn tất không lỗi; console VPS không ghi lỗi khi kiểm. Không lấy chênh lệch này làm mức tăng tốc thuần của JS vì backend/phần cứng/mạng khác nhau. Không đạt cam kết mọi thao tác cuộn <=100ms dưới tải hỗn hợp.

## Kết luận trong phạm vi phép đo

VPS 10 người còn trong mục tiêu p95 đọc/lưu/poll ở lượt ngắn; 20 người đọc gần 1s, lưu và poll vượt ngưỡng. Local 20 người vẫn trong các mục tiêu HTTP. Cả hai không có HTTP lỗi ở các lượt hợp lệ, giá trị cuối khớp. VPS chưa cạn RAM trong lượt này; app và PostgreSQL tiêu thụ CPU tăng rõ. Một khối 100×26 ô trả khoảng 321 KB chưa nén. Cần phân tích sâu CPU/SQL/đồng bộ và dung lượng phản hồi trước khi kết luận nâng worker/hạ tầng hay chỉ tối ưu renderer. Chưa thử 40/100 người, chạy bền, nhập/xuất nền, nhiều năm dữ liệu, nhiều team/phòng ban hoặc chỉnh cùng ô đồng thời trong bài tải chính. CAS/replay/quyền sửa kiểm riêng.

## Phát hiện cần xử lý tiếp — chưa sửa trong tác vụ đo

- Cuộn p95 dưới tải hỗn hợp ở lượt browser local là 350,9 ms, VPS 244,8 ms; không tuyên bố bản local đã nhanh hơn dưới tải ghi. Mỗi bản chỉ một probe 40 bước, không đủ chốt mức hồi quy ổn định hoặc nguyên nhân duy nhất.
- Log server riêng trong các phiên browser ghi nhận HTTP 409 trên đường đọc dữ liệu: local 30, VPS 4. Đây là phiên bản đọc không còn hợp lệ khi có ghi, không phải 30/4 lần lưu thất bại. Khoảng quan sát hai phiên không hoàn toàn bằng nhau; không so sánh thành tỷ lệ lỗi vận hành.
- Đối chiếu master-grid.js: HTTP 409 của loadBlock gọi invalidate trước nhánh xử lý lỗi tải đón; invalidation xóa cache/hủy request. Tải trước có thể mất lợi ích khi các người khác liên tục ghi. Cần tách đo cache invalidation/phiên bản và tải đón dưới ghi đồng thời trước khi phát hành tối ưu cuộn.
- HTTP phía Locust không chạy JS/version/cache; kết quả HTTP 0 lỗi không phủ nhận 409 đọc có phục hồi quan sát trong browser. Lưu dưới tải: 0 lỗi trong các lượt hợp lệ và giá trị cuối đã đối chiếu.
- Query count trong các phiên browser: đường đọc thường 12 SQL (13 ở lượt ghi dấu phiên), lưu 22 SQL (23 ở lượt ghi dấu phiên). Chưa phân tích EXPLAIN từng truy vấn; không tự thêm index hoặc đổi cấu hình.
- Fingerprint JS và các service đọc/ghi trực tiếp không đổi. Trong lúc đo có tác vụ khác sửa optimization.py ở nhánh protocol 2 (14:49:44); CRM_OPT_READ tắt và Gunicorn kiểm thử không autoreload. Phép đo này không đánh giá nhánh protocol 2 mới đó; giữ nguyên thay đổi của tác vụ khác.

## Kết thúc

Đã dừng app và PostgreSQL kiểm thử trên local và VPS; giữ volume test và log để tái lập. ERP/CRM production vẫn chạy image da6e2c0, checkout VPS 3e5b9a4, domain CRM HTTP 200. Không đổi code hoặc cấu hình production.
