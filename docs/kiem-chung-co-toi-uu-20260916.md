# Kiểm chứng lưới và cờ tối ưu — 16.09.2026

## Phạm vi và nguồn

Đối chứng cố định: `3e5b9a4b74fd55a1cf9230d84323153aa1e10be6`.
Bản ứng viên đổi `master-grid.js`: cuộn cache, tải trước theo hướng,
gom nhảy xa và cập nhật vùng chọn/nhập khi đang lưu. Bổ sung sửa tương thích
metadata tại `optimization.block` sau khi test tái hiện lỗi. Không lấy thay đổi
ngày tháng, báo cáo hoặc backend chưa commit của task ERP.

SHA-256 JS ứng viên trước kiểm tải:
`7ed0015fb0cd223f3d1c2d80f48934fec1a77b7ac31ff0078eb772c3b19e1b6f`.
Nguồn trước/sau được chụp riêng trong `storage/grid-flags-20260916/`.
Thư mục runtime không thuộc Git và có session test; chỉ đưa số đo đã loại
thông tin phiên vào tài liệu bằng chứng.

## Môi trường và cách đo

- Docker Desktop: 12 CPU logic, khoảng 7,63 GiB RAM được cấp cho engine.
- Network riêng `knjsc-gridflags-test`; PostgreSQL 16 và Redis 7 riêng.
- Database `test_knjsc_gridflags_load`: 100.000 đơn, 200.000 dòng sản phẩm,
  30 Sale, 10 Vận đơn; ba thị trường và tám sản phẩm. Không seed database
  local đang dùng hoặc VPS. Khôi phục bản mẫu test giữa các cấu hình.
- Lượt thăm dò ban đầu: 3 Gunicorn worker × 4 thread, giới hạn 2 CPU/768 MiB;
  PostgreSQL: 2 CPU/2 GiB. Số đo này chỉ dùng chẩn đoán, không trộn với
  các lượt nghiệm thu đã chuẩn hóa theo cấu hình VPS bên dưới.
- Lượt `final-*`: 1 worker gthread × 4 thread, CRM 640 MiB; PostgreSQL
  1.280 MiB, shared_buffers 512 MB, work_mem 4 MB, max_connections 40.
  Không giới hạn CPU bằng Docker, tương ứng cấu hình VPS đã đọc ngày này.
  Máy vật lý và tổng RAM vẫn khác VPS; đây chưa phải số đo người dùng thật.
- VPS thực tế đọc bằng `getconf _NPROCESSORS_ONLN`/`free -m`: **2 vCPU,
  3.915 MiB RAM**. Local có 12 CPU logic; không lấy độ trễ local để kết luận
  VPS đủ tải. Bài 300.000 dòng/toàn bảng của task khác là phạm vi khác và
  vẫn giữ kết luận chưa đạt trong tài liệu riêng.
- Host còn chạy ứng dụng và benchmark khác. Ghi nhận giới hạn này khi
  đọc độ trễ và so sánh; không quy mọi biến động server cho JavaScript.
- Locust 9 Vận đơn + 1 Chrome; lượt hỗn hợp thêm 30 Sale, nghỉ 20–40 giây
  giữa đơn. Trang đọc/lưu ô/tạo đơn báo riêng; 60 giây làm nóng bị loại
  khỏi phân vị của lượt đo 300 giây. HTTP nhanh không thay thế đo vẽ lưới.
- Oracle đối chiếu đơn được xác nhận, người tạo, Decimal, hai chi tiết,
  bản sao Vận đơn, giá trị ô và lịch sử sau lượt chạy.
- Cờ kiểm riêng: `RENDER`, `READ`, `READ+SYNC`. Các cờ còn lại giữ tắt.

## Kết quả và trạng thái dừng theo yêu cầu

- 126 bài hồi quy server liên quan chạy qua trên bản ứng viên cố định.
  Chỉ có cảnh báo pytest không ghi cache được vì nguồn mount chỉ đọc.
