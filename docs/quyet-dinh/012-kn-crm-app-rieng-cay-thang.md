# ADR-012 — KN CRM là app riêng, trang chủ là cây Bộ phận ▸ Quý ▸ Tháng ▸ bảng

| Mục | Nội dung |
|---|---|
| Trạng thái | Đã áp dụng |
| Ngày | 06.09.2026 |
| Người quyết định | Anh/chị chủ dự án, qua bốn yêu cầu và ba câu hỏi ngày 06.09.2026 |
| Thay thế cho | **ADR-010 mục 1** phần "bảng khác sửa được ở cả hai dịch vụ" — nay lưới chỉ có ở KN CRM · **ADR-010 mục 8** phần khung: nút ← theo trang |
| Liên quan | ADR-004 · ADR-009 · ADR-010 · ADR-011 · FR-7.13 · backlog Q54 → Q56, K24 |

---

## Bối cảnh

Sau ADR-011, anh/chị chủ dự án đặt lại câu hỏi gốc: vì sao có Bảng tính,
Bảng dữ liệu để làm gì, và so với Excel, Google Sheets, Lark thì sao. Câu trả
lời chốt được ba điều:

1. Bảng dữ liệu trong ERP từ đầu chỉ để **xem nhanh**; Bảng tính là **nơi làm
   việc** — thay cho dây chuyền Google Form → Google Sheet của Vận đơn vốn lag
   dần khi Sheet tới vài chục nghìn dòng (công thức nhìn cả cột chạy lại mỗi
   lần gõ, mọi người cùng mở một tài liệu).
2. Bảng tính không nằm cùng chỗ với ERP: nó là **một app riêng trong hệ sinh
   thái, tách tên miền**, mở ra ở tab mới với bộ chức năng riêng. Tên gọi:
   **KN CRM**. Không làm app cài đặt (native hay PWA) — quá đắt so với nhu cầu.
3. Vào KN CRM thấy **thư mục trước**: Bộ phận → Quý → Tháng → tệp vận đơn hay
   báo cáo marketing, như cách đặt tên file thời Sheet; quyền xem, sửa do
   Manager cấp.

Hai chỗ tôi phản biện và anh/chị chấp nhận: **không tách bảng theo tháng**
(một bảng vận đơn duy nhất — Lên đơn ghi vào đó, Lọc trùng và "mua lại lần"
đếm trên cả lịch sử; tách theo tháng là thói quen chống lag của Sheet, cơ sở
dữ liệu không cần), và **không thêm lớp quyền theo thư mục** (quyền theo bảng
đã có đủ).

So sánh ba cách đặt KN CRM so với ERP, bàn ngày 06.09.2026:

| | A · chung tiến trình | **B · tách tiến trình và tên miền, chung mã, chung cơ sở dữ liệu** | C · tách kho mã |
|---|---|---|---|
| Cách ly tải | Lưới chậm là Lên đơn chờ theo | Lưới chậm chỉ lưới chậm | Như B |
| Hiệu năng một người | Như nhau — nút thắt là cơ sở dữ liệu | Như nhau | Như nhau |
| Đăng nhập, quyền, nhật ký, giao dịch Lên đơn → vận đơn | Một bộ | Một bộ, thêm cookie phiên dùng chung | Hai bộ hoặc qua API; mất "được cả hoặc không" |
| Giá | 0 | Một ngày cấu hình khi lên máy chủ | Nhiều tuần, tăng dần |

Chọn **B**. Đó chính là dịch vụ `bangtinh` ở cổng 8021 mà ADR-009 đã dựng.

---

## Quyết định

1. **KN CRM = dịch vụ `bangtinh`** (cùng kho mã, cùng cơ sở dữ liệu, container
   riêng, cổng 8021, sau này tên miền con với cookie phiên dùng chung). KN ERP
   **không còn lưới**: `knjsc/urls.py` bỏ `crm.urls`; thanh bên của mọi bộ phận
   có một mục **KN CRM** là liên kết ngoài tới `BANGTINH_URL` (gốc dịch vụ),
   mở tab mới; Bảng dữ liệu có nút "Mở trong KN CRM" trỏ đúng bảng. Ở chính
   KN CRM, mục này là liên kết trong về trang chủ. Cùng một khung
   `base_bang_tinh.html` cho cả trang chủ lẫn lưới; nút ← theo trang: từ lưới về
   trang chủ (đúng nhánh đang mở), từ trang chủ về KN ERP.
2. **Trang chủ KN CRM (`/`) là cây Bộ phận ▸ Quý ▸ Tháng ▸ bảng**, bên trái;
   bên phải là danh sách bảng của nút đang chọn (tên, số dòng, cập nhật gần
   nhất, nhãn Xem/Sửa, nút Mở). Bấm một bảng mới mở lưới; từ lưới phải bấm ←
   mới về trang chủ. Không tự mở bảng nào; `/bang-tinh/` vẫn mở bảng mặc định
   cho ai muốn đi tắt.
