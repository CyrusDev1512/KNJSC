# Tiêu chí nghiệm thu

## AC-26 — Trạng thái và chứng từ thanh toán (12.09.2026)

| Mã | Đạt khi |
|---|---|
| AC-26.1 | Ba trạng thái sửa trực tiếp qua autosave/CAS/history/Undo; sửa tiền không ghi đè trạng thái; dữ liệu cũ giữ nguyên |
| AC-26.2 | Vận đơn thêm theo phạm vi; Kế toán/Admin quản lý chứng từ; quyền đọc Kế toán không thành quyền sửa ô/phân công |
| AC-26.3 | Ref giữ số 0 đầu, duy nhất trong đơn đang hiệu lực; replay tạo không trùng; sửa đồng thời có CAS; xóa mềm/khôi phục không mất file |
| AC-26.4 | JPG/PNG tối đa 5 ảnh và 10 MB/lượt; ảnh riêng tư có kiểm quyền; lỗi lưu dọn file mới; không chuyển chứng từ sang đơn khác |
| AC-26.5 | Bill hiển thị tối đa hai Ref và đường xem đủ; giữ Bill cũ; tìm/lọc/Excel đúng phạm vi, không nhúng ảnh |
| AC-26.6 | Chrome 1440/1280/390: chọn/dán ảnh, tạo/sửa/xem, X/Escape; 10k dòng không tải ảnh khi mở/cuộn; metadata một truy vấn/khối; cache ≤10 |

[Quyết định](quyet-dinh/025-trang-thai-va-chung-tu-thanh-toan.md) ·
[Kết quả và giới hạn](kiem-chung-chung-tu-thanh-toan-20260912.md).

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

Mỗi ô là một bài kiểm thử. Năm vai trò nhân với mười đường dẫn chính — 50 ô, thêm hai dòng ngày 03.09.2026 (nhập tệp và Bảng tính) và một dòng ngày 17.09.2026 (thư viện tài liệu).

Hai ô đáng chú ý sau ADR-023. **Màn hình lên đơn** không còn mở ngay tại KN ERP: người có quyền được chuyển sang KN CRM, người không có quyền vẫn bị từ chối tại chỗ. **Thư viện biểu mẫu và tài liệu** dùng chung đường dẫn `/bieu-mau/`: mở ra là tab Tài liệu, ai đăng nhập cũng vào được; tab quản lý biểu mẫu `?tab=forms` vẫn chỉ Manager trở lên, gọi thẳng bằng vai khác trả lỗi từ chối. Từ ADR-036 (một bảng vận đơn) **Bảng tính vận đơn** với Sale các cấp là "Chuyển Lên đơn": lưới `van_don` đưa họ sang `/van-don/len-don/` tại CRM thay vì 404.

| Đường dẫn | Staff Sale | Leader Sale | Manager Sale | Staff Vận đơn | Chưa đăng nhập |
|---|---|---|---|---|---|
| Báo cáo của chính mình | Vào được | Vào được | Vào được | Vào được | Chuyển đăng nhập |
| Báo cáo người cùng team | Từ chối | Vào được | Vào được | Từ chối | Chuyển đăng nhập |
| Báo cáo team khác cùng bộ phận | Từ chối | Từ chối | Vào được | Từ chối | Chuyển đăng nhập |
| Báo cáo bộ phận khác | Từ chối | Từ chối | Từ chối | Từ chối | Chuyển đăng nhập |
| Màn hình lên đơn | Chuyển sang KN CRM | Chuyển sang KN CRM | Chuyển sang KN CRM | Từ chối | Chuyển đăng nhập |
| Bảng vận đơn | Từ chối | Từ chối | Từ chối | Vào được | Chuyển đăng nhập |
| Quản lý biểu mẫu (`?tab=forms`) | Từ chối | Từ chối | Vào được | Từ chối | Chuyển đăng nhập |
| Nhập tệp vào bảng của Sale | Từ chối | Vào được | Vào được | Từ chối | Chuyển đăng nhập |
| Bảng tính vận đơn | Chuyển Lên đơn | Chuyển Lên đơn | Chuyển Lên đơn | Vào được | Chuyển đăng nhập |
| Thư viện tài liệu (`/bieu-mau/`) | Vào được | Vào được | Vào được | Vào được | Chuyển đăng nhập |

---

## 4. Báo cáo hằng ngày

