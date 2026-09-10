# ADR-021 — Lưới master Vận đơn mới và Thống kê KN CRM

| Mục | Nội dung |
|---|---|
| Trạng thái | Đã triển khai, kiểm chứng local; xem test-log |
| Ngày | 10.09.2026 |
| Phạm vi | `van_don_moi`; không đổi lưới bảng cũ hoặc quyền tiền/bằng chứng H7 |
| Thay thế | Bố cục nhóm/Vận hành đơn và thống kê nhúng của ADR-018/019; renderer HTML của ADR-016 chỉ riêng bảng mới |

## Quyết định

Bảng tính là một tính năng; mỗi bảng là một nguồn dữ liệu trong tính năng đó.
Vận đơn mới đóng vai trò file master để xem, tìm và chỉnh sửa. Không có công
thức Excel tự do, thanh công thức, định dạng mới, kéo điền hoặc xóa dòng trong
giao diện này. Định dạng đã lưu vẫn hiển thị. Tính toán nghiệp vụ hiện có trong
chi tiết sản phẩm được giữ nguyên, không biến thành công thức người dùng nhập.

1. Lưới JavaScript/CSS thuần riêng, giữ URL bảng. Header chữ/tên cột và số dòng;
   lưới kem, khung nhận diện hiện có, chiếm phần màn hình còn lại. Không chạy
   bộ chọn/sửa của lưới HTML cũ đồng thời. Dòng mặc định 28px; kéo mép dưới số hàng để chỉnh 28–400px, hàng cao xuống dòng; phần còn cắt đọc qua vùng nổi.
2. Một lần bấm chọn/đọc chữ bị cắt trong vùng nổi; bấm đúp/F2 sửa hoặc mở hộp
   chi tiết sản phẩm. Khung nhập văn bản kéo rộng trong viewport; không đổi
   hàng/cột. Kéo cột dùng cùng chiều rộng cho header, ô và vị trí cột cố định.
3. Chọn chữ nhật, hàng, cột; Shift và kéo gần mép tự cuộn. Mũi tên/Tab di
   chuyển xuyên khối. Ctrl+A chọn toàn kết quả lọc bằng trạng thái, không dựng
   mọi ô. Trong input Ctrl+A chỉ chọn chữ. Ctrl+C/V TSV giữ mã/số 0 đầu;
   không nhập công thức hay định dạng. Dán sai/khóa từ chối toàn lượt, không
   tự tạo dòng. Delete bỏ qua ô khóa và báo số lượng, không xóa dòng.
4. Undo/Redo tối đa 100 thao tác sửa/dán/xóa nội dung trong phiên, theo đúng
   ô trong bản đang làm. Không hoàn tác phân công/chi tiết. Enter kết thúc sửa
   ô thường; textarea Enter xuống dòng, Ctrl+Enter kết thúc sửa. Các thao tác
   này chỉ giữ nháp trong RAM. IME đang ghép chữ không kết thúc sửa/đổi ô.
5. Khối 100 dòng, LRU tối đa 10 khối; chỉ dựng hàng/cột đang nhìn và đệm nhỏ.
   Lọc/tìm/sắp xếp trên server, thêm ID làm khóa phụ. Đổi truy vấn về đầu,
   bỏ vùng chọn, hủy/bỏ phản hồi cũ; URL giữ lọc và hỗ trợ Back. Mã dòng/cột
   là định danh ghi. LocalStorage chứa thứ tự/ẩn/chiều rộng và chiều cao theo ID dòng, tách user/bảng trên máy hiện tại; không chứa nội dung khách hàng.
6. Poll 8 giây, đổi mốc thì bỏ cache và nạp vùng nhìn. Giữ bản nháp khi lỗi;
   kiểm lại quyền dòng đang sửa, đóng bản nháp khi mất quyền. Có trạng thái
   Đang lưu/Đã lưu/Có thay đổi chưa lưu/Xung đột, thử lại hoặc bỏ bản nháp.
   Đổi bộ lọc hoặc mở/đóng chức năng trên bảng giữ bản đang làm; rời bảng,
   tải lại hoặc đóng tab bỏ phần chưa lưu mà không hỏi. Không tự tải thống kê sau khi sửa ô.

## Giao tiếp và an toàn dữ liệu

