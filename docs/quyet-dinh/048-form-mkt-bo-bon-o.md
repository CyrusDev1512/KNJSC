# ADR-048 — Form báo cáo Marketing bỏ bốn ô

| Mục | Nội dung |
|---|---|
| Ngày | 03.10.2026 |
| Trạng thái | Xong local 03.10.2026, PR nháp về `Staging` — phụ thuộc PR #83 (ADR-047), gộp #83 trước; chờ chủ dự án thử local rồi gộp |
| Thay thế / bổ sung | Bổ sung ADR-047 (tiền Việt); ADR-043 (form Nộp báo cáo — thêm bốn ô vào `MKT_FORM_SKIP`); ADR-038 (Tệp khách hàng rời form và bộ lọc Marketing); ADR-042 (lọc theo sản phẩm, thị trường, tệp chỉ còn ở nguồn Sale); ADR-046 (cột Loại tiền không hiện khi báo cáo chỉ có một loại tiền cố định) |

## Bối cảnh

Chủ dự án 03.10.2026: "ở báo cáo marketing tôi đang có ý định bỏ sản phẩm, thị trường, tệp khách hàng, loại tiền
đi". Đã nghe hệ quả (mất lọc theo sản phẩm/thị trường/tệp, không tính CPO theo sản phẩm), chủ dự án chọn **"Bỏ cả bốn
ô"**. Cùng ngày: marketer nhập mọi ô tiền bằng tiền Việt, không dùng tỉ giá (ADR-047), "tạm thời làm marketing
trước"; DS Chốt (TT) "chờ KN CRM rồi làm một lượt".

Từ ADR-047 Loại tiền của báo cáo Marketing luôn là VND, nên ô Loại tiền chỉ để xem và Thị trường không còn quyết định
gì. Sản phẩm và Tệp khách hàng chỉ phục vụ việc lọc.

## Quyết định

1. **Form Nộp báo cáo Marketing bỏ Sản phẩm, Thị trường, Tệp khách hàng, Loại tiền.** Bốn cột được thêm vào
   `configure_erp_reports.MKT_FORM_SKIP` (cách đã dùng để bỏ Hóa đơn, ADR-043). Lệnh chạy mỗi lần bật máy và mỗi
   lần phát hành, gỡ trường đang có và không tạo lại. Cùng lệnh gỡ cờ bắt buộc cấp cột (`ColumnDef.required`) của
   bốn cột trên bảng Marketing, phòng khi ai đó từng bật tay ở màn "Sửa cột".
   **Cột, ánh xạ `market`, `currency`, `segment` và dữ liệu cũ giữ nguyên.** Dòng mới vẫn được ghi Loại tiền VND
   ở tầng ghi (`record_service.report_input_values` → `currency_service.report_currency`). Sale không đổi.
2. **Nộp và Sửa báo cáo Marketing không đòi Thị trường.** `daily_service.submit` chỉ kiểm Thị trường với nguồn
   không có loại tiền cố định trong `REPORT_CURRENCY` — tức chỉ còn Sale.
3. **Xem trước chỉ số giữ đơn vị.** Form không còn ô Loại tiền để đọc đơn vị, nên view truyền loại tiền cố định
   (`daily_service.fixed_currency`) thành thuộc tính `data-tien` của khối "Xem trước chỉ số". `report-entry.js`
   dùng giá trị này khi form không có ô Loại tiền.
4. **Bộ lọc của nguồn Marketing.** Báo cáo tổng hợp, Bảng dữ liệu và tệp Excel của nguồn Marketing không còn ba bộ
   lọc Sản phẩm, Thị trường, Tệp khách hàng. Tham số cũ `sp`, `thi_truong`, `tep` bị bỏ qua: không lỗi 400, không
   chip, không lọc. Phần này nằm ở một chỗ: `reports.screen.parameters` và `filter_options`, với danh sách loại nguồn
   khai ở `reports.constants.NO_DIMENSION_FILTER_KINDS`. Tầng dịch vụ (`activity_service.build`) vẫn nhận các tham
   số này cho Sale, Vận đơn và cho dữ liệu cũ.
5. **Bảng báo cáo Marketing toàn VND không có cột Loại tiền.**
   - `activity_service.build` đặt `fixed_currency` khi nguồn có loại tiền cố định và mọi dòng đúng loại tiền đó;
     `layout.with_currency` khi ấy bỏ cột.
   - Khi kéo ngang, vùng đứng yên còn STT · Nhân sự.
   - Đơn vị ghi một lần: "Tiền: ₫" ở hàng tiêu đề kết quả, và câu "Mọi số tiền là tiền Việt (₫), không quy đổi."
     trong Giải thích số liệu (Bảng dữ liệu cũng có câu này).
   - Excel giữ nhãn "TỔNG CỘNG · … · VND".
   - Có dòng mang loại tiền khác (dữ liệu ghi tay, không qua form) thì cột tự hiện lại, để không che chuyện lẫn
     tiền.
6. **Thống kê KN CRM nguồn Marketing bỏ biểu đồ "Đóng góp theo sản phẩm"**, vì dòng mới không có sản phẩm nên cột
   "Chưa có sản phẩm" sẽ chiếm gần hết biểu đồ. Sale giữ biểu đồ này.

## Hệ quả

- **Mất:** không còn lọc hay xem báo cáo Marketing mới theo sản phẩm, thị trường, tệp khách, và không tính được CPO
  theo từng sản phẩm.
- **Giữ:** giá trị cũ của bốn ô vẫn lưu và xem được ở Bảng dữ liệu dạng thô (`?dang=tho`), nhưng không sửa được ở
  "Sửa báo cáo".
- Leader Marketing không thêm được sản phẩm mới từ form Marketing; vẫn thêm được ở Lên đơn.
- Số đơn (TT) và Tỉ lệ chốt (TT) đối soát như cũ (theo marketer phụ trách và ngày lên đơn). DS Chốt (TT) vẫn "—"
  (ADR-047).
- Đoạn "— để trống khi lọc theo Tệp khách hàng" trong Giải thích số liệu bỏ, vì nguồn Marketing không còn lọc theo
  tệp.
- Không có tệp chuyển đổi mới. Phát hành chỉ cần `configure_erp_reports`, bước đã có trong quy trình.

## Việc để lại

- Báo cáo Sale: chủ dự án làm Marketing trước.
- DS Chốt (TT) bằng VND: chờ KN CRM quy vận đơn về tiền Việt rồi làm một lượt.
- `scripts/kiem-thu-erp-ui.cjs` (kịch bản tay, không chạy trong CI) đã chỉ điền Sản phẩm và Thị trường khi là Sale.
  Kịch bản này còn bước chọn ô Cách xem `#nhom`, ô đã bỏ từ 01.10 — đây là chỗ cũ có từ trước, lượt này chưa sửa.