| Mã | Tiêu chí | Yêu cầu | Loại |
|---|---|---|---|
| AC-4.1 | Mỗi bộ phận thấy biểu mẫu riêng của mình, không thấy biểu mẫu bộ phận khác | FR-4.1 | Tự động |
| AC-4.2 | Nộp báo cáo thì thời điểm nộp được ghi lại chính xác | FR-4.2 | Tự động |
| AC-4.3 | Người dùng xem lại được danh sách báo cáo cũ của mình | FR-4.3 | Tự động |
| AC-4.4 | Báo cáo đã nộp không sửa được ngoài luồng sửa có lịch sử (ADR-032): Staff gọi thẳng đường dẫn sửa bị chặn, ghi bằng mã bị chặn; nộp lại cùng ngày không đè bản cũ (ADR-038) | FR-4.4 | Tự động |
| AC-4.5 | Leader xem được báo cáo của người trong team | FR-4.5 | Tự động |
| AC-4.6 | Trường mang nhãn Người bán trên biểu mẫu và báo cáo ngày được hệ thống tự ghi **mã nhân sự** người gửi (ADR-037; chưa gán mã thì tên đăng nhập); gửi giá trị khác trong yêu cầu cũng không đổi được; ô trên màn hình chỉ đọc, không gửi lên | FR-4.6 | Tự động |
| AC-4.7 | Một người nộp cùng biểu mẫu nhiều lần trong ngày được: mỗi lần một bản riêng với thời điểm nộp riêng, không chặn, không đè; màn nộp cho biết hôm nay đã nộp bao nhiêu lần (ADR-038 thay khoá một bản/ngày) | FR-4.2 | Tự động |
| AC-4.8 | Kế toán thấy báo cáo của mọi bộ phận trong Lịch sử, mở và sửa được có `ReportRevision`, giữ người nộp và ngày; không bỏ được báo cáo của người khác; nhân viên bộ phận khác vẫn bị 404 ở xem lẫn sửa | FR-4.4 · FR-4.5 · ADR-038 | Tự động |

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
| AC-6.10 | Cùng số điện thoại nhưng gõ tên khác: đơn mới ghi **tên vừa gõ**, danh bạ đổi theo và có nhật ký; đơn cũ giữ nguyên tên lúc đó; số điện thoại khác nhau thì mỗi đơn mang tên của mình; ô Facebook/Email bỏ trống không xoá dữ liệu đã có ; trước khi lưu, lời nhắc khách báo trước "sẽ đổi tên khách của số …" kèm cả tên cũ lẫn tên đang gõ, và mảnh nhắc mang sẵn tên để ô Tên khách tự điền khi đang trống | FR-6.7 | Tự động |
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
| AC-10.9 | `manage.py nap_khach_mau --bang <mã> --so-khach N` nạp N khách giả (mã đơn `KH-*`) theo lô 2.000 vào bảng vận đơn chỉ định (mặc định Vận đơn mới `van_don`, ADR-036): số dòng = N ÷ (1 − tỉ lệ mua lại, mặc định 20 %), mỗi khách ít nhất một dòng, khách mua lại dùng lại số điện thoại để cột Trùng có việc, bảng có profile Vận đơn thì mỗi dòng có phân công Vận đơn/CSKH; `--xoa-cu` xoá sạch dòng `KH-*`; DEBUG tắt thì từ chối như `seed_perf` | NFR-2 | Tự động |

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
| AC-11.9 | Nhập tệp vận đơn thật (ẩn danh) không chỉnh sửa: 221 dòng vào, 0 lỗi (PTTT "Cheque" thuộc bảy PTTT theo sheet Vận đơn, bổ sung ADR-031), trạng thái và thanh toán khớp danh sách (kể cả nhãn cũ, khác hoa thường), điện thoại là chuỗi | FR-7.5 | Tự động |
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
| AC-11.37 | **1.000 dòng trống sẵn để nhập** (góp ý 17.09.2026): mở bảng có quyền thêm thì cuối lưới có sẵn 1.000 dòng trống, chân trang ghi số dòng trống; gõ một dòng thành bản ghi thật **không tải lại khối JSON**, dòng trống được bù đủ; tới dòng trống áp chót thì thêm 1.000 dòng nữa; tải lại trang chỉ còn dòng thật | FR-7.4 | Tự động |
| AC-11.38 | **Cột ghim đứng đầu thứ tự nhìn thấy**: cột ghim không ở đầu thứ tự cột (người dùng đổi thứ tự, hoặc bảng vận đơn có Mã đơn/Tên khách/SĐT ở giữa) vẫn được xếp lên đầu khi vẽ — không ô trống ở vị trí gốc, không che cột đứng trước; vùng chọn, phím mũi tên và địa chỉ `A1:E2` theo đúng thứ tự trên màn hình | FR-7.4 | Tự động |
| AC-11.39 | ~~**Bảng nhận đơn liệt kê mọi bảng vận đơn đang có** (ADR-034): `van_don` cũ, bảng đang nhận và bảng bộ phận Vận đơn có cột Mã đơn đúng cấu trúc; bảng báo cáo cùng bộ phận và bảng bộ phận khác không hiện; bảng chưa đủ điều kiện hiện kèm lý do và không chọn được (400)~~ **Bỏ theo ADR-036 (18.09.2026): một bảng vận đơn, không còn Bảng nhận đơn / Vận đơn DB** | ADR-029 · ADR-034 | Tự động |
| AC-11.41 | Hộp lọc cột có nền, khung và danh sách giá trị cuộn được, không đè lên lưới; không chú thích CSS nào nuốt luật (quên `*/` ở dòng tiêu đề mục); lớp chỉ khai trong chú thích không tính là đã khai | FR-7.3 | Tự động |
| AC-11.42 | Ô tìm trong mảnh lọc cột trỏ vào ruột hộp chứ không vào cả `#hop-loc`: đổi sang cột khác thì hộp hiện đúng giá trị của cột đó, không sót mục của cột trước | FR-7.3 | Tự động |
| AC-11.43 | Hộp lọc cột chọn công cụ theo số giá trị thật: dưới ngưỡng thì giữ danh sách ô tích và ghi đúng tổng; vượt ngưỡng thì mở sẵn ô gõ chữ, danh sách ô tích gập lại và không bày hai ô cùng công dụng; `dem_gia_tri` đếm đúng cho cột tách, cột JSON và khi có ô tìm | FR-7.3 | Tự động |
| AC-11.40 | **Gõ rồi Enter không giật**: dòng nháp thành bản ghi được nối tại chỗ trong cùng một bước (tổng dòng và chiều cao lưới không đổi từng dòng, dòng trống chỉ bù theo đợt, không thanh thông báo đẩy lưới); phản hồi lưu mang mốc `moi-nhat` để lưới không coi mốc do mình vừa lưu là người khác sửa; khi người khác sửa thật thì tải lại **mềm** — giữ ô cũ tới khi khối mới về, không hoá `…` | FR-7.4 · AC-11.26 | Tự động |

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
| AC-18.1 | Khởi tạo máy sạch và chạy lại trên máy có dữ liệu đều chỉ có **một** bảng vận đơn `van_don` "Vận đơn mới" (ADR-036): chạy lại không sinh bảng thứ hai, dòng/ID/quyền cũ giữ nguyên, không gieo đơn demo | ADR-018 · ADR-036 | Tự động |
| AC-18.2 | Tạo ở ERP/CRM sinh đúng một dòng bảng mới và chi tiết cùng giao dịch; lỗi chi tiết hoàn tác cả đơn; ngày Việt Nam, người bán từ tài khoản | FR-6.3 · ADR-018 | Tự động |
| AC-18.3 | Chi tiết nhiều sản phẩm, tiền thu từng sản phẩm, tổng/trạng thái khớp; số tiền chính xác, sửa bản sao không đổi ERP; editor cũ không ghi đè, audit không chứa thông tin khách | ADR-018 · BR-3 · BR-8 | Tự động |
| AC-18.4 | Ba cấp bậc và Admin kiểm cả hai chiều trên khu nhập, chi tiết GET/POST, thống kê; quyền lên đơn không cấp quyền xem bảng, chỉ có quyền xem không sửa được | FR-3.5 · ADR-018 | Tự động |
| AC-18.5 | Ô tổng và trạng thái tự tính không sửa trực tiếp/dán đè; gói dán có ô cấm hoàn tác cả gói; cột chuẩn không đổi cấu trúc hoặc bị xoá | ADR-018 | Tự động |
| AC-18.6 | Thống kê theo toàn bộ bộ lọc và quyền, bốn kiểu nhóm; tách tiền, distinct đơn, nhóm mã sản phẩm; sửa, xoá mềm, khôi phục phản ánh đúng, Hủy/Hoàn không bị bỏ ngầm | ADR-018 | Tự động |
| AC-18.7 | Xuất/nhập lại bảo toàn chi tiết và tiền; dòng thiếu chi tiết, tổng không khớp hoặc mã sản phẩm lạ báo lỗi xem trước, không tự phân bổ | FR-7.5 → FR-7.7 · ADR-018 | Tự động |
| AC-18.8 | Bảng chỉ có Vận hành đơn, Thống kê và tiêu đề nhóm; không có form hoặc yêu cầu tải Lên đơn nhúng. Thống kê thu gọn được, ô tổng mở chi tiết, không có Blacklist; 390px cuộn trong lưới. Hai trang Lên đơn riêng hoạt động như trước | ADR-018, ADR-019 | Tự động |
| AC-18.9 | ~~Máy sạch có thêm bảng động độc lập `van_don_db`, đúng 26 cột theo cấu hình 14.09.2026; Ngày thanh toán đứng đầu nhóm thanh toán; chạy lệnh khởi tạo nhiều lần không trùng bảng/cột và không tạo dữ liệu~~ **Bỏ theo ADR-036 (18.09.2026): một bảng vận đơn, không còn Bảng nhận đơn / Vận đơn DB** | Cấu hình Vận đơn DB 14.09.2026 | Tự động |

## 21. Feedback Vận đơn mới — ADR-020

Các tiêu chí này thay giả định thấy toàn bộ hàng đợi của nhân viên Vận đơn
ở AC-18.4 trên bảng mới. AC-18.7 chỉ nhập lại phần dữ liệu nghiệp vụ;
phân công trong file không được dùng để cấp quyền.

