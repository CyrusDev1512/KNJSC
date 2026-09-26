# ADR-033 — Nhân viên Vận đơn xem và sửa toàn bảng; nút Tôi / Toàn bộ thay Chế độ xem

| Mục | Nội dung |
|---|---|
| Trạng thái | Đã triển khai local, kiểm chứng ở `docs/kiem-chung-pham-vi-toi-toan-bo-20260917.md` |
| Ngày | 17.09.2026 |
| Người quyết định | Chủ dự án (hỏi ba câu, trả lời trong phiên Claude Code) |
| Thay thế cho | Toàn bộ ADR-026; điều "Vận đơn chỉ xem và sửa dòng được giao" của ADR-020; điều "Chế độ Xem mặc định / Chỉnh sửa" của ADR-021; câu "xem toàn bảng không mở quyền sửa" của ADR-029 |

## Bối cảnh

ADR-020 (09.09) cho nhân viên Vận đơn chỉ thấy và chỉ sửa dòng được giao ở cột
Phụ trách Vận đơn. ADR-026 (12.09) thêm trang "Chế độ xem bảng" để Admin/Manager
chọn "Chỉ dòng được phân công" hay "Toàn bộ bảng" cho cả bảng, nhưng vẫn giữ
quyền sửa theo phân công. Lưới master (ADR-021) có nút "Chế độ: Xem / Chỉnh sửa".

Chủ dự án thử trên VPS 17.09 và chốt: mặc định của công ty là **nhân viên Vận
đơn thấy cả đơn của người khác**; hai lớp "chế độ" trên gây nhầm (chế độ xem
bảng là cấu hình của Admin theo bảng, chế độ Xem/Chỉnh sửa là trạng thái của
lưới), không lớp nào là điều nhân viên cần: **tự chọn xem đơn của tôi hay toàn
bộ**.

Ba câu đã hỏi và được trả lời:

| Câu | Trả lời |
|---|---|
| Ở "Toàn bộ", nhân viên Vận đơn có sửa được dòng người khác phụ trách không? | **Có, sửa được mọi dòng.** Cột phân công chỉ còn để biết ai phụ trách |
| Nút Tôi / Toàn bộ hiện cho ai? | **Mọi người có cột phụ trách**: Vận đơn → Phụ trách Vận đơn, Sale và CSKH → Phụ trách CSKH, Marketing → Phụ trách Marketing. Admin và Kế toán không có nút |
| Nhớ lựa chọn ở đâu, mặc định gì? | **Trên trình duyệt** theo tài khoản và bảng; **mặc định Toàn bộ**. Không thêm cột |

## Các lựa chọn đã cân nhắc

| Lựa chọn | Ưu | Nhược |
|---|---|---|
| A. Giữ ADR-026, chỉ đổi mặc định sang Toàn bộ bảng | Không đổi mã | Vẫn hai lớp chế độ; nhân viên vẫn không tự chọn; quyền sửa vẫn theo phân công, trái yêu cầu |
| B. Thêm nút Tôi / Toàn bộ, giữ song song Chế độ xem bảng và Chế độ Xem/Chỉnh sửa | Ít xoá | Ba nút "chế độ" trên một lưới, mã chết cho cấu hình không ai dùng |
| **C. Bỏ hẳn Chế độ xem bảng và Chế độ Xem/Chỉnh sửa; nút Tôi / Toàn bộ là bộ lọc của người dùng; Vận đơn sửa mọi dòng** | Một khái niệm, một nút; xoá được service, trang, trường, test, script cũ | Đổi quyền sửa; phải sửa lại các bài kiểm ghim ADR-020/026 |

## Quyết định

Chọn **C**.

