# Kiểm chứng chế độ xem Vận đơn mới — 12.09.2026

**12.09.2026, 17:28 — Đã bật nhánh fix để chủ dự án test nút:** checkout chính `C:/KNJSC/KNJSC` và local 8020/8021 hiện chạy `fix/trung-ma-don-dong-thoi`. Bản CRM-UPDATE được giữ nguyên tại `C:/KNJSC/worktrees/CRM-UPDATE`, chưa ghép. Đã sao lưu database, áp dụng riêng `forms_builder.0011_delivery_view_mode`; không seed hoặc đổi chế độ xem thay người dùng. 10 test chế độ xem đạt trên PostgreSQL test riêng; hai URLconf sạch. Đọc READ ONLY trên local xác nhận trang chế độ xem, liên kết từ lưới và Cột & cấp quyền đều 200; mặc định hiện là theo phân công. Chưa commit/push.

Triển khai local tại `C:/KNJSC/worktrees/fix-trung-ma-don-dong-thoi`, nhánh
`fix/trung-ma-don-dong-thoi`, nền `95988c9`. Không commit/push, không thay
checkout chính đang có công việc chứng từ thanh toán và dọn chức năng cũ.

## Hành vi đã kiểm

- Admin/Manager Vận đơn đổi Chỉ dòng được phân công / Toàn bộ bảng, áp dụng
  cho nhân viên Vận đơn có quyền vào bảng `van_don_moi`. Mặc định giữ phân công.
- Leader giữ quyền xem/phân công hiện có nhưng không được đổi cấu hình này.
- Mở rộng đọc không mở rộng ghi: sửa ô, chi tiết và gửi lại biên nhận đều kiểm
  quyền hiện hành. Nhân viên chỉ sửa dòng đang được giao cho mình.
- Cấp quyền → Cột & cấp quyền có khối chế độ xem; lưới menu … và hộp Phân công
  có liên kết tới cùng màn hình, không tạo hai cấu hình độc lập.
- Trang lưới đang mở phát hiện phiên bản đổi qua polling 8 giây và reload.
  Tab ẩn kiểm lại sau khi hoạt động và tới lượt polling; request đọc/ghi luôn
  kiểm quyền server hiện hành. Không logout. Nháp không lưu qua reload;
  màn hình quản lý giải thích tác động trước khi lưu.
- Hai trường TableDef (bool và version) bằng migration mới 0011. Không đổi
  `is_shared`, không viết lại khách hàng/đơn hay tác động bảng cũ.

## Kiểm thử thực tế

Môi trường Docker riêng `knjsc-view-mode-test`, PostgreSQL 16 container
`knjsc-view-mode-db`, database `test_view_mode` do pytest quản lý; không
expose DB ra host. Image `knjsc-web` sẵn có, mount app của worktree fix.

Lệnh chạy (trong container, `RUN_MIGRATIONS=0`, `POSTGRES_HOST=knjsc-view-mode-db`,
`POSTGRES_DB=view_mode`):

```text
pytest crm/tests/test_delivery_view_mode.py -q --reuse-db
pytest crm/tests orders/tests forms_builder/tests reports/tests -q --reuse-db --tb=short
pytest crm/tests/test_delivery_view_mode.py crm/tests/test_master_grid.py crm/tests/test_optimization.py --reuse-db -ra
python manage.py makemigrations --check --dry-run
python manage.py check
DJANGO_SETTINGS_MODULE=knjsc.settings.bangtinh python manage.py check
python manage.py migrate --noinput
python manage.py migrate forms_builder 0010 --noinput
python manage.py migrate --noinput
```

- TDD: 6 test thất bại vì đường đổi chế độ chưa có → 6 đạt; bổ sung thành
  10 test quyền, mặc định, dữ liệu không hợp lệ, CSRF, cache/token/sync,
  xuất Excel, audit, tính lặp lại, giữ bảng cũ và trần truy vấn.
- Hồi quy rộng: 500 passed / 4 failed / 10 skipped. Hai lỗi do chưa mount
  `/docs/tham-khao/vandon-mau.xlsx`: thêm mount `/docs:ro`, chạy lại 2/2 đạt.
  Hai lỗi còn lại là test markup điều hướng `test_dich_vu_bangtinh` đã ghi
  trên cùng nền ở biên bản trùng mã đơn; không sửa chen tác vụ này.
- Focused cuối sau refactor: **46 passed trong 18,11 giây**.
- `makemigrations --check`: không thiếu migration; check hai URLconf sạch.
- Migration 0011 xuôi → ngược 0010 → xuôi: đều OK trên DB test riêng.
- 10 skip của lượt rộng không tính đạt; E2E mới được chạy riêng, không skip.

## Chrome thật và hiệu năng giới hạn

```text
KN_VIEW_BROWSER=1 pytest crm/tests/test_delivery_view_browser_server.py --reuse-db --liveserver=0.0.0.0:8852 -ra
node scripts/kiem-thu-delivery-view.cjs
```

Publish duy nhất app test `127.0.0.1:8852`, mount thư mục bằng chứng vào
`/evidence`. Node dùng Playwright và Chrome có sẵn, không cài dependency.

**1 E2E passed (57,69 giây)**, Chrome 1440px và 390px: đăng nhập Manager và
nhân viên riêng, mở cấu hình từ lưới, đổi hai chiều, nhân viên tự reload và
số dòng đổi 1 ↔ 2, dòng người khác readonly, POST sửa bị 403, Staff vào
cấu hình bị 403, liên kết từ Cột & cấp quyền hoạt động, không pageerror hoặc
tràn ngang màn hình cấu hình. Đã xem ảnh 390px.

Đo 60 GET qua browser API request, cùng fixture hai dòng, gồm middleware,
HTTP và SQL; không phải số đo render và không đại diện 100.000 dòng/10 người:

| Chế độ | Mẫu | p50 | p95 | max |
|---|---:|---:|---:|---:|
| Toàn bảng | 30 | 23,60 ms | 24,38 ms | 26,10 ms |
| Theo phân công | 30 | 23,67 ms | 26,76 ms | 27,58 ms |

Test đọc 100 dòng ở chế độ toàn bảng giữ **trần 22 truy vấn của endpoint
lưới hiện có**, không N+1. Không tuyên bố toàn bảng nhanh hơn hay đủ tải CRM;
chưa chạy Locust hoặc phép đo quy mô lớn cho thay đổi này.

Log, JSON 60 mẫu và ảnh ở `storage/delivery-view-verification/` (ignored).
Không có mật khẩu hoặc session trong bằng chứng. Test container và database
được dọn sau kiểm chứng; không xóa Docker volume/dữ liệu đang sử dụng.

## Khi đưa vào checkout đang chạy

Phải tích hợp với thay đổi task chứng từ/dọn cũ trước, kiểm lại các file giao
nhau (`assignment_service`, grant, master grid, URLs). Áp dụng migration
0011 trước khi khởi động code mới cho ERP/CRM/worker. Chưa làm bước tích hợp
hoặc migration trên database đang dùng; giao diện ở cổng 8021 vẫn là checkout
chính, không tự nhận file trong worktree này.