| Mã | Đạt khi | Yêu cầu | Kiểm bằng |
|---|---|---|---|
| AC-20.1 | Leader/Manager Vận đơn và Admin phân công; nhân viên Vận đơn thấy và sửa mọi dòng (ADR-033 thay điều "chỉ đơn được giao"), Sale thấy đơn mình tạo; CSKH chỉ bổ sung xem; grant bảng/Marketing không vượt phạm vi; đọc chung ERP và số đếm tuân thủ | ADR-020 · ADR-033 | Tự động |
| AC-20.2 | Ba người phụ trách là tài khoản hoạt động đúng bộ phận, mã/họ tên hiển thị; chặn ô/dán/nhập ghi phân công; người cũ không ghi được dữ liệu đã đọc trước khi chuyển giao | ADR-020 | Tự động |
| AC-20.3 | Một/nhiều dòng, giữ/đổi/bỏ từng trường; hai request đồng thời không ghi đè, phiên bản cũ trả 409, lỗi rollback cả lượt, audit không thông tin khách | ADR-020 | Tự động |
| AC-20.4 | Lọc AND/OR đúng, mã sản phẩm chi tiết không nhân dòng; Quốc gia/Marketing và chưa gán đúng; ngày và trạng thái độc lập; lựa chọn/thống kê trong phạm vi | ADR-020 | Tự động |
| AC-20.5 | Xuất toàn kết quả lọc/ngày, mã nhân viên phân biệt trùng tên, dòng thiếu Order để trống mã Sale; trực tiếp/nền đồng nhất, worker và tải lại kiểm quyền | ADR-020 | Tự động |
| AC-20.6 | Desktop/mobile không tràn trang; bàn phím mở phân công, chọn nhiều dòng, lỗi xung đột có cách tải lại; URL giữ lọc/sắp xếp, trạng thái rỗng rõ; không có Lên đơn nhúng | ADR-020 | Tự động |
| AC-20.7 | Migration xuôi/ngược trên DB test bảo toàn đơn/dòng/chi tiết, không tự phân công; lưới 100 dòng không truy vấn riêng từng dòng | ADR-020 | Tự động |


## 22. Lưới master và Thống kê KN CRM — ADR-021

AC-21.1 thay AC-18.8 về Vận hành đơn/tiêu đề nhóm/thống kê nhúng; giữ các
quyền và hợp đồng dữ liệu của AC-18/20. Các bảng khác tiếp tục tiêu chí cũ.

| Mã | Đạt khi | Yêu cầu | Kiểm bằng |
|---|---|---|---|
| AC-21.1 | Chỉ bảng mới chạy controller riêng, không form Lên đơn/thống kê nhúng/thanh công thức; hàng mặc định 28px, kéo 28–400px và xuống dòng; ghi nhớ theo user/bảng/ID local, Escape hủy/↑↓/Home; cuộn/neo đồng bộ, reader/editor không tự giãn hàng | ADR-021 | Tự động |
| AC-21.2 | Khối 100/cache 10, DOM hữu hạn; chọn/đi xuyên khối, Ctrl+A toàn kết quả, copy/dán ≤2.000 ô giữ số 0 đầu; sai/khóa không ghi phần, không tạo dòng; IME đúng; nhập trong ô không che hàng dưới, Admin sửa trạng thái/ngày ngay trong ô (lưới luôn chỉnh sửa, ADR-033), rê nhẹ vẫn mở và lỗi danh sách chọn không khóa ô khác | ADR-021 · bổ sung 11.09.2026 | Tự động |
| AC-21.3 | Tự lưu nền sau kết thúc nhập, gộp 500ms/tối đa 2s; vẫn sửa được khi lưu; Ctrl+S gửi ngay; tối đa 2.000 ô/lượt; CAS cùng ô trả 409, khác ô giữ cả hai; UUID gửi lại không ghi hai lần, UUID khác nội dung bị từ chối; batch atomic, audit không nội dung khách | ADR-021 | Tự động |
| AC-21.4 | Mọi đọc/ghi/copy chưa tải/poll theo scope, thu quyền không trả dòng hoặc ghi bản nháp; lọc/sắp xếp ổn định, phản hồi cũ bị bỏ; đổi lọc/popup giữ nháp, X luôn thấy được; lỗi lưu giữ nội dung, rời/tải lại bảng cảnh báo nếu còn thay đổi chưa xác nhận | ADR-021 | Tự động |
| AC-21.5 | Thống kê riêng, biểu đồ/tổng hợp toàn kết quả lọc, tiền tách loại; top 10 nhưng đối chiếu đủ nhóm; trạng thái trống/partial, đơn thiếu chi tiết đúng; link/redirect giữ lọc | ADR-021 | Tự động |
| AC-21.6 | Desktop 1440/laptop 1280/mobile 390/zoom 125% không vỡ; cuộn sâu, chọn/đọc/resize p95 ≤100ms; HTTP 100k/300k ×10/20 người đọc p95 ≤1s, ghi ≤0,5s, cache/DOM/bộ nhớ hữu hạn | ADR-021 · ADR-016 | Tự động |
| AC-21.7 | Migration biên nhận/lịch sử và chỉ mục master xuôi/ngược trên DB test không đổi dữ liệu đơn/phân công; hồi quy lưới cũ, Lên đơn ERP/CRM, chi tiết, nhập/xuất nền/direct và quyền trước tải | ADR-021 | Tự động |
| AC-21.8 | Mặc định Xem; Chỉnh sửa mở nhập khi bấm/chuyển ô, giữ mũi tên trong chữ và thao tác chọn vùng; hàng được chọn và viền dùng xanh dương; số dòng đầu là 1; mặc định đơn cũ trước/mới cuối, khóa phụ ID | ADR-021 | Tự động |
| AC-21.9 | Cỡ chữ/màu chữ/màu nền giữ thuộc tính khác; CAS riêng từng thuộc tính; định dạng/Undo/Redo nguyên tử; phản hồi lượt cũ không xóa nháp mới, retry giữ UUID/nội dung; lỗi quyền/kiểu/xung đột không retry tự động | ADR-021 | Tự động |
| AC-21.10 | Lịch sử chỉ nối thêm, trước/sau theo ô, tài khoản/thời điểm/nhóm thao tác; 50 mục/trang, kiểm quyền hiện hành, replay không trùng; xung đột đối chiếu trong phiên và gửi lại bằng CAS mới, không ghi đè cưỡng bức | ADR-021 | Tự động |
| AC-21.11 | Admin CRM bắt buộc chọn Sale hoạt động/hợp lệ; creator là Admin, seller/phòng ban/team theo Sale; Sale đọc đơn đứng tên; người khác không giả mạo seller; lỗi tạo đơn/chi tiết/vận đơn rollback cả lượt | ADR-021 | Tự động |

## 23. Bàn điều hành KN CRM — ADR-022

AC-22 thay phần đích Thống kê Vận đơn riêng của AC-21.5; giữ nguyên hợp đồng
lưới, bộ lọc và dữ liệu Vận đơn của AC-18/20/21.

