# Kiểm chứng local — Team hệ thống và quyền menu ERP

Ngày: 25.09.2026. Nhánh `claude/team-bao-cao-va-quyen-menu`, nền ban đầu `a23573d`,
đã tích hợp đầu nhánh CEO `604910c` (mã triển khai `cd7e7a1`).
Quyết định: [ADR-045](quyet-dinh/045-team-he-thong-va-quyen-menu-erp.md).

## Trạng thái

Đã tích hợp bản hoàn tất từ task **FIX EROR**, nhánh
`claude/phan-quyen-mat-khau-xoa-tai-khoan`. Chủ dự án chốt bổ sung: **CEO chỉ xem,
không nộp/sửa báo cáo**. Các bài CEO dùng vai trò thật, không còn skip chờ tích hợp.
Đã kiểm giao diện đủ Staff, Leader, Manager, CEO, Admin trên dữ liệu riêng.

Không tạo commit mới, push, merge PR/main hoặc cập nhật VPS. Nhánh local kế thừa
commit CEO qua Git; bản thay đổi Team/menu đã lưu stash trước tích hợp và giữ
stash sau áp dụng. SHA stash nằm trong file tạm `kn-team-menu-integration-stash.txt`.
Checkout gốc và worktree tài khoản không bị thay thế. Phần Team/menu không thêm
migration/dependency; migration CEO `org.0006_ceo_and_account_soft_delete` được
kế thừa nguyên trạng, đã sao lưu và áp dụng trên database preview riêng.

## Thay đổi

- Team của Staff/Leader/Manager lấy từ hồ sơ, hiển thị chỉ đọc, server bỏ qua
  Team giả. Admin giữ chọn Team. Bỏ ô Team mẫu trùng khi nộp; sửa báo cáo cũ giữ
  Team lịch sử. Đường điền biểu mẫu trực tiếp cũng có bảo vệ Team cho Sale/MKT.
- Quản trị ERP chỉ Admin; Staff/Leader bị chặn các URL Bảng dữ liệu ERP. Manager
  còn dùng trong phạm vi. Giữ Biểu mẫu & tài liệu và nút KN CRM.
- Danh sách tác vụ ERP chỉ Admin; tiến độ/tải cá nhân vẫn hoạt động. Truy vấn
  tác vụ dùng `scope.is_admin` đã tách đúng vai trò Admin trong nhánh CEO,
  không dùng `all_departments`. CRM giữ quyền hiện hành.
- CEO không có menu/CTA nộp báo cáo; URL nộp và điền biểu mẫu trả 403, URL sửa
  báo cáo trả 404 theo hợp đồng hiện hành. Vẫn đọc lịch sử và bảng nhiều bộ phận.

## Môi trường và kiểm tự động

Container kiểm thử riêng `knjsc-team-menu-tests`, image local `knjsc-web`, bind
`app/` và `docs/` của worktree này. `RUN_MIGRATIONS=0`, pytest dùng settings test
và database riêng `test_knjsc_team_menu_test`; không dùng database preview hay
database dev. Các kiểm thuần repo cần thêm bản sao `scripts/`, `.agents/`,
`.claude/`, AGENTS/CLAUDE/PRODUCT/DESIGN vào container (không đổi Compose đang chạy).

| Kiểm | Kết quả thực tế |
|---|---|
| Hồi quy mới trước sửa Team/menu | 10 thất bại, 4 đạt; tái hiện Team nhập tay và quyền cũ |
| Nhóm liên quan sau sửa lần đầu | 142 đạt, 1 loại theo marker |
| Scope toàn công ty không được xem job người khác | Tái hiện thất bại trước sửa; đạt trong lượt cuối |
| Lượt rộng `pytest -m 'not cham and not trinh_duyet' --tb=short` | 2.698 đạt, 2 thất bại truy vết tài liệu, 1 skip, 62 loại theo marker; 306,08 giây |
| Sửa hai số liệu docs/06 và kiểm lại nhóm mới + truy vết | **56 đạt, 1 skip CEO, 1 loại theo marker**; 8,89 giây |
| Hai đường điền biểu mẫu trực tiếp Sale/MKT | 2 đạt; đã được bao gồm trong 56 bài ở lượt cuối |
| Django `check` | Không có lỗi |
| `makemigrations --check --dry-run` | Không có thay đổi model |

