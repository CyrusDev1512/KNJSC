# KNERP — định danh và mật khẩu tạm, 10.09.2026

## Hành vi và phạm vi

- Lịch sử/chi tiết hiển thị mã nhân sự kèm họ tên từ tài khoản liên kết;
  tìm không phân biệt hoa/thường theo cả hai. Không viết lại nội dung báo cáo cũ.
- Phân trang, đổi cỡ trang, mở chi tiết và quay lại giữ bộ lọc lịch sử.
  Bộ lọc biểu mẫu/phòng ban dùng danh sách đã lọc quyền; không mở quyền mới.
- Admin tạo nhân sự: để trống mật khẩu thì tự sinh 16 ký tự có hoa/thường/số;
  nhập tay thì kiểm cùng validators hiện có. Trang kết quả cho sao chép bàn giao,
  không có đường xem lại. Người mới phải đổi mật khẩu ở lần đăng nhập đầu.
- Mật khẩu rõ không đưa vào session/messages/audit/URL. Database giữ hash;
  trang tạo/kết quả `no-store`, tham số nhạy cảm được đánh dấu cho báo lỗi Django.
- Service tạo tài khoản cũ giữ hợp đồng. Không migration hoặc dependency mới.

## Ma trận đã dùng để kiểm

| Trang/đường thao tác | Staff | Leader | Manager | Admin |
|---|---|---|---|---|
| Tổng quan, lịch sử, chi tiết, tổng hợp/xuất | Bản thân | Team và bản thân | Phòng ban | Công ty |
| Nhân sự | 403 | Trong phạm vi | Trong phạm vi | Toàn bộ |
| Tạo nhân sự GET/POST | 403 | 403 | 403 | Cho phép |
| Quản lý Biểu mẫu | 403 | 403 | Trong phạm vi | Toàn bộ |
| Bảng dữ liệu ERP | Chỉ đọc theo quyền bảng | Chỉ đọc theo quyền bảng | Chỉ đọc theo quyền bảng | Chỉ đọc |

Ngoại lệ dữ liệu nội bộ dùng chung và quyền bảng giữ nguyên. Chi tiết báo cáo
ngoài phạm vi trả 404; chọn nguồn thống kê/xuất ngoài quyền trả 403.

## Hướng dẫn kiểm tra cho Admin

1. Mở Nhân sự → tạo nhân sự. Nhập mã, họ tên, email, cấp bậc và bộ phận.
2. Để trống Mật khẩu tạm để tự sinh hoặc nhập mật khẩu riêng đáp ứng quy tắc.
3. Bấm Lưu, sao chép mã và mật khẩu từ trang kết quả để bàn giao cho đúng người.
   Sau khi rời trang không có đường xem lại mật khẩu đó.
4. Nhân sự đăng nhập bằng mã, đổi mật khẩu bắt buộc rồi mới sử dụng hệ thống.
5. Trong Lịch sử báo cáo, tìm bằng mã hoặc họ tên; mở chi tiết rồi Quay lại
   để kiểm trạng thái lọc/trang được giữ. Báo cáo cũ không bị viết lại nội dung.

## Tái chạy

Chạy pytest với `POSTGRES_DB=knjsc_erp_verify`, `RUN_MIGRATIONS=0` để dùng
`test_knjsc_erp_verify`; không tác động database local đang sử dụng.

- Nhóm tác động: `pytest org/tests reports/tests`.
- Toàn bộ: `pytest`, không bỏ marker chậm. Xem JUnit `identity-full-final.xml`.
- Chrome host sẵn có: `scripts/kiem-thu-erp-identity.cjs` và
  `scripts/kiem-thu-erp-role-navigation.cjs`; không ghi ảnh/trace chứa mật khẩu.
- Dữ liệu bổ sung: `app/tests/perf/identity_dataset.py`, chỉ chạy bằng Django shell
  trên DB `knjsc_erp_verify`. Thêm 40k báo cáo tổng hợp từ 2000–2002, bỏ qua phần đã có.
- Locust: `app/tests/perf/locust_identity.py`, chỉ nhận host container
  `http://knjsc-erp-final:8000`. Mỗi mức 10/20 người chạy 360 giây,
  reset thống kê ở giây 60; sau sửa đặt `IDENTITY_EXPECT_CODE=1`.