| Mã | Đạt khi | Yêu cầu | Kiểm bằng |
|---|---|---|---|
| AC-22.1 | `/thong-ke/` tổng hợp tối đa một nguồn mỗi profile; `nguon` phân tích đúng một bảng; mọi bảng hoạt động trong scope đều chọn được; mặc định nguồn cập nhật gần nhất và ưu tiên `van_don` | ADR-022 | Tự động |
| AC-22.2 | Nhận diện đúng Vận đơn mới → Marketing → Sale → Chung; bảng cũ có ghi chú lịch sử; thiếu nhãn Ngày được liệt kê, không tự đoán | ADR-022 | Tự động |
| AC-22.3 | Kỳ trước cùng số ngày; CPO/AOV/tỷ lệ dùng tổng có trọng số; kỳ trước 0 không sinh vô cực; tiền tách loại hoặc ghi đơn vị theo bảng | ADR-022 · BR-3 | Tự động |
| AC-22.4 | Sale–Vận đơn chỉ đối chiếu tổng cùng kỳ, chênh lệch ghi cần đối chiếu; mỗi màn hình tối đa ba insight đúng thứ tự, trung tính, có bằng chứng/nguồn/link ngày và trạng thái tương ứng | ADR-022 | Tự động + trình duyệt |
| AC-22.5 | Staff/Leader/Manager/Admin chỉ thấy đúng scope trên danh sách, aggregate và link; mã ngoài scope/ngừng dùng trả 403 có audit; owner username không phải Admin không được nâng giao diện hoặc quyền | ADR-022 · FR-3.5 | Tự động |
| AC-22.6 | Ngày sai hoặc `tu > den` hiện lỗi và không aggregate; một profile lỗi không che phần khác; bảng rỗng/partial/thiếu chi tiết vẫn có trạng thái rõ | ADR-022 | Tự động |
| AC-22.7 | Biểu đồ đúng bộ theo profile, ≤10 nhóm và bảng đối chiếu phân trang đủ; ngày/tuần/tháng theo 45/180 ngày; cột 2.5D không sai tỷ lệ, đường phẳng, có title/nhãn/bảng/focus/reduced-motion | ADR-022 | Tự động + trình duyệt |
| AC-22.8 | Sidebar hiện khi có bất kỳ bảng nào; Trang chủ CRM và Báo cáo tổng hợp ERP chỉ thêm link; xuất Excel ERP và `f_*`/`group`/phân trang/redirect Vận đơn cũ không hồi quy | ADR-022 · ADR-014 | Tự động |
| AC-22.9 | Query không tăng theo số dòng hoặc toàn bộ bảng ngoài ba nguồn; p95 đọc ≤1 giây trên 100k/300k Vận đơn và 20k Sale; không có dependency, cache, polling hoặc tác vụ nền mới | ADR-022 · ADR-016 | Tự động + hiệu năng |
| AC-22.10 | **Tổng hợp có cột Nhân sự và Leader, nhóm theo ngày × nhân sự** (ADR-035, bổ sung 19.09): mỗi người một hàng trong ngày, ngày lặp lại ở từng hàng; cột Nhân sự là **mã nhân sự** (chỉ mã, không họ tên — `employee_code`, chưa có mã thì tên đăng nhập; người lập dòng; Vận đơn: người được phân công), Leader là mã `Team.leader` của người đó; ô chọn Nhân sự và chip bộ lọc vẫn `MÃ · Họ tên` (ADR-037 bổ sung 18.09), ngay sau cột Ngày; Theo nhân viên thêm cột Leader; Staff chỉ thấy dòng của mình, Leader team mình, Manager cả bộ phận, Admin tất cả; lọc `nhan_su` thu hẹp bảng, người ngoài phạm vi 403; Excel cùng cột, dòng tổng để trống ô danh tính; vẫn ≤ 10 truy vấn | ADR-022 · ADR-035 · FR-3.5 | Tự động |
| AC-22.11 | Báo cáo hoạt động phân trang mặc định **100 nhóm mỗi trang** (vẫn trong 25/50/100), dòng "Tổng trong bộ lọc" tính trên toàn bộ kết quả; bảng theo token 13px, ô đệm 5×8 px, khung cao theo màn hình | ADR-035 · Quy tắc 1 | Tự động + trình duyệt |
| AC-22.12 | **Cột Loại tiền của bảng báo cáo nhận đủ USD/CAD/PHP** (TL-41, 18.09.2026): `configure_erp_reports` gặp cột `loai_tien` có sẵn (kịch bản mẫu 15.09 chỉ có VND) thì bổ sung ba mã tiền theo quốc gia, giữ giá trị cũ và tên cột, chạy lại không đổi; cột không phải Chọn một thì báo lỗi; sau đó nộp báo cáo với Quốc gia Canada được nhận và Loại tiền = CAD | ADR-031 · ADR-022 | Tự động |
| AC-22.13 | **Bố cục Báo cáo tổng hợp theo bản vẽ 18.09**: bộ lọc ba trạng thái qua `data-filters` (mở 260px, thanh dọc 48px có huy hiệu số bộ lọc, dưới 900px là ngăn kéo mặc định đóng), nhớ trong phiên `{filters, focus}` và đọc được khoá cũ; Toàn màn hình tự chuyển thanh dọc, Escape đóng ngăn kéo trước rồi thoát toàn màn hình; hàng chip bộ lọc đang áp (kể cả Tệp khách hàng) với × bỏ đúng tham số và Xóa lọc; giữ Chọn nhanh kỳ; tiêu đề, dòng Tổng ghim trên, cột định danh ghim trái theo lớp tổng quát `.report-identity` với chiều rộng bằng biến CSS, ô định danh xuống dòng không cắt chữ, ô số `nowrap`; Toàn màn hình: khung bảng nằm trong viewport (grid hàng `minmax(0,1fr)`), thanh kéo ngang và phân trang luôn thấy, không tràn | ADR-035 · ADR-038 · NFR-7 | Tự động + trình duyệt |
| AC-22.14 | **Cách xem Tổng hợp nhóm theo ngày × nhân sự — mỗi người một HÀNG** (chủ dự án 19.09.2026, theo ảnh mẫu): ngày có nhiều người thì ra nhiều hàng, mỗi hàng chỉ mang số của người đó, ngày lặp lại; Doanh thu suy ra khoá theo cặp (ngày, marketer) nên không dồn tiền cả ngày cho từng người; dòng Tổng trong bộ lọc không đổi; Excel cũng mỗi người một dòng; Vận đơn nhóm theo ngày × người phụ trách như vậy | ADR-035 · ADR-038 | Tự động |
| AC-22.15 | **Khối theo ngày: dòng Tổng ngày và cột STT** (chủ dự án 19.09.2026, theo ảnh mẫu): mỗi ngày là một khối, dòng **Tổng ngày** đứng đầu khối với số bằng tổng các dòng con, cột tính được tính lại từ tổng (CPO = ΣCPQC ÷ Σđơn, không phải trung bình các dòng) và Doanh thu suy ra cộng theo ngày; cột **STT** sau cột Ngày đếm lại từ 1 trong từng ngày; dòng "Tổng trong bộ lọc" không đổi và vẫn ghim trên; Excel cùng khối, dòng Tổng ngày in đậm; không thêm lệnh truy vấn | ADR-035 · ADR-038 · Quy tắc 1 | Tự động |
| AC-22.16 | **Tô màu chỉ tiêu** (chủ dự án 19.09.2026, theo ảnh mẫu): cột **chỉ số quan trọng** (`FOCUS_METRICS`: Tỉ lệ chốt, CPO, Giá Mess, CPQC/Doanh số) có nền riêng ở cả tiêu đề và ô; ô **tỉ lệ** so với dòng "Tổng trong bộ lọc" theo chiều tốt khai ở `METRIC_DIRECTION` — hơn mốc 10 % về phía tốt là đạt, kém 10 % là cảnh báo, trong biên để trơn; **cột cộng không tô** (mốc là tổng mọi dòng nên dòng nào cũng nhỏ hơn) và chỉ tiêu chưa rõ chiều (Hóa đơn/Doanh thu) cũng không tô; dòng Tổng là mốc nên chỉ có nền cột; màu lấy từ token nên đúng ở cả chế độ sáng và tối | ADR-035 · ADR-038 | Tự động + trình duyệt |

## 24. CRM-Optimization — ADR-024, đang kiểm chứng

ADR-024 thay riêng điều kiện “không có cache mới” của AC-22.9 bằng cache
Thống kê tối đa 15 giây. Giữ công thức, scope và các tiêu chí giao diện trước đó.
Các mục dưới là điều kiện nghiệm thu, **không phải kết quả đã đạt**.

