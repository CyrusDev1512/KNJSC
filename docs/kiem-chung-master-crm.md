# Kiểm chứng lưới master và Thống kê KN CRM — 10.09.2026

Phạm vi ADR-021, nhánh `codex/sua-feedback`. Baseline là snapshot Git `c4f82b995a7eca8433e60a63a8b2ad777cf78fc1`; bản sau là mã làm việc của phiên triển khai. Không commit/push.

## Kết quả HTTP

Docker Desktop: 12 CPU được cấp, 7,63 GiB RAM; PostgreSQL 16; Gunicorn 3 worker × 4 thread, keep-alive 5 giây. Mỗi lượt 45 giây, bỏ 10 giây đầu, 10/20 tài khoản test scope toàn bảng, nghỉ 1–3 giây. Cùng fixture trước/sau; chỉ DB `test_knjsc_master_capacity`. Có các container khác đang chạy trên máy, đây không phải môi trường sản xuất biệt lập.

Đơn vị thời gian: **ms, p95 nearest rank**. Số trong ngoặc là số mẫu của cửa sổ đo; không gộp đọc và ghi thành một số trung bình.

| Dòng | Người | Tải khối trước | Tải khối sau | Lọc sau | Lưu ô trước | Lưu ô sau | Lỗi sau |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 100,000 | 10 | 786.8 (90) | 126.4 (102) | 131.9 (25) | 84.2 (29) | 53.9 (41) | 0 |
| 100,000 | 20 | 915.2 (173) | 127.6 (206) | 143.9 (45) | 95.4 (56) | 74.4 (78) | 0 |
| 300,000 | 10 | 2757.1 (68) | 355.1 (99) | 230.0 (20) | 181.1 (21) | 77.8 (29) | 0 |
| 300,000 | 20 | 3399.9 (123) | 376.3 (195) | 311.8 (39) | 1123.7 (51) | 87.0 (73) | 0 |

Cả bốn lượt sau đạt ngưỡng đọc≤1s và lưu≤0,5s trong workload này. Các log tổng của lượt keep-alive 5 cuối cũng không ghi lỗi, gồm giai đoạn khởi động.

Phản hồi trước là HTML 100 dòng; sau là JSON 100 dòng. Không đánh đồng số byte với tốc độ vẽ, không kết luận “trang 20 KB”. Byte trung bình chưa nén của tải khối:

| Dòng/người | HTML trước (KiB) | JSON sau (KiB) |
|---|---:|---:|
| 100,000/10 | 908.5 | 381.7 |
| 100,000/20 | 907.1 | 380.5 |
| 300,000/10 | 907.6 | 383.4 |
| 300,000/20 | 911.2 | 380.6 |

## Trình duyệt

Chrome headless trên Windows, viewport 1440×900; đo riêng sau từng lượt HTTP. Mỗi loại thao tác 30 mẫu, từ phát event đến hai animation frame. Đây là phép đo phản hồi vẽ, không phải INP thực địa hoặc độ trễ của bộ gõ vật lý.

| Dòng | Chọn/Ctrl+A trước | Chọn/Ctrl+A sau | Đọc chữ dài sau | Kéo cột sau | DOM node trước/sau | Heap sau GC, khối 16–35 |
|---:|---:|---:|---:|---:|---:|---|
| 100,000 | 39.6 | 36.3 | 36.4 | 35.4 | 3625/777 | 5.36–5.37 MiB |
| 300,000 | 43.4 | 34.1 | 36.0 | 35.9 | 3625/777 | 5.36–5.38 MiB |

Cache≤10 khối, DOM ô hữu hạn sau 35 lượt cuộn, gồm khối cuối; heap sau GC ổn định trong khoảng trên. Không có lỗi JavaScript trong lượt đo. Ctrl+A của bản cũ chỉ xử lý DOM trang đã tải; bản mới chọn toàn kết quả bằng trạng thái, nên hai phép đo không đại diện cho cùng khối lượng dữ liệu được chọn.

## Hồi quy và phạm vi đã kiểm

- Lệnh ứng dụng kèm truy vết cuối: **1.026 passed, 3 skipped trong 77,64 giây**, không có failure hoặc warning. Gồm `crm/tests orders/tests forms_builder/tests core/tests tests/test_truy_vet.py`; kết quả lưu tại `review/master/regression-final.txt`.
- `crm/tests/test_master_grid.py`: **17 bài**, có CAS, hai request đồng thời, replay cùng UUID, scope thu lại, giới hạn/atomic, snapshot, trạng thái rỗng/tiền khác loại/top10 và migration xuôi/ngược. Dùng DB test riêng; test đa luồng đóng kết nối sau mỗi worker để teardown database sạch.
- Chrome đầy đủ: chọn/copy xuyên khối, giới hạn 2.000, số 0 đầu, tiếng Việt/multiline, tín hiệu IME, Undo/Redo, xung đột, retry sau server đã lưu nhưng mất phản hồi, bộ lọc cũ về trễ, Phân công/Chi tiết. Desktop 1440/laptop 1280/mobile 390/zoom 125%. Kiểm thêm thu quyền trước poll đầu đã tái hiện lỗi cache cũ và đạt sau sửa; chi tiết trong test-log.
- Đọc ứng dụng local bằng `scripts/kiem-thu-van-don-ui.cjs`: đạt Lên đơn riêng, lưới master và Thống kê desktop/mobile. Không gửi đơn/sửa dữ liệu thật; `migrate crm --plan` không còn migration phải áp dụng ở thời điểm kiểm.
- Ba bài skip trong lệnh thường là server Chrome master, alias feedback và capacity. Master Chrome đã chạy riêng: **1 passed trong 32,63 giây**, script Node đạt; capacity đã chạy riêng: **1 passed trong 453,06 giây** cùng bộ đo Chrome. Alias feedback dùng lại fixture/script master, chưa chạy độc lập. Không coi skip là đã kiểm.

