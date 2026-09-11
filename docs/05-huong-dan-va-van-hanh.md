# Hướng dẫn sử dụng và vận hành

**CRM-Optimization — đã kiểm local, chưa phát hành, 11.09.2026:** cấu hình production ứng
viên và quy trình bật/tắt từng nhóm ở
[deploy/production/README](../deploy/production/README.md). Không thay launcher
hoặc Compose local. Cờ tối ưu mặc định tắt; không tự migrate DB đang dùng.
Thống kê khi bật cache hiển thị thời điểm tính, tối đa 15 giây; nút Làm mới
lấy số liệu mới. Không đổi cách nhập/sửa của vận đơn.
Xem [kết quả và điều kiện chưa đạt](kiem-chung-crm-optimization-20260911.md):
không bật đồng loạt chỉ vì bài tải trả mã 0. Đặc biệt theo dõi backlog xuất,
cold Thống kê và tăng RAM app; renderer giữ tắt khi chưa có lợi ích ổn định.

**11.09.2026 — Điều hướng ERP/thư viện/Lên đơn CRM:** đã triển khai local theo ADR-023. Giữ Bảng dữ liệu ERP; sửa Biểu mẫu thiếu người tạo, gộp hai tab đúng quyền; chuyển nhập đơn và xem đơn gốc sang CRM. Kiểm thử, số đo và giới hạn tại [báo cáo bàn giao](kiem-chung-erp-hub-20260911.md). Chưa commit/push.

| Mục | Nội dung |
|---|---|
| Dự án | Kim Ngân JSC — Hệ thống vận hành nội bộ |
| Phiên bản tài liệu | 0.1 — bản nháp |
| Ngày | (điền ngày) |
| Người viết | (điền tên) |

> Tài liệu này chia làm hai phần.
> **Phần A** dành cho người sử dụng hệ thống hằng ngày.
> **Phần B** dành cho người giữ cho hệ thống chạy được.
>
> Nếu bạn chỉ dùng hệ thống thì đọc phần A là đủ.

> ## ⚠ Một mục chưa chạy được
>
> Cập nhật 06.09.2026 — xong Giai đoạn 0 tới 7. Mọi mục dưới đây đều chạy được,
> trừ một chỗ:
>
> | Mục | Chờ |
> |---|---|
> | **A5 · Báo cáo tổng hợp** — riêng cách nhóm **Theo thị trường** | Chờ chốt backlog N9 |
>
> Danh sách đầy đủ những gì đã chạy và chưa chạy nằm ở `backlog.md` **mục 0**.

---

# PHẦN A — HƯỚNG DẪN SỬ DỤNG

## A1. Bắt đầu

### Đăng nhập

1. Mở trình duyệt, vào địa chỉ được cấp
2. Nhập email và mật khẩu
3. Lần đầu đăng nhập, hệ thống yêu cầu đổi mật khẩu — đây là bắt buộc

**Nếu không thao tác quá một tiếng**, hệ thống tự đăng xuất để bảo vệ dữ liệu.
Đăng nhập lại là tiếp tục được.

**Nếu nhập sai mật khẩu năm lần**, tài khoản bị khoá tạm mười lăm phút.

### Sau khi đăng nhập

Mọi người đều vào **trang Tổng quan** (Q34 — 03.09.2026). Thanh bên trái chỉ
hiện những mục thuộc phận sự của bạn; việc của bộ phận nào thì bấm vào mục
tương ứng — Sale vào **Lên đơn**, Marketing vào **Nộp báo cáo ngày**, Vận đơn
vào **Bảng dữ liệu**.

---

## A2. Nộp báo cáo hằng ngày

Mỗi bộ phận có biểu mẫu riêng.

1. Vào mục **Báo cáo**
2. Chọn **Nộp báo cáo hôm nay**
3. Điền các trường, những trường có dấu sao là bắt buộc
4. Bấm **Gửi**

**Trường Marketer / Người bán hệ thống tự ghi tên bạn**, ô chỉ đọc, không phải
điền. **Trường kiểu Chọn một là ô chọn**: chọn từ danh sách, không gõ tay được;
thiếu giá trị cần chọn thì báo quản lý thêm (quản lý thấy thêm mục **＋ Thêm
mới…** ngay cuối danh sách: chọn nó, gõ giá trị, Enter là có).

**Sau khi gửi thì không sửa được.** Kiểm tra kỹ trước khi bấm.

### Xem lại báo cáo cũ

Vào mục **Báo cáo** rồi chọn **Báo cáo của tôi**. Danh sách hiện các báo cáo
đã nộp, sắp xếp theo thời gian mới nhất.

Bạn xem lại được nhưng không sửa được.

### Nếu bạn là Leader hoặc Manager

Bạn thấy thêm mục **Báo cáo cấp dưới** — danh sách báo cáo của người thuộc
phạm vi quản lý.

| Cấp bậc | Thấy báo cáo của ai |
|---|---|
| Staff | Chỉ mình |
| Leader | Toàn bộ team mình phụ trách |
| Manager | Toàn bộ bộ phận |

---

## A3. Lên đơn — dành cho Sale

### Tạo đơn mới

1. Vào mục **Lên đơn**
2. Điền thông tin khách hàng
3. Thêm sản phẩm: chọn sản phẩm từ danh mục, nhập số lượng. Sản phẩm chưa có
   trong danh mục thì quản lý chọn **＋ Thêm mới…** cuối danh sách, gõ tên, Enter —
   sản phẩm vào danh mục, được chọn ngay, và bảng vận đơn có thêm cột số lượng
4. Bấm **Thêm sản phẩm** nếu đơn có nhiều mặt hàng
5. Nhập giá bán và phương thức thanh toán
6. Bấm **Lưu đơn**

**Sau khi lưu, đơn tự động chuyển sang bộ phận vận đơn.** Bạn không cần làm gì thêm.

### Khách đã mua trước đó

Nếu số điện thoại đã có trong hệ thống, màn hình hiện thông báo kèm số lần
khách này đã mua. Thông tin này giúp bạn tư vấn phù hợp hơn.

### Xem lại đơn cũ

Vào mục **Đơn của tôi**. Danh sách hiện các đơn bạn đã tạo.

**Đơn đã lưu không sửa được.** Nếu có sai sót, báo cho quản lý để xử lý.

---

## A4. Bảng dữ liệu — dành cho Marketing và Vận đơn

### Xem và tìm

| Việc | Cách làm |
|---|---|
| Cuộn xem nhiều dòng | Cuộn chuột hoặc kéo thanh cuộn |
| Chuyển trang | Nút chuyển trang ở cuối bảng |
| Tìm nhanh | Ô tìm kiếm ở đầu bảng |
| Lọc theo cột | Bấm biểu tượng lọc ở tiêu đề cột |
| Sắp xếp | Bấm vào tiêu đề cột, bấm lần nữa để đảo thứ tự |

### Chỉ xem — sửa số liệu ở KN CRM

Bảng dữ liệu chỉ để xem, với mọi bảng và mọi cấp bậc (ADR-014): bấm vào ô
không mở được gì. Đầu bảng có dòng báo "Bảng này chỉ để xem" và nút **Mở
trong KN CRM** dẫn sang đúng bảng đó trên lưới KN CRM (mục A8) — sửa, dán,
thêm dòng, định dạng đều ở đó. Cột tính sẵn (nền chàm nhạt) hệ thống tự tính ở
mọi nơi. Cột kiểu Chọn một hiện giá trị dạng chữ; danh sách chọn Quản lý đặt
trong **Sửa cột** hoặc thêm bằng **＋ Thêm mới…** ở biểu mẫu, báo cáo ngày và
Lên đơn.

