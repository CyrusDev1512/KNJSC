# ADR-040 — KN CRM chỉ còn một bảng Vận đơn, bỏ cấp Quý ▸ Tháng

- **Ngày quyết định:** 24.09.2026
- **Người quyết định:** chủ dự án (trong phiên làm việc với Claude, sau đợt soát ADR-036)
- **Trạng thái:** đã chốt, triển khai trên nhánh `claude/crm-chi-mot-bang-van-don`

## Bối cảnh

Sau đợt gộp một bảng vận đơn (ADR-036, 18.09) chủ dự án soát lại và chốt bốn điều
về ranh giới hai dịch vụ (24.09.2026, nguyên văn):

1. **Bảng Sale và Marketing: input – output đều bên ERP.** Báo cáo ngày nhập bằng
   biểu mẫu ERP, xem bằng Báo cáo tổng hợp và Bảng dữ liệu ERP.
2. **Chưa có tính năng sửa và xoá của cấp Leader/Manager dành cho báo cáo của cấp
   dưới** — ghi nhận là khoảng trống, chờ làm (chưa quyết khi nào).
3. **KN CRM hiện tại chỉ có Bảng tính của Vận đơn.**
4. **Thống kê lấy thông tin từ cả hai bên** — trang Thống kê KN CRM vẫn đọc nguồn
   Sale/MKT, không bỏ.

Ngoài ra cấp **Quý ▸ Tháng** của trang thư mục (ADR-012) là góc nhìn tự sinh từ cột
Ngày, không phải thư mục lưu; khi CRM chỉ còn một bảng thì hai cấp đó thành thừa —
chủ dự án chốt **bỏ hẳn**, lọc thời gian là việc của bộ lọc trên lưới.

**Ràng buộc quan trọng nhất: dữ liệu không đổi một dòng nào.** Bảng thường chỉ
không hiện và không mở được ở dịch vụ 8021; ERP đọc ghi như cũ.

## Quyết định

1. **KN CRM chỉ phục vụ bảng vận đơn** (mã `van_don` hoặc `workflow="waybill"`).
   Điều kiện lọc đặt một chỗ duy nhất `crm/services/catalog.chi_van_don` (quy tắc 7),
   áp ở mọi cửa: trang chủ tổng quan (ô số, Bảng gần đây, **cả Hoạt động gần đây**),
   thư mục, sidebar, lưới + mọi endpoint JSON (`table_for`), Nhập tệp, Cấp quyền,
   và các route forms_builder theo mã bảng trên URLconf 8021 (guard
   `_chi_bang_van_don`). Bảng thường trả 404/403 như ngoài phạm vi, kể cả Admin.
2. **Bỏ cấp Quý ▸ Tháng**: trang thư mục phẳng Bộ phận ▸ thư mục ▸ bảng
   (`tree_service.build` viết lại; `Quarter`, `quarters`, `month_counts`,
   `parse_month/quarter` xoá). Giữ `Month` + `month_of_params` cho nhãn
   "Tháng x/nnnn" trên thanh lưới khi bộ lọc ngày vừa đúng một tháng; URL cũ mang
   `quy`/`thang`/`tat-ca` bị bỏ qua, không lỗi.
3. **Thống kê giữ nguyên** — đọc số liệu từ cả bảng vận đơn lẫn nguồn báo cáo
   Sale/MKT (điều 4 của chủ dự án). Không đụng `statistics_views`.

### Bốn quyết định phụ (hỏi–đáp cùng ngày)

| Việc | Chốt |
|---|---|
| Nút "+ Tạo bảng" (chỉ KN CRM có) | **Ẩn nút, giữ đường dẫn** `/bang/moi/` — quản lý cần gấp vẫn vào bằng địa chỉ; bảng thường tạo ra quản lý tiếp bên ERP |
| Trang "Đã xóa" (xoá/khôi phục bảng) | **Giữ mọi bảng** — là cửa quản trị duy nhất, lọc mất là hết đường khôi phục bảng thường |
| Khối Hoạt động gần đây ở trang chủ | **Lọc chỉ vận đơn** (dòng, bảng/cột vận đơn, đơn gốc) |
| Bảng thường hết chỗ sửa ô (ERP chỉ đọc theo ADR-014, CRM không phục vụ) | **Chấp nhận: bảng không phải vận đơn sửa bên ERP** (biểu mẫu, nhập tệp); đây là hướng tạm, **tương lai có thể đổi** — chủ dự án dặn ghi rõ |

## Hệ quả

- Dòng vận đơn chỉ sinh từ Lên đơn (`protect_table` của profile) nên khi CRM chỉ
  còn bảng vận đơn, tính năng "dòng trống cuối lưới sinh dòng thật" **chết trên
  toàn sản phẩm** — AC-11.14 viết lại thành chiều bị từ chối.
- Bài kiểm tính năng lưới chuyển đạo cụ sang bảng mang `workflow="waybill"`;
  các hành vi generic-qua-HTTP kiểm ở mức dịch vụ (AC-40.4).
- `sidebar_service` sửa một lỗi tiềm ẩn lộ ra khi kiểm: bảng workflow vận đơn
  thiếu cột chuẩn làm trang lưới đổ 500 — nay bỏ nhóm lọc thiếu cột, không đổ.
- Trang Đã xóa và đường dẫn Tạo bảng là hai ngoại lệ có chủ đích (bảng quản trị,
  không phải nơi làm việc) — ghi ở đây để không ai tưởng là sót.

## Khoảng trống ghi nhận (chưa làm, chờ chủ dự án xếp lịch)

- Leader/Manager **chưa sửa và xoá được báo cáo của cấp dưới** (điều 2 ở trên).
- Nơi sửa từng ô cho bảng thường: hiện không có; nếu nghiệp vụ cần thì quyết
  riêng (mở sửa bên ERP là đổi ADR-014).

## Không đổi

Dữ liệu mọi bảng; toàn bộ KN ERP (biểu mẫu, Báo cáo tổng hợp, Bảng dữ liệu chỉ
đọc, quản lý cột); Thống kê KN CRM; Lên đơn; phân quyền và Custom Manager.