| Mã | Đạt khi | Kiểm bằng |
|---|---|---|
| AC-24.1 | Khối v2 ≤100 dòng; token/cursor ký theo user/bảng/điều kiện/quyền; ID/thứ tự/tổng khớp truy vấn và xuất; cache hit không COUNT lại; Redis lỗi đọc DB | Unit/functional và EXPLAIN |
| AC-24.2 | Mọi đường ghi phát revision cùng transaction; rollback không phát; commit đảo thứ tự khởi tạo không mất sự kiện; journal ≤10k phiên bản/bảng và ≤2k ID/sự kiện | Transaction/bulk/migration test |
| AC-24.3 | Sync ≤4k ID client, chỉ trả dòng còn scope; mất quyền/khóa tài khoản gỡ dữ liệu khỏi UI; cache nóng không vượt quyền; lọc/sort đổi loại phản hồi cũ | Functional + trình duyệt |
| AC-24.4 | V1/v2 cùng giữ CAS, nguyên tử, nháp mới, Undo và replay; biên nhận v2 không nhân lịch sử, trả đúng xác nhận ban đầu sau kiểm quyền, kể cả tắt cờ | Unit + E2E |
| AC-24.5 | Sticky lệch ≤1 CSS px trong cuộn; cache ≤10, DOM/heap có giới hạn; không đổi thao tác inline/IME/selection/resize; UI p95 ≤100ms, ≥100 mẫu | Chrome 1440/1280/390, CSS zoom và zoom thực ghi riêng |
| AC-24.6 | Thống kê giữ công thức và snapshot, TTL không gia hạn quá15s, Làm mới bỏ cache; Excel giữ kiểu/chuỗi số0 đầu/định dạng/ID/thứ tự; worker/tải lại kiểm quyền; cấu hình giới hạn một tác vụ nặng chạy đồng thời, đo riêng độ dài/thời gian chờ hàng đợi | Functional + xuất/nhập nền |
| AC-24.7 | Đo cùng snapshot/seed/tài nguyên: 100k/300k ×10/20, warmup60s/đo5phút; bản cuối 300k/20/30phút; đọc/lọc/history p95≤1s, lưu ô≤0,5s, 2k ô≤5s; không lỗi mạng/5xx không chủ đích hoặc sai dữ liệu | Raw HTTP/browser/resource/storage evidence |

Không gộp skip thành đạt. VPS chưa có thì chỉ báo kết quả local; không dùng
cấu hình dự kiến thay phép đo. Cờ không đạt hồi quy phải để tắt.

## 33. Phạm vi Tôi / Toàn bộ và quyền sửa Vận đơn — ADR-033

Thay AC-26 về Chế độ xem bảng (trang, service, trường đã xoá) và vế "nhân
viên Vận đơn chỉ đơn được giao" của AC-20.1. Sale, CSKH, Marketing, Kế toán
giữ tiêu chí cũ.

| Mã | Đạt khi | Yêu cầu | Kiểm bằng |
|---|---|---|---|
| AC-33.1 | Nhân viên Vận đơn thấy mọi dòng bảng Vận đơn kể cả chưa phân công hay người khác phụ trách; sửa được qua lưới JSON và `record_service`; chi tiết mở được; số dòng thư mục đếm đủ | ADR-033 | Tự động |
| AC-33.2 | CSKH được giao chỉ xem (ghi 403); Sale không sửa dòng Sale khác; Admin gõ vào cột `phu_trach_*` vẫn 400, phân công chỉ qua hộp Phân công | ADR-033 · ADR-020 | Tự động |
| AC-33.3 | `cua_toi=1` lọc theo cột phụ trách của bộ phận (Vận đơn → delivery, Sale/CSKH → care, Marketing → marketing); Admin, Kế toán, bảng thường bỏ qua; khối dữ liệu đổi phiên bản; 100 dòng không vượt trần 22 truy vấn | ADR-033 | Tự động |
| AC-33.4 | `cua_toi=1` đi theo Tải Excel trực tiếp và nền, và Thống kê | ADR-033 | Tự động |
| AC-33.5 | `che-do-xem/` trả 404; `TableDef` không còn `delivery_view_all` nhưng còn `delivery_view_version`; Cột & cấp quyền không còn khối Chế độ xem bảng | ADR-033 | Tự động |
| AC-33.6 | Nút Tôi / Toàn bộ chỉ hiện cho người có cột phụ trách; không còn nút Chế độ: Xem; `?cua_toi=1` đánh dấu nút Tôi; `config.myScope` đúng trường | ADR-033 | Tự động |
| AC-33.7 | Migration 0013 chạy xuôi và ngược trên DB test, giữ `delivery_view_version` và dữ liệu | ADR-033 | Tự động |
| AC-33.8 | Xoá trống ô Quốc gia thì Loại tiền trống; dòng có tiền hỏi xác nhận rồi ghi được cả lượt xoá; điền lại Quốc gia tiền về đúng; nhập tệp và lên đơn vẫn bắt buộc quốc gia. Lưới như Excel: bấm chỉ chọn, gõ là nhập, Enter/F2/bấm đúp mở ô, Tab/Enter chỉ chuyển ô, Ctrl+A chọn cả bảng (kiểm trình duyệt) | ADR-033 · ADR-031 | Tự động |

## 36. Một bảng vận đơn duy nhất — ADR-036

Thay AC-11.39, AC-18.9 (đã gạch) và vế "hai bảng" của AC-18.1. Sale, CSKH, Marketing,
Kế toán giữ tiêu chí cũ trên bảng duy nhất.

| Mã | Đạt khi | Yêu cầu | Kiểm bằng |
|---|---|---|---|
| AC-36.1 | Máy sạch: `tao_bang_van_don` tạo đúng một bảng `van_don` "Vận đơn mới", `workflow=waybill`, dùng chung, đủ 25 cột chuẩn + 9 cột giữ lại, Mã đơn là khoá, cột chọn đủ lựa chọn chuẩn, cột bắt buộc đúng; chạy lại không thêm gì; không sinh crmThuận hay Vận đơn DB | ADR-036 | Tự động |
| AC-36.2 | Bảng cũ có sẵn (cột chữ tự do, tên cũ, dòng, quyền): nâng cấp tại chỗ giữ ID/dòng/quyền/cột tuỳ biến, Loại tiền và PTTT thành danh sách chuẩn, tên "Vận đơn mới", có nhật ký; chạy lại không đổi | ADR-036 | Tự động |
| AC-36.3 | Lên đơn ghi vào `van_don` kèm chi tiết; lưới có cột Trùng lẫn `detail_url` và cờ detail/assignment/protected/frozen; Sale chưa thấy bảng vào `/bang-tinh/van_don/` được đưa sang Lên đơn; `/bang-tinh/` mặc định `van_don`; Thống kê `nguon=van_don` profile Vận đơn; `/van-don/thong-ke/` chuyển tới `nguon=van_don` | ADR-036 | Tự động |
| AC-36.4 | Dòng đủ cột bắt buộc, không Chi tiết sản phẩm → tạo được, không item, Thống kê đếm thiếu chi tiết, tổng giữ như nhập; có chi tiết sai tổng vẫn bị từ chối; nhập tệp mẫu cũ vào `van_don` không lỗi cột | ADR-036 | Tự động |
| AC-36.5 | `xoa_bang_van_don_cu` thiếu cờ → từ chối, không xoá; đủ cờ → hai bảng cũ mất hẳn cùng dòng, chi tiết, phân công, lịch sử ô, biên nhận, quyền, nguồn báo cáo; đơn ERP giữ với `record=None`; `van_don` nguyên; nhật ký DELETE; chạy lại "không có gì để xoá"; không bao giờ xoá `van_don` | ADR-036 | Tự động |
| AC-36.6 | `/cau-hinh/nhan-don/` 404 với mọi vai; sidebar Admin không còn "Bảng nhận đơn"; `TableDef` không còn `receives_orders`, còn `delivery_view_version`; migration 0014 xuôi/ngược giữ dữ liệu | ADR-036 | Tự động |
| AC-36.7 | `configure_erp_reports` tạo nguồn Vận đơn cho `van_don`; `nap_du_lieu_van_don` và `nap_khach_mau` (mặc định) nạp vào `van_don` có phân công | ADR-036 | Tự động |
## 37. Mã nhân sự — ADR-037

