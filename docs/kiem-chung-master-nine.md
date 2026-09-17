# Kiểm chứng chín hạng mục Vận đơn mới — 10.09.2026

**Bổ sung 11.09:** đã chạy lại đủ 30 phút trên snapshot `7449e73`, còn lỗi
kết nối đọc và mục tiêu lọc chưa đạt. Bản inline mới đo ngắn riêng; xem
[kết quả 11.09](kiem-chung-master-admin-20260911.md). Phần dưới giữ số đo
và trạng thái lịch sử của ngày 10.09.

Trạng thái: đã triển khai và kiểm chức năng chín hạng mục; chưa đạt toàn
bộ mục tiêu hiệu năng (lọc 300k). Chạy kéo dài dừng theo yêu cầu chủ dự án;
để phiên sau chạy lại đủ 30 phút, không đánh dấu đã đạt.
Nhánh `codex/sua-feedback`; chủ dự án đã yêu cầu commit/push khi tạm dừng. Snapshot baseline là workspace
trước sửa, gồm cả thay đổi chưa commit, không phải HEAD cũ.

## Môi trường và giới hạn

Mọi ghi thử dùng PostgreSQL test riêng. Chrome headless trên Windows;
server UI cổng 8035, capacity cổng 8036, không dùng database ở 8021 để thử ghi.
Docker PostgreSQL 16, Gunicorn 3 worker/4 thread; cùng máy có các dịch vụ dev
đang chạy. Một phần baseline trùng thời gian chạy test chức năng/dung lượng:
phải coi là nhiễu, không suy ra mức tăng tốc chính xác từ chênh lệch đơn lẻ.
Ma trận ngắn cuối đã hoàn tất trước lượt E2E cuối. Riêng chạy kéo dài có
E2E/90 test chức năng dùng DB test khác chạy chung máy khoảng 18:07–18:09
để rút thời gian chờ theo phản hồi chủ dự án; tài nguyên PostgreSQL có thể
chịu nhiễu ở cửa sổ này. Không trình bày đây là môi trường độc chiếm.
Windows có 12 luồng CPU và khoảng 15,75 GiB RAM; Docker được thấy 12 CPU và
khoảng 7,63 GiB RAM. Kết nối DB của bài tải giới hạn parallel query về 0
do `/dev/shm` hiện có; thiết lập giống nhau trước/sau, không ALTER SYSTEM.

IME thực tế trên bộ gõ Windows chưa được kiểm bằng thao tác người thật;
sự kiện composition mô phỏng chỉ là một phần hồi quy.

## Truy vết

- `app/crm/tests/test_master_nine.py`: thứ tự, Admin/Sale, quyền, lịch sử,
  style, CAS, replay, cursor, migration và giới hạn truy vấn.
- `scripts/kiem-thu-master-autosave-unit.cjs`: phản hồi cũ không mất nháp mới,
  value/style độc lập và Undo/Redo.
- `scripts/kiem-thu-master-nine-ui.cjs`: UI và E2E nhiều vai trò trên DB test.
- `app/crm/tests/test_master_nine_capacity.py` và
  `scripts/kiem-thu-master-nine-capacity.cjs`: HTTP và Chrome lớn riêng.
- `app/crm/tests/test_master_nine_storage.py`: PostgreSQL history/receipt,
  thao tác 1 ô/2.000 ô và lịch sử 300.000 mục.

Artifact cục bộ: `.agents/design-state/review/master-nine/` và
`.agents/design-state/review/master-nine-capacity/`. Manifest session test là
tệp tạm; không đưa chúng vào bàn giao hoặc commit.

## Kết quả chức năng

- Red: bốn hồi quy đầu thất bại đúng thiếu lịch sử/style/thứ tự/conflict.
- Red: Admin chọn Sale vẫn lỗi chưa gán phòng ban.
- Red hiệu năng: 25 dòng dùng 99 truy vấn; bỏ kiểm/tải lại từng dòng sau
  kiểm scope/khóa lô, giữ service kiểm kiểu/tính cột và transaction.
