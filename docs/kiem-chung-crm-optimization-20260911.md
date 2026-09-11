# CRM-Optimization — nhật ký kiểm chứng 11.09.2026

**Đã triển khai trong checkout riêng và kiểm local; chưa nghiệm thu toàn bộ
mục tiêu hiệu năng/phát hành.** Cờ mặc định tắt, không commit/push/VPS.

## Baseline

- HEAD nguồn: `3c3fd09df63dd56b8eb7583391a6a976dba5406a` + thay đổi chưa commit.
- Snapshot bất biến: `C:/KNJSC/CRM-Optimization-baseline`; manifest SHA256 từng
  file trong `snapshot-manifest.json`. Manifest 700 mục, trong đó 698 file
  được sao chép và hai mục tài khoản mẫu/env example bị loại; bốn file đã xóa
  được ghi riêng. Không sao chép DB, upload hay khách hàng thật.
- Evidence local: `.agents/design-state/review/optimization/` (gitignore).
  Phiên đăng nhập fixture chỉ ở `.test-runtime/` (gitignore), không bàn giao
  manifest có session cho Git. `git diff` với HEAD có cả thay đổi nền; phải
  đối chiếu snapshot để tách diff riêng tác vụ tối ưu.
- Docker local báo 12 CPU, 8.192.139.264 byte RAM. Không phải VPS 24 GB.
- Hai bản dùng Django 5.2.6, psycopg 3.2.3, Gunicorn 23.0.0, Celery 5.4.0,
  redis-py 5.2.1, openpyxl 3.1.5 theo image đang kiểm; Locust 2.41.5.
- Fixture: bốn DB test riêng (trước/sau × 100k/300k), có đơn vị sản phẩm,
  phân công và vai trò. Mỗi DB có thêm 300k mục lịch sử và 300k biên nhận cũ.
  Gunicorn và Locust khác container; không tính RAM Locust thành RAM server.

## Đã kiểm

| Kiểm tra | Kết quả |
|---|---|
| Suite nền crm/orders/forms_builder/core | 1.076 passed, 4 failed, 8 skipped |
| RED giao thức v2 trên mã cũ | Thất bại đúng: thiếu `protocol` |
| Hồi quy tối ưu ban đầu | 10 passed: count cache, rollback, gom giao dịch, replay gọn, tắt cờ vẫn replay, sync, thu quyền, Redis lỗi, thống kê TTL/refresh, Excel tương đương |
| JS working copy/queue/conflict/geometry | Đạt sau cập nhật fixture unit có config giao thức |
| Baseline chẩn đoán 100k/10, keep-alive 2s | 2.488 request tổng; 3 RemoteDisconnected; không sai ID/thứ tự/giá trị theo oracle |
| Suite cuối tại thời điểm chốt backend | 1.092 passed, 4 lỗi nền, 9 skipped; `final-functional.log` |
| Hồi quy tập trung trước suite cuối | 71 passed; migration xuôi/ngược, commit đảo thứ tự, journal 10k/2k, cursor, CAS/replay, Redis lỗi |
| Xuất Excel | Bản thường/write-only và trực tiếp/nền giữ cùng nội dung; thu phân công chặn tải file đã tạo |
| Production candidate | Compose `config --no-env-resolution --quiet` hợp lệ; Nginx `-t` hợp lệ với hostname/chứng chỉ test |
| Cache Thống kê đồng thời, bổ sung cuối | 1 passed: hai request cùng key chỉ dùng một lần tính khi lease còn hiệu lực, đối tượng trả về độc lập |
| Redis thực sự mất kết nối | `ConnectionError` ở Redis loopback cổng 1 trong process test riêng; đường đọc v2 vẫn trả đúng ID/thứ tự/tổng từ PostgreSQL |
| Đồng bộ model/migration cuối | `makemigrations --check --dry-run`: `No changes detected` |

Migration `0005_assignment_journal_columns` sửa tên cột trong hàm journal bằng
migration bổ sung, không sửa phiên bản cũ hoặc dữ liệu lịch sử. Đã có bài RED
trước sửa. Hai hồi quy JS bổ sung chặn khối trả về trước mốc sync và polling
đến muộn khi đã bắt đầu lưu; kiểm trình duyệt bản cuối được ghi riêng.

## Ma trận trước/sau đã hoàn thành