**Viền và màu.** Mọi ô có viền, tiêu đề cột nền xanh lá. Quản lý đặt trong
**Sửa cột** cho từng cột: **Màu cột** (vàng, đỏ, xanh lá, xanh dương) tô cả tiêu
đề lẫn ô; **Cảnh báo** kèm **Ngưỡng** cho cột số — ô vượt ngưỡng tô đỏ, ô đạt tô
xanh lá, ô trống không tô. Màn hình xem lại báo cáo cũng mang màu đó.

### Nhập từ tệp Excel

Ai làm được: quản lý trở lên của bộ phận sở hữu bảng, hoặc người được cấp
quyền *Sửa* trên bảng.

1. Bấm **Nhập tệp**, chọn tệp `.xlsx` hoặc `.csv` từ máy, bấm **Tải lên và xem trước**
2. Màn hình xem trước cho biết cột nào trong tệp khớp cột nào của bảng, cột
   nào bị bỏ qua (và vì sao), kèm năm dòng đầu để đối chiếu
3. Bấm **Xác nhận nhập** — từ lúc này mới ghi vào bảng
4. Trang **Tác vụ nền** hiện tiến độ, tự cập nhật mỗi hai giây; xong thì ghi
   số dòng đã nhập và **liệt kê từng dòng lỗi theo số hàng trong tệp Excel**
   để bạn mở tệp sửa đúng chỗ

Tệp không cần chỉnh sửa trước: hệ thống tự tìm hàng tiêu đề trong 10 hàng
đầu, hiểu tên cột tiếng Anh của tệp cũ (Name, Phone, Add…), đổi số điện thoại
Excel lưu dạng số về chữ, đọc ngày kiểu `14/10/2023`. Ô danh sách (trạng thái)
chỉ nhận giá trị trong danh sách, không phân biệt hoa thường.

**Giới hạn:** tệp tối đa 10 MB, tối đa 5.000 dòng mỗi lần. Tệp đổi đuôi (ví
dụ `.exe` đổi thành `.xlsx`) bị từ chối ngay.

Dòng lỗi không chặn dòng hợp lệ: 5 dòng có 2 dòng lỗi thì 3 dòng vẫn vào.

### Xuất ra tệp Excel

Bấm **Xuất tệp**. Tệp mang **đúng những gì đang hiện** — bộ lọc, tìm kiếm,
sắp xếp đi theo — và chỉ gồm dòng trong phạm vi quyền của bạn.

Dưới 2.000 dòng thì tải về ngay. Lớn hơn thì hệ thống xuất ở nền và báo; tệp
sẵn sàng thì tải ở trang **Tác vụ nền**, giữ 24 giờ rồi tự dọn. Trần 50.000
dòng một lần — quá thì thu hẹp bộ lọc.

Tệp xuất ra nhập lại được vào hệ thống mà không cần chỉnh sửa.

---

## A5. Báo cáo tổng hợp

### Xem báo cáo

1. Vào mục **Báo cáo · Báo cáo tổng hợp**
2. Chọn **Nguồn số liệu** — một bảng trong phạm vi quyền của bạn, ví dụ Báo
   cáo Marketing hay Bảng vận đơn. Mỗi lần xem một bảng, số liệu không lẫn
   nguồn (Q35)
3. Chọn khoảng thời gian — mặc định từ đầu tháng tới hôm nay
4. Chọn cách nhóm bằng các thẻ phía trên bảng

| Cách nhóm | Cho biết |
|---|---|
| Tổng hợp | Số liệu từng ngày và cả kỳ |
| Theo nhân viên | Ai làm được bao nhiêu |
| Theo sản phẩm | Sản phẩm nào bán chạy, kèm tỉ trọng |
| Theo thị trường | **Đang hoãn** — chờ chốt nguồn số liệu, backlog N9 |

Số liệu đã lọc sẵn theo phạm vi quyền: nhân viên thấy phần của mình, trưởng
nhóm thấy cả team, quản lý thấy cả bộ phận. Dòng cuối bảng là **tổng cộng**;
các cột tính sẵn như CPO hay tỉ lệ chốt được tính lại trên tổng, không phải
cộng dồn từng dòng.

### Bộ lọc

Các bộ lọc phía trên bảng: khoảng thời gian, sản phẩm.
Chọn nhiều điều kiện thì chúng cộng dồn với nhau. Điền cả hai ô ngày rồi bấm
**Áp dụng** thì bốn ô số đầu trang hiện thêm chênh lệch so với kỳ liền trước.

### Xuất báo cáo

Bấm **Xuất Excel**. Tệp tải về chứa đúng số liệu đang hiển thị trên màn hình,
kể cả dòng tổng cộng. Mọi lần xuất đều được ghi vào nhật ký hoạt động
(nguyên tắc P5).

---

## A6. Quản lý biểu mẫu — dành cho Manager

### Tạo biểu mẫu mới

1. Vào mục **Quản lý biểu mẫu**
2. Bấm **Tạo biểu mẫu**
3. Đặt tên, chọn bộ phận áp dụng
4. Chọn các trường từ danh sách, kéo thả để sắp xếp thứ tự
5. Đánh dấu trường nào bắt buộc
6. Chọn bảng đích — nơi dữ liệu sẽ được ghi vào
7. Phân quyền: ai được điền, ai được xem bảng
8. Bấm **Lưu**

### Sửa biểu mẫu đã có

Sửa được, và **dữ liệu đã nhập trước đó không bị mất**.

Nhưng lưu ý: nếu bỏ một trường khỏi biểu mẫu, dữ liệu cũ của trường đó vẫn còn
trong bảng nhưng không nhập thêm được nữa.

### Tạo bảng mới

Tương tự tạo biểu mẫu. Chọn các cột, đặt kiểu dữ liệu cho từng cột.

Cột nào dùng để thống kê thì gán **nhãn ý nghĩa** — ví dụ cột "Giá bán" gán nhãn
"Doanh thu". Nhờ vậy báo cáo tổng hợp mới tính được.

### Sửa cột

| Ô | Dùng khi |
|---|---|
| **Danh sách chọn** | Cột kiểu Chọn một: gõ mỗi dòng một giá trị. Cột mang nhãn Sản phẩm lấy danh sách từ danh mục sản phẩm, nhãn Người bán gợi ý nhân sự bộ phận — hai cột đó không nhập tay ở đây |
| **Màu cột** | Tô nền tiêu đề và mọi ô của cột trên Bảng dữ liệu |
| **Cảnh báo** và **Ngưỡng** | Chỉ cột kiểu số: chọn "Đỏ khi lớn hơn" hay "Đỏ khi nhỏ hơn" kèm ngưỡng; ô vượt tô đỏ, ô đạt tô xanh lá |

---

## A7. Câu hỏi thường gặp

