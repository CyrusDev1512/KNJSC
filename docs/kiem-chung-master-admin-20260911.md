# Vận đơn mới — sửa Admin, nhập trong ô và chạy bền 11.09.2026

## Phạm vi và mốc mã

- Nhánh `vandonmoi`, mốc trước sửa `7449e73`.
- Sửa nguồn danh sách chọn, lỗi draft dang dở, click rê nhẹ và trình nhập
  nằm trong ô. Không đổi quyền, H7, dữ liệu thật, schema hoặc dependency.
- Mọi lần ghi thử dùng database test; không dùng khách mẫu hoặc đơn thật.
- Chạy bền tiếp phần hôm trước trên snapshot bất biến `7449e73`, được tách
  khỏi mã đang sửa để số đo không thay phiên bản giữa lượt. Vì vậy số đo
  chạy bền không phải bằng chứng 30 phút của trình nhập inline mới.

## Nguyên nhân và kiểm hồi quy

API dùng bộ tra danh sách chỉ theo bảng/cột, bỏ qua danh sách trực tiếp của
cột Vận đơn mới; trả `null` cho dropdown. Frontend tạo draft trước khi lặp
qua danh sách, phát sinh `c.options is not iterable` rồi để lại draft không
có input. Lần bấm sau bị chặn ở bước kết thúc draft. Một đường lỗi khác là
rê hơn 5px trong cùng ô bị coi là kéo vùng và không mở sửa.

Hồi quy trước sửa đã đỏ với rê 7px, hình học khung nổi và nguồn options.
Sau sửa, kiểm nguồn chọn trùng dịch vụ ghi, lưu trạng thái hợp lệ; lỗi
metadata mô phỏng không tạo draft ma hoặc chặn ô khác. Không quy lỗi cho PC.

| Nhóm | Kết quả ngày 11.09 |
|---|---|
| Backend liên quan | 1.041 passed, 2 failed, 7 skipped, 103,31s |
| Truy vết tài liệu, chạy riêng | 10 passed, 3 failed; cả ba lỗi cũng tái hiện trên snapshot trước sửa |
| Nhóm master grid riêng | 19 passed |
| Kiểm bổ sung nguồn options | 1 passed sau cùng; metadata của bộ cột chuẩn không thêm SQL |
| JavaScript | 6 script đạt: working copy, geometry, autosave, queue, conflict, scope |
| End-to-end | Đạt Admin tạo → Leader giao → Staff sửa/tự lưu → Sale đọc lịch sử; thu quyền, CAS, mất phản hồi, Undo/Redo |
| Hồi quy Admin | Đạt click thường/rê nhẹ, trạng thái/ngày có lưu thật, Tab, dán TSV giữ số 0 đầu; F2/bấm đúp 120ms ở Xem; metadata lỗi không chặn ô khác |
| UI | Đạt hình học inline, cột ghim, 1440/1280/390px, CSS zoom 125%; hồi quy chiều cao hàng/cache/polling/phím/cảm ứng mô phỏng |

Hai lỗi suite rộng ở `core/tests/test_giao_dien.py` đối với
`crm/statistics.html`: bộ rà CSS báo các lớp `exec-*` chưa khai; bộ rà nhãn
báo bảy input/select thiếu nhãn phù hợp với quy tắc kiểm. Chạy lại chính hai
bài trên snapshot `7449e73` cũng thất bại (2 failed/566 deselected).
Đây là tồn tại trước sửa lưới; chưa sửa màn Thống kê trong tác vụ này.
Không gọi toàn suite là xanh. Bảy skip là fixture trình duyệt/kiểm tải/
dung lượng cần bật riêng; E2E và chạy bền được thực thi riêng như bên dưới.

Nhóm `tests/test_truy_vet.py` chạy riêng: 10 đạt/3 lỗi, trên snapshot cũng
10 đạt/3 lỗi. Bộ phân tích không nhận các tiêu chí AC-22.4/7/9 và số lượng
trong docs/06 lệch số bộ phân tích đọc được. Đây là nợ đồng bộ tài liệu/bài
kiểm đã tồn tại, chưa sửa trong phạm vi lưới lần này.

Lệnh suite từ gốc repo:

```powershell
docker compose -f deploy/docker-compose.yml run --rm -e RUN_MIGRATIONS=0 -e POSTGRES_DB=knjsc_admin_unit_0911 web pytest crm/tests orders/tests forms_builder/tests core/tests -ra
```

Chrome dùng `test_master_browser_server.py`, cổng test 8035; chạy
`scripts/kiem-thu-master-admin-click.cjs` và `scripts/kiem-thu-master-nine-ui.cjs`.
Phép đo ngắn bật `MASTER_INLINE_PERF=1`. Cần Playwright/Chrome đã có sẵn,
không cài dependency. Marker/sự kiện trong fixture không phải dữ liệu thật.

