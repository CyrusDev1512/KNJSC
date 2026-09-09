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
| Nhập tệp vào bảng của Sale | Từ chối | Vào được | Vào được | Từ chối | Chuyển đăng nhập |
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
| AC-4.6 | Trường mang nhãn Người bán trên biểu mẫu và báo cáo ngày được hệ thống tự ghi họ tên người gửi (thiếu họ tên thì tên đăng nhập); gửi giá trị khác trong yêu cầu cũng không đổi được; ô trên màn hình chỉ đọc, không gửi lên | FR-4.6 | Tự động |

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
| AC-6.9 | Manager lên đơn thêm được sản phẩm mới ngay tại ô chọn: mã tự sinh không trùng, sản phẩm hiện trong danh sách chọn và có ngay cột số lượng trên bảng vận đơn, mỗi lần thêm có nhật ký; Staff và Leader gửi thẳng bị từ chối có ghi nhật ký; tên trùng bị từ chối | FR-6.8 | Tự động |

---

## 7. Bảng dữ liệu

| Mã | Tiêu chí | Yêu cầu | Loại |
|---|---|---|---|
| AC-7.1 | Bảng 50.000 bản ghi tải trang đầu dưới 2 giây | FR-7.1 · NFR-1 | Tự động |
| AC-7.2 | Lọc theo cột trả về đúng số bản ghi | FR-7.2 | Tự động |
| AC-7.3 | Sắp xếp theo cột cho ra thứ tự đúng, cả tăng và giảm | FR-7.3 | Tự động |
| AC-7.4 | Bảng dữ liệu ở KN ERP chỉ để xem với mọi cấp bậc, kể cả người tạo dòng, người được cấp quyền Sửa và Admin: không có ô sửa, gọi thẳng đường sửa ô cũ trả 404, dữ liệu và nhật ký không đổi; nút Mở trong KN CRM hiện với mọi bảng | FR-7.4 | Tự động |
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
| AC-8.7 | Cột kiểu Chọn một chỉ nhận giá trị trong danh sách chọn (không phân biệt hoa thường), giá trị lạ bị từ chối kèm gợi ý; danh sách chỉ đặt được cho kiểu Chọn một, bỏ dòng trống và trùng; trên biểu mẫu và báo cáo ngày cột này hiện thành ô chọn, trên Bảng dữ liệu chỉ hiện chữ vì chỉ xem | FR-8.7 | Tự động |
| AC-8.8 | Cột Chọn một mang nhãn Sản phẩm lấy danh sách từ danh mục sản phẩm đang bán; quản lý bộ phận sở hữu bảng (Leader, Manager — ADR-015, hoặc Admin) thêm giá trị mới ngay tại ô chọn và có ghi nhật ký, trùng thì lấy giá trị có sẵn; Staff gửi thẳng bị từ chối có ghi nhật ký, Manager bộ phận khác bị chặn; bảng vận đơn giữ nguyên sổ danh sách của Bảng tính | FR-8.7 · FR-3.6 | Tự động |
| AC-8.9 | Manager (hoặc Leader cùng bộ phận — ADR-015) đặt màu cột và ngưỡng cảnh báo trong Sửa cột; ngưỡng chỉ nhận cột kiểu số; tiêu đề và ô của cột mang màu đã đặt, ô vượt ngưỡng tô đỏ, ô đạt tô xanh lá, ô trống không tô; màn hình xem báo cáo cũng mang màu | FR-8.8 | Tự động |
| AC-8.10 | Bảng dữ liệu có viền mọi ô, tiêu đề cột nền xanh lá, màu cột và ô cảnh báo nhìn rõ trên cả nền sáng lẫn nền tối, cả ở màn hình Bảng dữ liệu và xem báo cáo | FR-8.9 | Thủ công |

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
| AC-10.8 | **Kiểm tải KN CRM ở cỡ 100 nghìn khách** (docs/06 tầng 9): chạy `scripts/kiem-tai-kn-crm.*` trên máy có Docker — nạp 100.000 dòng vận đơn (≈ 3 triệu ô, 86 nghìn số điện thoại) và bảng Sale 20.000 dòng có cột tính sẵn, `do_hieu_nang` đo một người, rồi Locust **100 người 5 phút** (70 nhân viên vận đơn di qua di lại, 20 Sale/Marketing, 7 trưởng nhóm dán/xoá, 3 Manager đổi cột tính sẵn giữa phiên) trên gunicorn 3 worker; in **ĐẠT** khi p95 nhóm đọc ≤ 1 s, nhóm ghi ≤ 0,5 s, `moi-nhat/` ≤ 0,3 s, 0 lỗi, tính lại cột 100.000 dòng ≤ 30 s mà p95 người khác vẫn ≤ 1 s (`core/constants.py`) | NFR-2 | Thủ công |

---

## 11. Bảng tính