- Kiểm Node về vùng chọn, quyền sở hữu request, phản hồi cũ và mất quyền đạt.
- Smoke 35 giây: 35/35 đơn lưu và xác nhận đúng, 22 ô đối chiếu đúng,
  không lỗi server/browser. Lượt này không có warmup và không dùng để
  nghiệm thu p95 hoặc tuyên bố cải thiện.
- Đã tái hiện và sửa hai lỗi metadata của READ bằng test thất bại trước:
  thiếu `capabilities`/`schema_version`; danh sách lựa chọn động đổi nhưng
  `metadata_version` không đổi nên trình duyệt không nhận cột mới.
  Dùng cùng metadata/hash/quyền với giao thức cũ, tái sử dụng metadata
  khi serialize. 28 bài liên quan tối ưu/hợp đồng mới chạy qua.
- Chrome/API thật, Admin xem 100.000 dòng, 1440/390px: p95 cuộn liên tục
  92,1/69,1 → 49,2/49,0 ms; cached khoảng 32 ms trước/sau. Ba chuỗi nhảy
  mỗi viewport giảm 13 → 1 request; chờ sau lần nhảy cuối khoảng 190–227 ms
  ở bản mới. Chọn/mở/nhập khi giữ phản hồi lưu đã kiểm, reload/API xác nhận
  dữ liệu lưu. Không lấy thời gian cố ý giữ phản hồi làm độ trễ server.
- `RENDER` thử ngắn chưa có lợi ích rõ: p95 cuộn 49,6/49,3 ms, so với
  49,2/49,0 khi tắt trên cùng bản ứng viên. Chưa có căn cứ bật mặc định.
- `READ` thử hỗn hợp ngắn có lỗi E2E: lưới báo đổi dữ liệu/bỏ vùng chọn
  trong lúc mở editor. 52/52 đơn và các ô đã xác nhận đối chiếu đúng,
  HTTP không lỗi, nhưng browser thất bại nên **không đạt điều kiện bật**.
  `READ+SYNC` qua thử ngắn 65/65 đơn; chưa thay thế kiểm tải dài.
- Các lượt ngắn chuẩn hóa đã kết thúc; dừng kiểm bền theo yêu cầu chủ dự án. Chưa push hoặc bật cờ trên VPS.

Các lượt chính local đã kết thúc trước bài chạy bền:

| Cấu hình | Tải khối p95 | Tìm p95 | Lưu ô p95 | Tạo đơn p95 | Kết quả |
|---|---:|---:|---:|---:|---|
| Đối chứng, 10 Vận đơn | 377,74 ms | 448,82 ms | 147,84 ms | — | Đủ 300 giây, oracle/Chrome đạt |
| Bản mới, 10 Vận đơn | 350,69 ms | 374,37 ms | 144,45 ms | — | Đủ 300 giây, oracle/Chrome đạt |
| Bản mới, 30 Sale + 10 Vận đơn | 316,81 ms | 406,39 ms | 148,57 ms | 217,58 ms | Đủ 300 giây, 367/367 đơn đúng kể cả warmup/drain |

Thay đổi JavaScript không phải thay đổi truy vấn SQL. Biến động API giữa
hai lượt không đủ để tuyên bố server nhanh lên; lợi ích vẽ/tải trước được
đo riêng. Staff Vận đơn thấy khoảng 10.000/100.000 dòng thuộc phân công;
phép đo Admin đơn lẻ mới nhìn đủ 100.000 dòng. 390px là viewport Chrome
desktop, không phải đo phần cứng điện thoại.

137 bài hồi quy cuối trên snapshot ứng viên đạt; E2E lưới chung đạt
1440/1280/390px và zoom 125%: tạo dòng, dán giữ số 0 đầu, Undo/Redo, công
thức, nhập lựa chọn tự do, xóa/khôi phục và thu quyền. Không có skip ở các
lượt này. `final-functional.xml`, `shared/server.log` giữ lệnh/kết quả.

