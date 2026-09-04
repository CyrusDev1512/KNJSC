# Tiêu chí nghiệm thu

| Mục | Nội dung |
|---|---|
| Dự án | Kim Ngân JSC — Hệ thống vận hành nội bộ |
| Giai đoạn | Phase 1 |
| Phiên bản tài liệu | 0.1 — bản nháp |
| Ngày | (điền ngày) |
| Người viết | (điền tên) |
| Tài liệu liên quan | `02-yeu-cau-san-pham.md` · `03-thiet-ke-ky-thuat.md` |

> Tài liệu này định nghĩa **thế nào là xong**.
> Mỗi tiêu chí có mã riêng và tham chiếu ngược tới yêu cầu ở `02-yeu-cau-san-pham.md`.

---

## Cách đọc

```
AC-x.y     Tiêu chí nghiệm thu
FR-x.y     Yêu cầu chức năng tương ứng
Tự động    Có bài kiểm thử tự động, chạy mỗi lần sửa mã
Thủ công   Người kiểm tra bằng tay trước mỗi lần bàn giao
```

**Quy ước:** mỗi tiêu chí tự động phải có một hàm kiểm thử trong mã nguồn, và
docstring của hàm đó ghi mã tiêu chí. Ví dụ:

```
def test_staff_khong_xem_duoc_du_lieu_nguoi_khac():
    """AC-3.1 — Staff chỉ xem được dữ liệu do chính mình tạo"""
```

Nhờ vậy tìm được hai chiều: từ tài liệu ra mã, và từ mã về tài liệu.
Bài `app/tests/test_truy_vet.py` kiểm điều này tự động, nên quy ước không
trôi được: tiêu chí Tự động nào chưa có bài kiểm là đỏ ngay.

**Mã ở đầu docstring mới tính.** Nhắc tới một mã ở giữa lời giải thích chỉ là
chú thích, không phải lời khẳng định bài đó kiểm tiêu chí này.

**Bài kiểm ghi mã quy tắc thay vì mã tiêu chí là hợp lệ.** Nhiều bài kiểm quy
tắc nghiệp vụ (`BR-`), yêu cầu chức năng (`FR-`), quyết định kiến trúc (`ADR-`)
hoặc quy tắc trong `CLAUDE.md` — chúng không tương ứng tiêu chí nghiệm thu nào,
và đó là chuyện bình thường.

---

## 1. Tài khoản và phiên đăng nhập

| Mã | Tiêu chí | Yêu cầu | Loại |
|---|---|---|---|
| AC-1.1 | Gọi mọi đường dẫn khi chưa đăng nhập thì bị chuyển về trang đăng nhập | FR-1.1 | Tự động |
| AC-1.2 | Đăng nhập sai 5 lần liên tiếp thì lần thứ 6 bị từ chối, kể cả khi nhập đúng | FR-1.2 | Tự động |
| AC-1.3 | Tài khoản bị khoá tự mở lại sau 15 phút | FR-1.2 | Tự động |
| AC-1.4 | Phiên không thao tác quá 60 phút thì yêu cầu tiếp theo bị từ chối | FR-1.3 | Tự động |
| AC-1.5 | Người dùng mới đăng nhập lần đầu bị buộc đổi mật khẩu trước khi làm gì khác | FR-1.4 | Tự động |
| AC-1.6 | Quản trị viên khoá tài khoản đang mở phiên thì yêu cầu tiếp theo của người đó bị từ chối ngay | FR-1.5 | Tự động |
| AC-1.7 | ~~Sale đăng nhập vào thẳng màn hình lên đơn, Vận đơn vào thẳng bảng vận đơn~~ **Bỏ theo Q34** — mọi người vào trang tổng quan chung | FR-1.6 | Bỏ |

---

## 2. Cơ cấu tổ chức

