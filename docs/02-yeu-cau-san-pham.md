# Yêu cầu sản phẩm

| Mục | Nội dung |
|---|---|
| Dự án | Kim Ngân JSC — Hệ thống vận hành nội bộ |
| Giai đoạn | Phase 1 |
| Phiên bản tài liệu | 0.1 — bản nháp |
| Ngày | (điền ngày) |
| Người viết | (điền tên) |
| Người duyệt | (điền tên) |
| Tài liệu liên quan | `01-tong-quan-san-pham.md` · `03-thiet-ke-ky-thuat.md` · `04-tieu-chi-nghiem-thu.md` |

> Tài liệu này quy định hệ thống **phải làm được gì**, viết dưới dạng kiểm chứng được.
> Mỗi yêu cầu có mã riêng và có ít nhất một bài kiểm thử tương ứng ở `04-tieu-chi-nghiem-thu.md`.
>
> Từ **phải** mang nghĩa bắt buộc. Từ **nên** mang nghĩa khuyến nghị, không bắt buộc.

---

## Cách đọc mã yêu cầu

```
FR-x.y     Yêu cầu chức năng    — hệ thống làm được gì
NFR-x      Yêu cầu phi chức năng — hệ thống phải đạt mức nào
BR-x       Quy tắc nghiệp vụ     — ràng buộc luôn đúng
```

---

## 1. Tài khoản và phiên đăng nhập

| Mã | Yêu cầu |
|---|---|
| FR-1.1 | Hệ thống phải yêu cầu đăng nhập trước khi truy cập bất kỳ dữ liệu nào |
| FR-1.2 | Hệ thống phải khoá tạm tài khoản trong 15 phút sau 5 lần đăng nhập sai liên tiếp |
| FR-1.3 | Hệ thống phải đóng phiên khi người dùng không thao tác quá 60 phút |
| FR-1.4 | Hệ thống phải buộc người dùng đổi mật khẩu trong lần đăng nhập đầu tiên; form tạo tài khoản không hỏi email và ngày sinh (24.09.2026 — đăng nhập bằng mã nhân sự, ngày sinh bổ sung ở màn Sửa hồ sơ) |
| FR-1.5 | Khi quản trị viên khoá tài khoản hoặc thay đổi quyền, phiên đang mở của người đó phải mất hiệu lực ngay |
| FR-1.6 | ~~Sau khi đăng nhập, hệ thống phải đưa người dùng tới màn hình phù hợp với bộ phận và cấp bậc của họ~~ **Bỏ theo Q34** — mọi người vào trang tổng quan chung, phân quyền đã ẩn tính năng ngoài phận sự |
| FR-1.7 | Mỗi nhân sự có **mã nhân sự** theo quy ước công ty (TÊN + chữ đầu họ + chữ đầu tên đệm, viết hoa không dấu; trùng thì thêm số từ 2), cố định sau khi gán; tài khoản mới có tên đăng nhập là mã, đăng nhập không phân biệt hoa/thường; mọi chỗ định danh hiện mã trước, tên sau — ADR-037 |

---

## 2. Cơ cấu tổ chức

| Mã | Yêu cầu |
|---|---|
| FR-2.1 | Hệ thống phải cho phép tạo và quản lý bộ phận |
| FR-2.2 | Hệ thống phải cho phép tạo nhiều team trong một bộ phận |
| FR-2.3 | Hệ thống phải cho phép gán mỗi người dùng vào một bộ phận, một team và một cấp bậc |
| FR-2.4 | Hệ thống phải cho phép thêm team mới mà không cần thay đổi mã nguồn |

---

## 3. Phân quyền

| Mã | Yêu cầu |
|---|---|
| FR-3.1 | Người dùng cấp Staff chỉ được xem dữ liệu do chính mình tạo |
| FR-3.2 | Người dùng cấp Leader được xem dữ liệu của toàn bộ team mình phụ trách |
| FR-3.3 | Người dùng cấp Manager được xem dữ liệu của toàn bộ bộ phận |
| FR-3.4 | Người dùng không được xem dữ liệu của bộ phận khác trừ khi được cấp quyền riêng |
| FR-3.5 | Khi người dùng truy cập dữ liệu ngoài phạm vi quyền, hệ thống phải trả về lỗi từ chối, không trả về danh sách rỗng |
| FR-3.6 | Việc kiểm tra quyền phải thực hiện ở phía máy chủ, không chỉ ẩn chức năng trên giao diện |