1. **Phạm vi và quyền của nhân viên Vận đơn** trên bảng có profile Vận đơn
   (`workflow = "waybill"`): thấy mọi dòng và sửa mọi dòng, như Leader/Manager
   Vận đơn. Hai chỗ duy nhất từng chặn là `assignment_service.scope_condition`
   (đọc) và `grant_service.can_edit_visible_record` (sửa); cả hai bỏ điều kiện
   "phải là người được giao". `waybill_service.assert_editable` vẫn chặn gõ vào
   ba cột `phu_trach_*`: phân công chỉ sửa qua hộp Phân công, và chỉ Leader/
   Manager Vận đơn hoặc Admin được phân công (ADR-020 giữ nguyên điều này).
2. **Sale, CSKH, Marketing, Kế toán không đổi**: Sale thấy dòng mình tạo hoặc
   được giao CSKH và sửa dòng mình tạo; CSKH chỉ xem dòng được giao; Marketing
   theo grant; Kế toán xem toàn bảng, không sửa ô.
3. **Nút Tôi / Toàn bộ** trên thanh công cụ lưới (`#mg-pham-vi`), chỉ ở bảng
   Vận đơn và chỉ khi `assignment_service.field_for(user)` có giá trị
   (`delivery`, `care`, `marketing`). Tôi = thêm `cua_toi=1` vào URL; máy chủ
   lọc `assignment__<trường>_id = user.pk` trong `grid_service.build_grid`.
   Tham số đi theo mọi thứ lấy từ `build_grid`: khối JSON, digest phiên bản,
   chip lọc, Thống kê, Tải Excel trực tiếp và nền. Admin, Kế toán, bảng thường
   bỏ qua tham số (không lỗi, không lọc).
4. **Nhớ lựa chọn** trong `localStorage` cùng khoá `kn-master:<user>:<bảng>`
   đã có (`preferences.scope`). URL có `cua_toi` thì URL thắng; không có thì
   dùng bản nhớ; chưa nhớ gì thì Toàn bộ.
5. **Lưới luôn ở chế độ chỉnh sửa**: bấm ô sửa được là gõ ngay, mũi tên mở ô,
   Enter xuống hàng, Shift+mũi tên chọn vùng. Ô không sửa được (CSKH, Kế toán,
   Sale trên dòng người khác, cột chỉ đọc) bấm vào mở vùng đọc `#mg-reader`,
   không báo lỗi. Nút "Chế độ: Xem" và biến `editMode` bỏ.
6. **Xoá** trang `che-do-xem/`, `crm/delivery_view_views.py`,
   `orders/services/delivery_view_service.py`, template
   `delivery_view_mode.html`, khối "Chế độ xem bảng" ở Cột & cấp quyền và hộp
   Phân công, trường `TableDef.delivery_view_all` (migration 0013, đảo được),
   hai bài kiểm và script `kiem-thu-delivery-view.cjs`.
   **Giữ** `TableDef.delivery_view_version`: `destination_service` vẫn dùng nó
   để ép tab đang mở tải lại khi đổi bảng nhận đơn (ADR-029); JS chỉ đổi lời
   báo thành "Cấu hình bảng đã thay đổi. Đang tải lại trang."

## Bổ sung 18.09.2026 — thao tác ô như Excel

Chủ dự án gửi video: sau 17.09 bấm ô là mở ô nhập ngay, nên **Ctrl+A** rơi vào ô
nhập (chọn chữ) chứ không chọn cả bảng. Chốt (hỏi, trả lời "Như Excel"): **bấm
chỉ chọn ô; gõ phím chữ hay số là vào nhập ngay với ký tự vừa gõ; Enter, F2, bấm
đúp mở ô nhập giữ giá trị cũ; Enter và Tab trong ô nhập chỉ chuyển ô, không tự mở
ô kế; mũi tên chỉ di chuyển.** Ctrl+A, Delete, Ctrl+C/V luôn tác động lên lưới.
Ô chỉ đọc, phân công, chi tiết: gõ phím thì ô phồng to tại chỗ. Điều 5 ở trên đọc theo
nghĩa này. Chân lưới ghi "Chọn ô rồi gõ để sửa · Enter/F2 mở ô · Ctrl+A chọn hết".

