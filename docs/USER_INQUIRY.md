# Câu hỏi cần xác nhận với người sử dụng

## CRM-Optimization — chủ dự án đã chốt 11.09.2026

1. **Đích triển khai/đối tượng:** KN CRM, lưới mới chỉ `van_don_moi`; VPS chưa
   có. Đáp: làm checkout/nhánh `CRM-Optimization`, đo local trước, chuẩn bị
   cấu hình 12 CPU/24 GB/300 Mbps; không suy năng lực VPS từ máy hiện tại.
2. **Độ trễ Thống kê:** chấp nhận cache tối đa 15 giây, có thời điểm tính và
   Làm mới bỏ cache. Quyền vẫn kiểm hiện hành; không đổi công thức nghiệp vụ.
3. **Lưu giữ:** journal kỹ thuật giữ 10.000 revision/bảng, tối đa 2.000 ID/sự
   kiện rồi đồng bộ lại. Không xóa lịch sử ô hoặc biên nhận nghiệp vụ.
4. **Nghiệm thu:** trước/sau cùng fixture 100k/300k × 10/20, bản cuối chạy bền
   300k/20/30 phút. Không chấp nhận ngưỡng lỗi mạng “dưới 5%”. Chưa commit/push.
5. **Lịch sử có phình không?** Có, tăng theo số ô/thuộc tính được sửa, không
   theo riêng số khách. Lịch sử ở `crm_gridcellhistory`, biên nhận ở
   `crm_gridmutationreceipt`; nháp ở RAM trình duyệt. Lượt test 20 lần dán
   2.000 ô: JSON receipt giảm 4.052.670 → 361.808 byte; vẫn đủ 40.000 history.
   [Số đo/index/WAL và giả định một năm](kiem-chung-crm-optimization-20260911.md#sql-biên-nhận-và-dung-lượng).
   Chưa thay chính sách lưu giữ hoặc tự xóa lịch sử.

[ADR-024](quyet-dinh/024-crm-optimization.md) và
[tiến độ kiểm](kiem-chung-crm-optimization-20260911.md). Đây là quyết định đã
duyệt, không phải câu hỏi mới cần người dùng trả lời.

Nơi tập hợp câu hỏi để chủ dự án mang đi hỏi đúng người. Chia theo vấn đề,
ghi rõ đối tượng trả lời; đánh số câu hỏi trong từng nhóm.

Chuyển các câu H1–H7 từ mục 5 của [backlog](backlog.md) sang đây ngày
09.09.2026. Giữ mã H để truy vết. Các vấn đề N/V và quyết định lịch sử vẫn
được quản lý trong backlog; đây chưa phải danh sách toàn bộ việc còn nợ.

Khi có trả lời, ghi ngay dưới câu hỏi: **Trả lời / Người xác nhận / Ngày**.
Không tự điền đáp án. Đã xác nhận nghiệp vụ không đồng nghĩa đã triển khai.

## Vấn đề 1 — Nhập tiền đã thu, bằng chứng và xác nhận của kế toán

**Đối tượng:** Vận đơn, Kế toán và người có thẩm quyền chốt quy trình.
**Trạng thái:** Chờ chủ dự án hỏi người có thẩm quyền.

1. **H7 — Ai được nhập và sửa số tiền đã thu, bằng chứng thanh toán trong
   bảng Vận đơn mới?** Vận đơn nhập rồi kế toán xác nhận, hay chỉ kế toán
   được nhập/sửa?

   **Trả lời:** Chưa có.

**Bối cảnh đã chốt, không hỏi lại:** Leader Vận đơn phân công người xử lý;
nhân viên Vận đơn/CSKH chỉ xem khách hoặc đơn được giao cho mình. Kế toán
làm việc trên cùng bảng Vận đơn mới, ban đầu cần xem toàn bộ đơn chưa thu
tiền; đối chiếu tình trạng giao hàng, thanh toán và bằng chứng khi đã trả.
Không suy ra rằng kế toán không được xem lại đơn đã trả, hoặc mặc định ai
có quyền ghi tiền/bằng chứng khi H7 chưa được trả lời.

## Vấn đề 2 — Thao tác bảng tính quen dùng

**Đối tượng:** Nhân viên Vận đơn, Marketing trực tiếp dùng Excel/Sheets.
**Trạng thái:** Câu hỏi khảo sát đã có, chưa ghi nhận câu trả lời chi tiết.

1. **H1 — Trong tệp Excel hiện tại, anh/chị có gõ công thức không? Gõ những gì?**

   **Trả lời:** Chưa có mô tả thao tác thực tế. Chủ dự án đã xác nhận CRM
   hiện chưa cần công thức; khảo sát này không tự mở lại phạm vi làm công thức.

2. **H2 — Anh/chị có hay kéo góc ô để điền cả cột không?**

   **Trả lời:** Chưa có.

3. **H3 — Anh/chị có dán dữ liệu từ tệp Excel khác vào không?**

   **Trả lời:** Chưa có.

## Vấn đề 3 — Nhập liệu và tìm kiếm trong công việc hằng ngày

**Đối tượng:** Nhân viên Sale, Marketing và Vận đơn.
**Trạng thái:** Chờ khảo sát người sử dụng.

1. **H4 — Mỗi ngày mất bao lâu cho việc nhập liệu và tổng hợp thủ công?**

   **Trả lời:** Chưa có.

2. **H5 — Lần gần nhất cần tìm một thông tin mà tìm không ra là khi nào?**

   **Trả lời:** Chưa có.

## Vấn đề 4 — Cơ cấu team thực tế

**Đối tượng:** Quản lý các bộ phận.
**Trạng thái:** Chờ thông tin cơ cấu thực tế.

1. **H6 — Một bộ phận hiện có mấy team, ai phân team?**

   **Trả lời:** Chưa có thông tin thực tế đầy đủ. Câu hỏi này không hỏi lại
   việc ai phân công xử lý đơn: chủ dự án đã chốt là Leader Vận đơn.


## Vấn đề 5 — Báo cáo muộn trong Đánh giá nhân sự

**Đã chốt:** báo cáo muộn ảnh hưởng trực tiếp tới Đánh giá nhân sự (tên cũ:
Văn hoá). Không hỏi lại việc có áp dụng hay không.

1. **H8 — Hạn nộp cho từng loại báo cáo là khi nào; ngày nghỉ, nộp lại và
   trường hợp được miễn được xử lý thế nào?**
2. **H9 — Mỗi lần muộn ảnh hưởng bao nhiêu điểm, tính theo kỳ nào và có tác
   động tới sao/xếp hạng hiện có không? Ai được xác nhận hoặc điều chỉnh?**

**Đối tượng:** Chủ dự án, Nhân sự và người có thẩm quyền chốt đánh giá.
**Trả lời:** Chưa có. Chưa triển khai tự trừ điểm.

## Vấn đề 6 — Phân công, lọc và xuất Vận đơn mới

**Đối tượng:** Leader Vận đơn, Sale/CSKH, Marketing; chủ dự án xác nhận.

1. **Ai phân công, chọn ai và dòng chưa giao hiển thị cho ai?**

   **Trả lời / Chủ dự án / 09.09.2026:** Leader/Manager Vận đơn và Admin
   xem/phân công toàn bảng. Nhân viên Vận đơn chỉ xem đơn được giao; Sale
   thấy đơn mình tạo hoặc được giao CSKH; CSKH chỉ thấy đơn được giao.
   Người Vận đơn chọn tài khoản Vận đơn; CSKH chọn Sale hoặc CSKH; Marketing
   chọn tài khoản Marketing. Chỉ nhận tài khoản hoạt động, không bị khoá.
   Giao CSKH không tự cấp quyền sửa; tên Marketing không mở quyền xem.

2. **Mã nhân viên và file xuất dùng định danh nào?**

   **Trả lời / Chủ dự án / 09.09.2026:** Username là mã nhân viên; phân công
   liên kết tài khoản bằng ID. Excel giữ cấu trúc hiện tại, thêm mã Sale
   tạo đơn và ba người phụ trách. Không suy mã từ họ tên hoặc dòng nhập cũ.

3. **Lọc ngày, trạng thái và sản phẩm theo nguồn nào?**

   **Trả lời / Chủ dự án / 09.09.2026:** Ngày của đơn; giữ các trạng thái
   hiện có (kể cả trả một phần); mã sản phẩm từ chi tiết, Quốc gia là thị
   trường, Marketing từ người được Leader gán. Xuất toàn bộ kết quả lọc
   trong quyền. Không tạo mẫu kho riêng.

Đã triển khai theo [ADR-020](quyet-dinh/020-phan-cong-loc-xuat-van-don-moi.md).
H7 ở vấn đề 1 vẫn chờ trả lời; phần này không thay quyền ghi tiền/bằng chứng.

## Quyết định bổ sung — file master và Thống kê (10.09.2026)

**Đối tượng xác nhận:** Chủ dự án. Đây là quyết định phạm vi đã duyệt triển
khai, không thay câu trả lời khảo sát chi tiết H2/H3 của nhân viên.

1. **Bảng tính cần làm gì?** Xem/tìm/chỉnh sửa như thao tác Excel cơ bản;
   thường cuộn kiểm tình trạng giao và bấm ô đọc hết chữ. Không công thức
   tự do. Làm Vận đơn mới trước; các bảng khác giữ nguyên.
2. **Tải và chọn thế nào?** Cuộn liên tục theo khối; Ctrl+A toàn kết quả
   lọc. Sửa/copy/dán/Delete nội dung/Undo/Redo, tối đa 2.000 ô/lượt; chưa có
   kéo điền, định dạng mới hoặc xóa dòng. Không lưu nháp/khách vào localStorage.
3. **Thống kê đặt đâu?** Tính năng riêng cùng cấp Bảng tính, có donut/cột
   và bảng đối chiếu; chuyển bộ lọc hai chiều. Giữ trạng thái và tiền tệ
   hiện có, không bổ sung công thức đối soát hoặc quyền tiền/bằng chứng H7.

**Trả lời / Chủ dự án / 10.09.2026:** Kế hoạch triển khai ADR-021 đã được duyệt.

## Vấn đề cần bàn sau phiên — Nhiều người sửa cùng dữ liệu KN CRM

**Đối tượng:** Chủ dự án, Leader Vận đơn và người sử dụng bảng tính.

1. Khi hai người sửa cùng một ô rồi bấm Lưu, người dùng cần xem và xử lý
   hai giá trị như thế nào? Ai được quyết định giá trị cuối?
2. Khi một lượt Lưu có nhiều ô và chỉ một ô bị xung đột, mong muốn xử lý
   cả lượt hay từng ô ra sao?
3. Undo sau khi người khác đã sửa hoặc sau khi phân công đổi cần có hành vi nào?

**Trạng thái / Chủ dự án / 10.09.2026:** Ghi lại, bàn sau phiên này; chưa chốt
cách giải quyết mới. Giữ CAS/biên nhận/kiểm quyền hiện có, không tự cho ghi đè.

**Đã chốt riêng về lưu dữ liệu / Chủ dự án / 10.09.2026:** Các ô bảng Vận đơn
mới dùng lưu thủ công. Enter/chuyển ô/đóng popup giữ bản đang làm trong RAM;
Lưu dữ liệu hoặc Ctrl+S mới ghi database. Rời bảng/tải lại/đóng tab mất phần
chưa lưu, không hỏi ba lựa chọn. Phân công, Chi tiết và Nhập Excel vẫn xác nhận
riêng. Menu … gom Lưu dữ liệu, Nhập/Xuất, Phân công; Chia sẻ link chưa triển khai.

## 11.09.2026 — Bỏ khung nhập che bảng

**Hỏi:** Chỉnh sửa nhập ngay trong ô, Tab/Enter chuyển ô; chọn vùng rồi
dán/xóa/định dạng vẫn dùng autosave và kiểm xung đột, được không?

**Chủ dự án duyệt:** Có; đồng thời sửa lỗi Admin lúc bấm được lúc không và
tiếp tục chạy bền. Ô tổng, chi tiết và phân công giữ cơ chế riêng.
Không mở thêm quyền hay đổi quy tắc trạng thái thanh toán.

## 10.09.2026 — Chốt chín hạng mục Vận đơn mới

1. Lưu thế nào? Tự lưu nền sau kết thúc sửa; 500ms/tối đa 2s. Không hỏi khi
   đổi chức năng; chỉ cảnh báo rời trang nếu còn chưa xác nhận.
2. Định dạng gì? Cỡ chữ, màu chữ, màu nền; không thêm bộ định dạng đầy đủ.
3. Ai xem lịch sử? Người hiện có quyền xem dòng. Chỉ lịch sử qua lưới mới,
   không suy dựng từ nhập file/phân công/chi tiết cũ.
4. Xung đột? Làm cùng đợt; giữ RAM trong phiên. Người sửa đối chiếu và chọn,
   cả lượt được kiểm lại; không lưu một phần hoặc ghi đè âm thầm.
5. Admin đứng đơn? Chỉ CRM thêm chọn Sale. Admin là người thực hiện, Sale
   là người đứng đơn; phòng ban/team của đơn theo Sale.
   **Thay thế 11.09.2026:** chủ dự án chốt Admin cũng tự đứng đơn bằng mã của mình, bỏ chọn Sale. Admin thử nghiệm không thuộc Sale dùng Sale/team trống làm giá trị nội bộ; không đổi hồ sơ. Chi tiết ADR-023.
6. Chế độ Chỉnh sửa? Mũi tên trong chữ, Tab chuyển ô, Enter ô một dòng xuống
   hàng; nhiều dòng dùng Ctrl+Enter kết thúc. Mặc định vẫn là chế độ Xem.
7. Lịch sử lưu ở đâu, có chậm/phình không? Sau triển khai: PostgreSQL
   `crm_gridcellhistory` lưu trước/sau theo ô; 300.000 mục test gồm chỉ mục
   khoảng 69,28 MiB. Biên nhận `crm_gridmutationreceipt` là bảng riêng,
   320 lượt test khoảng 2,26 MiB, chứa cả kết quả để gửi lại an toàn.
   Trang 50 lịch sử p95 28,56ms trong TestClient riêng; chưa đại diện mọi tải.
   Nháp chỉ ở RAM trình duyệt. Dung lượng tăng theo số ô/lượt sửa và độ dài,
   không bằng số khách. Xem kịch bản năm và giới hạn trong báo cáo
   [chín hạng mục](kiem-chung-master-nine.md). Chưa tự đặt thời hạn xóa.
