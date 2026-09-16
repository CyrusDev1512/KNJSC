# Báo cáo ERP — local 16/09/2026

## Phạm vi đã duyệt

Chủ dự án yêu cầu triển khai local trước: sửa lỗi thêm sản phẩm báo cáo,
bổ sung lọc nhân sự cho Báo cáo tổng hợp và tạo mẫu đã nộp để xem lịch sử.
Ngày 16/09 chốt Vận đơn chỉ cần báo cáo công việc ngày tại chức năng Báo cáo:
Ngày báo cáo, Nhân sự tự nhận diện, Công việc đã thực hiện, Kết quả,
Vướng mắc/đề xuất. Không thêm chỉ tiêu tiền, đối soát hoặc nguồn tổng hợp mới.

## Đã triển khai local

- Tổng hợp: lọc Team/nhân sự theo dữ liệu được phép xem; tìm tên không dấu;
  Team và nhân sự nằm cạnh nhau khi nhóm theo người. Kẻ ô, tổng ở đầu bảng,
  bảng cuộn riêng; giữ chỉ tiêu, công thức và phạm vi quyền cũ.
- Lọc áp trước tổng hợp, thống kê trạng thái và xuất Excel. Đổi nguồn trên UI
  bỏ lựa chọn team/nhân sự cũ, tải danh mục mới khi bấm Áp dụng.
- Metadata `bc_van_don_ngay` → `bao_cao_van_don_ngay`, năm trường đã duyệt;
  dùng service nộp/khóa/lịch sử hiện có, không ghi vào bảng đơn hàng.
- Lịch sử không gắn nhãn Doanh số khi bản ghi không có giá trị này; số 0
  vẫn hiển thị đúng. Không đổi điều hướng nộp/lịch sử.
- 36 DailyReport mẫu được nộp qua service: mỗi bộ phận 12, 2 team/4 người,
  cho 14–16/09/2026. Tiền tố tài khoản `mau_erp_1609_`, tài khoản không hoạt
  động và không có mật khẩu đăng nhập. Chạy lại không nhân bản báo cáo.

Lệnh metadata/sample đã chạy trên dịch vụ web local:

```powershell
docker compose -f deploy/docker-compose.yml exec -T web python manage.py configure_delivery_daily_report
docker compose -f deploy/docker-compose.yml exec -T web python manage.py seed_local_report_history
```

Command sample từ chối settings ngoài dev/test. Không dùng command sample
trên VPS. Command metadata chỉ tạo cấu hình, không tạo dòng nghiệp vụ.

## Kiểm chứng

```powershell
docker compose -f deploy/docker-compose.yml run --rm -e RUN_MIGRATIONS=0 web pytest reports/tests -q --maxfail=2 --junitxml=/storage/reports-20260916-tests.xml
docker compose -f deploy/docker-compose.yml run --rm -e RUN_MIGRATIONS=0 web pytest reports/tests/test_product_options.py -q --maxfail=1
```

- Suite báo cáo: **111 passed, 0 failed/error/skipped**, XML tại
  `storage/reports-20260916-tests.xml` (không theo Git).
- Hai bài thêm sau đó: **2 passed**, đi theo chính URL thêm sản phẩm được
  render trong form Marketing/Sale; quản lý thêm được, Staff gọi trực tiếp
  bị 403 và không tạo sản phẩm.
- Có kiểm Staff/Leader/Manager/Admin với bộ lọc người; từ chối ngoài team,
  Excel khớp tổng, Vận đơn dùng người được giao thay vì người tạo.
- Delivery form: cấu hình lặp không trùng; tự nhận diện nhân sự dù đầu vào
  giả mạo; lịch sử đọc được; Sale không mở form/dữ liệu ngoài quyền.
- Sample: đủ 36 báo cáo/12 người/6 team, chạy lại không thêm; chặn production.
- Hai bài ngân sách truy vấn Sale/Vận đơn vẫn đạt trần 10 với trang không
  chọn người/team. Danh mục team/người dùng chung một truy vấn; khung trang
  tái sử dụng department đã được JOIN. Không tuyên bố đây là đo tải lớn.
- Trình duyệt local đã đăng nhập: thêm sản phẩm Sale thành công, tìm `binh`
  ra Bình, lọc Bình chỉ còn một dòng (165 Mess/18 đơn/405 doanh số), đổi
  Sale → Marketing không gửi ID người cũ. Đọc đủ 12 mẫu Vận đơn và năm
  trường trong form; nhãn Doanh số đã biến mất khỏi lịch sử Vận đơn.
- Responsive tổng hợp: 1440px không tràn document; 390px document=390px,
  lưới rộng 1823px cuộn trong khung 335px. Lịch sử 390px không tràn document.
- `git diff --check` đạt. Chưa chạy toàn bộ suite ngoài reports, chưa kiểm
  đủ bàn phím/zoom/theme tối; không dùng kết quả này thay nghiệm thu VPS.

