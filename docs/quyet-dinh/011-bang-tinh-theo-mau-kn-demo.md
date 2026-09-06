# ADR-011 — Bảng tính nhìn và thao tác theo bảng tính KN Demo

| Mục | Nội dung |
|---|---|
| Trạng thái | Đã áp dụng |
| Ngày | 04.09.2026 |
| Người quyết định | Anh/chị chủ dự án — *"đủ rồi, tạo nhánh riêng và làm cái view y hệt như ảnh"*, ngày 04.09.2026 |
| Thay thế cho | Sửa **ADR-010 mục 3** (sổ định dạng sáu màu, cỡ 10–18), **mục 7** (thanh công cụ) và **mục 8** (menu ☰); thay cách *bấm ô là sửa* của ADR-009 |
| Liên quan | ADR-001 · ADR-002 · ADR-006 · ADR-009 · ADR-010 · FR-7.9 → FR-7.12 · backlog Q51 → Q53, S8 → S10 |

---

## Bối cảnh

Sau ADR-010, anh/chị chủ dự án gửi gói **KN Demo** (`Kim_Ngan_DEMO.rar`) — một
ứng dụng thử nghiệm có màn hình bảng tính — kèm mười ảnh chụp, và chốt: *tạo
nhánh riêng, làm cái view y hệt như ảnh*. Ảnh và ghi chú nằm ở
`docs/tham-khao/kn-demo/`.

Đọc trọn mã của demo (`sheet_detail.html`, gần 2.000 dòng) thấy nó là một
**bảng tính JSON tự viết**: lưới 100×26 ô trống, công thức `=SUM()` tính ở
trình duyệt, mỗi lần đổi là lưu cả tài liệu, không phân trang, không phân
quyền dòng. KNJSC thì ngược lại: bảng động (ADR-001), mỗi ô là một bản ghi
thật có phạm vi quyền, lưu từng ô qua HTMX, phân trang 100 dòng (Q4), không
thư viện (ADR-002). "Y hệt" vì vậy phải hiểu là **y hệt cách nhìn và cách thao
tác**, không phải y hệt cách lưu.

Ràng buộc giữ nguyên: ADR-001, ADR-002, ADR-006 (không có engine công thức),
ADR-009 (hai dịch vụ 8020 / 8021), ADR-010 (lưới cho mọi bảng, định dạng lưu
cơ sở dữ liệu dưới dạng sổ đóng, thư mục).

---

## Quyết định

1. **Nhìn theo demo, đo bằng số.** Khung tối viền vàng, thanh trên 48px, thanh
   công cụ 42px đúng thứ tự demo, thanh công thức 34px có ô địa chỉ `A1` /
   `C3:F7` và chữ `fx`, cột số dòng 46px, hàng chữ cột A B C 27px có nút lọc ▼
   và mép kéo, ô 25px chữ 13px viền `#e6e0d1` nền `#fffdf8`, vùng chọn viền
   vàng `#b8952b`, chân trang 38px có tab bảng. Số đo ghi ở
   `docs/tham-khao/kn-demo/README.md`. Chưa chọn nền bao giờ thì trang này
   **mặc định tối** như demo; nền sáng dùng bảng màu `kn-light` của demo.
   Việc riêng của KNJSC (nhập tệp, thêm cột, thư mục, ẩn cột, đặt lại cột, lọc
   theo ô, bỏ lọc) dồn vào nút **⋯**; thanh lọc bên trái **ẩn mặc định**, mở
   bằng nút Bộ lọc.
2. **Hàng tên cột là hàng 1, dữ liệu từ hàng 2**, số dòng nối tiếp qua trang
   (`page_obj.start_index`). Cột trống bên phải cho đủ chữ tới Z
   (`GRID_MIN_COLUMNS`, tối thiểu `GRID_FILLER_COLUMNS`) **chỉ để nhìn giống**:
   không có `ColumnDef` sau lưng, gõ vào không có gì; cột thật do Manager
   chèn (mục 6). Dòng trống cuối lưới giữ như ADR-010; `+100 dòng` nhân bản
   phía trình duyệt tới `GRID_SPARE_ROWS_MAX`.
3. **Bấm một lần là chọn; bấm đúp, Enter, F2 hoặc gõ chữ là sửa** — như demo
   và Excel, thay cho *bấm ô là sửa* của ADR-009. Không thế thì không kéo chọn
   vùng được. Rời ô đang sửa mà đã đổi thì tự lưu. Trạng thái lưu hiện ở thanh
   trên: "Đang lưu…", "✓ Đã lưu HH:MM", "⚠ Lỗi lưu".
