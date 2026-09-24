# ADR-041 — Form Nộp báo cáo ngày: chọn Team, bốn trường bắt buộc, bỏ Hóa đơn, bố cục ngang

| | |
|---|---|
| Ngày | 24.09.2026 |
| Trạng thái | Xong local, cùng PR nháp #36 với ADR-040; chờ chủ dự án nghiệm thu và Codex phát hành |
| Bổ sung | ADR-032 (ngày hệ thống, sửa báo cáo — giữ), ADR-037 (danh tính tự ghi — giữ), ADR-038 (Hóa đơn: giữ cột và chỉ tiêu, bỏ ô nhập), ADR-028 (Solarpunk — áp cho form) |

## Bối cảnh

Chủ dự án xem thử nhánh ADR-040 trên local và góp ý về màn **Nộp báo cáo ngày** (`/bao-cao/`):
chọn Team bằng dropdown các team đang có; Số Mess, CPQC, Số đơn, Doanh số bắt buộc; bỏ trường Hóa đơn
khi nhập; thiết kế lại view cho "full view", chia ngang, ô nhập nhỏ.

Trước đó: form không có ô Team — dòng lấy team theo hồ sơ người nộp nên tài khoản chưa gán team ra
"Chưa có team" ở báo cáo; chỉ Số Mess (MKT) bắt buộc và dấu `*` chỉ là chữ; `configure_erp_reports`
tự đưa mọi cột nhập lên form kể cả `hoa_don`; hai thẻ `max-width:860px`, lưới `.bm` một cột, ô cao 40 px
rộng hết thẻ.

## Quyết định

1. **Dropdown Team** (`daily_service.team_choices/resolve_team`): team đang hoạt động của bộ phận sở hữu
   biểu mẫu, chọn sẵn team hồ sơ; ai cũng chọn được team khác trong bộ phận; team đã chọn ghi vào
   `DataRecord.team` **và** `DailyReport.team` (`create_record(team=)`, `fill(team=)`, `submit(team=)`) nên
   cột Team của Báo cáo tổng hợp / Bảng dữ liệu và phạm vi Leader (`apply_scope`, `can_amend`) đi theo lựa
   chọn. Team bộ phận khác hay id lạ → từ chối rõ (quy tắc 8); để trống → theo hồ sơ; bộ phận không có
   team → không hiện ô. Màn Sửa báo cáo không đổi team (giữ như ngày, danh tính — ADR-032).
2. **Bắt buộc** khai một chỗ: `configure_erp_reports.REQUIRED_INPUTS = (ngay, san_pham, thi_truong, so_mess,
   cpqc, so_don, doanh_so)`; trường mới lẫn trường đã có đều bị ép `required=True` mỗi lần chạy (lệnh chạy ở
   mỗi lần bật máy). Sale không có `cpqc` nên tự ra ba trường số. Phía trình duyệt thêm thuộc tính `required`
   (`_truong_nhap.html`, `o_chon.html`); máy chủ vẫn là nơi quyết (`form_service.missing_required`, AC-8.2).
3. **Hóa đơn** rời form nhập MKT bằng `MKT_FORM_SKIP = (doanh_thu cũ, hoa_don)` — cơ chế `skip` sẵn có gỡ
   trường đang có và không tạo lại. Cột `hoa_don`, ánh xạ `invoice`, chỉ tiêu "Hóa đơn" và "Hóa đơn/DS Chốt
   (TT)" **giữ** cho dữ liệu cũ (chủ dự án chốt "chỉ bỏ khỏi form nhập"); dòng mới hiện "—".
4. **Bố cục** theo quy trình Impeccable thủ công (đọc DESIGN.md, design.json, craft-floor; không chạy engine):
   một thẻ, không thẻ lồng thẻ; hàng điều khiển Biểu mẫu · Team · Ngày trên nền phụ; lưới `.bm-ngang`
   `repeat(auto-fill, minmax(168px, 1fr))`, ô `.o-nhap` 34 px, nhãn 13 px, số tabular; cột tính sẵn là dòng chip
   `.bm-tinh` thay cho năm ô nhập giả; ô chữ dài (Vận đơn) chiếm trọn hàng; ≤ 600 px hai cột. Chỉ thêm lớp
   trong phạm vi `.bm-ngang/.bm-dau/.bm-tinh`, không đụng `.bm`, `.truong`, `.o-nhap` dùng chung ở ~20 form.
5. **Dữ liệu mẫu** thêm team MKT 1 (trưởng nhóm `mkt.leader`, thành viên `mkt.staff`); tài khoản mẫu có sẵn
   mà chưa có team thì được gán khi chạy lại `du_lieu_mau`.

## Hệ quả

- Tiêu chí AC-41.1 → 41.4 (`docs/04` mục 41); FR-4.7 → FR-4.10.
- `test_new_marketing_report_derives_currency_and_keeps_zero` đổi: dòng mới không có `hoa_don`.
- Script `.cjs` điền form (`kiem-thu-erp-ui`, `kiem-thu-erp-identity`) phải điền đủ bốn trường số.

## Giới hạn, việc để lại

- Team chọn sai (nhân viên chọn team bạn) thì Leader team đó thấy và sửa được báo cáo — chấp nhận, vì đó là
  lựa chọn có chủ ý; quản lý sửa lại team qua Lịch sử chưa có (chưa cần).
- FieldDef `erp_<pk>_hoa_don` mồ côi sau khi gỡ trường để nguyên, không hại.