Lưới làm việc kiểu Excel. Dựng đầu tiên cho bộ phận Vận đơn theo tệp thật
`MITA Vận đơn CSKH Nội bộ CANADA.xlsx` (bản ẩn danh: `docs/tham-khao/vandon-mau.xlsx`)
— ADR-009, backlog Q38 tới Q45 — rồi mở cho **mọi bảng dữ liệu** ở
`/bang-tinh/<mã bảng>/` — ADR-010, Q46 tới Q50 — rồi **nhìn và thao tác như
bảng tính KN Demo** (ảnh ở `docs/tham-khao/kn-demo/`) — ADR-011, Q51 tới Q53.
Từ ADR-014 (06.09.2026) **mọi bảng chỉ xem ở KN ERP** và sửa ở KN CRM (dịch
vụ `bangtinh`, cổng 8021); KN ERP không còn đường sửa ô.

| Mã | Tiêu chí | Yêu cầu | Loại |
|---|---|---|---|
| AC-11.1 | Lưới hiện đủ cột của bảng vận đơn; bốn cột đầu và hàng tiêu đề đứng yên khi cuộn | FR-7.8 | Thủ công |
| AC-11.2 | Lọc theo từng cột — danh sách giá trị kèm số đếm, chứa chữ, khoảng số hoặc ngày, ô trống — nhiều cột cộng dồn, số dòng đúng | FR-7.8 | Tự động |
| AC-11.3 | Sửa ô tại chỗ đúng kiểu cột; ô danh sách chỉ nhận giá trị trong danh sách, giá trị lạ bị từ chối kèm lý do; mỗi lần sửa ghi một dòng nhật ký | FR-7.4 · BR-5 | Tự động |
| AC-11.4 | Người ngoài phạm vi bảng vận đơn (không phải quản trị viên) bị từ chối ở mọi đường dẫn Bảng tính của bảng đó, kể cả gọi thẳng và gửi POST | FR-3.6 | Tự động |
| AC-11.5 | Cột Lọc trùng đếm đúng số dòng cùng số điện thoại và tô màu khi lớn hơn 1; lọc được "chỉ số trùng" | FR-7.8 | Tự động |
| AC-11.6 | Dòng Hủy trước giao, Hủy sau giao, Hoàn đơn được tô màu | FR-7.8 | Tự động |
| AC-11.7 | Không bảng nào sửa được ô ở Bảng dữ liệu KN ERP — đường sửa ô cũ trả 404, kể cả bảng vận đơn với nhân viên Vận đơn lẫn Admin; cùng ô đó ở lưới KN CRM thì sửa được, bảng chỉ xem ở dịch vụ này thì 403 | FR-7.4 | Tự động |
| AC-11.8 | Mỗi sản phẩm đang bán có một cột số lượng trên bảng vận đơn; lên đơn điền tự động số lượng, địa chỉ và lần mua | FR-6.3 · FR-6.7 | Tự động |
| AC-11.9 | Nhập tệp vận đơn thật (ẩn danh) không chỉnh sửa: mọi dòng vào, không dòng lỗi, trạng thái và thanh toán khớp danh sách, điện thoại là chuỗi | FR-7.5 | Tự động |
| AC-11.10 | Bàn phím: mũi tên và Tab đi giữa các ô, Enter sửa, Esc huỷ, chọn giá trị danh sách thì ô cập nhật không tải lại trang | FR-7.8 | Tự động |
| AC-11.11 | Bảng tính dùng được trên điện thoại và máy tính bảng | NFR-8 | Thủ công |
| AC-11.12 | Bảng nào trong phạm vi quyền cũng mở được ở `/bang-tinh/<mã>/`; ngoài phạm vi bị từ chối; `/bang-tinh/` mở bảng vận đơn nếu thấy, không thì bảng đầu tiên trong phạm vi; thanh công cụ hiện nút theo quyền | FR-7.1 · FR-3.6 | Tự động |
| AC-11.13 | Thanh lọc bên trái: chọn nhanh (hôm nay, hôm qua, 7 ngày, tháng này, tháng trước) và từ ngày / đến ngày viết vào bộ lọc cột Ngày; sản phẩm đánh dấu chọn lọc "có một trong"; xuất Excel ra đúng số dòng của lưới đang lọc | FR-7.2 · FR-5.2 · FR-5.3 · FR-7.6 | Tự động |
| AC-11.14 | Lưới thừa dòng trống cho người có quyền thêm; gõ vào rồi rời đi là thành bản ghi thật thuộc bộ phận sở hữu bảng; lỗi thì báo lý do và giữ giá trị đã gõ; không quyền thì không có dòng trống và gửi thẳng bị từ chối có ghi nhật ký | FR-7.4 · FR-3.6 | Tự động |
| AC-11.15 | Định dạng ô — đậm, màu nền, cỡ chữ, căn lề — lưu vào cơ sở dữ liệu, người khác mở cũng thấy; chỉ nhận giá trị trong sổ đóng; quyền bằng quyền sửa ô, kiểm ở máy chủ; mỗi lần đổi ghi nhật ký | FR-7.4 · BR-5 | Tự động |
| AC-11.16 | Mỗi bảng một cột khoá do Manager đặt trong Sửa cột; ô cột khoá có nút lọc theo giá trị, cộng dồn với bộ lọc đang bật; cột tính sẵn không làm khoá được | FR-7.2 · FR-8.5 | Tự động |
| AC-11.17 | Thư mục chứa bảng: quản lý của bộ phận (Leader, Manager — ADR-015) tạo, đổi tên, xoá (xoá mềm, bảng về không thư mục) và xếp bảng vào thư mục cùng bộ phận; Staff và Manager bộ phận khác bị từ chối; thanh bên chỉ hiện thư mục trong phạm vi; trùng tên báo lỗi | FR-8.1 · FR-3.6 · BR-4 | Tự động |
| AC-11.18 | Bảng tính mở thành trang toàn màn hình riêng (không thanh bên hệ thống, lưới chiếm hết cửa sổ, menu ☰ dẫn về các màn hình khác); mọi ô có viền như Excel; cột có chữ A B C; kéo mép tiêu đề đổi được độ rộng, kéo thả tiêu đề đổi được thứ tự cột; thanh công cụ đủ mục (nhập, xuất, thêm dòng, thêm cột, thư mục, định dạng, lọc theo ô, ẩn cột, đặt lại cột); độ rộng, thứ tự, cột ẩn và thanh bên thu gọn nhớ trên trình duyệt | FR-7.8 | Thủ công |
| AC-11.19 | Dán nhiều ô (kể cả chữ tab từ Excel), kéo tay điền, xoá nội dung vùng chọn đi qua một đường dẫn lưu nhiều ô, được cả hoặc không gì: một ô sai thì 400 nêu đúng ô và không ô nào đổi; ô tràn xuống dòng trống thành bản ghi mới thuộc bộ phận sở hữu bảng; cột tính sẵn và cột trống bị bỏ qua, cột tính sẵn tính lại; quyền kiểm từng dòng ở máy chủ (Staff chỉ dòng của mình; Leader, Manager và Admin cả bộ phận — ADR-015; bảng chỉ xem thì 403) có ghi nhật ký từ chối; tối đa `GRID_PASTE_CELLS_MAX` ô một lần | FR-7.4 · FR-7.8 | Tự động |
| AC-11.20 | Hoàn tác (Ctrl+Z, nút ↶) trả lại giá trị cũ của các ô vừa dán, điền, sửa hay xoá nội dung; làm lại (Ctrl+Y) áp lại; ngăn xếp phía trình duyệt tối đa 100 bước, tải lại trang là hết | FR-7.4 | Tự động |
| AC-11.21 | Menu chuột phải có Cắt · Sao chép · Dán · Chèn N hàng trống · Xoá N hàng · Chèn N cột bên trái/phải · Xoá N cột · Xoá nội dung · Xoá định dạng (N theo vùng đang chọn, mục không có quyền mờ đi); Xoá hàng chỉ đánh dấu xoá (BR-4) sau hộp xác nhận, quyền = quyền sửa dòng kiểm từng dòng ở máy chủ (dòng người khác 403 có nhật ký, cả gói không xoá); Ctrl+Z ngay sau đó khôi phục đúng dòng về chỗ cũ, có nhật ký | FR-7.4 · BR-4 | Tự động |
| AC-11.22 | Quản lý của bộ phận sở hữu bảng (Leader, Manager — ADR-015, hoặc Admin) chèn N cột chữ ngắn bên trái hay bên phải cột đang chọn ngay trên lưới, thứ tự cột đánh lại theo vị trí mới; bỏ cột xoá định nghĩa nhưng giữ giá trị trong bản ghi; cột khoá, cột là vế của cột tính sẵn và cột hệ thống của bảng vận đơn bị từ chối; Staff 403 có nhật ký, Manager bộ phận khác 404 | FR-7.8 · BR-4 | Tự động |
| AC-11.23 | Sổ định dạng ô mở rộng theo mẫu demo mà vẫn là sổ đóng: nghiêng, gạch chân, gạch ngang, xuống dòng, viền, màu chữ và màu nền từ bảng 40 màu `m01…m40`, cỡ chữ 10–28, định dạng số (số, phần trăm, USD, VND, văn bản) hiện đúng trên ô số bằng `Decimal` mà giá trị thô không đổi; giá trị ngoài sổ vẫn bị từ chối | FR-7.8 · BR-8 | Tự động |
| AC-11.24 | Hộp lọc cột như demo: tên cột và số giá trị, ô tìm, danh sách giá trị kèm số dòng cho mọi kiểu cột, mục gập Điều kiện khác (khoảng hay chứa chữ, ô trống / có giá trị), bốn nút Chọn tất cả · Không chọn · Xóa lọc · Áp dụng; giá trị chọn gửi lên `f_<cột>__trong` và cộng dồn với bộ lọc khác | FR-7.2 | Tự động |
| AC-11.25 | Ô địa chỉ hiện `A1` hay `C3:F7` theo ô và vùng đang chọn, gõ địa chỉ + Enter thì nhảy tới ô đó; ô giá trị trên thanh công thức hiện giá trị thô, Enter lưu rồi xuống dòng; bấm một lần chỉ chọn ô, bấm đúp hoặc gõ chữ mới mở sửa với đúng ký tự vừa gõ; rời ô đang sửa mà đã đổi thì lưu | FR-7.4 | Tự động |
| AC-11.26 | Lưới hỏi máy chủ mốc mới nhất (thời điểm sửa gần nhất, số dòng, số cột — trong phạm vi người xem, không có dữ liệu) mỗi vài giây khi rảnh; người khác sửa thì thân bảng tự nạp lại và hiện báo Có dữ liệu mới; đổi số cột thì tải lại trang; bộ phận khác 404 | FR-7.1 | Tự động |
| AC-11.27 | Nhìn và thao tác như bảng tính KN Demo, đối chiếu ảnh `docs/tham-khao/kn-demo/`: khung tối viền vàng, thanh công cụ đúng thứ tự demo, thanh công thức có ô địa chỉ, cột số dòng, chữ cột A B C có nút ▼, hàng tên cột là hàng 1, cột trống tới Z, ô 25px có viền, chân trang có tab bảng và `+100 dòng`, nút ⛶ phóng toàn màn hình, trạng thái lưu ở thanh trên; kéo chuột chọn vùng thấy viền vàng và tay kéo điền | FR-7.9 · FR-7.12 | Thủ công |
| AC-11.30 | KN CRM là app riêng (dịch vụ `bangtinh`): ở KN ERP mục **KN CRM** trên thanh bên của mọi bộ phận là liên kết ngoài tới `BANGTINH_URL` mở tab mới, `/bang-tinh/` ở ERP không tồn tại (404); nút "Mở trong KN CRM" ở Bảng dữ liệu trỏ đúng bảng; ở KN CRM gốc `/` là trang chủ, các màn hình ERP không tồn tại, mục KN CRM là liên kết trong cùng tab | FR-7.13 · FR-3.6 | Tự động |
| AC-11.28 | Mục **Bảng tính** của KN CRM (trang thư mục `/thu-muc/`) là cây **Bộ phận ▸ Quý ▸ Tháng ▸ bảng** tự sinh từ cột Ngày của các bảng trong phạm vi quyền (`in_scope`): bộ phận nào không có bảng được xem thì không có nhánh, `bp` ngoài phạm vi 404, Admin thấy mọi bộ phận, bảng được cấp quyền Xem hiện với nhãn Xem; số dòng theo tháng đúng phạm vi cấp bậc; Manager của bộ phận thấy Cấp quyền và tạo thư mục; đếm theo tháng một truy vấn cho cả bộ phận, cả trang trong ngân sách truy vấn của lưới (14, K24) | FR-7.13 · FR-3.1 · FR-3.6 | Tự động |
| AC-11.29 | Tháng là **góc nhìn** trên một bảng: nút tháng mở lưới với `f_<cột Ngày>__lon_bang/__nho_bang` đúng ngày đầu và cuối tháng (kể cả năm nhuận), lưới trả đúng số dòng của tháng và ghi nhãn Tháng M/YYYY trên thanh trên, nút ← về đúng nhánh đang mở; bảng không có cột Ngày chỉ nằm ở Toàn bộ bảng; quý gõ tay chưa có dữ liệu vẫn mở với ba tháng trống | FR-7.13 · FR-7.2 | Tự động |
| AC-11.33 | **Leader như Manager trong bộ phận mình** (ADR-015): Leader của bộ phận sở hữu bảng tạo bảng (vào đúng bộ phận), sửa cột, chèn/bỏ cột trên lưới, tạo và sắp thư mục, nhập tệp, sửa và xoá dòng của người khác, xuất Excel; Staff bị từ chối có nhật ký; Leader bộ phận khác không thấy bảng (404), được cấp quyền Xem thì xem được nhưng đổi cấu trúc hay nhập tệp vẫn 403 có nhật ký; cấp quyền cho người khác vẫn chỉ Manager | FR-3.6 · FR-8.1 · FR-7.5 | Tự động |
| AC-11.31 | **Khung KN CRM có sidebar** (ADR-015, dáng Teeze): trang chủ `/` là tổng quan theo phạm vi quyền (dòng nhập tháng này và hôm nay, số bảng, tổng dòng, bảng cập nhật gần nhất, danh sách bảng có nút Mở, hoạt động gần đây — Staff chỉ đếm dòng của mình); sidebar trái có avatar + tên + cấp bậc, mục Trang chủ, Bảng tính gập được với mục con là từng bộ phận trong phạm vi (Sale không thấy Vận đơn), Tác vụ nền, KN ERP; trang có sidebar **không có nút ←**; logo KN CRM tự vẽ (`static/img/kn-crm.svg`) ở đầu menu trái và trên thanh trên của lưới, bấm là về trang chủ, favicon riêng của KN CRM còn KN ERP dùng logo KN JSC; chưa đăng nhập bị chuyển về đăng nhập; trong ngân sách truy vấn của lưới | FR-7.13 · FR-3.6 | Tự động |
| AC-11.32 | **Chỉ khi chủ động quay về mới thấy menu trái**: bấm Bảng tính trên sidebar mở trang thư mục (cây tháng, có sidebar); bấm một bảng mở lưới toàn màn hình không sidebar; nút ← của lưới về đúng trang thư mục và nhánh đang mở, không bao giờ về KN ERP; mục con bộ phận trên sidebar được đánh dấu đang chọn khi đang ở nhánh đó | FR-7.13 | Tự động |
| AC-11.34 | **Tạo bảng, sửa cột kèm cấp quyền, nhập tệp chạy ngay trong KN CRM** (ADR-015): cùng view của forms_builder, template kế thừa khung KN CRM có sidebar; sidebar có mục Nhập tệp (Leader trở lên) liệt kê bảng được nhập và mục Cấp quyền (Manager) liệt kê bảng bộ phận mình; Staff và Leader vào mục không được phép bị 403 có nhật ký; liên kết `bang`/`bang_xem` ở KN CRM dẫn về trang thư mục và lưới; Bảng dữ liệu `/bang/` vẫn không có ở KN CRM; ở KN ERP các màn này vẫn dùng khung ERP | FR-8.1 · FR-7.5 · FR-8.4 | Tự động |
| AC-11.35 | **Đổi cột tính sẵn trên bảng lớn thì tính lại ở tác vụ nền** (ADR-016): bảng nhiều hơn `RECOMPUTE_SYNC_MAX_ROWS` dòng thì thêm/sửa/bỏ cột tính sẵn hay cột mang nhãn tạo `BackgroundJob` "Tính lại cột" chạy theo lô `bulk_update`; cột hiện ngay, màn Sửa cột nói rõ có tác vụ nền, `moi-nhat/` trả tiến độ `tinh_lai` để lưới báo "Đang tính lại cột…" và nạp lại một lần khi xong; giá trị đúng khi xong; bảng nhỏ tính ngay tại chỗ, không có tác vụ | FR-7.9 | Tự động |
| AC-11.36 | **Lưới không phình theo số ô** (K27): 100 dòng × 39 cột ≤ 13 truy vấn, ô dựng bằng `grid_service.cell_html` với URL ghép chuỗi khớp `reverse('bang_tinh_o')`; cột Trùng đếm một truy vấn theo trang, `?trung=1` lọc bằng danh sách số điện thoại trùng (không subquery từng dòng); dán 500 ô ghi bằng `bulk_update` ≤ 25 truy vấn; `moi-nhat/` ≤ 8 truy vấn, không đếm dòng | NFR-1 | Tự động |

