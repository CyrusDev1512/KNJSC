# ADR-024 — Tối ưu KN CRM theo số đo

Ngày: 11.09.2026. Trạng thái: **đã triển khai sau cờ và kiểm local;
chưa nghiệm thu toàn bộ hiệu năng/phát hành**.

## Phạm vi đã duyệt

Nhánh `CRM-Optimization`, checkout riêng `C:/KNJSC/CRM-Optimization`.
Mốc `3c3fd09` cộng toàn bộ thay đổi chưa commit đã đóng băng trong snapshot;
không dùng HEAD đơn thuần để thay cho baseline. Không sửa checkout đang dùng,
database nghiệp vụ hoặc cấu hình launcher. Không commit/push khi chưa được yêu cầu.

VPS 12 CPU/24 GB/300 Mbps mới là dự kiến. Chỉ báo năng lực local đã đo.
Giữ phân quyền, CAS, biên nhận, autosave, 2.000 ô/lượt, lịch sử nghiệp vụ,
cuộn ảo 100 dòng/khối và cache 10 khối. ERP tiếp tục chỉ đọc.

## Quyết định triển khai

- `GridRevision`, `GridChange` và bảng đệm giao dịch `GridPendingChange`
  chỉ chứa metadata kỹ thuật. Statement trigger bắt cả bulk SQL. Trigger
  deferred gom theo transaction, khóa phiên bản các bảng theo ID tăng dần
  ở cuối giao dịch; rollback không công bố phiên bản. Không dùng sequence
  làm bằng chứng commit. Không ghi nội dung khách hàng vào nhật ký này.
- Journal giữ 10.000 revision/bảng; mỗi sự kiện tối đa 2.000 ID. Vượt ngưỡng
  ghi dấu đồng bộ lại. Không xóa lịch sử nghiệp vụ hoặc biên nhận.
- Giao thức đọc v2 ký token theo người dùng, database, bảng, điều kiện và
  phiên bản quyền/cấu trúc/trường liên quan. Tổng số dòng được cache có
  phiên bản; Redis lỗi thì đọc PostgreSQL. Cursor chỉ cho thứ tự mặc định;
  offset vẫn phục vụ nhảy giữa/cuối và sắp xếp động.
- Polling 8 giây dùng journal, kiểm lại những ID client giữ trong phạm vi
  hiện hành. Chỉ trả dòng đang nhìn cần đổi, ID cần bỏ cache hoặc yêu cầu
  dựng lại truy vấn. Không trả ID ngoài quyền chưa do client cung cấp.
- Renderer giữ node sticky; cache hình học và tái sử dụng hàng không đổi.
  Thay lựa chọn chỉ cập nhật lớp chọn; bản nháp vẫn thuộc RAM theo ID.
- Biên nhận v2 lưu xác nhận theo ô/thuộc tính và các ô phụ thuộc thực sự đổi.
  Replay trả đúng xác nhận ban đầu sau kiểm quyền, kể cả khi cờ rollout tắt.
- Cache Thống kê có tuổi tối đa 15 giây từ đầu lần tính, không gia hạn khi
  đọc lại. Khóa tính có thời hạn và chờ hữu hạn; lỗi cache đọc DB. Quyền và
  cấu trúc thay đổi làm mất hiệu lực ngay. Làm mới bỏ qua cache; mọi biểu đồ
  và bảng của lần tính dùng snapshot nhất quán. Không đổi công thức.
- Xuất write-only của openpyxl là tùy chọn có cờ, giữ kiểu dữ liệu/tiêu đề/
  freeze panes và thứ tự. Không tăng giới hạn xuất. Hàng đợi nặng tách riêng,
  một worker nặng và một worker thường, tổng concurrency tối đa 2.
- Cấu hình ứng viên VPS tại `deploy/production/`; Redis cache riêng 512 MB,
  broker/result riêng không eviction. Không áp cấu hình RAM VPS vào máy local.

Các cờ `CRM_OPT_READ`, `SYNC`, `RECEIPTS`, `RENDER`, `STATS`, `EXPORT`,
`QUEUES` (cùng tiền tố `CRM_OPT_`) mặc định tắt. Migration hạ tầng vẫn phát
metadata khi tắt cờ đọc để không bỏ sót ghi trong lúc rollout/rollback.
Chi phí trigger phải được đo cùng đường ghi, không được coi là miễn phí.
Ma trận local cho thấy đọc/lọc/sync cải thiện; render chưa nhanh hơn ổn định,
Thống kê cold còn >1 giây, xuất nền tích hàng đợi và RSS app còn tăng trong
bài bền. Giữ các cờ mặc định tắt; không dùng cấu hình VPS chưa đo để đóng
các mục này. Không bổ sung index khi chưa đủ điều kiện đo bên dưới.

## Nghiệm thu và rollback

Xem [biên bản kiểm chứng](../kiem-chung-crm-optimization-20260911.md).
Chưa thêm chỉ mục suy đoán. Chỉ chấp nhận chỉ mục sau ba lượt đo cải thiện
p95 ít nhất 20%, p95 ghi tăng không quá 10%, kết quả không đổi.

Lỗi mạng/5xx không chủ đích không có ngưỡng "dưới 5% là đạt". CAS hợp lệ
phân loại riêng và không đếm hai lần. Sai dữ liệu/quyền/ghi trùng dừng lượt đo.
Quay lui bằng cờ; không xóa lịch sử/biên nhận hoặc phục hồi DB để rollback code.

## Lợi ích và chi phí cần đối chiếu

| Nhóm | Việc giảm | Chi phí/rủi ro phải đo |
|---|---|---|
| Phiên bản/count | COUNT/MAX lặp | Trigger, khóa revision cuối transaction, journal |
| Cursor | OFFSET khi đi khối liền kề | Token ràng buộc phạm vi; offset vẫn còn cho nhảy xa |
| Sync/render | Nạp lại cache, dựng cây ô không đổi | Cache phía client/server và tính đúng khi đổi quyền |
| Receipt | JSON cả dòng trong mỗi xác nhận | Hợp đồng v1/v2, normalize, replay và nháp mới |
| Thống kê | Tính lại trong 15 giây | Số liệu có độ trễ tối đa 15 giây, khóa tính |
| Xuất/queue | Giữ toàn workbook trong RAM | Một tác vụ nặng/lần; giữ định dạng và quyền tải |
| Production | Cách ly tác vụ nặng/cache/broker | Cần VPS thực để đo CPU steal, I/O, RTT và connection |