Bổ sung AC-4.6 và AC-22.10: định danh trên mọi màn hình là **mã nhân sự** (`UserProfile.staff_code`),
mã trước, tên sau. Ngoại lệ (bổ sung 18.09 tối): ô bảng và Excel của Báo cáo tổng hợp **chỉ mã**.

| Mã | Đạt khi | Yêu cầu | Kiểm bằng |
|---|---|---|---|
| AC-37.1 | Mã = TÊN + chữ đầu họ + chữ đầu tên đệm, viết hoa không dấu (Lê Thưởng Thuận → `THUANLT`); họ tên không cho mã hợp lệ thì lấy chữ số của tên đăng nhập; hồ sơ lưu mà rỗng thì tự gán nên mọi hồ sơ đều có mã; `employee_code` trả mã | ADR-037 | Tự động |
| AC-37.2 | Trùng mã thì thêm 2, 3…; trùng tên đăng nhập của người khác cũng nhảy số; gán tay mã đã có người dùng bị từ chối | ADR-037 | Tự động |
| AC-37.3 | Mã đã gán không đổi được (model lẫn form sửa hồ sơ); hồ sơ cũ còn rỗng thì Admin gán một lần, có nhật ký; gợi ý mã chỉ Admin, Staff/Manager bị 403 | ADR-037 | Tự động |
| AC-37.4 | Tài khoản mới để trống tên đăng nhập thì tên đăng nhập = mã; đăng nhập bằng mã gõ hoa hay thường đều vào, sai mật khẩu vẫn chặn; tài khoản cũ giữ tên đăng nhập | ADR-037 | Tự động |
| AC-37.5 | Danh sách nhân sự có cột Mã và tìm theo mã; ô Người bán gợi ý mã; nhãn danh tính `MÃ · Họ tên` ở Báo cáo tổng hợp, Lịch sử, Excel; Staff không vào danh sách nhân sự | ADR-037 | Tự động |
| AC-37.6 | `gan_ma_nhan_su_cu` xem trước không ghi; chạy thật gán mã hồ sơ rỗng và đổi ô danh tính khớp đúng tên đăng nhập (cả `val_seller`), giữ giá trị lạ; chạy lần hai không đổi thêm | ADR-037 | Tự động |

## 38. Báo cáo Marketing hoàn thiện — ADR-038, ADR-031 bổ sung

Bổ sung AC-4.x (nộp tự do, Kế toán) và AC-22.x (nguồn báo cáo); bảy thị trường theo ADR-031 bổ sung 18.09.2026.

| Mã | Đạt khi | Yêu cầu | Kiểm bằng |
|---|---|---|---|
| AC-38.1 | Bảy thị trường US, CA, PH, EU, KR, JP, AU ↔ tám loại tiền; cột Thị trường và Loại tiền của bảng cấu hình trước 18.09 được bổ sung giá trị mới, giữ giá trị cũ, chạy lại không đổi, cột không phải Chọn một thì báo lỗi; nộp Hàn Quốc → KRW, Úc → AUD, quốc gia lạ bị từ chối; báo cáo một loại tiền mới công bố tổng, lẫn tiền thì cảnh báo; JPY/KRW không phần lẻ; xếp hạng quy đổi EUR/AUD được, KRW chưa có tỉ giá thì báo rõ | ADR-031 bổ sung | Tự động |
| AC-38.2 | DS Chốt (TT) — Doanh thu Marketing suy ra từ vận đơn, quy ₫ theo loại tiền từng đơn (ADR-040) (`WaybillItem.paid_amount` của đơn có Phụ trách Marketing là marketer trong phạm vi, cùng kỳ theo ngày lên đơn, cùng sản phẩm/quốc gia khi lọc) đúng ở mọi cách xem (ngày, nhân viên, sản phẩm, thị trường, phòng ban); tổng bằng tổng các dòng; đơn chưa phân công, marketer khác, ngoài kỳ, khác sản phẩm không vào; Staff chỉ thấy tiền của mình; Excel và Tổng quan cùng số; lọc Tệp khách hàng thì Doanh thu trống | ADR-038 | Tự động |
| AC-38.3 | Hóa đơn/DS Chốt (TT) (nhãn cũ Hóa đơn/Doanh thu) = Hóa đơn ÷ DS Chốt (TT) theo đúng nhãn (thay K/J 09.09) ở báo cáo nguồn và đường cũ; thiếu một vế thì trống; tiền vận đơn khác loại tiền với báo cáo thì quy ₫ rồi cộng, không cảnh báo, không để trống (ADR-040 thay cách cũ); `configure_erp_reports` không tạo cột nhập Doanh thu, gỡ trường đó khỏi biểu mẫu, bỏ cột tính từng dòng, chạy lại không đổi | ADR-038 | Tự động |
| AC-38.4 | Cột Tệp khách hàng (Chọn một) với danh sách mặc định theo sheet MKT có trên bảng và biểu mẫu Marketing; nộp giá trị ngoài danh sách bị từ chối; lọc `tep` đúng giá trị, `__missing__` = chưa có, giá trị lạ → 400; Leader/Manager Marketing thêm giá trị ngay ô chọn, Staff bị từ chối; phụ đề Excel ghi tệp | ADR-038 | Tự động |
| AC-38.5 | Chọn nhanh kỳ ở Báo cáo tổng hợp: Hôm nay, Hôm qua, 7 ngày (hôm nay − 6 → hôm nay), Tháng này, Tháng trước — đúng ngày theo giờ Việt Nam, điền hai ô ngày và áp ngay; nút khớp khoảng đang lọc được đánh dấu | ADR-038 | Tự động |

## 39. Ẩn cột với cả công ty — ADR-039

Nút "Cột" của lưới (ADR-011) chỉ nhớ trong trình duyệt từng người. Từ 19.09.2026 quản lý bảng
ẩn được cột với **cả công ty**: cột biến khỏi lưới KN CRM, tệp Excel xuất ra và Bảng dữ liệu bên
KN ERP, nhưng định nghĩa cột và giá trị từng ô vẫn giữ nguyên (không phạm BR-4).

| Mã | Đạt khi | Yêu cầu | Kiểm bằng |
|---|---|---|---|
| AC-39.1 | Quản lý bảng ẩn một cột: cột biến khỏi lưới KN CRM với mọi người, khỏi tệp Excel xuất ra và khỏi Bảng dữ liệu bên KN ERP; giá trị ô vẫn nằm trong bản ghi; có nhật ký hoạt động | FR-8.10 · ADR-039 | Tự động |
| AC-39.2 | Hiện lại cột đã ẩn: cột về đúng vị trí cũ trên lưới, không xếp xuống cuối; dữ liệu cũ hiện đủ | FR-8.10 · ADR-039 | Tự động |
| AC-39.3 | Nhân viên và quản lý bộ phận khác bị từ chối (403 khi thấy bảng, 404 khi bảng ngoài phạm vi), không cột nào đổi; Admin và quản lý bộ phận sở hữu bảng thì được | FR-8.10 · ADR-039 | Tự động |
| AC-39.4 | Từ chối ẩn cột khoá, cột bắt buộc nhập, và lần ẩn làm bảng không còn cột nào hiện; chọn mã cột không có thì báo lỗi | FR-8.10 · ADR-039 | Tự động |
| AC-39.5 | Ẩn cả nhóm cột số lượng theo sản phẩm bằng một nút; thêm sản phẩm mới sau đó thì cột của nó vào ở trạng thái ẩn, nhóm không tự hiện lại; Lên đơn vẫn ghi số lượng vào cột đang ẩn nên hiện lại là có đủ dữ liệu | FR-8.10 · ADR-039 | Tự động |
| AC-39.6 | Quản lý bảng thấy mục "Đang ẩn với cả công ty" để bật lại; nhân viên không thấy mục đó và không biết bảng có cột ẩn | FR-8.10 · ADR-039 | Tự động |
| AC-39.7 | Migration `forms_builder/0015` chạy xuôi và ngược đều được, giữ nguyên cột và dữ liệu | FR-8.10 · ADR-039 | Tự động |