---

## 12. Tài liệu

Thư viện tài liệu chia theo mục — FR-9.1 tới FR-9.5, ADR-017.

| Mã | Tiêu chí | Yêu cầu | Loại |
|---|---|---|---|
| AC-12.1 | Manager tạo mục cho bộ phận mình và tải tệp lên mục trong phạm vi; Manager không tạo được mục toàn công ty, Admin tạo được; Staff và Leader gọi đường tải lên thì bị từ chối và có nhật ký; tên mục trùng chỉ khác hoa thường bị chặn ngay ở cơ sở dữ liệu, mục đã gỡ không giữ chỗ tên | FR-9.1 · FR-9.2 · FR-3.6 | Tự động |
| AC-12.2 | Staff thấy tài liệu toàn công ty và của bộ phận mình, không thấy của bộ phận khác; gọi thẳng đường tải về tài liệu bộ phận khác trả 404; Admin thấy tất cả; tải về đi qua view có kiểm quyền, trả tệp đính kèm đúng tên gốc và ghi nhật ký (mở liên kết cũng ghi); tệp mất trên đĩa thì báo lỗi, không 500; tài liệu đã gỡ trả 404 | FR-9.3 · FR-3.5 | Tự động |
| AC-12.3 | Tệp đổi đuôi, sai loại hoặc quá 10 MB bị từ chối; ZIP rác đổi đuôi `.docx` bị từ chối vì thiếu `word/document.xml`; Word nhận theo đuôi khai báo; tài liệu chỉ có liên kết tạo được; thiếu cả hai, có cả hai, hoặc liên kết sai giao thức thì từ chối | FR-9.2 · NFR-11 · NFR-12 | Tự động |
| AC-12.4 | Người tải, Manager của bộ phận và Admin gỡ được tài liệu (xoá mềm, có nhật ký); người khác bị từ chối có nhật ký; ngoài phạm vi là 404; gọi thẳng tầng dịch vụ bằng người không có quyền cũng bị từ chối, không trông vào view; thêm mục với mã bộ phận không phải số trả 404 | FR-9.4 · BR-4 | Tự động |
| AC-12.5 | Tệp tài liệu nằm ở `storage/tai-lieu/` và không bị tác vụ dọn tệp 24 giờ xoá | FR-9.5 | Tự động |