## Giới hạn và các lượt không đạt được giữ lại

- Clipboard được kiểm trong Chrome với cả TSV và HTML, gồm mã `00123`; HTML có gợi ý định dạng văn bản cho Excel. Chưa kiểm vòng sao chép/dán trực tiếp bằng ứng dụng Excel desktop hoặc bộ gõ tiếng Việt vật lý. Trình duyệt thiếu clipboard HTML dùng TSV; phần mềm nhận có thể tự chuyển kiểu dữ liệu.

- Đây là phép đo ngắn trên dữ liệu tổng hợp,25 cột và một WaybillItem/dòng; nhiều giá trị và Ngày lặp lại. Không chứng minh100k khách duy nhất, mọi phân phối thị trường/sản phẩm/ngày hoặc tải nhiều năm ngoài300k dòng.
- Workload dùng20 tài khoản scope toàn bảng để đọc rộng; chưa đo riêng20 nhân viên với phân công phức tạp. Nhập/xuất nền và quyền tải được kiểm hồi quy chức năng, không chạy cùng tải này. Chưa kiểm endurance nhiều giờ hoặc máy chủ sản xuất.
- Lượt đầu hết `/dev/shm`64MB của PostgreSQL. Cả hai snapshot sau đó chỉ dùng kết nối DB test đặt `max_parallel_workers_per_gather=0`; không sửa cấu hình database đang dùng.
- Đã tái hiện và sửa đọc409 quá nhiều bằng snapshot; giảm OFFSET rộng bằng cửa sổ ID. Các số trước sửa còn trong `before-snapshot-*`/`before-id-window-*`.
- Với keep-alive 2 mặc định của harness có lỗi kết nối đơn lẻ. Lượt cuối dùng keep-alive 5 đúng profile Gunicorn hiện có cho cả trước/sau; giữ số cũ ở `keepalive2-*`, không gộp vào bảng cuối.
- Baseline2 dòng chưa tái hiện chắc hiện tượng vỡ toàn bảng ban đầu. Kiểm lưới mới đã xác nhận chọn/đọc/resize không đổi hình học; không tuyên bố biết chắc nguyên nhân lỗi cũ.

Hai POST ô HTML cũ bị chặn cho Vận đơn mới (409 sau kiểm quyền), có hồi quy chống tab cũ bỏ qua CAS. Đường ghi các bảng khác giữ nguyên.

## Tái chạy và bằng chứng

Xem [kế hoạch kiểm thử](06-ke-hoach-kiem-thu.md), [ADR-021](quyet-dinh/021-luoi-master-va-thong-ke-crm.md) và [test-log](test-log.md). Raw JSON/log/ảnh nằm tại `.agents/design-state/review/master/` (local, không commit). Manifest đăng nhập test được fixture dọn; không có dữ liệu khách thật trong bộ đo.

Diff local: `review/master/implementation.patch` chứa các tệp code/kiểm thử CRM và tài liệu riêng của ADR-021; `review/master/shared-documents.patch` chứa tài liệu dùng chung, có thể gồm cập nhật từ tác vụ ERP đang làm đồng thời. Không thay đổi hoặc gom code ERP vào bản diff CRM.


## Bổ sung sau phản hồi thao tác chuột

Chủ dự án báo không sửa/kéo được. Kiểm lại đã tìm thấy khoảng trống kiểm thử:
`dblclick()` không có khoảng nghỉ đã bỏ sót việc thay node giữa hai lần bấm;
bài kéo cột chỉ kiểm tiêu đề bằng dữ liệu, chưa kiểm chiều rộng thực sự tăng.
Đã sửa giữ node trong cửa sổ cuộn và đặt tay kéo trọn trong tiêu đề, nâng bài
Chrome lên bấm đúp cách 120 ms, kiểm tăng chiều rộng cột/khung nhập và thứ tự
DOM sau cuộn. Xem kết quả lần chạy bổ sung trong [test-log](test-log.md).
Số đo trình duyệt 100k/300k ở trên là trước bản sửa chuột này, chưa đo lại toàn
ma trận. Kiểm local chỉ mở/hủy editor, không ghi vào 20 khách mẫu.

Bản kéo chiều cao hàng đã đo lại trình duyệt: [kiểm chứng 100k/300k](kiem-thu/keo-chieu-cao-hang.md).
