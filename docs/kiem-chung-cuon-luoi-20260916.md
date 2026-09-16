# Cuộn vùng cache và tải trước theo hướng — 16.09.2026

## Bổ sung: gom request khi nhảy xa (local)

Theo yêu cầu tiếp theo, khi một bước cuộn vượt chiều cao viewport, gom vị trí
trong 80 ms yên cuộn rồi lấy khối tại vùng đích đang nhìn. Không trì hoãn vẽ
cache, không tải các vùng trung gian hoặc overscan của lần nhảy. Tải trước
tạm dừng sau nhảy, chỉ trở lại sau hai bước cuộn nhỏ cùng hướng cách nhau
dưới 250 ms. Đổi lọc/mất quyền xóa timer. Không đổi quyền hay endpoint.

Request thuộc viewport cũ được hủy nếu không còn hữu ích; request được
editor/copy/dán dùng chung chuyển quyền sở hữu và không bị hủy theo viewport.
Phản hồi lỗi/thành công đã bị hủy không được thay đổi trạng thái mới. Hủy ở
client không bảo đảm SQL đã chạy trên server sẽ dừng.

So với bản local tối ưu cuộn vừa hoàn tất, cùng API mô phỏng trễ 120 ms:

| Kịch bản | Trước | Sau |
|---|---:|---:|
| Request khi nhảy qua 12 vị trí cách 1.000 dòng, mỗi 25 ms | 48 | 1 |
| Chờ vùng đích sau chuỗi nhảy, desktop | 140,5 ms | 235,1 ms |
| Chờ vùng đích sau chuỗi nhảy, mobile | 138,9 ms | 247,7 ms |
| Nhảy xa về cache, request mới | 0 | 0 |
| Nhảy xa về cache, desktop/mobile sau sửa | — | 28,3 / 30,8 ms |

Đây là **giảm request thừa**, không phải làm lần nhảy đơn lẻ nhanh hơn.
Chấp nhận chi phí gom 80 ms; số chờ bảng trên là một chuỗi/viewport, không
gọi là p95. Không suy ra mức giảm CPU/SQL hoặc tải 10 người từ số request.
Số đo/hash nằm ở `verification/grid-jump-20260916.json`; raw log `jump-*`
trong `storage/grid-scroll/`. Các số ở phần dưới là lịch sử trước bổ sung này.

Hồi quy browser 1440/390: giữ cache, tiếp tục tải đón sau cuộn ổn định,
lọc khi timer còn chờ, nháp, lỗi mạng/403, chiều cao hàng và cờ renderer
tương thích đạt. Unit quyền sở hữu request/hủy request/callback cũ đạt;
Node geometry/queue/autosave/conflict/scope/optimization đạt.
E2E `test_market_currency_browser.py` chạy lại trên `test_grid_jump_browser`:
**1 đạt, 40,56 giây**, hai viewport, lưu đơn/sửa ô thật trên database test.
Không chạy lại toàn suite Python vì không sửa backend; 110 test liên quan
ở đợt trước giữ làm bằng chứng hồi quy nền, không ghi thành lượt chạy mới.
Tái lập: script browser dùng `--jump-baseline` với `jump-baseline.js` đóng
băng trước thay đổi, `--jump` cho bản mới; `kiem-thu-grid-jump-unit.cjs` kiểm
request trực tiếp. Chưa push hoặc cập nhật VPS.

**Hoàn tất bản local và kiểm chứng trong phạm vi bên dưới; chưa push/VPS.**
Chủ dự án chọn làm trước cuộn vùng đã cache (mục tiêu 16–50 ms) và cuộn
liên tục cùng hướng (16–100 ms nếu dữ liệu tải trước theo kịp).
Không kết luận đã tối ưu toàn CRM hoặc đạt tải nhiều người trên VPS.

## Thay đổi

- Khi chỉ cuộn, giữ hàng/ô và header không đổi; không dựng lại toàn vùng.
  Nếu cùng frame có sửa ô, nhận kết quả lưu, đổi lựa chọn hoặc cấu trúc,
  đường vẽ đầy đủ được ưu tiên. Không bỏ cập nhật để đổi lấy tốc độ.
- Lấy trước tối đa hai khối phía trước theo hướng cuộn, 100 dòng/khối,
  sử dụng endpoint và kiểm quyền hiện có. Cache vẫn tối đa 10 khối.
  Không đẩy dữ liệu vùng đang nhìn khỏi cache khi tải đón hoàn thành.
- Đổi hướng/nhảy xa chỉ hủy request tải đón không còn hữu ích. Request do
  copy/dán/editor gọi trực tiếp giữ nguyên. Đổi lọc hủy cả thế hệ cũ.
- Lỗi mạng tải đón không chặn vùng có cache; khi thực sự xem vùng lỗi,
  hiện lỗi và cho thử lại. 403/404 vẫn gỡ nội dung mất quyền ngay.
- Không đổi schema, phân quyền, nghiệp vụ, cờ cấu hình hoặc dependency.
  Phần cuộn đơn thuần chạy ở mặc định; đây không phải bật toàn bộ
  `CRM_OPT_RENDER`. Đã kiểm tương thích khi cờ renderer bật trong harness.

