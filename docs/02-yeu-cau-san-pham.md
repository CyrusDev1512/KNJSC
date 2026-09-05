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
| FR-1.4 | Hệ thống phải buộc người dùng đổi mật khẩu trong lần đăng nhập đầu tiên |
| FR-1.5 | Khi quản trị viên khoá tài khoản hoặc thay đổi quyền, phiên đang mở của người đó phải mất hiệu lực ngay |
| FR-1.6 | ~~Sau khi đăng nhập, hệ thống phải đưa người dùng tới màn hình phù hợp với bộ phận và cấp bậc của họ~~ **Bỏ theo Q34** — mọi người vào trang tổng quan chung, phân quyền đã ẩn tính năng ngoài phận sự |

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
| FR-4.2 | Hệ thống phải ghi nhận thời điểm nộp của mỗi báo cáo |
| FR-4.3 | Người dùng phải xem lại được các báo cáo cũ do chính mình nộp |
| FR-4.4 | Người dùng không được sửa báo cáo đã nộp |
| FR-4.5 | Leader và Manager phải xem được báo cáo của người thuộc phạm vi quản lý |

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

---

## 6. Lên đơn

| Mã | Yêu cầu |
|---|---|
| FR-6.1 | Hệ thống phải cho phép nhập đơn hàng với thông tin khách hàng, danh sách sản phẩm, giá bán và phương thức thanh toán |
| FR-6.2 | Một đơn hàng phải chứa được nhiều sản phẩm, không giới hạn số lượng dòng |
| FR-6.3 | Sau khi lưu đơn, hệ thống phải tự động ghi dữ liệu sang bảng vận đơn |
| FR-6.4 | Hệ thống phải lưu mã liên kết giữa đơn hàng và dòng tương ứng trên bảng vận đơn |
| FR-6.5 | Người tạo đơn phải xem lại được các đơn cũ do chính mình tạo |
| FR-6.6 | Người tạo đơn không được sửa đơn đã lưu |
| FR-6.7 | Hệ thống phải nhận diện được khách hàng đã mua trước đó, dựa trên số điện thoại |

---

## 7. Bảng dữ liệu

| Mã | Yêu cầu |
|---|---|
| FR-7.1 | Hệ thống phải hiển thị dữ liệu dạng bảng, có phân trang |
| FR-7.2 | Hệ thống phải cho phép lọc theo từng cột |
| FR-7.3 | Hệ thống phải cho phép sắp xếp theo từng cột |
| FR-7.4 | Hệ thống phải cho phép sửa dữ liệu trực tiếp trên bảng, nếu người dùng có quyền |
| FR-7.5 | Hệ thống phải cho phép nhập dữ liệu từ tệp Excel |
| FR-7.6 | Hệ thống phải cho phép xuất dữ liệu ra tệp Excel |
| FR-7.7 | Tệp xuất ra phải nhập lại được vào hệ thống mà không phát sinh lỗi |
| FR-7.8 | Hệ thống phải hỗ trợ công thức tính toán trên bảng — *phạm vi cụ thể xem mục 11*. Đã chốt: cột tính sẵn trên Bảng dữ liệu (ADR-006) và **Bảng tính vận đơn** là lưới làm việc theo tệp thật, không có công thức tự do (ADR-009); nhìn và thao tác theo bảng tính KN Demo, công thức ở thanh công thức chờ cách thứ ba (ADR-011) |
| FR-7.9 | Bảng tính phải thao tác được như bảng tính quen thuộc: kéo chuột chọn vùng, cắt/chép/dán (kể cả dán từ Excel), tay kéo điền, xoá nội dung, hoàn tác và làm lại — mỗi ô vẫn là bản ghi thật có phạm vi quyền, một gói ô lưu một giao dịch được cả hoặc không gì (ADR-011) |
| FR-7.10 | Bảng tính phải có menu chuột phải: chèn hàng trống, xoá hàng (xoá mềm, hoàn tác được), chèn và xoá cột ngay trên lưới cho Manager của bộ phận sở hữu bảng, xoá nội dung, xoá định dạng (ADR-011) |
| FR-7.11 | Định dạng ô đủ như bảng tính — nghiêng, gạch chân, gạch ngang, xuống dòng, viền, màu chữ và màu nền từ bảng 40 màu, cỡ chữ, định dạng số — vẫn là sổ đóng lưu trong cơ sở dữ liệu (ADR-010, ADR-011) |
| FR-7.12 | Bảng tính phải nhìn như bảng tính KN Demo (khung, thanh công thức có ô địa chỉ, số dòng, chữ cột, cột trống, chân trang có tab, toàn màn hình), lọc theo giá trị cột như demo, và tự cập nhật khi người khác sửa (ADR-011) |

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

