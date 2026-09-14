# Solarpunk Office — bản xem thử 14.09.2026

## Chạy và xem

Worktree `C:/KNJSC/worktrees/ui-solarpunk`, nhánh `codex/ui-solarpunk`,
từ `fix/trung-ma-don-dong-thoi` tại `95988c9`, kèm toàn bộ thay đổi chưa commit.
Checkout `C:/KNJSC/KNJSC` giữ nguyên. Bản chụp kế thừa ở
`C:/KNJSC/worktrees/ui-solarpunk-baseline-20260914` gồm tree, SHA256 manifest,
Git status và patch ban đầu.

```powershell
docker compose -f deploy/docker-compose.solarpunk.yml up -d
```

- ERP: http://localhost:18020/
- CRM: http://localhost:18021/
- Tài khoản dữ liệu mẫu: `quantri`, `sale.manager`, `sale.leader`, `sale.staff`,
  `mkt.staff`; mật khẩu chung của môi trường mẫu: `matkhaucuatoi`.
- Database `solarpunk`, volume và cookie riêng. Không dùng dữ liệu khách hàng.
- Khởi tạo mới: `exec -T web python manage.py migrate --noinput`, sau đó
  `du_lieu_mau` và `du_lieu_solarpunk`. Lệnh cuối tự chặn ngoài DB/settings preview.

## Đã triển khai

Khung và thành phần chung của mọi trang kế thừa bốn base: ERP, CRM thư mục,
lưới, đăng nhập/tài khoản/lỗi. Chất liệu mới, nền kiến trúc tối ưu, sáng/tối,
điều hướng dưới có bàn phím, bố cục báo cáo hai vùng, form/danh sách/thư viện/
bảng tin/tổng quan/thư mục và popup đồng bộ. Không thay Django Admin.

Hai lưới dùng chung controller `grid-focus.js`. Công cụ gốc và trạng thái lưu
được giữ, không thay logic ghi dữ liệu hoặc backend. Chi tiết ở ADR-027.

## Bằng chứng trình duyệt

Các script chạy Chrome headless trên dữ liệu mẫu riêng; kết quả/ảnh ở
`artifacts/solarpunk/` (bỏ qua trong Git, giữ trên máy để review).

- `node scripts/kiem-thu-solarpunk.cjs`: fail đúng hành vi header còn hiện
  trước thay đổi; pass sau thay đổi. Kiểm cả master/legacy, công cụ, Esc,
  trình sửa ô, popup và hình học ô.
- `node scripts/kiem-thu-solarpunk-save.cjs`: lưu đang chờ qua chuyển chế độ,
  hoàn tác, lỗi mạng/thử lại, dán 2 dòng và hoàn tác — pass.
- `node scripts/kiem-thu-solarpunk-conflict.cjs`: hai yêu cầu ghi CAS thật,
  lỗi/xung đột và hộp đối chiếu hiện rõ, Esc không thoát nhầm; cột ghim và
  vị trí cuộn qua chuyển chế độ — pass. Khôi phục dữ liệu tổng hợp sau kiểm tra.
- `node scripts/audit-solarpunk.cjs`: duyệt các liên kết menu theo Admin,
  Manager, Leader, Staff; ảnh desktop/điện thoại và báo cáo overflow/JS.
  404 khi Sale truy cập trực tiếp bảng Marketing là chặn quyền dự kiến.
  Liên kết thư mục mặc định của Manager/Leader Sale trả 404 trên seed hiện có;
  không sửa quyền hay backend trong nhánh UI.
- `node scripts/kiem-thu-solarpunk-layout.cjs`: 1920×1080, 1440×900,
  1366×768, 768×1024, 390×844; thêm viewport 1152×720 mật độ 1,25 và
  720×450 mật độ 2 để mô phỏng không gian CSS của zoom 125%/200% trên màn
  1440×900. Cả sáng/tối, báo cáo/lưới/tập trung: không tràn trang hoặc đè dock.
  Đây là mô phỏng viewport/mật độ, không phải thao tác menu zoom của Chrome.

## Suite, hiệu năng và diff