Raw bằng chứng trong `storage/erp-verification/identity-*`. Workload đọc gồm
tìm mã, tìm tên, xem chi tiết, cùng dữ liệu/máy trước và sau. Kết quả tìm mã trước
sửa rỗng do thiếu chức năng, nên không coi so sánh thời gian đó là tỷ lệ tăng tốc.
Máy/Postgres dùng chung với kiểm thử và tác vụ khác; số đo local không thay
nghiệm thu máy chủ sản xuất.

## Các lỗi ngoài phạm vi đã đối chiếu

- `test_mot_ngay_cua_cong_ty`: bước sửa trạng thái ở endpoint CRM nhận 409
  trong khi test kỳ vọng 200; payload cũ chỉ gửi giá trị, thiếu thông tin kiểm xung đột.
- Kiểm CSS `_assignment.html` nhận nhầm `master_grid` trong biểu thức template
  là tên lớp CSS. Không thay template CRM hoặc bộ kiểm CSS của tác vụ khác.
- Cả hai tái hiện với file org/reports trước đợt thay đổi được mount trong
  container kiểm thử riêng (`identity-preexisting.xml`).
- Các bài browser bị skip do thiếu Chromium trong container không được tính đạt;
  luồng thay đổi ERP kiểm riêng bằng Chrome trên host.

## Kết quả cuối

- Nhóm org/reports: **143 passed**, không skip; chạy lại sau sửa nút Lưu dùng
  chung biểu mẫu tạo/sửa hồ sơ. Test trần 10 truy vấn với bộ lọc kết hợp đạt.
- Toàn suite: **2.068 passed, 2 failed, 22 skipped, 2 xfailed**, 151,252 giây.
  Hai lỗi đã đối chiếu ở trên; không tuyên bố toàn hệ thống đạt. Bản sửa cuối
  của nút Lưu kiểm lại bằng nhóm org/reports và browser, không chạy lại toàn suite.
- Chrome: **4 luồng tạo/sửa hồ sơ → bàn giao → đổi mật khẩu → nộp → tìm → chi tiết → xuất**
  đạt ở 1440/390, gồm mật khẩu tự sinh/nhập tay; thêm **8 luồng ma trận vai trò** đạt.
  Không console/page error; mật khẩu tạm cũ đăng nhập thất bại sau khi đổi.
- Tạo tài khoản 239–252 ms; tải lịch sử 92,9–145,1 ms; lọc 107–170 ms;
  chuyển trang 110–178 ms. Từ input đến callback khung hình kế tiếp tối đa 16 ms
  trong mẫu gõ tự động; đây không phải INP đo trên người dùng thật.

| Lượt Locust | Yêu cầu | Lỗi | p95 tìm mã | p95 tìm tên | p95 chi tiết |
|---|---:|---:|---:|---:|---:|
| Trước, 10 người | 1.923 | 0 | 83 ms | 160 ms | 31 ms |
| Trước, 20 người | 3.817 | 0 | 93 ms | 180 ms | 33 ms |
| Sau, 10 người | 1.889 | 0 | 110 ms | 170 ms | 37 ms |
| Sau, 20 người | 3.767 | 0 | 120 ms | 170 ms | 34 ms |

Mỗi lượt cấu hình 360 giây, làm nóng 60 giây rồi đo khoảng 5 phút; số liệu
cuối lấy từ HTML report Locust (CSV định kỳ có thể thiếu vài request cuối).
Trong khoảng ngày workload có 100.000 báo cáo. Không tuyên bố tăng tốc:
tìm mã trước sửa chưa trả dữ liệu, sau sửa trả dữ liệu đúng. Cả hai mức sau sửa
đạt ngưỡng p95 ≤ 1 giây, không lỗi. p50/p99/throughput lưu trong
[bằng chứng tải](erp-2026-09-10/identity-load.json).

Database đang sử dụng vẫn giữ 49 báo cáo mẫu, không có tài khoản `identity_`
từ E2E. Không commit/push; các mục KNJSC chỉ đánh dấu phần đã kiểm chứng.
