# Sửa màu cột ghim trên VPS — 16.09.2026

**Cập nhật phát hành:** đã push `5ce53f3` và cập nhật VPS; xem
[kết quả cuối và giới hạn](phat-hanh-tien-te-20260916.md). Các mục bên dưới
ghi nhận quá trình kiểm chứng trước phát hành.

Chủ dự án yêu cầu sửa ba cột Số điện thoại/Mã đơn/Tên khách bị nền tối,
chữ tối trong ảnh VPS. Phạm vi CSS; không đổi dữ liệu, quyền hoặc nghiệp vụ.

## Nguyên nhân và sửa

Solarpunk định nghĩa biến `--mg-pinned-*` trên phần tử cha theo theme toàn
ứng dụng. `mg-viewport` lại giữ bảng màu giấy sáng và chữ tối. CSS giải các
biến tham chiếu tại nơi định nghĩa, nên nền ghim vẫn kế thừa màu tối của cha.

Đặt biến màu ghim tại `.mg-waybill-master .mg-viewport` trong master-grid.css
để dùng cùng bảng màu giấy với chữ. Không sửa inline style do người dùng đặt,
không đổi ghim, cuộn ảo hoặc selection.

## Kiểm chứng

`scripts/kiem-thu-grid-contrast.cjs` đã được bổ sung đủ CSS theo đúng thứ tự
trang thật, đặc biệt `solarpunk.css`. Test trước đây chỉ nạp tokens/master-grid
nên không phát hiện xung đột với Solarpunk.

- Trước sửa: Chrome dựng đủ CSS tái hiện độ tương phản tối thiểu 1,003:1.
- Sau sửa: Chrome sáng/tối × 1440/390 đạt, tối thiểu 13,115:1.
- Kiểm domain CRM thật, trang `/bang-tinh/van_don_db/`, bằng phiên đăng nhập
  riêng; chỉ đọc/đổi theme trong hồ sơ test/cuộn, không tạo hoặc sửa đơn.
- VPS trước sửa: theme tối 1,003:1 ở cả hai kích thước.
- VPS sau sửa: 1440px 13,115:1; 390px 13,475:1, cùng kết quả ở sáng/tối.
  Bốn lượt không pageerror, cuộn dọc/ngang hoạt động.
- ERP/CRM HTTPS đăng nhập trả 200; log CRM không ERROR/CRITICAL/Traceback
  trong khoảng kiểm sau phát hành. `git diff --check` đạt.
- CSS không đổi SQL/đường ghi; không chạy kiểm tải/database migration.

Log và số màu ở `storage/market-currency/pinned-*`; ảnh Chrome local ở
`storage/crm-update/contrast`. Thông tin đăng nhập chỉ đọc vào RAM, không lưu
vào ảnh/trace/log. Chưa commit/push GitHub.

## Phát hành và quay lui

Image mới: `knjsc-app:7b827a6-pinned-contrast-20260916`, dựng từ image đang
chạy `knjsc-app:cf51ad2-destination-prepare`, chỉ COPY master-grid.css.
`collectstatic`: 1 file thay đổi, 150 không đổi. ERP/CRM chạy image mới;
worker/heavy/beat giữ image cũ vì không có thay đổi Python/nghiệp vụ.

Dùng đủ compose.yml + compose.vps.yml; giữ ERP 512MiB, CRM 640MiB. Không
restart database/Redis, không seed. Giữ hotfix sidebar `crm-frame.css` hash
`123d7f0073d13af7ee0d2db539f1b9ea159ba6f06f1f31543deddb0b58782d89`.
master-grid.css mới có SHA256
`70bc53fd86b74673ef228888a27e36a248efa24ecfdf193a7f4252a1f8ffd8b7`.

Checkout VPS vẫn 7b827a6, hai file CSS có thay đổi local: crm-frame.css của
hotfix trước và master-grid.css của lần này. Phải giữ hai thay đổi khi cập
nhật Git/deploy tiếp; chưa ghép các thay đổi local tiền tệ/báo cáo/Đơn vị phụ.

Backup CSS, cấu hình chọn image và script tại
`/opt/knjsc-runtime/hotfix-pinned-20260916` (thư mục 700, bản env 600).
Quay lui: khôi phục `env.before` và `master-grid.before.css`, chạy collectstatic
bằng image cũ, rồi `compose up -d --no-deps erp crm` với cả hai compose. Không
phục hồi database. Image cũ được giữ nguyên.

## Giải thích cột được hỏi

- “Trùng” là cột ảo của profile Vận đơn cũ: đếm cùng `val_phone` trong bảng,
  bỏ số trống, chỉ hiện số khi lớn hơn 1. Không tự gộp/chặn/xóa đơn; khách mua
  lại hợp lệ cũng có thể được đánh dấu. Không phải bộ chống trùng mã đơn.
- “Đơn vị phụ” là chuỗi bổ sung `Order.sub_unit` của luồng cũ, từng sao sang
  `don_vi_phu`; không dùng để tính tiền/số lượng hoặc quy đổi. Form Lên đơn và
  đơn gốc đã bỏ ở local theo yêu cầu trước; cột/database lịch sử vẫn giữ.
  Lần phát hành CSS này không xóa cột hoặc phát hành phần thay đổi form đó.