## Đo trình nhập inline mới

100 mẫu trên một dòng lọc trong fixture 1.300 dòng, giữ phản hồi request
lưu để xác nhận vẫn nhập được. Đơn vị ms, percentile nearest rank:

| Phép đo | p50 | p95 | p99 |
|---|---:|---:|---:|
| Pointerup thật → hai frame | 30,20 | 30,90 | 31,10 |
| Input event → hai frame | 24,00 | 29,50 | 29,90 |
| Toàn chuỗi Playwright click + insertText + hai frame | 96 | 98 | 112 |

Lần đo đầu toàn chuỗi có p95 112ms; lần đo có thêm mốc sự kiện là số ở
bảng. Không dùng khác biệt hai lượt để tuyên bố tối ưu tốc độ. Playwright
có thời gian chờ thao tác; mốc sự kiện là thước đo phản hồi trình duyệt.
Không gọi đây là INP, gõ IME Việt thực tế hoặc đo trên 300.000 dòng.

## Chạy bền snapshot 7449e73

Đã chạy đủ: 08:21:07–08:52:07, 60s warmup + khoảng 1.800s đo;
300.000 dòng/20 người, 3 gunicorn worker ×4 thread. Host i5-12400/12 logical
CPU; Docker 29.7.2, 12 CPU/7,63GiB RAM, PostgreSQL dùng cấu hình kết nối test
`max_parallel_workers_per_gather=0`. Không sửa cấu hình PostgreSQL toàn máy.

22.460 request trong cửa sổ đo, 12,48 request/s; 16 lỗi đọc = **0,0712%**.
135 xung đột CAS được ghi riêng (bộ đếm này có thể gồm warmup), không tính
thêm lần nữa vào số request. Không có lỗi request ghi; harness không phát
hiện sai giá trị trả về hoặc trùng/không giới hạn dòng trong khối. Kiểm này
không phải đối soát toàn database hoặc bằng chứng tuyệt đối không mất dữ liệu.

| HTTP | Số mẫu | p50 / p95 / p99 (ms) | Lỗi |
|---|---:|---|---:|
| Đọc khối | 9.534 | 175,83 / 645,07 / 861,11 | 11 |
| Đọc dòng chuẩn bị sửa | 3.877 | 83,61 / 281,67 / 429,26 | 5 |
| Lưu ô, gồm CAS 409 hợp lệ | 3.873 | 49,81 / 118,36 / 232,30 | 0 |
| Polling | 3.301 | 195,79 / 367,36 / 493,75 | 0 |
| Lọc Quốc gia | 1.875 | 893,48 / 1.353,64 / 1.617,38 | 0 |

Lọc Quốc gia **chưa đạt p95 ≤1s**. 16 lỗi là RemoteDisconnected/
ConnectionResetError, rải trong lượt đo, không chỉ lúc tắt server; chưa chốt
nguyên nhân kết nối. Log gunicorn không có worker restart/timeout/traceback
trong lượt. Không loại lỗi khỏi báo cáo vì harness cho phép tỷ lệ dưới 5%.
Hoàn tất thời lượng và exit 0 không đồng nghĩa đạt mọi điều kiện nghiệm thu.

Chrome riêng hoàn tất **1.800,377s/31 mẫu**. Heap sau GC 2,59–3,37MiB,
cuối 2,83MiB; 350–460 ô, cache tối đa 2 trong lượt có polling thường xuyên.
DOM counter 1.738–12.704 node, có dao động nhưng không tăng mãi theo số dòng
đã cuộn trong mẫu đo. Bài cuộn ngắn riêng đạt cache 10, heap ba vòng khoảng
7,41–7,49 triệu byte; không dùng cache thấp của lượt polling thay bài LRU.

Resource monitor 61 mẫu, khoảng 31s/lượt:

| Container | CPU p50 / p95 / max | RAM đầu / cuối / max (MiB) |
|---|---|---|
| Server test + Locust | 41,36% / 73,97% / 85,75% | 394,3 / 415,1 / 415,1 |
| PostgreSQL dùng chung | 226,68% / 427,51% / 568,73% | 812,5 / 867,2 / 925,2 |

CPU Docker có thể vượt 100% do nhiều lõi. Container test giữ toàn bộ mẫu
Locust trong RAM; mức tăng này không tách riêng RSS worker ứng dụng. Cùng
máy còn tác vụ khác và hồi quy trên DB test riêng, nên đây không phải
benchmark phần cứng độc quyền. Không kết luận rò bộ nhớ server từ tổng RAM
container; cũng không kết luận đã loại trừ mọi rò bộ nhớ.