| Mã | Tiêu chí | Yêu cầu | Loại |
|---|---|---|---|
| AC-2.1 | Tạo được bộ phận mới, hiển thị trong danh sách | FR-2.1 | Tự động |
| AC-2.2 | Tạo được nhiều team trong một bộ phận | FR-2.2 | Tự động |
| AC-2.3 | Gán người dùng vào bộ phận, team và cấp bậc, thay đổi có hiệu lực ngay | FR-2.3 | Tự động |
| AC-2.4 | Thêm team mới không cần khởi động lại hệ thống | FR-2.4 | Thủ công |

---

## 3. Phân quyền

Đây là nhóm quan trọng nhất. Mỗi tiêu chí kiểm cả hai chiều: được phép và bị từ chối.

| Mã | Tiêu chí | Yêu cầu | Loại |
|---|---|---|---|
| AC-3.1 | Staff chỉ thấy bản ghi do chính mình tạo, không thấy của người cùng team | FR-3.1 | Tự động |
| AC-3.2 | Leader thấy toàn bộ bản ghi của team mình | FR-3.2 | Tự động |
| AC-3.3 | Leader không thấy bản ghi của team khác cùng bộ phận | FR-3.2 | Tự động |
| AC-3.4 | Manager thấy toàn bộ bản ghi của bộ phận mình | FR-3.3 | Tự động |
| AC-3.5 | Manager không thấy bản ghi của bộ phận khác | FR-3.4 | Tự động |
| AC-3.6 | Truy cập dữ liệu ngoài phạm vi trả về lỗi từ chối, không phải danh sách rỗng | FR-3.5 | Tự động |
| AC-3.7 | Gọi thẳng đường dẫn không qua giao diện vẫn bị kiểm quyền | FR-3.6 | Tự động |
| AC-3.8 | Quản trị viên thấy dữ liệu của mọi bộ phận | FR-3.3 · cấp bậc thứ tư | Tự động |

### Ma trận kiểm chéo

Mỗi ô là một bài kiểm thử. Năm vai trò nhân với chín đường dẫn chính — 45 ô, thêm hai dòng ngày 03.09.2026 (nhập tệp và Bảng tính).

| Đường dẫn | Staff Sale | Leader Sale | Manager Sale | Staff Vận đơn | Chưa đăng nhập |
|---|---|---|---|---|---|
| Báo cáo của chính mình | Vào được | Vào được | Vào được | Vào được | Chuyển đăng nhập |
| Báo cáo người cùng team | Từ chối | Vào được | Vào được | Từ chối | Chuyển đăng nhập |
| Báo cáo team khác cùng bộ phận | Từ chối | Từ chối | Vào được | Từ chối | Chuyển đăng nhập |
| Báo cáo bộ phận khác | Từ chối | Từ chối | Từ chối | Từ chối | Chuyển đăng nhập |
| Màn hình lên đơn | Vào được | Vào được | Vào được | Từ chối | Chuyển đăng nhập |
| Bảng vận đơn | Từ chối | Từ chối | Từ chối | Vào được | Chuyển đăng nhập |
| Quản lý biểu mẫu | Từ chối | Từ chối | Vào được | Từ chối | Chuyển đăng nhập |
| Nhập tệp vào bảng của Sale | Từ chối | Từ chối | Vào được | Từ chối | Chuyển đăng nhập |
| Bảng tính vận đơn | Từ chối | Từ chối | Từ chối | Vào được | Chuyển đăng nhập |

---

## 4. Báo cáo hằng ngày

| Mã | Tiêu chí | Yêu cầu | Loại |
|---|---|---|---|
| AC-4.1 | Mỗi bộ phận thấy biểu mẫu riêng của mình, không thấy biểu mẫu bộ phận khác | FR-4.1 | Tự động |
| AC-4.2 | Nộp báo cáo thì thời điểm nộp được ghi lại chính xác | FR-4.2 | Tự động |
| AC-4.3 | Người dùng xem lại được danh sách báo cáo cũ của mình | FR-4.3 | Tự động |
| AC-4.4 | Báo cáo đã nộp không sửa được, kể cả khi gọi thẳng đường dẫn sửa | FR-4.4 | Tự động |
| AC-4.5 | Leader xem được báo cáo của người trong team | FR-4.5 | Tự động |