---

## 13. Bảng tin

Bảng tin chung của công ty — FR-10.1 tới FR-10.6, ADR-017.

| Mã | Tiêu chí | Yêu cầu | Loại |
|---|---|---|---|
| AC-13.1 | Ai đăng nhập cũng đăng được bài dạng chữ và thấy mọi bài, không phân theo bộ phận; bài ghim đứng đầu; bài trống hay quá dài bị từ chối và giữ lại bài đang gõ; danh sách phân trang 25 dòng; GET vào đường đăng trả 405; chưa đăng nhập bị chuyển về đăng nhập | FR-10.1 · FR-10.6 | Tự động |
| AC-13.2 | Bấm thích qua HTMX nhận về đúng nút mới với số lượt — nút là form thật nên không có JS vẫn dùng được, có `hx-sync` chống bấm đúp; bấm lại là bỏ thích, thích lại không sinh dòng mới; bình luận hiện dưới bài kèm số bình luận, gửi qua HTMX nhận về mảnh bình luận kèm số cập nhật tại chỗ; bài chỉ tải 20 bình luận mới nhất, cũ hơn tải tiếp qua HTMX; bình luận trống bị từ chối; đường dẫn trong bài thành liên kết; bài đã gỡ hay không có trả 404; mỗi tương tác một dòng nhật ký | FR-10.2 · FR-10.6 · BR-5 | Tự động |
| AC-13.3 | Manager và Admin ghim, gỡ ghim và gỡ được bài bất kỳ; tác giả gỡ được bài của mình; Staff hay Leader ghim hoặc gỡ bài người khác bị từ chối có nhật ký và không thấy nút; gỡ là xoá mềm; bình luận gỡ bởi người viết hoặc Manager trở lên; ghim gửi rõ ý muốn (ghim hay gỡ ghim) nên hai quản lý bấm trên trang cũ không làm ngược ý nhau | FR-10.3 · FR-3.5 · BR-4 | Tự động |
| AC-13.4 | Mỗi sáng hệ thống đăng thiệp cho người có sinh nhật hôm đó theo hồ sơ, mỗi người mỗi năm một thiệp; dịch vụ, lệnh và tác vụ nền chạy lại không nhân đôi, thiệp đã gỡ không đăng lại; tài khoản đã khoá không có thiệp; sinh 29.02 được chúc ngày 28.02 năm không nhuận; thiệp hiện trên Bảng tin với kiểu riêng và liên kết tới người được chúc; máy tắt vài ngày thì bật lại đăng bù (tối đa 14 ngày), không đăng cho ngày tương lai | FR-10.4 | Tự động |
| AC-13.5 | Thanh bên hiện sinh nhật tháng này theo ngày, năm người nhiều sao nhất, ba ghi nhận mới nhất và thành viên có hồ sơ tạo trong 30 ngày; trang Bảng tin và trang bài có dữ liệu chạy không quá 10 lệnh truy vấn | FR-10.5 · Q4 | Tự động |
| AC-13.6 | Bảng tin trên điện thoại: bài đọc được, bấm Thích và gửi bình luận được, thanh bên xếp xuống dưới bài, không tràn ngang | FR-10.1 · NFR-7 | Thủ công |

