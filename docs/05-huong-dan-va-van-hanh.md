# Hướng dẫn sử dụng và vận hành

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

> ## ⚠ Tài liệu này viết trước, một phần chưa chạy được
>
> Cập nhật 29.08.2026 — xong Giai đoạn 5. Những mục dưới đây **mô tả tính năng
> chưa xây xong**, đọc để biết hướng chứ đừng đi thử:
>
> | Mục | Chờ |
> |---|---|
> | **A4 · Nhập từ tệp Excel** và **Xuất ra tệp Excel** | Giai đoạn 7 |
> | **A5 · Báo cáo tổng hợp** — trọn mục | Giai đoạn 6 |
> | **B · Sao lưu và phục hồi** | Giai đoạn 8 |
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

Hệ thống đưa bạn tới màn hình phù hợp với bộ phận của mình:

| Bộ phận | Màn hình đầu tiên |
|---|---|
| Sale | Lên đơn |
| Marketing | Bảng dữ liệu |
| Vận đơn | Bảng vận đơn |

---

## A2. Nộp báo cáo hằng ngày

Mỗi bộ phận có biểu mẫu riêng.

1. Vào mục **Báo cáo**
2. Chọn **Nộp báo cáo hôm nay**
3. Điền các trường, những trường có dấu sao là bắt buộc
4. Bấm **Gửi**

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
3. Thêm sản phẩm: chọn sản phẩm, nhập số lượng
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

### Sửa dữ liệu

Bấm đúp vào ô cần sửa, nhập giá trị mới, bấm ra ngoài để lưu.

Nếu bạn không có quyền sửa cột đó, ô sẽ không cho nhập.

### Nhập từ tệp Excel

> **Chưa làm — Giai đoạn 7.** Mô tả dưới đây là dự kiến.

1. Bấm **Nhập tệp**
2. Chọn tệp Excel từ máy
3. Xem trước dữ liệu, kiểm tra cột có khớp không
4. Bấm **Xác nhận nhập**

**Giới hạn:** tệp tối đa 10 MB, tối đa 5.000 dòng mỗi lần.

Nếu tệp có dòng lỗi, hệ thống vẫn nhập các dòng hợp lệ và liệt kê dòng bị bỏ qua.

### Xuất ra tệp Excel

> **Chưa làm — Giai đoạn 7.** Mô tả dưới đây là dự kiến.

Bấm **Xuất tệp**. Hệ thống tạo tệp và tải về máy.

Tệp xuất ra nhập lại được vào hệ thống mà không cần chỉnh sửa.

---

## A5. Báo cáo tổng hợp

> **Chưa làm — Giai đoạn 6.** Mô tả dưới đây là dự kiến.

### Xem báo cáo

1. Vào mục **Báo cáo tổng hợp**
2. Chọn khoảng thời gian
3. Chọn cách nhóm số liệu

| Cách nhóm | Cho biết |
|---|---|
| Tổng hợp | Số liệu chung toàn bộ |
| Theo nhân viên | Ai làm được bao nhiêu |
| Theo sản phẩm | Sản phẩm nào bán chạy |
| Theo thị trường | Thị trường nào hiệu quả |

### Bộ lọc

Bên trái màn hình có các bộ lọc: khoảng thời gian, sản phẩm.
Chọn nhiều điều kiện thì chúng cộng dồn với nhau.

### Xuất báo cáo

Bấm **Xuất Excel**. Tệp tải về chứa đúng số liệu đang hiển thị trên màn hình.

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

---

## A7. Câu hỏi thường gặp

| Tình huống | Cách xử lý |
|---|---|
| Quên mật khẩu | Liên hệ quản trị viên để đặt lại |
| Tài khoản bị khoá | Chờ mười lăm phút, hoặc liên hệ quản trị viên |
| Không thấy mục nào đó trong menu | Bạn chưa được cấp quyền, liên hệ quản lý |
| Không thấy dữ liệu của người khác | Đúng như thiết kế, mỗi cấp bậc có phạm vi riêng |
| Hệ thống tự đăng xuất | Do không thao tác quá một tiếng, đăng nhập lại |
| Nhập tệp báo lỗi | Kiểm tra kích thước dưới 10 MB và số dòng dưới 5.000 |
| Lỡ nhập sai đơn đã lưu | Báo quản lý, không tự sửa được |

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

1. Mở hệ thống, đăng nhập, kiểm màn hình chính hiện đủ số liệu
2. Kiểm bản sao lưu đêm qua có được tạo không
3. Nếu hệ thống không mở được, xem mục B5

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

| Mục | Quy định |
|---|---|
| Tần suất | Mỗi ngày một lần, tự động |
| Thời gian giữ | 30 ngày, tối đa 30 bản gần nhất |
| Nơi lưu | Ít nhất một bản ở nơi khác máy chủ chính |
| Mã hoá | Bản sao lưu mã hoá trước khi rời khỏi máy chủ |
| Thử phục hồi | Mỗi quý một lần |

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