Mỗi tổ hợp warmup 60 giây, đo 300 giây. Gunicorn 3 worker × 4 thread,
keep-alive 5 giây, qua Nginx đóng kết nối upstream sau phản hồi. Hai bản dùng
cùng cấu hình này để không trộn lợi ích cấu hình kết nối vào lợi ích mã v2.

| Dòng / người | Mẫu sau warmup | Khối p95 ms | Lọc p95 ms | Lưu p95 ms | Poll p95 ms | Thống kê p95 ms | Lỗi ngoài dự kiến |
|---|---:|---:|---:|---:|---:|---:|---:|
| 100k / 10 | 1.842 | 167 | 237 | 94 | 89 | 331 | 0 |
| 100k / 20 | 3.669 | 180 | 250 | 98 | 93 | 364 | 0 |
| 300k / 10 | 1.690 | 541 | 667 | 94 | 300 | 1.285 | 0 |
| 300k / 20 | 3.386 | 608 | 672 | 97 | 305 | 1.322 | 0 |

Bản tối ưu, cùng thứ tự cột và đơn vị:

| Dòng / người | Mẫu sau warmup | Khối p95 ms | Lọc p95 ms | Lưu p95 ms | Poll p95 ms | Thống kê p95 ms | Lỗi ngoài dự kiến |
|---|---:|---:|---:|---:|---:|---:|---:|
| 100k / 10 | 1.858 | 127 | 177 | 66 | 68 | 334 | 0 |
| 100k / 20 | 3.685 | 136 | 203 | 93 | 71 | 377 | 0 |
| 300k / 10 | 1.806 | 242 | 141 | 104 | 71 | 1.047 | 0 |
| 300k / 20 | 3.637 | 255 | 280 | 108 | 81 | 1.222 | 0 |

Ở 300k/20: khối giảm khoảng **58%**, lọc **58%**, polling **73%**.
Lưu một ô tăng từ 97 lên 108 ms (khoảng 11%), vẫn dưới 500 ms; cần tính
chi phí journal/đồng thời, không tuyên bố mọi đường ghi đều nhanh hơn.
Không thêm index mới nên đây không phải bài chấp nhận index theo ngưỡng 10%.
Trang lịch sử p95 khoảng 42–55 ms. Thống kê tính mới ở 300k còn vượt mục tiêu
1 giây; cache không chữa chi phí lần tính đầu cho mỗi phạm vi người xem.

Tám lượt ngắn không ghi nhận sai oracle hoặc lỗi mạng/5xx ngoài dự kiến.
Tình huống CAS cùng ô được phân loại riêng. Workload ngắn nhảy offset ngẫu
nhiên; không lấy cải thiện trên đây làm số đo riêng của cursor.

Số đo p50/p95/p99, payload và RPS đầy đủ được tổng hợp từ raw JSON bằng
`scripts/bao-cao-optimization.cjs`, không suy từ mục tiêu. Sai ID/thứ tự/tổng
hoặc giá trị xác nhận dừng ngay lượt đo; CAS hợp lệ được tách riêng.

## Chrome: baseline và bản cuối

Mỗi thao tác 100 mẫu, Chrome headless, gọi riêng Gunicorn và không chạy đồng
thời ma trận HTTP. Các số dưới đây là p95 millisecond, gồm chờ khung hình.

| Bản / dòng | Chọn | Nhập khi đang lưu | Kéo cột | Kéo hàng | Render khi cuộn | Long task khi cuộn |
|---|---:|---:|---:|---:|---:|---:|
| Nền / 100k | 31 | 32 | 19 | 18 | 22,1 | 0 |
| Tối ưu cuối / 100k | 31 | 31 | 24 | 20 | 26,4 | 5 |
| Nền / 300k | 31 | 32 | 19 | 17 | 20,7 | 1 |
| Tối ưu cuối / 300k | 31 | 31 | 26 | 18 | 21,3 | 0 |

Cột ghim lệch 0 CSS px trong 120 mẫu cuộn tiến/lùi kết hợp dọc. Kiểm
1440/1280/390 và **CSS zoom 125%**, không gọi là zoom trình duyệt thật.
Cache tối đa 10 khối, DOM tối đa 698 node trong phép thử; heap sau GC tăng
khi nạp cache rồi ổn định khoảng 7 MiB qua hai vòng 12 khối. Điều này không
thay thế phép thử rò bộ nhớ kéo dài. Renderer chưa cho lợi ích ổn định ở
300k; giữ cờ mặc định tắt và không tuyên bố nhanh hơn chỉ vì dưới 100 ms.