- Baseline nguyên vẹn, chạy trên database test mới: **2153 passed, 15 failed,
  28 skipped, 2 xfailed**, 272,45 giây. Log `baseline-fresh-tests.txt`.
  Lượt baseline đầu bị kẹt ở dọn 50.000 dòng test nên đã dừng container kiểm
  riêng và chạy lại với tên database test mới; không reset dữ liệu preview/thật.
- Full suite UI: **2154 passed, 14 failed, 28 skipped, 2 xfailed**, 260,74 giây.
  Log `ui-final-tests.txt`. Trong 14 lỗi, 13 trùng baseline; một bài kiểm
  nhận diện khung ERP giữ chuỗi tiêu đề cũ đã được cập nhật theo ADR-027 và
  chạy lại: **1 passed** (`crm-shell-final.txt`). Không còn lỗi mới do UI
  trong tập so sánh sau lượt chạy lại này. Không tuyên bố full suite xanh.
- Nhóm HTML/CRM shell/báo cáo cuối: **590 passed, 2 failed** (hai lỗi đã có ở
  baseline). Đã bổ sung CSS thống kê vào bộ kiểm tra và nhãn trực tiếp cho
  ô lọc thống kê, giải quyết hai lỗi markup nền nằm trong phạm vi UI.
- 28 skip của suite không được tính là kiểm chứng trình duyệt. Các script
  Chrome riêng ở trên thực sự đã chạy và đạt. Audit gồm **88 lượt HTTP,
  115 quan sát bố cục, 0 lỗi JavaScript và 0 tràn ngang**.
- `manage.py check` trên cả web và bangtinh: không có vấn đề. `git diff
  --check`: đạt. SHA256 xác nhận 0 khác biệt của checkout gốc so với bản
  chụp đầu phiên (769 đường dẫn trong manifest).

Đo Chrome headless, 1440×900, 120 dòng tổng hợp, cùng DB và máy. 30 bước
cuộn, 15 bước chọn/mở trình sửa; đo thời gian tới hai requestAnimationFrame,
không phải INP ngoài thực tế hoặc độ trễ gõ IME của người dùng.

| Phép đo trung vị | Baseline | UI |
|---|---:|---:|
| Cuộn, tới hai frame | 33,4 ms | 33,4 ms |
| Chọn ô, tới hai frame | 32,3 ms | 32,5 ms |
| Mở trình sửa, tới hai frame | 33,4 ms | 33,3 ms |
| Long task trong lượt đo | 0 | 0 |
| Ô đang render | 360 | 360 |

Không có blur trên ô; lượt đo ngắn không cho thấy suy giảm đáng kể.
Đây không phải kiểm tải/cam kết hiệu năng trên dữ liệu thực hàng triệu dòng.
Chi tiết: `performance.json`; script `profile-solarpunk.cjs`. Container tham
chiếu 18022 dùng lúc đo đã dừng; hai preview 18020/18021 vẫn chạy.

Diff UI được tạo bằng `python scripts/solarpunk-diff.py`: so SHA256 với
manifest đầu phiên rồi xuất patch **có binary asset** ở
`artifacts/solarpunk/ui-only.patch`, danh sách tại `ui-files.json`.
Patch có đường dẫn chuẩn `a/...`, `b/...`; khi áp thủ công
cần xem trước bằng `git apply --check -p1`. Không áp lên checkout gốc trong
phiên này. Toàn bộ diff Git thông thường còn gồm thay đổi kế thừa.

## Giới hạn còn lại

Chưa kiểm menu zoom thực của trình duyệt (đã mô phỏng viewport tương ứng),
chưa đo phần cứng yếu hoặc IME tiếng Việt thực. Audit vai trò là duyệt/đọc
menu; không phải mọi tổ hợp thao tác nghiệp vụ đều đã được tự động hóa bằng
Chrome. Kiểm ghi thực tập trung vào lưới, suite kiểm nghiệp vụ/phân quyền
vẫn có 13 lỗi nền như trên. Bản này là nhánh xem thử để chủ dự án đánh giá,
chưa merge, chưa commit/push và chưa triển khai thật.