## 40. Báo cáo tổng hợp như ảnh mẫu — ADR-040

Chủ dự án 23.09.2026, theo ảnh mẫu LUMI OMS: Báo cáo tổng hợp là màn hình đối tác thích nhất
nên giữ mọi chức năng đang có và nâng cấp cho giống ảnh. Đợt 1 là số liệu: tiền quy ₫ ngay trong
truy vấn rồi mới cộng (thay cách "để trống khi lẫn tiền" của ADR-038), ba cột đối soát từ vận đơn
"(TT)", Tỉ lệ chốt cho BC MKT, và hai lỗi thật (phân trang, chip Kỳ). Các đợt sau bổ sung tiêu chí
tiếp theo trong mục này.

| Mã | Đạt khi | Yêu cầu | Kiểm bằng |
|---|---|---|---|
| AC-40.1 | **Tiền quy về ₫ trước khi cộng:** mọi cột kiểu Tiền nhân tỉ giá cố định (`EXCHANGE_RATES_VND`) theo loại tiền của **từng dòng** ngay trong truy vấn rồi mới cộng; hai báo cáo USD và EUR cùng ngày cùng người thành một dòng CPQC = 10×25.500 + 10×28.500 ₫; CPO, Giá Mess, AOV tính trên ₫; dòng Tổng bằng tổng dòng; ô hiện "540.000 ₫" không phần lẻ, tỉ lệ chốt hiện %; nhãn đơn vị nêu tỉ giá; Excel và Tổng quan cùng số; nguồn không ánh xạ Loại tiền vẫn cộng thô như cũ, không hậu tố ₫ | FR-5.4 · BR-8 · ADR-040 | Tự động |
| AC-40.2 | **Dòng không quy đổi được** (loại tiền chưa có tỉ giá như KRW, hoặc báo cáo cũ trống loại tiền): tiền của dòng đó không vào tổng, các cột đếm (Số Mess, Số đơn) vẫn tính đủ; cảnh báo nêu số dòng và loại tiền thiếu; dòng khác vẫn ra số ₫ | ADR-031 · ADR-040 | Tự động |
| AC-40.3 | **Cột đối soát (TT) của BC MKT:** Số đơn (TT) = số vận đơn có Phụ trách Marketing là marketer theo ngày lên đơn, kể cả đơn không có chi tiết sản phẩm (đơn đó không góp tiền); DS Chốt (TT) = tiền đã thu của các đơn đó quy ₫; Tỉ lệ chốt (TT) = Số đơn (TT) ÷ Số Mess; lọc sản phẩm chỉ đếm đơn có sản phẩm đó; đơn chưa phân công không vào; Theo nhân viên cộng cả kỳ; Staff chỉ thấy của mình; không có đơn thì Số đơn (TT) là 0 chứ không trống | FR-5.1 · ADR-038 · ADR-040 | Tự động |
| AC-40.4 | **Ngân sách truy vấn với nguồn Marketing thật** (quy ₫ + đối soát vận đơn): cách xem Tổng hợp và Theo nhân viên mỗi cách không quá 10 truy vấn | Q2 · ADR-040 | Tự động |
| AC-40.5 | **Phân trang và chip Kỳ:** liên kết phân trang không mang `trang`/`moi_trang` cũ nên từ trang 2 sang trang khác đi đúng; chip Kỳ chỉ có dấu × khi kỳ khác mặc định — gửi đúng kỳ mặc định thì không × và không tính là đang lọc | AC-22.13 · ADR-040 | Tự động |
| AC-40.6 | **Bố cục khối như ảnh mẫu** (cách xem Tổng hợp): khối đầu là **toàn kỳ theo nhân sự** (STT · Team · Nhân sự · Leader, mỗi người một dòng cộng cả kỳ, TỔNG CỘNG toàn kỳ đứng ngay dưới hàng tiêu đề cột, sắp theo mã); rồi **mỗi ngày một bảng riêng** mới nhất trước, tiêu đề ngày đặt trên bảng, không có cột Ngày, TỔNG CỘNG của ngày bằng tổng các dòng con và cột tính tính lại từ tổng, STT đếm lại từ 1; khối toàn kỳ cộng trong bộ nhớ, không thêm truy vấn; ngày bị tách trang thì trang sau ghi "(tiếp)" và lặp TỔNG CỘNG đủ cả ngày; Excel hai sheet "Toan ky theo nhan su" và "Theo ngay" cùng khối, cùng số | FR-5.1 · FR-5.4 · ADR-035 · ADR-040 | Tự động + trình duyệt |
| AC-40.7 | **Gộp / Không gộp** (`gop=1`): Gộp thì mỗi ngày chỉ còn một dòng là TỔNG CỘNG của ngày (bố cục trước 19.09), phân trang theo ngày, khối toàn kỳ vẫn đứng đầu; chip "Gộp" có × để về Không gộp; Excel sheet "Theo ngay" chỉ dòng ngày, cùng số với màn hình | ADR-035 · ADR-040 | Tự động |
| AC-40.8 | **Màu ba bậc theo ngưỡng tuyệt đối:** chỉ tiêu có ngưỡng (`ReportSource.thresholds`) tô xanh khi đạt mốc Tốt, đỏ khi qua mốc Kém, vàng ở giữa, đúng chiều tốt (Tỉ lệ chốt càng cao càng tốt, CPO càng thấp càng tốt); dòng TỔNG CỘNG cũng tô; chỉ tiêu chưa có ngưỡng giữ cách so với dòng Tổng ±10 % (AC-22.16); màu lấy từ token nên đúng ở chế độ sáng và tối | FR-8.8 · ADR-040 | Tự động + trình duyệt |
| AC-40.9 | **Form Ngưỡng màu:** chỉ Admin hoặc quản lý (Leader, Manager) của bộ phận sở hữu nguồn thấy và lưu được (302, có nhật ký Sửa); Staff và quản lý bộ phận khác bị 403 có nhật ký từ chối và không thấy form; mốc sai thứ tự theo chiều tốt, thiếu một mốc hay không phải số thì báo lỗi bằng tiếng Việt và không lưu; để trống cả hai mốc thì bỏ ngưỡng của chỉ tiêu đó | FR-8.8 · ADR-040 | Tự động |
| AC-40.10 | Migration `reports/0005` (cột `thresholds`) chạy xuôi và ngược đều được, không đụng dữ liệu nghiệp vụ | ADR-040 | Tự động |
| AC-40.11 | **Lọc nhiều sản phẩm:** tham số `sp` lặp lại (tick nhiều mục có ô tìm nhanh, Chọn tất cả / Bỏ chọn), tổng và phần đối soát (TT) đúng theo các sản phẩm đã chọn; URL cũ một sản phẩm `sp=A` vẫn đúng; danh sách tick chỉ gồm sản phẩm có thật trong phạm vi quyền (Leader không thấy hàng team khác); chip "N sản phẩm"; phụ đề Excel ghi danh sách | FR-5.3 · ADR-040 | Tự động |
| AC-40.12 | **Chọn nhanh "Tuần này"** (thứ Hai tuần này tới hôm nay, kể cả tuần vắt qua tháng) đứng sau "7 ngày" trong dãy Chọn nhanh của Báo cáo tổng hợp | FR-5.3 · ADR-040 | Tự động |
| AC-40.13 | **Bảng dữ liệu của bảng có nguồn báo cáo Sale/MKT là báo cáo chi tiết theo ngày** dùng chung động cơ với Báo cáo tổng hợp (quy ₫, cột và nhãn theo nguồn, ngưỡng màu, (TT)): **mỗi lần nộp một dòng** — hai lần nộp cùng ngày cùng người là hai dòng với STT riêng; khối toàn kỳ theo nhân sự đứng đầu, mỗi ngày một bảng có TỔNG CỘNG; (TT) trên dòng người chỉ hiện khi cặp (ngày, người) nộp một lần, nộp nhiều lần thì "—" và TỔNG CỘNG ngày vẫn đúng, không cộng đôi; bộ lọc Kỳ, Chọn nhanh, Sản phẩm, Thị trường, Tệp, Team, Nhân sự và Gộp; mặc định 25 dòng một trang; `?dang=tho` về liệt kê thô có liên kết quay lại và mọi liên kết giữ `dang=tho`; bảng không có nguồn giữ nguyên; Staff chỉ thấy dòng của mình, bộ phận khác 404; Xuất tệp ra Excel cùng khối; form Ngưỡng màu cho quản lý; không quá 10 truy vấn | FR-7.1 · FR-5.4 · ADR-014 · ADR-040 | Tự động |
| AC-40.14 | **Liệt kê thô của Bảng dữ liệu:** liên kết phân trang và sắp xếp giữ tìm kiếm, bộ lọc cột và cỡ trang, cột đang sắp có `aria-sort`; ô Đúng/sai hiện "Có"/"Không"; nút "Sửa cột" chỉ hiện với Admin hoặc quản lý bộ phận sở hữu bảng — quản lý bộ phận khác chỉ được cấp quyền xem không thấy, gọi thẳng vẫn 403; trạng thái rỗng không còn nhắc "phần 3B" | FR-7.2 · FR-7.3 · ADR-015 · ADR-040 | Tự động |