Hai lỗi của lượt rộng là đếm tiêu chí trong docs/06 (bản cũ ghi 269 và 233/256).
Đã cập nhật theo bộ phân tích thực tế: 275 tiêu chí, 262 tự động, 13 thủ công;
239 tiêu chí có bài kiểm. Các kết quả 56 bài/skip CEO ở trên là **trước tích hợp**;
không đại diện cho trạng thái CEO hiện tại.

Lệnh kiểm trước tích hợp:

```powershell
docker exec knjsc-team-menu-tests pytest core/tests/test_quyen_menu_erp.py core/tests/test_quyen_ceo_erp.py reports/tests/test_team_he_thong.py tests/test_truy_vet.py crm/tests/test_master_capacity.py -m 'not cham and not trinh_duyet' --tb=short -rs
```

Skip của lượt rộng là `crm/tests/test_scroll_fixture.py`: chỉ xuất fixture đo
cuộn riêng khi bật `GRID_SCROLL_FIXTURE=1`; đã xác nhận bằng `pytest ... -rs`.
Không bật kiểm tải. Nhóm trình duyệt pytest chưa chạy; kiểm UI bằng trình duyệt
Codex được ghi riêng dưới đây, không tính thành E2E tự động.

Log trên máy thực hiện:
`C:/Users/PC/AppData/Local/Temp/kn-team-menu-suite-final.log` và
`C:/Users/PC/AppData/Local/Temp/kn-team-menu-verification.log`.

### Sau tích hợp CEO

- TDD cho menu nộp của CEO: 1 thất bại, 1 đạt trước sửa; đã ẩn menu/CTA và
  chặn đường nộp bằng kiểm quyền ghi nghiệp vụ sẵn có của nhánh CEO.
- Nhóm Team/menu/CEO/tài khoản: **80 đạt**, 11,96 giây.
- Lượt rộng trên bản tích hợp: **2.786 đạt, 1 thất bại, 1 skip, 63 loại theo
  marker**, 325,45 giây. Bài mới đòi 403 ở URL sửa, trong khi view đã chặn bằng
  404 từ trước. Sửa kỳ vọng thành đúng 404, vẫn kiểm cả GET/POST và dữ liệu không
  đổi; không sửa quyền hoặc nới điều kiện chấp nhận của endpoint.
- Django `check` và `makemigrations --check --dry-run` sau tích hợp đều đạt.
- Lượt cuối sau sửa kỳ vọng: **117 đạt, không skip**, 14,09 giây; gồm toàn bộ
  file Team/menu/CEO, quản lý tài khoản và truy vết tài liệu. Không chạy lại toàn
  suite vì mã ứng dụng không đổi sau lượt rộng; kết quả rộng vẫn ghi đúng ở trên.

  ```powershell
  docker exec knjsc-team-menu-tests pytest core/tests/test_quyen_menu_erp.py core/tests/test_quyen_ceo_erp.py reports/tests/test_team_he_thong.py org/tests/test_account_management.py tests/test_truy_vet.py -m 'not cham and not trinh_duyet' --tb=short -rs
  ```

- Log: `kn-team-menu-ceo-red.log`, `kn-team-menu-ceo-green.log`,
  `kn-team-menu-integrated-suite.log`, `kn-team-menu-integrated-final.log`
  trong `C:/Users/PC/AppData/Local/Temp/`.

## Kiểm bằng trình duyệt