- Nhóm liên quan sau sửa: 60 passed. Bộ rộng cuối sau tối ưu truy vấn/chỉ mục:
  **1.049 passed, 6 skipped**, 87,87 giây. Sáu skip là các fixture trình duyệt/kiểm tải phải bật riêng;
  không coi skip là pass. Hai kỳ vọng cũ đã cập nhật theo quyết định Admin
  bắt buộc chọn Sale và từ chối giả mạo seller.
- UI: đã đi qua luồng Admin → cuối bảng → Leader giao → Staff tự lưu → Sale
  xem lịch sử; chọn xanh, chế độ, định dạng/Undo, phản hồi trễ, conflict,
  popup, kéo hàng và các viewport. Mất phản hồi sau commit đã kiểm gửi lại
  cùng UUID/nội dung và nhận replay, không ghi lần hai.
- Dung lượng: đã có artifact `storage.json`, 300.000 lịch sử; số đo sẽ được
  tổng hợp cùng báo cáo hiệu năng cuối, không lấy kích thước mã làm ước lượng.

Không đánh dấu đạt toàn bộ: chạy bền đã dừng theo yêu cầu chủ dự án ngày
10.09.2026, mẫu Chrome cuối ở phút 15. Chỉ giữ mẫu từng phút để chẩn đoán;
chưa có kết quả HTTP đủ 30 phút, cần chạy lại trong phiên sau.

Lượt cuối khoảng 18:07–18:09: 90 test tác động đạt, fixture UI và 16 nhóm
kiểm Chrome đạt. Bao gồm các bổ sung cuối về Sale/phòng ban, 2.000 ô lỗi
ở cuối và thu quyền giữa lượt dán. Các ảnh đã xem lại: chọn hàng xanh,
desktop/mobile và lịch sử có trước/sau/nút đóng. Zoom trong script dùng
CSS 1,25, không phải thao tác đổi zoom native của Chrome.

Trước push, xuất chính index CRM sang snapshot riêng (không mang code ERP
chưa commit) và kiểm lại nhóm master/Orders/Lên đơn/giao diện core/luồng
ba bộ phận: **660 passed, 24,52s**. Đây là kiểm nội dung đóng gói, không
chạy lại kiểm tải hoặc thay thế các bằng chứng UI ở trên.

Bằng chứng gọn có thể đi cùng repository:
[số đo](kiem-thu/master-nine-2026-09-10/performance.md),
[JSON](kiem-thu/master-nine-2026-09-10/summary.json),
[E2E](kiem-thu/master-nine-2026-09-10/ui-result.json),
[chọn hàng](kiem-thu/master-nine-2026-09-10/row-selected.png),
[lịch sử](kiem-thu/master-nine-2026-09-10/history.png),
[mobile](kiem-thu/master-nine-2026-09-10/grid-390.png).

Rà đường 403 và polling phát hiện có thể bỏ nháp còn quyền hoặc tự gửi
phần còn lại sau khi một dòng mất quyền. Hồi quy controller thật đỏ rồi
xanh: giữ nháp hợp lệ, nhả trạng thái lượt cũ, hủy timer đã lên lịch và
chờ Thử lại. Không chuyển lỗi quyền thành lưu một phần. Bài E2E thu quyền
giữa lượt dán hai hàng đã đạt ở lượt Chrome cuối: server rollback cả lượt,
gỡ dòng bị thu quyền, còn đúng một nháp; chờ hơn 2s không tự gửi một phần;
Thử lại dùng UUID mới và chỉ lưu dòng còn quyền.

Ma trận ngắn sau tối ưu đã kết thúc, mỗi lượt 60s làm nóng + 300s đo:

| Dòng / người | Đọc khối p95 | Lọc Quốc gia p95 | Lưu ô p95 | Lỗi / request |
|---|---:|---:|---:|---:|
| 100k / 10 | 164ms | 387ms | 86ms | 0 / 2.052 |
| 100k / 20 | 167ms | 365ms | 97ms | 2 / 4.094 |
| 300k / 10 | 540ms | 1.135ms | 106ms | 2 / 1.918 |
| 300k / 20 | 664ms | 1.340ms | 124ms | 2 / 3.751 |