---

## 14. Công việc

Quản lý việc trong bộ phận — FR-11.1 tới FR-11.5, ADR-015.

| Mã | Tiêu chí | Yêu cầu | Loại |
|---|---|---|---|
| AC-14.1 | Staff tự giao cho mình, giao người khác bị từ chối; Leader giao trong team, người team khác bị từ chối; Manager giao cả bộ phận, không giao sang bộ phận khác; Admin giao được mọi người | FR-11.1 · FR-3.5 | Tự động |
| AC-14.2 | Staff thấy việc mình nhận hoặc tạo; Leader thấy việc của team; Manager cả bộ phận; Admin tất cả; gọi thẳng việc ngoài phạm vi trả 404 | FR-11.3 | Tự động |
| AC-14.3 | Người làm đổi trạng thái qua HTMX nhận về đúng một dòng bảng; chuyển sai bước trả 400 dạng chữ thường để trình duyệt hiện lý do; việc nhỏ chuyển thẳng Mới → Xong, Huỷ mở lại thành Mới; người cùng team không phải người làm bị 404 còn Leader đổi được; tham số quay về chỉ nhận đường dẫn trong hệ thống; mỗi lần một dòng nhật ký | FR-11.2 · BR-5 | Tự động |
| AC-14.4 | Tab Của tôi và Trong phạm vi; lọc theo trạng thái, người làm, ưu tiên, chỉ việc quá hạn; sắp theo hạn gần trước; Staff không thấy ô lọc Người làm vì chỉ có mình; danh sách phân trang 25 dòng và giữ bộ lọc qua trang | FR-11.4 | Tự động |
| AC-14.5 | Người tạo hoặc Leader trở lên sửa được việc (nhật ký ghi trường đổi; biểu mẫu sai thì lỗi hiện tại chỗ, không mất chữ; để trống người làm là giữ nguyên, đổi người làm thì việc sang bộ phận người đó); gỡ là xoá mềm bởi người tạo hoặc Manager; người làm không phải người tạo, hay Leader không phải người tạo, bị từ chối có nhật ký; gọi thẳng tầng dịch vụ cũng bị từ chối | FR-11.5 · BR-4 | Tự động |

