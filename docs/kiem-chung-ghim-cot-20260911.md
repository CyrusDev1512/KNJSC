# Sửa rung cột ghim Vận đơn mới — 11.09.2026

## Phạm vi và nguyên nhân

Chủ dự án đã duyệt kế hoạch sticky. Chỉ thay `master-grid.js`,
`master-grid.css`, bài kiểm và tài liệu liên quan; không commit/push.
Các thay đổi Admin/nhập inline/Lên đơn/ERP đang có được giữ nguyên.

Trước sửa, vị trí ô ghim được tính bằng `scrollLeft + pinX`, số hàng bằng
`scrollLeft`, tiêu đề bằng `scrollTop`. Khi trình duyệt đã cuộn nhưng callback
render chưa chạy, các ô trượt theo nội dung rồi được kéo lại. Thêm/bớt cột ảo
còn làm thay node nút tiêu đề. Bài hồi quy viết và chạy trước sửa đã thất bại
đúng hai hành vi này; không có lỗi JavaScript trong lượt tái hiện.

Sau sửa, vùng sticky trong mỗi hàng giữ số hàng/tay kéo/cột ghim; tiêu đề
sticky dọc. Ô thường vẫn cuộn tự nhiên. Đồng bộ DOM giữ node ô/nút tiêu đề,
kể cả khi thay tập cột ảo. Không nhân đôi dữ liệu, không đổi màu hay quyền.

## Môi trường, cách đo và kết quả

Chrome headless trên máy Windows hiện tại, PostgreSQL test riêng; dùng
`test_master_row_capacity.py` tạo 100.000 rồi 300.000 dòng, khối 100/cache 10.
Fixture SQL được bổ sung `unit` cho khớp migration 0006 đang có trong workspace.
Lần khởi tạo đầu thiếu trường này đã thất bại trước khi mở lưới; không tính
là lỗi hồi quy ghim. Không ghi vào dữ liệu local thật hoặc khách mẫu.

Baseline là bản JS/CSS working tree ngay trước sửa, không dùng HEAD cũ.
Phép so sánh profile phục vụ hai bản JS/CSS qua Playwright route trên cùng
database test và phiên người dùng; runtime server không bị thay.

| Kiểm vị trí | Trước | Sau |
|---|---|---|
| 1440/1280/390 px, CSS zoom 100%/125%, 40 bước mỗi tổ hợp, mỗi cỡ dữ liệu | Bước cuộn đầu lệch 137–246 px; sau đó có node tiêu đề bị thay | 0 px; node được giữ |
| Tiêu đề ngay sau cuộn dọc | Lệch đến 18 px màn hình ở CSS zoom 125% | 0 px |
| Profile cuộn tiến/lùi và dọc, 120 bước ở 1440 px, mỗi cỡ dữ liệu | Lệch ngang tối đa 131 px | 0 px |
| Tải dữ liệu trong kịch bản capacity | 25 request/cỡ dữ liệu | 25 request/cỡ dữ liệu |
| Tải dữ liệu trong kịch bản profile và hai vòng qua 12 khối | 46 request/cỡ dữ liệu | 46 request/cỡ dữ liệu |

Đo vị trí ngay sau thay offset, trước khi rAF ứng dụng chạy; vì vậy bắt được
trạng thái trượt tạm thời. Video trước/sau được ghi từ Chrome. Các khung hình
đã xem cho thấy vùng ghim kín và đứng yên; đây không phải xác nhận cảm nhận
trên mọi màn hình/GPU hoặc thao tác trackpad thực tế của người dùng.

Đo thời gian thực thi `render()` bằng wrapper chỉ trong script kiểm thử,
119 mẫu mỗi bản/cỡ dữ liệu, không bao gồm toàn bộ paint/compositing:

| Dữ liệu | Bản | p50 / p95 / p99 render (ms) | Long task trong đoạn cuộn |
|---|---|---|---|
| 100.000 | Trước | 9,6 / 12,6 / 13,8 | 0 |
| 100.000 | Sau | 12,9 / 21,1 / 24,3 | 0 |
| 300.000 | Trước | 9,5 / 15,0 / 20,5 | 0 |
| 300.000 | Sau | 10,9 / 17,5 / 25,9 | 0 |