Ảnh/video/JSON baseline ở `.../optimization/browser/`, bản cuối ở
`.../optimization/browser-final/`, đều bị gitignore. Bộ kiểm UI riêng
`pinned-20260911/ui.json` đạt bấm đúp 120 ms, nhập inline, clipboard,
Undo, kéo hàng/cột, đổi thứ tự/ẩn cột và mất cache. IME/cảm ứng mô phỏng
không thay thế bộ gõ hoặc thiết bị thật.

E2E cuối tại `optimization/e2e/ui-result.json` đạt: Sale lên đơn → Leader
phân công → Staff sửa/tự lưu → Sale xem lịch sử; 403 thu quyền nguyên tử,
409 đối chiếu/gửi lại, mất phản hồi rồi replay, sửa tiếp khi request đang
chạy, định dạng/Undo/Redo và clipboard. Đây là luồng **Sale đứng đơn theo
snapshot mới**, không phải thêm lại bộ chọn Sale cho Admin. Script cũ thất
bại vì tìm bộ chọn đã bị bỏ trước tác vụ; ảnh thất bại được giữ riêng.
Một nhãn trong raw E2E còn chữ Admin; thao tác thực dùng actor Sale.

Một lượt Chrome cuối thử ghi lại đúng giá trị cũ không phát request và làm
harness chờ sai. Đã sửa harness luân phiên hai giá trị, chạy lại thành công;
giữ `attempt-noop-value.json` và video lần thất bại, không tính lần đó là đạt.

## SQL, biên nhận và dung lượng

`optimization_measure.py` chạy từ container đo riêng, gọi Gunicorn trực tiếp,
không chạy đồng thời benchmark HTTP/Chrome. Mỗi câu EXPLAIN có ba lần
`ANALYZE, BUFFERS`: trang ID đầu khoảng 0,1 ms, giữa 150k khoảng 17–18 ms,
cuối 299.900 khoảng 34–35 ms; cursor cuối khoảng dưới 1 ms. Các lọc Quốc gia,
ngày, giao hàng, thanh toán, sản phẩm, Marketing, phân công và tìm kiếm
được lưu đủ plan. Đây là **truy vấn lấy ID với cache nóng**, không phải thời
gian toàn endpoint/COUNT. Chưa có bằng chứng cần thêm index đạt điều kiện
ba lượt ≥20%; giữ index hiện có.

Các số dưới là HTTP wall time qua Gunicorn, không tính debounce và không
gọi là thời gian server thuần. PostgreSQL đo riêng bằng kích thước quan hệ
và `pg_column_size`; dữ liệu dài ~5.000 ký tự lặp nên nén tốt, không phải
trường hợp dung lượng xấu nhất.

| Lượt kiểm | Số thao tác / ô đổi | p95 trước → sau (ms) | JSON biên nhận trước → sau (byte, tổng lượt) |
|---|---:|---:|---:|
| Sửa ngắn | 100 / 100 | 42,22 → 25,57 | 106.224 → 46.540 |
| Sửa dài | 100 / 100 | 30,92 → 37,99 | 139.842 → 71.247 |
| Định dạng | 100 / 100 | 33,21 → 30,66 | 143.493 → 60.697 |
| Dán 2.000 ô | 20 / 40.000 | 1.928,37 → 1.744,66 | 4.052.670 → 361.808 |

Biên nhận của 20 lần dán giảm khoảng **91% JSON**. Lịch sử vẫn ghi đủ
40.000 thay đổi, không cắt lịch sử để đạt con số này. Mỗi lượt đều kiểm số
ô xác nhận, số mục lịch sử và số biên nhận; request replay không ghi trùng.

Lịch sử ở PostgreSQL **`crm_gridcellhistory`** (trước/sau từng ô/thuộc tính);
biên nhận chống gửi trùng ở **`crm_gridmutationreceipt`**. Hai cấu trúc khác
nhau với **`crm_gridchange`/`crm_gridrevision`** chỉ chứa metadata đồng bộ.
Bản nháp/xung đột trên trình duyệt nằm trong RAM, mất khi kết thúc phiên;
không phải dữ liệu đã lưu ở PostgreSQL hoặc localStorage.

Kích thước quan hệ sau bộ đo dung lượng của bản tối ưu (byte):