---

## 4. Báo cáo hằng ngày

| Mã | Yêu cầu |
|---|---|
| FR-4.1 | Mỗi bộ phận phải có biểu mẫu báo cáo riêng |
| FR-4.2 | Hệ thống phải ghi nhận thời điểm nộp của mỗi báo cáo; một người nộp cùng biểu mẫu **nhiều lần trong ngày** được, mỗi lần là một bản riêng (ADR-038 thay khoá một bản/ngày) |
| FR-4.3 | Người dùng phải xem lại được các báo cáo cũ do chính mình nộp |
| FR-4.4 | Staff không sửa báo cáo đã nộp; Leader trong team, Manager trong bộ phận, Admin toàn hệ thống và **Kế toán mọi bộ phận** (ADR-038) sửa nội dung có lịch sử và kiểm phiên bản. Giữ ngày/danh tính/thời điểm nộp gốc — quyết định thay thế 16/09/2026, ADR-032 |
| FR-4.5 | Leader và Manager phải xem được báo cáo của người thuộc phạm vi quản lý; Kế toán xem được báo cáo của mọi bộ phận (ADR-038) |
| FR-4.6 | Trường danh tính người điền (nhãn Người bán) trên biểu mẫu và báo cáo hằng ngày phải do hệ thống tự ghi **mã nhân sự** của tài khoản đang đăng nhập (ADR-037); người dùng không phải điền và không đổi được |
| FR-4.7 | Bỏ báo cáo đã nộp: người nộp, Leader trong team, Manager trong bộ phận, Admin; Kế toán không. Bỏ là xoá mềm cả dòng số liệu (BR-4) nên số rời khỏi Báo cáo tổng hợp. Manager bộ phận và Admin khôi phục được từ trang "Đã bỏ" — ADR-041, thay câu khoá quyền của ADR-032 |
| FR-4.8 | Form nộp báo cáo có **dropdown Team** gồm các team đang hoạt động của bộ phận sở hữu biểu mẫu, chọn sẵn team trong hồ sơ; team đã chọn ghi vào dòng dữ liệu và báo cáo nên cột Team của báo cáo và phạm vi Leader đi theo lựa chọn đó (ADR-043) |
| FR-4.9 | Trên form báo cáo Sale và Marketing, **Số Mess, CPQC, Số đơn, Doanh số là bắt buộc** (Sale không có CPQC); trình duyệt chặn sớm bằng `required`, máy chủ vẫn kiểm lại; "0" là giá trị hợp lệ (ADR-043) |
| FR-4.10 | Form báo cáo Marketing **không còn ô Hóa đơn**; cột và hai chỉ tiêu Hóa đơn ở báo cáo giữ cho dữ liệu cũ (ADR-043) |
| FR-4.11 | Form nộp báo cáo trải hết chiều rộng: hàng điều khiển Biểu mẫu · Team · Ngày, lưới ô nhập **ngang, ô nhỏ**, cột tính sẵn chỉ nhắc công thức dạng chip (ADR-043, theo hướng Solarpunk ADR-028) |

---

## 5. Báo cáo tổng hợp