`READ+SYNC` tái hiện lỗi mở editor trong lượt hỗn hợp chính. Lượt bị dừng,
không tính đạt hoặc đủ 10 Vận đơn sau khi Chrome lỗi. Audit riêng xác nhận
Sale thêm một đơn **ngoài quyền Vận đơn**: tổng và ID khối đầu không đổi;
giao thức v1 giữ HTTP 200, v2 dùng token cũ trả 409. Token phụ thuộc mốc
membership của cả bảng, dẫn tới các lần vô hiệu vùng xem không cần thiết.
Giữ READ/SYNC tắt, ghi nợ riêng; không tự đổi mô hình phiên bản/phạm vi.
RENDER chưa chứng minh lợi ích bổ sung nên cũng giữ tắt. Không có cấu hình
cờ mới đạt vòng sàng lọc để đưa vào ba lượt so sánh xác nhận hoặc bật VPS.

Bài chạy bền dùng bản cuộn/chọn ô mới, bảy cờ vẫn tắt; dừng theo yêu cầu
chủ dự án lúc khoảng 15:52, sau **882,58 giây đo (14,71 phút)** và 60 giây
làm nóng. Không tính đạt kiểm bền 60 phút. 939/939 đơn xác nhận tồn tại,
đủ chi tiết/bản sao; Chrome không lỗi. p95 tạo đơn 269,01 ms, tải khối
399,84 ms, tìm 470,67 ms, lưu ô 184,65 ms; đây là số đo một phần local.

Lúc dừng bằng SIGTERM có một poll bị hủy và oracle báo lệch ô 99005.
Kiểm lịch sử xác nhận giá trị đã ack vẫn có; một ghi mới commit khoảng
479 ms sau khi file metrics đóng, khiến giá trị cuối khác acknowledgement
cuối mà harness giữ. Không biến lượt dừng thành đạt hoặc kết luận mất dữ
liệu; giữ lỗi và bằng chứng dừng riêng trong JSON. Chưa kiểm lại bằng một
lượt kết thúc tự nhiên. RAM app cuối khoảng 94,5 MiB; heap Chrome cuối
khoảng 6,2 MB, cache 3 khối. Chưa kết luận ổn định dài hạn.

Phép đo browser **dưới tải**, nhảy vùng xa qua Playwright: p95 chờ dữ liệu
859 → 842 ms giữa hai lượt 10 Vận đơn; hỗn hợp 845 ms. Chọn ô khoảng
71 ms; gồm chi phí điều khiển trình duyệt. Không nhầm với phép đo cuộn
liên tục đơn lẻ ~49 ms, hoặc lấy thời gian edit-to-save có debounce làm
thời gian server. Chưa chứng minh mọi thao tác dưới tải nhanh hơn rõ rệt.

Kết luận hiện tại: các tối ưu hẹp có lợi ích đo được; giữ bảy cờ tắt,
không nghiệm thu toàn bộ CRM hoặc VPS. **Tại thời điểm dừng: chưa commit/push/phát hành**; trạng thái mới bên dưới.

## Sửa sai số của harness, không che lỗi nghiệm thu

Lượt `after-delivery` ban đầu phát hiện ô 20004 không khớp kết quả cuối.
Lịch sử DB cho thấy request mới commit 42 ms sau thời điểm Locust bị cắt,
trong khi harness chỉ giữ acknowledgement cũ. Lượt này giữ nguyên bằng
chứng và **không được tính đạt**. Harness sau đó dùng `--stop-timeout 45`,
ghi mọi lần gửi/ack ô, đối chiếu lịch sử và kết quả cuối. Cửa sổ tính p95
giới hạn đúng thời gian đo, không cộng phần chờ kết thúc vào phân vị.