| Tình huống | Cách xử lý |
|---|---|
| Quên mật khẩu | Liên hệ quản trị viên để đặt lại |
| Tài khoản bị khoá | Chờ mười lăm phút, hoặc liên hệ quản trị viên |
| Không thấy mục nào đó trong menu | Bạn chưa được cấp quyền, liên hệ quản lý |
| Không thấy dữ liệu của người khác | Đúng như thiết kế, mỗi cấp bậc có phạm vi riêng |
| Hệ thống tự đăng xuất | Do không thao tác quá một tiếng, đăng nhập lại |
| Nhập tệp báo lỗi | Kiểm tra kích thước dưới 10 MB và số dòng dưới 5.000; đuôi tệp phải đúng nội dung |
| Nhập xong báo "dòng lỗi" | Mở trang Tác vụ nền, xem bảng dòng lỗi theo số hàng Excel, sửa tệp rồi nhập lại phần đó |
| Ô chọn không có giá trị mình cần | Cột Chọn một chỉ nhận giá trị trong danh sách. Quản lý thêm ở Sửa cột hoặc chọn **＋ Thêm mới…** ngay tại ô chọn trên biểu mẫu, báo cáo ngày, Lên đơn; nhân viên báo quản lý |
| Không gõ được ô Marketer / Người bán | Đúng như thiết kế — hệ thống tự ghi tên bạn (FR-4.6) |
| Không sửa được ô trên Bảng dữ liệu | Đúng như thiết kế — Bảng dữ liệu chỉ để xem với mọi bảng; sửa số liệu ở KN CRM, cổng 8021, nút **Mở trong KN CRM** ngay đầu bảng (mục A8, ADR-014) |
| Bảng tính không có dòng trống cuối lưới | Bạn không có quyền thêm dòng vào bảng đó |
| Nút định dạng báo "Chưa chọn ô nào" | Bấm vào một ô trước, Shift+bấm để chọn vùng |
| Bảng tính báo "không có trong danh sách" | Ô đó chỉ nhận giá trị trong danh sách chọn — chọn từ ô xổ xuống |
| Lỡ nhập sai đơn đã lưu | Báo quản lý, không tự sửa được |

---

## A8. KN CRM — app Bảng tính, lưới kiểu Excel cho mọi bảng

Mục **KN CRM** trên thanh bên của KN ERP mở **một tab mới** sang app riêng
(máy phát triển: `http://localhost:8021/`; trên máy chủ là tên miền con, dùng
chung đăng nhập). Đây là nơi làm việc trên dữ liệu; KN ERP chỉ để xem nhanh
và làm nghiệp vụ. Bạn chỉ thấy bảng trong phạm vi của mình; gọi thẳng đường
dẫn bảng khác cũng bị từ chối.

### Trang chủ và menu trái

Vào KN CRM là **trang chủ tổng quan** có **menu trái** (ADR-015): trên cùng là
chữ cái đầu tên, tên và cấp bậc của bạn; rồi **Trang chủ**, **Bảng tính** (gập
được — mục con là từng bộ phận bạn có bảng), **Nhập tệp** (Leader trở lên),
**Cấp quyền** (Manager), **Tác vụ nền**, **Nhật ký** (Manager) và **KN ERP**.
Nút **‹** ở đầu thanh trên thu gọn menu còn dải biểu tượng, nhớ cho lần sau.
Logo KN CRM (ô xanh chữ KN có dấu lưới) ở đầu menu trái và ở thanh trên của lưới:
bấm vào là về trang chủ; tab trình duyệt cũng mang logo đó, còn KN ERP mang logo KN JSC.
Trang chủ ghi số dòng nhập tháng này và hôm nay, số bảng, tổng số dòng, bảng
cập nhật gần nhất, danh sách bảng có nút **Mở** và hoạt động gần đây — tất cả
đã lọc theo phạm vi của bạn. Trang có menu trái **không có nút ←**; về hệ thống
chính bằng mục **KN ERP**.

### Bảng tính: Bộ phận ▸ Quý ▸ Tháng ▸ bảng

Bấm **Bảng tính** trên menu trái (hay một bộ phận dưới nó) là mở **trang thư
mục** với cây bên trái, như mở ổ đĩa thời còn dùng Sheet:
bộ phận (chỉ bộ phận nào bạn có bảng được xem), rồi **Quý**, rồi **Tháng**, mỗi
tháng ghi số dòng. Bấm một tháng thì bên phải liệt kê các bảng của bộ phận
có cột Ngày, kèm số dòng trong tháng, lần cập nhật gần nhất và nhãn **Xem**
hay **Sửa** (quyền của bạn trên bảng đó, do Manager cấp ở KN ERP). Bấm **Mở**
là vào lưới **lọc sẵn đúng tháng đó** — thanh trên ghi "Tháng 9/2026". Tháng
chỉ là góc nhìn: vẫn là một bảng, dữ liệu không bị tách. Mục **Toàn bộ bảng**
dưới mỗi bộ phận liệt kê mọi bảng không lọc thời gian, xếp theo thư mục tay
(Leader hay Manager của bộ phận tạo bằng nút **+ Thư mục**; nút **+ Tạo bảng**
cũng ở đây). Bảng không có cột Ngày chỉ nằm ở đó.

Bấm một bảng mới mở **lưới toàn màn hình** — menu trái ẩn đi để lưới rộng như
Excel. Từ lưới, bấm **←** ở góc trên trái là về trang thư mục, cây mở đúng chỗ
vừa rời và thấy lại menu trái. ← không bao giờ đưa bạn sang KN ERP.

### Quản lý bộ phận: Leader và Manager

Trong KN CRM, **Leader được như Manager trong bộ phận mình**: tạo bảng, sửa và
chèn/bỏ cột, tạo thư mục, nhập tệp, tải Excel, sửa hay xoá dòng của người khác
trong phạm vi mình thấy. Chỉ **cấp quyền cho người ngoài bộ phận** vẫn là việc
của Manager. Ba việc này làm ngay trong KN CRM, không phải bật sang KN ERP:
**Nhập tệp** trên menu trái liệt kê bảng bạn được nhập, bấm **Nhập tệp** là vào
luồng bốn bước quen thuộc; **Cấp quyền** (Manager) liệt kê bảng của bộ phận,
bấm **Cột & cấp quyền** là màn Sửa cột có phần cấp quyền ở dưới; **+ Tạo bảng**
có ở trang chủ và trang thư mục.

### Lưới

Lưới là một trang **toàn màn hình**, nhìn và dùng như một bảng tính quen
thuộc: khung tối viền vàng, thanh công cụ, thanh công thức, cột số dòng, chữ
cột A B C… Z, ô có viền, chân trang có tab các bảng. Thanh trên có **←** về
trang thư mục, tên bảng, nhãn tháng đang xem (nếu có), trạng thái lưu ("Đã lưu",
"Đang lưu…", "Lỗi lưu"), nút **Tải Excel**, nút **⛶** phóng toàn màn hình (Esc
để thoát) và chữ cái đầu tên bạn — bấm vào mở menu Nền sáng/tối, các màn hình
khác và Đăng xuất.

**Hàng 1 là tên cột, dữ liệu từ hàng 2**, số dòng nối tiếp qua các trang (mỗi
trang 100 dòng, chuyển trang ở chân trang). Cột trống bên phải chỉ để nhìn cho
đủ chữ tới Z — gõ vào không có gì; Manager thêm cột thật bằng chuột phải. Cuối
lưới luôn thừa dòng trống để gõ bản ghi mới; nút **+100 dòng** ở chân trang
thêm dòng trống.

**Chọn và sửa:** bấm một lần là **chọn** ô (viền vàng, ô địa chỉ trên thanh
công thức hiện `B3`); kéo chuột để chọn vùng (`B3:D6`), bấm số dòng chọn cả
hàng, bấm chữ cột chọn cả cột, góc trên trái chọn cả trang. **Bấm đúp**, Enter,
F2 hoặc gõ thẳng chữ số mới mở sửa; rời ô đã đổi thì tự lưu. Ô giá trị trên
thanh công thức cũng sửa được: Enter lưu rồi xuống dòng, Tab sang phải. Gõ `=`
thì báo chưa hỗ trợ công thức — dùng cột tính sẵn (Manager đặt trong Sửa cột).