---

## 15. Ghi nhận văn hoá

Ghi nhận, sao và bảng xếp hạng doanh số — FR-12.1 tới FR-12.5, ADR-017.

| Mã | Tiêu chí | Yêu cầu | Loại |
|---|---|---|---|
| AC-15.1 | Trưởng nhóm trở lên ghi nhận cấp dưới trong phạm vi mình (Leader: team, Manager: bộ phận, Admin: mọi người) theo một giá trị văn hoá, người nhận được cộng đúng một sao cùng giao dịch và có nhật ký; nhân viên không ghi nhận ai và không thấy form; ghi nhận người ngoài phạm vi, ngang hoặc trên cấp, chính mình, lời nhắn trống, giá trị lạ hay người đã khoá đều bị từ chối, thông báo nêu đúng ô sai; ô chọn chỉ có cấp dưới trong phạm vi; GET vào đường gửi trả 405 — Q75 | FR-12.1 · FR-12.2 · BR-5 | Tự động |
| AC-15.2 | Bảng xếp hạng gộp đơn tháng này theo người bán, quy về VND bằng tỉ giá cố định trong cấu hình, xếp theo tổng rồi số đơn; đơn đã bỏ và đơn tháng trước không tính; mọi bộ phận xem được nhưng không thấy mã đơn; thiếu tỉ giá thì báo lỗi, không trả số sai; người bán đã khoá không chiếm hạng; bằng tổng và bằng số đơn thì đồng hạng 1, 1, 3 (Q77); mọi người bán kể cả quản lý đều tranh hạng (Q76); người bán nhiều loại tiền được gộp về VND; dữ liệu mẫu ra đúng số ghi ở `docs/07` | FR-12.3 · BR-8 | Tự động |
| AC-15.3 | Ngày 1 hằng tháng những người ở hạng 1, 2, 3 kỳ trước nhận 5, 3, 1 sao, đồng hạng cùng nhận; lệnh và tác vụ nền chạy lại không nhân đôi, kỳ `2026-9` và `2026-09` là một; kỳ sai định dạng bị từ chối; mỗi lần chạy một dòng nhật ký ghi tỉ giá và tổng từng người | FR-12.4 · BR-5 | Tự động |
| AC-15.4 | Trang thành viên hiện tổng sao mọi kỳ, sao kỳ này, sao theo tháng và ghi nhận nhận được phân trang 25 dòng; bảng Nhiều sao nhất xếp theo tổng sao; thành viên không có hoặc đã khoá trả 404 | FR-12.5 · FR-12.2 | Tự động |