| Mã | Yêu cầu |
|---|---|
| FR-5.1 | Hệ thống phải thống kê số liệu theo bốn cách nhóm: tổng hợp, theo nhân viên, theo sản phẩm, theo thị trường |
| FR-5.2 | Hệ thống phải cho phép lọc theo khoảng thời gian |
| FR-5.3 | Hệ thống phải cho phép lọc theo sản phẩm |
| FR-5.4 | Báo cáo phải hiển thị dòng tổng cộng |
| FR-5.5 | Báo cáo phải chỉ hiển thị dữ liệu trong phạm vi quyền của người xem |
| FR-5.6 | Hệ thống phải cho phép xuất báo cáo ra tệp Excel |
| FR-5.7 | **Tiền quy về ₫ trước khi cộng** (ADR-042): mọi cột tiền nhân tỉ giá cố định theo loại tiền của từng dòng ngay trong truy vấn rồi mới cộng; dòng thiếu tỉ giá không vào tổng và được đếm trong cảnh báo; không còn để trống chỉ tiêu khi lẫn loại tiền |
| FR-5.8 | Báo cáo Marketing có ba cột **đối soát từ vận đơn**: Số đơn (TT), DS Chốt (TT), Tỉ lệ chốt (TT) — theo marketer phụ trách và ngày lên đơn; Tỉ lệ chốt hiện %; nhãn cột theo ảnh mẫu (DS Chốt, CPQC/DS Chốt, Hóa đơn/DS Chốt (TT)) (ADR-042) |
| FR-5.9 | Cách xem Tổng hợp có **bố cục khối như ảnh mẫu**: khối toàn kỳ theo nhân sự đứng đầu (STT · Team · Nhân sự · Leader, TỔNG CỘNG ngay dưới tiêu đề), rồi mỗi ngày một bảng riêng có TỔNG CỘNG và STT đếm lại; nút **Gộp / Không gộp** (Gộp = mỗi ngày một dòng); Excel hai sheet cùng khối (ADR-042) |
| FR-5.10 | **Ngưỡng màu ba bậc** xanh / vàng / đỏ theo mốc tuyệt đối từng chỉ tiêu, do quản lý của bộ phận sở hữu nguồn đặt ngay trên màn hình báo cáo; chưa đặt thì tô tương đối so với dòng Tổng; không có số mặc định (ADR-042) |
| FR-5.11 | Bộ lọc Sản phẩm **tick nhiều mục** (có ô tìm nhanh, Chọn tất cả), Chọn nhanh có "Tuần này"; danh sách sản phẩm chỉ gồm sản phẩm có thật trong phạm vi quyền (ADR-042) |
| FR-5.12 | Mọi màn hình báo cáo giữ ngân sách không quá 10 truy vấn (Q2); liên kết phân trang và chip bộ lọc phản ánh đúng trạng thái đang áp (ADR-042) |

---

## 6. Lên đơn

| Mã | Yêu cầu |
|---|---|
| FR-6.1 | Hệ thống phải cho phép nhập đơn hàng với thông tin khách hàng, danh sách sản phẩm, giá bán và phương thức thanh toán |
| FR-6.2 | Một đơn hàng phải chứa được nhiều sản phẩm, không giới hạn số lượng dòng |
| FR-6.3 | Sau khi lưu đơn ở trang Lên đơn riêng của ERP hoặc KN CRM, tự ghi một dòng và bản sao chi tiết vào bảng vận đơn duy nhất Vận đơn mới `van_don` (ADR-036); bảng không nhúng form Lên đơn. Bảng `van_don` đổi tên Vận đơn cũ, không chuyển dữ liệu lịch sử — ADR-018, ADR-019 |
| FR-6.4 | Hệ thống phải lưu mã liên kết giữa đơn hàng và dòng tương ứng trên bảng vận đơn |
| FR-6.5 | Người tạo đơn phải xem lại được các đơn cũ do chính mình tạo |
| FR-6.6 | Người tạo đơn không được sửa đơn đã lưu |
| FR-6.7 | Hệ thống phải nhận diện được khách hàng đã mua trước đó, dựa trên số điện thoại |
| FR-6.8 | Người dùng cấp Manager phải thêm được sản phẩm vào danh mục ngay tại ô chọn sản phẩm; sản phẩm mới phải có ngay cột số lượng trên bảng vận đơn |

---

## 7. Bảng dữ liệu

