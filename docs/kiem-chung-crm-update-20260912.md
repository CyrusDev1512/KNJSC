# Kiểm chứng CRM-UPDATE — 12.09.2026

**Mốc bàn giao 14.09:** đã hoàn tất kiểm chứng trong phạm vi CRM-UPDATE.
Bốn lượt tải bản sau 100k/300k × 10/20 đã đạt sau sửa truy vấn phạm vi;
Chrome tải lớn đủ bốn cấu hình, lưu 2.000 ô, Celery và bài bền 30 phút đạt.
Giữ riêng bốn lỗi kiểm thử nền và 11 skip; không tuyên bố toàn hệ thống xanh.
Các mục tạm dừng ngày 12.09 bên dưới là lịch sử, được thay thế bởi mốc này.
Checkout chính vẫn ở nhánh fix; chưa kích hoạt CRM-UPDATE, commit hoặc push.

### Bài bền và kiểm cuối 14.09

19 Locust + 1 Chrome, cùng worker nhập/xuất nền; 60 giây làm nóng và đủ
**1800 giây đo**, 31.985 mẫu HTTP, không lỗi. Oracle đối chiếu 2.859 dòng,
gồm 2.840 dòng mới, đúng người tạo, ID, giá trị và công thức. Số dòng mới gồm
cả warmup/drain; số mẫu HTTP chỉ tính cửa sổ đo. Tập nền ban đầu 300k/bảng,
có thêm dữ liệu từ bài bulk và các lượt tạo/nhập trong bài bền.

| Nhóm | Đọc p95 ms | Lọc p95 ms | Lưu p95 ms | Lịch sử p95 ms |
|---|---:|---:|---:|---:|
| Marketing | 234,79 | 169,98 | 131,81 | 79,41 |
| Sale | 304,48 | 200,12 | 126,08 | 78,58 |
| Vận đơn cũ | 314,27 | 363,72 | 310,66 | 88,37 |

Tạo dòng p95 117–141 ms; sửa đầu vào công thức p95 108–117 ms.
31 job nhập × 100 dòng và 31 job xuất × 11.111 dòng đều DONE, đối chiếu
Excel theo ID và số điện thoại dạng chuỗi. `endurance-gate.json` đạt.

Chrome: 587 mẫu, p95 43,62 ms, cache tối đa 4 khối, tối đa 405 ô/808 DOM.
Heap đầu/cuối 3,02/3,03 MiB, cực đại lấy mẫu 9,49 MiB; các khoảng 5 phút
đều có giảm trở lại, chưa thấy xu hướng tăng liên tục trong 30 phút.
Không suy ra không rò nhớ ở mọi thời lượng. Có 522 phản hồi đổi phiên bản;
ghi 667 phản hồi 200 phục hồi (nhiều request/khối có thể cùng phục hồi một
thay đổi), không lỗi ngoài giao thức. Lưới vẫn có thể tải lại vùng khi người
khác ghi; kết quả này không chứng minh mọi thao tác nhiều người đều liền mạch.

Docker stats trong cửa sổ đo (257 mẫu/container; 100% CPU = một logical core):

| Container test | CPU trung bình | CPU cao nhất lấy mẫu | RAM cao nhất MiB |
|---|---:|---:|---:|
| App | 55,23% | 148,26% | 277,50 |
| PostgreSQL | 251,61% | 620,69% | 3110,91 |
| Worker | 3,75% | 101,50% | 176,60 |
| Redis | 0,45% | 0,79% | 5,39 |

Hai URLconf `knjsc.urls`/`knjsc.urls_bangtinh` check không lỗi;
`makemigrations --check --dry-run`: No changes detected (`resume-startup.log`).
Các cờ READ/SYNC/RECEIPTS/RENDER/STATS giữ tắt trong lượt tải chính.
Không thêm migration/dependency của chiến dịch; migration chứng từ đã có
trong snapshot nền không được tính thành thay đổi mới này.

