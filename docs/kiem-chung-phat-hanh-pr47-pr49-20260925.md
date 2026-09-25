# Phát hành VPS main — PR #47, #49 — 25.09.2026

## Kết quả và giới hạn

**VPS đã cập nhật** từ `knjsc-app:9c4d285-main` lên `knjsc-app:a23573d-main`.
Checkout `/opt/knjsc` ở `main`, SHA `a23573d7aaaabac1eedfa9ec169d68c7b33b2fd6`, sạch.
Cả năm dịch vụ `crm`, `erp`, `worker`, `heavy`, `beat` dùng cùng image.
Image ID: `sha256:75604dcf1b5a6a77a81f152b8d9b29ace7011886cea3cead9cec35b03c7ecfb1`.

Bảo trì ngày 25.09: **09:35:23–09:36:26 giờ Việt Nam, 63 giây**.
Theo dõi tới **09:51:26**, mẫu cuối 901 giây sau mở truy cập: không HTTP 5xx,
không restart, hai domain trả 200 ở trang đăng nhập. Hai lỗi `DisallowedHost`
do truy cập trực tiếp bằng IP đã được kiểm và tách riêng; không nới `ALLOWED_HOSTS`.
Hai hàng đợi `celery`, `crm_heavy` xử lý được tác vụ probe không ghi dữ liệu/gửi tin.

Các kiểm chính và đối chiếu dữ liệu đạt. **Chưa đóng toàn bộ danh sách nghiệm thu**:
390 px trên domain chưa xác nhận, đăng nhập/đổi mật khẩu tài khoản mới chỉ kiểm trên
diễn tập, cảnh báo trùng điện thoại và lọc cột ẩn chưa hoàn tất bằng UI domain.
Không suy từ CI hoặc HTTP 200 thành tất cả thao tác trình duyệt đều đạt.

## Bằng chứng trước phát hành

- Chốt đúng SHA trên `main`; chứa PR #47, #49. Phần sau `6b29d97` chỉ gỡ tài liệu
  phát hành lỗi thời. Không sửa ứng dụng, dependency, API hoặc migration đợt này.