4. **Chọn vùng, cắt/chép/dán, kéo điền, xoá nội dung đi qua một đường dẫn lưu
   nhiều ô**, `POST /bang-tinh/<mã>/luu-o/` → `record_service.update_cells`:
   **một giao dịch, được cả hoặc không gì**; một ô sai thì 400 chỉ đúng ô
   (`CellError`), không ô nào đổi. Quyền kiểm **từng dòng** ở máy chủ
   (`can_edit_record`, `can_create_record`), ngoài phạm vi 403 có nhật ký. Ô
   tràn xuống dòng trống thành bản ghi mới; cột tính sẵn và cột trống bị bỏ
   qua; trần `GRID_PASTE_CELLS_MAX`. Clipboard là TSV nên dán từ Excel và dán
   sang Excel đều được; dán nội bộ mang theo định dạng. Một dòng nhật ký cho
   cả gói.
5. **Hoàn tác / làm lại ở phía trình duyệt**, tối đa 100 bước, tải lại trang
   là hết. Mỗi bước gọi lại đúng đường dẫn đã có (`luu-o/`, `dinh-dang/`,
   `khoi-phuc-dong/`), nên máy chủ không cần bảng lịch sử mới và nhật ký vẫn
   ghi đủ từng lần đổi.
6. **Menu chuột phải** đúng nhãn demo. *Xoá N hàng* là xoá mềm (BR-4) sau hộp
   xác nhận, `POST xoa-dong/`; hoàn tác gọi `khoi-phuc-dong/`
   (`record_service.restore_record`). Quyền xoá dòng **bằng đúng quyền sửa
   dòng** (`grant_service.can_delete_record`, tên riêng để sau này tách được
   — Q52). *Chèn N hàng trống* là thêm dòng trống ở cuối lưới, vì dòng trong
   cơ sở dữ liệu không có vị trí — thứ tự do cột sắp xếp quyết định. *Chèn /
   xoá cột* ngay trên lưới chỉ cho Admin hoặc **Manager của bộ phận sở hữu
   bảng** (`can_manage_columns`, cùng luật `can_manage_folders`):
   `table_service.insert_columns` chèn cột chữ ngắn "Cột mới k" và đánh lại
   `order`; `remove_column` giữ giá trị trong JSON; cột khoá, cột là vế của
   cột tính sẵn và cột hệ thống của bảng vận đơn thì từ chối
   (`removable_reason`).
7. **Sổ định dạng mở rộng theo thanh công cụ demo, vẫn là sổ đóng** (tinh
   thần ADR-010 mục 3 giữ nguyên): thêm nghiêng, gạch chân, gạch ngang, xuống
   dòng, viền; màu chữ và màu nền lấy từ **bảng 40 màu của demo** đặt khoá
   `m01…m40` (`record_service.PALETTE`, một chỗ duy nhất; sáu tên màu cũ vẫn
   nhận, không chuyển đổi dữ liệu); cỡ chữ 10–28; định dạng số `num / pct /
   usd / vnd / text` chỉ đổi cách **hiện** ô số bằng `Decimal` (BR-8), giá
   trị thô không đổi. 80 lớp CSS màu sinh bằng `scripts/sinh-css-mau.py`,
   không gõ tay, để bài quét lớp CSS vẫn kiểm được.
8. **Hộp lọc cột theo giá trị** như demo cho mọi kiểu cột (`filter_options`,
   trần `GRID_FILTER_OPTIONS_MAX`): tên cột và số giá trị, ô tìm, danh sách
   giá trị kèm số dòng, Chọn tất cả · Không chọn · Xóa lọc · Áp dụng; điều
   kiện toán tử cũ xếp vào mục gập "Điều kiện khác". Kết quả vẫn là tham số
   `f_<cột>__trong` trên URL, nên chip, phân trang và Tải Excel hiểu ngay
   (ADR-010 mục 5).
9. **Tự cập nhật bằng hỏi thăm, không WebSocket.** `GET moi-nhat/` trả mốc
   sửa gần nhất, số dòng, số cột trong phạm vi người xem (không có dữ liệu);
   trình duyệt hỏi mỗi `GRID_POLL_SECONDS` giây khi rảnh (không sửa, không
   kéo, tab đang hiện), khác thì nạp lại thân bảng và hiện "Có dữ liệu mới".
   Đủ cho 50 người đồng thời; S6 (thời gian thực) vẫn để sau.
10. **Công thức chưa làm.** Thanh công thức chỉ hiện và sửa giá trị ô; gõ `=`
    thì báo "chưa hỗ trợ công thức, dùng cột tính sẵn". Anh/chị đã chốt "giữ
    nguyên" ADR-006 và chờ "cách thứ ba" — khi có, nó cắm đúng vào ô này
    (S10).