**Cột:** kéo mép phải của chữ cột để đổi độ rộng; kéo thả chữ cột sang chỗ
khác để đổi thứ tự (cột đứng yên khi cuộn không đổi được); **⋯ → Ẩn/hiện cột**
để giấu cột; **Đặt lại cột** để về mặc định. Ba thứ này nhớ trên trình duyệt
của bạn, không ảnh hưởng người khác.

**Bộ phận Vận đơn:** bảng vận đơn sửa ở địa chỉ riêng
**`http://localhost:8021/bang-tinh/`** (trên máy chủ sẽ là một subdomain), cùng
tài khoản. Ở KN ERP mọi bảng, kể cả bảng vận đơn, chỉ xem (ADR-014). Lưới vận đơn dựng theo đúng
tệp Excel bộ phận đang dùng: mỗi sản phẩm một cột số lượng, trạng thái chọn từ
danh sách, cột Trùng đếm số điện thoại trùng, đơn Hủy tô đỏ, bốn cột đầu và
hàng tiêu đề đứng yên khi cuộn.

### Thanh công cụ

| Nút | Làm gì |
|---|---|
| ↶ ↷ | Hoàn tác, làm lại (Ctrl+Z, Ctrl+Y) — tối đa 100 bước, tải lại trang là hết |
| Định dạng số · Cỡ chữ | Số, phần trăm, USD, VND, văn bản cho ô số; cỡ chữ 10–28 |
| **B** *I* U S · A · ▣ | Đậm, nghiêng, gạch chân, gạch ngang; màu chữ và màu nền từ bảng 40 màu |
| ⫷ ⫶ ⫸ · ↩ · ▦ · Xóa ĐD | Căn trái/giữa/phải, xuống dòng trong ô, viền đậm, xoá mọi định dạng của vùng chọn |
| Bộ lọc | Mở thanh bên trái (bảng, chọn nhanh ngày, sản phẩm, tìm) |
| ⋯ | Việc riêng của hệ thống: Nhập tệp, Thêm cột, Thư mục mới, Ẩn/hiện cột, Đặt lại cột, Lọc theo ô này, Bỏ mọi lọc, Bảng dữ liệu |
| Tải Excel (thanh trên) | Xuất đúng lưới đang lọc |

### Chuột phải

Chuột phải lên ô hay vùng đang chọn mở menu: **Cắt · Sao chép · Dán** (dán từ
Excel được — chép trong Excel rồi Ctrl+V trên lưới), **Chèn N hàng trống** (thêm
ở cuối lưới), **Xoá N hàng** (chỉ đánh dấu xoá, có hộp xác nhận, Ctrl+Z khôi
phục), **Chèn N cột bên trái / bên phải** và **Xoá N cột** (chỉ Manager của bộ
phận sở hữu bảng; cột khoá và cột đang dùng cho cột tính sẵn không xoá được),
**Xoá nội dung**, **Xoá định dạng**. Mục bạn không có quyền thì mờ đi.

### Dán, kéo điền, xoá nội dung

Chép vùng (Ctrl+C) rồi dán (Ctrl+V) vào ô khác — cả vùng lưu **một lần**, được
cả hoặc không: một ô sai (chữ vào cột số, để trống cột bắt buộc) thì báo đúng ô
đó và không ô nào đổi. Dán tràn xuống dòng trống thì thành dòng mới. Kéo ô
vuông vàng ở góc dưới phải vùng chọn để **điền tiếp**: số cách đều thì nối
chuỗi (1, 2, 3 → 4, 5), không thì lặp lại. **Delete** xoá nội dung vùng chọn.
Chân trang hiện Tổng · Trung bình · Số ô của vùng đang chọn.

### Tự cập nhật

Người khác sửa cùng bảng thì lưới của bạn tự nạp lại trong vài giây và hiện
"Có dữ liệu mới" — không cần bấm tải lại.

### Thanh bên trái

| Khối | Cách dùng |
|---|---|
| Bảng | Cây thư mục và bảng. Manager tạo, đổi tên, xoá thư mục (⋯ cạnh tên) và chọn thư mục cho bảng đang mở |
| Chọn nhanh | Hôm nay, Hôm qua, 7 ngày qua, Tháng này, Tháng trước — lọc theo cột Ngày |
| Khoảng ngày | Gõ Từ ngày, Đến ngày rồi Áp dụng |
| Sản phẩm | Tích một hay nhiều sản phẩm (hoặc Tất cả), Áp dụng — lấy dòng có **một trong** các sản phẩm đó |

Thanh bên ẩn mặc định — bấm **Bộ lọc** trên thanh công cụ để mở, bấm lần nữa
(hoặc **×** trong thanh bên) để đóng; trạng thái nhớ trên trình duyệt.

### Dòng trống và cột khoá

Gõ vào dòng trống cuối lưới rồi nhấn Enter hoặc rời khỏi dòng — dòng thành bản
ghi thật ngay, thuộc bộ phận sở hữu bảng. Sai kiểu hay thiếu cột bắt buộc thì
ô đỏ kèm lý do, giá trị đã gõ còn nguyên. Không thấy dòng trống nghĩa là bạn
không có quyền thêm vào bảng này.

Cột khoá (Manager đánh dấu trong Sửa cột; bảng vận đơn là Mã đơn) có nút **⌕**
trong ô: bấm là lọc lưới theo giá trị đó, cộng dồn với bộ lọc đang bật.

### Định dạng

Kéo chuột chọn vùng (hoặc **Shift+bấm**, Shift+mũi tên), rồi bấm nút trên
thanh công cụ: đậm (**B** hoặc Ctrl+B), nghiêng, gạch chân, gạch ngang, màu
chữ và màu nền (bảng 40 màu), cỡ chữ 10–28, căn trái/giữa/phải, xuống dòng,
viền, định dạng số, **Xóa ĐD**. Định dạng lưu vào hệ thống — ai mở bảng cũng
thấy — và đòi quyền sửa ô đó. Định dạng số chỉ đổi cách hiện; giá trị gõ vào
giữ nguyên. Ctrl+Z trả lại định dạng vừa đổi.

### Lọc

| Việc | Cách làm |
|---|---|
| Lọc một cột | Bấm **▼** trên chữ cột. Mọi cột: tích các giá trị (kèm số dòng), ô tìm để thu hẹp, Chọn tất cả / Không chọn, **Áp dụng**. Mục **Điều kiện khác**: cột số và ngày từ – đến, cột chữ chứa chữ, Chỉ ô trống / Chỉ ô có giá trị. **Xóa lọc** bỏ lọc của cột đó |
| Lọc nhiều cột | Lọc cột thứ hai thì cộng dồn với cột thứ nhất; chân trang ghi "Đang lọc N cột"; mỗi bộ lọc là một chip trong thanh bên **Bộ lọc**, bấm **×** để bỏ đúng lọc đó |
| Chỉ số điện thoại trùng | Bấm **Bộ lọc**, tích ô **Chỉ số điện thoại trùng** |
| Tìm nhanh | Ô tìm trong thanh bên **Bộ lọc** — tìm trong tên khách, số điện thoại, người bán, sản phẩm |
| Sắp xếp | Bấm tên cột ở hàng 1; bấm lần nữa để đảo |
| Chia sẻ đúng bộ lọc | Chép địa chỉ trên thanh trình duyệt — bộ lọc nằm trong đó |

Chân trang ghi `1–100 / N vận đơn` thay cho công thức đếm trong tệp cũ. Mỗi
trang 100 dòng, chuyển trang bằng ‹ ›.

### Sửa

