# ADR-010 — Bảng tính cho mọi bảng, có định dạng ô, cột khoá và thư mục

| Mục | Nội dung |
|---|---|
| Trạng thái | Đã áp dụng |
| Ngày | 04.09.2026 |
| Người quyết định | Anh/chị chủ dự án, qua bốn câu hỏi ngày 04.09.2026 |
| Thay thế cho | **ADR-009 mục 1** (lưới chỉ của Vận đơn) · **ADR-002 phần "Mất gì"** (chấp nhận không có định dạng màu) |
| Liên quan | ADR-001 · ADR-007 · ADR-009 · FR-7.1 → FR-7.8 · backlog Q46 → Q50 |

---

## Bối cảnh

ADR-009 dựng Bảng tính làm lưới làm việc của riêng bộ phận Vận đơn trên bảng
`van_don`. Ngày 04.09.2026 anh/chị chủ dự án gửi ảnh một công cụ vận hành đang
dùng (Lumi OMS) và yêu cầu:

> *Ở chức năng bảng tính cần thêm thanh menu với các chức năng y hệt một CRM
> chuyên biệt: nhập xuất Excel, tạo folder, filter như thanh công cụ bên trái.
> View phải giống Excel, có thừa ô trống để nhập, các ô luôn có viền. Tô màu,
> in đậm, font, size, căn lề. Các trường phải ấn được để sửa; bấm vào ô của
> khoá độc nhất thì lọc được.*

Bốn câu hỏi được chốt cùng ngày:

| Câu hỏi | Chốt |
|---|---|
| Xây trên nền nào | Trên mã `main` (Giai đoạn 7C), không làm lại |
| Định dạng ô lưu ở đâu | **Cơ sở dữ liệu**, mọi người cùng thấy |
| "Tạo folder" nghĩa là gì | **Thư mục chứa bảng** |
| Lưới áp cho bảng nào | **Mọi bảng dữ liệu**, `/bang-tinh/` mặc định mở bảng vận đơn |

Hai điều này đảo hai quyết định cũ, nên phải ghi thành mục mới thay vì sửa
mục cũ (quy tắc 1 của thư mục này).

---

## Quyết định

1. **Lưới cho mọi bảng trong phạm vi quyền.** `/bang-tinh/<mã bảng>/` mở
   bất kỳ bảng nào `TableDef.objects.in_scope(user)` trả về; ngoài phạm vi
   → 404 như màn hình Bảng dữ liệu (không còn chặn theo bộ phận Vận đơn).
   `/bang-tinh/` mở bảng vận đơn nếu người này thấy nó, không thì bảng đầu
   tiên trong phạm vi. Phần riêng của vận đơn theo tệp thật — cột Lọc trùng,
   thứ tự cột, tô màu dòng, lọc sản phẩm theo cột `sl_<mã>` — bật theo
   `grid_service.is_waybill(table)`. **Luật hai dịch vụ của ADR-009 giữ
   nguyên:** bảng vận đơn chỉ xem ở 8020, sửa ở 8021 (`GRID_ONLY_TABLES`);
   bảng khác sửa được ở cả hai.
2. **Lưới nhìn như Excel.** Mọi ô có viền dọc lẫn ngang; cuối lưới luôn thừa
   `GRID_SPARE_ROWS` dòng trống — gõ vào rồi rời đi là thành bản ghi thật qua
   `record_service.create_record`, thuộc bộ phận sở hữu bảng. Quyền thêm dòng
   (`grant_service.can_create_record`): cùng bộ phận sở hữu, hoặc cấp quyền
   Sửa, hoặc Admin; bảng chỉ xem ở dịch vụ này thì không.
3. **Định dạng ô lưu trong cơ sở dữ liệu.** `DataRecord.style` là JSON
   `{"<mã cột>": {"b": 1, "bg": "vang", "fs": 12, "al": "c"}}`. Khoá và giá trị
   nằm trong **sổ đóng** `record_service.STYLE_SCHEMA` (đậm; sáu màu nền;
   cỡ 10–18; căn trái/giữa/phải) — không nhận CSS tự do, giao diện dịch từng
   giá trị sang một lớp CSS cố định. Quyền định dạng bằng quyền sửa ô, kiểm
   từng dòng ở máy chủ; mỗi lần đổi ghi nhật ký. Không phải "font" tự do:
   phông chữ theo hệ thống, chỉ đổi cỡ.