| Mã | Yêu cầu |
|---|---|
| FR-7.1 | Hệ thống phải hiển thị dữ liệu dạng bảng, có phân trang |
| FR-7.2 | Hệ thống phải cho phép lọc theo từng cột |
| FR-7.3 | Hệ thống phải cho phép sắp xếp theo từng cột |
| FR-7.4 | Bảng dữ liệu ở KN ERP **chỉ để xem** với mọi bảng và mọi cấp bậc: không có ô sửa tại chỗ, không có đường sửa ô; sửa số liệu là việc của KN CRM (FR-7.13) — ADR-014, thay cho yêu cầu cũ "sửa trực tiếp trên bảng nếu có quyền" |
| FR-7.5 | Hệ thống phải cho phép nhập dữ liệu từ tệp Excel |
| FR-7.6 | Hệ thống phải cho phép xuất dữ liệu ra tệp Excel |
| FR-7.7 | Tệp xuất ra phải nhập lại được vào hệ thống mà không phát sinh lỗi |
| FR-7.8 | Hệ thống phải hỗ trợ công thức tính toán trên bảng — *phạm vi cụ thể xem mục 16*. Đã chốt: cột tính sẵn trên Bảng dữ liệu (ADR-006) và **Bảng tính vận đơn** là lưới làm việc theo tệp thật, không có công thức tự do (ADR-009); nhìn và thao tác theo bảng tính KN Demo, công thức ở thanh công thức chờ cách thứ ba (ADR-011) |
| FR-7.9 | Bảng tính phải thao tác được như bảng tính quen thuộc: kéo chuột chọn vùng, cắt/chép/dán (kể cả dán từ Excel), tay kéo điền, xoá nội dung, hoàn tác và làm lại — mỗi ô vẫn là bản ghi thật có phạm vi quyền, một gói ô lưu một giao dịch được cả hoặc không gì (ADR-011) |
| FR-7.10 | Bảng tính phải có menu chuột phải: chèn hàng trống, xoá hàng (xoá mềm, hoàn tác được), chèn và xoá cột ngay trên lưới cho Manager của bộ phận sở hữu bảng, xoá nội dung, xoá định dạng (ADR-011) |
| FR-7.11 | Định dạng ô đủ như bảng tính — nghiêng, gạch chân, gạch ngang, xuống dòng, viền, màu chữ và màu nền từ bảng 40 màu, cỡ chữ, định dạng số — vẫn là sổ đóng lưu trong cơ sở dữ liệu (ADR-010, ADR-011) |
| FR-7.12 | Bảng tính phải nhìn như bảng tính KN Demo (khung, thanh công thức có ô địa chỉ, số dòng, chữ cột, cột trống, chân trang có tab, toàn màn hình), lọc theo giá trị cột như demo, và tự cập nhật khi người khác sửa (ADR-011) |
| FR-7.13 | Bảng tính là app riêng **KN CRM** trong hệ sinh thái (dịch vụ riêng, tên miền riêng, mở tab mới từ KN ERP); trang chủ là cây Bộ phận → Quý → Tháng → bảng tự sinh từ cột Ngày, tháng là góc nhìn lọc sẵn trên một bảng; ai không được xem bảng nào thì không thấy nhánh đó, quyền do Manager cấp theo bảng (ADR-012) |
| FR-7.14 | KN CRM có **khung riêng như một app**: sidebar trái theo Teeze (avatar, tên, cấp bậc; Trang chủ; Bảng tính gập được với mục con là từng bộ phận trong phạm vi; Nhập tệp; Cấp quyền; Tác vụ nền; KN ERP; thu gọn được); trang chủ là **tổng quan theo phạm vi**; mục Bảng tính mở trang thư mục (cây Bộ phận → Quý → Tháng → bảng); bấm bảng mới mở lưới toàn màn hình như Excel, chỉ lưới có nút ← và nó về trang thư mục, không về KN ERP (ADR-015) |
| FR-7.15 | **Leader được như Manager trong bộ phận mình** ở KN CRM: tạo bảng, sửa cột, chèn/bỏ cột, thư mục, nhập tệp, xuất Excel, sửa và xoá dòng của người khác trong phạm vi; cấp quyền cho người khác vẫn chỉ Manager; ba việc tạo bảng, sửa cột kèm cấp quyền, nhập tệp chạy ngay trong KN CRM (ADR-015) |
| FR-7.16 | Bảng dữ liệu của **bảng có nguồn báo cáo Sale/MKT** hiện thành **báo cáo chi tiết theo ngày** dùng chung động cơ với Báo cáo tổng hợp: mỗi lần nộp một dòng, khối toàn kỳ theo nhân sự, mỗi ngày một bảng, Gộp, ngưỡng màu, (TT), bộ lọc Kỳ / Sản phẩm / Thị trường / Team / Nhân sự, 25 dòng một trang, Xuất tệp cùng khối; `?dang=tho` xem từng dòng thô; bảng không có nguồn giữ liệt kê thô (ADR-042) |

---

## 8. Quản lý biểu mẫu và bảng