---

## 16. Tài nguyên

Danh mục tài nguyên dùng chung — FR-13.1 tới FR-13.4, ADR-017.

| Mã | Tiêu chí | Yêu cầu | Loại |
|---|---|---|---|
| AC-16.1 | Tài nguyên chia theo mục BM, Via, Page…; mọi cấp bậc, mọi bộ phận xem được cả danh sách với trạng thái là chip; lọc theo mục, trạng thái, người giữ và tìm theo tên; mục hay người giữ không có trả 404; Xoá lọc giữ mục đang chọn; danh sách phân trang 25 dòng; Manager trở lên thêm mục, Staff và Leader bị từ chối có nhật ký; trùng tên kể cả khác hoa thường bị chặn ở cả dịch vụ lẫn cơ sở dữ liệu, mục mới xếp cuối | FR-13.1 · FR-13.2 · FR-3.5 | Tự động |
| AC-16.2 | Manager trở lên thêm, sửa, gỡ tài nguyên; sửa ghi nhật ký từng trường đổi nhưng không chép ghi chú; gỡ là xoá mềm; Staff và Leader bị từ chối có nhật ký và không thấy nút; tài nguyên đã gỡ trả 404; người giữ đã bị khoá vẫn hiện trong ô chọn khi sửa nên bấm Lưu không mất người giữ | FR-13.3 · FR-3.5 · BR-4 · BR-5 | Tự động |
| AC-16.3 | Tên, ghi chú hay liên kết chứa mật khẩu, token, mã bí mật, hoặc OTP/2FA/PIN/mk kèm số đều bị từ chối ở cả thêm lẫn sửa, kể cả gõ dấu rời (NFD); nhắc tới OTP hay 2FA mà không kèm mã thì được; liên kết không phải http(s) bị từ chối ở tầng dịch vụ; không có cột mật khẩu trong bảng; nhật ký không chứa ghi chú | FR-13.4 · BR-6 | Tự động |