| Việc | Cách làm |
|---|---|
| Sửa một ô | **Bấm đúp** vào ô, hoặc đi tới ô rồi **Enter** / F2, hoặc gõ thẳng giá trị mới (bấm một lần chỉ chọn ô) |
| Ô trạng thái, thanh toán, đối soát | Chọn từ danh sách — chọn xong là lưu ngay |
| Ô nhân viên vận đơn | Gợi ý danh sách tài khoản bộ phận, nhưng gõ mã khác vẫn được |
| Ghi chú nhiều dòng | Gõ Enter để xuống dòng, **Ctrl+Enter** để lưu |
| Huỷ | **Esc** |
| Di chuyển | Mũi tên bốn hướng, **Tab** sang ô kế, **Shift+Tab** lùi lại, Ctrl+Home về đầu, PageUp/PageDown 20 dòng; gõ địa chỉ như `B7` vào ô địa chỉ + Enter để nhảy tới |

Mỗi lần sửa ghi một dòng nhật ký (ai, lúc nào, giá trị cũ → mới). Giá trị
ngoài danh sách bị từ chối kèm lý do ngay tại ô.

### Nhập và xuất

**⋯ → Nhập tệp** mở luồng nhập của Bảng dữ liệu (mục A4) cho bảng vận đơn —
tệp Excel cũ của bộ phận nhập được không cần sửa. Nút **Tải Excel** ở thanh
trên xuất đúng lưới đang lọc (chưa mang theo định dạng ô).

---

## A9. Bảng tin — cả công ty

Mục **Bảng tin** trong nhóm Nội bộ trên thanh bên. Ai cũng thấy mọi bài, không
phân theo bộ phận.

| Việc | Cách làm |
|---|---|
| Đăng bài | Gõ vào ô trên cùng, bấm **Đăng**. Chỉ chữ, tối đa 2.000 ký tự; đường dẫn trong bài tự thành liên kết; gửi lỗi thì bài đang gõ vẫn còn |
| Thích, bình luận | Nút **♡ Thích** dưới bài (bấm lại là bỏ thích; bấm đúp cũng chỉ tính một lần); bấm **n bình luận** để mở bài và viết bình luận — số đổi ngay sau khi gửi. Bài chỉ hiện 20 bình luận mới nhất, bấm **Xem bình luận cũ hơn** |
| Ghim, gỡ bài | Manager và Admin thấy nút **Ghim** (bài lên đầu trang) và **Gỡ bài** với mọi bài; ai cũng gỡ được bài của mình. Gỡ là ẩn đi, không mất |
| Thiệp sinh nhật | Mỗi sáng 06:00 hệ thống tự đăng thiệp cho người có sinh nhật hôm đó — lấy từ **Ngày sinh** trong hồ sơ nhân sự (Nhân sự → Sửa). Không có ngày sinh thì không có thiệp. Máy tắt qua ngày sinh nhật thì lúc bật lại tự đăng bù (tối đa 14 ngày). Thiệp có tên người được chúc, bấm là ra trang thành viên |
| Thanh bên | Sinh nhật tháng này, năm người nhiều sao nhất, ba ghi nhận mới, thành viên vào trong 30 ngày |

---

## A10. Tài liệu

Quy định, quy trình, biểu mẫu dùng chung — chia theo **mục**. Bạn thấy mục dùng
chung toàn công ty và mục của bộ phận mình.

| Việc | Ai | Cách làm |
|---|---|---|
| Xem, tải về | Mọi người | Bấm **Tải về** (tệp) hoặc **Mở** (liên kết) — mỗi lượt có một dòng nhật ký. Lọc theo mục ở cột phải, tìm theo tiêu đề |
| Thêm mục | Manager (mục bộ phận mình), Admin (cả mục toàn công ty) | Ô **Thêm mục** ở cột phải |
| Tải lên | Manager trở lên | **Tải lên**: chọn mục, tiêu đề, rồi chọn tệp (PDF, Word, Excel, CSV, ảnh; tối đa 10 MB) **hoặc** dán liên kết Google Drive, Notion… |
| Gỡ | Người tải, Manager bộ phận, Admin | Nút **Gỡ** — ẩn đi, không xoá tệp |

Tệp được kiểm theo nội dung, không theo đuôi: đổi tên `.exe` thành `.pdf` vẫn
bị từ chối; tệp ZIP đổi đuôi `.docx` hay `.xlsx` cũng bị từ chối nếu bên trong
không phải Word hay Excel. Tệp mất trên đĩa (người vận hành lỡ xoá) thì bấm Tải
về báo rõ, không sập trang.

---

## A11. Công việc

| Việc | Cách làm |
|---|---|
| Giao việc | **Thêm việc**: tiêu đề, người làm, ưu tiên, hạn. Staff chỉ tự giao cho mình; Leader giao trong team; Manager giao cả bộ phận; Admin giao ai cũng được |
| Đổi trạng thái | Nút ngay trên dòng: Mới → Đang làm → Xong (hoặc Huỷ); việc nhỏ bấm **Xong** ngay từ Mới; Huỷ mở lại thành Mới. Người làm, người tạo và Leader trở lên đổi được; đổi xong dòng cập nhật tại chỗ, không tải lại trang; bấm sai bước thì hiện lý do |
| Xem | Tab **Của tôi** (việc mình nhận hoặc tạo) và **Trong phạm vi** (team với Leader, bộ phận với Manager); lọc theo trạng thái, người làm, ưu tiên, **Chỉ việc quá hạn**; sắp **Hạn gần trước** |
| Sửa, gỡ | Người tạo hoặc Leader trở lên sửa (biểu mẫu sai thì lỗi hiện ngay dưới ô, chữ đã gõ còn nguyên; để trống Người làm là giữ nguyên người cũ); người tạo hoặc Manager gỡ, có hỏi lại. Hạn đã qua mà chưa xong thì ngày hạn đỏ |

---

## A12. Văn hoá — ghi nhận, sao, xếp hạng

| Việc | Cách làm |
|---|---|
| Ghi nhận cấp dưới | Chỉ **trưởng nhóm trở lên** có ô ghi nhận (Q75): Leader chọn được nhân viên team mình, Manager cả Leader và nhân viên bộ phận, Admin mọi người; nhân viên xem danh sách ghi nhận và bảng xếp hạng. Chọn người, chọn một giá trị (Tận tâm, Chính trực, Hợp tác, Sáng tạo, Trách nhiệm), viết lời nhắn, **Gửi ghi nhận**. Không tự ghi nhận mình. Ghi nhận **không sửa, không xoá** được — nghĩ kỹ rồi gửi |
| Sao | Mỗi ghi nhận cho người nhận **một sao**. Ngày 1 hằng tháng, những người ở hạng 1, 2, 3 doanh số tháng trước nhận thêm **5, 3, 1 sao**; bằng tổng và bằng số đơn thì đồng hạng, cùng nhận (Q77). Máy tắt đúng ngày 1 thì lần bật kế tiếp tự thưởng bù |
| Xếp hạng doanh số | Tính từ **Đơn hàng** tháng này theo người bán (ngày lên đơn trên hệ thống), quy về VND theo tỉ giá cố định trong cấu hình; mọi người bán kể cả quản lý đều có hạng (Q76); người bán đã khoá tài khoản không chiếm hạng; cả công ty xem hạng, số đơn, tổng — không thấy chi tiết đơn. Đổi tỉ giá giữa tháng thì hạng đổi theo; nhật ký thưởng ghi tỉ giá đã dùng |
| Trang thành viên | Bấm tên bất kỳ: tổng sao, sao tháng này, sao theo tháng, ghi nhận nhận được |

---

## A13. Tài nguyên

Kho tài nguyên dùng chung — BM, Via, Page, Tài khoản QC, SIM… — ai cũng xem
được cả danh sách.