| Mã | Yêu cầu |
|---|---|
| FR-8.1 | Người dùng cấp Manager phải tạo được biểu mẫu mới mà không cần thay đổi mã nguồn |
| FR-8.2 | Khi tạo biểu mẫu, Manager phải chọn được các trường, thứ tự hiển thị và trường nào bắt buộc |
| FR-8.3 | Manager phải chọn được bảng đích nơi dữ liệu từ biểu mẫu được ghi vào |
| FR-8.4 | Manager phải phân quyền được ai điền biểu mẫu nào và ai xem bảng nào |
| FR-8.5 | Manager phải sửa được biểu mẫu đã tạo mà không làm mất dữ liệu đã nhập |
| FR-8.6 | Hệ thống phải kiểm tra tính tương thích khi nối trường của biểu mẫu với cột của bảng |
| FR-8.7 | Mọi cột kiểu Chọn một phải hiện thành ô chọn từ danh sách ở mọi chỗ nhập (biểu mẫu, báo cáo ngày, Lên đơn; Bảng dữ liệu chỉ xem nên không có ô chọn — FR-7.4); danh sách do Manager quản lý (đặt trong Sửa cột hoặc thêm ngay tại ô chọn), cột mang nhãn Sản phẩm lấy danh sách từ danh mục sản phẩm; giá trị ngoài danh sách bị từ chối |
| FR-8.8 | Manager phải đặt được màu nền cho từng cột và ngưỡng cảnh báo cho cột kiểu số; Bảng dữ liệu tô màu tiêu đề và ô theo cài đặt đó, ô vượt ngưỡng tô đỏ, ô đạt tô xanh lá |
| FR-8.10 | Quản lý bảng ẩn được cột với cả công ty trong hộp "Cột" của lưới: cột biến khỏi lưới KN CRM, tệp Excel xuất ra và Bảng dữ liệu bên KN ERP, dữ liệu ô vẫn giữ và hiện lại được (ADR-039) |
| FR-8.9 | Bảng dữ liệu phải có viền mọi ô và tiêu đề cột có màu nền |

---

## 9. Tài liệu

Thư viện tài liệu dùng chung, chia theo mục — nhóm Nội bộ, ADR-017.

| Mã | Yêu cầu |
|---|---|
| FR-9.1 | Tài liệu phải chia theo mục; mỗi mục thuộc một bộ phận hoặc dùng cho toàn công ty. Manager tạo mục cho bộ phận mình, Admin tạo mục toàn công ty |
| FR-9.2 | Manager trở lên tải lên được tệp PDF, Word, Excel, CSV, ảnh JPG hoặc PNG (giới hạn NFR-11, kiểm nội dung theo NFR-12), hoặc thêm tài liệu dạng liên kết |
| FR-9.3 | Mọi người trong phạm vi của mục xem và tải về được; tải về đi qua đường có kiểm quyền, không có đường tĩnh tới tệp; mỗi lượt tải về hay mở liên kết ghi một dòng nhật ký |
| FR-9.4 | Gỡ tài liệu là xoá mềm (BR-4); người tải, Manager của bộ phận đó hoặc Admin mới gỡ được |
| FR-9.5 | Tệp tài liệu nằm ngoài các thư mục bị dọn tự động sau 24 giờ |

---

## 10. Bảng tin

Bảng tin chung của công ty — ADR-017.

| Mã | Yêu cầu |
|---|---|
| FR-10.1 | Mọi người đăng được bài dạng chữ; ai cũng xem được toàn bộ bài, không phân theo bộ phận |
| FR-10.2 | Mọi người thích và bình luận được; bỏ thích được, thích lại được; bài chỉ tải 20 bình luận mới nhất, cũ hơn tải tiếp |
| FR-10.3 | Manager và Admin ghim bài (đứng đầu trang) và gỡ bài bất kỳ; tác giả gỡ được bài của mình; gỡ là xoá mềm |
| FR-10.4 | Hệ thống tự đăng thiệp chúc mừng sinh nhật theo ngày sinh trong hồ sơ nhân sự, mỗi người mỗi năm một thiệp |
| FR-10.5 | Thanh bên có sinh nhật tháng này, bảng xếp hạng sao, ghi nhận mới nhất và thành viên mới |
| FR-10.6 | Mọi tương tác (đăng, thích, bình luận, ghim, gỡ) đều ghi nhật ký (BR-5) |

---

## 11. Công việc

Quản lý việc trong bộ phận — ADR-015.

| Mã | Yêu cầu |
|---|---|
| FR-11.1 | Tạo việc và giao cho người trong phạm vi của mình; Staff tự giao cho chính mình |
| FR-11.2 | Việc có bốn trạng thái Mới, Đang làm, Xong, Huỷ và chỉ chuyển theo bảng chuyển hợp lệ (việc nhỏ chuyển thẳng Mới → Xong; Huỷ mở lại thành Mới); có ưu tiên và hạn |
| FR-11.3 | Phạm vi xem theo cấp bậc: Staff thấy việc mình nhận hoặc tạo, Leader thấy việc của team, Manager cả bộ phận, Admin tất cả |
| FR-11.4 | Danh sách có tab Của tôi và Trong phạm vi, lọc theo trạng thái, người làm, ưu tiên, chỉ việc quá hạn; sắp theo hạn gần trước; phân trang |
| FR-11.5 | Gỡ việc là xoá mềm; người tạo hoặc Manager trở lên mới gỡ được |

