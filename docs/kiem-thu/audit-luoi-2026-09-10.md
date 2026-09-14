# Kiểm tra độc lập tính tối ưu và chịu tải lưới — 10.09.2026

## Kết luận

Lưới master `van_don_moi` đã có giới hạn dữ liệu và DOM hữu ích. Bản chụp được
đo đạt mục tiêu p95 đọc <= 1 giây ở 100.000 dòng trong phép đo ngắn 10/20 người,
nhưng không đạt ở 300.000 dòng. Đây không phải nghiệm thu tải sản xuất hoặc
kết luận về mọi bảng CRM. Không sửa code ứng dụng, quyền hoặc dữ liệu đang dùng.

**Mốc mã:** sao chép workspace khoảng 17:03 ngày 10.09, lưu SHA256 trong
`storage/grid-audit-20260910/evidence/source-hashes.json`. Task CRM tiếp tục sửa
workspace trong lúc đo; snapshot chưa có migration `0010_master_cover_index`.
Index mới và thay đổi sau mốc này chưa được phép đo này chứng minh hiệu quả.
Không so phần trăm cải thiện với các lượt trước có cấu hình/workload khác.

## Môi trường và phương pháp

- Database riêng `test_knjsc_master_capacity_nine_audit0910`; pytest tạo và dọn.
  Functional dùng database test khác. Không seed, migrate hoặc kiểm tải database
  `knjsc_db` đang dùng.
- PostgreSQL 16 trên Docker Desktop, RAM Docker 7,63 GiB dùng chung với các dịch
  vụ khác. Trong lượt đo có task CRM chạy kiểm thử khác; tài nguyên không biệt lập.
- Gunicorn 3 worker x 4 thread, keep-alive 5 giây, cổng riêng 8037.
  Chỉ kết nối DB test đặt `max_parallel_workers_per_gather=0` theo harness sẵn có.
- Tái sử dụng fixture và Locust `test_master_nine_capacity.py` /
  `locust_master_nine.py` trong snapshot. Bản harness chỉ đổi cổng và keep-alive.
  Mỗi mức chạy 90 giây, bỏ 15 giây đầu, cửa sổ mẫu thực tế khoảng 74,6 giây.
- 100.000/300.000 DataRecord, 25 cột, một chi tiết sản phẩm mỗi dòng, phân công
  quay vòng; các giá trị quốc gia/ghi chú lặp lại. Số dòng không chứng minh số
  khách hàng duy nhất. Workload Admin, Leader Vận đơn, Staff Vận đơn và Sale,
  nghỉ 1–3 giây, đọc vùng đầu/giữa/cuối, lọc, poll và lưu một ô.
- Ngưỡng đối chiếu: p95 đọc <= 1.000 ms, lưu ô <= 500 ms. Điều kiện dừng harness
  lỗi > 5% chỉ là bảo vệ phép đo, không phải ngưỡng chấp nhận lỗi sản phẩm.
- p50/p95/p99 tính nearest rank từ mẫu gốc. Không gộp từ chối CAS vào lỗi server.

## HTTP vừa chạy

Đơn vị ms, p95; xem `summary.json` cho p50/p99, dung lượng và số mẫu mỗi endpoint.

| Dòng | Người | Đọc khối | Lọc | Lưu ô | Request trong cửa sổ đo | Lỗi request |
|---:|---:|---:|---:|---:|---:|---:|
| 100.000 | 10 | 304 | 291 | 68 | 504 | 0 |
| 100.000 | 20 | 338 | 302 | 115 | 976 | 0 |
| 300.000 | 10 | 1.553 | 2.104 | 134 | 365 | 0 |
| 300.000 | 20 | 1.299 | 1.737 | 293 | 789 | 0 |

Tổng 2.634 request trong cửa sổ đo, 0 lỗi ngoài CAS. Harness ghi thêm 4 phản hồi
409 trong các lượt 20 người, tính cả warm-up; không đủ dữ liệu để khẳng định
mọi 409 đều là tranh chấp ô vì harness nhận mọi 409 là expected conflict.
Lượt 20 người nhanh hơn 10 người ở một số endpoint không chứng minh tăng tải
làm nhanh hơn: cửa sổ ngắn, tập request ngẫu nhiên và tài nguyên dùng chung.

Harness hoàn tất: 1 passed, 0 skipped, 509,757 giây (gồm dựng dữ liệu và Chrome).
**Harness passed không đồng nghĩa đạt ngưỡng hiệu năng: 300.000 dòng chưa đạt.**

## Chrome vừa chạy

Chrome headless trên Windows, 1440x900 và 390x900. Mỗi màn hình đo 20 lần chọn
dòng và 22 lần chuyển vùng, kiểm đúng chỉ số dòng đã tải, gồm vùng cuối bảng.
Chọn dòng tính từ event đến hai animation frame; cuộn tính từ thao tác Playwright
đến khi ô đích có dữ liệu, gồm mạng/driver. Không gọi các số này là INP hay FPS.

| Dòng | Rộng | Mở trang đến ô đầu, ms (1 mẫu) | Chọn dòng p95, ms | Cuộn/tải vùng p95, ms |
|---:|---:|---:|---:|---:|
| 100.000 | 1440 | 1.781 | 32,2 | 231 |
| 100.000 | 390 | 1.054 | 32,4 | 317 |
| 300.000 | 1440 | 1.897 | 32,2 | 841 |
| 300.000 | 390 | 1.846 | 32,1 | 835 |