Lượt `acceptance-before-delivery` bị dừng trong warmup vì Docker vẫn giữ
CPU quota cũ sau `docker update --cpus 0`. `measured_seconds=0`, không phải
lượt đo đạt. Container DB test được dựng lại với **cùng volume test**, rồi
kiểm `NanoCpus=0`; không thao tác container/volume đang dùng của dự án.

## Tái lập

Đọc script trước khi chạy. `scripts/grid-flags-check/prepare.py` đóng băng
nguồn và tạo bản thích ứng của harness `scripts/order-code-check/`.
`run.py setup` chỉ tạo/seed container test riêng; `run.py start <variant>`
chỉ đặt lại database test từ bản pristine, đồng thời giữ nguyên các cờ
ngoài biến thể đang đo. `run.py phase <name> <variant> mixed|delivery
<seconds> [width]` lưu số đo và chạy kiểm toàn vẹn sau tải.

`browser-real.cjs` dùng Chrome/API thật tại `127.0.0.1:18641` trên cả
1440/390px. Request lưu được giữ phản hồi có chủ đích khi đo tương tác,
rồi trả phản hồi, tải lại và đọc API để kiểm giá trị thực sự đã lưu.
Độ trễ tương tác đó không được báo thành thời gian xử lý server.

Bằng chứng tổng hợp: [JSON](verification/grid-flags-20260916.json).
Kiểm tải dài đã dừng theo yêu cầu; kết quả phát hành tiếp theo ghi bên dưới.

## Phát hành theo yêu cầu tiếp theo

Chủ dự án yêu cầu push và cập nhật VPS sau khi đọc kết luận dừng kiểm.
Chỉ phát hành ứng viên đã đo; giữ các cờ thử nghiệm tắt và các giới hạn
kiểm chứng nêu trên. Đã push commit `0907cdd794231b7830dafc9741d5af9e5408c212` lên
`codex/crm-update-solar-ui`. VPS cập nhật lúc khoảng 16:03 ngày 16.09.2026:

- ERP/CRM/worker/heavy/beat cùng image `knjsc-app:0907cdd-grid`, image ID
  `sha256:22c67b5c6409349a8c993b014c1f3cbef385e5bdd51938f572d73915b5566816`.
- Bảy cờ CRM_OPT đều `0`; bộ nhớ/CPU limit và CSS hiện có giữ nguyên.
- Backup: `/opt/knjsc-runtime/release-grid-20260916-160244/`, dump 857.957
  byte, `pg_restore --list` đọc được 733 dòng danh mục. Không restore đè DB.
- `manage.py check` ERP/CRM đạt, collectstatic và nginx reload thành công;
  hai domain HTTPS trả 200. Không migration, seed hoặc tạo đơn test trên VPS.
- Chrome domain thật ở 1440/390px: hash JS khớp đúng snapshot đã đo,
  cuộn/chọn ô đạt, cache 3 khối, không lỗi JS/server. Chưa đăng nhập bị
  chuyển về login; đăng nhập CRM rồi sang ERP không phải đăng nhập lại.
- Năm service đang chạy, restart count 0; không traceback/Internal Server
  Error trong log kể từ lần khởi động được kiểm. Đây là smoke sau phát hành,
  không nghiệm thu tải VPS hay bài bền 60 phút.
- Lần gọi script đầu qua SSH stdin dừng sau bước check đầu do Docker nhận
  stdin; chưa đổi runtime. Chạy lại từ file đã hoàn tất đầy đủ. Script đã
  thêm `--interactive=false`. Probe chọn ô được sửa chờ frame UI trước
  assert; không thay code ứng dụng để làm smoke đạt.

[Bằng chứng phát hành đã bỏ thông tin đăng nhập](verification/grid-release-20260916.json).
Các ghi chú “chưa push/VPS” ở những biên bản cuộn trước là lịch sử tại lúc đo;
trạng thái phát hành đoạn này thay thế chúng. Phần ERP/ngày của task khác vẫn
ở working tree local, không được đưa vào commit này.