- GET `bang-tinh/<code>/du-lieu/`: chỉ bảng mới; `offset`, bộ lọc/sắp xếp,
  `version` tùy chọn. Trả cột, tổng, phiên bản và tối đa 100 dòng có ID,
  giá trị gốc/hiển thị, quyền sửa. Mỗi request đọc khối riêng dùng snapshot
  REPEATABLE READ READ ONLY; nếu caller đã có transaction, kiểm mốc cuối
  vẫn từ chối dữ liệu không nhất quán. `check_id` chỉ kiểm quyền hiện hành của
  một dòng đang sửa, trả 403 nếu đã ra ngoài phạm vi.
- POST `bang-tinh/<code>/luu-json/`: UUID `operation`, `cells` gồm `id`,
  `column`, `old`, `value`. Giới hạn 2.000 ô, cả copy cũng 2.000; vượt phải
  lọc nhỏ hơn hoặc xuất Excel. Không cắt vùng chọn âm thầm.
- Khóa dòng theo ID tăng dần, kiểm lại scope/quyền/cột/kiểu và giá trị cũ
  trong một transaction. Cùng ô đã đổi trả 409; khác ô giữ cả hai thay đổi.
  Undo/Redo sửa bản đang làm; khi bấm Lưu, phần đảo cũng dùng CAS tương tự;
  một xung đột làm cả lượt lưu không áp dụng.
- Hai đường ghi ô HTML cũ (`o/<id>/<cột>/`, `luu-o/`) từ chối ghi
  Vận đơn mới bằng409 sau kiểm quyền; tab cũ phải giữ nháp và tải lại. Không
  cho phép đi vòng CAS/Undo bằng renderer cũ. Bảng khác giữ hợp đồng cũ.
- `GridMutationReceipt` có unique `(actor, operation)`, fingerprint nội dung
  và kết quả, cùng transaction ghi. Gửi lại cùng request không áp lần hai;
  cùng UUID khác nội dung trả 409. Replay kiểm scope hiện hành trước trả dòng.
  Audit chỉ metadata thao tác, không ghi nội dung khách. Biên nhận là dữ liệu
  nghiệp vụ có kiểm quyền, không dùng làm log; chưa tự thêm chính sách xóa nó.
- Migration `crm.0001_initial` chỉ tạo biên nhận. Giữ dịch vụ quyền, phân công,
  chi tiết, lọc, nhập/xuất và worker kiểm quyền file nền. ERP vẫn chỉ đọc lưới.

## Thống kê độc lập

Sidebar có Thống kê ngang cấp Bảng tính, `/thong-ke/`; nguồn đầu tiên là Vận
đơn mới trong phạm vi người xem. Đường `/van-don/thong-ke/` kiểm quyền rồi
chuyển hướng, giữ bộ lọc. Xóa fragment, sự kiện và CSS thống kê nhúng.

- Tổng đơn từ toàn tập dòng đã lọc, kể cả thiếu chi tiết. Số lượng/giá trị/
  đã thanh toán từ WaybillItem; tiền Decimal và tách loại tiền.
- Hai donut SVG đếm đơn theo từng trạng thái vận chuyển/thanh toán, giữ trả
  một phần và trạng thái trống. Tỷ trọng là **số đơn**, không phải tỷ lệ thu tiền.
- Cột thị trường đếm đơn theo Quốc gia; cột sản phẩm cộng số lượng theo mã,
  tên đi kèm mã. Vẽ 10 nhóm lớn nhất; bảng đối chiếu xem đủ nhóm, có phân trang.
- Bảng tổng hợp giữ nhóm tổng/nhân viên/sản phẩm/thị trường và phân trang.
  Không cộng số đơn giữa các nhóm sản phẩm. Thông báo số đơn thiếu chi tiết;
  không suy số lượng/tiền. Giữ Hủy/Hoàn nếu chưa lọc loại bỏ.
- Ngày lọc là Ngày của đơn. Có thời điểm cập nhật và Làm mới. Liên kết hai
  chiều với Bảng tính giữ bộ lọc. Không thêm tỷ lệ đối soát hoặc công thức chưa chốt.

## Kiểm chứng và giới hạn

Xem [AC-21](../04-tieu-chi-nghiem-thu.md), [hướng dẫn chạy](../06-ke-hoach-kiem-thu.md)
và [test-log](../test-log.md). Chỉ ghi đạt khi có kết quả; không dùng “đã merge”
thay bằng chứng. Baseline Chrome trên 2 dòng chưa tái hiện được hiện tượng vỡ
toàn bảng người dùng mô tả; đã lưu số đo/ảnh, không kết luận chắc nguyên nhân cũ.

Nghiệm thu tải: 100.000/300.000 dòng, 10/20 người; HTTP và trình duyệt riêng.
Đọc p95 ≤1s, lưu ≤0,5s, thao tác trình duyệt ≤100ms là **mục tiêu**, không phải
lời hứa đã đạt. Giữ kết quả lỗi, điều kiện Docker và cửa sổ đo cùng số liệu.