| Việc | Ai | Cách làm |
|---|---|---|
| Xem | Mọi người | Lọc theo mục (cột phải), trạng thái (Trống, Đang dùng, Khoá, Hỏng), người giữ; tìm theo tên; **Xoá lọc** giữ mục đang chọn |
| Thêm, sửa, gỡ | Manager trở lên | **Thêm tài nguyên**, nút **Sửa** và **Gỡ** trên dòng. Mỗi lần lưu có nhật ký ghi trường nào đổi |
| Thêm mục | Manager trở lên | Ô **Thêm mục** ở cột phải |

**Không ghi mật khẩu, mã OTP, 2FA, token vào tên, ghi chú hay liên kết** — hệ
thống từ chối lưu khi thấy các từ này (OTP, 2FA, PIN, mk chỉ bị chặn khi kèm số).
Liên kết chỉ nhận `http://` hoặc `https://`. Người giữ đã bị khoá tài khoản vẫn
hiện trong ô chọn khi sửa, để bấm Lưu không làm mất người giữ. Kho chỉ trả lời "có gì, ai giữ, tình trạng ra sao"; mật
khẩu để ở kho mật khẩu riêng.

---

# PHẦN B — SỔ TAY VẬN HÀNH

> Phần này dành cho người chịu trách nhiệm giữ cho hệ thống chạy được.
> Viết với giả định người đọc chưa từng làm việc với hệ thống này.

## B1. Người chịu trách nhiệm

| Vai trò | Tên | Việc | Tần suất |
|---|---|---|---|
| Vận hành kỹ thuật | (điền tên) | Kiểm hệ thống còn chạy, kiểm bản sao lưu | Hằng ngày |
| Vận hành kỹ thuật | (điền tên) | Thử phục hồi trên môi trường thử | Hằng quý |
| Quản trị người dùng | (điền tên) | Tạo tài khoản, đặt lại mật khẩu, phân quyền | Khi cần |

**Phải điền tên người cụ thể.** Ghi tên phòng ban thay cho tên người nghĩa là
không ai chịu trách nhiệm.

---

## B2. Hệ thống gồm những gì

| Thành phần | Vai trò | Mất thì sao |
|---|---|---|
| Thư mục cài đặt | Chứa mã nguồn và công cụ | Tải lại từ kho mã nguồn |
| Vùng lưu cơ sở dữ liệu | Toàn bộ dữ liệu nghiệp vụ | **Mất vĩnh viễn nếu không có bản sao lưu** |
| Thư mục tệp đính kèm | Ảnh, tệp người dùng tải lên | Mất các tệp đó |
| Tệp cấu hình | Mật khẩu cơ sở dữ liệu, khoá bí mật | Hệ thống không khởi động được |

**Ba thứ tuyệt đối không được xoá:** vùng lưu cơ sở dữ liệu, thư mục tệp đính kèm,
và tệp cấu hình.

---

## B3. Việc hằng ngày

1. Mở hệ thống, đăng nhập `quantri`, kiểm màn hình chính hiện đủ số liệu
2. Nhìn ô **Sao lưu đêm qua** trên Tổng quan: chip xanh "Thành công" kèm giờ
   là được; chip đỏ thì mở Tác vụ nền đọc lý do, chạy lại `scripts/backup.sh`
   và xem mục B7. Người vận hành cũng nhận thư khi sao lưu hỏng (biến
   `OPERATOR_EMAILS`)
3. Nhìn ô **Tác vụ nền**: có tác vụ "kẹt" nghĩa là worker không chạy — xem B5
4. Nếu hệ thống không mở được, xem mục B5
5. Bảng tin: hồ sơ có người sinh nhật hôm nay mà sau 06:00 không thấy thiệp
   thì `beat` không chạy — xem B5. Máy để bàn tắt đêm thì `beat` không có lúc
   06:00 (thiệp) hay 01:00 ngày 1 (thưởng sao) để chạy: lần bật kế tiếp
   `entrypoint.sh` tự đăng bù thiệp (tối đa 14 ngày) và thưởng sao tháng trước,
   nên chỉ cần bật máy. Tác vụ hỏng (thiếu tỉ giá) thì người vận hành nhận thư
   và Nhật ký có một dòng

Mất khoảng hai phút. **Đừng bỏ qua bước kiểm bản sao lưu** — sao lưu hỏng thường
im lặng, chỉ phát hiện khi cần dùng thì đã muộn.

---

## B4. Việc hằng quý

Thử phục hồi từ bản sao lưu. Đây là việc quan trọng nhất trong sổ tay này.

1. Chuẩn bị một bản cài riêng, tách khỏi bản đang dùng thật
2. Lấy bản sao lưu gần nhất
3. Chạy phục hồi trên bản cài riêng đó
4. Đăng nhập, kiểm số liệu có khớp với bản thật không
5. Ghi lại kết quả và ngày thực hiện

**Bản sao lưu chưa từng được phục hồi thử thì chưa phải bản sao lưu.**
Nhiều hệ thống chỉ phát hiện sao lưu hỏng vào đúng lúc cần dùng.

---

## B5. Khi hệ thống không mở được

Làm theo thứ tự, dừng lại khi hệ thống chạy lại được.

| Bước | Kiểm tra | Nếu sai thì làm gì |
|---|---|---|
| 1 | Máy chủ đã bật chưa | Bật máy, chờ hai phút |
| 2 | Các thành phần nền đã khởi động xong chưa | Chờ tới khi báo sẵn sàng |
| 3 | Địa chỉ truy cập có đúng không | Xem lại địa chỉ được cấp |
| 4 | Thử lại sau một phút | |
| 5 | Vẫn không được | Khởi động lại máy chủ, làm lại từ bước 1 |
| 6 | Vẫn không được | Xem nhật ký hệ thống, gửi cho người phụ trách kỹ thuật |

**Không tự ý làm ba việc sau:** xoá thư mục cài đặt, cài đè bản mới lên bản đang
chạy, hoặc xoá vùng lưu cơ sở dữ liệu. Cả ba đều có thể làm mất dữ liệu vĩnh viễn.

---

## B6. Cập nhật hệ thống

**Máy cá nhân — một lệnh:** nháy đúp `KN JSC.bat` ở thư mục gốc (Windows), hoặc
chạy `scripts\cap-nhat-local.bat` / `./scripts/cap-nhat-local.sh`. Script tự mở
Docker Desktop và chờ nó sẵn sàng, kéo mã mới, dựng lại container, migrate, tạo
bảng vận đơn, nạp dữ liệu mẫu (kể cả đặt lại đúng mật khẩu in ra cho tài khoản mẫu
có sẵn) rồi mở trình duyệt. Muốn xem một nhánh khác thì truyền tên nhánh:
`scripts\cap-nhat-local.bat <tên nhánh>`. Dừng ở bước nào thì in rõ bước đó.

Máy chủ thật thì làm theo thứ tự dưới đây:

1. **Tạo bản sao lưu mới trước khi làm gì**
2. Chép bản sao lưu đó ra một nơi khác
3. Lấy mã nguồn mới
4. Chỉ thay phần mã nguồn, giữ nguyên cơ sở dữ liệu, thư mục tệp và tệp cấu hình
5. Khởi động lại
6. Kiểm: đăng nhập, xem dữ liệu, thử phân quyền
7. Nếu có gì sai, phục hồi từ bản sao lưu ở bước 1

---

## B7. Khi có sự cố