## Lý do

- Yêu cầu nghiệp vụ là của người làm việc, không phải của Admin: nhân viên
  cần tự thu hẹp về việc của mình rồi mở rộng lại, nhiều lần trong ngày.
  Một bộ lọc theo người dùng đúng hơn một cấu hình theo bảng.
- Mỗi lớp "chế độ" là một trạng thái phải nhớ, phải kiểm, phải giải thích.
  Bỏ hai lớp cũ thì lưới còn đúng một câu hỏi: đang xem của tôi hay của tất cả.
- Quyền sửa mọi dòng là quyết định của chủ dự án về cách bộ phận Vận đơn làm
  việc (đơn đổi tay trong ngày, người này trực cho người kia). Lịch sử ô
  (`GridCellHistory`) và nhật ký vẫn ghi ai sửa gì, nên trách nhiệm không mất.
- Đặt lọc trong `build_grid` thay vì ở JS để Thống kê, Excel và worker nền
  cùng một kết quả, không có đường nào lộ dòng ngoài phạm vi hay quên lọc.

## Hệ quả

**Được gì:** một nút, một khái niệm; bớt 1 trang, 1 service, 1 trường, 2 bài
kiểm, 1 script; lưới không còn trạng thái "Xem" khiến bấm ô không gõ được.

**Mất gì:** không còn cách ép một nhân viên Vận đơn chỉ thấy dòng của mình.
Muốn giới hạn thật thì phải là quyết định mới (ví dụ theo bảng hoặc theo team).

**Chỗ cần cẩn thận về sau:**

- Cờ `CRM_OPT_SYNC` đang tắt nên dòng vừa bị bỏ phân công không tự biến khỏi
  lưới "Tôi" đang mở; nó biến mất khi tải lại hoặc khi lọc lại. Đây là hành vi
  chung của lưới, không riêng nút này.
- Bài kiểm nào cần "mất phân công thì mất quyền" phải dùng CSKH (chỉ xem theo
  phân công) hoặc Sale có Grant EDIT và được giao CSKH, không dùng Vận đơn nữa.
- `docs/kiem-chung-che-do-xem-van-don-20260912.md` giữ làm lịch sử của ADR-026.

## Điều kiện xem lại

Khi công ty cần giới hạn thật quyền xem hoặc sửa của một nhóm nhân viên Vận đơn
(nhiều chi nhánh, nhân viên thử việc), hoặc khi bộ lọc "Tôi" cần theo team thay
vì theo người.

## Bổ sung 26.09.2026 — hộp đọc thành ô phồng to tại chỗ

Chủ dự án so với Google Sheets (26.09) và chốt: bỏ hộp đọc dạng panel nổi có tiêu đề
và nút × đặt dưới ô; thay bằng **ô phồng to tại chỗ** — bấm ô đang bị cắt chữ thì chính
ô đó nở ra đè lên các ô lân cận hiện đủ nội dung, bấm chỗ khác thì thu về. Vẫn là
`#mg-reader`, chỉ đổi cách trình bày (định vị theo khuôn `positionEditor`: fixed đúng
rect ô, chia scale, `clipPath` không đè tiêu đề và cột ghim; quá chỗ thì cuộn bên trong).

Bốn công dụng của hộp đọc **giữ nguyên**: mọi ô bị cắt ở mọi cột; gõ phím trên ô chỉ
đọc/phân công/chi tiết (mục bổ sung 18.09 ở trên); cột chứng từ chép nguyên nút con;
nơi duy nhất bôi đen chép chữ được. Bấm đúp lên ô phồng vẫn mở ô nhập (nó che ô thật
nên tự chuyển tiếp). Không đụng tự giãn chiều cao dòng và trần 2.000 px (AC-11.44).