---

## 5. Báo cáo tổng hợp

| Mã | Tiêu chí | Yêu cầu | Loại |
|---|---|---|---|
| AC-5.1 | Bốn cách nhóm đều cho ra số liệu đúng khi đối chiếu với dữ liệu gốc | FR-5.1 | Tự động |
| AC-5.2 | Lọc theo khoảng thời gian trả về đúng số bản ghi trong khoảng đó | FR-5.2 | Tự động |
| AC-5.3 | Lọc theo sản phẩm trả về đúng số bản ghi | FR-5.3 | Tự động |
| AC-5.4 | Dòng tổng cộng bằng đúng tổng các dòng chi tiết | FR-5.4 | Tự động |
| AC-5.5 | Leader chỉ thấy số liệu của team mình trong báo cáo tổng hợp | FR-5.5 | Tự động |
| AC-5.6 | Tệp xuất ra mở được bằng Excel, số liệu khớp với màn hình | FR-5.6 | Thủ công |

---

## 6. Lên đơn

| Mã | Tiêu chí | Yêu cầu | Loại |
|---|---|---|---|
| AC-6.1 | Tạo đơn thiếu trường bắt buộc thì bị từ chối, dữ liệu đã nhập không mất | FR-6.1 | Tự động |
| AC-6.2 | Đơn có 5 sản phẩm lưu được đầy đủ, không mất dòng nào | FR-6.2 | Tự động |
| AC-6.3 | Lưu đơn xong thì bảng vận đơn có thêm đúng một dòng tương ứng | FR-6.3 | Tự động |
| AC-6.4 | Mã liên kết giữa đơn và dòng trên bảng được lưu và tra cứu được | FR-6.4 | Tự động |
| AC-6.5 | Nếu ghi sang bảng vận đơn thất bại thì đơn hàng cũng không được lưu | FR-6.3 | Tự động |
| AC-6.6 | Người tạo đơn xem lại được đơn cũ của mình | FR-6.5 | Tự động |
| AC-6.7 | Đơn đã lưu không sửa được, kể cả khi gọi thẳng đường dẫn sửa | FR-6.6 | Tự động |
| AC-6.8 | Nhập đơn với số điện thoại đã có thì hệ thống báo khách đã mua trước đó | FR-6.7 | Tự động |

---

## 7. Bảng dữ liệu

| Mã | Tiêu chí | Yêu cầu | Loại |
|---|---|---|---|
| AC-7.1 | Bảng 50.000 bản ghi tải trang đầu dưới 2 giây | FR-7.1 · NFR-1 | Tự động |
| AC-7.2 | Lọc theo cột trả về đúng số bản ghi | FR-7.2 | Tự động |
| AC-7.3 | Sắp xếp theo cột cho ra thứ tự đúng, cả tăng và giảm | FR-7.3 | Tự động |
| AC-7.4 | Người không có quyền sửa thì không sửa được ô, kể cả gọi thẳng đường dẫn | FR-7.4 | Tự động |
| AC-7.5 | Nhập tệp Excel 2.000 dòng hoàn tất dưới 60 giây | FR-7.5 · NFR-3 | Tự động |
| AC-7.6 | Tệp Excel có dòng lỗi thì các dòng hợp lệ vẫn được nhập, dòng lỗi được liệt kê | FR-7.5 | Tự động |
| AC-7.7 | **Xuất ra tệp Excel rồi nhập lại chính tệp đó thì không phát sinh lỗi** | FR-7.7 | Tự động |
| AC-7.8 | Tệp vượt 10 MB bị từ chối với thông báo rõ ràng | NFR-11 | Tự động |
| AC-7.9 | Tệp không đúng định dạng cho phép bị từ chối | NFR-12 | Tự động |
| AC-7.10 | Cột tính sẵn cho ra đúng kết quả, đối chiếu với số liệu thật của khách hàng | FR-7.8 · ADR-006 | Tự động |
| AC-7.11 | Chia cho không hoặc thiếu toán hạng thì cột tính sẵn để trống, không hỏng cả dòng | FR-7.8 · ADR-006 | Tự động |
| AC-7.12 | Đổi công thức của một cột thì bản ghi cũ được tính lại, không còn giữ số cũ | FR-7.8 · ADR-006 | Tự động |

