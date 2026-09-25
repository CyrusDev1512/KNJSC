# Chuẩn bị cập nhật VPS từ main — 25.09.2026

Trạng thái cập nhật 25.09: **đã phát hành `a23573d`**, xem [kết quả và các mục còn thiếu](kiem-chung-phat-hanh-pr47-pr49-20260925.md). Nội dung bên dưới giữ làm bản chụp kế hoạch trước phát hành. Phạm vi bổ sung
PR #47 và #49, đặc biệt mục 9 của Việc 3. Không dùng lại prompt phát hành cũ
đã bị gỡ bởi PR #50 vì prompt đó nhận nhầm VPS còn `72af235-gop`.

## Phiên bản và bằng chứng hiện tại

- Kiểm trực tiếp qua SSH ngày 25.09: `/opt/knjsc` ở `main`, SHA
  `9c4d285a3a873fdc05037994fe91d4b30095dd80`, checkout sạch; cả năm dịch vụ
  `crm`, `erp`, `worker`, `heavy`, `beat` đang chạy `knjsc-app:9c4d285-main`.
- SHA chuẩn bị: **`a23573d7aaaabac1eedfa9ec169d68c7b33b2fd6`** trên `origin/main`.
  `6b29d9799e252282004fe6d4e28e679200ce32d5` là merge PR #49; phần chênh tới
  SHA chuẩn bị chỉ xóa `docs/prompt-cli-phat-hanh-20260924.md` qua PR #50,
  không thay mã ứng dụng. Chốt một SHA, không kéo tiếp trong lúc phát hành.
