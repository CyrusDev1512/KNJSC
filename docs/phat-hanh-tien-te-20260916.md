# Phát hành tiền theo quốc gia và sửa cột ghim — 16.09.2026

## Cập nhật VPS theo GitHub `9ff2dec`

Theo yêu cầu tiếp theo, VPS đã fast-forward đến `9ff2dec` và dựng image
`knjsc-app:9ff2dec-sidebar-20260916`. ERP, CRM, worker, heavy, beat đều chạy
image này, giữ giới hạn tài nguyên. Checkout VPS sạch; hotfix sidebar đã
trở thành nội dung Git, đối chiếu byte trước/sau không đổi.

Backup riêng `/opt/knjsc-runtime/release-sidebar-20260916-101508`; pg_dump
thành công và pg_restore đọc được danh mục. Không thay schema/dữ liệu.
Django check ERP/CRM đạt; collectstatic và kiểm/nạp lại proxy thành công;
hai domain HTTPS 200. Chrome 1440/390 kiểm form tiền, PTTT, xác nhận quốc gia,
metadata lưới và màu ghim sáng/tối đạt, không pageerror, không lưu đơn thử.
Log: `storage/market-currency/deploy-sidebar-latest.log` và
`storage/market-currency/sidebar-vps-browser.log`.

## Bổ sung: đưa hotfix sidebar vào Git

Theo yêu cầu đồng bộ tiếp theo, bổ sung đúng hai dòng CSS đang chạy trên VPS
vào `app/static/css/crm-frame.css`: căn giữa logo và liên kết nhóm khi thu gọn
sidebar. Đối chiếu nội dung file Git với file VPS và container CRM, không đổi
hành vi đang chạy hoặc cần phát hành image mới chỉ cho lần đồng bộ này.
Giữ các thay đổi ERP chưa hoàn tất ngoài commit.

Đã push `5ce53f357521b4bc984e1d0c6ccf7a0cd887e0a0` lên
`codex/crm-update-solar-ui` và phát hành VPS. Kết quả này thay thế trạng thái
“local/chưa push/VPS” của các mục tiền, PTTT, Đơn vị phụ và cột ghim trước đó.
Không bao gồm thay đổi báo cáo/ngày nhập của tác vụ ERP đang làm song song.

## Bản chạy và bảo toàn dữ liệu

- Image: `knjsc-app:5ce53f3-market-20260916`; ERP, CRM, worker, heavy, beat
  cùng phiên bản. Giữ giới hạn RAM và hai cấu hình Compose đang sử dụng.
- Đã áp dụng `orders.0008_market_payment_methods` (SQL no-op), collectstatic
  và kiểm tra Django cho cả ERP/CRM. Không seed hoặc tạo đơn thử trên VPS.
- Backup: `/opt/knjsc-runtime/release-market-20260916/database.dump`,
  857.693 byte; đọc danh mục thành công bằng `pg_restore --list`.
  SHA256: `d42b86d5881386249fd4eca45d6712bc8a1797bd90403bffb4aec48fbc215c43`.
  Đây là kiểm đọc danh mục, không phải diễn tập phục hồi toàn database.
- Cùng thư mục lưu cấu hình trước phát hành, image cũ và diff/CSS; quyền
  thư mục 700, cấu hình 600. Không đưa thông tin đăng nhập vào Git/báo cáo.
- Giữ hotfix sidebar `crm-frame.css`, SHA256
  `123d7f0073d13af7ee0d2db539f1b9ea159ba6f06f1f31543deddb0b58782d89`.

## Kiểm chứng đúng cây mã phát hành

Xuất index đã chọn phạm vi bằng `git checkout-index` ra thư mục test riêng,
mount vào container để tránh đưa thay đổi ERP chưa hoàn tất vào kết quả.

- `pytest crm/tests orders/tests forms_builder/tests --tb=short -q
  -o addopts= --ds=knjsc.settings.test`: **535 đạt, 1 lỗi nền, 17 skip**,
  175,83 giây. Database test riêng `test_market_release`.
- Lỗi nền `test_export_import_roundtrip_and_preview_ambiguous`: kỳ vọng cũ
  cho nhập lại mã đơn đã tồn tại; đã tái hiện trên nền `7b827a6`.
- Cảnh báo teardown database test còn hai connection từ test đồng thời;
  không ảnh hưởng database vận hành. Không coi toàn suite đạt.
- Browser fixture `test_market_currency_browser.py`, Chrome 1440/390:
  **1 đạt, 49,01 giây**, bao gồm tạo đơn/xem đơn gốc, xác nhận đổi quốc gia,
  giữ số tiền, thao tác lưới và giá trị thanh toán cũ trên database test riêng.
- Node kiểm hàng đợi lưu và bài kiểm màu cột ghim đạt.

Log local trong `storage/market-currency/release-*`; các file này không nằm
trong Git vì chứa bằng chứng chạy theo môi trường.

## Kiểm tra domain thật sau phát hành

Chrome sạch, 1440/390: form chỉ có Zelle/PayPal; US/USD, CA/CAD, PH/PHP;
loại tiền chỉ đọc; xác nhận đổi quốc gia hủy/chấp nhận đúng và giữ giá trị
12,50 đã nhập thử (không lưu đơn); không còn trường Đơn vị phụ.
Metadata bảng Vận đơn DB xác nhận loại tiền được bảo vệ và hai danh mục
PTTT cùng dùng Zelle/PayPal.

Bốn lượt sáng/tối × 1440/390: cột ghim tương phản tối thiểu 13,115:1 desktop,
13,475:1 mobile; cuộn dọc/ngang hoạt động; không JavaScript pageerror.
ERP/CRM HTTPS 200. Các thao tác ghi nghiệp vụ được kiểm trên database test,
không ghi thử vào dữ liệu VPS; đợt này không đo kiểm tải.

Sau recreate container, proxy còn địa chỉ upstream cũ và trả 502 trong bước
kiểm tra đầu. Đã chạy `nginx -t` rồi `nginx -s reload`; kiểm tra domain và
toàn bộ browser ở trên đạt sau đó. Khi thay container lần sau cần nạp lại
proxy trước bước smoke test. Không nhầm lỗi này thành lỗi selector đăng nhập.

## Quay lui

Khôi phục `env.before` đã lưu, collectstatic bằng image trước phát hành,
khởi động lại các dịch vụ bằng cả hai Compose rồi kiểm/nạp lại proxy.
Giữ migration choices no-op; không phục hồi đè database để quay lui code.
Image ERP/CRM trước đó: `knjsc-app:7b827a6-pinned-contrast-20260916`;
`images.before` ghi đủ image từng dịch vụ.

## Thêm phương thức thanh toán

Manager hiện chưa có màn hình tự thêm. Danh mục thống nhất ở
`app/orders/constants.py`: thêm mã/nhãn vào `PaymentMethod` và
`ACTIVE_PAYMENT_METHODS`, tạo migration choices, kiểm thử rồi phát hành.
Không sửa tùy chọn cột riêng lẻ để vượt danh mục; giữ mã cũ phục vụ lịch sử.
Hướng dẫn tại [ADR-031](quyet-dinh/031-tien-theo-quoc-gia-va-pttt.md).