## Đo trước/sau

Chrome headless trên cùng máy Windows, 1440×900 và 390×900. Template được
render thật từ fixture Django trên PostgreSQL test riêng; dữ liệu API mô
phỏng tổng 100.000 dòng, chỉ tạo JSON từng khối, trễ cố định 120 ms. Baseline
đóng băng file trước sửa, gồm thay đổi ngày nhập local đang tồn tại để so
sánh cùng nền. Hash và số đo ở
[verification/grid-scroll-20260916.json](verification/grid-scroll-20260916.json).

Thời gian từ đặt scrollTop đến toàn bộ hàng trong vùng nhìn có dữ liệu và
một cơ hội paint ở rAF tiếp theo; không phải đo màn hình vật lý/INP thực địa.
40 mẫu cached, 55 bước cuộn mỗi viewport; có CDP trace trong lượt cuộn.

| Chỉ số | Trước desktop | Sau desktop | Trước mobile | Sau mobile |
|---|---:|---:|---:|---:|
| p95 vùng đã cache, ms | 32,1 | 31,9 | 32,1 | 32,0 |
| p95 cuộn cùng hướng, ms | 140,9 | 47,7 | 136,9 | 49,4 |
| Phần tử tạo mới trong 40 lượt cached | 27.880 | 2.594 | 14.680 | 2.126 |
| Khối cache cuối phép đo | 10 | 10 | 10 | 10 |

Vùng cached đã nằm trong mục tiêu từ baseline: không tuyên bố tăng tốc rõ
ở độ trễ này. Điểm cải thiện là giảm tạo phần tử thừa và thời gian chờ khi
vào khối tiếp theo. Header/ô giữ cùng node, tránh phá focus/double-click.

Kiểm wheel thật riêng: 50 lượt × 240 px, nghỉ 35 ms giữa lượt, không đợi
request hoàn thành. Baseline có 4 đoạn thiếu dữ liệu mỗi viewport,
50–133 ms; bản sửa 0 đoạn thiếu trong lượt thử này. Quan sát bằng rAF;
không bảo đảm mọi khung hình trên mọi thiết bị/mạng đều không trống.

**Chi phí:** toàn kịch bản đo gồm nhảy xa, quay lại và wheel tăng từ 19 lên
33 request dữ liệu. Tải trước có thể tải cả phần người dùng không xem;
không diễn giải giảm lag là giảm tải server. Lượt này không kiểm tải 10
người, không đo database 100.000 bản ghi hoặc rò bộ nhớ dài hạn trên VPS.

## Kiểm thử

- TDD đỏ trước sửa: 40 lượt cached tạo 27.880 phần tử, không có tải trước
  khối tiếp theo. Hồi quy sau sửa đạt tại 1440/390, cờ render tắt và bật.
- Chrome kiểm wheel/ngang, giữ selection, nháp editor, chiều cao hàng,
  phản hồi cũ sau đổi lọc, lỗi 503 tải đón/đang nhìn/thử lại và 403 xóa cache.
- `pytest crm/tests/test_master_grid.py crm/tests/test_master_nine.py
  crm/tests/test_shared_grid.py crm/tests/test_shared_integrity.py
  crm/tests/test_waybill_feedback.py -q -o addopts= --ds=knjsc.settings.test`:
  **110 đạt**, 38,13 giây, database `test_grid_scroll`.
- Fixture xuất template: **1 đạt**, 4,93 giây trên DB test.
- Chrome với server Django/database test thật qua
  `test_market_currency_browser.py`: **1 đạt**, 60,59 giây; desktop/mobile
  tạo đơn, xem đơn gốc, sửa lưới, xác nhận quốc gia và autosave.
- Node: optimization, row geometry, queue, autosave, conflict, scope đạt.
  Hai fixture Node cũ thiếu binding (`ensureDrafts` và guard chế độ xem);
  đã bổ sung để chạy đúng đường thật. Test scope cũ cũng thất bại trên
  baseline do thiếu guard, không phải hồi quy phân quyền của bản sửa.
- Không có skip trong các lượt chủ động chạy trên đây. Không chạy toàn suite.

## Tái lập

1. Xuất fixture: `docker compose -f deploy/docker-compose.yml run --rm
   -e RUN_MIGRATIONS=0 -e POSTGRES_DB=grid_scroll -e GRID_SCROLL_FIXTURE=1
   web pytest crm/tests/test_scroll_fixture.py -q -o addopts=
   --ds=knjsc.settings.test`.
2. Giữ bản JS trước sửa tại `storage/grid-scroll/baseline.js`.
3. Với Node/Playwright có sẵn, chạy `scripts/kiem-thu-grid-scroll.cjs`
   lần lượt `--baseline`, không tham số, `--render-flag`.
4. JSON/trace/log nằm ở `storage/grid-scroll/`, chỉ là dữ liệu kiểm thử.

Giữ nguyên các thay đổi ERP/ngày nhập của tác vụ khác. Diff của phần này
chỉ sửa controller lưới, fixture/harness và tài liệu. Bản VPS hiện hành chưa
có tối ưu cuộn này; cần phát hành riêng khi được yêu cầu.
