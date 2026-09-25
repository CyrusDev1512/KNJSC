# Chuẩn bị phát hành Team, quyền ERP và mật khẩu — 25.09.2026

> Cập nhật: chủ dự án đã duyệt merge PR #53; VPS nhận main `85227ee`.
> Đây là ghi chép giai đoạn chuẩn bị. Trạng thái sau phát hành và giới hạn
> kiểm chứng nằm tại [biên bản phát hành](phat-hanh-team-quyen-20260925.md).

## Phạm vi và mốc quay lui

Chủ dự án yêu cầu kiểm kỹ rồi đưa lên VPS. Bản này gồm định nghĩa CEO và quản
lý tài khoản từ PR #52, Team tự nhận diện, giới hạn menu/URL ERP theo ADR-045,
và quyết định thay thế về đặt lại mật khẩu tại ADR-044. Không triển khai phương
án lưu mật khẩu có thể giải mã. Giữ quyền CRM hiện hành.

Kiểm trực tiếp lúc bắt đầu: VPS sạch, checkout `main a23573d`, năm dịch vụ cùng
image `knjsc-app:a23573d-main`; đây là mốc quay lui. GitHub `main` vẫn `a23573d`,
PR #52 đang nháp. Bản Team/menu kế thừa `604910c`, chưa nằm trên main.

Không tự merge. Sau khi có PR cụ thể đã kiểm, cần chủ dự án duyệt bước merge
theo AGENTS.md; chỉ phát hành SHA trên main với CI đạt. Không dùng image nhánh
ứng viên thay phiên bản đang chạy. File có sẵn `docs/test.png` không thuộc đợt này.

## Kiểm chứng local

- Bộ chính theo CI, gồm nhóm chậm thông thường, database test riêng:
  **2.804 đạt, 2 lỗi, 7 skip, 48 loại theo marker**, 403,91 giây. Hai lỗi đã
  được xử lý: lớp CSS không tồn tại ở nút hiện mật khẩu; bài đo Bảng dữ liệu
  còn dùng Staff dù ADR-045 đã chặn cấp này. Đổi sang Manager cho ERP, giữ Staff
  cho CRM, giữ nguyên ngưỡng 2 giây và 10 truy vấn.
- Nhóm xác nhận sau sửa (toàn bộ kiểm giao diện, bài đo 50.000 dòng trong suite,
  quản lý tài khoản): **682 đạt**, 40,03 giây. Không bật fixture 100k/300k.
- E2E Chromium lượt đầu: **32 đạt, 1 lỗi, 2 skip**, 204,23 giây. Lỗi fixture
  thiếu Manager Vận đơn trong bài điện thoại đã được bổ sung. Bài điện thoại
  cũng được sửa URL báo cáo cũ và bắt HTTP 200 để tránh đo nhầm trang lỗi.
- Có sáu E2E mới cho Manager/CEO/Admin ở 1440/390: nhập mật khẩu mới, hiện/ẩn,
  bấm bằng bàn phím, gửi form, hash lưu đúng, ô trống sau gửi/tải lại, phiên cũ
  mất hiệu lực và đăng nhập mới không bị ép đổi. Dữ liệu hoàn toàn nằm trong DB test.
- Kiểm lại hai file E2E sau sửa: **10 đạt**, 50,72 giây. Nhóm trình duyệt còn
  lại theo CI: **1 đạt, 9 skip**, 24,39 giây; có cảnh báo dọn DB test vì còn một
  kết nối, không phải lỗi assertion. Các skip cần Chrome host/proxy/server riêng.

Log nằm tại `%TEMP%/kn-team-release-*.log`; ảnh ở container kiểm `/storage/e2e/`
và bản sao local ngoài Git. Không đưa bản sao dữ liệu VPS, cấu hình hoặc khóa vào Git.

## Diễn tập và phát hành

Chuẩn bị candidate bằng Dockerfile hiện có, `INSTALL_DEV=0`. Phục hồi database
VPS trong mạng Docker `--internal`, không mở cổng, không worker/beat hoặc gửi
thông báo. Giới hạn bộ nhớ/CPU cho container diễn tập, giữ hai Compose thật.

Chỉ có migration kế thừa `org.0006_ceo_and_account_soft_delete`; kiểm model,
migration plan, dữ liệu trước/sau và chạy lại image cũ trên schema mới. Không
chạy lại cấu hình biểu mẫu/bảng vận đơn, seed hoặc gán lại nhân sự/team.
Các luồng ghi thử chạy trong transaction rollback trên bản sao. Đối chiếu
metadata nguyên trạng, hash dữ liệu nghiệp vụ và trường tài khoản cũ; riêng
hai cột mới `deleted_at/deleted_by_id` được kiểm bổ sung, không đưa vào hash
so schema cũ/mới. Diễn tập phải đạt trước bảo trì.

Khi được duyệt merge và SHA main đạt CI: lấy cả hai khóa phát hành, xác nhận
runtime/checkout không đổi ngoài dự kiến, build image main. Bật 503, drain,
sao lưu database/storage/static/runtime, kiểm phục hồi dump cuối rồi mới áp
migration và collectstatic. Giữ `RUN_MIGRATIONS=0`; năm dịch vụ dùng một image.
Kiểm domain và theo dõi ít nhất 15 phút trước kết luận phát hành xong.

Nếu lỗi nghiêm trọng: bảo trì và quay image/static về `a23573d-main` theo cách
đã diễn tập; không tự đảo migration hoặc phục hồi toàn database vận hành.
Nếu nghi hỏng dữ liệu, giữ bảo trì và báo phạm vi trước khi phục hồi.

## Trạng thái

Đang chuẩn bị; **chưa cập nhật VPS**. Kết quả CI, diễn tập và quyết định merge
sẽ được bổ sung bằng bằng chứng của đúng SHA ứng viên.
