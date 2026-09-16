# Chọn ô và nhập trong lúc lưu — 16/09/2026

Đã hoàn tất phạm vi local được chủ dự án yêu cầu. Không đổi API, quyền,
lịch autosave 500 ms/2 s, CAS hoặc dữ liệu khách; chưa commit/push/VPS.

## Nguyên nhân và sửa

Baseline đã cho chọn/nhập khi request lưu đang chờ, nhưng mỗi lần chọn,
mở/hủy editor lại dựng cây ô/header cho cả vùng nhìn. Tách repaintSelection
để cập nhật lớp lựa chọn, aria, nhãn vùng và vị trí editor. Đổi nội dung,
phản hồi lưu hoặc scroll/selection cùng frame ưu tiên vẽ đầy đủ để không
bỏ cập nhật. Giữ nguyên tối ưu cuộn từ tác vụ khác.

## Đo trước/sau

Template Django thật từ test_scroll_fixture; API mô phỏng 10.000 hàng theo
khối, không ghi database dev/VPS. Chromium trong Codex trên Windows,
1280×720, cùng fixture và cấu hình renderer mặc định. Request lưu bị giữ
đến khi nhấn trả kết quả; 40 lượt mỗi thao tác. Đo sự kiện tổng hợp tới
hai requestAnimationFrame, không phải INP thực địa hoặc thời gian server.

| Chỉ số | Trước | Sau |
|---|---:|---:|
| Chọn ô p95 | 33,6 ms | 33,6 ms |
| Mở editor p95 | 33,7 ms | 33,7 ms |
| Nhập nội dung p95 | 33,7 ms | 33,7 ms |
| Lượt chọn chậm nhất | 58,1 ms | 33,6 ms |
| Phần tử tạo mới trong kịch bản | 51.891 | 466 |

Baseline đã đạt p95 mục tiêu; không tuyên bố cải thiện rõ độ trễ trung vị.
Giảm khoảng 99,1% phần tử tạo thừa; mọi mẫu bản cuối dưới 34,2 ms. Không bảo
đảm mọi thiết bị đều dưới 50 ms. Chưa đo mobile, IME composition của bộ gõ
hệ điều hành hoặc bộ nhớ dài hạn. [Số đo/hash](verification/grid-interaction-20260916.json).

## Kiểm chứng

- TDD red: chọn ô vẫn gọi dựng nội dung; green: chỉ cập nhật lựa chọn.
  Test phát hiện và sửa thứ tự scroll trước selection trong cùng frame.
- Harness xác nhận chọn đúng hàng, nhập đúng chữ khi busy; gửi A rồi sửa B
  cùng ô, response A về vẫn giữ B. Không đợi server để tương tác.
- Click/F2/gõ qua công cụ trình duyệt khi busy: chữ tiếng Việt còn nguyên;
  mô phỏng 503 hiện Lỗi lưu/Thử lại; Ctrl+Z về giá trị cũ, Ctrl+Y khôi phục
  chữ vừa gõ khi request vẫn đang chờ.
- Node đạt: grid-interaction-unit, master-autosave-unit, master-conflict-unit,
  master-scope-unit, grid-jump-unit, optimization-unit.
- PostgreSQL test riêng: **48 passed, 0 failed/error/skipped**:
  `docker compose -f deploy/docker-compose.yml run --rm -e RUN_MIGRATIONS=0 -e POSTGRES_DB=interaction_regression web pytest crm/tests/test_master_nine.py crm/tests/test_shared_integrity.py -q --maxfail=1 --junitxml=/storage/grid-interaction/server-tests.xml`.
- Không chạy full suite, kiểm tải nhiều người hoặc ghi VPS trong lượt này.

## Tái lập

Dùng fixture `storage/grid-scroll/fixture.html` và `fixture.json` theo
[hướng dẫn kiểm cuộn](kiem-chung-cuon-luoi-20260916.md). Giữ JS trước sửa ở
`storage/grid-interaction/baseline.js`. Chạy `node scripts/serve-grid-interaction.cjs`
(chỉ bind 127.0.0.1:18621), mở `/?stage=before` hoặc `/?stage=after`, nhấn
“Đo chọn và nhập khi đang lưu”. Nhấn “Trả kết quả lưu” cho lượt còn lại trước
khi rời trang. Dừng server sau khi kiểm. Harness chỉ giữ dữ liệu thử trong
RAM, không nối Django/database; các nút kiểm thử không vào sản phẩm.

Các việc tải/server/sync, bộ nhớ dài hạn và nhập bù 3.333 dòng vẫn có phạm
vi riêng trong daily tasks; không coi lượt này hoàn tất toàn bộ tối ưu CRM.