---

## 9. Quy tắc nghiệp vụ

Những ràng buộc phải luôn đúng, không phụ thuộc màn hình hay thao tác.

| Mã | Quy tắc |
|---|---|
| BR-1 | Mỗi người dùng thuộc đúng một bộ phận và một cấp bậc tại một thời điểm |
| BR-2 | Báo cáo đã nộp không được sửa hoặc xoá |
| BR-3 | Đơn hàng đã lưu không được sửa hoặc xoá |
| BR-4 | Xoá dữ liệu là đánh dấu đã xoá, không xoá vĩnh viễn khỏi cơ sở dữ liệu |
| BR-5 | Mọi thao tác thay đổi dữ liệu phải được ghi vào nhật ký hoạt động |
| BR-6 | Nhật ký hoạt động chỉ ghi thêm, không sửa hoặc xoá được |
| BR-7 | Mọi thời gian lưu theo giờ quốc tế, hiển thị theo giờ Việt Nam |
| BR-8 | Mọi số tiền lưu dưới dạng số thập phân chính xác, không dùng số thực dấu phẩy động |

---

## 10. Yêu cầu phi chức năng

| Mã | Yêu cầu | Ngưỡng |
|---|---|---|
| NFR-1 | Thời gian tải màn hình danh sách | Dưới 2 giây với 50.000 bản ghi |
| NFR-2 | Số người dùng đồng thời | 50 |
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
| NFR-13 | Số dòng tối đa mỗi lần nhập từ tệp | 5.000 dòng |
| NFR-14 | Số bản ghi tối đa mỗi lần xuất ra tệp | 50.000 dòng |
| NFR-15 | Thời gian giữ bản sao lưu tự động | 30 ngày, tối đa 30 bản gần nhất |
| NFR-16 | Thời gian giữ tệp tạm sinh ra khi xuất dữ liệu | 24 giờ |
| NFR-17 | Thời gian giữ nhật ký hoạt động | 24 tháng |
| NFR-18 | Mức tăng dung lượng lưu trữ dự kiến | Dưới 5 GB mỗi năm |
| NFR-19 | Tần suất sao lưu tự động | Mỗi ngày một lần |
| NFR-20 | Nơi lưu bản sao lưu | Ít nhất một bản ở nơi khác máy chủ chính |

---

> **Về các con số trong mục 10.** Những giá trị này được đặt dựa trên quy mô dự kiến
> tại mục 5 của `01-tong-quan-san-pham.md`. Chúng cần được xác nhận với người sử dụng
> trước khi triển khai, và có thể điều chỉnh mà không ảnh hưởng tới thiết kế.

---

## 11. Nội dung chưa quyết định

Những mục sau ảnh hưởng tới phạm vi và cần thống nhất trước khi triển khai.

| # | Nội dung | Phương án | Ảnh hưởng |
|---|---|---|---|
| 1 | Mức độ công thức trên bảng — FR-7.8 | Chỉ cột tính sẵn / Cho gõ công thức tự do / Kết hợp cả hai | Độ phức tạp và thời gian triển khai |
| 2 | Tạo biểu mẫu thì tự sinh bảng mới, hay luôn phải chọn bảng có sẵn | Tự sinh có tuỳ chọn / Luôn chọn | Cách vận hành hằng ngày |
| 3 | Lịch nộp báo cáo có bắt buộc đúng giờ không | Chỉ ghi nhận / Nhắc nhở / Chặn nộp muộn | Có cần tác vụ chạy nền hay không |
| 4 | Cách thống kê trên bảng do người dùng tự tạo | Gán nhãn ý nghĩa cho trường / Không thống kê | Báo cáo tổng hợp có bao phủ được dữ liệu tự tạo hay không |

---

## 12. Ngoài phạm vi phase 1

| Nhóm | Nội dung |
|---|---|
| Nhân sự | Đánh giá năng lực, đào tạo, chấm công, nghỉ phép, bảo hiểm |
| Kế toán | Thống kê và đối chiếu với phần mềm kế toán bên ngoài |
| Kho | Hàng sản xuất, vận chuyển, tồn kho, xuất kho |
| Trợ lý AI | Hỗ trợ Sale và Chăm sóc khách hàng |
| Ứng dụng di động | Bản cài đặt từ cửa hàng ứng dụng |
| Đồng bộ hai chiều | Sửa trên bảng vận đơn cập nhật ngược lại đơn hàng |
| Tích hợp bên ngoài | Kết nối với phần mềm kế toán hoặc sàn thương mại điện tử |