| Quan hệ | Dữ liệu + TOAST | Chỉ mục | Tổng |
|---|---:|---:|---:|
| Lịch sử | 41.672.704 | 36.265.984 | 77.938.688 |
| Biên nhận | 351.887.360 | 27.336.704 | 379.224.064 |
| Journal | 778.240 | 155.648 | 933.888 |
| Revision | 16.384 | 16.384 | 32.768 |

Tổng biên nhận vẫn lớn vì fixture có **300.000 biên nhận v1 cả dòng** từ
đầu. Không chuyển đổi/xóa chúng. Các lượt load đã thêm mục mới trước khi đo;
không gọi số hàng cuối bảng này là đúng 300.000.

| Lượt đo bản tối ưu | Tăng vật lý lịch sử (byte) | Tăng vật lý biên nhận (byte) | WAL toàn cluster (byte) |
|---|---:|---:|---:|
| 100 sửa ngắn | 16.384 | 8.192 | 2.491.784 |
| 100 sửa dài | 49.152 | 114.688 | 1.717.424 |
| 100 định dạng | 40.960 | 24.576 | 2.681.752 |
| 20 lần dán 2.000 ô | 9.125.888 | 417.792 | 214.465.248 |

Tăng vật lý có thể sử dụng lại trang trống, không chia 8 KB/100 để kết luận
mỗi biên nhận chỉ tốn 82 byte. WAL là số chênh LSN **toàn cluster**, có thể
kèm autovacuum/hoạt động DB khác; WAL không bằng dung lượng lịch sử lưu lâu.
Raw giữ cả số trước/sau và chỉ mục, không chỉ tổng dung lượng database.

Ước tính kế hoạch một năm: giả sử 100.000 khách, mỗi lần sửa một ô tạo một
history và một receipt; **tạm dự trù 1–2 KB tổng/ô** gồm dữ liệu và chỉ mục
cho phần lớn nội dung ngắn, chưa gồm file xuất/backup/WAL. Đây là giả định
lập ngân sách từ bậc dung lượng đo, không phải trần đã chứng minh:

| Số lần sửa mỗi khách/năm | Mục lịch sử mới | Dự trù tăng |
|---|---:|---:|
| 10 | 1 triệu | 1–2 GB |
| 20 | 2 triệu | 2–4 GB |
| 50 | 5 triệu | 5–10 GB |

Một lần dán 2.000 ô chỉ có một receipt nhưng có thể 2.000 history; nhiều
nội dung dài ít nén sẽ vượt giả định trên. Không đồng nhất 100.000 khách
với 100.000 history. Đề xuất theo dõi hàng tuần kích thước dữ liệu/index,
số receipt/history mỗi thao tác, autovacuum và dung lượng backup; đo lại
với phân bố nội dung thực đã ẩn danh trước chốt ổ đĩa. Chưa tự xóa hoặc
đưa lịch sử/biên nhận sang lưu trữ lạnh.

## Lợi ích, chi phí và cờ phát hành

| Nhóm | Kết quả local | Quyết định |
|---|---|---|
| READ + SYNC | Khối/lọc/poll cải thiện, scope/token/rollback đạt hồi quy | Có thể thử có kiểm soát sau migrate test tương ứng; mặc định vẫn tắt |
| RECEIPTS | JSON nhỏ hơn, CAS/replay/history đạt; ghi đơn có lúc chậm hơn | Giữ v1 tương thích, theo dõi write/WAL khi bật |
| RENDER | Sticky đúng, cache/DOM giới hạn; render chưa cải thiện ổn định | **Giữ tắt**, chưa công nhận lợi ích hiệu năng |
| STATS | TTL/refresh/snapshot/quyền đạt; cold compute 300k vẫn >1 giây | Giữ mục tối ưu cold query trong backlog |
| EXPORT/QUEUES | Peak RAM worker 300k/20 từ ~612 xuống ~181 MiB | Theo dõi thời gian có file và backlog, không coi HTTP queue nhanh là xuất xong |
| Production | Cấu hình + HTTPS/request ID qua proxy test hợp lệ | Chỉ là ứng viên, chưa triển khai VPS |

Peak RAM app các lượt ngắn khoảng 246–260 MiB. PostgreSQL CPU p95 lượt
300k/20 giảm khoảng 374% → 163% trong mẫu đo, nhưng dùng container chung
và có nhiễu worker: không suy toàn bộ giảm này do một thay đổi. **100% CPU
ở Docker tương ứng khoảng một core**, không phải 100% của 12 core.
Locust tách container và số liệu RAM, không cộng vào Gunicorn.

