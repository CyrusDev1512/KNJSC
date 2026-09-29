# 29.09.2026 — Phát hành main c7065fe lên VPS

## Phạm vi và nguồn kiểm chứng

Chủ dự án chuyển bàn giao từ Claude Code: phát hành đúng `c7065fe`, sau đó kiểm kê
dữ liệu rác; chỉ dọn sau khi chủ dự án chỉ rõ nhóm và cách xoá. Giữ cấu trúc bảng,
quyền, nguồn báo cáo, tài khoản, sản phẩm và nhật ký. Không sửa mã ứng dụng.

Local và GitHub `main` cùng SHA `c7065feeb5bfb7d6ce148e35229877f5115d3d3e`.
[CI 36590419922](https://github.com/CyrusDev1512/KNJSC/actions/runs/36590419922)
được truy vấn trực tiếp: `completed/success`, đúng SHA. Các số pytest trong bàn giao
là kết quả của Claude, không phải lượt chạy lại của phiên phát hành này.

**Đính chính hiện trạng:** VPS trước phát hành sạch, checkout `main 97bff53`, cả năm
dịch vụ dùng `knjsc-app:97bff53-main`; không phải `85227ee` như bàn giao. `97bff53`
là tổ tiên của `c7065fe`, chứa thêm PR #55. Diff migration giữa hai mốc rỗng.
Vận đơn có **38 cột**, không phải 45 của dữ liệu local; đã kiểm bằng bản phục hồi backup.

## Sao lưu và phát hành

- Backup: `/opt/knjsc-runtime/release-c7065fe-20260929/database.dump`, **379.253 byte**.
- SHA-256: `f7963ebaada7954fb43c3851f00e7bb413b54a26588c2e09e849f77191ff0c36`.
- Đã đọc danh mục dump, phục hồi thật vào database tạm riêng với `--exit-on-error`,
  đối chiếu số dòng từng bảng và 51 bảng public; xoá database tạm sau kiểm tra.
- Lưu `commit.before`, `env.before`, `images.before` trong thư mục release quyền 700.
  Không đưa cấu hình bí mật hoặc dump vào Git.
- Fast-forward checkout VPS tới đúng SHA, build `knjsc-app:c7065fe-adr046` từ
  `deploy/Dockerfile`, `INSTALL_DEV=0`.
- `check` và `check --deploy` trên cả CRM/ERP đạt; `showmigrations` và
  `migrate --check` không có migration chờ.
- Mọi lệnh Compose dùng **cả** `compose.yml` và `compose.vps.yml` tại runtime.
- Chạy `static-owner`, `migrate --noinput`, `tao_bang_van_don`,
  `configure_erp_reports`, `configure_delivery_daily_report`, `collectstatic`.
  Ba nguồn `bao_cao_sale`, `bao_cao_mkt`, `van_don` được in đủ; không có `CANH BAO`.
- Static: 9 tệp mới, 147 không đổi. Chuyển `KNJSC_IMAGE` trong `.env`, chạy các
  dịch vụ rồi `nginx -t` và reload thành công.
- Chuyển phiên bản lúc **23:40:15 giờ Việt Nam** (16:40:15 UTC).
  Năm app dùng cùng image mới. Compose cũng tái tạo DB/proxy khi cập nhật cấu hình
  runtime; volume giữ nguyên, DB healthy sau khởi động.
- Đối chiếu lần hai với backup: **42 DataRecord có cùng ID và hash toàn bộ dòng**;
  số cột các bảng giữ nguyên: Vận đơn 38, Marketing 19, Sale 11, báo cáo Vận đơn 5.

## Kiểm trực tiếp

Trình duyệt có kết nối là **Codex in-app browser**, không phải Chrome host. Chủ dự án
tự đăng nhập Admin; không lấy mật khẩu hoặc thay tài khoản để kiểm.

| Kiểm tra | Kết quả |
|---|---|
| Hai domain đăng nhập | HTTP 200, HTTPS bình thường |
| Tổng quan Admin | Mỗi chỉ tiêu một hàng, các loại tiền tách cột |
| Báo cáo theo nhân viên | Mở được; doanh số USD `13.250.000` đúng số đã nhập, CAD tách riêng |
| Tổng hợp / Từng lần nộp | Chuyển được qua form; có cột giờ/lần nộp, tổng tách tiền |
| Nộp báo cáo Marketing và Sale | Mỗi form đúng một ô Team, không nộp dữ liệu thử |
| CRM Admin | Mở lưới 25 dòng sống; nút Tôi/Toàn bộ đổi trạng thái; menu không có Phân công |
| Console ERP/CRM trong các trang đã kiểm | Chưa thấy lỗi JavaScript qua bộ đọc console |
| Leader/Staff Vận đơn trên VPS | Chưa kiểm: không có tài khoản hoạt động thuộc bộ phận này |
| Ghi ô, autosave, phân công và F5; lịch sử sau ghi | Chưa kiểm trực tiếp trong lượt này; không đánh đồng kiểm đọc với kiểm ghi |

Kiểm bổ sung bằng `RequestFactory` gọi view trên image production, dùng tài khoản
hiện có, toàn bộ nằm trong transaction rollback: Admin `/tac-vu/` 200; Staff Sale
`/tac-vu/` 403; Staff Marketing cả trang lưới và `du-lieu/` 403; Staff Sale cả hai
đường đọc lưới 200 (**6/6**). Đây không phải kiểm qua HTTP/trình duyệt. Bước thử
`READ ONLY` ban đầu bị PostgreSQL chặn vì nhánh từ chối quyền ghi audit; lượt sau
cho phép audit trong transaction và rollback toàn bộ, không sửa/xoá audit đã có.

## Theo dõi và kiểm kê

Theo dõi tới **23:55:58 VN**, tổng **15 phút 43 giây** từ mốc chuyển phiên bản.
Năm app luôn running, restart 0; hai domain đăng nhập 200. Trong log đã gom:
143 HTTP 200, 4 HTTP 302, 8 HTTP 400, **0 HTTP 5xx**. Tám lỗi `DisallowedHost`
đều là yêu cầu dùng IP trực tiếp làm Host, bị cấu hình host từ chối; không mở
ALLOWED_HOSTS để bỏ chặn. Không có ERROR khác. Worker/heavy có cảnh báo cấu hình
Celery sẽ thay đổi ở phiên bản 6, vẫn kết nối broker và ready.

Số p95 từ log container mới, `--since 1h` (thực tế chỉ có từ lúc tạo container):

| Nhóm | Mẫu | p95 ms | Giới hạn của kết luận |
|---|---:|---:|---|
| CRM đọc | 7 | 285 | Ít hơn 20 mẫu, chưa kết luận tải thực |
| CRM POST | 50 | 51 | Chỉ là `quyen-dong/`, **không phải phép đo lưu ô** |
| CRM hỏi thăm | 52 | 60 | Dưới ngưỡng 300 ms trong cửa sổ này |
| ERP đọc | 15 | 164 | Ít mẫu; không có mẫu ghi nghiệp vụ |

File p95, monitor và log nằm trong thư mục release trên VPS. Không chạy kiểm tải.
Staff Sale chưa đăng nhập vào trình duyệt trước thời điểm chốt biên bản; quyền
chỉ có kiểm view rollback như trên. Kiểm ghi ô/phân công/Undo/lịch sử, Gộp/Không gộp
và cuộn sau đổi chế độ, Chrome host, Leader/Staff Vận đơn còn chưa nghiệm thu trực tiếp.

Kiểm kê bằng transaction **READ ONLY** sau hơn 15 phút:

| Nhóm | Số lượng |
|---|---:|
| Vận đơn sống / xoá mềm | 25 / 3 |
| Dòng sống thiếu mã đơn hoặc tên khách | 18 (chỉ nghi vấn, chưa duyệt xoá) |
| Mã PERF-/MAU-/KH- | 0 / 0 / 0 |
| Order không có record | 2 |
| Customer không có vận đơn sống | 7 |
| WaybillItem / WaybillAssignment / GridCellHistory / PaymentDocument mồ côi | 0 / 0 / 0 / 0 |
| Dòng Sale / Marketing xoá mềm | 0 / 2 |
| DailyReport toàn bộ / xoá mềm | 14 / 2; chưa xác định bản thử |
| Tệp exports / uploads | 0 / 0, không có tệp quá 30 ngày |

Database **34.151.447 byte**. Năm bảng lớn nhất (byte): `forms_builder_datarecord`
18.137.088; `core_auditlog` 589.824; `crm_gridmutationreceipt` 335.872;
`org_userprofile` 327.680; `orders_order` 327.680.

Phân bố 28 dòng theo ngày VN: 15/09: 1, 17/09: 8, 18/09: 3, 19/09: 3, 22/09: 4,
23/09: 1, 24/09: 2, 25/09: 2, 27/09: 4. Có 25 dòng do Admin tạo, 2 do Sale,
1 không còn định danh người tạo. Giữ nguyên cấu trúc (38 cột, 1 ReportSource,
0 FormDef), chưa xoá dữ liệu hoặc viết lệnh xoá.

Danh sách ID và ví dụ riêng tư ở `outputs/release-20260929/kiem-ke-cho-duyet.md`
trên máy local, ngoài Git; JSON gốc quyền riêng nằm trong thư mục release VPS.
**Chờ chủ dự án chọn nhóm và xoá mềm/cứng** theo B2 của bàn giao. Không suy ra
dòng thiếu thông tin, Order không liên kết hoặc Customer không có vận đơn là rác.

## Quay lui

Image cũ: `knjsc-app:97bff53-main`. Nếu có lỗi ứng dụng: đặt lại image này trong
runtime, collectstatic bằng image cũ và cập nhật năm app với đủ hai Compose; kiểm
nginx và domain. Không đảo migration (không có migration mới), không khôi phục
database chỉ để quay lui mã. Backup chỉ dùng khi xác định có hỏng dữ liệu.
