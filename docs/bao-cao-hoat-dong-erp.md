# Báo cáo hoạt động KNERP — 10.09.2026

## Phạm vi đã duyệt

Mở rộng bộ tổng hợp hiện có cho Sale, Marketing và hoạt động Vận đơn.
Dữ liệu vẫn ở TableDef/ColumnDef/DataRecord; phép tính dùng reports/aggregations
và Metric của reports/marketing. Không gọi view hoặc service thống kê CRM.

- Sale: Số Mess, Số đơn, Doanh số, Tỉ lệ chốt = tổng Số đơn / tổng Số Mess,
  Doanh thu khi nguồn khai báo rõ. Mẫu số 0/thiếu hiện `—`.
- Marketing: giữ các chỉ tiêu BC MKT; Hóa đơn/Doanh thu vẫn là Giá Mess / CPO,
  tính trên đầu vào chưa làm tròn. Không suy nghĩa hai trường Doanh thu/Hóa đơn.
- Vận đơn: số đơn ID duy nhất, tổng số lượng chi tiết còn hiệu lực, trạng thái,
  người phụ trách được phân công, sản phẩm và quốc gia. Không thống kê tiền.
- Hiệu suất: nhóm kết quả thực tế theo tài khoản hoặc phòng ban, không mục tiêu,
  điểm, sao, tuyển dụng, thăng tiến hoặc đánh giá tuân thủ.

Ngày là kỳ báo cáo; nếu biểu mẫu có Ngày ra đơn thì giữ riêng. Khi nộp báo cáo,
Ngày của biểu mẫu phải khớp ngày báo cáo để lịch sử và thống kê không lệch kỳ.
Mỗi dòng có một sản phẩm và một thị trường. Giữ ràng buộc một biểu mẫu/người/ngày
hiện có; chưa tự đổi quy tắc nộp nhiều báo cáo trong một ngày.

## Nguồn và quyền

`ReportSource` giữ loại báo cáo và ánh xạ cột tường minh tại thời điểm cấu hình.
Migration reports/0002 chỉ tạo metadata, không sửa hoặc tái ghi báo cáo đã nộp.
Lệnh `python manage.py configure_erp_reports` cấu hình các mã nguồn hiện hành:
`bao_cao_sale`, `bao_cao_mkt`, `van_don_moi`. Lệnh chạy trong transaction,
lặp lại không nhân biểu mẫu/trường và dừng nếu thiếu cột bắt buộc.
Nguồn có schema khác cần ánh xạ được kiểm tra, không tự dò dữ liệu để đoán.

Biểu mẫu Sale/Marketing dùng danh mục Market của orders qua choice_registry;
thị trường bắt buộc cho lần nộp mới. Dữ liệu cũ thiếu thị trường giữ nguyên và
thuộc nhóm Chưa xác định. Không chia chi phí hay suy thị trường từ sản phẩm.
Không sửa quyền tiền hoặc UI của KN CRM. Trách nhiệm tiền thuộc Kế toán/Kho;
quyền cụ thể của từng bộ phận còn phải chốt riêng.

Danh sách nguồn dùng phạm vi TableDef hiện có. Bản ghi báo cáo dùng apply_scope:
Staff bản thân, Leader team và bản thân, Manager phòng ban, Admin toàn công ty.
Vận đơn dùng tài khoản delivery của WaybillAssignment làm người phụ trách;
người tạo đơn không thay thế người được giao. Đơn chưa giao có nhóm riêng trong
phạm vi Manager/Admin. Tên nhóm kèm username để phân biệt người trùng họ tên.
Nguồn ngoài quyền trả 403 cả trang lẫn Excel; Tổng quan hiện khối lỗi riêng.
Nội dung nội bộ dùng chung không đổi quyền.

## Cách xem và vận hành

Menu duy nhất **Báo cáo tổng hợp**: chọn một nguồn, ngày, sản phẩm, thị trường; xem theo
ngày, nhân viên, sản phẩm, thị trường, phòng ban. Excel dùng cùng SummaryResult
và bộ lọc; riêng Vận đơn có thêm sheet trạng thái giao hàng. Giữ trần xuất hiện có.
Lịch sử của nguồn đã cấu hình có liên kết Báo cáo tổng hợp giữ nguồn và kỳ.

Tổng quan có ba khối, chung khoảng ngày (mặc định đầu tháng đến hôm nay), mỗi
khối một nguồn. Không cộng doanh số Marketing với Sale. Chưa có nguồn, chưa có
dữ liệu và lỗi tải là các trạng thái riêng. Khối Marketing cũ chỉ làm dự phòng
khi chưa cấu hình nguồn báo cáo; không tính hai lần khi đã có nguồn mới.

Chốt bổ sung 10.09.2026: URL chính là `/bao-cao/tong-hop/` và đường xuất
`/bao-cao/tong-hop/xuat/`, mở trực tiếp kết quả. URL `/bao-cao/hoat-dong/`
và đường xuất cũ chuyển về URL chính, giữ toàn bộ query (kể cả trang/bộ lọc).
Quyết định này thay hướng chuyển trang ban đầu của ADR-022. Thống kê bảng chưa cấu hình vẫn
hoạt động theo quy tắc cũ; tab thị trường
của nguồn chưa có ánh xạ chưa được coi là hoàn thành. Dữ liệu tiền của bảng động
vẫn có giới hạn đơn vị tiền tệ hiện hành (N10), không tự quy đổi hoặc cộng giữa
các nguồn để tạo doanh số công ty.

## Kiểm chứng