## 41. Form Nộp báo cáo ngày: chọn Team, bắt buộc, bỏ Hóa đơn, bố cục ngang — ADR-041

Chủ dự án góp ý 24.09.2026 sau khi xem thử trên local. Kết quả tại
[biên bản form nhập báo cáo](kiem-chung-form-nhap-bao-cao-20260924.md).

| Mã | Tiêu chí | Nguồn | Cách kiểm |
|---|---|---|---|
| AC-41.1 | **Dropdown Team trên form nộp báo cáo:** liệt kê team đang hoạt động của bộ phận sở hữu biểu mẫu (không lẫn team bộ phận khác), chọn sẵn team trong hồ sơ; nộp với team khác trong bộ phận thì dòng dữ liệu và báo cáo mang team đó — Leader team ấy xem và sửa được, Leader team khác không thấy; team bộ phận khác hay id lạ bị từ chối nêu rõ, không lưu; để trống thì theo hồ sơ; bộ phận không có team thì không có ô Team | FR-4.7 · ADR-041 | Tự động |
| AC-41.2 | **Bốn trường bắt buộc:** sau `configure_erp_reports` form MKT bắt buộc Số Mess, CPQC, Số đơn, Doanh số (cùng Ngày, Sản phẩm, Thị trường), form Sale bắt buộc Số Mess, Số đơn, Doanh số; trường đã có từ trước cũng bị ép; nộp thiếu bị từ chối nêu tên trường, không tạo dòng; "0" hợp lệ; các ô đó mang `required` phía trình duyệt, ô hệ thống và ô không bắt buộc thì không | FR-4.8 · AC-8.2 · ADR-041 | Tự động |
| AC-41.3 | **Bỏ Hóa đơn khỏi form nhập MKT:** form đang có trường Hóa đơn thì `configure_erp_reports` gỡ và không tạo lại; cột `hoa_don`, ánh xạ `invoice`, hai cột báo cáo "Hóa đơn" và "Hóa đơn/DS Chốt (TT)" vẫn còn cho dữ liệu cũ; giá trị `hoa_don` gửi thẳng lên bị bỏ qua | FR-4.9 · ADR-041 | Tự động |
| AC-41.4 | **Bố cục ngang, ô nhỏ:** form là một thẻ trải hết chiều rộng nội dung — hàng điều khiển Biểu mẫu · Team · Ngày, lưới ô nhập ngang (`bm-ngang`, ô cao ≤ 36 px, nhiều ô một hàng ở 1440, hai cột ở 390, không tràn ngang), cột tính sẵn là dòng chip thay cho ô nhập giả; màn Sửa báo cáo cùng lưới; cùng bộ điều khiển và token Solarpunk, sáng và tối | FR-4.10 · ADR-028 · ADR-041 | Tự động + trình duyệt |

## 27. Lưới dùng chung và vòng đời bảng — ADR-027

Đây là tiêu chí, chưa phải nhãn hoàn thành. Kết quả tại
[báo cáo CRM-UPDATE](kiem-chung-crm-update-20260912.md).

| Mã | Đạt khi | Kiểm bằng |
|---|---|---|
| AC-27.1 | Mọi bảng động dùng chung shell/JSON/virtual grid; renderer nghiệp vụ từ registry; ERP chỉ đọc, Vận đơn mới giữ Lên đơn/Bill/phân công | Functional + Chrome |
| AC-27.2 | Công thức/kiểu/định dạng đúng; CAS hai đầu vào đồng thời; ô khóa hoặc sai kiểu làm toàn lượt rollback và chỉ đúng vị trí | Functional/transaction |
| AC-27.3 | Nháp cuối bảng, thiếu bắt buộc giữ RAM; paste tạo/sửa nguyên tử; retry không trùng; Undo có xung đột từ chối toàn lượt, Redo cùng ID | Functional + Chrome |
| AC-27.4 | Manager đúng phòng ban/Admin xóa với tên chính xác, khôi phục giữ ID; Staff/Leader/Grant bị từ chối; Vận đơn mới được bảo vệ | Functional + Chrome |
| AC-27.5 | Biểu mẫu/job ghi chặn xóa; khóa chia sẻ cho ghi và độc quyền cho vòng đời; bảng xóa ngừng đọc/ghi/tải file và tab nóng gỡ dữ liệu | Transaction + worker + Chrome |
| AC-27.6 | Không còn renderer/asset ghi cũ; URL ghi cũ trả 409; metadata đổi cấu trúc giữ nháp theo mã cột; không ghi vòng qua CAS | Quét nguồn + functional + Chrome |
| AC-27.7 | 1440/1280/390 và zoom Chrome thật 125%; DOM/cache giới hạn; ít nhất 100 mẫu/thao tác, p95 ≤100ms; ghim lệch ≤1 CSS px; phân biệt IME mô phỏng/thật | Chrome + bằng chứng thô |
| AC-27.8 | 100k/300k ×10/20, 60s ấm +300s đo; nếu đạt chạy 300k/20/30 phút; đọc/lọc/history p95 ≤1s, lưu ≤0,5s, 2.000 ô ≤5s; không sai/mất/trùng/lộ dữ liệu | Locust + SQL + oracle + tài nguyên |

Tạo bảng trắng và duplicate cấu trúc hoãn; quyền tạo bảng sẵn có giữ nguyên.