Cả 4 trường hợp đạt kiểm tra vùng cuối, cache <= 10 khối, tối đa 460 ô desktop /
176 ô hẹp; không có pageerror hoặc long task được observer ghi nhận trong lượt
đo. Heap sau GC ở đoạn cuối khoảng 6,9–7,1 MiB, không tăng mạnh trong 22 lượt
cuộn. Không suy ra không rò bộ nhớ sau nhiều giờ. Viewport 390 trên PC không
đại diện CPU/mạng của điện thoại thật. Browser chạy sau từng lượt HTTP, chưa
đo nhập liệu trong lúc 20 trình duyệt cùng sửa.

## Kiểm tra code và tính đúng

- Lưới dựng DOM bằng JavaScript; `mg-canvas` là thẻ `div`, không phải Canvas
  bitmap hoặc ảnh bảng Python vẽ sẵn. Có virtualization cả hàng và cột.
- Backend trả khối 100 dòng; frontend cache tối đa 10 khối, chọn toàn bảng bằng
  trạng thái; không đưa hàng triệu ô vào DOM. Hình học chiều cao hàng dùng cấu
  trúc thưa, không cấp một mảng đầy đủ theo số dòng.
- Có index theo bảng/ngày/cập nhật/số điện thoại, GIN cho JSON và index FK.
  Chỉ cắt OFFSET trên cửa sổ ID trước khi lấy chi tiết; vẫn còn chi phí OFFSET
  và tổng hợp theo phạm vi, không phải keyset pagination toàn bộ.
- `stamp()` tính COUNT/MAX theo quyền và mỗi khối lại đếm tổng lọc. Phạm vi Sale
  có nhiều nhánh OR/JOIN; đây là điểm ưu tiên lấy EXPLAIN theo vai trò.
  Probe SQL bổ sung của lượt này không hoàn tất trước khi fixture dọn DB;
  không công bố thời gian SQL riêng hoặc quy trách nhiệm chắc chắn cho một query.
- JSON khối có lặp metadata và thông tin hiển thị từng ô; phản hồi đọc trung
  bình khoảng 475–478 KB trong các lượt đã xem. Đây là độ dài phản hồi Locust,
  không phải dung lượng truyền qua một reverse proxy có nén ở production.
- CAS, receipt và lịch sử được giữ. Đã chạy `test_master_grid.py`,
  `test_master_nine.py`, `test_waybill_feedback.py` trên snapshot:
  **68 passed, 0 failed, 0 skipped, 21,631 giây**. Có hồi quy ghi đồng thời,
  replay, rollback và quyền bị thu hồi. Không coi đó là full-suite hoặc chứng
  minh mọi tình huống tranh chấp khi kiểm tải.

## Việc cần kiểm tiếp, chưa triển khai trong audit

1. Đo lại index mới cùng dữ liệu/cấu hình, thu EXPLAIN cho COUNT/MAX, phạm vi
   Sale/CSKH và cuộn sâu; tối ưu truy vấn vẫn phải giữ nguyên quyền và tổng đúng.
2. Bổ sung workload thực của tab: POST kiểm quyền các ID trong cache, gửi version,
   invalidation khi người khác sửa. Locust hiện chưa mô phỏng đầy đủ các bước này.
   Phân loại 409 bằng nội dung thay vì coi toàn bộ là CAS đúng.
3. Kiểm đủ warm-up 1 phút + đo 5 phút trên mã cuối, sau đó endurance và trình
   duyệt vừa cuộn/nhập vừa có người khác lưu. Chưa có phép đo endurance đạt trong
   audit này; không dùng tệp `endurance-browser` chưa hoàn tất của task khác.
4. Đo nhập/xuất lớn, dán/lưu hàng loạt, nhiều chi tiết sản phẩm, dữ liệu đa dạng và
   mạng/máy yếu. Đánh giá payload/nén và dung lượng receipt/lịch sử theo tần suất
   sửa thực tế trước khi quyết định thay đổi. Chưa có lý do đo được để đổi thư
   viện lưới hoặc chuyển sang Canvas chỉ vì số ô tổng lớn.

## Bằng chứng và tái chạy

Raw JSON, JUnit, snapshot và script ở `storage/grid-audit-20260910/` (local).
`evidence/summary.json`, `browser-100000.json`, `browser-300000.json`,
`capacity.xml`, `functional.xml`, `resources.json`, `source-hashes.json`.
Resource samples là quan sát rời rạc, không phải peak CPU/RAM đầy đủ.

Lệnh capacity dùng Compose run với `RUN_MIGRATIONS=0`,
`POSTGRES_DB=knjsc_master_capacity_nine_audit0910`, `KN_NINE_CAPACITY=1`,
`NINE_STAGE=after`, `NINE_DURATION=90s`, `NINE_WARMUP=15`; mount snapshot `/app`
và `/before/app:ro`, evidence `/evidence`, port `8037:8037`, chạy
`pytest crm/tests/test_master_nine_capacity.py -s -q --junitxml=/evidence/capacity.xml`.
Chạy đồng thời `node storage/grid-audit-20260910/browser.cjs` bằng runtime đã có
Playwright/Chrome. Functional chạy ba file kể trên với tên database test riêng.

Đã dọn container kiểm thử do audit tạo; không dừng dịch vụ của task khác.
Không thêm `-> đã làm` vào KNJSC_PROBLEM, không commit/push.