Render có tăng chi phí; không tuyên bố bản mới nhanh hơn về CPU hoặc đạt
60 FPS. Việc đứng yên của cột không còn chờ callback JavaScript bù vị trí.
DOM canvas tối đa trong profile tăng từ 651 lên 698 node do vùng ghim,
không tăng theo tổng số dòng; cache tối đa 10. Heap sau GC ở vòng thứ hai:
100k sau sửa 6.577.909–7.419.111 byte, 300k 6.633.795–6.734.847 byte.
Hai vòng cuộn là kiểm có giới hạn, không thay thế chạy bền bộ nhớ dài hạn.

## Hồi quy thao tác

`kiem-thu-master-pinned-ui.cjs` đạt trên fixture 1.302 dòng riêng:

- Tiêu đề và dữ liệu thẳng nhau khi đã cuộn; kéo rộng cột ghim 60 px.
- Ô cuộn không đè vùng ghim; chọn vùng xuyên ranh giới ghim.
- Bấm đúp 120 ms, nháp inline giữ nội dung/vị trí khi cuộn; Escape hủy.
- F2, Tab, autosave và đọc lại sau reload xác nhận giá trị đã lưu.
- Ẩn/hiện/đổi thứ tự cột giữ đúng tọa độ và một node cho mỗi ô.
- Tái sử dụng toàn bộ bài chiều cao hàng: kéo 28–400, Escape/Home, mất focus,
  pointercancel, lưu theo ID, lọc/sắp xếp, loại khối cache, polling, đọc chữ dài,
  copy/paste/Delete/Undo, chọn vùng, PageUp/Down, CSS zoom và cảm ứng mô phỏng.

Bốn script unit autosave/conflict/queue/scope, row-geometry và bài lớp chọn
frozen-selection đều đạt. `node --check` và `git diff --check` đạt.
Fixture server pytest kết thúc thành công cho baseline, after, UI và profile.
Không chạy lại ma trận HTTP nhiều người hoặc suite backend đầy đủ vì không
đổi backend; số request do cơ chế ghim không tăng trong kịch bản đã đo.

## Tái chạy và bằng chứng

Từ gốc repository, dùng fixture DB test, không dùng launcher seed local:

```powershell
docker compose -f deploy/docker-compose.yml run --rm -p 8033:8033 -v C:/KNJSC/KNJSC/.agents/design-state/review/pinned-20260911:/evidence -e RUN_MIGRATIONS=0 -e POSTGRES_DB=knjsc_master_capacity_rows_pinned_check -e KN_MASTER_ROW_CAPACITY=1 web pytest crm/tests/test_master_row_capacity.py -q
# Ở terminal khác khi fixture sẵn sàng:
node scripts/kiem-thu-master-pinned.cjs
```

Node cần resolve Playwright từ runtime đã có qua `NODE_PATH`; không cài thêm
dependency. `kiem-thu-master-pinned-profile.cjs` cần snapshot `before.js/css`
trong thư mục evidence. Bài UI dùng `test_master_browser_server.py`,
`KN_MASTER_BROWSER=1`, `--liveserver=0.0.0.0:8035` và port 8035 riêng.

Bằng chứng local tại `.agents/design-state/review/pinned-20260911/`:

- `before-100000/300000.json`, `after-100000/300000.json`: vị trí, node, cache.
  Giá trị null trong dãy baseline biểu thị node bị tháo khỏi DOM, không phải 0 px.
- `profile-before/after-100000/300000.json`: render, vị trí đo lại bằng selector,
  long task, request, DOM và heap.
- `ui.json`, ảnh PNG, video `before-300000.webm`, `after-300000.webm`.
- `sticky-only.patch`: diff JS/CSS riêng so với snapshot trước tác vụ.

Thư mục evidence bị gitignore: video/trace/diff local **không tự lên GitHub**.
Script kiểm thử và biên bản này nằm ngoài thư mục bỏ qua, hiện chưa commit.

## Giới hạn còn lại

- Đã kiểm CSS zoom 125%; **chưa kiểm zoom trình duyệt thật 125%**.
- Chưa nghiệm thu thủ công bằng thanh cuộn/trackpad và màn hình/GPU của end user.
  Không dùng riêng số p95 để kết luận cảm giác chuyển động trên mọi máy.
- Không gộp 16 lỗi kết nối đọc và vấn đề API trước đó vào kết luận sửa cột ghim;
  các vấn đề ấy tiếp tục được theo dõi riêng.