- [CI 36084889618](https://github.com/CyrusDev1512/KNJSC/actions/runs/36084889618)
  đúng SHA: 2.697 đạt / 7 skip / 41 không chọn; E2E 27 đạt / 2 skip;
  nhóm trình duyệt còn lại 1 đạt / 8 skip / 2.707 không chọn / 1 cảnh báo.
  CI của `6b29d97` bị hủy, không tính đạt. Skip gồm bài tải 300.000 dòng,
  fixture dòng trống và các bài cần Chrome host/proxy riêng; không chạy kiểm tải.
- Giữ hai khóa `deployment.lock`, `overview-release.lock` trong suốt phát hành.
  Checkout và runtime trước cập nhật được chụp; không reset thay đổi của phiên khác.
- Build Dockerfile hiện có với `INSTALL_DEV=0`. Hai Compose thực tế giữ nguyên byte;
  `.env` chỉ đổi `KNJSC_IMAGE`. Giữ giới hạn 2 CPU/4 GB, domain và cờ tính năng.

## Diễn tập và cấu hình

Database được phục hồi trong mạng Docker `--internal`, không publish cổng,
không chạy beat/worker hay gửi thông báo. Kiểm Django không có cảnh báo;
`makemigrations --check --dry-run`, `migrate --plan`, `migrate --check` không có
thay đổi model/migration cần áp dụng. Đo nhóm check/cấu hình: 21 giây.

Chạy `configure_erp_reports` hai lần. Lần hai không đổi nội dung metadata sau khi
loại timestamp tự cập nhật. Tác động thực tế lần đầu:

- `FormField` ID 5, 6, 7, 8, 16, 17, 18 chuyển `required=true`.
- Gỡ `FormField` 24 và `FormTableLink` 24 (ô Hóa đơn khỏi form nhập).
- Giữ cột Hóa đơn và toàn bộ dữ liệu cũ, nguồn báo cáo và cột ẩn.

Django Client trên bản sao: 36 đường GET và các luồng ghi/quyền chính đạt;
Staff/Leader/Manager/Admin, nộp/sửa/bỏ/khôi phục báo cáo, giữ danh tính/ngày,
tạo đơn, lưu ô và xung đột phiên bản 409. Mỗi nhóm ghi dùng transaction rollback.
PR #47 kiểm tạo không email, đăng nhập bằng mã, bắt đổi mật khẩu tạm, đổi thành công,
sau đó đăng nhập bình thường và sửa ngày sinh.
PR #49 kiểm thiếu riêng từng trường phía server, 0 hợp lệ, team hợp lệ/khác bộ phận/
không tồn tại; team chọn ghi vào cả dòng và báo cáo. Leader đúng team 200,
ngoài team 404; Staff không sửa, Manager/Admin trong phạm vi được phép.

Image cũ `9c4d285-main` vượt 29 đường GET và nhóm ghi cơ bản với metadata mới;
phục hồi riêng metadata rồi kiểm image cũ lần nữa đạt. Script phục hồi kiểm đối chiếu
trước ghi, chỉ phục hồi các hàng bị thay đổi, không phục hồi toàn database.
Metadata phục hồi khớp bản trước; sau đó áp lại cấu hình mới và kiểm lại đạt.

## Thực hiện và sao lưu

HTTP 503 trên hai domain, dừng beat, ngừng nhận request, drain rồi dừng năm dịch vụ.
Giữ database, Redis và các volume. Backup cuối được kiểm checksum, phục hồi database
vào `knjsc_restore_final` và đối chiếu hash. Fast-forward đúng SHA đã chốt;
`RUN_MIGRATIONS=0`, kiểm Django/migration, chạy rõ `configure_erp_reports`,
`collectstatic`, khởi động đồng bộ năm dịch vụ; nginx test/reload trước mở lại.
Không seed, không gán lại nhân sự/team, không cấu hình lại bảng vận đơn.

Hồ sơ riêng trên VPS (không đưa dữ liệu/runtime secrets vào Git):

`/opt/knjsc-runtime/release-main-20260925-a23573d/`

| Tệp | Nội dung |
|---|---|
| `database.dump`, `storage.tar.gz`, `static.tar.gz`, `runtime.tar.gz`, `backups.sha256` | Backup ngay trước cập nhật và checksum |
| `metadata.before.json`, `metadata.after.json` | Biểu mẫu, liên kết, nguồn báo cáo, cột |
| `business.before.json`, `business.backup.normalized.json`, `business.final.excluded.json`, `business.verified.json` | Đối chiếu dữ liệu và ngoại lệ kiểm thử |
| `monitor.jsonl`, `monitor.passed`, `queue.verified.json`, `final.passed` | Giám sát, hàng đợi, trạng thái cuối |
| `rollback.sh`, `restore_metadata.py` | Quay lui image/static và metadata có kiểm đối chiếu |

Đã dọn đúng ba container diễn tập, mạng riêng và volume DB ẩn danh của chúng;
giữ các backup. Đã nhả cả hai khóa phát hành. Không đụng volume production.

## Kiểm domain thực tế

| Mục | Kết quả thực tế |
|---|---|
| PR #47 | Admin thấy form tạo không Email/Ngày sinh; tạo tài khoản mẫu không email, sửa ngày sinh 15/01/1999 và tải lại còn. Luồng mật khẩu mới chỉ kiểm trên diễn tập; không tuyên bố đã bấm đổi trên domain. |
| PR #49 / Marketing | Phiên người dùng đăng nhập MKT: dropdown 5 team, mặc định theo hồ sơ; Marketer/ngày tự nhận diện. Không ô Hóa đơn nhập. Thiếu từng Số Mess/CPQC/Số đơn/Doanh số bị browser chặn; server đã kiểm trên diễn tập. Nộp bốn giá trị 0, chọn team khác hồ sơ, lịch sử và database đúng team. Staff không có nút sửa. |
| Bố cục | 1440 px: một thẻ ngang, không tràn ngang; có ảnh hiển thị trong task. Yêu cầu viewport 390 px không được công cụ áp dụng (đo vẫn 1440/1280), nên **chưa đạt kiểm domain điện thoại**. |
| Sale / Vận đơn | Admin mở form Sale có ba số bắt buộc, không CPQC; form báo cáo ngày Vận đơn đúng ba vùng nội dung. Màn sửa báo cáo cũ mở được, giữ ngày/người nộp. |
| Tổng hợp / lịch sử | Đọc báo cáo cũ và Hóa đơn cũ; lọc ngày/nhân sự, chuyển Gộp, mở/thoát toàn màn hình, xuất Excel phát sinh download. Chưa kiểm riêng thao tác lọc sản phẩm trên domain. |
| CRM | Thư mục chỉ nhóm Vận đơn; tạo đơn thử; lưu Bang, chuyển toàn màn hình khi đang chờ lưu, tải lại giữ giá trị; ghi chú sáu dòng cao 122 px, cột ghim đồng bộ chiều cao; popup xác nhận bốn cột sản phẩm ẩn. |
| Lỗi ghi/quyền | CAS 409 và quyền ngoài phạm vi kiểm trên bản sao. Chưa hoàn tất UI cảnh báo trùng điện thoại/lọc cột ẩn trên domain, không đánh dấu đạt. |

Ảnh PR #47 (Sửa hồ sơ) và PR #49 desktop đã hiển thị trực tiếp trong task;
không lưu ảnh có thông tin tài khoản vào repository.

## Dữ liệu kiểm thử và đối chiếu

- User 27 / profile 25 (`TESTPR492509`): đã khóa bằng account service, giữ audit.
- Order 15 / DataRecord 6802 (`DH-2509-0001`): ghi nhãn mẫu không giao;
  đã bỏ bằng UI, xác nhận soft delete cả đơn/dòng, nội dung ô đã lưu vẫn giữ.
- DailyReport 9 và 10: các số đều 0, đã bỏ bằng UI và xác nhận soft delete cả dòng.
  Bản 9 có nhãn kiểm PR49 và team 02; bản 10 phát sinh trong thao tác xác thực,
  chưa có ghi chú nhãn, được nhận diện bằng ID/thời điểm trong biên bản này.

Đối chiếu hash từng model sau loại đúng các ID trên và các đối tượng con của đơn:
132 dòng dữ liệu cũ, 7 khách, 14 đơn, 17 chi tiết đơn, 14 waybill item, 8 báo cáo cũ
giữ nguyên; chứng từ, ảnh chứng từ, phân công, revision cũng khớp. Auth giữ nguyên
trừ `last_login`; kiểm từng trường profile cũ chỉ đổi `last_login_at` của profile 24.
Không bỏ qua email, ngày sinh, quyền hoặc team trong phép đối chiếu này.

## Phát hiện và việc còn lại

1. **Ô Team cũ bị trùng:** metadata mẫu còn `team_mau` trong form Marketing/Sale,
   nên có textbox Team bên cạnh dropdown Team mới. Cột mẫu có trước phát hành,
   không phải cấu hình tự sinh thêm đợt này. Dropdown ghi đúng quyền/team nhưng
   textbox gây nhầm; chờ duyệt phương án ẩn trường khỏi form và giữ dữ liệu cũ.
2. Tìm kiếm chung bằng mã đơn thử chưa ra kết quả. `ColumnMap.searchable_paths`
   chỉ tìm các cột tách có meaning/index, không tìm mọi khóa JSON. Mã search không
   đổi trong đợt này; cần rà hợp đồng tìm kiếm riêng, chưa kết luận là hồi quy PR.
3. Hoàn tất những mục UI domain còn trống trong bảng trên, nhất là điện thoại 390 px.
   Không dùng bằng chứng bố cục của bản local cũ thay cho kiểm domain đợt này.

## Quay lui

Mốc quay lui **`knjsc-app:9c4d285-main`**. Dùng hồ sơ runtime ở trên: bật 503/drain,
kiểm metadata hiện tại chưa bị phiên khác sửa, phục hồi riêng thay đổi metadata đã
diễn tập, trả image/static cũ rồi kiểm nginx và ứng dụng trước mở truy cập.
`rollback.sh` đã kiểm cú pháp; các thành phần phục hồi metadata/image cũ đã diễn tập,
không chạy rollback toàn bộ trên production. Đổi image đơn thuần không phục hồi
ô Hóa đơn hay cờ required. Không đảo migration, không tự phục hồi toàn database.
Nếu phát hiện hỏng dữ liệu: giữ bảo trì, báo phạm vi trước khi phục hồi.