---

## 8. Quản lý biểu mẫu và bảng

| Mã | Tiêu chí | Yêu cầu | Loại |
|---|---|---|---|
| AC-8.1 | Manager tạo biểu mẫu mới, biểu mẫu xuất hiện cho người được phân quyền | FR-8.1 | Tự động |
| AC-8.2 | Trường đánh dấu bắt buộc thì không gửi được nếu bỏ trống | FR-8.2 | Tự động |
| AC-8.3 | Dữ liệu từ biểu mẫu ghi đúng vào bảng đích đã chọn | FR-8.3 | Tự động |
| AC-8.4 | Người không được phân quyền không thấy biểu mẫu đó | FR-8.4 | Tự động |
| AC-8.5 | Sửa biểu mẫu không làm mất dữ liệu đã nhập trước đó | FR-8.5 | Tự động |
| AC-8.6 | Nối trường kiểu chữ vào cột kiểu số thì bị chặn với thông báo rõ ràng | FR-8.6 | Tự động |

---

## 9. Quy tắc nghiệp vụ

| Mã | Tiêu chí | Quy tắc | Loại |
|---|---|---|---|
| AC-9.1 | Xoá bản ghi thì bản ghi vẫn còn trong cơ sở dữ liệu, chỉ đánh dấu đã xoá | BR-4 | Tự động |
| AC-9.2 | Mọi thao tác thay đổi dữ liệu sinh một dòng trong nhật ký hoạt động | BR-5 | Tự động |
| AC-9.3 | Không có đường nào sửa hoặc xoá được bản ghi nhật ký | BR-6 | Tự động |
| AC-9.4 | Thời gian hiển thị theo giờ Việt Nam, dữ liệu lưu theo giờ quốc tế | BR-7 | Tự động |
| AC-9.5 | Cộng 1.000 dòng tiền cho kết quả chính xác tuyệt đối, không sai số | BR-8 | Tự động |

---

## 10. Hiệu năng và vận hành

| Mã | Tiêu chí | Yêu cầu | Loại |
|---|---|---|---|
| AC-10.1 | 50 người dùng thao tác đồng thời, không có yêu cầu nào quá 3 giây | NFR-2 | Thủ công |
| AC-10.2 | Màn hình danh sách chạy không quá 10 lệnh truy vấn | Q2 | Tự động |
| AC-10.3 | Gặp lỗi thì hiện thông báo tiếng Việt, không hiện trang trắng | NFR-6 | Thủ công |

> `AC-10.3` giữ **Thủ công** vì phần trang lỗi 404 và 500 chưa làm (backlog **K9**).
> Phần lỗi nhập liệu đã có bài kiểm tự động, ghi mã `NFR-6` trong docstring.
| AC-10.4 | Giao diện dùng được trên điện thoại và máy tính bảng | NFR-7 | Thủ công |
| AC-10.5 | Phục hồi thành công từ bản sao lưu trên môi trường thử | NFR-10 | Thủ công |
| AC-10.6 | Bản sao lưu tự động chỉ giữ tối đa 30 bản gần nhất | NFR-15 | Tự động |
| AC-10.7 | Đọc trực tiếp cơ sở dữ liệu không thấy mật khẩu dạng đọc được | NFR-4 | Tự động |