## Chạy bền bản cuối

Chạy từ khoảng **15:00:27 đến 15:31:27 ngày 11.09**, 300k/20 người,
cấu hình 60 giây warmup + 30 phút đo. Raw ghi phần đo **1.799,26 giây**
(sai lệch dưới một giây so với thời lượng cấu hình do mốc khởi động/dừng
Locust); không làm tròn số raw thành chính xác 1.800 giây.

- **21.828 request sau warmup**, 12,13 request/giây; **0 lỗi ngoài dự kiến**,
  **0 lỗi oracle**; 7 xung đột CAS hợp lệ được tách riêng, không tính hai lần.
- Một Admin thử ghi/định dạng 2.000 ô mỗi 120 giây trong vùng các Staff cũng
  sửa. **Cả 7 lượt dán giá trị bị 409**; không có mẫu dán giá trị thành công
  trong bài bền này. Không dùng tốc độ trả 409 làm tốc độ ghi 2.000 ô.
- Bảy lượt định dạng 2.000 ô thành công, p95 HTTP 2.423,88 ms, server
  2.418,09 ms. Số mẫu ít, p95 gần giá trị lớn nhất; ghi rõ n=7.

| Thao tác | Mẫu thành công | HTTP p50 / p95 / p99 (ms) | Server p95 (ms) |
|---|---:|---:|---:|
| Đọc khối | 7.650 | 83 / 255 / 339 | 249 |
| Lọc | 1.526 | 72 / 266 / 438 | 261 |
| Lưu một ô | 3.052 | 48 / 106 / 161 | 102 |
| Polling | 3.055 | 45 / 76 / 115 | 71 |
| Lịch sử | 1.518 | 29 / 56 / 92 | 49 |
| Thống kê | 1.504 | 626 / 1.166 / 1.311 | 1.162 |

Đã ghép toàn bộ các mẫu trên với log Django bằng request ID. Riêng yêu cầu
xuất đi qua redirect sang trang job nên HTTP bao gồm nhiều response; không
lấy thời gian của trang cuối làm toàn thời gian xếp job ở server.
Thống kê còn vượt 1 giây; các endpoint lưới chính đạt ngưỡng trong lượt này.

269 mẫu tài nguyên: CPU p95 app 58,26%, worker 95,13%, PostgreSQL 184,46%
(100% ≈ một core). Peak RAM tương ứng app **361,4 MiB**, worker **176,8 MiB**,
PostgreSQL dùng chung **1.870,8 MiB**; Locust **105,6 MiB**, ghi riêng.
RAM app đầu/giữa/cuối: **312,1 / 343,2 / 355,6 MiB**. Có tăng khoảng 43,5
MiB; chưa phân biệt hết allocator/cache với rò rỉ nên **không kết luận RSS
server ổn định hoàn toàn**. Heap trình duyệt là phép đo khác.

186 mẫu DB, tối đa 15 connection gồm app/worker/fixture, hai mẫu chờ khóa
transaction; có mẫu chờ I/O/WAL ghi riêng trong JSON. Không lỗi lấy mẫu.

**Xuất nền chưa theo kịp tải:** ở lần tổng kết 15:31:57, riêng job tạo từ
đầu bài bền có 112 done, 71 pending và 1 running. Đối với job đã xong:
thời gian thực thi p95 **17,97 giây**, thời gian từ yêu cầu tới file p95
**704,83 giây (~11 phút 45 giây)**. Job chưa xong không được loại đi để gọi
toàn bộ xuất là nhanh; pending lớn nhất trong telemetry là 72. Worker làm
việc gần một core liên tục. Việc giới hạn consumer giữ RAM thấp nhưng chưa
đủ năng lực cho tần suất xuất liên tiếp này. Không tự tăng worker/gộp yêu cầu
hoặc thay luồng UI để che backlog.

