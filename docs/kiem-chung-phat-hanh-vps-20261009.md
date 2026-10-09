# 09.10.2026 — Phát hành main e979323 lên VPS

## Trạng thái và phạm vi

Đã chuyển hệ thống thật sang `e979323f15e399091705a09337a8d461e726c040`, image
`knjsc-app:e979323-main-r2`. Đã hoàn tất 15 phút theo dõi và kiểm các luồng chính
bằng phiên Admin trên domain thật; giới hạn kiểm chứng được ghi riêng bên dưới.
Không thay mã ứng dụng trong lượt phát hành.

Chủ dự án xác nhận **local đạt** trên bản xem thử riêng đúng SHA, sau đó duyệt
tag `-r2` và cho bảo trì ngay khi ít người dùng. Checkout cũ sạch, nhánh `main`,
SHA `c7065feeb5bfb7d6ce148e35229877f5115d3d3e`; cả năm ứng dụng dùng
`knjsc-app:c7065fe-adr046`. Đây là image quay lui.

- Diff với tree diễn tập `415f46271828fe4d002180f7ced57c9e346c32c6`: đúng 23 tệp;
  không đổi migration, requirements, Dockerfile hoặc entrypoint trong đoạn diff này.
- [CI đúng SHA](https://github.com/CyrusDev1512/KNJSC/actions/runs/37876931582):
  `completed/success`; chính 3.128 đạt/7 bỏ qua, E2E 65 đạt/2 bỏ qua, nhóm trình duyệt
  bổ sung 19 đạt/9 bỏ qua. Đây là kết quả CI, không phải chạy lại toàn suite trên VPS.
- Image ID: `sha256:a8ce068c33eb440b0de6bc7e629294ec3ef8dcc633dba43d37aef7be2a036cd6`.
  Build đúng SHA bằng Dockerfile hiện có, `INSTALL_DEV=0`.
- Hai khóa `deployment.lock`, `overview-release.lock` được giữ khi thực hiện từng
  script; script chuyển bản tiếp tục giữ khóa trong thời gian theo dõi. Không xóa khóa.
- Không seed, gán lại nhân sự/team, bật cờ tối ưu, đổi domain hoặc chạy kiểm tải lớn.

Các skip/cảnh báo CI được giữ riêng:

- Bảy bài chính: fixture đo cuộn, executive statistics capacity, master capacity,
  master nine capacity/storage, master row capacity, optimization capacity;
  đều yêu cầu phép đo/môi trường riêng.
- Hai E2E: nhập ghi chú vào dòng trống cuối bảng (fixture không có quyền/dòng trống),
  và bài ghi chú 300k cần bật riêng `KN_GHI_CHU_300K`.
- Chín bài browser server/Chrome host: shared login, account, feedback, market
  currency, master, order hub, payment, shared grid, statistics labels; thiếu
  môi trường host/proxy/DB riêng nên không chạy trong CI này.
- Nhóm browser bổ sung có cảnh báo teardown DB test còn một kết nối; CI vẫn
  `success`. Các action Node cũng có cảnh báo deprecation. Không tính các mục
  này là đã nghiệm thu; không sửa môi trường CI trong lượt phát hành.

## Diễn tập và xử lý lỗi đóng gói

Tag đầu `knjsc-app:e979323-main` **không được phát hành**. Export nguồn với umask
077 khiến entrypoint nguồn mode 600, vào image thành 711/root và người dùng ứng dụng
không đọc được script. Giữ nguyên tag lỗi để truy vết; xuất lại nguồn với mode Git
đúng trong thư mục cha quyền 700, build tag mới do chủ dự án duyệt. Entry point r2
mode 755; không sửa Dockerfile hay mã nguồn.

Backup chuẩn bị tại `/opt/knjsc-runtime/release-e979323-prep-20261009-103845`.
Các lượt chuẩn bị 102145/102211 không hoàn tất, không dùng làm backup phát hành.
Lượt đầu bị tiến trình Docker đọc mất stdin của script; lượt sau không đọc được
chứng chỉ bằng tài khoản host. Lượt hoàn tất lấy chứng chỉ qua mount sẵn có của
proxy, không đổi quyền khóa.

Diễn tập trên project Compose riêng, database/storage/static/broker/cache riêng,
không publish port, không chạy worker/beat gửi thông báo. Mạng Docker không được
cấu hình chặn toàn bộ egress; không tuyên bố cách ly Internet tuyệt đối.

| Kiểm tra trên bản sao | Kết quả |
|---|---|
| Check deploy CRM và ERP, `--fail-level WARNING` | Đạt cả hai |
| Migration plan | Đúng ba migration bên dưới; migrate khoảng 4 giây |
| Ba lệnh cấu hình và static `--clear` | Đạt |
| Đối chiếu | 44 DataRecord giữ ID, 19 bảng nghiệp vụ giữ hash; 11 nhãn tiền MKT sang VND |
| Quyền tài khoản cũ | Giữ nguyên; chỉ thêm bốn quyền Django cho SubmissionReceipt |
| Bảy vai trò: Sale, Marketing, Vận đơn, Leader, Manager, CEO, Admin | 50 lượt kiểm HTTP qua Django Client về Quản trị/Cột trên hai URLconf đạt |
| Lên đơn | Gửi lại mã lần nộp trả cùng đơn, không tạo lặp |
| Lưới | Sửa ô NFD được; đọc lại còn giá trị; CAS lỗi 409 không ghi đè; mã trùng bị 400 |
| Báo cáo MKT/Sale/Vận đơn | Nộp, chống nộp lặp, lịch sử, Gộp/Không gộp và xuất XLSX đạt |
| Dữ liệu mã trùng trước nâng cấp | Database probe riêng: migrate bị chặn trước cả ba migration |
| PostgreSQL `panic` | Tạo lại DB diễn tập khoảng 7 giây; SHOW đúng giá trị |
| Quay lui image cũ | Hai lệnh configure + static khoảng 10 giây; lưới, lọc, nộp MKT/Sale, lịch sử/tổng hợp đạt |
| Tiến lên lại sau quay lui | Dữ liệu nghiệp vụ/migration giữ nguyên; không còn migration chờ |
| Static sau quay lui | Hai JS cũ khớp image; `phan-trang.js` không có trong image cũ và đã được `--clear` loại khỏi static |

Dữ liệu thử của smoke nằm trong transaction rollback trên bản sao; không sửa
tài khoản hoặc dữ liệu khách trên production. Đây là kiểm endpoint/service, không
thay cho kiểm thao tác chuột, bàn phím và cuộn trong trình duyệt. Các bài trình duyệt
TL-77/78 và ma trận rộng hơn có bằng chứng CI/lượt diễn tập 08.10, không ghi là đã
chạy lại qua UI trên bản sao này. Đã dừng hạ tầng diễn tập sau kiểm, giữ volume.

## Sao lưu cuối và trình tự thực tế

Mọi lệnh chạy từ `/opt/knjsc-runtime`, Compose luôn có đủ
`-f compose.yml -f compose.vps.yml`. Giữ nguyên giới hạn VPS 2 CPU/4 GB.

- Cookie domain: cả hai biến có mặt, không ghi giá trị vào log bàn giao.
- Bốn câu SQL trước bảo trì: `0|0`, `0|0`, `0|0`, `0`.
- Database pending/running, worker active/reserved/scheduled, broker queued/unacked:
  đều bằng 0 trước bảo trì và sau drain. Hai worker đều phản hồi.
- Bật 503 giữ TLS, dừng beat, drain rồi dừng đủ năm ứng dụng trước migration.
- Bảo trì: **11:04:01–11:06:26 giờ Việt Nam**, tương ứng 04:04:01–04:06:26 UTC:
  **2 phút 25 giây**. Không lấy riêng thời gian migration làm thời gian gián đoạn.
- Backup cuối: `/opt/knjsc-runtime/release-e979323-live-20261009-110341` (quyền 700),
  gồm DB, media, static, chứng chỉ, `.env`, hai Compose, nginx template/rendered,
  snapshot metadata và trạng thái trước/sau. Không đưa các tệp này vào Git.
- SHA-256 `database.dump`:
  `f7729527a192029863bcae7f37461ddf85af16dea709a8fb547758987d5713c9`.
  `SHA256SUMS` chứa các archive/cấu hình còn lại; kiểm checksum và gzip đạt.
- `pg_restore --exit-on-error` vào DB riêng đạt; snapshot phục hồi khớp toàn bộ
  **51 bảng**, gồm số dòng/hash, metadata, dữ liệu và danh sách migration.
- Thêm đúng cặp `-c`, `log_min_error_statement=panic` vào `db` của override thực tế;
  tạo lại **chỉ DB** bằng `up -d --no-deps --wait db`, SHOW xác nhận `panic`.
- Fast-forward checkout tới đúng SHA chốt; không reset, không kéo thêm phiên bản.
- `.env` vẫn trỏ image cũ khi migrate bằng biến `KNJSC_IMAGE` theo lệnh; ép
  `RUN_MIGRATIONS=0`, `PGOPTIONS='-c lock_timeout=10s'`.

Ba migration đã áp:

1. `core.0007_submission_receipt`
2. `forms_builder.0017_datarecord_val_order_code`
3. `reports.0006_bao_cao_mkt_tien_viet`

Sau đó: `tao_bang_van_don` → `configure_erp_reports` →
`configure_delivery_daily_report` → `collectstatic --noinput --clear`.
Migrate check không còn chờ. Đối chiếu giữ 44 dòng, 19 bảng nghiệp vụ không đổi;
11 nhãn tiền MKT đổi VND, giữ số tiền/người/ngày/lịch sử. Không quy đổi tỷ giá.

`kiem_tra_du_lieu --bang van_don` chạy trong container riêng trả exit 1 vì đúng
hai đơn mồ côi baseline; script xử lý lỗi tổng quát ban đầu dừng tại đây. Đã đọc
kết quả, đối chiếu baseline, chạy lại với xử lý exit rõ ràng rồi tiếp tục. Không
dùng `--sua`. Không có lệch cột tách, mã trùng hoặc giá trị ngoài danh sách; một
dòng `sl_*` lệch Chi tiết sản phẩm là thông tin đã có trong diễn tập, không tính
vào mã thoát. Chi tiết riêng tư nằm trong thư mục release.

Chạy `VACUUM ANALYZE forms_builder_datarecord`; đổi riêng KNJSC_IMAGE trong `.env`,
bật năm ứng dụng với `--no-deps`, kiểm nginx rồi reload ngay. Kiểm nội bộ trước
khi bỏ 503, kiểm/reload nginx lần nữa để mở truy cập.

## Static, vận hành và giao diện domain thật

Cả hai domain trả 200 ở trang đăng nhập. Năm container cùng image ID r2,
running, restart 0 và không OOM tại thời điểm mở lại. Hash bytes tải thực trên
**cả hai domain** khớp file trong image:

Đã chạy lại `check --deploy --fail-level WARNING` bằng container riêng của cả
CRM và ERP với cấu hình production thực tế sau chuyển image: cả hai đạt.
PostgreSQL kiểm lại vẫn `panic`.

| Tệp | SHA-256 |
|---|---|
| master-grid.js | `3ee400a4f4b8b1d5635734d5cf1d2b6f1ccd16abf668fbbb9b17ade49fd34266` |
| report-filters.js | `3bc1955e085e6a52d21ca1abedfdbc7e78c2d2766f72474edbb799fe7d471d50` |
| phan-trang.js | `80e81dfcdf1436b6958757aed9b48cdd37147c3aae6bd8432a78b4b84ef194ca` |

Tác vụ sẵn có `core.kiem_tra_hang_doi` đã được gửi qua hai queue `celery` và
`crm_heavy`; log từng worker xác nhận received/succeeded và kết quả đúng.
Tác vụ cấu hình `ignore_result=True`, nên `AsyncResult.get()` không cung cấp
bằng chứng hoàn tất; đã kiểm log thực thi thay vì coi giá trị `None` là lỗi worker.

Theo dõi liên tục kết thúc lúc 11:21:43 VN, đủ 15 phút sau mở lại; tiếp tục kiểm
log sau các thao tác UI. Cả năm ứng dụng vẫn chạy image r2, restart 0, không OOM.
Không có HTTP 5xx hoặc lỗi ứng dụng ngoài dự kiến. Có một request dùng IP làm
Host bị từ chối HTTP 400/DisallowedHost (kèm traceback), không nới ALLOWED_HOSTS;
proxy có một HTTP 499 (client đóng kết nối), không coi là 5xx hay che khỏi số liệu.

12 mẫu tài nguyên: RAM khả dụng thấp nhất 2.381 MiB, swap dùng cao nhất 38 MiB;
lock wait, transaction idle quá 30 giây và tác vụ DB pending/running cao nhất
đều 0. Không có kiểm tải lớn. Log và `monitor-summary.json` ở thư mục backup cuối.

| Lưu lượng quan sát (gồm thao tác nghiệm thu) | Số mẫu | p95 server |
|---|---:|---:|
| ERP GET | 31 | 119,97 ms |
| ERP POST | 11 | 817,75 ms |
| CRM GET | 34 | 143,52 ms |
| CRM POST | 6 | 158,36 ms |

Đây là mẫu ít, đặc biệt POST; không phải độ trễ toàn trình duyệt, so sánh trước/sau
hoặc bằng chứng chịu tải nhiều người dùng.

### Thao tác thật bằng tài khoản Admin

| Luồng | Kết quả trên domain thật |
|---|---|
| Phiên ERP → CRM | Dùng chung phiên đăng nhập, không phải đăng nhập lại |
| Marketing | Form tiền VND, xem trước công thức; nộp 10 Mess/1.000 CPQC/1 đơn/2.000 doanh số thành công |
| Sale | Chọn sản phẩm/Canada, tiền CAD tự điền; nộp ba trường số bằng 0 thành công |
| Lịch sử | Đọc, sửa ghi chú, giữ người/ngày/thời điểm nộp; bỏ/khôi phục/bỏ lại thành công, giữ lịch sử sửa |
| Tổng hợp | Lọc ngày/nhân sự, Gộp, thu gọn bộ lọc, toàn màn hình/Esc, tải XLSX thành công |
| Lên đơn | Đơn có nhãn kiểm thử tạo qua form, xuất hiện trong lưới đúng ngày DD/MM/YYYY |
| Lưu ô | Sửa tên trên dòng thử, bấm ô khác, tự lưu và tải lại còn giá trị; không cảnh báo ngày |
| Lưới | Tìm kiếm, cuộn ngang với cột ghim; toàn màn hình/Esc giữ bộ lọc; ghi chú ba dòng mở ngay trong ô |
| Xóa/hoàn tác | Xóa dòng cuối đang lọc → 0 dòng; Hoàn tác → dòng trở lại; xóa mềm lại thành công |
| Màn hình | Tổng hợp desktop 1440 px; form MKT và lưới 390 px không tràn ngang trang (đối chiếu innerWidth/scrollWidth) |
| Console | Không ghi nhận console error trong hai tab kiểm thử |

Dữ liệu thử production được tạo có chủ đích và đã dọn qua chức năng có audit:
DailyReport **16/17**, DataRecord **6816/6817/6818**, Order **22**. Kiểm DB chỉ đọc
xác nhận cả hai báo cáo, ba dòng và đơn đều đã soft delete. Một lần sửa báo cáo
và các thao tác khôi phục/hoàn tác giữ lịch sử, không xóa audit. Số dòng tổng vật lý
có thêm các bản thử này; không nhầm với tăng dữ liệu ngoài dự kiến.

Ảnh và XLSX tải qua UI giữ ngoài Git trong hồ sơ máy kiểm thử: ảnh tổng hợp
1440 px, form MKT 390 px và ghi chú dòng thử. Ảnh ghi chú cho thấy nội dung nhiều
dòng, không đưa thông tin khách thật vào PR. XLSX đã tải thành công, chưa mở đối
chiếu từng ô trên production; kiểm nội dung xuất có bằng chứng diễn tập/CI.

**Chưa kiểm lại qua UI production:** toàn bộ vai trò ngoài Admin, giả lập mất mạng,
CAS/mã trùng, nộp Vận đơn, chuyển trang với dữ liệu vượt một trang, và tương tác
thu hồi ghi chú sau chọn ô khác bằng đo hình học. Các ca quyền, NFD/CAS/mã trùng,
báo cáo Vận đơn được kiểm trên bản sao/CI như phần trên, không ghi thành đã thao
tác bằng đúng vai trên VPS. Không có lỗi nghiêm trọng được phát hiện để quay lui.

## Quay lui và giới hạn

Giữ image `knjsc-app:c7065fe-adr046` và backup cuối. Nếu lỗi nghiêm trọng:
bật 503, drain/dừng năm ứng dụng; dùng image cũ chạy `configure_erp_reports`,
`configure_delivery_daily_report`, `collectstatic --noinput --clear`; đổi
KNJSC_IMAGE về cũ, bật năm app bằng `--no-deps`, kiểm/reload nginx, nghiệm thu
cơ bản trước mở lại. Mọi lệnh Compose vẫn dùng hai tệp runtime thực tế.

Không đảo migration hoặc restore toàn DB để quay lui mã. Giữ PostgreSQL panic
nếu hoạt động đúng. Quay lui không hoàn nguyên nhãn tiền MKT đã chuyển; bản cũ
có thể tạo báo cáo theo quy tắc tiền cũ, phải kiểm dữ liệu trước khi tiến lên lại.

Nhắc người dùng tải lại các trang đang mở, đặc biệt form báo cáo cũ. Không chạy
300.000 dòng, không tuyên bố hiệu năng đa người dùng từ lưu lượng ít mẫu.
Tài liệu đi qua nhánh `claude/phat-hanh-vps-e979323` từ Staging đã fetch, PR nháp
về Staging; không tự merge. Không chứa thông tin kết nối SSH hoặc dữ liệu khách.
