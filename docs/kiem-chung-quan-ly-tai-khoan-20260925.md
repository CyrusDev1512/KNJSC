# Kiểm chứng quản lý tài khoản — 25.09.2026

Nền: `main a23573d7aaaabac1eedfa9ec169d68c7b33b2fd6`.
Nhánh: `claude/phan-quyen-mat-khau-xoa-tai-khoan`.
Checkout: `C:/KNJSC/account-management`. Không sửa checkout task khác hoặc VPS.
Quyết định: [ADR-044](quyet-dinh/044-ceo-va-quan-ly-tai-khoan.md).

## Phạm vi đã kiểm

- Năm cấp, khác team/phòng ban, ngang/cao cấp, tự tác động, URL/POST ngoài quyền.
- Reset: hai mật khẩu không khớp/yếu, không echo, bản băm, audit/session không chứa
  mật khẩu, phiên ERP/CRM cũ mất hiệu lực, lần sau buộc đổi, giữ tài khoản khóa.
- Xóa: GET không ghi, POST có xác nhận/CSRF, giữ User/mã/team/đơn/báo cáo/phân công;
  không tái dùng username/mã; primitive từ chối sửa/reset/mở khóa hồ sơ đã xóa.
  Backend chặn cả khi tài khoản bị bật active lại nhưng còn mật khẩu hợp lệ.
- CEO đọc dòng của nhiều phòng ban; không kế thừa quyền Admin, ghi lưới, điền
  biểu mẫu, sửa báo cáo, chứng từ/phân công/cấu hình. Admin tạo CEO không cấp
  `is_staff/is_superuser`; xuống CEO thu lại quyền kỹ thuật và vô hiệu phiên.
- Hai connection PostgreSQL đồng thời: hai Admin xóa chéo giữ một Admin hoạt động;
  reset và xóa cùng target không hồi sinh tài khoản. Đọc lại actor/target trước ghi.
- Migration 0006 xuôi/ngược trên DB test: giữ tài khoản, đảo mất dấu xóa và không
  mở lại tài khoản. Không đảo migration trên DB đang vận hành.
- Trần 10 truy vấn cho danh sách và màn Sửa theo các cấp quản lý; auth backend
  đọc profile cùng User, không thêm query hồ sơ theo từng ô CRM.

## Cách chạy

PostgreSQL 16 test riêng, không public port. User/DB test chỉ dùng ở network
`knjsc-account-test`; không seed dữ liệu vào môi trường đang sử dụng.

```powershell
# $testEnvironment là mảng -e POSTGRES_* trỏ đúng container PostgreSQL test riêng.
# Mount cả repo để các bài scripts/skills truy được nguồn; RUN_MIGRATIONS=0 bỏ seed entrypoint.
docker run --rm --network knjsc-account-test -e RUN_MIGRATIONS=0 @testEnvironment `
  -v C:/KNJSC/account-management:/repo -v C:/KNJSC/account-test-evidence:/evidence `
  -w /repo/app knjsc-web pytest `
  -o 'addopts=--strict-markers --ds=knjsc.settings.test' --tb=short `
  --junitxml=/evidence/full-suite-final.xml
```

Nhóm nhanh: `org/tests/test_account_management.py org/tests/test_account_concurrency.py`.
Nhóm phân loại lỗi lượt đầu bổ sung `reports/tests/test_ma_tran_phan_quyen_bao_cao.py`,
`tests/test_dong_bo_skill.py`, `tests/test_gom_p95.py`: 88 đạt trong 16,48s.

Chrome: container DB test riêng cho browser, `ACCOUNT_BROWSER=1`, port localhost
18047, pytest `org/tests/test_account_browser_server.py --liveserver=0.0.0.0:18047`.
Sau khi fixture ghi `account-browser-ready.json`, đặt `ACCOUNT_EVIDENCE` tới thư mục
bằng chứng và chạy `node scripts/kiem-thu-quan-ly-tai-khoan.cjs` bằng Playwright sẵn có.
Chrome ánh xạ hai hostname test ERP/CRM về localhost; cookie domain test riêng.
Không có tài khoản test/mật khẩu phát hành lên dữ liệu thật.

## Kết quả và giới hạn

- TDD đỏ đã quan sát trước sửa; kết quả lượt đầu/full và cách xử lý ở test-log.
- Chrome: 8 luồng reset → đăng nhập/đổi mật khẩu → hủy/xác nhận xóa đạt,
  4 cấp quản lý × 2 kích thước; Staff và truy cập Admin ngoài quyền bị chặn.
  Fixture đối chiếu 8 target đều xóa mềm: 1 đạt, 67,88s. Không có pageerror.
- Tổng suite cuối: **2.770 đạt, 49 bỏ qua, không lỗi**, 376,34s.
  Các bài bỏ qua cần Chromium trong container hoặc fixture browser/capacity bật
  riêng. Chrome tính năng tài khoản được chạy riêng như trên; skip không tính đạt.
- Nhóm tài khoản sau rà soát đường Django admin: **58 đạt**, 16,13s; bổ sung
  4 bài ngân sách màn Sửa, hạ Admin xuống CEO và chặn Django admin bật lại cờ
  kỹ thuật/hồi sinh hồ sơ xóa. Các bài bổ sung này chạy riêng sau khi toàn suite
  đã thu danh sách bài, không cộng vào số 2.770 ở trên.
- Khởi động/check ERP và CRM không lỗi. Migration check không có thay đổi còn thiếu.
- Kiểm lại phần bị tác động trên các file cuối: **101 đạt**, 17,30s, không bỏ qua.
  Bao gồm 58 bài tài khoản và 43 bài biểu mẫu/hai tab.
- Đây là kiểm chức năng và trần truy vấn, không phải phép đo tải toàn CRM hoặc
  tuyên bố tăng tốc. Không triển khai VPS; PR nháp cần chủ dự án duyệt.

Bằng chứng thô local: `C:/KNJSC/account-test-evidence` (JUnit, JSON Chrome,
ảnh xác nhận xóa không có mật khẩu). Script/fixture tái chạy được nằm trong repo.
Tóm tắt máy đọc được: [JSON kết quả](evidence/account-management-20260925.json).

## Kiểm nhanh cho Admin sau khi áp migration trên môi trường test

1. Vào Nhân sự → Sửa một tài khoản khác, dùng form Đặt lại mật khẩu riêng.
2. Đăng nhập bằng tài khoản đó: phiên cũ hết hiệu lực, mật khẩu mới buộc đổi.
3. Dùng tài khoản quản lý cấp dưới để xác nhận chỉ có thông tin đọc và reset,
   không có form sửa cấp bậc/khóa/tạo người.
4. Xóa → kiểm mã/họ tên → Hủy; mở lại và xác nhận. Người biến khỏi danh sách
   nhưng tên/mã trong báo cáo, đơn và phân công lịch sử vẫn còn.