Lệnh và cấu hình chạy lại: [harness](../scripts/crm-update-perf/README.md).
Diff riêng so với 773 file snapshot: `storage/crm-update/campaign.diff`;
danh sách file, trạng thái và hash: `campaign-files.json`. Bốn lỗi nền:
hai bài điều hướng `test_dich_vu_bangtinh` và hai bài CSS/nhãn thống kê
`core/tests/test_giao_dien.py`. Ba lỗi khác trong lượt suite đầu đã được
phân loại/sửa harness, 21 bài liên quan chạy lại đạt; không sửa log lần đầu.
IME hệ điều hành/trackpad thật chưa kiểm, 11 skip không tự coi là đạt.

Dọn dẹp: đã dừng sampler, gỡ bốn container và network test; database tmpfs
đã được gỡ. Bốn manifest đã bỏ session/CSRF test; muốn chạy lại phải seed
database test mới. Bộ duyệt tự động chặn xóa đệ quy 14 Chrome profile và
thư mục upload/export test (`blocked by policy`, không nêu lý do chi tiết).
Các thư mục trong `cleanup-directories.json` còn giữ; không báo dọn sạch.
Snapshot, diff, ảnh và số đo giữ nguyên; không tác động storage/database local.

### Kết quả đo lại 14.09

Mỗi lượt dưới đây có 60 giây làm nóng và 300 giây đo, không lỗi HTTP/oracle.
100k/300k là số dòng **mỗi bảng**, gồm ba bảng Marketing/Sale/Vận đơn.

| Dòng/bảng × người | Mẫu | p95 đọc MKT/Sale/VĐ (ms) | p95 lưu MKT/Sale/VĐ (ms) |
|---|---:|---|---|
| 100k × 10 | 2828 | 91,64 / 88,13 / 111,95 | 80,90 / 79,60 / 80,62 |
| 100k × 20 | 5635 | 89,26 / 84,84 / 106,41 | 74,14 / 76,76 / 87,80 |
| 300k × 10 | 2735 | 162,81 / 143,69 / 218,48 | 87,44 / 85,01 / 172,59 |
| 300k × 20 | 5397 | 186,20 / 169,34 / 261,50 | 105,50 / 104,36 / 170,68 |

`matrix-gate.json` kiểm đủ thời gian, khoảng trống mẫu, các nhóm đọc/lọc/lưu/
lịch sử và oracle. p50/p95/p99, throughput, SQL và bytes ở `load-summary.json`
và `load-summary.md`; tài nguyên ở `resources-continued.jsonl`/`resource-summary.json`.
Baseline cùng đợt đủ bốn lượt; bản sau ban đầu không đạt độ trễ được giữ riêng
trong `rejected-scope-20260914`, không dùng làm kết quả cuối.

Chrome trên 300k có 100 mẫu mỗi thao tác/mỗi cấu hình; p95 chọn/cuộn/nhập (ms):
1440: 24,30/36,11/21,44; 1280: 25,89/33,42/20,26;
390: 23,82/22,60/22,35; zoom thật 125%: 25,66/28,16/21,13.
Không lỗi JS, cache tối đa 10 khối, sai lệch cột ghim 0 px.
Đây là thao tác automation tới animation frame, không phải số đo INP/FPS.
Baseline mobile bị cột ghim chặn nhập; không suy ra tỷ lệ tăng tốc mobile.

Lưu 2.000 ô/400 dòng: 30 lượt, p95 624,92 ms; kiểm 12.000 dòng, ID/người tạo,
Decimal và số 0 đầu. Lượt này có fixture Chrome riêng chạy đồng thời, không
dùng để so sánh trước/sau. Celery thật: nhập 100 dòng và xuất 11.111 dòng;
đối chiếu Excel với tập ID đã xuất và số điện thoại dạng chuỗi.
Chuẩn hóa timestamp synthetic chỉ thực hiện sau các phép so sánh; parallel
VACUUM gặp giới hạn `/dev/shm` của container test, chuyển bảo trì sang
`VACUUM (ANALYZE, PARALLEL 0)`. Không đổi cấu hình truy vấn ứng dụng.