---

## 17. Kiểm thử thủ công trước bàn giao

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

## 18. Điều kiện coi là hoàn thành phase 1

| # | Điều kiện |
|---|---|
| 1 | Toàn bộ tiêu chí đánh dấu **Tự động** đều có bài kiểm thử và đều đạt |
| 2 | Ma trận kiểm chéo phân quyền ở mục 3 được kiểm đầy đủ, cả trường hợp cho phép và từ chối |
| 3 | Toàn bộ danh sách kiểm thủ công ở mục 17 đã thực hiện và đạt |
| 4 | Đã phục hồi thành công ít nhất một lần từ bản sao lưu |
| 5 | Tệp Excel thật của công ty nhập được mà không cần chỉnh sửa thủ công |
| 6 | Ba vai trò đã chạy trọn quy trình trên dữ liệu thật |
| 7 | Tài liệu hướng dẫn sử dụng và vận hành đã bàn giao |

**Không bỏ qua** các tiêu chí thuộc mục 3 và mục 9 với lý do sẽ sửa sau.
Lỗi phân quyền dẫn tới rò rỉ dữ liệu, và dữ liệu đã lộ thì không thu hồi được.

---

## 19. Nội dung chưa quyết định

| # | Nội dung | Ảnh hưởng |
|---|---|---|
| 1 | ~~Tiêu chí cho công thức trên bảng~~ | Đã chốt 29.08.2026 — ADR-006, thành AC-7.10 tới AC-7.12 |
| 2 | Số lượng bài kiểm thử tự động tối thiểu | Có nên đặt ngưỡng tỉ lệ bao phủ không |
| 3 | ~~Công cụ đo hiệu năng khi kiểm AC-10.1~~ | Đã chốt 03.09.2026 — Locust, chỉ dùng khi kiểm thử (backlog Q44, K6 đóng) |

## 20. Vận đơn mới theo CRM Tân — ADR-018

| Mã | Đạt khi | Yêu cầu | Kiểm bằng |
|---|---|---|---|
| AC-18.1 | Khởi tạo máy sạch và cập nhật máy có dữ liệu đều có hai bảng; chạy lại không trùng, bảng cũ giữ dữ liệu/ID/liên kết/quyền; bảng mới trống, chỉ sao quyền đang hiệu lực một lần | ADR-018 | Tự động |
| AC-18.2 | Tạo ở ERP/CRM sinh đúng một dòng bảng mới và chi tiết cùng giao dịch; lỗi chi tiết hoàn tác cả đơn; ngày Việt Nam, người bán từ tài khoản | FR-6.3 · ADR-018 | Tự động |
| AC-18.3 | Chi tiết nhiều sản phẩm, tiền thu từng sản phẩm, tổng/trạng thái khớp; số tiền chính xác, sửa bản sao không đổi ERP; editor cũ không ghi đè, audit không chứa thông tin khách | ADR-018 · BR-3 · BR-8 | Tự động |
| AC-18.4 | Ba cấp bậc và Admin kiểm cả hai chiều trên khu nhập, chi tiết GET/POST, thống kê; quyền lên đơn không cấp quyền xem bảng, chỉ có quyền xem không sửa được | FR-3.5 · ADR-018 | Tự động |
| AC-18.5 | Ô tổng và trạng thái tự tính không sửa trực tiếp/dán đè; gói dán có ô cấm hoàn tác cả gói; cột chuẩn không đổi cấu trúc hoặc bị xoá | ADR-018 | Tự động |
| AC-18.6 | Thống kê theo toàn bộ bộ lọc và quyền, bốn kiểu nhóm; tách tiền, distinct đơn, nhóm mã sản phẩm; sửa, xoá mềm, khôi phục phản ánh đúng, Hủy/Hoàn không bị bỏ ngầm | ADR-018 | Tự động |
| AC-18.7 | Xuất/nhập lại bảo toàn chi tiết và tiền; dòng thiếu chi tiết, tổng không khớp hoặc mã sản phẩm lạ báo lỗi xem trước, không tự phân bổ | FR-7.5 → FR-7.7 · ADR-018 | Tự động |
| AC-18.8 | Bảng chỉ có Vận hành đơn, Thống kê và tiêu đề nhóm; không có form hoặc yêu cầu tải Lên đơn nhúng. Thống kê thu gọn được, ô tổng mở chi tiết, không có Blacklist; 390px cuộn trong lưới. Hai trang Lên đơn riêng hoạt động như trước | ADR-018, ADR-019 | Tự động |
