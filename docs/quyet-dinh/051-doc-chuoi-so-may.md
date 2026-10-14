# ADR-051 — Tách bộ đọc chuỗi số máy khỏi bộ đọc chữ người gõ

| Mục | Nội dung |
|---|---|
| Ngày | 14.10.2026 |
| Trạng thái | Mở PR nháp về `Staging` (P0-3, TL-03). Chưa gộp |
| Thay thế / bổ sung | Bổ sung ADR-043 (form đọc số theo `parse_money`) và ADR-046 (tiền giữ đúng số đã nhập). Không đổi luật đọc chữ người gõ |

## Bối cảnh

Số tiền và số thập phân lưu trong JSON dạng **chuỗi máy**: `str(Decimal)`, dấu chấm là thập phân (`"0.125"`).
Chữ **người gõ** lại đọc bằng `core.money.parse_money` theo luật Việt: chấm là ngăn nghìn, `"1.234"` là 1234.

Ở luật Việt, chỉ có dấu chấm và sau chấm không phải 1–2 chữ số thì mọi dấu chấm bị xoá. Vì vậy mọi đường đưa chuỗi máy
trở lại `parse_money` đều nhân nghìn số tiền (TL-03, S1):

- Hoàn tác, làm lại trên lưới KN CRM gửi lại đúng chuỗi máy cũ, `"0.125"` thành 125.
- Chép một ô tiền trên lưới (ghi chuỗi máy) rồi dán lại cũng ra 125.
- Ô sửa trên lưới điền sẵn chuỗi máy; người dùng sửa `"0.125"` thành `"0.126"` thì được 126.
- **Sửa nhãn hay màu một cột Tiền** ở màn Sửa cột: form luôn gửi kèm kiểu cột, nên `_chuyen_kieu` chạy `parse_value` trên
  mọi giá trị đã lưu. Cả cột bị nhân nghìn, kể cả dòng đã xoá (phát hiện khi thiết kế đợt P0).
- Đổi kiểu Tiền sang Số nguyên: `"1234.5"` thành 12345 thay vì bị từ chối.

## Quyết định

Chủ dự án chốt 13.10.2026: **tách chuỗi máy khỏi chữ người gõ.**

1. **`core.money.parse_stored_number`** đọc chuỗi máy: dấu chấm luôn là thập phân. Hàm chỉ nhận dạng
   `-?\d+(\.\d+)?` và số mũ âm (`str(Decimal("0.0000001"))` là `"1E-7"`). Nhóm nghìn, phẩy, số mũ dương hay chữ đều là
   lỗi, không đoán. Kết quả giữ nguyên dạng (`str(kết quả)` bằng chuỗi vào), nên ô "không đổi" nhận ra là không đổi.
   Dùng lại `check_amount` (AC-9.7).
2. **Lưới KN CRM:** ô trong gói `luu-json/` có thể mang cờ `machine: true` (đúng kiểu bool, không thì 400). Có cờ thì
   ô cột số đọc bằng `record_service.stored_number`. Không có cờ là chữ người gõ, giữ luật Việt. Tab còn JS cũ không gửi
   cờ, nên vẫn chạy như trước, không sinh lỗi mới.
3. **JS lưới:**
   - Bản đang làm (`master-working-copy.js`) đánh dấu giá trị đến từ máy chủ. Hoàn tác, làm lại gửi lại giá trị cũ kèm
     cờ; máy chủ chuẩn hoá giá trị thì các bước hoàn tác cũng mang cờ.
   - Ô sửa và bản sao chép (Ctrl+C) của cột Tiền và Số thập phân hiện kiểu Việt (`"0,125"`). Dán lại ở đâu cũng đọc đúng
     theo luật người gõ, kể cả qua Excel, không phải đoán "dán từ lưới".
   - Mở ô rồi Enter mà không sửa thì không gửi gì.
4. **Đổi kiểu cột** (`table_service._chuyen_kieu`): giá trị đã lưu của kiểu số đọc bằng `parse_stored_number`. Sửa nhãn
   cột Tiền không còn viết lại số. Tiền còn số lẻ sang Số nguyên thì bị từ chối kèm số dòng. Kiểu cũ là Chữ thì vẫn là
   chữ người gõ (`"1.500"` → 1500). Điều kiện chạy `_chuyen_kieu` giữ nguyên, nên phép kiểm danh sách Chọn một không mất.

## Không làm (chờ duyệt riêng)

- **Bước 2:** siết chữ người gõ (từ chối nhóm nghìn sai như `"0.125"`, `"1.2345"` người gõ hay trong tệp CSV). Hôm nay
  chúng vẫn ra 125 và 12345, nên kiểm tay K2-5 (`docs/08-ke-hoach-kiem-thu/06`) còn ghi nhận.
- **Bước 3:** ô Số nguyên từ chối `"1,5"`. Bước này trái ADR-046 mục 8 ("Số nguyên bỏ mọi dấu như máy chủ"), nên muốn
  làm thì phải sửa chính ADR-046.
- Ô trên lưới vẫn hiện chuỗi máy `"0.125"` (`grid_service.display_value`), lệch với ô sửa đang hiện `"0,125"`. Gõ lại
  đúng số đang thấy thì đi luật người gõ. Hiển thị ô bằng `format_decimal` là việc riêng.

## Hệ quả

- Dữ liệu **đã** bị nhân nghìn trước bản vá không tự sửa được. Muốn tìm thì chạy SQL chỉ đọc, lọc giá trị tiền có từ ba
  chữ số lẻ trở lên hoặc lớn bất thường.
- Dữ liệu cũ dạng `"1.500"` nằm trong cột số (ghi trước khi có `parse_value`) nay được đọc theo luật máy (1,5). Kết quả
  là giữ nguyên hoặc bị từ chối khi đổi kiểu, không bị viết lại âm thầm.