Preview riêng: <http://localhost:18030/bao-cao/>, container
`knjsc-team-menu-preview`, DB `knjsc_team_menu_preview_20260925`. Chỉ bind localhost,
không thay dịch vụ 8020/8021. Tài khoản `test_staff`, `test_leader`, `test_manager`,
`test_admin`, `test_ceo` và toàn bộ dữ liệu tại đây là mẫu riêng.

- Bốn vai trò đã được đăng nhập kiểm: Staff/Leader/Manager Team chỉ đọc, Admin
  có dropdown. Menu Quản trị chỉ Admin; Bảng dữ liệu chỉ Manager/Admin.
- Staff mở Dữ liệu chỉ thấy Biểu mẫu & tài liệu; gõ thẳng `/bang/` thấy lỗi 403.
  KN CRM vẫn hiện. `/tac-vu/1/` của Staff mở được, `/tac-vu/2/` của Leader trả 404.
- Staff nộp báo cáo mẫu ID 1, Team Marketing 01; Admin chọn Team Marketing 02
  nộp ID 2. Lịch sử hiển thị đúng Team trên nội dung và danh tính cuối báo cáo.
  Giữ các báo cáo này để xem thử; không tạo dữ liệu trên VPS.
- Staff mở Báo cáo tổng hợp, bấm Xuất Excel: trình duyệt nhận sự kiện download.
  Kiểm job hoàn tất và tải nội dung file cá nhân qua endpoint nằm trong bài tự động.
- Điện thoại 390 px: `innerWidth == scrollWidth == 390`, Team readonly và không
  tràn ngang; ảnh đã hiển thị trong cuộc trao đổi. Desktop đã kiểm form/menu,
  trả viewport trình duyệt về mặc định sau kiểm.
- CEO đăng nhập thật: đọc bảng Marketing và bảng mẫu Sale `ceo_sale_preview`;
  có thông báo chỉ đọc, không có điều khiển sửa. Menu Báo cáo chỉ có lịch sử và
  tổng hợp; không có Quản trị. Gõ `/bao-cao/` trả 403 đúng thông báo chỉ xem.
- CEO đọc được cả hai báo cáo mẫu trong lịch sử, không có nút nộp/sửa/bỏ.
  Desktop 1440 px và điện thoại 390 px: chiều rộng nội dung bằng viewport;
  ảnh đã hiển thị trong cuộc trao đổi. Hai báo cáo vẫn còn sau migration CEO.

## Giới hạn kiểm chứng và bàn giao

Không chạy nhóm pytest trình duyệt hoặc bài tải lớn; kiểm UI thủ công riêng ở
trên không được tính thành E2E tự động. Các bài bị loại theo marker chưa được
kiểm chứng trong tác vụ này. Không dùng dữ liệu thật hoặc kiểm lại trên VPS.
Bản local và diff chưa commit được giữ để chủ dự án xem; PR #52 của phần CEO
vẫn là phụ thuộc, chưa tự merge. Không có quyền phát hành trong tác vụ này.

## Chuyển checkout để chủ dự án test local

Theo yêu cầu tiếp theo ngày 25.09.2026, đã chuyển `C:/KNJSC/KNJSC` sang nhánh
`claude/team-bao-cao-va-quyen-menu` và mang đủ 44 file thay đổi chưa commit về.
Worktree preview cũ giữ nguyên nội dung tại detached HEAD `604910c`; không còn
là nơi chỉnh sửa chính. File có sẵn `docs/test.png` ở checkout gốc giữ nguyên.

Sao lưu database và file trước chuyển tại
`C:/KNJSC/local-backups/team-menu-20260925/`; có dump, patch, manifest SHA256.
Đã áp dụng riêng migration kế thừa `org.0006` trên database local `knjsc_db`,
không seed hoặc thay tài khoản. ERP/CRM ở 8020/8021 đã nạp lại mã, Django check
đạt, không còn migration chờ; HTTP trang đăng nhập cả hai cổng trả 200.
Worker/beat local được khởi động lại để nhận mã. Không tác động VPS/GitHub,
không tạo commit mới.