Chrome Vận đơn mới chạy lại sau dọn handler cũ: 1 passed (52,87 giây),
copy qua khối, đổi chiều cao hàng, phân công, Staff autosave, lịch sử,
mất phản hồi/replay và CAS đều đạt; bằng chứng `payment-resume/`.

Bài bền đầu ngày 14.09 dừng trước làm nóng vì harness coi cảnh báo HTTP 409
đổi phiên bản là lỗi JavaScript. Giữ lượt bị loại tại
`endurance-rejected-protocol-20260914`. Harness sau chỉ chấp nhận đúng JSON
đổi phiên bản từ GET `/bang-tinh/van_don/du-lieu/` có tham số version;
ghi riêng từng phản hồi và kiểm GET 200 phục hồi. Các 409 khác, 4xx/5xx,
pageerror và lỗi mạng vẫn làm thất bại. Không đổi code ứng dụng để bỏ cảnh báo.
Không tính thời gian của lượt dừng vào bài 30 phút chạy lại.


Trạng thái lúc 17:28 ngày 12.09.2026: chủ dự án yêu cầu chuyển local sang
`fix/trung-ma-don-dong-thoi` để thử chế độ xem. CRM-UPDATE giữ ở worktree riêng;
kiểm tải tạm dừng, chưa nghiệm thu toàn chiến dịch. Mốc bật CRM-UPDATE 17:20
bên dưới là lịch sử, không còn là bản đang phục vụ ở 8020/8021.

Feedback khi test: cột ghim nền sáng/chữ trắng. Nguyên nhân đã xác nhận:
gỡ bang-tinh.css làm mất token màu giấy dùng chung cho .mg-viewport/.mg-float.
Chrome regression `kiem-thu-grid-contrast.cjs` tái hiện tỷ lệ tương phản
1,05:1 và 1,16:1 ở theme tối; đã sửa và kiểm lại ngày 14.09, xem mục tiếp tục.
Chế độ xem toàn bảng của nhánh fix chưa tích hợp vào bản này.

## Mốc và phạm vi diff

Nhánh `CRM-UPDATE` ở worktree `C:/KNJSC/worktrees/CRM-UPDATE`, từ `95988c9`
của `codex/chung-tu-thanh-toan` cộng toàn bộ thay đổi chưa commit. Manifest
`storage/crm-update/manifest.json` ghi SHA256 773 file, 40 đường dẫn dirty.
Snapshot và diff nền ở `C:/KNJSC/worktrees/CRM-UPDATE/storage/crm-update`.
Checkout chính hiện ở nhánh fix. So sánh với snapshot này,
không coi diff với HEAD là toàn bộ thay đổi của CRM-UPDATE.

**Quyết định thay thế ngày 12.09, theo yêu cầu “chuyển sang nhánh đó để tôi
test trước”:** checkout chính và dịch vụ 8020/8021 đã chuyển sang bản này.
Đối chiếu đủ 773 file của checkout chính với snapshot trước khi chuyển; sao
lưu riêng `activation-before`, đưa 95 file chiến dịch sang và giữ 714 file
không thuộc diff. Nhánh cũ và toàn bộ thay đổi nền được bảo toàn.

Khởi động lại web/CRM/worker/beat cùng code; web dùng override ngoài Git
`storage/crm-update/local-no-seed.yml` đặt RUN_MIGRATIONS=0. Không commit/push,
không seed/migrate hoặc đổi dữ liệu. Hai URLconf `check` đạt; `migrate --check`
không báo migration thiếu. Đọc trong transaction READ ONLY xác nhận Marketing
(30 dòng) và Sale (28 dòng) trả HTTP 200, dùng master-grid và API JSON 200.
File JS phục vụ qua HTTP có SHA256 khớp code mới. Login 8020/8021 đều 200.
Phần chọn phạm vi xem Vận đơn ở worktree nhánh fix vẫn giữ riêng, chưa ghép.

