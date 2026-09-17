# Hai bảng báo cáo mẫu trên VPS — 15.09.2026

Chủ dự án duyệt tạo Báo cáo Marketing và Báo cáo Sale, mỗi bảng 50 dòng,
thuộc team/nhân sự kiểm thử riêng. Đã thực hiện trên domain thật lúc 15:12
giờ Việt Nam qua phiên SSH riêng của tài khoản deploy.

## Kết quả

- VPS trước thực hiện chỉ có bộ phận Kế toán/Vận đơn và ba bảng vận đơn.
- Bổ sung bộ phận Marketing/Sale, bảng `bao_cao_mkt`/`bao_cao_sale`, các cột
  chuẩn hiện có, form và cấu hình ReportSource tương ứng.
- Mỗi bảng: 50 DataRecord, 5 team, 10 nhân sự, mỗi người 5 ngày 11–15/09/2026.
  Tổng 10 team và 20 nhân sự. `created_by`, `team`, `department` khớp hồ sơ;
  có thêm cột Team hiển thị và Ghi chú đánh dấu dữ liệu mẫu.
- Team và họ tên có tiền tố “Mẫu —”; username bắt đầu `mau_baocao_`.
  Tài khoản `is_active=False`, mật khẩu không sử dụng được, không tạo quyền
  đăng nhập hay ảnh hưởng phiên/tài khoản người thật.
- Các số liệu đều tổng hợp giả lập, tiền VND; không quy đổi tiền tệ. Cột Sản
  phẩm để trống do VPS chưa có danh mục. Không tự tạo sản phẩm hoặc cột vận đơn.
- Không tạo DailyReport đã nộp. DataRecord mẫu có thể được tổng hợp qua nguồn
  báo cáo trong phạm vi quyền; không khẳng định mẫu bị loại khỏi thống kê.
- Bảng vận đơn giữ số dòng trước/sau: ID 1 = 1, ID 3 = 6667; bảng vận đơn nhận
  đơn mới không có dòng. Không ghi/sửa/xóa nội dung các bảng này.

## Kiểm chứng

Kịch bản: `scripts/tao-bao-cao-mau-20260915.py`. Chỉ định nghĩa `provision()`
và `verify()`, không tự chạy khi nhập module. Chạy lại chỉ xác minh bộ mẫu đã
đủ; nếu mã bảng/tài khoản bị chiếm bởi dữ liệu khác thì dừng, không ghi đè.
Thao tác tạo nằm trong một transaction, dùng khóa riêng theo tên bộ mẫu.
Không khóa bảng vận đơn, restart/reload dịch vụ, migrate hoặc thay image.

Kiểm riêng trên database pytest trước khi ghi VPS:

```powershell
docker compose -f deploy/docker-compose.yml run --rm -e RUN_MIGRATIONS=0 web pytest -c /app/pytest.ini --ds=knjsc.settings.test /storage/report-samples/test_provision.py -ra --maxfail=1
```

**2 passed in 5.01s**: đủ số dòng/team/người, tài khoản không đăng nhập được,
phạm vi Staff mỗi người 5 dòng, chạy lại không thêm dòng, giữ dòng vận đơn cũ,
không tạo DailyReport; từ chối khi đã có bảng báo cáo ngoài bộ mẫu.
Test viết cùng lúc với kịch bản vận hành, không phải chu trình TDD red/green.

Sau commit transaction, một tiến trình đọc riêng trên VPS gọi `verify()`:
cả hai bảng 50 dòng/5 team/10 người, đúng ngày và metadata người sở hữu.
Trình duyệt tài khoản quantri trên domain thật thấy cả hai nhánh và số dòng
50 trong tháng 9. Mở cả hai lưới tải được tên người/team; tìm Nguyễn Minh Anh
trên Marketing trả đúng 5 dòng. Không thực hiện sửa ô trong lượt kiểm này.

## Vận hành và sao lưu

Backup trước ghi:
`/opt/knjsc-runtime/backups/before-report-samples-pc-20260915-1512.dump`.
Đã kiểm file không rỗng và `pg_restore --list` đọc được; không thực hiện phục
hồi thử trên VPS. SSH host ED25519 khớp fingerprint do chủ dự án cung cấp.
Khóa PC riêng, không sửa authorized_keys hoặc cấu hình phiên bên kia.

Image CRM trước/sau: `knjsc-app:f971683-crm-sidebar-20260915`.
Thời điểm khởi động trước/sau cùng là `2026-09-15T06:58:14.845549572Z`.
Không commit/push trong tác vụ tạo dữ liệu này.