Đọc khối/lưu đạt mục tiêu của bốn lượt; lọc 300k **chưa đạt** 1 giây.
Không diễn giải harness chạy xong thành nghiệm thu toàn bộ. Lỗi kết nối
được giữ trong mẫu; cần đối chiếu log, không loại chúng để báo tỷ lệ 0%.
Độ trễ Chrome sau sửa (100 mẫu/thao tác): p95 chọn ~32ms, nhập trong lúc
chờ phản hồi lưu ~31ms, đọc ~30–31ms, kéo hàng/cột ~49ms. Ba vòng cuộn
qua 12 vị trí mỗi vòng giữ cache 10, 350 ô và 4.794 DOM node; heap sau GC
khoảng 7,45–7,48 MB. Mẫu chạy dài chưa đủ thời lượng để kết luận nghiệm thu.

## Đối chiếu chín hạng mục

| # | Kết quả triển khai | Bằng chứng chức năng |
|---|---|---|
| 1 | Autosave, tiếp tục nhập khi đang lưu, giữ nháp mới hơn phản hồi | Unit working copy/queue; E2E trì hoãn phản hồi, mất phản hồi sau commit |
| 2 | Số hàng và vùng hàng được tô khi chọn | E2E và ảnh Chrome |
| 3 | Viền/nền chọn xanh dương, không thay style đã lưu | E2E; test lớp cột cố định |
| 4 | Mặc định Xem; Chỉnh sửa bấm/chuyển ô mở nhập | E2E mode/Tab; F2 và bấm đúp 120ms |
| 5 | Cỡ chữ, màu chữ/nền; CAS riêng thuộc tính; Undo/Redo | Unit/backend style + E2E định dạng/Undo/Redo |
| 6 | Lịch sử dòng/ô, 50 mục/trang; đối chiếu conflict trong RAM | Backend scope/cursor/replay; E2E lịch sử/conflict/thu quyền |
| 7 | Admin chọn Sale; creator giữ Admin, seller và đơn vị theo Sale | Backend cho phép/từ chối/rollback; E2E nhiều vai trò |
| 8 | Riêng bảng mới mặc định created_at ASC, ID ASC | Backend + E2E Admin tạo đơn ở cuối |
| 9 | Dòng đầu là 1, địa chỉ vùng chọn thống nhất | E2E; ARIA tính thêm hàng tiêu đề nên chỉ số ARIA khác số hiển thị |

Lịch sử/chọn mode/định dạng chỉ thay `van_don_moi`. Cột bảo vệ, phân công,
chi tiết sản phẩm và H7 giữ hợp đồng hiện có. Lịch sử chỉ gồm thay đổi qua
API lưới mới, không suy dựng dữ liệu trước migration.

## Lệnh và kiểm chứng chức năng

```powershell
docker compose -f deploy/docker-compose.yml run --rm -e RUN_MIGRATIONS=0 -e POSTGRES_DB=knjsc_nine_verify web pytest crm/tests orders/tests forms_builder/tests core/tests tests/test_luong_ba_bo_phan.py -ra
node scripts/kiem-thu-master-working-copy.cjs
node scripts/kiem-thu-master-row-geometry.cjs
node scripts/kiem-thu-master-autosave-unit.cjs
node scripts/kiem-thu-master-queue-unit.cjs
node scripts/kiem-thu-master-frozen-selection.cjs
node scripts/kiem-thu-master-conflict-unit.cjs
```

Node dùng runtime sẵn có trên máy; các script Chrome dùng Playwright sẵn có
qua NODE_PATH, không thêm dependency. Queue unit chạy trực tiếp hàm controller
với đồng hồ/network giả: 499ms chưa gửi, 500ms gửi; nhập liên tục gửi trước 2s;
một request đang chạy; retry 1–2–4–8s giữ nguyên UUID/nội dung; dừng sau bốn
retry và không tự thử lại 400/409. Không dùng sleep thực để kết luận thời gian.

UI dùng `test_master_browser_server.py`, `KN_MASTER_BROWSER=1`, database test
`knjsc_nine_browser`, port 8035, rồi chạy `kiem-thu-master-nine-ui.cjs`.
Hồi quy gồm thu quyền trong lúc nhập (gỡ cả giá trị trong editor), cả hai
cách xử lý dữ liệu đồng thời ở backend, các popup, Ctrl+A vượt giới hạn,
copy/paste số 0 đầu, kéo hàng/cột, localStorage và cuộn xuyên cache.