---

## 12. Ghi nhận văn hoá

Ghi nhận đồng nghiệp, sao và bảng xếp hạng doanh số — ADR-017.

| Mã | Yêu cầu |
|---|---|
| FR-12.1 | **Trưởng nhóm trở lên ghi nhận cấp dưới trong phạm vi mình** (Leader: nhân viên team, Manager: cả bộ phận, Admin: mọi người) theo một giá trị văn hoá kèm lời nhắn; nhân viên chỉ xem; không tự ghi nhận mình — Q75 |
| FR-12.2 | Mỗi ghi nhận cho người nhận một sao |
| FR-12.3 | Bảng xếp hạng doanh số tháng này tính từ Đơn hàng theo người bán (ngày lên đơn trên hệ thống), quy về VND bằng tỉ giá cố định trong cấu hình; mọi người bán kể cả quản lý đều tranh hạng (Q76); bằng tổng và bằng số đơn thì đồng hạng (Q77); toàn công ty xem hạng, số đơn và tổng, không thấy chi tiết đơn |
| FR-12.4 | Ngày 1 hằng tháng, những người ở hạng 1, 2, 3 tháng trước nhận 5, 3, 1 sao thưởng, đồng hạng cùng nhận (Q72); chạy lại không nhân đôi; nhật ký thưởng ghi tỉ giá đã dùng |
| FR-12.5 | Tổng sao hiện ở bảng xếp hạng sao và trang thành viên |

---

## 13. Tài nguyên

Danh mục tài nguyên dùng chung — ADR-017, thay quyết định Q2.

| Mã | Yêu cầu |
|---|---|
| FR-13.1 | Tài nguyên chia theo mục (BM, Via, Page, …); Manager trở lên thêm mục |
| FR-13.2 | Mọi người xem được toàn bộ danh sách; lọc theo mục, trạng thái, người giữ; tìm theo tên |
| FR-13.3 | Manager trở lên thêm, sửa, gỡ (xoá mềm) tài nguyên; mỗi thay đổi ghi nhật ký |
| FR-13.4 | Không lưu mật khẩu hay mã bí mật trong ghi chú tài nguyên |

---

## 14. Quy tắc nghiệp vụ

Những ràng buộc phải luôn đúng, không phụ thuộc màn hình hay thao tác.

| Mã | Quy tắc |
|---|---|
| BR-1 | Mỗi người dùng thuộc đúng một bộ phận và một cấp bậc tại một thời điểm |
| BR-2 | Báo cáo đã nộp không xoá cứng và không sửa ngoài luồng sửa có lịch sử (ADR-032, ADR-038); nộp nhiều lần trong ngày là các bản riêng, không đè |
| BR-3 | Đơn hàng đã lưu không được sửa hoặc xoá |
| BR-4 | Xoá dữ liệu là đánh dấu đã xoá, không xoá vĩnh viễn khỏi cơ sở dữ liệu |
| BR-5 | Mọi thao tác thay đổi dữ liệu phải được ghi vào nhật ký hoạt động |
| BR-6 | Nhật ký hoạt động chỉ ghi thêm, không sửa hoặc xoá được |
| BR-7 | Mọi thời gian lưu theo giờ quốc tế, hiển thị theo giờ Việt Nam |
| BR-8 | Mọi số tiền lưu dưới dạng số thập phân chính xác, không dùng số thực dấu phẩy động |

---

## 15. Yêu cầu phi chức năng