3. **Cây tự sinh, không ai tạo thư mục tháng bằng tay.** Bộ phận = bộ phận
   có ít nhất một bảng trong phạm vi; Quý và Tháng sinh từ cột **Ngày**
   (`Meaning.DATE`, cột tách `val_date` có chỉ mục) của các bảng đó, đếm số
   dòng bằng một truy vấn cho cả bộ phận; quý hiện tại luôn có dù trống. Thư
   mục tay (ADR-010 mục 6) vẫn dùng ở mục **Toàn bộ bảng** của mỗi bộ phận.
4. **Tháng là góc nhìn trên một bảng, không phải bảng riêng.** Nút tháng mở
   lưới với `f_<cột Ngày>__lon_bang` và `__nho_bang` đúng ngày đầu và cuối
   tháng — cùng tham số thanh bên đang dùng (ADR-010 mục 5), nên chip, phân
   trang, Tải Excel hiểu ngay. Lưới ghi nhãn "Tháng 9/2026" khi bộ lọc đúng
   trọn một tháng. Bảng không có cột Ngày chỉ nằm ở Toàn bộ bảng.
5. **Quyền không đổi mô hình.** Cây dựng từ `TableDef.objects.in_scope`
   (bộ phận mình + bảng được cấp quyền Xem); số dòng theo phạm vi cấp bậc
   (`DataRecord.objects.in_scope`); nhãn Sửa khi `can_create_record` và bảng
   không chỉ xem. Manager cấp quyền theo bảng ở màn hình đã có của KN ERP;
   KN CRM chỉ hiển thị. `bp` ngoài phạm vi trả 404 có nhật ký, không trang rỗng.
6. **Kiểm thử theo đúng dịch vụ.** `crm/tests/conftest.py` đặt URLconf 8021
   cho toàn bộ bài của `crm`; `tests/test_khoi.py` duyệt cả hai URLconf; ma
   trận, hiệu năng và Playwright gọi lưới dưới URLconf KN CRM. Ngân sách truy
   vấn trang chủ bằng của lưới (14, K24).

### Không làm

| Việc | Vì sao |
|---|---|
| App cài đặt (native, Electron, PWA) | Anh/chị chốt quá đắt; cái cần trên điện thoại là KN ERP, đi Giai đoạn 8 |
| Tách kho mã cho KN CRM | ADR-004: tách khi có đội riêng hoặc đo được cơ sở dữ liệu phải tách |
| Bảng riêng từng tháng | Lên đơn phải chọn bảng, Lọc trùng chỉ trong tháng, báo cáo cộng nhiều bảng — mất hết lợi thế của cơ sở dữ liệu |
| Quyền theo thư mục hay theo tháng | Thêm lớp quyền mới; quyền theo bảng đủ dùng, ai không xem được bảng thì không thấy nhánh |
| Cấp quyền ngay trong KN CRM | Màn hình cấp quyền của KN ERP đã có; làm lại là hai chỗ cùng một việc |
| Danh sách bảng kiểu bảng nhiều cột như Teeze | Anh/chị chốt chỉ cần danh sách bên trái và hàng đơn giản |

---

## Đã cân nhắc và bỏ

| Cách | Vì sao bỏ |
|---|---|
| Giữ lưới ở cả ERP lẫn KN CRM (ADR-010 mục 1) | Hai lưới cùng dữ liệu, một cái kém hơn; và trái ý "Bảng dữ liệu chỉ để xem nhanh" |
| Trang chủ mở thẳng bảng dùng gần nhất | Anh/chị muốn thấy thư mục trước, như mở ổ đĩa |
| Quý và tháng lưu thành `Folder` thật | Phải tạo và dọn tay mỗi tháng; cây tự sinh từ cột Ngày không bao giờ lệch dữ liệu |
| Đếm số dòng theo tháng bằng một truy vấn mỗi bảng | Bộ phận nhiều bảng là vượt trần truy vấn; gộp `GROUP BY table_id, month` một lệnh |

---

## Hệ quả

| Được | Mất |
|---|---|
| Người dùng có "ổ đĩa" quen thuộc: bộ phận, quý, tháng, tệp — mà dữ liệu vẫn một bảng, không lag | ERP không còn lưới; ai quen mở `/bang-tinh/` ở 8020 phải sang KN CRM |
| Lưới chậm không kéo ERP chậm theo; KN CRM lên máy riêng được | Hai container, hai nhật ký, một tên miền con phải lo khi lên máy chủ |
| Cây và quyền không thêm bảng mới, không thêm luật mới | Bộ phận chưa có bảng nào thì KN CRM trả 404 kèm lời, phải tạo bảng ở ERP trước |
| Kiểm thử gọi đúng dịch vụ, hết lẫn lộn "dịch vụ chính chỉ xem" | Mọi bài của `crm/tests` phụ thuộc `conftest.py` đặt URLconf |

Tiêu chí nghiệm thu: `docs/04` mục 11, AC-11.28 → AC-11.30. Xem lại khi: đo
được cơ sở dữ liệu là nút thắt (khi đó ADR-004); có yêu cầu cấp quyền trong
KN CRM; hoặc bộ phận muốn cây theo thị trường thay vì theo thời gian (câu N9).
