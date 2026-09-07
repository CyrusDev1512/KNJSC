# Product

<!-- impeccable:product-schema 1 -->

> Hồ sơ sản phẩm cho skill thiết kế (Impeccable). Ba điều ghi "xác nhận 06.09.2026"
> là câu trả lời trực tiếp của chủ dự án trong phiên `/impeccable init`; phần còn
> lại lấy từ `docs/` và các quyết định đã chốt trong `docs/quyet-dinh/`. Không ghi
> hướng thẩm mỹ ở đây: màu, chữ, bố cục thuộc về DESIGN.md và từng màn hình.

## Platform

web

## Users

Nhân viên ba bộ phận của Kim Ngân JSC, công ty thương mại điện tử xuyên biên
giới đang bán sang Canada và Philippines:

- **Marketing**: chạy quảng cáo, thu tin nhắn khách, nộp báo cáo hằng ngày, dùng bảng dữ liệu.
- **Sale**: tư vấn, chốt đơn, lên đơn, nộp báo cáo hằng ngày.
- **Vận đơn**: giao hàng, theo dõi trạng thái, đối soát thanh toán, làm việc trên bảng vận đơn.

Ba cấp bậc quyết định phạm vi dữ liệu: **Staff** chỉ thấy của mình, **Leader**
thấy cả team mình phụ trách, **Manager** thấy cả bộ phận; thêm **Admin** quản
trị toàn hệ thống. Một bộ phận có nhiều team, Manager tự thêm.

Quy mô: dưới 100 người dùng, tối đa 50 người cùng lúc, mỗi team thêm khoảng
2.000 đến 5.000 bản ghi mỗi tháng.

Tình huống dùng (xác nhận 06.09.2026): làm việc ở văn phòng trên **máy tính là
chính**; điện thoại là phụ, để nộp báo cáo ngày hoặc xem nhanh. Một số người
dùng máy cấu hình thấp hoặc mạng yếu, nhưng chủ dự án chốt cùng ngày: **hiện
chưa cần quá lo về hiệu năng**, giữ trang gọn là đủ.

## Product Purpose

Một nơi làm việc chung thay cho biểu mẫu và bảng tính rời rạc trên Google Form,
Google Sheets và Lark: dữ liệu nhập một lần, bộ phận liên quan đều thấy; mỗi
người chỉ thấy phần thuộc quyền; báo cáo tổng hợp tự sinh từ dữ liệu đã có.

Thành công nghĩa là ba bộ phận đối chiếu được số với nhau, không ai xem được
dữ liệu ngoài quyền, và quản lý không còn gom báo cáo tay mỗi ngày.

Hai phần có tên riêng (xác nhận 06.09.2026):

- **KNERP**: hệ thống chính. Đăng nhập, báo cáo hằng ngày, lên đơn, bảng dữ liệu, báo cáo tổng hợp, quản lý biểu mẫu và bảng.
- **KN CRM**: bảng tính kiểu Excel cho bảng vận đơn và các bảng khác trong phạm vi quyền, chạy ở dịch vụ riêng (cổng 8021 trên máy cá nhân, sau này là subdomain riêng).

Tên công ty **Kim Ngân JSC** đứng ở tiêu đề trang và chân trang.

## Positioning

Quản lý tự dựng bảng và biểu mẫu cho từng thị trường mà không sửa mã (bảng
động, ADR-001), nhưng mỗi ô trong bảng vẫn là một bản ghi thật có phạm vi quyền
theo cấp bậc và có nhật ký không sửa được, còn người dùng thao tác trên nó như
bảng tính quen thuộc (ADR-009, ADR-011). Google Sheets hay Lark không phân
quyền được đến từng dòng theo cấp bậc; một ERP đóng gói không cho tự tạo bảng
theo thị trường mới.

## Operating Context

- Dây chuyền Marketing → Sale → Vận đơn; dữ liệu đơn hàng đi qua cả ba bộ phận.
- Nhịp ngày: nộp báo cáo hằng ngày theo biểu mẫu của bộ phận; Sale lên đơn trong ngày; Vận đơn cập nhật trạng thái và đối soát; Manager xem báo cáo tổng hợp theo ba cách nhóm và xuất Excel.
- Dữ liệu vào ra bằng Excel và CSV: nhập bốn bước có xem trước và tiến độ, xuất kèm bộ lọc, tệp lớn chạy nền. Bảng vận đơn có mỗi sản phẩm một cột số lượng.
- Tiền tệ CAD và PHP. Giờ lưu theo UTC, hiển thị theo giờ Việt Nam.
- Hiện chạy trên máy cá nhân bằng Docker (`KN JSC.bat` ở thư mục gốc), sao lưu tự động 02:00 mỗi đêm giữ 30 bản. Máy chủ thật và tên miền là Giai đoạn 8, chưa có.
- Nghiệm thu bằng tay theo `docs/07-kich-ban-nghiem-thu.md`; tới 06.09.2026 chưa màn hình nào được nghiệm thu chính thức.