## Tiếp tục ngày 14.09.2026

- Làm tiếp trong worktree `CRM-UPDATE`; checkout sử dụng local vẫn ở nhánh fix.
- Tái hiện lỗi chữ trắng trên cột ghim ở theme tối: contrast 1,05/1,16.
  Khôi phục các token màu giấy từ CSS lưới cũ vào `.mg-viewport, .mg-float`;
  Chrome kiểm sau sửa đạt 12,43/11,27 cho ô/tiêu đề ghim, cả hai theme.
- Chrome chức năng chạy lại: 1440/1280/390 px và zoom thật 125% đều đạt,
  không pageerror. Các nhóm shared_grid/shared_integrity/table_lifecycle đạt.
- PostgreSQL test dùng tmpfs đã mất dữ liệu khi Docker tắt. Lưu bằng chứng
  tải cũ vào `storage/crm-update/archive-20260912`; dựng lại hai database test
  100k/300k. Phải đo lại trước/sau cùng đợt, không ghép số cũ thành so sánh mới.
- Ma trận tải và bài bền tiếp tục trong ngày; kết quả bàn giao thay thế ở đầu tài liệu.

### Điểm nghẽn phát hiện trong lượt đo lại

Bốn lượt baseline đủ 300 giây, không lỗi. Bản trước sửa truy vấn đạt 100k
nhưng ở 300k/20: p95 đọc Marketing/Sale/Vận đơn là 1172/1350/1299 ms;
lưu 830/883/898 ms. Không lỗi HTTP và đối chiếu dữ liệu đạt, nhưng **không đạt
độ trễ**, nên chưa chạy bài bền. Bằng chứng giữ tại
`storage/crm-update/rejected-scope-20260914`, không ghi đè bằng lượt đạt sau này.

EXPLAIN ANALYZE chỉ đọc xác nhận COUNT/mốc cập nhật trên bảng đã biết vẫn
mang truy vấn con ID và nhánh JOIN Order/WaybillAssignment của Vận đơn mới.
`DataRecordQuerySet.in_scope` nay ghép trực tiếp hai queryset phạm vi hiện có
cho bảng xác định không phải Vận đơn mới. Truy vấn toàn hệ thống/Vận đơn mới
giữ đường cũ; điều kiện dùng chung vẫn ở SQL, không cấp quyền từ object cũ.
Không migration, index, cache hoặc bật cờ tối ưu. Test rút gọn SQL đỏ ba ca
trước sửa, xanh sau sửa; kiểm tương đương với đường tổng quát qua các cấp
bậc, Grant người/team, shared, tombstone, bảng tắt/xóa và metadata cũ.

Suite mở rộng ban đầu: 1194 passed, 7 failed, 11 skipped. Trong bảy lỗi có
bốn lỗi nền đã ghi ngày 12.09; hai bài thiếu mount `/docs` và một assertion
báo cáo bắt nhầm `700` trong URL cache CSS. Bổ sung mount và kiểm số liệu/nội
dung báo cáo thay vì thuộc tính HTML; 21 bài liên quan đã đạt. Giữ log gốc,
không ghi lại lần đầu thành xanh. Ma trận mới sau sửa đã đạt, xem mốc bàn giao.

## Kết quả đã ghi nhận

- Baseline trên snapshot: 1.129 passed, 4 failed, 10 skipped. Bốn lỗi là hai
  kiểm markup điều hướng và hai kiểm CSS/nhãn của `crm/statistics.html`.