Đã nghiệm thu local: 897 test, 24 kịch bản browser, 10/20 client Locust đạt;
p95 trang đọc cao nhất 450 ms. Đã thêm dấu hoàn thành vào từng phần được chốt
trong KNJSC_PROBLEM. Kết quả, lệnh chạy và giới hạn phép đo nằm ở
[test-log](test-log.md) và [CSV final 20](kiem-thu/erp-2026-09-10/final-20.csv).


## Tái lập môi trường kiểm chứng

Các script ERP có mục tiêu riêng, không dùng seed hoặc cổng ứng dụng đang sử dụng.
Database `knjsc_erp_verify` do lượt kiểm chứng này tạo riêng trong Postgres local;
pytest dùng `test_knjsc_erp_verify`. Web thực tế 8020/8021 không nhận tải.

1. Cố định bản mã baseline trước sửa (`c4f82b9`, thư mục
   `storage/erp-verification/baseline/app`). Bản ERP sau sửa nằm tại `final/app`,
   chỉ phủ file ERP lên baseline để không phụ thuộc thay đổi CRM đang dở.
2. Trên database mới rỗng, chạy `app/tests/perf/erp_dataset.py`: 30.000 Marketing,
   30.000 Sale, 40.000 Vận đơn, 80.000 chi tiết; không sửa dataset đã tồn tại.
   Bản ghi nền thuộc 2020–2025, bản nộp của workload thuộc các kỳ 2040+ riêng.
3. Baseline chạy 8134, final chạy 8135; Gunicorn 3 worker × 4 thread, cùng máy và
   Postgres. Dùng StaticFilesHandler chỉ trong bản test cho browser vì không có
   reverse proxy phục vụ static ở hai cổng riêng. Không thêm dependency.
4. Locust dùng `app/tests/perf/locustfile_erp.py`, các biến `ERP_MODE` và
   `ERP_DAY_OFFSET`; chạy 60 giây làm nóng + 300 giây đo, tăng 10 rồi 20 client,
   pacing 1–3 giây. Các vai Staff/Leader/Manager/Admin trải trên ba bộ phận;
   tài khoản chỉ là fixture, một số vai quản lý được nhiều client dùng lại.
5. Kịch bản `scripts/kiem-thu-erp-ui.cjs` nhận `ERP_BROWSER_KIND=sale|mkt` và
   `ERP_BROWSER_MONTH` để chọn kỳ test mới; thêm `kiem-thu-erp-delivery-ui.cjs`
   cho Vận đơn. Dùng Chromium/Playwright có sẵn, kích thước 1440/390.
6. `scripts/kiem-thu-erp-browser-perf.cjs` ghi Chrome trace + Navigation Timing,
   cuộn ngang và thao tác lọc; `app/tests/perf/erp_integrity.py` đối chiếu dữ liệu
   nền và số lần nộp Locust đã xác nhận với database.

Lệnh Locust dùng trong lượt 20 client (từ gốc repo):

```powershell
docker compose -f deploy/docker-compose.yml run --rm -e ERP_MODE=final -e ERP_DAY_OFFSET=2000 --entrypoint locust web -f /storage/erp-verification/locustfile_erp.py --host http://knjsc-erp-final:8000 --headless -u 20 -r 4 -t 360s --stop-timeout 10 --csv /storage/erp-verification/final-20 --html /storage/erp-verification/final-20.html --only-summary
```

Lượt 10 dùng `-u 10 -r 2`, offset 1000. Baseline hợp lệ dùng ERP_MODE=baseline,
host `knjsc-erp-baseline-v1`, offset 600. Cả ba dùng Connection: close để tránh
race kết nối keep-alive của harness local; không che lỗi bằng retry. Hai lượt
baseline trước đó có ConnectionResetError và được loại khỏi nghiệm thu.

Raw HTML, trace, ảnh và JUnit nằm trong `storage/erp-verification` (local).
Các số đo gọn có thể đồng bộ Git nằm trong `docs/kiem-thu/erp-2026-09-10`.
Máy/Postgres dùng chung với môi trường local khác: đây là nghiệm thu local theo
workload xác định, không phải số đo production hoặc benchmark tăng tốc có lặp
thống kê. Nội dung Tổng quan/Vận đơn mới nhiều hơn baseline; không suy tỷ lệ
cải thiện chỉ từ việc đối chiếu hai bảng latency.

## Bổ sung 10.09.2026 — Biểu mẫu và mã nhân sự

- Sửa lỗi `/bieu-mau/` trả 500 khi biểu mẫu hệ thống không có người tạo:
  hiển thị `—`. Giữ quyền quản lý biểu mẫu Manager/Admin.
- Theo yêu cầu mới, ô danh tính trên báo cáo ngày dùng mã đăng nhập cho mọi
  nhân sự, cả hiển thị và ghi dữ liệu. Server ép về tài khoản nộp để chống giả mạo.
  Thay thế Q59 riêng ở đường báo cáo ngày; biểu mẫu thông thường vẫn dùng họ tên.
  Không viết lại báo cáo cũ, không đổi quyền hay cách xác định chủ báo cáo.
- 226 test biểu mẫu/báo cáo đạt, không skip; 16 luồng E2E Sale/Marketing đạt
  trên Chrome 1440/390 với Staff/Leader/Manager/Admin. Đối chiếu database:
  cả 16 báo cáo mới lưu đúng mã. Biểu mẫu Sale test có người tạo NULL.
- Đo Navigation Timing local: Biểu mẫu 35,7–58,4 ms (8 lượt hợp lệ), báo cáo
  ngày 41,6–76,2 ms (16 lượt). Test trần 10 truy vấn danh sách biểu mẫu đạt.
  Đây là kiểm hiệu năng phạm vi bản sửa; không chạy lại tải đồng thời 100k.