## Capabilities and Constraints

- Tài khoản riêng từng người, buộc đổi mật khẩu lần đầu, tự đăng xuất sau một giờ không thao tác, khoá 15 phút sau năm lần sai.
- Phân quyền áp ở tầng truy cập dữ liệu; truy cập ngoài phạm vi trả lỗi từ chối, không trả danh sách rỗng.
- Bảng động và biểu mẫu do Manager tạo. Danh sách chọn, màu cột, cột khoá là thuộc tính của cột (ADR-013); định dạng ô lưu trong cơ sở dữ liệu (ADR-010).
- Xoá là đánh dấu, không xoá cứng. Nhật ký hoạt động không sửa được. Tiền lưu dạng số thập phân chính xác.
- Kỹ thuật: Django 5.2, PostgreSQL 16, HTMX, Celery với Redis, Docker Compose. Giao diện là HTML, CSS và JS thuần: **không thêm khung giao diện như React hay Vue, không nhúng thư viện bảng tính (ADR-002), không thêm thư viện mà chưa hỏi.** Màn hình danh sách phân trang 25 dòng, lưới bảng tính 100 dòng.
- Ngôn ngữ: nhãn và thông báo trên giao diện bằng tiếng Việt có dấu; tên trong mã nguồn bằng tiếng Anh.
- Thuật ngữ cố định: bộ phận, team, cấp bậc (Staff, Leader, Manager, Admin), báo cáo hằng ngày, lên đơn, bảng dữ liệu, bảng tính (KN CRM), vận đơn, biểu mẫu, bảng động.
- Chưa quyết: máy chủ và tên miền thật (Giai đoạn 8); công thức kiểu `=SUM()` trong bảng tính (backlog S10).

## Brand Commitments

- Tên gọi (xác nhận 06.09.2026): **KNERP** cho hệ thống chính, **KN CRM** cho bảng tính, **Kim Ngân JSC** là tên công ty.
- Biểu tượng hiện có: chữ KN trắng trên nền xanh chuyển sắc, vạch cam, chữ JSC nhỏ; nguồn `scripts/KN JSC.svg`, tệp `scripts/KN JSC.ico`. Đang dùng cho lối tắt trên máy tính; chưa chốt là logo chính thức trên giao diện.
- Giọng nói: tiếng Việt có dấu, ngắn, nói thẳng việc; thông báo lỗi nói rõ người dùng nên làm gì tiếp.
- Hướng thiết kế (chốt 07.09.2026 trên bàn chọn, sau hai vòng gieo): **chuẩn ngành theo Google Workspace và Google Sheets**, chơi thẳng. Mốc chất lượng là độ tinh của Sheets và Workspace. Đang dựng thử trên nhánh `claude/thiet-ke-chuan-nganh`, chưa gộp.

## Evidence on Hand

- Tệp vận đơn thật đã ẩn danh: `docs/tham-khao/vandon-mau.xlsx`.
- Mười ảnh chụp bảng tính KN Demo mà chủ dự án muốn giống: `docs/tham-khao/kn-demo/`.
- Dữ liệu mẫu: lệnh `du_lieu_mau` tạo 12 tài khoản, bảng Báo cáo Marketing với số liệu thật, biểu mẫu và sản phẩm; danh sách ở `docs/tai-khoan-mau.md`.
- Không có: lời khách hàng, nghiên cứu người dùng chính thức, số liệu hiệu quả sau khi dùng. Không bịa những thứ này.

## Product Principles

1. Nhập một lần, ai liên quan đều thấy đúng số đó.
2. Chỉ thấy phần thuộc quyền, và không có đường vòng.
3. Quản lý tự dựng bảng và biểu mẫu, không đợi sửa mã.
4. Số liệu và nhật ký là sự thật: không làm tròn sai, không sửa được lịch sử.
5. Thiết kế cho máy tính trước, nhưng điện thoại phải dùng được. Gọn nhẹ là nếp tốt, không phải rào cản: chưa cần hy sinh hiệu ứng hay tính năng vì hiệu năng.

## Accessibility & Inclusion

- Một số người dùng máy cấu hình thấp hoặc mạng yếu (xác nhận 06.09.2026), nhưng **hiện chưa cần quá lo về hiệu năng** (chủ dự án chốt cùng ngày). Giữ nếp gọn: không tải thứ không dùng, lưu từng ô không mất dữ liệu khi rớt mạng. Tối ưu sâu để sau, khi có số đo thật.
- Điện thoại là phụ nhưng phải dùng được: 390px không tràn ngang, đã có kiểm thử tự động.
- Trình đọc màn hình và tương phản cao: chưa ai nêu yêu cầu. Ghi nhận là chưa quyết, không phải "không cần".