## Lỗi 404 còn mở

Chưa tái hiện được lỗi thêm sản phẩm trên domain thật. Local Sale đã bấm
thêm thành công; Marketing local hiện là cột text nên không có nút thêm.
Trên fixture Marketing kiểu choice, endpoint hoạt động và kiểm quyền đúng.
Chẩn đoán chỉ đọc ứng dụng VPS: đường dẫn render đúng, gọi view với nhãn
rỗng trả 400 ở cả hai nguồn. Điều này **không chứng minh** request qua proxy
và phiên người dùng thật không còn lỗi 404.

Đang chờ xác nhận lỗi xảy ra ở “＋ Thêm mới…” của ô Sản phẩm hay thao tác
khác. Cần request/URL và vai trò gây lỗi để chốt nguyên nhân; chưa sửa đoán,
chưa đánh dấu hạng mục 404 hoàn thành.

## Xem thử và bàn giao

- `http://localhost:8020/bao-cao/?bieu_mau=bc_van_don_ngay`
- `http://localhost:8020/bao-cao/lich-su/?tim=mau_erp_1609_`
- `http://localhost:8020/bao-cao/tong-hop/?nguon=bao_cao_sale&nhom=person`

Chưa commit/push/VPS. Working tree còn thay đổi CRM/orders từ tác vụ khác;
không gộp chúng vào diff báo cáo và không reset chúng.

## Bổ sung theo phản hồi 16/09 — ẩn bộ lọc và toàn màn hình bảng

Chủ dự án yêu cầu panel trái bật/tắt được và bảng mở full view. Local đã có
nút Ẩn/Hiện bộ lọc và Toàn màn hình/Thoát toàn màn hình. Chế độ tập trung
chiếm vùng hiển thị của tab, ẩn header/dock/nền, không gọi Fullscreen API.
Thanh gọn giữ tên nguồn, kỳ báo cáo, bộ lọc, xuất Excel và nút thoát;
phân trang vẫn dùng được. Mở bộ lọc trên desktop chia chỗ với bảng, mobile
mở panel có cuộn riêng. Esc đóng panel đang mở trước, lần tiếp theo thoát.

Không tạo lại bảng/form khi vào/ra. Chọn người, điều kiện chưa Áp dụng và
dữ liệu giữ nguyên; trạng thái bố cục được giữ trong sessionStorage của tab
(chỉ hai boolean, không lưu dữ liệu người/khách hàng). Áp dụng lọc khi đang
full view vẫn ở full view sau tải trang; thoát trả trạng thái panel thường.

Kiểm trước sửa: trình duyệt chưa có cả hai nút. Kiểm sau sửa trực tiếp:
ẩn panel mở rộng bảng; khung focus đúng (0,0,1440,900), header ẩn và
fullscreenElement rỗng; nội dung bảng trước/sau giống nhau. Esc hai bước,
giữ chữ tìm `binh`, chọn Bình rồi Áp dụng vẫn focus, số liệu 165/18/405.
Mobile 390×844: view bằng viewport, document không tràn ngang, lưới 902px
cuộn trong khung 390px, panel 320px không che các nút điều khiển.

Hồi quy sau đổi template: **113 passed, 0 failed/error/skipped**:
`docker compose -f deploy/docker-compose.yml run --rm -e RUN_MIGRATIONS=0 web pytest reports/tests -q --maxfail=1 --junitxml=/storage/reports-focus-20260916-tests.xml`.
Các thao tác JS ở trên là kiểm trình duyệt, không gộp vào số pytest.


## Bổ sung 16/09 — ngày, chủ báo cáo, quyền sửa và Marketing

Phạm vi được duyệt tại ADR-032. Đã áp dụng migration reports.0003 local,
chạy configure_erp_reports để bổ sung metadata; không ghi lại hàng loạt
lịch sử. Chỉ mẫu Marketing /bao-cao/52/ đã được sửa qua UI để xem kết quả.
Mẫu này giữ ngày/người nộp; phiên bản mới có lịch sử người sửa và giá trị
trước/sau. Bản ghi đã nộp không sửa/xóa qua đường lưới chung.

- Shared date-inputs.js hiển thị DD/MM/YYYY, chuyển về ISO khi gửi, ngày giờ
  hiển thị Việt Nam và truyền UTC. Django Admin không đổi. Grid cũng dùng
  adapter này; ngày sai bị chặn trước khi đưa vào hàng đợi lưu.
- Ngày báo cáo mới tự lấy hôm nay phía server; danh tính không lấy từ POST.
  Leader trong team, Manager trong bộ phận, Admin toàn hệ thống; truy cập
  URL trực tiếp ngoài quyền bị từ chối. Sửa giữ ngày/chủ/thời điểm nộp gốc.