| Tình huống | Việc đầu tiên | Việc tiếp theo |
|---|---|---|
| Hệ thống chạy chậm bất thường | Kiểm dung lượng đĩa còn trống | Dọn bản sao lưu cũ |
| Đầy đĩa | Kiểm thư mục sao lưu và tệp tạm | Xoá bản cũ, giữ 30 bản gần nhất |
| Người dùng không đăng nhập được | Kiểm tài khoản có bị khoá tạm không | Chờ mười lăm phút hoặc mở khoá |
| Nghi ngờ dữ liệu bị sửa sai | Xem nhật ký hoạt động | Phục hồi từ bản sao lưu nếu cần |
| Nghi ngờ lộ thông tin đăng nhập | Đổi mật khẩu ngay | Điều tra sau, đừng điều tra trước |

---

## B8. Sao lưu

| Mục | Quy định | Cách làm |
|---|---|---|
| Tần suất | Mỗi ngày một lần, tự động | Service `beat` chạy lúc **02:00**, ra tệp `storage/backups/knjsc-<ngày>-<giờ>.dump` |
| Thời gian giữ | 30 ngày, tối đa 30 bản gần nhất | Tự xoá bản cũ hơn bản thứ 30 |
| Nơi lưu | Ít nhất một bản ở nơi khác máy chủ chính | Đặt biến `BACKUP_DIR` trỏ sang ổ khác, hoặc chép thư mục `storage/backups/` đi mỗi ngày |
| Mã hoá | Bản sao lưu mã hoá trước khi rời khỏi máy chủ | Chưa có trong hệ thống — mã hoá khi chép ra ngoài (Giai đoạn 8) |
| Thử phục hồi | Mỗi quý một lần | Xem dưới |
| Tệp tài liệu | `storage/tai-lieu/` **không** nằm trong `pg_dump` | Chép thư mục đó đi cùng bản sao lưu; phục hồi thì chép lại — backlog K30 |
| Bản sao lưu cũ hơn mã | Bản dựng trước khi có nhóm Nội bộ vẫn phục hồi được | Lần bật kế tiếp `entrypoint.sh` chạy `migrate` tạo bảng còn thiếu; tài liệu, bài, việc, ghi nhận sau mốc sao lưu thì mất theo bản |

**Sao lưu ngay bây giờ:** `scripts/backup.sh` (Windows: chạy lệnh trong tệp
đó bằng PowerShell). Trước mỗi lần cập nhật hệ thống nên chạy một lần.

**Phục hồi — đè lên dữ liệu hiện tại:**

```
scripts/restore.sh                          # chỉ liệt kê các bản, không làm gì
scripts/restore.sh --toi-chac-chan          # phục hồi bản mới nhất
scripts/restore.sh knjsc-20260903-020000.dump --toi-chac-chan
```

Script dừng worker, beat và Bảng tính trong lúc phục hồi rồi bật lại. Không
có cờ `--toi-chac-chan` thì không bao giờ ghi gì. Mỗi lần phục hồi ghi một
dòng nhật ký.

**Bản sao lưu chưa từng được phục hồi thử thì chưa được tính là bản sao lưu.**
Mỗi quý: sao lưu, sửa một ô, phục hồi, kiểm ô đó trở về giá trị cũ.

---

## B9. Bàn giao cho người khác

Khi người vận hành nghỉ hoặc chuyển việc, bàn giao đủ những thứ sau:

- Địa chỉ truy cập hệ thống và tài khoản quản trị
- Vị trí thư mục cài đặt trên máy chủ
- Vị trí tệp cấu hình và nơi lưu mật khẩu cơ sở dữ liệu
- Nơi lưu bản sao lưu ngoài máy chủ và cách truy cập
- Tài liệu này và các tài liệu trong thư mục `docs/`
- Danh sách việc định kỳ và ngày thực hiện gần nhất

**Cách kiểm bàn giao đã đủ chưa:** người tiếp nhận tự làm được một lần phục hồi
trên môi trường thử mà không cần hỏi ai. Làm được nghĩa là bàn giao đủ.

---

## B10. Thư mục `storage/` và các dịch vụ

`storage/` nằm cạnh kho mã, **không** đưa lên git, là thứ duy nhất ngoài cơ sở
dữ liệu cần giữ:

| Thư mục | Chứa gì | Dọn |
|---|---|---|
| `storage/backups/` | Bản sao lưu `pg_dump` | Tự giữ 30 bản |
| `storage/exports/` | Tệp Excel xuất ở nền | Tự xoá sau 24 giờ (03:00) |
| `storage/uploads/imports/` | Tệp đang chờ nhập | Xoá sau khi nhập xong, hoặc sau 24 giờ nếu bỏ dở |
| `storage/e2e/` | Ảnh chụp màn hình của bài kiểm trình duyệt | Xoá tay khi muốn |
| `storage/tai-lieu/` | Tệp ở mục Tài liệu (FR-9.2) | **Không dọn**, giữ vĩnh viễn; chép cùng bản sao lưu — K30. Tài liệu đã gỡ thì tệp vẫn nằm đây |
| `storage/celerybeat-schedule` | Lịch của `beat`: mốc chạy gần nhất của từng tác vụ | Không dọn; lỡ xoá thì `beat` chạy lại như mới, không mất gì |

Container chạy bằng uid 1000; trên máy Linux thư mục phải ghi được bởi uid đó
(backlog K21). Lúc khởi động, `entrypoint.sh` in cảnh báo nếu không ghi được.

Sáu dịch vụ trong `docker-compose.yml`:

| Dịch vụ | Việc | Cổng |
|---|---|---|
| `db` | PostgreSQL 16 | 5433 (ra ngoài) |
| `redis` | Hàng đợi | — |
| `web` | Hệ thống chính | **8020** |
| `bangtinh` | Bảng tính vận đơn — cùng mã, cùng cơ sở dữ liệu, cấu hình `knjsc.settings.bangtinh` | **8021** |
| `worker` | Chạy nhập tệp, xuất tệp, sao lưu | — |
| `beat` | Bấm giờ: sao lưu 02:00, dọn tệp 03:00, canh tác vụ kẹt mỗi 15 phút, thiệp sinh nhật 06:00, thưởng sao xếp hạng ngày 1 lúc 01:00; lịch ghi ở `storage/celerybeat-schedule` | — |

Không có `worker` thì nhập tệp treo ở "Chờ xử lý" và sau 15 phút bị đánh dấu
kẹt; không có `beat` thì không có gì tự chạy đêm.

**Tỉ giá cho bảng xếp hạng** đặt bằng biến môi trường `EXCHANGE_RATES_VND`,
đúng dạng `USD=25400,CAD=18500,PHP=440` — số nguyên VND, không dấu chấm hay
phẩy trong số. Sai định dạng thì cả bốn dịch vụ không lên và báo tên biến, để
không có số sai lặng lẽ vào sổ sao.


### Bảng master Vận đơn mới — ADR-021

Bảng mới cuộn liên tục; bấm ô để đọc chữ bị cắt, F2/bấm đúp sửa theo quyền.
Ctrl+A chọn toàn bộ kết quả lọc; Ctrl+C/V, Delete nội dung, Ctrl+Z/Y giới hạn
2.000 ô/lượt. Enter/Tab hoặc đóng khung nhập bằng X giữ nội dung trong bản
đang làm; ô nhiều dòng dùng Ctrl+Enter để kết thúc nhập, Escape hủy phần đang gõ.
**… → Lưu dữ liệu** hoặc **Ctrl+S** mới ghi database, tối đa 2.000 ô chưa lưu.
Mở/đóng chức năng và đổi bộ lọc giữ nháp; Lưu ghi cả ô đã sửa ngoài bộ lọc hiện tại.
**Tải lại/rời bảng/đóng tab mất phần chưa lưu, không có hộp hỏi xác nhận.**
Khi báo Chưa lưu/Xung đột, phần đang làm còn trên màn hình; chưa coi là đã lưu.
Menu … có Nhập/Xuất, Phân công và Chia sẻ link (chưa triển khai). Các hộp có X
ở đầu hộp, luôn nhìn thấy khi cuộn. Xuất Excel/lọc/thống kê dùng dữ liệu đã lưu.
Phân công/chi tiết dùng hộp riêng. Thống kê chuyển sang mục sidebar riêng,
nhận cùng bộ lọc, không tự cập nhật sau mỗi lần sửa ô.