| Mã | Yêu cầu | Ngưỡng |
|---|---|---|
| NFR-1 | Thời gian tải màn hình danh sách | Dưới 2 giây với 50.000 bản ghi |
| NFR-2 | Số người dùng đồng thời | 50 (cam kết). Mục tiêu mở rộng đã đo được: **100 người trên 100 nghìn khách** ở KN CRM, p95 mở/lọc/chuyển trang ≤ 1 s, lưu ô ≤ 0,5 s — AC-10.8, ADR-016 |
| NFR-3 | Thời gian nhập tệp Excel 2.000 dòng | Dưới 60 giây |
| NFR-4 | Mật khẩu lưu dưới dạng đã băm, không lưu dạng đọc được | Bắt buộc |
| NFR-5 | Kết nối mã hoá bắt buộc khi truy cập từ ngoài máy chủ | Bắt buộc |
| NFR-6 | Hệ thống không được hiển thị trang trắng khi gặp lỗi | Luôn hiện thông báo tiếng Việt |
| NFR-7 | Giao diện dùng được trên máy tính, máy tính bảng và điện thoại | Bắt buộc |
| NFR-8 | Cấu hình thay đổi được qua biến môi trường, không sửa mã nguồn | Bắt buộc |
| NFR-9 | Mức mất dữ liệu tối đa chấp nhận được khi có sự cố | 24 giờ |
| NFR-10 | Thời gian phục hồi sau sự cố | Dưới 4 giờ |
| NFR-11 | Kích thước tối đa mỗi tệp tải lên | 10 MB |
| NFR-12 | Loại tệp được phép tải lên | Excel, CSV, ảnh JPG và PNG |
| NFR-13 | Số dòng tối đa mỗi lần nhập từ tệp | 10.000 dòng |
| NFR-14 | Số bản ghi tối đa mỗi lần xuất ra tệp | 50.000 dòng |
| NFR-15 | Thời gian giữ bản sao lưu tự động | 30 ngày, tối đa 30 bản gần nhất |
| NFR-16 | Thời gian giữ tệp tạm sinh ra khi xuất dữ liệu | 24 giờ |
| NFR-17 | Thời gian giữ nhật ký hoạt động | 24 tháng |
| NFR-18 | Mức tăng dung lượng lưu trữ dự kiến | Dưới 5 GB mỗi năm |
| NFR-19 | Tần suất sao lưu tự động | Mỗi ngày một lần |
| NFR-20 | Nơi lưu bản sao lưu | Ít nhất một bản ở nơi khác máy chủ chính |

---

> **Về các con số trong mục 15.** Những giá trị này được đặt dựa trên quy mô dự kiến
> tại mục 5 của `01-tong-quan-san-pham.md`. Chúng cần được xác nhận với người sử dụng
> trước khi triển khai, và có thể điều chỉnh mà không ảnh hưởng tới thiết kế.

---

## 16. Nội dung chưa quyết định

Những mục sau ảnh hưởng tới phạm vi và cần thống nhất trước khi triển khai.

| # | Nội dung | Phương án | Ảnh hưởng |
|---|---|---|---|
| 1 | ~~Mức độ công thức trên bảng — FR-7.8~~ | Đã chốt: cột tính sẵn, không công thức tự do — ADR-006, ADR-009 | — |
| 2 | ~~Tạo biểu mẫu thì tự sinh bảng mới, hay luôn phải chọn bảng có sẵn~~ | Đã chốt: luôn chọn bảng có sẵn — ADR-007 | — |
| 3 | Lịch nộp báo cáo có bắt buộc đúng giờ không | Chỉ ghi nhận / Nhắc nhở / Chặn nộp muộn | Có cần tác vụ chạy nền hay không — backlog N1 |
| 4 | ~~Cách thống kê trên bảng do người dùng tự tạo~~ | Đã chốt: bảy nhãn ý nghĩa — ADR-007 | — |
| 5 | Tỉ giá cố định quy doanh số về VND cho bảng xếp hạng Văn hoá — FR-12.3 | Đang tạm USD 25.400, CAD 18.500, PHP 440 trong cấu hình (biến `EXCHANGE_RATES_VND`, dạng `USD=25400,CAD=18500,PHP=440`) | Số trên bảng xếp hạng — backlog N11; đổi tỉ giá giữa tháng thì hạng đổi theo — S21 |
| 6 | Danh sách giá trị văn hoá để ghi nhận — FR-12.1 | Đang tạm năm giá trị: Tận tâm, Chính trực, Hợp tác, Sáng tạo, Trách nhiệm | Đổi sau khi có ghi nhận thật thì phải chuyển dữ liệu — backlog N12 |

---

## 16a. Bổ sung feedback KN CRM đã duyệt