---

## 11. Bảng tính

Lưới làm việc kiểu Excel. Dựng đầu tiên cho bộ phận Vận đơn theo tệp thật
`MITA Vận đơn CSKH Nội bộ CANADA.xlsx` (bản ẩn danh: `docs/tham-khao/vandon-mau.xlsx`)
— ADR-009, backlog Q38 tới Q45 — rồi mở cho **mọi bảng dữ liệu** ở
`/bang-tinh/<mã bảng>/` — ADR-010, Q46 tới Q50. Bảng vận đơn vẫn chỉ xem ở
dịch vụ chính và sửa ở dịch vụ riêng (`bangtinh`, cổng 8021); bảng khác sửa
được ở cả hai.

| Mã | Tiêu chí | Yêu cầu | Loại |
|---|---|---|---|
| AC-11.1 | Lưới hiện đủ cột của bảng vận đơn; bốn cột đầu và hàng tiêu đề đứng yên khi cuộn | FR-7.8 | Thủ công |
| AC-11.2 | Lọc theo từng cột — danh sách giá trị kèm số đếm, chứa chữ, khoảng số hoặc ngày, ô trống — nhiều cột cộng dồn, số dòng đúng | FR-7.8 | Tự động |
| AC-11.3 | Sửa ô tại chỗ đúng kiểu cột; ô danh sách chỉ nhận giá trị trong danh sách, giá trị lạ bị từ chối kèm lý do; mỗi lần sửa ghi một dòng nhật ký | FR-7.4 · BR-5 | Tự động |
| AC-11.4 | Người ngoài phạm vi bảng vận đơn (không phải quản trị viên) bị từ chối ở mọi đường dẫn Bảng tính của bảng đó, kể cả gọi thẳng và gửi POST | FR-3.6 | Tự động |
| AC-11.5 | Cột Lọc trùng đếm đúng số dòng cùng số điện thoại và tô màu khi lớn hơn 1; lọc được "chỉ số trùng" | FR-7.8 | Tự động |
| AC-11.6 | Dòng Hủy trước giao, Hủy sau giao, Hoàn đơn được tô màu | FR-7.8 | Tự động |
| AC-11.7 | Bảng vận đơn không sửa được ô ở Bảng dữ liệu; cùng đường dẫn đó ở Bảng tính thì sửa được | FR-7.4 | Tự động |
| AC-11.8 | Mỗi sản phẩm đang bán có một cột số lượng trên bảng vận đơn; lên đơn điền tự động số lượng, địa chỉ và lần mua | FR-6.3 · FR-6.7 | Tự động |
| AC-11.9 | Nhập tệp vận đơn thật (ẩn danh) không chỉnh sửa: mọi dòng vào, không dòng lỗi, trạng thái và thanh toán khớp danh sách, điện thoại là chuỗi | FR-7.5 | Tự động |
| AC-11.10 | Bàn phím: mũi tên và Tab đi giữa các ô, Enter sửa, Esc huỷ, chọn giá trị danh sách thì ô cập nhật không tải lại trang | FR-7.8 | Tự động |
| AC-11.11 | Bảng tính dùng được trên điện thoại và máy tính bảng | NFR-8 | Thủ công |
| AC-11.12 | Bảng nào trong phạm vi quyền cũng mở được ở `/bang-tinh/<mã>/`; ngoài phạm vi bị từ chối; `/bang-tinh/` mở bảng vận đơn nếu thấy, không thì bảng đầu tiên trong phạm vi; thanh công cụ hiện nút theo quyền | FR-7.1 · FR-3.6 | Tự động |
| AC-11.13 | Thanh lọc bên trái: chọn nhanh (hôm nay, hôm qua, 7 ngày, tháng này, tháng trước) và từ ngày / đến ngày viết vào bộ lọc cột Ngày; sản phẩm đánh dấu chọn lọc "có một trong"; xuất Excel ra đúng số dòng của lưới đang lọc | FR-7.2 · FR-5.2 · FR-5.3 · FR-7.6 | Tự động |
| AC-11.14 | Lưới thừa dòng trống cho người có quyền thêm; gõ vào rồi rời đi là thành bản ghi thật thuộc bộ phận sở hữu bảng; lỗi thì báo lý do và giữ giá trị đã gõ; không quyền thì không có dòng trống và gửi thẳng bị từ chối có ghi nhật ký | FR-7.4 · FR-3.6 | Tự động |
| AC-11.16 | Mỗi bảng một cột khoá do Manager đặt trong Sửa cột; ô cột khoá có nút lọc theo giá trị, cộng dồn với bộ lọc đang bật; cột tính sẵn không làm khoá được | FR-7.2 · FR-8.5 | Tự động |
| AC-11.18 | Mọi ô trên lưới có viền như Excel; thanh công cụ đủ mục (nhập, xuất, thêm dòng, thêm cột, thư mục, định dạng, lọc theo ô, ẩn cột); ẩn cột nhớ trên trình duyệt; thanh bên thu gọn được | FR-7.8 | Thủ công |