Phép đo bổ sung `bulk-disjoint-final` dùng 2.000 dòng cuối không trùng đích
sửa đơn ô, 20 người vẫn hoạt động: warmup 10 giây, cấu hình đo 5 phút
(raw 299,44 giây). **3.843 request**, không lỗi ngoài dự kiến/oracle;
**15 lượt dán 2.000 ô thành công** với p95 HTTP **2.130,31 ms**, server
**2.120,94 ms**, p95 DB **802,89 ms**. Lưu một ô p95 HTTP **107,22 ms**;
có một CAS đơn ô hợp lệ được tách riêng. Số mẫu dán n=15, không gọi là
100 mẫu. Không thay thế hoặc sửa lại bảy 409 của bài bền. Dữ liệu vẫn ở
DB test; không đổi CAS. Lượt này còn backlog export từ bài bền nên không
gọi là phép đo cách ly hoàn toàn.

Smoke trước đó phát hiện proxy kiểm thử giới hạn mặc định 1 MB khiến lượt
2.000 ô trả 413. Đã đồng bộ proxy test thành 11 MB như production candidate,
chạy smoke lại 90 giây không còn lỗi, ghi/định dạng khoảng 1,6–2 giây.
Giữ cả raw smoke lỗi; không tăng timeout/retry để che lỗi. Tám lượt ngắn
dùng cấu hình proxy cũ, đều có payload dưới 1 MB; bài bền dùng cấu hình mới.

Telemetry mỗi 10 giây ghi connection/wait và số job, tài nguyên Docker đo
riêng; không ghi nội dung job hoặc ô. Worker nặng concurrency 1 nên cần
đối chiếu độ dài hàng đợi với tốc độ yêu cầu xuất; chưa tăng concurrency
ngoài quyết định đã duyệt.
Giới hạn một tác vụ nặng đang chạy **không giới hạn số yêu cầu được xếp
hàng**. Bản này chưa bổ sung gộp yêu cầu xuất hoặc từ chối khi hàng đợi dài.

## Giới hạn của môi trường đo

- Nginx dùng bản Debian 1.26.3 trong container test riêng vì Docker Hub tải
  image thất bại; production candidate vẫn cần kiểm trên image được chốt.
- Worker local mỗi DB một process, concurrency 1, nhận cả hai queue. VPS
  candidate tách một worker nặng và một thường; chưa chứng minh cấu hình đó.
- Load fixture có Admin/Leader Vận đơn/Staff Vận đơn/Sale, phạm vi toàn bảng
  hoặc phần được giao. Phân công sinh theo vòng, chưa mô phỏng riêng team
  lệch tải nặng hoặc thêm Manager/CSKH/Marketing thành nhóm phát tải độc lập.
  Kiểm quyền chức năng không thay thế phép đo dung lượng cho các nhóm này.
- Các lượt mixed nối tiếp có thể còn export chờ từ lượt trước. Ví dụ worker
  100k/20 còn chạy trong khoảng 76 giây đầu phần đo 300k/10 ở bản nền.
  Không gọi từng lượt là hoàn toàn cách ly tác vụ nền. Tài nguyên PostgreSQL
  là container chung; không coi toàn RAM/CPU của nó là riêng một endpoint.
- Mẫu tài nguyên báo `No such container: crm-opt-load` tại ranh giới tạo/xóa
  container là mẫu thiếu của bộ đo, không phải lỗi HTTP của ứng dụng.
- Chẩn đoán keep-alive 5 giây có 2.436 request tổng, không tái hiện lỗi;
  chưa đủ để quy toàn bộ 16 lỗi lịch sử không có request ID về cùng nguyên nhân.

Bốn lỗi nền: hai bài `crm/tests/test_dich_vu_bangtinh.py` (điều hướng
CRM/ERP), hai bài `core/tests/test_giao_dien.py` (CSS exec-* và label trên
statistics.html). Giữ riêng, không quy thành lỗi mới hoặc tự sửa ngoài phạm vi.
Lượt 100k/10 trên dùng chẩn đoán: có bài pytest chạy cạnh trong một phần thời
gian, chưa đủ tài nguyên mẫu, **không dùng làm baseline nghiệm thu trước/sau**.

## Chưa đạt / chưa kiểm chứng

- Chưa đủ bằng chứng quy nguyên nhân **toàn bộ 16 lỗi lịch sử** về keep-alive;
  request ID bổ sung giúp điều tra nếu tái phát. Tám lượt ngắn mới không lỗi.