## Phép đo ngắn bản inline trên 300.000 dòng

Đã hoàn tất lượt 20 người/90s (30s warmup) và Chrome 100 mẫu trên snapshot
có bốn file runtime đã sửa; hash lưu trong `master-inline-capacity-20260911/code.json`.
Runtime snapshot khớp hash bốn file hiện tại. 683 request trong cửa sổ đo,
11,46 request/s, **2 lỗi ConnectionResetError khi đọc khối (0,293%)**,
1 CAS hợp lệ ghi riêng, không có lỗi request ghi hoặc integrity error của
harness. Log toàn lượt còn một lỗi đọc đích trong warmup, không trộn vào 683.

| HTTP bản inline | Mẫu | p50 / p95 / p99 (ms) |
|---|---:|---|
| Đọc khối | 288 | 502,13 / 1.278,14 / 1.557,52 |
| Đọc đích ghi | 121 | 217,34 / 551,76 / 674,68 |
| Lưu ô | 121 | 49,08 / 185,17 / 365,51 |
| Lọc Quốc gia | 50 | 1.005,48 / 1.853,80 / 2.252,26 |
| Polling | 103 | 290,59 / 764,79 / 1.002,36 |

Lượt ngắn trước sửa cùng 300k/20 người/90s có 739 request, 0 lỗi,
đọc/lưu/lọc p95 694,36/120,53/1.535,53ms. Lượt sau chậm hơn ở đọc;
**chưa đạt ngưỡng đọc/lọc**, chưa tách được đóng góp của code, trạng thái
cache database và tải nền trên máy dùng chung. Không tuyên bố không có hồi
quy hiệu năng. Kiểm riêng resolver mới trên bộ cột chuẩn xác nhận thêm 0 SQL;
điều đó không thay cho phép đo cô lập toàn API. Chưa chạy lại ma trận dài.

Chrome mới trên 300k, mỗi thao tác 100 mẫu:

| Thao tác | p50 / p95 / p99 (ms) |
|---|---|
| Chọn | 32,30 / 32,60 / 44,00 |
| Mở/nhập khi phản hồi lưu đang bị giữ | 31 / 31 / 38 |
| Vùng đọc | 29,80 / 30,50 / 31,30 |
| Kéo cột | 49,00 / 49,50 / 50,70 |
| Kéo hàng | 49,10 / 49,30 / 57,10 |

Chọn/vùng đọc dùng sự kiện tổng hợp tới hai frame; mở/nhập dùng Playwright,
kéo dùng pointer thật; không phải phép đo native IME. Ba vòng cuộn: cache
10, 350 ô/4.794 DOM node; heap sau GC 7.498.112 → 7.504.720 → 7.504.960 byte.
Phản hồi UI đạt mục tiêu trong bài đo này; **không suy ra toàn hệ thống đạt**.

## Bằng chứng và giới hạn

- `.agents/design-state/review/master-admin-20260911/`: kết quả click,
  ảnh lỗi trước sửa và ảnh inline ở các kích thước.
- `.agents/design-state/review/master-nine/ui-result.json`: E2E hiện tại.
- `.agents/design-state/review/master-endurance-20260911/`: HTTP thô,
  Chrome, resource và log của lượt chạy bền.
- Lịch sử/biên nhận không đổi cấu trúc trong lần sửa này; số đo dung lượng
  hôm trước giữ tại [báo cáo chín hạng mục](kiem-chung-master-nine.md),
không trình bày như số đo mới.
- Chưa kiểm phiên trình duyệt ban đầu của người dùng, IME thật và native
  Chrome zoom 125%; CSS zoom/cảm ứng mô phỏng không thay bằng chứng đó.
- Chưa chạy lại toàn ma trận 100k/300k ×10/20 trước/sau cho inline.
- Chưa có profile truy vấn chậm hoặc chẩn đoán TCP riêng cho các lỗi đọc
  của lượt này; cần đo cô lập trước khi chốt cách tối ưu tiếp theo.
- Không commit/push; giữ thay đổi ngoài tác vụ.
- Cuối phiên có thêm thay đổi CRM/ERP từ phần việc khác. Suite rộng/E2E ở
  trên phản ánh trạng thái khi chạy khoảng 08:29–08:33; không phải chứng nhận
  tích hợp cho mọi thay đổi song song xuất hiện sau đó. Bốn file runtime của
  sửa lưới được kiểm hash với snapshot riêng, không thay giữa lượt đo.
- Diff mã thuộc tác vụ: `.agents/design-state/review/master-admin-20260911/implementation.patch`;
  không gồm mã CRM/ERP sửa song song. Tài liệu và bằng chứng ở các đường trên.