Số đo và giới hạn thực tế: [kiểm chứng 10.09.2026](../kiem-chung-master-crm.md).


## Bổ sung được duyệt — kéo chiều cao hàng, 10.09.2026

Thay quyết định chiều cao cố định tại mục 1 chỉ cho `van_don_moi`.
Tay nắm nằm trong mép dưới số hàng, hỗ trợ chuột/cảm ứng và focus bàn phím:
↑/↓ đổi 4px, Home về 28px; Escape/mất focus/pointercancel hủy lượt kéo.
Thả chuột lưu tùy chọn local; không gọi endpoint ghi, không thuộc Undo/Redo
nghiệp vụ. Kéo hàng kết thúc nhập ô vào bản đang làm, không bắt lưu database;
chỉ tạm chặn khi request lưu đang chạy.

Hình học dùng tổng cộng dồn thưa của độ lệch so với 28px, tìm hàng theo vị trí
cuộn bằng tìm kiếm nhị phân. Giữ node ô, LRU10 khối và DOM theo cửa sổ nhìn.
Chiều cao ghi nhớ khôi phục theo ID khi khối được nạp; vị trí hàng chưa biết
ước lượng 28px. Đổi query/version bỏ ánh xạ cũ, bù vị trí cuộn quanh hàng neo
khi áp chiều cao. Không tải toàn bộ ID hoặc quét tất cả dòng mỗi frame.
Giữ chiều cao đã biết trong phiên truy vấn khi khối dữ liệu rời cache.

Lỗi localStorage được báo; chiều cao vẫn dùng trong phiên. Không thêm API,
schema, migration, dependency hoặc áp dụng lưới mới cho các bảng khác.

## Quyết định thay thế — lưu thủ công và menu, 10.09.2026

Chủ dự án duyệt bỏ quy trình hỏi Lưu/Bỏ/Ở lại khi chuyển chức năng. Sửa,
dán, Delete và Undo/Redo chỉ thay bản đang làm trong RAM; Enter/Tab, đổi ô
hoặc đóng khung nhập bằng X giữ phần vừa nhập. Escape/Hủy trong khung nhập
bỏ riêng phần đang gõ. Chỉ **… → Lưu dữ liệu** hoặc **Ctrl+S** gửi các ô
đã đổi lên server, gồm cả dòng nằm ngoài bộ lọc đang xem. Tối đa 2.000 ô
khác nhau chưa lưu; vượt giới hạn từ chối toàn lượt mới và yêu cầu lưu trước.
Không lưu nháp vào localStorage. Lỗi lưu giữ nháp; mất phản hồi gửi lại đúng
UUID/nội dung cũ trước khi lưu phần sửa tiếp. Giữ kiểm quyền/CAS hiện có.

Menu … gom Lưu dữ liệu, Nhập/Xuất, Phân công theo quyền và Chia sẻ link
(vô hiệu hóa, Chưa triển khai). Popup có X ngoài phần nội dung cuộn, Escape
đóng được. Nhập file, phân công và chi tiết vẫn có nút gửi riêng; không thuộc
buffer ô. Lọc/sắp xếp, thống kê và xuất Excel dùng dữ liệu đã lưu trên server.

Các câu hỏi về nhiều người cùng sửa đã ghi vào [USER_INQUIRY](../USER_INQUIRY.md)
để bàn sau phiên; chưa bổ sung quy trình giải quyết xung đột mới.

## Quyết định thay thế tiếp theo — chín hạng mục, 10.09.2026

Chủ dự án duyệt triển khai kế hoạch chín hạng mục. Mục này thay quyết định
lưu thủ công và bỏ nháp không cảnh báo ở trên; giữ lịch sử quyết định cũ.

- Kết thúc nhập ô đưa vào hàng đợi tự lưu 500ms, chậm nhất 2s khi thao tác
  liên tục. Không kết thúc IME/ô đang nhập. Một request ghi đang chạy nhưng
  vẫn sửa tiếp được; phản hồi cũ không xóa bản nháp mới hơn. Ctrl+S gửi ngay.
- Nháp RAM, đổi lọc/popup giữ nháp. Chỉ cảnh báo rời/tải lại/đóng trang khi
  còn thay đổi chưa được xác nhận. Không gửi mỗi phím hoặc tải lại cả lưới.
