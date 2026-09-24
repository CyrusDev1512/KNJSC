# ADR-041 — Leader/Manager bỏ và khôi phục báo cáo của cấp dưới

- **Ngày quyết định:** 24.09.2026
- **Người quyết định:** chủ dự án (hỏi–đáp 4 điểm trong phiên làm việc với Claude)
- **Trạng thái:** đã chốt, triển khai trên nhánh `claude/xoa-khoi-phuc-bao-cao`

## Bối cảnh

Khi chốt ADR-040 (24.09), chủ dự án ghi nhận khoảng trống: *"chúng ta chưa có tính
năng sửa và xoá của cấp Leader và Manager dành cho báo cáo của cấp dưới"* và yêu cầu
lập kế hoạch làm. Khảo sát mã cho thấy:

- **Quyền SỬA đã tồn tại từ 16.09** (`daily_service.can_amend` — ADR-032/038: Leader
  trong team, Manager trong bộ phận, Kế toán mọi bộ phận, Admin; có khoá phiên bản và
  `ReportRevision`; test đầy đủ ở `reports/tests/test_report_amendments.py`). Nó chỉ
  khó thấy: nút Sửa nằm trong ô đọc chi tiết của trang Lịch sử.
- **Quyền BỎ bị khoá cứng cho người nộp** (`views.bao_cao_bo` check `created_by`),
  và ADR-032 dòng 15 ghi rõ *"luồng bỏ báo cáo/xoá mềm có sẵn không được mở rộng
  quyền trong tác vụ này"* — nên mở quyền cần một quyết định mới, là ADR này.

Chủ dự án chốt 4 điểm (hỏi–đáp 24.09):
1. Quyền sửa **giữ nguyên phạm vi hiện có**; người nộp vẫn không tự sửa (nộp thêm lần mới).
2. Quyền bỏ: **người nộp (như cũ) + Leader trong team + Manager trong bộ phận + Admin;
   Kế toán KHÔNG** — giữ đúng ADR-038 ("Kế toán không bỏ báo cáo người khác"): sửa số
   là việc của Kế toán, quyết bỏ hẳn một báo cáo là việc của quản lý trực tiếp.
3. Bỏ thì **xoá mềm cả dòng số liệu** — báo cáo biến khỏi Lịch sử và số rời khỏi
   Báo cáo tổng hợp (đúng hành vi `withdraw` sẵn có, chỉ mở phạm vi người bấm).
4. **Có nút khôi phục**: Manager bộ phận mình và Admin thấy trang "Đã bỏ" và khôi phục.

## Quyết định

1. `daily_service.can_withdraw(user, report)` — một chỗ khai quyền bỏ (quy tắc 7, 11):
   người nộp | Admin | Manager cùng bộ phận | Leader đúng team (theo `report.team_id`
   — team **tại lúc nộp**, đối chiếu team mình dẫn `scope_team_ids()`, y như quyền sửa).
   `withdraw` khoá dòng và **kiểm lại quyền trong giao dịch** (mẫu như `amend`);
   đã bỏ rồi thì lần bấm sau bỏ qua êm, không nhân đôi nhật ký.
2. `daily_service.restore(report)` + `can_restore` — Manager bộ phận mình và Admin;
   trả cả `DailyReport` lẫn dòng số liệu về trạng thái sống (nội dung nguyên vẹn),
   nhật ký UPDATE "Khôi phục báo cáo". Leader bỏ được nhưng khôi phục phải nhờ
   Manager — chủ dự án chọn phương án này khi hỏi–đáp.
3. Giao diện: nút "Bỏ báo cáo này" hiện theo quyền mới; trang **"Đã bỏ"**
   (`/bao-cao/da-bo/`, phân trang 25) liệt kê báo cáo đã bỏ trong phạm vi kèm ai-bỏ-lúc-nào
   và nút Khôi phục; liên kết "Đã bỏ" trên trang Lịch sử chỉ hiện với Manager/Admin.
4. Câu khoá của ADR-032 ("không mở rộng quyền bỏ") **hết hiệu lực từ ADR này**;
   phần Kế toán của ADR-038 giữ nguyên. Khoảng trống tương ứng ghi trong ADR-040
   coi như đã xử lý (mục "Leader/Manager sửa & xoá báo cáo cấp dưới").

## Hệ quả

- Từ chối trả **403 có nhật ký** khi người gọi thấy báo cáo nhưng không đủ quyền
  (Kế toán, quản lý sai phạm vi), **404** khi ngoài phạm vi xem — quy tắc 8.
- Không migration: `DailyReport` sẵn `SoftDeleteModel`; không đụng `ReportRevision`
  (lịch sử chỉnh sửa chỉ dành cho sửa nội dung).
- Tiêu chí: **AC-4.9** (bỏ, hai chiều), **AC-4.10** (khôi phục, hai chiều); FR-4.7 mới.
  Bài cũ "chỉ người nộp mới bỏ được" viết lại theo quyền mới.
- Ma trận phân quyền đầy đủ (13 vai × sửa/bỏ/khôi phục, kèm tài khoản khoá, không hồ
  sơ, CSKH, Leader không dẫn team) khoá ở
  `reports/tests/test_ma_tran_phan_quyen_bao_cao.py` — chủ dự án yêu cầu cùng ngày.

## Không đổi

Quyền sửa (`can_amend`) và toàn bộ luồng sửa/lịch sử chỉnh sửa; quyền xem (`in_scope`);
Kế toán sửa mọi báo cáo nhưng không bỏ/khôi phục; nộp nhiều lần trong ngày (ADR-038);
BR-4 không xoá cứng.