---

## 12. Kiểm thử thủ công trước bàn giao

Những việc máy không tự làm được, người phải kiểm bằng tay.

| # | Việc | Ghi chú |
|---|---|---|
| 1 | Cài đặt từ đầu trên máy sạch, chạy tới màn hình đăng nhập | |
| 2 | Ba vai trò đăng nhập, chạy trọn quy trình của mình | Sale, Marketing, Vận đơn |
| 3 | Nhập tệp Excel thật của công ty, không chỉnh sửa trước | |
| 4 | Xuất báo cáo, mở bằng Excel, đối chiếu số liệu | |
| 5 | Thử trên điện thoại và máy tính bảng thật | |
| 6 | Phục hồi từ bản sao lưu trên môi trường thử | |
| 7 | Ngắt mạng giữa chừng, kiểm thông báo lỗi | |

---

## 13. Điều kiện coi là hoàn thành phase 1

| # | Điều kiện |
|---|---|
| 1 | Toàn bộ tiêu chí đánh dấu **Tự động** đều có bài kiểm thử và đều đạt |
| 2 | Ma trận kiểm chéo phân quyền ở mục 3 được kiểm đầy đủ, cả trường hợp cho phép và từ chối |
| 3 | Toàn bộ danh sách kiểm thủ công ở mục 12 đã thực hiện và đạt |
| 4 | Đã phục hồi thành công ít nhất một lần từ bản sao lưu |
| 5 | Tệp Excel thật của công ty nhập được mà không cần chỉnh sửa thủ công |
| 6 | Ba vai trò đã chạy trọn quy trình trên dữ liệu thật |
| 7 | Tài liệu hướng dẫn sử dụng và vận hành đã bàn giao |

**Không bỏ qua** các tiêu chí thuộc mục 3 và mục 9 với lý do sẽ sửa sau.
Lỗi phân quyền dẫn tới rò rỉ dữ liệu, và dữ liệu đã lộ thì không thu hồi được.

---

## 14. Nội dung chưa quyết định

| # | Nội dung | Ảnh hưởng |
|---|---|---|
| 1 | ~~Tiêu chí cho công thức trên bảng~~ | Đã chốt 29.08.2026 — ADR-006, thành AC-7.10 tới AC-7.12 |
| 2 | Số lượng bài kiểm thử tự động tối thiểu | Có nên đặt ngưỡng tỉ lệ bao phủ không |
| 3 | ~~Công cụ đo hiệu năng khi kiểm AC-10.1~~ | Đã chốt 03.09.2026 — Locust, chỉ dùng khi kiểm thử (backlog Q44, K6 đóng) |