11. **Hai tệp JS, không thư viện.** `bang-tinh.js` giữ phần trang (thanh bên,
    cột, thanh công thức, sửa một ô); `bang-tinh-o.js` giữ phần ô (chọn vùng,
    clipboard, kéo điền, hoàn tác, menu chuột phải, tự cập nhật). Cả hai ES5,
    không bước dựng.

### Không làm — để "y hệt" không bị hiểu là 100%

| Của demo | Ở KNJSC | Vì sao |
|---|---|---|
| Công thức `=SUM(A1:A5)` | Chỉ hiện và sửa giá trị; gõ `=` báo chưa hỗ trợ | ADR-002, ADR-006; chờ cách thứ ba — S10 |
| Tab = trang trong một tài liệu | Tab = các bảng trong phạm vi quyền | KNJSC không có "trang" |
| Chèn hàng phía trên / dưới | Chèn N hàng trống ở cuối lưới | Dòng không có vị trí trong cơ sở dữ liệu |
| Kéo đổi chiều cao dòng | Không | Dòng đổi chỗ khi sắp xếp, phân trang — S9 |
| Chuột phải lên tab: đổi tên, nhân đôi, xoá | Không; Manager làm ở Bảng dữ liệu | Thao tác cấu trúc bảng |
| Cột trống E…Z gõ là có dữ liệu | Chỉ để nhìn; Manager chèn cột thật | Cột là `ColumnDef`, Staff không tự thêm cột (N2) |
| Vẽ 15.360 ô một lúc | Phân trang 100 dòng | Q4 |
| Lưu cả tài liệu mỗi lần đổi | Lưu từng ô hoặc từng gói ô | Phạm vi quyền theo dòng, nhật ký từng lần đổi |

---

## Đã cân nhắc và bỏ

| Cách | Vì sao bỏ |
|---|---|
| Nhúng thẳng mã bảng tính của demo | Nó lưu JSON cả tài liệu, không phân quyền dòng, không phân trang — trái ADR-001, ADR-002, Q4 |
| Nhúng thư viện lưới (Handsontable, AG Grid…) | Vẫn lý do của ADR-002; những gì demo có (chọn vùng, dán, kéo điền, chuột phải) tự viết trong hai tệp JS không bước dựng là đủ |
| Hoàn tác lưu ở máy chủ | Cần bảng lịch sử và giao thức riêng; nhật ký hoạt động đã ghi từng lần đổi, hoàn tác phía trình duyệt đủ cho một phiên làm việc |
| Lưu từng ô khi dán (N yêu cầu) | Dán 3×4 ô thành 12 yêu cầu, lỗi giữa chừng để lại nửa vời; một gói một giao dịch mới đúng |
| Cho gõ màu bất kỳ khi đã có 40 màu | Vẫn lý do sổ đóng của ADR-010; 40 màu của demo là đủ, cần thêm thì thêm vào `PALETTE` |
| WebSocket cho tự cập nhật | Thêm hạ tầng (Channels, ASGI) cho 50 người; hỏi thăm mỗi 8 giây rẻ hơn nhiều và đủ dùng |
| Cho Staff chèn cột trên lưới | Cột là cấu trúc bảng, N2 đã chốt Manager mới sửa |

---

## Hệ quả

| Được | Mất |
|---|---|
| Người quen Excel dùng được ngay: kéo chọn, dán từ Excel, kéo điền, chuột phải, Ctrl+Z | Bấm một lần không còn mở sửa — phải bấm đúp, Enter hoặc gõ chữ (Q53) |
| Một gói ô lưu một giao dịch, một dòng nhật ký, lỗi chỉ đúng ô | Thêm sáu đường dẫn và hai tệp JS phải bảo trì |
| Định dạng đủ như bảng tính, vẫn kiểm được ở máy chủ và bài quét CSS | Xuất Excel vẫn chưa mang định dạng (S8) |
| Người khác sửa thì lưới tự cập nhật trong vài giây | Mỗi tab mở gửi một yêu cầu nhỏ mỗi 8 giây |
| Hoàn tác không cần bảng lịch sử | Tải lại trang là mất ngăn xếp hoàn tác |

Tiêu chí nghiệm thu: `docs/04` mục 11, AC-11.19 → AC-11.27. Xem lại khi: có
"cách thứ ba" cho công thức (S10); có người cần chiều cao dòng (S9); hỏi thăm
8 giây làm máy chủ nặng khi hơn 50 tab cùng mở (khi đó cân nhắc SSE); hoặc
cần hoàn tác qua nhiều phiên.
