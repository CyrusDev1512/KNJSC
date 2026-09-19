# ADR-039 — Ẩn cột với cả công ty

| Mục | Nội dung |
|---|---|
| Trạng thái | Đã triển khai local, kiểm chứng ở `docs/kiem-chung-an-cot-20260919.md`; VPS chờ phát hành |
| Ngày | 19.09.2026 |
| Người quyết định | Chủ dự án (hai câu hỏi trả lời trong phiên Claude Code) |
| Liên quan | ADR-011 (hộp "Cột" của lưới), ADR-014 (Bảng dữ liệu chỉ xem), ADR-036 (một bảng vận đơn) |

## Bối cảnh

Mỗi sản phẩm đang bán có một cột số lượng `sl_<mã>` trên bảng vận đơn (AC-11.8, quyết
định Q39) — di sản từ tệp Excel thật, nơi mỗi sản phẩm là một cột. Thêm sản phẩm qua nút
"Tạo sản phẩm" ở Lên đơn hay "Thêm mới…" trong ô chọn Sản phẩm thì `product_service`
gọi luôn `dispatch_service.sync_product_columns`, nên cột hiện ra ngay.

Số cột chỉ tăng, không bao giờ giảm: sản phẩm ngừng bán vẫn giữ cột để xem đơn cũ. Bảng
Vận đơn mới đang 45 cột, trong đó 10 cột sản phẩm. Chủ dự án muốn tắt nhóm cột này, vì
chi tiết sản phẩm của mỗi dòng đã nằm trong hộp Chi tiết (`WaybillItem`, ADR-018) — cột
`sl_*` chỉ làm lưới rộng thêm.

Lưới đã có nút "Cột" (ADR-011) nhưng nó chỉ nhớ trong `localStorage` của từng trình
duyệt: mỗi người phải tự ẩn, máy khác lại hiện, người mới vào vẫn thấy. Không dùng để
tắt cho cả công ty được.

Hai câu đã hỏi và trả lời:

| Câu | Trả lời |
|---|---|
| Ai được bật tắt, bằng cờ cấu hình máy chủ hay nút trên giao diện? | **Hộp "Cột" ẩn được mọi cột cho cả công ty**, quản lý bảng tự bấm — không riêng cột sản phẩm |
| Tắt ở những màn hình nào? | **Cả ba**: lưới KN CRM, tệp Excel xuất ra, Bảng dữ liệu bên KN ERP |

Cách chọn không phải cờ trong `.env` như `PAYMENT_DOCUMENTS_ENABLED`: cờ đó chỉ người
vào được VPS mới đổi và phải khởi động lại, trong khi chủ dự án muốn tự bấm.

## Quyết định

1. **`ColumnDef.is_hidden`** (migration `forms_builder/0015`, đảo được): cột vẫn còn
   định nghĩa và giá trị, chỉ không hiện. Khác hẳn bỏ cột — không phạm BR-4, hiện lại
   là thấy đủ dữ liệu cũ, kể cả cột đã ẩn nhiều tháng.
2. **Một chỗ lọc duy nhất**: `table_service.visible_columns`. Ba màn hình gọi nó —
   `grid_service.display_columns` (lưới CRM, và tệp Excel vì xuất đi qua lưới),
   `export_service.build_queryset` (các đường xuất khác), `forms_builder.views.bang_xem`
   (Bảng dữ liệu ERP). Màn hình "Cấu trúc cột" bên ERP **vẫn liệt kê đủ**, vì đó là chỗ
   quản lý bảng.
3. **Ai bật tắt**: quản lý bộ phận sở hữu bảng hoặc Admin, đúng quyền đang dùng cho thêm
   và bỏ cột (`grant_service.can_manage_columns`). Đường dẫn `POST /bang-tinh/<mã>/an-cot/`,
   có ghi nhật ký hoạt động.
4. **Giao diện**: trong hộp "Cột" sẵn có. Ô tích bên trái vẫn là "ẩn cho riêng máy mình"
   như cũ; quản lý bảng có thêm nút "Ẩn cho cả công ty" ở từng dòng, một nút gộp "Ẩn cột
   số lượng theo sản phẩm" khi bảng có nhóm đó, và mục "Đang ẩn với cả công ty" để bật
   lại. Người không phải quản lý bảng không thấy mục này và không biết bảng có cột ẩn.
5. **Chặn ba trường hợp**: cột khoá (mất cách nhận dòng), cột bắt buộc nhập (không thêm
   dòng mới được), và lần ẩn làm bảng không còn cột nào hiện.
6. **Sản phẩm mới khi nhóm đang ẩn**: cột sinh ra ở trạng thái ẩn luôn. Thêm hàng không
   làm cả nhóm hiện trở lại — đây là điều chủ dự án hỏi đúng chỗ ("thêm sản phẩm test thì
   thấy một cột test").
7. **Lên đơn vẫn ghi số lượng vào cột đang ẩn.** Tốn không đáng kể và giữ dữ liệu liền
   mạch: bật lại là có đủ, không thủng một đoạn thời gian. Nhập tệp Excel cũ cũng vậy —
   cột ẩn vẫn nhận dữ liệu từ tệp, không mất gì.
8. **Không đụng profile**: ẩn không gọi `assert_column_change`, nên bảng vận đơn ẩn được
   cột thừa mà cấu trúc chuẩn của `waybill_service` vẫn nguyên.

## Vì sao không làm cách khác

| Cách | Vì sao không |
|---|---|
| Xoá hẳn cột `sl_*` | Mất số lượng theo sản phẩm của các dòng cũ, gồm 221 dòng nhập từ tệp thật. Phạm BR-4, không hoàn tác được |
| Cờ trong `.env` | Chủ dự án không tự bật tắt được; phải nhờ người vào VPS và khởi động lại hệ thống |
| Ô tích riêng cho nhóm cột sản phẩm | Giải đúng một việc; lần sau muốn ẩn cột khác lại phải làm tiếp |
| Ngừng sinh cột khi thêm sản phẩm | Không giải quyết 10 cột đang có, và bật lại thì thiếu cột của sản phẩm thêm trong lúc tắt |

## Hệ quả

- Cột `sl_*` vẫn được `sync_product_columns` sinh ra và Lên đơn vẫn điền; tắt hay không
  là việc hiển thị. Số cột trong cơ sở dữ liệu vẫn tăng theo danh mục sản phẩm.
- Bộ lọc theo cột đang ẩn không còn tác dụng trên lưới, vì lưới đọc bộ lọc từ danh sách
  cột đang hiện.
- Cột ẩn không ra tệp Excel, nên người nhận tệp thấy ít cột hơn trước. Cần báo trước cho
  ai đang dùng tệp xuất để đối chiếu.