Bản cập nhật cần migration `crm.0001_initial` (chỉ thêm biên nhận lưu): dùng
quy trình cập nhật/migration chuẩn. Không hạ migration trên DB đang làm việc
để kiểm; phép thử đảo chiều nằm trong `crm/tests/test_master_grid.py`.

Kéo mép dưới **số hàng** để chỉnh chiều cao 28–400px. Hàng cao sẽ xuống dòng,
phần chữ còn thiếu vẫn mở bằng bấm ô. Thả chuột ghi nhớ riêng theo tài khoản,
bảng và ID vận đơn trên trình duyệt/máy hiện tại; không đồng bộ sang máy khác.
Escape trong lúc kéo hủy lượt đó. Focus tay nắm: ↑/↓ đổi 4px, Home về 28px.
Kéo hàng giữ phần đang nhập vào bản đang làm, không yêu cầu lưu trước. Chỉnh chiều cao không đổi dữ liệu,
không vào Undo/Redo nội dung và không thay chiều cao trong file Excel xuất.

## Bổ sung thao tác Vận đơn mới — 10.09.2026

Quy định này thay phần lưu thủ công trước đó. Kết thúc sửa sẽ tự lưu nền;
Ctrl+S/Lưu dữ liệu gửi ngay. Chờ trạng thái Đã lưu trước khi đóng trang.
Đổi lọc/popup giữ nháp; cảnh báo rời trang chỉ xuất hiện khi còn chưa lưu.
Nhập file, phân công và chi tiết sản phẩm vẫn có nút gửi riêng.

- Chế độ Xem: chọn/đọc, F2 hoặc bấm đúp để sửa. Chế độ Chỉnh sửa: bấm/chuyển
  tới ô được phép sửa để nhập ngay. Tab chuyển ô; Enter xuống hàng cho ô
  một dòng. Ô nhiều dòng Enter xuống dòng, Ctrl+Enter kết thúc.
- Bấm số hàng để chọn hàng. Dòng đầu mang số 1. Đơn mới ở cuối theo mặc định.
- Định dạng có cỡ chữ/màu chữ/màu nền, dùng cùng autosave và Undo/Redo.
- Nếu một dòng mất quyền giữa lượt sửa, hệ thống gỡ dòng đó và giữ nháp
  còn quyền. Kiểm tra thông báo rồi bấm **Thử lại** để gửi phần còn hợp lệ;
  hệ thống không tự ghi một phần của lượt vừa bị từ chối.
- … → Lịch sử xem thay đổi qua lưới mới của dòng đang chọn. … → Xung đột
  đối chiếu giá trị và chọn server hoặc gửi lại; có xung đột thì cả lượt chưa ghi.
- Admin lên đơn tại CRM phải chọn Sale đứng đơn đang hoạt động.

**Cập nhật 11.09.2026:** nhập trực tiếp trong ô, không còn khung nhập nổi
che hàng dưới hoặc kéo giãn riêng khung nhập. Escape hủy phần đang gõ;
Tab/Enter kết thúc và tự lưu như trên. Muốn đọc dài, dùng chế độ Xem hoặc
kéo chiều cao hàng. Dán bảng nhiều ô từ trong ô nhập vẫn dùng giới hạn
2.000 ô và kiểm lỗi toàn lượt. Các ô tổng/chi tiết/phân công giữ cơ chế riêng.

Phạm vi và kết quả kiểm chứng: [báo cáo chín hạng mục](kiem-chung-master-nine.md).

## Nạp 10.000 vận đơn mẫu — 11.09.2026

Lệnh này chỉ dùng cho môi trường phát triển có `DEBUG=1`. Lệnh chỉ tác động nhóm
mã `MAU-20260910-*` trong `van_don_moi`; không tạo khách hàng, đơn hoặc dòng sản
phẩm bên ERP và không sửa vận đơn ngoài tiền tố mẫu.

Sao lưu database trước, rồi từ container `web` chạy xem trước:

```powershell
python manage.py nap_du_lieu_van_don_moi --tong-so 10000 --seed 20260911 --dry-run
```

Kết quả chuẩn trên database có 500 dòng mẫu cũ là 500 dòng cập nhật và 9.500 dòng
tạo mới. Khi đã đối chiếu đúng, bỏ `--dry-run` để chạy thật. Toàn bộ lượt chạy nằm
trong một giao dịch: thiếu bảng, sản phẩm hoặc nhân sự hợp lệ, hay lỗi giữa lượt,
thì không ghi một phần. Chạy lại cùng tổng và seed không tạo trùng và không đổi ID
các dòng/chi tiết/phân công đã đúng.

Sau khi chạy, kiểm tra tổng 10.000 mã và số điện thoại duy nhất, ghi chú không còn
`???`, mọi dòng có bang/thành phố/zipcode/địa chỉ, tổng số lượng/giá/đã thu khớp
`WaybillItem`, và Sale/CSKH/Vận đơn thuộc đúng bộ phận đang hoạt động.

## Bàn điều hành KN CRM — ADR-022

Mở **Bàn điều hành** trên sidebar KN CRM hoặc
`http://localhost:8021/thong-ke/`. Không chọn nguồn là góc nhìn tổng hợp; chọn
một bảng để xem chuyên sâu. Khoảng ngày mặc định từ đầu tháng đến hôm nay. Ba ô
Marketing/Sale/Vận đơn ở góc tổng hợp chỉ đổi nguồn đang dùng, không cộng nhiều
bảng cùng loại. Tên nguồn luôn hiện cạnh số liệu.

Nhận định trên màn hình được sinh theo quy tắc và chỉ dẫn tới dữ liệu cần xem;
đây chưa phải AI Agent, không tự gửi thông báo, tạo việc hay sửa bảng. Chênh lệch
Sale–Vận đơn là tổng cần đối chiếu, không phải kết luận thất lạc. Tiền không được
quy đổi hoặc cộng khác loại. Khi một phần báo tạm chưa khả dụng, mở bảng nguồn để
kiểm nhãn cột/dữ liệu; các phần còn lại vẫn dùng được.

Biến môi trường tùy chọn:

```env
EXECUTIVE_OWNER_USERNAMES=quan_tri,ceo
```

Biến này chỉ đổi tiêu đề giao diện cho username đang hoạt động có cấp Admin,
không cấp quyền xem dữ liệu. Để trống là hành vi mặc định. Sau khi đổi biến, khởi
động lại dịch vụ `bangtinh`; kiểm từng tài khoản vẫn chỉ thấy bảng/dòng theo cấp
bậc hiện hành. KN ERP giữ Báo cáo tổng hợp và xuất Excel; nút **Mở Bàn điều hành
KN CRM** chỉ mở nơi phân tích, không thay dữ liệu báo cáo.

Snapshot chuyên sâu Vận đơn dùng tối đa 64MiB `work_mem` cục bộ cho mỗi request
aggregate và tự hoàn nguyên sau transaction; không cần sửa `postgresql.conf`.
Khi kiểm tải đồng thời trên máy chủ thật, theo dõi RAM theo số request thống kê
chạy song song thay vì nhân con số này với toàn bộ tài khoản đã đăng nhập.