- Chế độ Xem mặc định; Chỉnh sửa mở ô khi bấm/chuyển tới ô được phép sửa.
  Mũi tên trong input di chuyển con trỏ; Tab chuyển ô, Enter ô một dòng xuống
  hàng; textarea Enter xuống dòng/Ctrl+Enter kết thúc. Ô chi tiết giữ hộp riêng.
- Số hàng bắt đầu 1; chọn hàng/ô dùng xanh dương. Định dạng chỉ fs/c/bg,
  dùng schema/màu hiện có, kiểm CAS theo thuộc tính và Undo/Redo cùng dữ liệu.
- POST `luu-json/` nhận thêm `property` (value/fs/c/bg), `kind` và trả
  `conflicts` khi 409. Giữ fingerprint cũ cho payload không có kind.
  Một ô lỗi/xung đột hủy cả lượt. Retry cùng UUID/nội dung sau mất phản hồi.
- Lịch sử nghiệp vụ riêng `GridCellHistory`, gắn dòng và biên nhận, trước/sau
  đúng thuộc tính, chỉ nối thêm; không chép cả dòng vào lịch sử hoặc log.
  GET `lich-su/?record=...&column=...&before=...` dùng cursor ID, 50 mục/lượt,
  kiểm scope hiện hành. Chỉ lịch sử qua lưới mới, không suy dựng lịch sử cũ.
- Xung đột chỉ trong phiên. Người sửa chọn server hoặc gửi lại giá trị của
  mình; server kiểm CAS và quyền lần nữa. Không có ghi đè bỏ qua kiểm tra.
- POST `quyen-dong/` chỉ đọc quyền, tối đa 4.000 ID; tránh URL quá dài khi
  kiểm cache/nháp. Mất quyền gỡ nội dung khỏi lưới và các popup.
- Admin tạo đơn tại CRM phải chọn Sale đang hoạt động, không khóa. Giữ
  created_by=Admin, seller=Sale, phòng ban/team đơn theo Sale. Sale đọc được
  đơn đứng tên; không tự mở quyền sửa/hủy. ERP không đổi biểu mẫu.
- Mặc định bảng mới `created_at ASC, id ASC`; lưới/xuất cùng thứ tự. Không
  dùng số hàng làm ID, không tự kéo người đọc xuống cuối khi có đơn mới.

Giữ khối 100/cache 10, tối đa 2.000 ô/lượt và Undo/Redo 100 lượt. Không đổi
lưới cũ, H7, công thức, dependency hay chính sách xóa/lưu trữ lịch sử.
Kết quả kiểm chứng đợt này được ghi riêng tại
[kiểm chứng chín hạng mục](../kiem-chung-master-nine.md).

### Điều chỉnh truy vấn từ phép đo 300.000 dòng

- Quyền mở bảng qua đơn được tạo/giao dùng `EXISTS`, không lấy hết ID bảng
  từ hàng trăm nghìn dòng. Khi caller đã biết bảng mới, bỏ nhánh quyền bảng
  cũ khỏi SQL; dùng cùng `scope_condition`, kiểm tập kết quả bằng hồi quy.
- Thêm `record_master_cover_idx` trên `(table, created_at, id)`, include
  `deleted_at, updated_at, created_by`. Phép thử riêng trên DB test cho thấy
  giảm đọc heap khi đếm/sắp xếp và kiểm phạm vi; không đổi schema nghiệp vụ.
  Migration `forms_builder.0010` dùng tạo/xóa chỉ mục concurrently và có
  kiểm đảo ngược riêng. Không chỉnh migration đã áp dụng.
- API lịch sử chỉ lấy `kind` từ JSON biên nhận, không tải toàn bộ kết quả
  lượt dán cho từng mục lịch sử. Biên nhận trong DB vẫn giữ hợp đồng replay.
- Lọc JSON chính xác bổ sung containment để dùng GIN hiện có; vẫn giữ
  phép bằng cũ, không thay tập kết quả hoặc suy ra giá trị từ chuỗi tên.
- Nếu một dòng trong lượt chờ/lưu mất quyền, gỡ nội dung dòng đó và giữ
  nháp còn quyền; dừng hàng đợi để người dùng kiểm tra và bấm Thử lại.
  Không tự gửi phần còn lại của lượt vừa bị từ chối. Biên nhận mới được
  tạo cho lượt đã điều chỉnh; mất quyền toàn bảng tiếp tục gỡ toàn bộ.
- Không đưa số đo bản trước tối ưu vào kết luận nghiệm thu bản cuối; giữ
  artifact `after-initial` để thể hiện lần chưa đạt và nguyên nhân đã tìm.