**Bổ sung đã duyệt 09.09.2026 — feedback KN CRM:** Vận đơn mới quản lý người
phụ trách Vận đơn, CSKH và Marketing bằng liên kết tài khoản. Leader/Manager
Vận đơn và Admin phân công; nhân viên Vận đơn xem dòng được giao, Sale thấy
dòng mình tạo hoặc chăm sóc, CSKH chỉ thấy dòng được giao. Giao CSKH không
tự cấp quyền sửa, gán Marketing không cấp quyền xem. Giữ bộ trạng thái hiện
có; lọc độc lập vận chuyển/thanh toán, mã sản phẩm chi tiết, Quốc gia và
Marketing được gán. Excel xuất toàn kết quả lọc/ngày trong quyền, có mã nhân
viên; file nền phải kiểm lại quyền trước tải. Chi tiết và các ngoại lệ thay
thế quy tắc bảng mới trước đây ở [ADR-020](quyet-dinh/020-phan-cong-loc-xuat-van-don-moi.md).
H7 về nhập tiền/bằng chứng vẫn chờ quyết định.

## 16b. File master và Thống kê KN CRM — chốt 10.09.2026

Chỉ Vận đơn mới chuyển sang lưới riêng, cuộn liên tục theo khối, thao tác
Excel cơ bản để xem/chỉnh sửa; không công thức tự do. Chữ dài đọc/sửa trong
vùng nổi, không giãn cấu trúc. Ctrl+A chọn toàn bộ kết quả lọc, copy/ghi tối
đa 2.000 ô, Undo/Redo có kiểm xung đột. Không thêm dòng/xóa dòng/định dạng/
kéo điền trong UI mới. Thống kê tách thành tính năng ngang cấp Bảng tính,
SVG và bảng đối chiếu theo toàn dữ liệu lọc/quyền, tách tiền tệ. Chi tiết
[ADR-021](quyet-dinh/021-luoi-master-va-thong-ke-crm.md). Không đổi nghiệp vụ H7.

## 17. Ngoài phạm vi phase 1

| Nhóm | Nội dung |
|---|---|
| Nhân sự | Đánh giá năng lực, đào tạo, chấm công, nghỉ phép, bảo hiểm |
| Kế toán | Thống kê và đối chiếu với phần mềm kế toán bên ngoài |
| Kho | Hàng sản xuất, vận chuyển, tồn kho, xuất kho |
| Trợ lý AI | Hỗ trợ Sale và Chăm sóc khách hàng |
| Ứng dụng di động | Bản cài đặt từ cửa hàng ứng dụng |
| Đồng bộ hai chiều | Sửa trên bảng vận đơn cập nhật ngược lại đơn hàng |
| Tích hợp bên ngoài | Kết nối với phần mềm kế toán hoặc sàn thương mại điện tử |

## Bổ sung thao tác Vận đơn mới — 10.09.2026

Quy định này thay phần lưu thủ công trước đó. Kết thúc sửa sẽ tự lưu nền;
Ctrl+S/Lưu dữ liệu gửi ngay. Chờ trạng thái Đã lưu trước khi đóng trang.
Đổi lọc/popup giữ nháp; cảnh báo rời trang chỉ xuất hiện khi còn chưa lưu.
Nhập file, phân công và chi tiết sản phẩm vẫn có nút gửi riêng.

- Thao tác như Excel (ADR-033, 18.09.2026): bấm chỉ chọn ô; gõ phím chữ hay số
  là nhập ngay với ký tự vừa gõ; Enter, F2 hoặc bấm đúp mở ô nhập giữ giá trị cũ.
  Tab và Enter trong ô nhập chuyển sang ô kế nhưng không tự mở; Ctrl+A chọn cả
  bảng, Delete xoá vùng chọn. Ô nhiều dòng Enter xuống dòng, Ctrl+Enter kết thúc.
  Ô không sửa được thì gõ phím mở vùng đọc. Nút **Tôi / Toàn bộ** ở bảng Vận đơn lọc theo cột phụ trách của
  bộ phận mình, nhớ trên trình duyệt, mặc định Toàn bộ.
- Bấm số hàng để chọn hàng. Dòng đầu mang số 1. Đơn mới ở cuối theo mặc định.
- Định dạng có cỡ chữ/màu chữ/màu nền, dùng cùng autosave và Undo/Redo.
- … → Lịch sử xem thay đổi qua lưới mới của dòng đang chọn. … → Xung đột
  đối chiếu giá trị và chọn server hoặc gửi lại; có xung đột thì cả lượt chưa ghi.
- Admin lên đơn tại CRM phải chọn Sale đứng đơn đang hoạt động.

Phạm vi và kết quả kiểm chứng: [báo cáo chín hạng mục](kiem-chung-master-nine.md).