4. **Cột khoá.** `ColumnDef.is_key`, mỗi bảng tối đa một cột (ràng buộc cơ sở
   dữ liệu), kiểu chữ ngắn hoặc số nguyên, không phải cột tính sẵn. Manager
   đặt trong Sửa cột; bảng vận đơn lấy Mã đơn. Ô cột khoá có nút ⌕ — một liên
   kết GET thêm `f_<cột>=<giá trị>` vào bộ lọc đang bật.
5. **Thanh lọc bên trái không có tham số mới.** Chọn nhanh (hôm nay, hôm qua,
   7 ngày, tháng này, tháng trước) và từ ngày / đến ngày viết vào
   `f_<cột Ngày>__lon_bang` và `__nho_bang`; sản phẩm viết vào
   `f_<cột Sản phẩm>__trong` (bảng vận đơn: `sp=<mã cột số lượng>`, "có một
   trong"). Nhờ vậy bộ đọc chung, chip "đang lọc" và nút Xuất Excel hiểu ngay
   — xuất vẫn "đúng thứ đang hiện" (ADR-002). `export_service` có sổ cách dựng
   queryset để Bảng tính đăng ký cách của mình mà `forms_builder` không phải
   biết tới `crm`.
6. **Thư mục chứa bảng, phẳng.** `forms_builder.Folder` thuộc một bộ phận,
   xoá mềm; `TableDef.folder` rỗng được. Model đặt ở `forms_builder` chứ không
   ở `crm` vì `TableDef` không được trỏ sang app sẽ tách ra (ADR-004). Manager
   của bộ phận (hoặc Admin) tạo, đổi tên, xoá, xếp bảng; thư mục chỉ sắp xếp
   thanh bên, **không** ảnh hưởng phạm vi quyền. Không lồng thư mục — chưa có
   nhu cầu, ghi ở backlog mục 3.
7. **Thanh công cụ** đủ mục: nhập, xuất Excel, thêm dòng, thêm cột, thư mục
   mới, định dạng, lọc theo ô, bỏ lọc, ẩn/hiện cột. Ẩn cột và thu gọn thanh bên
   nhớ trên trình duyệt (như ADR-009 mục 8), không lên máy chủ.

---

## Đã cân nhắc và bỏ

| Cách | Vì sao bỏ |
|---|---|
| Nhúng thư viện lưới kiểu bảng tính | Vẫn đúng lý do của ADR-002: nặng, lưu blob, không phân quyền dòng; lưới HTML + HTMX hiện có đã làm được mọi thứ yêu cầu |
| Định dạng lưu theo cột, không theo ô | Người dùng muốn tô từng ô như Excel; theo cột không đủ |
| Định dạng chỉ lưu trên trình duyệt | Đổi máy là mất, người khác không thấy — người dùng chốt phải cùng thấy |
| Cho gõ màu bất kỳ (`#rrggbb`), cỡ chữ bất kỳ | Mở đường cho CSS lạ vào trang và bài quét lớp CSS không kiểm được; sổ đóng đủ dùng, mở rộng thì thêm vào sổ |
| Thư mục lồng nhau | Chưa ai cần; thêm sau chỉ là thêm FK `parent` |
| Bỏ hẳn dịch vụ 8021 khi lưới đã chung | Lý do tách tải và subdomain của ADR-009 vẫn còn nguyên |

---

## Hệ quả

| Được | Mất |
|---|---|
| Marketing, Sale làm việc trên lưới kiểu Excel với bảng của mình, không chỉ Vận đơn | Màn hình Bảng dữ liệu và Bảng tính trùng chức năng xem; Bảng dữ liệu còn để sửa cột, nhập tệp, cấp quyền |
| Tô màu, in đậm từng ô, mọi người cùng thấy — cái mà ADR-002 từng chấp nhận mất | Thêm cột JSON trên bản ghi; xuất Excel chưa mang theo định dạng (ghi backlog) |
| Bấm ⌕ ở mã đơn là ra đúng đơn; chọn nhanh khoảng ngày, sản phẩm như công cụ đang quen | Thêm ba tệp chuyển đổi cấu trúc (0006, 0007) và một model mới phải bảo trì |
| Thanh bên có cây thư mục để bảng không nằm thành danh sách dài | Thư mục do Manager sắp, Staff không tự xếp được |

Tiêu chí nghiệm thu: `docs/04` mục 11, AC-11.12 → AC-11.18. Xem lại khi: có
bộ phận cần thư mục lồng nhau; có yêu cầu màu ngoài sáu màu; hoặc lưới chung
làm dịch vụ chính chậm hơn 2 giây trên 50.000 dòng (khi đó tách hẳn theo
ADR-004).
