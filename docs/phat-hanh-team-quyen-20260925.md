# Phát hành Team, quyền ERP, CEO và mật khẩu — 25.09.2026

## Phiên bản và phạm vi

- Chủ dự án duyệt merge PR #53 và tiếp tục cập nhật VPS trong cùng task.
- [PR #53](https://github.com/CyrusDev1512/KNJSC/pull/53) đã merge lúc
  14:51:12 giờ Việt Nam, SHA main `85227ee7c2d289f225ea1b54cd6d5954542a6d11`.
- Image `knjsc-app:85227ee-main`, ID
  `sha256:82b39dca24b615f39eafc5f3b35fc786bd5b206b655009252572ee20506686a1`.
- Mốc quay lui: `a23573d7aaaabac1eedfa9ec169d68c7b33b2fd6`, image
  `knjsc-app:a23573d-main`. Không dùng mốc `9c4d285` của đợt trước.
- PR #53 kế thừa toàn bộ CEO/quản lý tài khoản của PR #52; không merge riêng #52.
  Mã ứng dụng và deploy của main trùng candidate `5e710ed` đã diễn tập.

Team nộp báo cáo lấy từ hồ sơ cho Staff/Leader/Manager; Admin giữ dropdown.
CEO chỉ xem báo cáo, không nộp/sửa. Quản trị ERP chỉ Admin; Bảng dữ liệu ERP
cho Manager trong phạm vi, CEO toàn công ty và Admin. Người dùng vẫn theo dõi,
tải tác vụ xuất của mình. Quyền CRM giữ nguyên theo ADR-045.

Đặt lại mật khẩu không ép đổi ở lần đăng nhập sau, vẫn hủy phiên cũ và giữ khóa
tài khoản. Manager/CEO/Admin chỉ hiện/ẩn **mật khẩu mới đang nhập**, không đọc
mật khẩu cũ. Tạo tài khoản mới vẫn phải đổi mật khẩu lần đầu; đợt phát hành
không xóa hàng loạt cờ buộc đổi đã có. Xem quyết định thay thế tại ADR-044.

## Kiểm chứng trước phát hành

[CI đúng SHA main](https://github.com/CyrusDev1512/KNJSC/actions/runs/36109781426):

| Nhóm | Kết quả |
|---|---|
| Bộ chính, `not trinh_duyet` | 2.806 đạt, 7 skip, 48 loại theo marker; 339,92 giây |
| E2E Chromium | 33 đạt, 2 skip; 171,70 giây |
| Bài trình duyệt còn lại | 1 đạt, 9 skip, 2.816 loại theo marker; 20,83 giây |

Skip không tính là đạt: nhóm dung lượng lớn; fixture dòng trắng không có;
300.000 dòng không bật; các bài cần Chrome host/proxy/server riêng. Bài trình
duyệt còn lại có cảnh báo dọn database test còn kết nối; không có assertion lỗi.
GitHub có cảnh báo action Node 20; không thay workflow trong đợt này.

Sáu E2E mới kiểm Manager/CEO/Admin ở 1440/390 px: nút hiện/ẩn bằng chuột và
bàn phím, gửi form, hash lưu đúng, không giữ mật khẩu trong form sau gửi/tải lại,
hủy phiên cũ, đăng nhập mới không ép đổi. Các kiểm này dùng database test riêng.
Lịch sử sửa lỗi test local nằm trong [biên bản chuẩn bị](chuan-bi-phat-hanh-team-quyen-20260925.md).

Diễn tập ở `/opt/knjsc-runtime/rehearsal-team-20260925/`, mạng Docker nội bộ,
không mở cổng, không worker/beat/email. 55 kiểm tra Django Client của năm vai trò
đạt; 7 đường GET bằng image cũ với schema mới đạt. Luồng ghi thử nằm trong giao
dịch rollback. Hash nghiệp vụ/tài khoản và metadata trước/sau bằng nhau; hai
cột xóa mềm mới không có giá trị ngoài dự kiến. Nhóm check/migrate mất 24 giây.

## Thực hiện trên VPS

Giữ đồng thời `deployment.lock` và `overview-release.lock`. Xác nhận checkout
sạch, runtime không đổi kể từ diễn tập; giữ nguyên cả `compose.yml` và
`compose.vps.yml`, giới hạn tài nguyên, domain và cờ tính năng. Build
`INSTALL_DEV=0`; `RUN_MIGRATIONS=0` trong các lệnh phát hành.

- Bảo trì HTTP 503: **14:58:05–14:59:14 giờ Việt Nam, 69 giây**.
- Dừng beat, ngừng web, đợi hai worker hết active/reserved/scheduled rồi dừng.
- Backup database, storage, static, cấu hình/certificate runtime; checksum đạt.
- Phục hồi dump cuối vào DB riêng `knjsc_restore_team_final`, hash so với bản
  vận hành trước migration bằng nhau. Không phục hồi vào database vận hành.
- Fast-forward checkout main tới đúng `85227ee`; không kéo thêm SHA giữa đợt.
- Django `check --deploy`: không vấn đề. Migration duy nhất
  `org.0006_ceo_and_account_soft_delete` áp thành công; kiểm không còn migration
  chờ. Các lệnh migration/kiểm mất 9 giây (14:58:46–14:58:55).
- Không chạy seed, configure_erp_reports hoặc cấu hình bảng vận đơn; metadata
  biểu mẫu, trường–cột, nguồn báo cáo và cột giữ nguyên.
- Collectstatic và khởi động năm dịch vụ cùng image; nginx kiểm và reload đạt.
- Hai domain trang đăng nhập HTTP 200. Cả hàng đợi `celery` và `crm_heavy`
  chạy thành công tác vụ accumulate không thay dữ liệu nghiệp vụ.

Đối chiếu trước/sau lúc đóng truy cập: 135 DataRecord, 15 Order, 18 OrderLine,
15 WaybillItem, 8 Customer, 10 DailyReport, 26 UserProfile, 28 auth.User; hash
các model này và các model chứng từ/lịch sử kiểm tra bằng nhau. Không chỉ đếm
số dòng. Hash UserProfile loại hai trường schema mới và kiểm chúng riêng.

## Sao lưu và quay lui

Thư mục riêng trên VPS: `/opt/knjsc-runtime/release-team-20260925-85227ee/`.
Giữ `database.dump`, `storage.tar.gz`, `static.tar.gz`, `runtime.tar.gz`,
`backups.sha256`, snapshot nghiệp vụ/metadata, log migration/check/build,
nginx trước/bảo trì và các script triển khai/quay lui. Dữ liệu và cấu hình
nhạy cảm không được chép vào Git hoặc đưa vào tài liệu này.

Nếu lỗi nghiêm trọng: bảo trì, drain, dùng `rollback.sh` trong thư mục trên để
khởi động `a23573d-main` và collectstatic từ image cũ. Giữ schema mới đã kiểm
tương thích; không tự đảo migration hoặc phục hồi toàn database. Metadata
không đổi trong đợt này nên không cần phục hồi biểu mẫu. Script quay lui không
reset checkout; phải ghi riêng SHA mã nguồn và image đang chạy nếu quay lui.

Giới hạn của bài quay lui: kiểm khả năng đọc bằng Admin với schema mới, không
chứng minh image cũ hiểu CEO/xóa mềm. Kiểm sau phát hành có 0 hồ sơ CEO và 0 hồ
sơ xóa mềm. `rollback-guard.py` sẽ chặn quay image nếu đã phát sinh một trong
hai trạng thái này; giữ bảo trì để xem xét quyền/đăng nhập trước khi mở lại,
không tự đổi vai trò hoặc mở khóa tài khoản. Chức năng CEO đã có trong mã,
đợt phát hành không tự gán CEO cho tài khoản thật.

## Theo dõi và giới hạn

Theo dõi **14:59:14–15:14:14 giờ Việt Nam**, 21 mẫu, đạt mốc ít nhất 15 phút:
năm dịch vụ đúng image, không restart hoặc lỗi ứng dụng mới, không HTTP 5xx;
hai domain đăng nhập HTTP 200. Hai hàng đợi đã chạy thử thành công. Chỉ image
thay đổi trong runtime `.env`; cả hai Compose giữ nguyên. Kết quả máy đọc được
tại [evidence](evidence/team-release-20260925.json).
Container diễn tập được dừng sau khi xác minh bản sao cuối để trả tài nguyên.

Lúc 15:08:35 có hai yêu cầu GET/PROPFIND dùng Host là IP bị `ALLOWED_HOSTS`
từ chối HTTP 400. Đã đọc traceback xác nhận đúng `DisallowedHost`; monitor
ghi riêng số lần từ chối, không gộp vào lỗi ứng dụng và không bỏ qua lỗi khác.
Không nới ALLOWED_HOSTS để làm sạch log.

Chủ dự án đăng nhập Marketing vào cuối cửa sổ theo dõi. Đã kiểm trên domain
thật bằng tài khoản Staff HUNGPT: Team “Mẫu — Marketing 01”, `readonly=true`,
không còn input `team_mau`; Marketer tự nhận diện. Không thấy Quản trị; menu
Dữ liệu chỉ còn liên kết Biểu mẫu, không có Bảng dữ liệu. Mở trực tiếp `/bang/`,
`/nhat-ky/`, `/ma-tran-quyen/`, `/tac-vu/` đều thấy trang 403. Bốn lần từ chối
có chủ đích xảy ra sau cửa sổ monitor và được giữ trong log/audit.

Kiểm 1440×900 và 390×844: chiều rộng trang bằng viewport, không tràn ngang;
đã chụp ảnh qua trình duyệt trong task và trả viewport về mặc định. Form
Marketing vẫn mở để chủ dự án sử dụng, không nộp thêm báo cáo thử.

Giới hạn: kiểm trực tiếp domain thật lần này dùng Staff Marketing; các vai
trò khác, luồng ghi/giả mạo Team, reset mật khẩu, tải tác vụ cá nhân được kiểm
bằng pytest/Chromium và bản sao diễn tập. Không đổi mật khẩu tài khoản thật
hoặc gán CEO khi phát hành. Không tuyên bố đã thao tác bằng đủ năm vai trò
trên domain thật. Không chạy tải lớn hay đo hiệu năng đa người dùng đợt này.

**Đã cập nhật VPS và hoàn tất kiểm vận hành, CI, diễn tập và UI Marketing
trong phạm vi nêu trên.** Hai khóa phát hành được nhả sau khi lưu trạng thái
cuối. Hồ sơ tài liệu đi qua PR nháp riêng; không tự merge.