Rà ảnh cuối phát hiện ô hiện hành có z-index cao hơn cột cố định khi cuộn
ngang. Test `kiem-thu-master-frozen-selection.cjs` đỏ trước sửa, xanh sau
sửa lớp CSS; không đổi kích thước hoặc dữ liệu. Lịch sử và conflict dùng
tên cột/thuộc tính tiếng Việt thay mã kỹ thuật.

Migration `crm.0002_grid_cell_history` đã kiểm xuôi/ngược trên DB test;
đã áp dụng xuôi ở môi trường local. Không chuyển/ghi thử khách hàng thật.
`makemigrations --check --dry-run` không phát hiện migration còn thiếu.
`forms_builder.0010_master_cover_index` cũng đã kiểm xuôi/ngược và áp dụng
local. Chỉ mục thử trên 300.000 dòng khoảng 19,34 MiB; cần tính riêng khi
dự toán dung lượng ngoài hai bảng lịch sử/biên nhận.

Sau suite rộng, thêm kiểm đúng 2.000 ô với lỗi ở ô cuối (sai kiểu hoặc CAS):
cả 1.000 dòng, lịch sử và biên nhận đều không ghi một phần. Kiểm bổ sung Sale
thuộc phòng ban ngừng hoạt động/đã xóa mềm bị từ chối ở lựa chọn và server.
Nhóm cuối 90 test về chín hạng mục/Lên đơn đạt; không dùng số này cộng vào
1.049 để diễn đạt như một lần chạy suite duy nhất.

## Các bước xử lý điểm chậm được đo

1. Bản đầu sau sửa còn đọc khoảng 2–3s ở 300k; lưu bị ảnh hưởng cả bởi
   truy vấn mở bảng của Sale. SQL profile ghi một lần riêng khoảng 1,53s ở
   truy vấn mở bảng; dùng EXISTS giảm việc lấy mọi dòng vào nhánh quyền.
2. Caller biết bảng mới dùng trực tiếp điều kiện mới, không kéo nhánh bảng
   cũ vào JOIN/đếm. Hồi quy đối chiếu tập ID với phạm vi tổng quát cho các vai trò.
3. Chỉ mục master giảm đọc heap khi đếm/phạm vi/thứ tự. Tạo chỉ mục không
   thay quy tắc quyền hoặc công thức; migration riêng có rollback.
4. Lọc bằng khóa JSON thêm containment dùng GIN hiện có và vẫn giữ phép
   bằng cũ để bảo toàn kết quả. Không thêm cột dữ liệu hoặc thư viện.
5. Truy vấn lịch sử chỉ lấy nhãn thao tác từ biên nhận, không tải payload
   hàng nghìn ô lặp lại cho từng mục trên một trang lịch sử.

Có thử chỉ mục riêng Quốc gia trên DB test rồi xóa chỉ mục thử: lợi ích
chưa đủ rõ để triển khai thêm. Lượt smoke sau GIN có đọc khối p95 656ms,
lưu 122ms, lọc Quốc gia 1.320ms; cửa sổ ngắn 60s, chưa thay ma trận chính.
Lượt đo Chrome smoke/probe ban đầu thất bại được giữ riêng; kịch bản đo
reader đã sửa để dùng pointerdown/up trên ô đã tải, có ghi số lần chờ tải.
E2E thao tác chuột thật là bằng chứng riêng, không gọi sự kiện tổng hợp là
đo native input/INP hoặc kiểm bộ gõ thực tế.

## Lịch sử nằm ở đâu và tăng dung lượng ra sao?

- PostgreSQL `crm_gridcellhistory`: mỗi ô/thuộc tính thực sự đổi là một mục,
  lưu trước/sau và liên kết dòng/biên nhận; không chụp toàn bộ dòng ở bảng này.
  Lịch sử chỉ nối thêm qua ORM, không có chính sách tự xóa.
- PostgreSQL `crm_gridmutationreceipt`: một biên nhận cho mỗi lượt gửi, khóa
  duy nhất người dùng + UUID; giữ kết quả trả về để replay không ghi hai lần.
  Hiện kết quả vẫn chứa các dòng đã tác động, vì vậy biên nhận có thể lớn hơn
  riêng lịch sử ô; không được bỏ qua bảng này khi tính dung lượng.