- TDD ban đầu tái hiện thiếu API lưới chung/xóa bảng/tạo dòng nháp. Hồi quy
  riêng đã qua CAS, kiểu dữ liệu, công thức đồng thời, 2.000 ô tạo theo lô,
  replay, phụ thuộc biểu mẫu/job và khóa shared/exclusive. Suite cuối rộng:
  **1.130 passed, 4 lỗi nền không đổi, 11 skipped** trong 122,88 giây
  (`final-suite3.log`). Sau đó sửa một điều kiện replay/schema; nhóm cuối gồm
  lưới chung, tính nguyên tử, vòng đời và replay: **37 passed** (`receipt-green.log`).
- Chrome: 1440/1280/390 px và zoom thật 125% qua Settings của Chrome.
  `devicePixelRatio=1.25`, CSS zoom=1, visualViewport.scale=1 tại lượt zoom.
  Tạo dòng, Undo/Redo cùng ID, clipboard số 0 đầu, công thức, Escape, xóa bảng
  trên Manager → tab Staff dừng hiển thị → khôi phục đã qua. Không có `pageerror`.
  `shared-browser-final-server.log`: 1 passed; `shared-browser-result.json`: bốn case.
- IME chỉ mô phỏng composition, chưa kiểm bộ gõ hệ điều hành/trackpad thực.
- Chrome tái hiện rồi kiểm xanh hai ca biên bổ sung: bảng rỗng lưu dòng đầu
  nhưng chưa nạp lại khối 0; popup lọc vẫn chứa dữ liệu khi bảng bị xóa.
  Bản sửa nạp lại khối đầu và dọn popup/chặn HTMX trả muộn sau khi mất bảng.
- Chrome còn tái hiện ô datetime có múi giờ và lựa chọn gợi ý hiện trống khi
  mở sửa. Giữ chuỗi datetime và input/datalist cho lựa chọn không chặt; select
  chỉ dành cho danh sách chặt. Bản cuối có `fieldCompatibility=true`, giữ và
  lưu được giá trị tự do. Không đổi quy tắc kiểm dữ liệu ở server.
- TDD tái hiện biên nhận tạo dòng đã commit bị từ chối sau khi thêm cột.
  Replay nay trả biên nhận cũ sau kiểm quyền hiện hành; chỉ lượt ghi mới cần
  khớp schema hiện tại. Kiểm ID không tạo bản sao (`receipt-red/green.log`).
- Hồi quy Vận đơn mới trên 10.000 dòng: Bill/chứng từ, copy qua ranh giới khối,
  kéo hàng, phân công qua popup, Staff autosave/lịch sử, retry cùng UUID khi
  mất phản hồi và đối chiếu CAS đều đạt. `payment-server.log`: 1 passed.
- Lên đơn Sale/Admin nhiều sản phẩm, ba lựa chọn bắt buộc, đơn vị và đơn gốc
  bất biến qua Chrome 1440/390: `order-server.log` 1 passed; `order-result.json`.
- Khởi động cả hai URLconf không lỗi; `makemigrations --check --dry-run`
  báo No changes detected. Sáu script unit JS đều đạt (`node-final.log`).
- Các bài browser/capacity bị skip trong suite thường được liệt kê riêng;
  các luồng Chrome nêu trên chạy bằng launcher và DB riêng. Không coi cả
  11 skip là đã được thay thế hay đã đạt.
- Một lượt baseline thử nghiệm bị ngắt request lúc Locust kết thúc. Giữ file
  thô đó, không dùng để kết luận đạt; harness cuối có drain và cửa sổ đo rõ ràng.

## Lịch sử ngày 12.09 — tạm dừng để chủ dự án test local