- Marketing bổ sung hai đầu vào Doanh thu/Hóa đơn; CPO, Giá Mess,
  CPQC/Doanh số, Hóa đơn/Doanh thu (= Giá Mess/CPO), AOV theo tên chỉ tiêu.
  Tính với Decimal trước khi làm tròn; mẫu số 0/thiếu trả trống.
- Quốc gia/thị trường dùng danh mục hệ thống, tiền suy ra từ danh mục đó.
  Báo cáo tổng hợp/dashboard/Excel không cộng tiền khác đơn vị hoặc thiếu
  đơn vị; có thông báo. Dữ liệu cũ thiếu đơn vị không tự gán để tránh sai nghĩa.

### Kiểm thử thực tế

- TDD tái hiện trước sửa: giả ngày được chấp nhận, Leader sửa 404, đường
  lưới cho sửa báo cáo đã nộp, thiếu trường Marketing, cộng CAD với USD.
- Lượt rộng reports/forms_builder/CRM: 607 passed, 2 failed, 18 deselected.
  Một lỗi query metadata phát sinh đã sửa; lượt nhóm cuối chạy lại toàn bộ
  reports và các nhóm form/lưới liên quan đạt **256 passed (47,04s)**:
  `docker compose -f deploy/docker-compose.yml run --rm -e RUN_MIGRATIONS=0 web pytest reports/tests forms_builder/tests/test_bieu_mau.py crm/tests/test_master_grid.py crm/tests/test_master_nine.py crm/tests/test_shared_integrity.py crm/tests/test_kiem_tai.py -m "not cham and not trinh_duyet" --maxfail=2 --junitxml=/storage/reports-focused-final-20260916.xml`.
- Lỗi còn lại `test_export_import_roundtrip_and_preview_ambiguous`:
  test đòi nhập lại mã đã có, service từ chối trùng. Tái hiện cùng lỗi trên
  app trích từ HEAD 5ce53f3 bằng git archive, mount riêng; không sửa/reset
  checkout hay database local. Đây là lỗi nền, không báo suite toàn xanh.
- `node scripts/kiem-thu-date-inputs.cjs`: đạt các ca ngày hợp lệ/sai,
  năm nhuận, roundtrip ISO và ngày giờ Việt Nam.
- `manage.py check`, `makemigrations --check --dry-run`: đạt. Test migration
  đảo reports trên database test riêng rồi khôi phục toàn bộ leaf migrations.
- Chrome local: ngày lọc gõ 15/09/2026 gửi query ISO đúng; mẫu mới đổi Canada
  hiển thị CAD; sửa báo cáo 52 và mở lịch sử trước/sau thành công.
- Marketing mẫu: Mess 100, CPQC 200, đơn 20, doanh số 1000, doanh thu 900,
  hóa đơn 75; CPO 10, Giá Mess 2, hai tỷ số 0,2, AOV 50. Giữ chủ và ngày nộp.
- Lưới local: nhập 31/02/2026 bị báo lỗi, 29/02/2024 hợp lệ; Esc hủy nháp,
  không tạo dữ liệu thử. Form sửa mobile 390×844 đọc được, không tràn ngang.
- Ảnh: `storage/reports-amendments-20260916/marketing-history.png` và
  `storage/reports-amendments-20260916/edit-mobile.png`.

Chưa kiểm tất cả màn hình/ngày giờ trên mọi trình duyệt, zoom 125/200%,
full suite toàn ứng dụng hoặc luồng ghi VPS trong lượt này. Các kiểm tra
trình duyệt thủ công không tính vào số pytest. Phần báo cáo chưa push/VPS.


## 16/09/2026 — Sửa phần ngày hiển thị trong ô lưới bị sót

Ảnh phản hồi vẫn hiện YYYY-MM-DD: adapter trước chỉ đổi ô nhập. Đã sửa
CRM grid_service.display_value và nhãn bộ lọc thành DD/MM/YYYY; ngày giờ
hiển thị Việt Nam. Giá trị JSON/CAS/lọc giữ ISO. Nháp JS cũng dùng D/M/Y
ngay khi kết thúc nhập, không chờ server; không đổi màu/định dạng tiền.
TDD trước sửa: ba ca ô ngày/ngày giờ và một ca nhãn lọc thất bại đúng lỗi.
Sau sửa: 34 test (grid_date_display, master_grid, bang_tinh_dinh_dang) đạt,
0 failed/error/skipped. Node kiểm đường cellValue thực tế của nháp/hoàn tác
và UTC→Việt Nam đạt. XML: storage/grid-date-display-20260916.xml.
Chrome CRM local bảng Marketing: ô 14/09/2026, 15/09/2026, 16/09/2026;
chip 01/09/2026–30/09/2026, query vẫn ISO. Ảnh lưu tại
storage/reports-amendments-20260916/grid-date-display.png.
Chỉ sửa local, chưa push/VPS; không khẳng định ảnh phản hồi chụp ở môi trường nào.
