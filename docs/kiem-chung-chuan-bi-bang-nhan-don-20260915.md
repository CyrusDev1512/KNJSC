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

Đang phát hành. Trước chuyển đổi phải lưu backup và checksum toàn bộ dòng/cột;
sau chuyển đổi kiểm số dòng/hash không đổi, đích không đổi, lựa chọn được bật.