- Bản nháp, Undo/Redo và lựa chọn giải quyết xung đột nằm trong RAM trình
  duyệt của phiên. localStorage chỉ giữ tùy chọn bố cục, không giữ khách hàng.

Số đo PostgreSQL test, byte gồm bảng/TOAST và chỉ mục; các mốc dưới đây
**cộng dồn**, không phải dung lượng riêng của một lần sửa:

| Mốc | Lịch sử: bảng + TOAST | Chỉ mục lịch sử | Biên nhận: bảng + TOAST | Chỉ mục biên nhận |
|---|---:|---:|---:|---:|
| Rỗng | 8.192 | 32.768 | 8.192 | 32.768 |
| 100 sửa ngắn | 49.152 | 65.536 | 172.032 | 65.536 |
| Thêm 100 sửa dài ~960 ký tự | 253.952 | 65.536 | 491.520 | 65.536 |
| Thêm 100 định dạng | 270.336 | 81.920 | 778.240 | 90.112 |
| Thêm 20 lượt ×2.000 ô | 4.505.600 | 3.342.336 | 2.277.376 | 90.112 |
| Bổ sung lịch sử tới 300.000 mục | 45.424.640 | 27.222.016 | 2.277.376 | 90.112 |

Mốc cuối: lịch sử **69,28 MiB**, biên nhận **2,26 MiB/320 lượt**. Phần bổ
sung lịch sử bằng SQL chỉ tạo khối lượng để đo phân trang/dung lượng, không
đại diện 300.000 lượt API. Dữ liệu trước/sau dài và cách PostgreSQL nén
TOAST làm kết quả thay đổi; số đo lô nhỏ còn chịu cấp phát trang.

Độ trễ Django TestClient (không gồm HTTP trên mạng), percentile nearest rank:

| Thao tác | Số mẫu | p50 / p95 / p99, ms |
|---|---:|---|
| Sửa ngắn | 100 | 20,44 / 29,51 / 32,52 |
| Sửa dài | 100 | 19,14 / 24,53 / 34,84 |
| Định dạng | 100 | 21,51 / 27,53 / 33,80 |
| Lưu 2.000 ô | 20 | 817,67 / 1.060,08 / 1.173,57 |
| Trang 50 lịch sử trên 300.000 mục | 100 | 14,09 / 28,56 / 32,15 |

Đây là đo riêng dung lượng/endpoint, không thay kết quả nhiều người đồng
thời. Chưa có baseline lịch sử vì tính năng này chưa tồn tại trước sửa.

Ước tính một năm với **100.000 khách**, giả sử mỗi lần sửa chỉ đổi một ô,
mỗi lần gửi là một request; dùng khoảng 242 byte/mục lịch sử từ dữ liệu
300k và 1.966 byte/biên nhận từ lô sửa ngắn (bao gồm chỉ mục):

| Số lần sửa/khách/năm | Mục lịch sử/lượt gửi | Lịch sử, GB | Biên nhận, GB |
|---|---:|---:|---:|
| 10 | 1.000.000 | 0,24 | 1,97 |
| 50 | 5.000.000 | 1,21 | 9,83 |
| 100 | 10.000.000 | 2,42 | 19,66 |

GB là hệ thập phân. Đây là kịch bản, không phải dự báo chắc chắn hoặc tổng
dung lượng hệ thống: chưa gồm dữ liệu chính, WAL, backup, bloat và dung lượng
dự phòng. Gộp nhiều ô trong một lượt giảm số biên nhận; nội dung dài tăng
dung lượng. 100.000 khách hoặc hai triệu ô đang tồn tại không đồng nghĩa
100.000/hai triệu mục lịch sử.

Đề xuất theo dõi tăng trưởng riêng hai bảng và chỉ mục, độ trễ ghi/đọc lịch
sử; sau khi chốt yêu cầu giữ lại mới cân nhắc biên nhận gọn hơn và chính sách
lưu giữ. Chưa triển khai tự xóa, phân vùng hoặc chuyển lưu trữ lạnh.
