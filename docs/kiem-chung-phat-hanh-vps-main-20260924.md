# 24.09.2026 — VPS chuyển sang main

## Phiên bản và phạm vi

- Chủ dự án duyệt merge PR #43 và thực hiện kế hoạch chuyển toàn bộ ERP/CRM sang `main`.
- [PR #43](https://github.com/CyrusDev1512/KNJSC/pull/43) đã merge; chốt SHA
  `9c4d285a3a873fdc05037994fe91d4b30095dd80`, không kéo thêm mã trong lúc phát hành.
- `/opt/knjsc`: `codex/crm-update-solar-ui` tại `72af235` → `main` tại SHA trên;
  checkout sạch, theo dõi `origin/main`.
- Năm dịch vụ `crm`, `erp`, `worker`, `heavy`, `beat`: `knjsc-app:72af235-gop` →
  `knjsc-app:9c4d285-main`. Build bằng Dockerfile hiện có, `INSTALL_DEV=0`.
  Image ID: `sha256:f35bb912fdb9b5b17ff5daaffed6b26bde3c2e09935ee999effdd61e141ef5a4`.
- Giữ nguyên hai file Compose thực tế và giới hạn tài nguyên VPS 2 CPU/4 GB.
  Không đổi domain, SSH, kiến trúc, cờ tối ưu hoặc cơ chế CI/CD; không seed, xóa bảng
  hay gán lại mã nhân sự. Nhánh cũ không đổi tên thành staging.

## Điều kiện trước phát hành

[CI main run 35986294595](https://github.com/CyrusDev1512/KNJSC/actions/runs/35986294595)
đạt trên đúng SHA phát hành:

| Nhóm | Kết quả |
|---|---|
| Bộ chính | 2.692 đạt, 7 bỏ qua, 41 không chọn; 381,18 giây |
| E2E trong tests/e2e | 27 đạt, 2 bỏ qua; 144,47 giây |
| Trình duyệt còn lại theo CI | 1 đạt, 8 bỏ qua, 2.702 không chọn, 1 cảnh báo; 20,18 giây |

Các bài kiểm tải chủ động/300.000 dòng và bài cần Chrome host/proxy riêng vẫn không
chạy theo cấu hình CI hiện có. Cảnh báo dọn DB test không được tính là kiểm chứng
trường hợp bỏ qua; đây không phải phép đo tải mới.

Khóa phát hành giữ cả `deployment.lock` và `overview-release.lock` bằng `flock`.
Đã xác nhận checkout sạch và image cũ đúng trước khi đụng runtime.

Diễn tập trên PostgreSQL riêng, mạng Docker `--internal`, không mở cổng host,
không beat/worker hoặc gửi thông báo. Bản dump VPS được phục hồi thật; hash dữ liệu
khớp bản gốc. Chạy check, migration và ba lệnh metadata trong **14 giây**.

- Image mới: 29 kiểm tra GET; Staff/Leader/Manager/Admin, cấm truy cập ngoài phạm vi;
  nộp/sửa báo cáo, giữ ngày/người nộp, bỏ/khôi phục theo quyền; xuất Excel; tạo đơn;
  lưu ô và từ chối CAS cũ bằng 409 đều đạt.
- Image cũ `72af235-gop` trên schema đã nâng: 29 GET cùng luồng nộp/sửa, tạo đơn,
  lưu/xung đột đạt. Không gọi chức năng khôi phục chưa có trong image cũ.
- Dữ liệu kiểm thử diễn tập nằm trong giao dịch rollback; hash nghiệp vụ sau mỗi
  lượt vẫn khớp. Không đưa dump, cấu hình hoặc nội dung khách hàng vào Git.
- Lần build thử đầu chưa khởi động được do umask của thư mục build làm file
  entrypoint thiếu quyền đọc. Đã sửa quyền bản mã nguồn build và build lại trước
  diễn tập; image được phát hành là image đã vượt các kiểm tra trên. Không sửa
  Dockerfile/mã ứng dụng để xử lý lỗi chuẩn bị này.

## Bảo trì, sao lưu và cập nhật

**17:33:48–17:35:03 giờ Việt Nam: 75 giây bảo trì.** Hai domain trả HTTP 503,
ngừng nhận request; dừng beat, web, chờ hai worker xác nhận active/reserved/scheduled
đều 0 rồi dừng worker. Database, Redis, nginx và volume giữ nguyên.

Backup riêng trên VPS:
`/opt/knjsc-runtime/release-main-20260924-9c4d285/` (thư mục 700).

- `database.dump`, `storage.tar.gz`, `static.tar.gz`, `runtime.tar.gz`;
  SHA-256 trong `backups.sha256` đều kiểm đạt.
- Phục hồi dump cuối vào `knjsc_restore_final` trên PostgreSQL diễn tập; hash toàn bộ
  các model nghiệp vụ được đối chiếu khớp trước khi nâng database thật.
- `env.before`, hai Compose, cấu hình nginx trước/sau; `metadata.before.json` giữ
  trạng thái cột/ẩn/thứ tự, bảng và nguồn báo cáo. Các tệp này chỉ ở thư mục riêng.

Chạy tuần tự: `check --deploy`, `migrate`, `tao_bang_van_don`,
`configure_erp_reports`, `configure_delivery_daily_report`, `collectstatic`.
Migration và metadata trên VPS: **17:34:28–17:34:41, 13 giây**.

Ba migration: `forms_builder.0016_datarecord_val_phone_key`,
`orders.0011_an_cot_san_pham_dang_co`, `reports.0005_reportsource_thresholds`.
`migrate --check` sau phát hành đạt; 156 static files được chép.

Chỉ dòng `KNJSC_IMAGE` trong `.env` đổi; khởi động năm dịch vụ với `--no-deps`.
Nginx kiểm cấu hình và reload để nhận IP container mới trước khi mở lại.

## Kiểm trên domain thật và dữ liệu

Dùng phiên đăng nhập Admin do chủ dự án mở, không đọc cookie/mật khẩu:

- ERP: phiên đăng nhập còn dùng được, Báo cáo tổng hợp Marketing/Sale có khối theo
  ngày/nhân sự, quy đổi VND, bộ lọc nhân sự hoạt động; nhận sự kiện tải Excel sau lọc.
  Bật toàn màn hình và Esc thoát được. Lịch sử mở báo cáo cũ và biểu mẫu báo cáo ngày
  Marketing/Sale/Vận đơn hiện đủ; ngày hệ thống hiển thị 24/09/2026.
- CRM: thư mục chỉ hiện bảng Vận đơn trong phạm vi; ngày là cột dữ liệu đầu sau cột
  Trùng; bật chế độ tập trung chỉ còn lưới/Công cụ/trạng thái lưu/Thoát; Esc trở lại.
  Metadata sau nâng có bốn cột số lượng sản phẩm ẩn: `sl_yuna`, `sl_sda`, `sl_ada`,
  `sl_mr`; giữ 4 định nghĩa bảng và 3 nguồn báo cáo.
- Tạo **đơn thử DH-2409-0001**, Order 13, DataRecord 6800, tên khách
  “Mẫu kiểm phát hành main 24-09-2026”, ghi rõ không giao hàng. Sửa ô Bang, chờ Đã lưu,
  tải lại vẫn thấy giá trị; ghi chú 6 dòng tự tăng cao từ 28 lên **122 px**, cột ghim
  cũng 122 px. Đơn gốc giữ nguyên ghi chú ban đầu. Đã **bỏ đơn bằng UI**, xóa mềm
  dòng vận đơn; giữ lịch sử, không xóa cứng khách/đơn kiểm thử.
- Sau loại riêng các ID thuộc đơn thử khỏi phép so sánh, số lượng và SHA-256 của
  130 DataRecord, 6 Customer, 12 Order, 15 OrderLine, 12 WaybillItem, 8 DailyReport
  và các model chứng từ/phân công/lịch sử báo cáo đều khớp trước phát hành.
- Hai hàng đợi `celery` và `crm_heavy` xử lý thành công tác vụ `celery.accumulate`
  chỉ trả về chuỗi kiểm tra; không gửi thông báo hoặc ghi nghiệp vụ.

Giới hạn: quyền theo vai trò và CAS được kiểm trên DB diễn tập; domain thật kiểm
bằng Admin. Thử cảnh báo khách cũ qua gõ điện thoại chưa thu được bằng chứng UI ổn
định, không coi là đạt. Không chạy lại kiểm tải 300.000 dòng.

## Theo dõi sau mở lại

Đã theo dõi đến **17:51:05**, tức **16 phút 02 giây** từ khi mở lại. Cả năm dịch vụ
đúng image, restart 0; hai domain đăng nhập HTTP 200. Log proxy trong khoảng kiểm
ghi 132 phản hồi 200, 1 phản hồi 302, **0 phản hồi 5xx**.

Có **2 phản hồi 400** do yêu cầu dùng hostname IP `103.57.221.52` bị
`django.security.DisallowedHost` từ chối. Bộ theo dõi đã dừng cảnh báo ở lần đầu;
đã đọc đầy đủ traceback và xác nhận đúng trường hợp ALLOWED_HOSTS, rồi phân loại
riêng khi kiểm lại. Không bỏ qua lỗi ứng dụng tùy ý, không thêm IP vào ALLOWED_HOSTS.
Ngoài hai từ chối hostname này không có ERROR/CRITICAL/traceback mới.

RAM available khoảng 2,3 GB, swap dùng 0; CRM khoảng 76/640 MiB, ERP 77/512 MiB tại
lần chụp trạng thái. Đây là kiểm vận hành nhẹ, không phải kết quả kiểm tải.
Đã dọn đúng ba container/mạng/volume DB diễn tập, giữ nguyên backup và volume thật.
Log kỹ thuật riêng: `monitor.jsonl`, `deploy.log`, `queue-probe.json`,
`business.final-excluding-sample.json` trong thư mục phát hành trên VPS.

## Quay lui

Giữ image `knjsc-app:72af235-gop` và bản static trước phát hành. Nếu có lỗi nghiêm
trọng: bật lại nginx maintenance, ngừng nhận ghi và dừng/drain ứng dụng; đặt lại
`KNJSC_IMAGE`, chạy `collectstatic` từ image cũ, bật năm dịch vụ với cả hai Compose,
kiểm rồi restore cấu hình nginx/reload. Không thay hai Compose bằng cấu hình mặc định.

Schema mới giữ nguyên vì đã kiểm image cũ đọc/ghi được. Không tự đảo migration hoặc
phục hồi toàn database. Cột ẩn migration 0011 không tự khôi phục khi reverse; chỉ
khôi phục phần metadata cần thiết từ `metadata.before.json` nếu quay lui hiển thị.
Nếu có dấu hiệu hỏng dữ liệu: giữ bảo trì và báo phạm vi trước khi phục hồi.

Tài liệu phát hành đi qua nhánh `claude/phat-hanh-main-20260924`, PR nháp về `main`;
không đẩy thẳng hoặc tự merge PR tài liệu. Runtime không chờ PR tài liệu để hoạt động.