- Bốn lỗi suite nền và 9 skip không được đánh dấu đạt; không sửa UI ngoài phạm vi.
- Native IME/cảm ứng và zoom trình duyệt thật 125% chưa kiểm; đã kiểm mô phỏng/CSS zoom.
- Render chưa có lợi ích ổn định; cold Thống kê chưa đạt 1 giây ở 300k.
- Dán giá trị 2.000 ô trong bài bền đều xung đột; lượt bổ sung vùng không
  tranh chấp đạt p95 server 2,12s, ghi riêng. Hàng đợi xuất tăng và RAM app
  còn cần phân tích thêm trước chốt năng lực vận hành lâu dài.
- Cấu hình production chỉ là ứng viên chưa triển khai hoặc đo VPS.

Lệnh chính (tại checkout tối ưu):

```powershell
docker compose -p knjsc -f deploy/docker-compose.yml run --rm -e RUN_MIGRATIONS=0 -e POSTGRES_DB=knjsc_opt_green web pytest crm/tests/test_optimization.py
node scripts/kiem-thu-master-working-copy.cjs
node scripts/kiem-thu-master-queue-unit.cjs
node scripts/bao-cao-optimization.cjs
node scripts/bao-cao-optimization-server.cjs
node scripts/bao-cao-optimization-server.cjs bulk-disjoint-final
node scripts/bao-cao-optimization-final.cjs
node scripts/diff-optimization.cjs
```

Không đánh dấu feedback `-> đã làm` cho các hạng mục chưa nghiệm thu.

## Trạng thái bàn giao

- Nhánh **`CRM-Optimization`**, checkout **`C:/KNJSC/CRM-Optimization`**;
  chưa commit/push, mọi cờ tối ưu mặc định tắt. Không thay runtime localhost
  đang dùng của chủ dự án. Checkout gốc vẫn ở nhánh `vandonmoi`.
- Snapshot 698 file nguồn còn nguyên SHA256. Diff riêng của tác vụ được
  sinh lại sau cùng; diff với HEAD còn bao gồm phần nền chưa commit đã
  được chủ dự án yêu cầu giữ lại. Không gọi tất cả diff với HEAD là mã tối ưu.
- Đã dừng các container `crm-opt-*` của bài đo. Fixture tự dọn DB; truy vấn
  `pg_database` xác nhận bốn DB trước/sau và DB test bổ sung `test_knjsc_opt_tail`
  không còn. Không xóa volume hoặc khôi phục/xóa DB nghiệp vụ. Các dịch vụ
  `knjsc-web`, `knjsc-bangtinh`, worker, beat, Redis và PostgreSQL vẫn chạy.
- Bộ giám sát `docker wait` thu được mã 0 của fixture đầu; ba fixture còn
  lại tự xóa container trước khi lệnh wait tuần tự kịp gắn vào. Đây là giới
  hạn thu log teardown; việc DB test đã dọn được kiểm bằng truy vấn riêng.
- **Không kết luận đạt toàn bộ**: cold Thống kê, hiệu quả renderer, backlog
  export, tăng RSS app, native IME/zoom/thiết bị, phân bố team lệch tải và
  năng lực VPS vẫn có giới hạn/việc còn nợ đã ghi bên trên.

Số tổng hợp p50/p95/p99, tài nguyên, browser và dung lượng có thể theo Git:
[JSON tổng hợp](verification/crm-optimization-20260911.json),
[manifest baseline](verification/crm-optimization-baseline.json).
Video/raw HTTP/log và `optimization-only.diff` chỉ ở evidence local
bị gitignore; chúng không tự đi theo lần push sau này. Không có session,
mật khẩu hoặc dữ liệu khách thật trong các file tổng hợp này.

Điểm mở evidence local (không hoạt động trên GitHub nếu chưa bàn giao file riêng):

- [Diff riêng so với snapshot](../.agents/design-state/review/optimization/optimization-only.diff).
- [Video nền 300k](../.agents/design-state/review/optimization/browser/page@8860c8d38f4c7f14b7c0b57ddc8f4867.webm).
- [Video bản cuối 300k](../.agents/design-state/review/optimization/browser-final/page@72bb5502d7c59c00e1a943dac5f686ac.webm).
- [Ảnh desktop](../.agents/design-state/review/optimization/browser-final/after-300000-1440-1.png)
  và [mobile 390](../.agents/design-state/review/optimization/browser-final/after-300000-390-1.png).
- [Kết quả E2E](../.agents/design-state/review/optimization/e2e/ui-result.json).
- [Suite cuối](../.agents/design-state/review/optimization/final-functional.log).
