# Chuẩn bị Vận đơn DB nhận đơn — 15.09.2026

Chủ dự án xác nhận 6.667 dòng là placeholder, cho phép chuyển cấu hình nghiệp vụ
để bảng chọn được trong Lên đơn. Giữ nguyên dữ liệu/cột và đích đang nhận đơn.

## Triển khai

Service `destination_service.prepare_existing` + management command
`chuan_bi_bang_nhan_don`: Admin, giao dịch/khóa hiện có, cấu trúc chuẩn, số dòng
xác nhận bắt buộc; audit và metadata commit cùng nhau. Không chọn bảng đích,
không xóa/import lại placeholder, không tự suy người phụ trách hoặc đơn gốc.
Giữ chặn bảng có dữ liệu chưa được chuẩn bị; đây là chuyển đổi được duyệt riêng.

## Kiểm thử local

- TDD: 3 bài đỏ trước sửa do chưa có command/service.
- `pytest crm/tests/test_prepare_destination.py crm/tests/test_order_destination.py
  crm/tests/test_delivery_view_mode.py crm/tests/test_waybill_feedback.py
  orders/tests/test_len_don.py`: **87 passed**, 22,29 giây.
- Kiểm dữ liệu/cột giữ nguyên, idempotent, số dòng lệch, cấu trúc sai, người
  không phải Admin, rollback nếu audit lỗi; lưu đơn sau chọn và phân quyền.
- `DESTINATION_PREPARE_BROWSER=1 pytest crm/tests/test_prepare_destination_browser.py
  --liveserver=0.0.0.0:8864` + `node scripts/kiem-thu-chuan-bi-bang-nhan-don.cjs`:
  **1 passed**, 25,21 giây; Chrome **1440/390 đạt**, không pageerror.
  Admin chọn Vận đơn DB đã có placeholder, Sale phiên riêng bị chặn cấu hình
  nhưng lưu được đơn vào DB, Admin đổi lại bảng cũ. Kiểm DB: 2 đơn đúng đích,
  đúng Sale, tổng Decimal=25; placeholder giữ nguyên.
- PostgreSQL/container/network test riêng; không ghi đơn test lên VPS.
  Không chạy toàn suite hoặc kiểm tải dài cho thay đổi này; không tuyên bố
  cải thiện hiệu năng lưới.

## VPS

Đã phát hành commit ứng dụng `cf51ad2`, image
`knjsc-app:cf51ad2-destination-prepare` lên ERP/CRM/worker/heavy/beat cùng phiên
bản. Hai URLconf check đạt, restart count=0, giữ giới hạn tài nguyên và hotfix
sidebar. Giữ cấu hình đăng nhập chung ERP/CRM. Không migration hoặc seed.

Backup ở `/opt/knjsc-runtime/backups/destination-prepare-20260915/`, gồm database
dump đã đọc được bằng pg_restore --list, .env/compose/image trước, hash/diff CSS.
Chạy command cho `van_don_db`, actor `admin`, expected_rows=6667.

- Giữ đủ **6.667 dòng**. SHA256 toàn bộ giá trị dòng trước/sau:
  `ebd2f7b86d21a96c4b14c112e566a145a764698838d36e7c4f5702b79ded3407`.
- SHA256 cấu trúc cột trước/sau:
  `d8bbb7c2e7fe944b9e702d60079a256bddf6ed0d63452dd4e1cc6c1b2514eeb6`.
- Đích hiện hành giữ ID=2 (Vận đơn); Vận đơn DB ID=3 có workflow=waybill,
  eligibility trả chuỗi rỗng. Không tạo Order/chi tiết/phân công giả.
- Lần chuẩn bị metadata đo được **0,108 giây** trong process đã nạp Django;
  không phải phép đo tải hoặc thời gian toàn request.
- Chrome HTTPS domain thật ở **1440/390 đạt**: option không còn disabled hoặc
  “Chưa đủ điều kiện”, chọn được DB; API đọc bảng trả đúng 6.667 dòng.
  Không submit đổi đích trên VPS hoặc tạo đơn giả; chủ dự án tự chọn thời điểm
  đổi. Luồng submit Admin → Sale lưu đã kiểm trên database test riêng.
- Kiểm container/log sau phát hành không thấy traceback, 500, lỗi CSRF/Celery;
  cấu hình cookie chung và timeout 60 phút giữ nguyên.

Đã lưu bằng chứng gọn trên VPS và dọn container/database test riêng. Admin tải
lại màn hình Bảng nhận đơn, chọn Vận đơn DB rồi bấm Lưu khi muốn chuyển đích.