- [PR #47](https://github.com/CyrusDev1512/KNJSC/pull/47): tạo tài khoản bỏ Email
  và Ngày sinh; sửa hồ sơ vẫn có Ngày sinh. Giữ email cũ, đăng nhập bằng mã và
  luồng mật khẩu tạm. Không migration.
- [PR #49](https://github.com/CyrusDev1512/KNJSC/pull/49),
  [ADR-043](quyet-dinh/043-form-nhap-bao-cao.md): dropdown Team, trường bắt buộc,
  bỏ Hóa đơn khỏi form nhập và bố cục ngang một thẻ. Không migration.
- Diff toàn bộ từ bản VPS đến SHA chuẩn bị không có file migration thay đổi.
  `migrate --check` trên image VPS hiện tại đạt; đây chưa phải kiểm image mới.
- Hai Compose thực tế `/opt/knjsc-runtime/compose.yml` và `compose.vps.yml`
  cùng `.env` vượt `config --quiet`. Disk trống khoảng 49 GB; RAM available
  khoảng 2,4 GB tại lần kiểm. Chưa build image hoặc diễn tập đợt mới.
- Truy vấn chỉ đọc: Marketing có 5 team hoạt động, Sale có 5; Vận đơn và Kế toán
  không có team hoạt động. Không cần seed để tạo dropdown Marketing. Theo ADR-043,
  bộ phận không có team sẽ không hiện ô Team.

## Việc 1 — Kiểm chứng trước phát hành

[CI đúng SHA a23573d](https://github.com/CyrusDev1512/KNJSC/actions/runs/36084889618)
đã hoàn tất thành công; CI tại `6b29d97` bị hủy, không tính là đạt.

| Nhóm CI | Kết quả thực tế |
|---|---|
| Bộ chính | 2.697 đạt, 7 bỏ qua, 41 không chọn; 301,54 giây |
| E2E tests/e2e | 27 đạt, 2 bỏ qua; 149,12 giây |
| Bài trình duyệt còn lại | 1 đạt, 8 bỏ qua, 2.707 không chọn, 1 cảnh báo; 20,96 giây |

Skip không phải nghiệm thu: gồm bài kiểm tải 300.000 dòng, bài cần Chrome host/proxy
riêng và một bài nhập dòng trống không có fixture phù hợp. Không chạy lại phép đo tải.
Bộ kiểm PR #47 ở `org/tests/test_account.py`, `test_ma_nhan_su.py`,
`test_temporary_password.py`; PR #49 ở `reports/tests/test_form_nhap_bao_cao.py`
và kiểm sửa báo cáo. CI kiểm server/template không thay thế nghiệm thu UI domain thật.

Còn thực hiện trước bảo trì:

1. Giữ khóa phát hành chung `deployment.lock` và `overview-release.lock`;
   dừng nếu có phiên khác giữ khóa hoặc checkout/runtime thay đổi ngoài dự kiến.
2. Build image bất biến `knjsc-app:a23573d-main`, Dockerfile hiện có,
   `INSTALL_DEV=0`; giữ nguyên hai Compose và giới hạn tài nguyên 2 CPU/4 GB.
3. Sao lưu và phục hồi DB vào môi trường diễn tập riêng, mạng nội bộ, không mở
   Internet, không beat/worker gửi thông báo. Không đưa dump/runtime vào Git.
4. Trên bản diễn tập: check, `makemigrations --check --dry-run`, `migrate --plan`,
   `migrate --check`; xác nhận không có schema còn thiếu. Chạy
   `configure_erp_reports`, kiểm trước/sau và chạy lại để xác nhận idempotent.
5. Chụp metadata FormDef/FormField/FormTableLink/FieldDef, ReportSource và ColumnDef
   trước khi cấu hình; đối chiếu số dòng/hash dữ liệu nghiệp vụ, cột Hóa đơn và
   dữ liệu Hóa đơn cũ phải còn. Không seed, gán lại team hoặc mã nhân sự.
6. Kiểm ghi bằng PR #47/#49 trên DB diễn tập: tạo tài khoản không email, đổi mật khẩu
   tạm; thiếu từng trường bắt buộc bị từ chối, số 0 hợp lệ; team cùng bộ phận được
   ghi vào cả DailyReport/DataRecord; team sai bộ phận bị từ chối; quyền Leader theo
   team được chọn; ngày/người nộp không thay đổi. Dữ liệu thử có nhãn riêng.
7. Thử image cũ `9c4d285-main` với DB đã cấu hình và thử khôi phục riêng metadata
   biểu mẫu. Ghi thời gian để ước tính bảo trì. Chỉ phát hành khi các bước đạt.

## Việc 2 — Trình tự phát hành sau khi chuẩn bị đạt

1. Xác nhận lại SHA, CI, khóa phát hành và trạng thái VPS. Giữ backup image cũ,
   static, database, tệp tải lên, metadata biểu mẫu và cấu hình runtime; kiểm checksum
   và phục hồi thử. Ghi số lượng dữ liệu trước thay đổi.
2. Bật HTTP 503 hai domain, ngừng nhận yêu cầu mới, drain yêu cầu/tác vụ rồi dừng
   năm dịch vụ ứng dụng. Giữ database/broker/cache/volume; không `down -v`.
3. Fast-forward checkout `main` đến đúng SHA đã chốt, không reset thay đổi lạ.
   Kiểm cấu hình Django; chạy migration chỉ sau khi xác nhận kế hoạch không có
   migration ngoài dự kiến; chạy `configure_erp_reports` và `collectstatic`.
   Hai PR này không yêu cầu seed, tạo/nâng bảng vận đơn hoặc cấu hình lại báo cáo
   Vận đơn. Nếu kiểm tra phát hiện cần thêm tác động thì ghi rõ trước khi làm.
4. **Không bỏ `configure_erp_reports` dù không có migration:** lệnh đặt required
   cho trường đã có và gỡ FormField Hóa đơn; chỉ đổi image không đủ để cập nhật form.
5. Đổi duy nhất image phát hành trong runtime thành `knjsc-app:a23573d-main`, bật
   năm dịch vụ cùng image bằng cả hai Compose thực tế, kiểm nginx và reload upstream.
   Mở lại sau kiểm tra cơ bản; theo dõi ít nhất 15 phút, kiểm restart/lỗi/hàng đợi.

## Việc 3 — Nghiệm thu trên domain thật

Dùng phiên đăng nhập hợp lệ, giữ ảnh và kết quả thực tế theo từng mục. Không đánh
dấu đạt dựa riêng vào biên bản cũ. Thao tác ghi thử dùng nhãn riêng, ghi ID và dọn
bằng cơ chế bỏ/soft delete được phép, giữ lịch sử. Kiểm quyền sâu trên diễn tập.

1. CRM Vận đơn: ngày đứng đầu, cột ghim/cuộn, ghi chú dài tự giãn, cột sản phẩm ẩn,
   vào/thoát chế độ tập trung; sửa một ô thử, chờ lưu và tải lại kiểm giá trị.
2. Luồng lên đơn và cảnh báo/trùng điện thoại: kiểm hồi quy với dữ liệu thử có nhãn,
   không tạo đơn giao thật; CAS cũ bị từ chối trên diễn tập.
3. Bộ lọc cột ẩn: kiểm đúng hợp đồng hiện hành trong code/test và thông báo UI;
   không dùng mô tả mâu thuẫn trong prompt phát hành đã gỡ làm yêu cầu mới.
4. CRM thư mục chỉ bảng vận đơn; ERP vẫn mở được báo cáo MKT/Sale trong phạm vi.
5. Báo cáo tổng hợp: bộ lọc nhân sự/ngày/sản phẩm, bảng toàn kỳ và từng ngày,
   chỉ tiêu/đơn vị tiền, Gộp/Không gộp, toàn màn hình và xuất Excel.
6. Lịch sử: đọc báo cáo cũ, quyền sửa/bỏ/khôi phục theo vai trò, không đổi ngày và
   người nộp. Giữ giá trị Hóa đơn và chỉ tiêu tương ứng của báo cáo cũ.
7. **PR #47:** Admin mở `/nhan-su/moi/` không có Email/Ngày sinh; tạo tài khoản
   thử không email được, mã đăng nhập và mật khẩu tạm hoạt động. Màn Sửa hồ sơ vẫn
   có Ngày sinh và lưu được; đối chiếu email/ngày sinh tài khoản cũ không bị xóa.
8. Vận hành: cả năm dịch vụ cùng SHA/image, queue hoạt động, không lỗi mới hoặc
   restart bất thường. Nếu thu p95 thì chỉ đọc log bằng script đã khảo sát;
   không chạy tải lớn, không coi số p95 thiếu mẫu là bằng chứng hiệu năng.
9. **PR #49 / ADR-043:** đăng nhập **tài khoản Marketing**, mở `/bao-cao/`:
   - Team là dropdown team Marketing hoạt động, mặc định theo hồ sơ; không lẫn
     team Sale. Chọn một team hợp lệ, nộp thử và kiểm team ở Lịch sử/báo cáo.
   - **Số Mess, CPQC, Số đơn, Doanh số bắt buộc**: thiếu từng trường bị chặn;
     kiểm phía server trên diễn tập; giá trị 0 vẫn hợp lệ.
   - **Không còn ô Hóa đơn** ở form nhập; cột, dữ liệu và chỉ tiêu Hóa đơn cũ còn.
   - **Form trải ngang một thẻ**, hàng Biểu mẫu · Team · Ngày; kiểm 1440 px và
     điện thoại 390 px không tràn ngang. Ngày hệ thống và danh tính vẫn khóa.
   - Kiểm Sale: ba trường Số Mess/Số đơn/Doanh số bắt buộc, không ép CPQC;
     kiểm form Vận đơn và màn sửa báo cáo không vỡ bố cục dùng chung.

## Việc 4 — Quay lui và bàn giao

- Mốc quay lui là **`knjsc-app:9c4d285-main`**, không phải bản `72af235-gop`.
- Khi lỗi nghiêm trọng: bảo trì, drain/dừng ứng dụng, đổi image, phục hồi static
  tương ứng, kiểm rồi mở lại. Không đảo migration hoặc phục hồi toàn DB tự động.
- PR #49 thay đổi **metadata dữ liệu** dù không có migration: giữ snapshot trước
  cấu hình và quy trình khôi phục riêng FormField/FormTableLink/required đã thử
  ở diễn tập. Không giả định đổi image sẽ tự mang ô Hóa đơn và required cũ trở lại;
  không tự phục hồi metadata diện rộng hoặc ghi đè dữ liệu mới.
- Ghi SHA/image, thời gian bảo trì, nơi backup, đối chiếu dữ liệu, kết quả 9 mục,
  ảnh PR #47/#49, các skip và theo dõi 15 phút. Chỉ ghi “đã cập nhật VPS” sau
  kiểm chứng thực tế. Tài liệu qua nhánh/PR riêng, không tự merge.

## Phần đã làm trong lượt chuẩn bị này

Đã kiểm GitHub/CI, diff mã và migration, runtime VPS/Compose, số team hoạt động;
đã lưu kế hoạch. **Chưa build, backup đợt mới, diễn tập, thay image, chạy lệnh
cấu hình ghi DB, bảo trì hoặc nghiệm thu PR #47/#49 trên domain thật.** Không sửa
mã ứng dụng, không xóa nhánh; giữ checkout cũ và `docs/test.png` không theo dõi.