Baseline đủ bốn tổ hợp 100k/300k ×10/20, mỗi lượt 300 giây, không lỗi.
Bản cuối mới hoàn tất 100k/10: 2.722 mẫu, không lỗi HTTP/oracle; p95 đọc
Marketing/Sale/Vận đơn lần lượt 137,77/155,20/171,90 ms; lưu 86,11/81,85/108,25 ms.
Lượt 100k/20 bị chủ động dừng khi chuyển môi trường cho chủ dự án test;
không tính là đạt. Bằng chứng `interrupted-for-manual-100000-20*` được giữ.
Ba lượt còn lại, ghi 2.000 ô qua HTTP, Chrome tải lớn bản sau, nhập/xuất nền
và bài bền 30 phút **chưa hoàn tất**. Bộ lấy mẫu và app kiểm tải đã dừng;
database test riêng giữ để tiếp tục, không chạy tải trên 8020/8021.

Dùng PostgreSQL/container riêng `knjsc-crm-update-*`, không mở cổng DB. Mỗi cỡ
có ba bảng 100.000 hoặc 300.000 dòng/bảng, 20 tài khoản mỗi bộ phận, dữ liệu
synthetic: text dài, ngày, số điện thoại, số lượng, tiền, cột tính CPO.
Schema đo gồm 8–9 cột; không đại diện mọi độ rộng/schema bảng thực tế.
Timestamp synthetic của dữ liệu nền tăng theo ID, có thể ở tương lai; cột Ngày
nghiệp vụ cố định. Giữ cùng snapshot cho so sánh HTTP. Không dùng phép đo này
để kết luận phát hiện thay đổi bằng polling; polling được kiểm riêng trong
fixture Chrome có thời gian bình thường.

Ba worker Gunicorn × bốn thread; các cờ tối ưu tắt trong lượt chính. Đo tuần tự,
không chạy functional cùng lúc. Ghi SQL/request bằng middleware hiện có,
Locust và Docker stats. Máy local có nhiều dịch vụ khác đang bật; không suy
ra năng lực VPS từ số đo này. Không sử dụng dữ liệu/mật khẩu người thật.

Lệnh chính:

```powershell
scripts/crm-update-perf/matrix.ps1 -Stage before
scripts/crm-update-perf/matrix.ps1 -Stage after
```

Mỗi lượt warmup 60 giây, lấy mẫu 300 giây, có thời gian kết thúc request.
Cần kiểm đủ thời gian, số mẫu/gap, p50/p95/p99, throughput, lỗi, SQL/CPU/RAM.
Bài bền 300k/20/30 phút chỉ chạy sau khi ma trận đạt.

Đo Chrome before/after riêng trên 300k, không chạy đồng thời với Locust/suite.
Gunicorn dùng wrapper StaticFilesHandler chỉ cho phép đo Chrome, phục vụ static
của đúng snapshot. Một lần thử thiếu static đã loại khỏi kết quả. Bản nền
1440/1280/zoom 125% có 100 mẫu cho chọn/cuộn/nhập; ở 390px cột ghim che ô Ghi
chú nên không lấy được mẫu nhập. Giữ thất bại đó, không ép click xuyên lớp ghim.
Đây là hạn chế baseline; bản sau vẫn phải qua kiểm mobile bình thường.

## Thay thế kiểm thử và code cũ

Các assertion yêu cầu `<td>`/HTMX hoặc thanh định dạng mở rộng được thay bằng
JSON/CAS, bảo toàn các kiểm tra dữ liệu, công thức, quyền và nhập/xuất.
Hai endpoint xóa/khôi phục dòng cũ nay kiểm bị từ chối; Undo dòng mới có bài riêng.
Ngân sách lô nhập bổ sung số truy vấn cố định cho khóa/kiểm vòng đời, không
phình theo số dòng. Không tăng ngân sách để chấp nhận N+1.

Danh sách file gỡ và diff riêng đã xuất khi kiểm cuối. Bảng trắng và duplicate
cấu trúc tiếp tục hoãn. Chỉ đánh dấu phần CRM-UPDATE đã được kiểm chứng;
không đóng các yêu cầu hiệu năng hoặc nghiệp vụ còn lại.
