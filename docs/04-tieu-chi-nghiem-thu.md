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
| AC-1.8 | Form tạo tài khoản không hỏi Email và Ngày sinh (chốt 24.09.2026): tạo không email vẫn xong (email rỗng, không đụng email tài khoản cũ), đăng nhập bằng mã như thường, vẫn buộc đổi mật khẩu; màn Sửa hồ sơ vẫn có ô Ngày sinh để bổ sung cho thiệp sinh nhật | FR-1.4 | Tự động |
| AC-1.9 | Đăng nhập sai gửi **cùng lúc** nhiều lần vào một tài khoản không vượt được giới hạn: máy chủ thử mật khẩu nhiều nhất 5 lần, các lần còn lại báo đang khoá tạm đúng số phút; sai 4 lần rồi lần 5 đúng vẫn vào được (săn lỗi 06.10.2026) | FR-1.2 | Tự động |
| AC-1.10 | Đi giữa KN ERP và KN CRM không mất đăng nhập: trên máy local, liên kết sang dịch vụ kia giữ đúng host đang mở (127.0.0.1 hay localhost), chỉ đổi cổng; trên VPS giữ đúng địa chỉ cấu hình (06.10.2026) | FR-1.1 · ADR-009 | Tự động |
| AC-1.11 | Cấu hình VPS sai thì phát hành dừng: ERP, CRM ở hai tên miền mà cookie phiên chưa đặt cho tên miền cha chung → `check --deploy` báo lỗi; CRM ở tên miền thật mà thiếu `BANGTINH_GOC` → dừng khởi động thay vì chạy cấu hình dev (06.10.2026) | FR-1.1 · NFR-6 | Tự động |
| AC-1.12 | Cùng một đường dẫn ở KN ERP và KN CRM: từng vai được vào hay bị chặn đúng bảng đã chốt ở cả hai dịch vụ (ERP quản lý bảng chỉ Manager, ADR-045; CRM Leader như Manager trong bộ phận, ADR-015); đường dẫn chung mới phải được ghi quyền cho cả hai bên (06.10.2026) | FR-3.5 · FR-3.6 · ADR-045 | Tự động |

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
| AC-4.9 | Bỏ báo cáo cấp dưới (ADR-041): người nộp, Leader trong team, Manager trong bộ phận và Admin bỏ được — xoá mềm cả báo cáo lẫn dòng số liệu (BR-4), số rời khỏi Báo cáo tổng hợp, có nhật ký DELETE, bấm đúp không nhân đôi; nhân viên khác/Leader team khác/Manager bộ phận khác/Kế toán bị 403 (thấy) hoặc 404 (ngoài phạm vi xem) có nhật ký; service kiểm lại quyền trong giao dịch | FR-4.7 · ADR-041 | Tự động |
| AC-4.10 | Khôi phục báo cáo đã bỏ (ADR-041): Manager bộ phận mình và Admin thấy trang "Đã bỏ" (phân trang, đúng phạm vi) và khôi phục — báo cáo về Lịch sử, dòng số liệu sống lại nguyên nội dung, số về lại Báo cáo tổng hợp, nhật ký UPDATE; Staff/Leader/Kế toán/Manager bộ phận khác bị 403 có nhật ký; liên kết "Đã bỏ" chỉ hiện với người có quyền | FR-4.7 · ADR-041 | Tự động |
| AC-4.11 | Lịch sử báo cáo hiện Doanh số theo cách viết Việt Nam kèm loại tiền của dòng ("45.000.000 VND", "1.250.000 CAD", "720,5 USD"), không còn số máy kiểu "45000000,00" (kiểm toàn diện 04.10.2026) | FR-4.3 | Tự động |
| AC-4.12 | Một lần nộp chỉ ghi một báo cáo: form có mã lần nộp dùng một lần; gửi lại đúng lần đó (mạng gửi lại, Back rồi Nộp, hai yêu cầu cùng lúc) không ghi thêm và báo "đã ghi lúc…"; nộp lỗi rồi sửa lại cùng mã vẫn ghi được một lần; mở form mới là mã mới (vẫn nộp nhiều lần trong ngày, AC-4.7); mã tính riêng từng người (săn lỗi 06.10.2026) | BR-2 · FR-4.2 | Tự động |

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
| AC-6.8 | Nhập đơn với số điện thoại đã có thì hệ thống báo khách đã mua trước đó; "đã có" đếm theo **dòng đang sống trên bảng Vận đơn** cùng số (khoá 9 số cuối, như cột Trùng) — dòng đã xoá hay đơn của bảng cũ đã xoá cứng không tính, dòng nhập thẳng vào bảng có tính; cột "Mua lại lần" của đơn mới đếm cùng cách (chủ dự án 28.09.2026) | FR-6.7 | Tự động |
| AC-6.10 | Cùng số điện thoại nhưng gõ tên khác: đơn mới ghi **tên vừa gõ**, danh bạ đổi theo và có nhật ký; đơn cũ giữ nguyên tên lúc đó; số điện thoại khác nhau thì mỗi đơn mang tên của mình; ô Facebook/Email bỏ trống không xoá dữ liệu đã có ; trước khi lưu, lời nhắc khách báo trước "sẽ đổi tên khách của số …" kèm cả tên cũ lẫn tên đang gõ, và mảnh nhắc mang sẵn tên để ô Tên khách tự điền khi đang trống | FR-6.7 | Tự động |
| AC-6.9 | **Leader trở lên** của bộ phận Sale (chủ dự án 02.10.2026; trước đó Manager) lên đơn thêm được sản phẩm mới ngay tại ô chọn: mã tự sinh không trùng, sản phẩm hiện trong danh sách chọn và có ngay cột số lượng trên bảng vận đơn, mỗi lần thêm có nhật ký; Staff gửi thẳng bị từ chối có ghi nhật ký, không thấy hộp "Tạo sản phẩm"; bộ phận khác bị chặn; tên trùng bị từ chối; nút thêm một dòng vào đơn ghi "Thêm dòng", không ghi "Thêm sản phẩm" | FR-6.8 | Tự động |
| AC-6.11 | Một lần bấm Lưu đơn chỉ ra một đơn: form Lên đơn có mã lần nộp dùng một lần; gửi lại đúng lần đó (kể cả hai yêu cầu cùng lúc) chỉ ra một đơn một mã, lần sau báo lại mã đơn đã lưu "không tạo đơn mới"; lưu xong form có mã mới (săn lỗi 06.10.2026) | FR-6.1 | Tự động |

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
| AC-7.13 | Bảng dữ liệu ERP: bấm tiêu đề cột để sắp xếp chỉ thay khối bảng bằng HTMX, trang không tải lại; địa chỉ trang mang tham số sắp xếp; bấm lần nữa đảo chiều; qua HTMX vẫn chặn đúng (Staff 403, bảng bộ phận khác 404) (28.09.2026, TL-62) | FR-7.3 | Tự động + trình duyệt |
| AC-7.14 | Tệp Excel xuất ra (Bảng dữ liệu trực tiếp và chạy nền, Báo cáo tổng hợp, tệp mẫu nhập) không có ô công thức nào: chữ người dùng gõ bắt đầu bằng "=" (tên khách, ghi chú, tên bảng…) ghi thành chữ đúng nguyên văn, không chạy khi mở tệp (săn lỗi bảo mật 06.10.2026) | NFR-9 · ADR-002 | Tự động |
| AC-7.15 | Tệp nhập nhỏ mà giải nén khổng lồ bị từ chối với lời tiếng Việt **trước** khi đọc vào bộ nhớ: dòng vượt 500 cột (.xlsx và CSV), tổng giải nén .xlsx vượt 200 MB; tệp thật vài chục cột × 10.000 dòng vẫn nhập được (săn lỗi bảo mật 06.10.2026) | NFR-11 · NFR-13 | Tự động |

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
| AC-9.6 | Chữ Việt gõ từ máy nào cũng lưu và tìm như nhau: dạng tổ hợp (macOS, NFD) ở form, JSON của lưới, ô tìm kiếm và ô của tệp nhập Excel/CSV đều về dạng dựng sẵn NFC trước khi ghi hay tìm; ô mật khẩu giữ nguyên (săn lỗi 06.10.2026) | Tìm kiếm, tra trùng khách | Tự động |
| AC-9.7 | Ô tiền và số thập phân chỉ nhận chữ số với dấu chấm, phẩy và một dấu trừ: "NaN", "Infinity", "1e400", "+-5" bị từ chối; số vượt 16 chữ số phần nguyên báo lỗi tiếng Việt nói rõ trần; nộp báo cáo với các giá trị đó ở lại form, không trang lỗi 500, không thêm báo cáo; cách viết Việt Nam và số dán kiểu Mỹ vẫn đọc đúng (săn lỗi 06.10.2026) | BR-8 · NFR-6 | Tự động |
| AC-9.8 | Ngày "hôm nay" của chip chọn nhanh trên lưới và tên tệp Excel xuất từ lưới theo giờ Việt Nam, kể cả từ 0 giờ tới 7 giờ sáng khi máy chủ chạy giờ quốc tế (săn lỗi 06.10.2026) | BR-7 | Tự động |

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
| AC-10.10 | Dòng giả xoá **theo lô** qua một đường dùng chung `delete_fake_records` (`seed_perf.clear()` lẫn `nap_khach_mau --xoa-cu`): mỗi lô một giao dịch riêng có `SET LOCAL lock_timeout` trên đúng database của queryset, gọi `on_progress(đã xoá, tổng)`; hết hạn chờ khoá thì lỗi nói rõ đã xoá được bao nhiêu thay vì treo (TL-43) | NFR-2 | Tự động |
| AC-10.11 | **Máy chạy thử tự nhận CSS/JS mới** (chủ dự án 28.09.2026): DEBUG bật thì số phiên bản `?v=` sau đường dẫn CSS/JS quét lại mỗi lần tải trang (`core.context_processors.phien_ban_hien_tai`), sửa riêng tệp tĩnh là lần tải trang kế tiếp lấy bản mới, không phải Ctrl+F5; DEBUG tắt (VPS) giữ số tính một lần lúc khởi động | NFR-6 | Tự động |
| AC-10.12 | Mất mạng giữa chừng: lưới báo "Lỗi lưu" kèm lời tiếng Việt "Mất kết nối mạng…" (không còn "Failed to fetch"), có mạng lại tự lưu đúng một lần; Lên đơn và mọi yêu cầu HTMX gửi hỏng (mất mạng, quá hạn, lỗi 5xx) hiện ô báo ở đáy màn hình, dữ liệu đã điền còn nguyên; gửi lại ra đúng một bản (săn lỗi 06.10.2026) | NFR-6 · quy tắc bắt buộc 13 | Tự động |
| AC-10.13 | Hàng đợi tác vụ nền (Redis) chết: gửi tác vụ chỉ thử lại ngắn (dưới 3 giây, không lưu kết quả Celery); không gửi được thì tác vụ thành Thất bại kèm lời tiếng Việt, xuất Excel lưới báo ngay ở lưới, không treo 19 giây, không lỗi 500, không tác vụ kẹt "Chờ xử lý"; Redis bật lại thì gửi được ngay (săn lỗi 06.10.2026) | NFR-6 | Tự động |
| AC-10.14 | Lỗi máy chủ và trang không có hiện trang tiếng Việt (500, 404), không phải trang trắng chữ Anh khi DEBUG tắt; đĩa đầy khi ghi tệp (tải tài liệu, nhập tệp) trả 507 "hết chỗ lưu tệp, tệp chưa được lưu" và báo người vận hành; tác vụ xuất nền gặp đĩa đầy cũng nói rõ (săn lỗi 06.10.2026) | NFR-6 | Tự động |
| AC-10.15 | Postgres khởi động lại: kết nối giữ lại bị cắt không làm hỏng yêu cầu nào sau khi Postgres chạy lại (`CONN_HEALTH_CHECKS`) (săn lỗi 06.10.2026) | NFR-6 | Tự động |
| AC-10.16 | Ký tự NUL ở bất kỳ đầu vào nào (tham số GET, form POST, thân JSON): trả 400 với lời tiếng Việt, không lỗi 500; chữ thường, chữ Việt, tab, xuống dòng, emoji vẫn đi qua (săn lỗi 06.10.2026, fuzz) | NFR-6 | Tự động |

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
| AC-11.1 | Lưới hiện đủ cột của bảng vận đơn; **Ngày (lên đơn) là cột dữ liệu đầu tiên** (24.09.2026), năm cột đầu (Trùng, Ngày, Mã đơn, Tên khách, SĐT) và hàng tiêu đề đứng yên khi cuộn | FR-7.8 | Thủ công |
| AC-11.2 | Lọc theo từng cột — danh sách giá trị kèm số đếm, chứa chữ, khoảng số hoặc ngày, ô trống — nhiều cột cộng dồn, số dòng đúng | FR-7.8 | Tự động |
| AC-11.3 | Sửa ô tại chỗ đúng kiểu cột; ô danh sách chỉ nhận giá trị trong danh sách, giá trị lạ bị từ chối kèm lý do; mỗi lần sửa ghi một dòng nhật ký | FR-7.4 · BR-5 | Tự động |
| AC-11.4 | Người ngoài phạm vi bảng vận đơn (không phải quản trị viên) bị từ chối ở mọi đường dẫn Bảng tính của bảng đó, kể cả gọi thẳng và gửi POST | FR-3.6 | Tự động |
| AC-11.5 | Cột Lọc trùng đếm đúng số dòng cùng **khoá** số điện thoại — 9 chữ số cuối sau khi bỏ ký tự không phải số (TL-36) — và tô màu khi lớn hơn 1; lọc được "chỉ số trùng" | FR-7.8 | Tự động |
| AC-11.6 | Dòng Hủy trước giao, Hủy sau giao, Hoàn đơn được tô màu | FR-7.8 | Tự động |
| AC-11.7 | Không bảng nào sửa được ô ở Bảng dữ liệu KN ERP — đường sửa ô cũ trả 404, kể cả bảng vận đơn với nhân viên Vận đơn lẫn Admin; cùng ô đó ở lưới KN CRM thì sửa được, bảng chỉ xem ở dịch vụ này thì 403 | FR-7.4 | Tự động |
| AC-11.8 | Mỗi sản phẩm đang bán có một cột số lượng trên bảng vận đơn; lên đơn điền tự động số lượng, địa chỉ và lần mua | FR-6.3 · FR-6.7 | Tự động |
| AC-11.9 | Nhập tệp vận đơn thật (ẩn danh) không chỉnh sửa: 221 dòng vào, 0 lỗi (PTTT "Cheque" thuộc bảy PTTT theo sheet Vận đơn, bổ sung ADR-031), trạng thái và thanh toán khớp danh sách (kể cả nhãn cũ, khác hoa thường), điện thoại là chuỗi | FR-7.5 | Tự động |
| AC-11.10 | Bàn phím: mũi tên và Tab đi giữa các ô, Enter sửa, Esc huỷ, chọn giá trị danh sách thì ô cập nhật không tải lại trang | FR-7.8 | Tự động |
| AC-11.11 | Bảng tính dùng được trên điện thoại và máy tính bảng | NFR-8 | Thủ công |
| AC-11.12 | **Chỉ bảng vận đơn** mở được ở `/bang-tinh/<mã>/` (ADR-040): bảng thường 404 với mọi vai kể cả Admin, ngoài phạm vi cũng bị từ chối; `/bang-tinh/` mở bảng vận đơn trong phạm vi, không có thì 404 kèm lời; thanh công cụ hiện nút theo quyền | FR-7.1 · FR-3.6 · ADR-040 | Tự động |
| AC-11.13 | Thanh lọc bên trái: chọn nhanh (hôm nay, hôm qua, 7 ngày, tháng này, tháng trước) và từ ngày / đến ngày viết vào bộ lọc cột Ngày; sản phẩm đánh dấu chọn lọc "có một trong"; xuất Excel ra đúng số dòng của lưới đang lọc | FR-7.2 · FR-5.2 · FR-5.3 · FR-7.6 | Tự động |
| AC-11.14 | Dòng vận đơn chỉ sinh từ Lên đơn (`protect_table`): lưới không có dòng trống thêm, dòng nháp gửi thẳng bị từ chối không tạo dòng nào; bảng thường không được KN CRM phục vụ nên cũng không còn đường thêm dòng trên lưới (ADR-040) | FR-7.4 · FR-3.6 · ADR-040 | Tự động |
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
| AC-11.28 | Mục **Bảng tính** của KN CRM (trang thư mục `/thu-muc/`) là trang **phẳng Bộ phận ▸ thư mục ▸ bảng, không còn cấp Quý/Tháng** (ADR-040), chỉ dựng từ **bảng vận đơn** trong phạm vi quyền (`in_scope`): bộ phận không có bảng vận đơn được xem thì không có nhánh, `bp` ngoài phạm vi 404, Admin thấy mọi bộ phận có bảng vận đơn, bảng được cấp quyền Xem hiện với nhãn Xem; bảng thường không có mặt; Manager của bộ phận thấy Cấp quyền và tạo thư mục; thống kê bảng một truy vấn cho cả bộ phận, cả trang trong ngân sách truy vấn của lưới (14, K24) | FR-7.13 · FR-3.1 · FR-3.6 · ADR-040 | Tự động |
| AC-11.29 | Lọc thời gian là việc của lưới (ADR-040): nút Mở trên thư mục dẫn thẳng tới lưới không mang bộ lọc; URL bộ lọc trọn một tháng thì lưới vẫn ghi nhãn Tháng M/YYYY trên thanh trên (kể cả năm nhuận), nút ← về đúng bộ phận không mang tham số; tham số `thang`/`quy`/`tat-ca` cũ trên URL bị bỏ qua, không nổ | FR-7.13 · FR-7.2 · ADR-040 | Tự động |
| AC-11.33 | **Leader như Manager trong bộ phận mình** (ADR-015): Leader của bộ phận sở hữu bảng tạo bảng (vào đúng bộ phận), sửa cột, chèn/bỏ cột trên lưới, tạo và sắp thư mục, nhập tệp, sửa và xoá dòng của người khác, xuất Excel; Staff bị từ chối có nhật ký; Leader bộ phận khác không thấy bảng (404), được cấp quyền Xem thì xem được nhưng đổi cấu trúc hay nhập tệp vẫn 403 có nhật ký; cấp quyền cho người khác vẫn chỉ Manager | FR-3.6 · FR-8.1 · FR-7.5 | Tự động |
| AC-11.31 | **Khung KN CRM có sidebar** (ADR-015, dáng Teeze): trang chủ `/` là tổng quan theo phạm vi quyền (dòng nhập tháng này và hôm nay, số bảng, tổng dòng, bảng cập nhật gần nhất, danh sách bảng có nút Mở, hoạt động gần đây — Staff chỉ đếm dòng của mình); sidebar trái có avatar + tên + cấp bậc, mục Trang chủ, Bảng tính gập được với mục con là từng bộ phận trong phạm vi (Sale không thấy Vận đơn), Tác vụ nền, KN ERP; trang có sidebar **không có nút ←**; logo KN CRM tự vẽ (`static/img/kn-crm.svg`) ở đầu menu trái và trên thanh trên của lưới, bấm là về trang chủ, favicon riêng của KN CRM còn KN ERP dùng logo KN JSC; chưa đăng nhập bị chuyển về đăng nhập; trong ngân sách truy vấn của lưới | FR-7.13 · FR-3.6 | Tự động |
| AC-11.32 | **Chỉ khi chủ động quay về mới thấy menu trái**: bấm Bảng tính trên sidebar mở trang thư mục (cây tháng, có sidebar); bấm một bảng mở lưới toàn màn hình không sidebar; nút ← của lưới về đúng trang thư mục và nhánh đang mở, không bao giờ về KN ERP; mục con bộ phận trên sidebar được đánh dấu đang chọn khi đang ở nhánh đó | FR-7.13 | Tự động |
| AC-11.34 | **Sửa cột kèm cấp quyền, nhập tệp chạy ngay trong KN CRM nhưng chỉ cho bảng vận đơn** (ADR-015, ADR-040): mục Nhập tệp (Leader trở lên) và Cấp quyền (Manager) chỉ liệt kê bảng vận đơn, các trang quản lý bảng thường ở KN CRM trả 404 (quản lý tiếp bên KN ERP); nút Tạo bảng đã ẩn, đường dẫn còn sống; Staff và Leader vào mục không được phép bị 403 có nhật ký; Bảng dữ liệu `/bang/` vẫn không có ở KN CRM; ở KN ERP các màn này vẫn dùng khung ERP | FR-8.1 · FR-7.5 · FR-8.4 · ADR-040 | Tự động |
| AC-11.35 | **Đổi cột tính sẵn trên bảng lớn thì tính lại ở tác vụ nền** (ADR-016): bảng nhiều hơn `RECOMPUTE_SYNC_MAX_ROWS` dòng thì thêm/sửa/bỏ cột tính sẵn hay cột mang nhãn tạo `BackgroundJob` "Tính lại cột" chạy theo lô `bulk_update`; cột hiện ngay, màn Sửa cột nói rõ có tác vụ nền, `moi-nhat/` trả tiến độ `tinh_lai` để lưới báo "Đang tính lại cột…" và nạp lại một lần khi xong; giá trị đúng khi xong; bảng nhỏ tính ngay tại chỗ, không có tác vụ | FR-7.9 | Tự động |
| AC-11.36 | **Lưới không phình theo số ô** (K27): 100 dòng × 39 cột ≤ 13 truy vấn, ô dựng bằng `grid_service.cell_html` với URL ghép chuỗi khớp `reverse('bang_tinh_o')`; cột Trùng đếm một truy vấn theo trang, `?trung=1` lọc bằng danh sách số điện thoại trùng (không subquery từng dòng); dán 500 ô ghi bằng `bulk_update` ≤ 25 truy vấn; `moi-nhat/` ≤ 8 truy vấn, không đếm dòng | NFR-1 | Tự động |
| AC-11.37 | ~~**1.000 dòng trống sẵn để nhập** (góp ý 17.09.2026): mở bảng có quyền thêm thì cuối lưới có sẵn 1.000 dòng trống, chân trang ghi số dòng trống; gõ một dòng thành bản ghi thật **không tải lại khối JSON**, dòng trống được bù đủ; tới dòng trống áp chót thì thêm 1.000 dòng nữa; tải lại trang chỉ còn dòng thật~~ **Rút 29.09.2026 — hành vi không còn đường nào xảy ra:** KN CRM trả 404 cho mọi bảng không phải vận đơn (ADR-040) và bảng vận đơn đặt `waybill_service.protect_table = True` nên `row_mutations.can_create()` sai với mọi tài khoản. Mã bù dòng trống còn trong nguồn nhưng không ai gọi tới; bỏ hay giữ là quyết định riêng, đã ghi backlog. Mở lại tiêu chí này khi có quyết định cho thêm dòng thẳng trên lưới | FR-7.4 · ADR-036 · ADR-040 | Bỏ |
| AC-11.38 | **Cột ghim đứng đầu thứ tự nhìn thấy**: cột ghim không ở đầu thứ tự cột (người dùng đổi thứ tự, hoặc bảng vận đơn có Ngày/Mã đơn/Tên khách/SĐT ở giữa) vẫn được xếp lên đầu khi vẽ — không ô trống ở vị trí gốc, không che cột đứng trước; vùng chọn, phím mũi tên và địa chỉ `A1:E2` theo đúng thứ tự trên màn hình | FR-7.4 | Tự động |
| AC-11.39 | ~~**Bảng nhận đơn liệt kê mọi bảng vận đơn đang có** (ADR-034): `van_don` cũ, bảng đang nhận và bảng bộ phận Vận đơn có cột Mã đơn đúng cấu trúc; bảng báo cáo cùng bộ phận và bảng bộ phận khác không hiện; bảng chưa đủ điều kiện hiện kèm lý do và không chọn được (400)~~ **Bỏ theo ADR-036 (18.09.2026): một bảng vận đơn, không còn Bảng nhận đơn / Vận đơn DB** | ADR-029 · ADR-034 | Tự động |
| AC-11.41 | Hộp lọc cột có nền, khung và danh sách giá trị cuộn được, không đè lên lưới; không chú thích CSS nào nuốt luật (quên `*/` ở dòng tiêu đề mục); lớp chỉ khai trong chú thích không tính là đã khai | FR-7.3 | Tự động |
| AC-11.42 | Ô tìm trong mảnh lọc cột trỏ vào ruột hộp chứ không vào cả `#hop-loc`: đổi sang cột khác thì hộp hiện đúng giá trị của cột đó, không sót mục của cột trước | FR-7.3 | Tự động |
| AC-11.43 | Hộp lọc cột chọn công cụ theo số giá trị thật: dưới ngưỡng thì giữ danh sách ô tích và ghi đúng tổng; vượt ngưỡng thì mở sẵn ô gõ chữ, danh sách ô tích gập lại và không bày hai ô cùng công dụng; `dem_gia_tri` đếm đúng cho cột tách, cột JSON và khi có ô tìm | FR-7.3 | Tự động |
| AC-11.44 | **Ghi chú đọc được ngay trên lưới**: profile bảng Vận đơn (`waybill_service.grid_column`) trả rộng 400 px và cờ `auto_height` cho riêng cột Ghi chú — cột khác và bảng khác giữ 160 px, không cờ; lưới không nhận diện cột theo mã, dòng có cột mang cờ cao vừa nội dung, đo bằng chính lớp CSS của ô (`data-code`, cỡ chữ, đậm): rỗng hoặc vừa một dòng giữ 28 px, có ký tự xuống dòng hay dài thì giãn tới trần 2000 px và không cắt chữ; click đơn **chỉ chọn ô** — không phồng, không mở gì (kiểu Google Sheets, bổ sung ADR-033 26.09); bấm đúp thì ô sửa được mở ô nhập (khung nhập cột văn bản dài tự giãn hết chỗ khung nhìn, tới trần khi đủ chỗ), ô chỉ đọc đang bị cắt chữ (quá trần, dòng bị kéo thấp, hay cột thường ở dòng 28 px) thì **ô phồng to tại chỗ** đè lên ô lân cận hiện đủ nội dung, bấm chỗ khác hay Esc thu về, bấm đúp lên ô phồng vẫn mở ô nhập/hộp riêng; đo lại ngay khi sửa/dán/xoá/định dạng/hoàn tác, khi lưu về, khi người khác sửa, khi đổi rộng hay ẩn/hiện cột và khi phông tải xong — không tải lại trang; tải lại mềm không làm dòng co về 28 px; chiều cao người dùng tự kéo (kể cả về 28 px) thắng và được nhớ, Home về chiều cao tự động; ô nhập văn bản dài cao theo chữ đang gõ (Enter xuống dòng, Ctrl+Enter xong); ô Ghi chú ở Lên đơn là ô nhiều dòng và ký tự xuống dòng gom về một kiểu; tệp Excel xuất ra bật Wrap Text cho cột văn bản dài | FR-7.4 · FR-7.8 | Tự động |
| AC-11.40 | **Gõ rồi Enter không giật**: gõ liên tiếp nhiều dòng trên lưới vận đơn thì ô nhập không nhảy ngược lên, tổng dòng và chiều cao lưới không đổi từng dòng, không thanh thông báo đẩy lưới; phản hồi lưu mang mốc `moi-nhat` để lưới không coi mốc do mình vừa lưu là người khác sửa; khi người khác sửa thật thì tải lại **mềm** — giữ ô cũ tới khi khối mới về, không hoá `…`. *(Phần "dòng nháp thành bản ghi nối tại chỗ, dòng trống bù theo đợt" rút 29.09.2026 cùng AC-11.37.)* | FR-7.4 · AC-11.26 | Tự động |

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
| AC-21.1 | Chỉ bảng mới chạy controller riêng, không form Lên đơn/thống kê nhúng/thanh công thức; hàng mặc định 28px, kéo 28–2000px (trần nâng từ 400 theo AC-11.44) và xuống dòng; ghi nhớ theo user/bảng/ID local, Escape hủy/↑↓/Home; cuộn/neo đồng bộ, reader/editor không tự giãn hàng | ADR-021 | Tự động |
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
| AC-21.12 | **Sắp xếp không giật** (chủ dự án 28.09.2026, TL-62): bấm tiêu đề cột trên lưới thì mũi tên đổi ngay, dòng đang hiện giữ tới khi dữ liệu đã sắp xếp về rồi thay một lượt (không ô "…"), giữ vị trí cuộn ngang và chiều cao dòng, không tải lại trang HTML; bỏ chip lọc sau đó vẫn giữ thứ tự vừa chọn | ADR-021 | Trình duyệt |
| AC-21.13 | **Lịch sử từng ô trên lưới** (chủ dự án 28.09.2026): chuột phải một ô mở khung ngay cạnh ô — mã và tên người sửa, giờ Việt Nam, giá trị trước → sau, "Cũ hơn" để xem tiếp; Esc, bấm ra ngoài hay cuộn thì đóng; ô bị **người khác** sửa giá trị trong 24 giờ (`GRID_RECENT_EDIT_HOURS`) có dấu góc, một truy vấn mỗi khối; người không xem được dòng thì lịch sử trả 403 | ADR-021 | Tự động + trình duyệt |
| AC-21.14 | **Nhãn bộ lọc trên thanh công cụ** (chủ dự án 28.09.2026): nhãn các bộ lọc đang bật nằm trên thanh công cụ lưới, giữa nút Cột (và Tôi / Toàn bộ) và nút Định dạng, cùng hàng; bật hay bỏ lọc không đẩy trang tính xuống (đỉnh lưới giữ nguyên ở 1440 và 1280 px); nhiều nhãn thì cuộn ngang trong chỗ của nó, không tràn trang | ADR-021 | Trình duyệt |
| AC-21.15 | **Phân công ngay trong ô** (chủ dự án 28.09.2026): Leader/Manager Vận đơn và Admin bấm đúp, Enter hay F2 ô "Phụ trách Vận đơn/CSKH/Marketing" thì ô chọn hiện đè đúng ô như "Trạng thái vận chuyển", có "— Chưa gán —" và mã nhân viên đúng bộ phận, chọn sẵn người đang giao; chọn bằng chuột là lưu, phím di chuyển không tự lưu, Enter lưu, Esc đóng không đổi; lưu qua endpoint phân công (quyền, CAS phiên bản, nhật ký như cũ); người không có quyền phân công không có ô chọn và endpoint trả 403. Cột phụ trách mang tên trường phân công khai ở `assignment_service.COLUMNS`. Nút "Phân công" và hộp phân công nhiều dòng trong menu "…" đã bỏ (chủ dự án 28.09.2026) | ADR-020 | Tự động + trình duyệt |
| AC-21.16 | Ô chữ ở biên: lưới, nhập tệp, form từ chối ô có ký tự NUL và ô dài hơn 32.767 ký tự (trần một ô Excel) bằng lời tiếng Việt, không lỗi 500, dữ liệu không đổi (săn lỗi 06.10.2026, fuzz) | NFR-6 | Tự động |
| AC-21.17 | CEO đọc toàn công ty mở được lưới và thấy dòng nhưng không ô nào sửa được và ghi bị từ chối 403 — kể cả khi hồ sơ CEO gắn vào chính bộ phận của bảng dùng chung (săn lỗi 06.10.2026, đột biến) | ADR-020 | Tự động |

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
| AC-22.13 | **Bố cục Báo cáo tổng hợp theo bản vẽ 18.09**: bộ lọc ba trạng thái qua `data-filters` (mở 260px, thanh dọc 48px có huy hiệu số bộ lọc, dưới 900px là ngăn kéo mặc định đóng), nhớ trong phiên `{filters, focus}` và đọc được khoá cũ; Toàn màn hình tự chuyển thanh dọc, Escape đóng ngăn kéo trước rồi thoát toàn màn hình; hàng chip bộ lọc đang áp (kể cả Tệp khách hàng) với × bỏ đúng tham số và Xóa lọc; giữ Chọn nhanh kỳ; tiêu đề, dòng Tổng ghim trên, cột định danh theo lớp tổng quát `.report-identity` với chiều rộng bằng biến CSS — từ 02.10.2026 chỉ cột đầu, Nhân sự, Loại tiền đứng yên khi kéo ngang, Team/Leader/Lần nộp trôi theo (AC-22.25; báo cáo Marketing ẩn cột Lần nộp, Loại tiền từ 03.10.2026, AC-47.6; báo cáo Sale ẩn cột Lần nộp từ 04.10.2026, AC-47.7) —, ô định danh xuống dòng không cắt chữ, ô số `nowrap`; Toàn màn hình: khung bảng nằm trong viewport (grid hàng `minmax(0,1fr)`), thanh kéo ngang và phân trang luôn thấy, không tràn | ADR-035 · ADR-038 · NFR-7 | Tự động + trình duyệt |
| AC-22.14 | **Cách xem Tổng hợp nhóm theo ngày × nhân sự — mỗi người một HÀNG** (chủ dự án 19.09.2026, theo ảnh mẫu): ngày có nhiều người thì ra nhiều hàng, mỗi hàng chỉ mang số của người đó, ngày lặp lại; Doanh thu suy ra khoá theo cặp (ngày, marketer) nên không dồn tiền cả ngày cho từng người; dòng Tổng trong bộ lọc không đổi; Excel cũng mỗi người một dòng; Vận đơn nhóm theo ngày × người phụ trách như vậy | ADR-035 · ADR-038 | Tự động |
| AC-22.15 | **Khối theo ngày: dòng Tổng ngày và cột STT** (chủ dự án 19.09.2026, theo ảnh mẫu): mỗi ngày là một khối, dòng **Tổng ngày** đứng đầu khối với số bằng tổng các dòng con, cột tính được tính lại từ tổng (CPO = ΣCPQC ÷ Σđơn, không phải trung bình các dòng) và Doanh thu suy ra cộng theo ngày; cột **STT** sau cột Ngày đếm lại từ 1 trong từng ngày; dòng "Tổng trong bộ lọc" không đổi và vẫn ghim trên; Excel cùng khối, dòng Tổng ngày in đậm; không thêm lệnh truy vấn | ADR-035 · ADR-038 · Quy tắc 1 | Tự động |
| AC-22.16 | **Tô màu chỉ tiêu** (chủ dự án 19.09.2026, theo ảnh mẫu): cột **chỉ số quan trọng** (`FOCUS_METRICS`: Tỉ lệ chốt, CPO, Giá Mess, CPQC/Doanh số) có nền riêng ở cả tiêu đề và ô; ô **tỉ lệ** so với dòng "Tổng trong bộ lọc" theo chiều tốt khai ở `METRIC_DIRECTION` — hơn mốc 10 % về phía tốt là đạt, kém 10 % là cảnh báo, trong biên để trơn; **cột cộng không tô** (mốc là tổng mọi dòng nên dòng nào cũng nhỏ hơn) và chỉ tiêu chưa rõ chiều (Hóa đơn/Doanh thu) cũng không tô; dòng Tổng là mốc nên chỉ có nền cột; màu lấy từ token nên đúng ở cả chế độ sáng và tối | ADR-035 · ADR-038 | Tự động + trình duyệt |
| AC-22.17 | **Thẻ Báo cáo tổng hợp trên Tổng quan đọc được** (TL-60, 26.09.2026): mỗi chỉ tiêu một hàng nhãn trái – số phải; số tiền dài (cỡ nghìn tỉ ₫) nằm một dòng ở màn 1440 px, không bẻ giữa chữ số; 390 px không tràn ngang; luật `.dashboard-*` chỉ khai ở `dashboard.css` và bài khai lớp CSS quét cả tệp đó | ADR-035 | Tự động + trình duyệt |
| AC-22.18 | **Thẻ Tổng quan không có ô đơn vị/cảnh báo quy đổi** (chủ dự án 26.09.2026): thẻ Báo cáo tổng hợp trên Tổng quan không hiện dòng tỉ giá lẫn ô "… dòng chưa quy đổi được"; từ ADR-046 (28.09) không còn quy đổi nên cả màn chi tiết cũng không có cảnh báo đó — dòng KRW hiện với loại tiền của nó, thẻ có cột KRW | ADR-042 · ADR-046 | Tự động |
| AC-22.19 | **Lăn chuột trên bảng không bị kẹt** (TL-63, chủ dự án 28.09.2026): con trỏ đặt trên khung bảng Báo cáo tổng hợp (và Bảng dữ liệu dạng báo cáo, cùng khung `.report-table-scroll`) — bảng vừa khung theo chiều dọc mà tràn ngang thì trang cuộn ngay; bảng dài thì bảng cuộn trước, cuộn hết bảng thì trang cuộn tiếp; khung bảng có nền đặc để cuộn không phải vẽ lại | ADR-042 | Trình duyệt |
| AC-22.20 | **Cách xem "Hiệu suất theo team"** (chủ dự án 30.09.2026) thay "Hiệu suất theo phòng ban" (bảng báo cáo nào cũng thuộc một bộ phận nên phòng ban chỉ ra một dòng = TỔNG CỘNG): mỗi team một dòng, mỗi loại tiền một dòng (ADR-046), kèm cột Leader của team; dòng của người chưa có team gom "Chưa có team"; DS Chốt (TT) đối soát theo team của marketer phụ trách vận đơn; Leader chỉ thấy team mình; đường dẫn cũ `nhom=department` mở thành Theo team. **Từ 01.10.2026 chỉ còn ở tầng service** (`activity_service.build(group="team")`): màn hình không còn ô Cách xem (AC-22.23), `nhom=team`/`department` mở ra từng lần nộp có cột Team, Leader | ADR-042 | Tự động |
| AC-22.21 | **Dòng TỔNG CỘNG dính đọc được** (TL-69, chủ dự án 30.09.2026): cuộn bảng Báo cáo tổng hợp (và Bảng dữ liệu dạng báo cáo, cùng khối bảng) thì mọi ô của các dòng TỔNG CỘNG đang dính có nền đặc ở chế độ sáng và tối, kể cả cột chỉ số — dòng đang cuộn bên dưới không lộ chữ, màu cột chỉ số nhìn như cũ; dòng tổng đầu dính sát đáy hàng tiêu đề của chính bảng đó, các dòng tổng liền nhau — đúng cả khi khung bảng đổi cỡ mà cửa sổ không đổi (Toàn màn hình, thu hay mở bộ lọc), ở màn hẹp và ở từng khối có hàng tiêu đề cao khác nhau | ADR-042 · ADR-046 | Trình duyệt |
| AC-22.22 | **Chọn nhanh chỉ sáng một nút** (chủ dự án 01.10.2026): ngày 01 "Hôm nay" và "Tháng này" cùng khoảng, thứ Hai "Hôm nay" và "Tuần này" cùng khoảng — chỉ một nút sáng: nút vừa bấm (ô ẩn `ky`) nếu khoảng của nó khớp kỳ đang lọc, không thì nút khớp đầu tiên; sửa tay ô ngày thì bỏ `ky`; đúng ở Báo cáo tổng hợp và Bảng dữ liệu dạng báo cáo | ADR-038 · ADR-046 | Tự động + trình duyệt |
| AC-22.23 | **Không còn ô Cách xem và ô Chế độ** (chủ dự án 01.10.2026: "để mặc định là từng lần nộp; thị trường, sản phẩm, thời gian đều có các filter bên dưới rồi"): Báo cáo tổng hợp và Bảng dữ liệu dạng báo cáo luôn mỗi lần nộp một dòng (cột Lần nộp "Lần N · giờ", số đúng như nhập), không chip Cách xem/Chế độ; URL cũ mang `nhom=…` hay `che_do=cong` vẫn mở 200 và vẫn ra từng lần nộp; phụ đề Excel không còn "Chế độ:"; nguồn Vận đơn vẫn mỗi ngày như cũ | ADR-046 | Tự động |
| AC-22.24 | **Vừa mở trang đã thấy số** (chủ dự án duyệt mockup "Ba chỗ sửa Báo cáo tổng hợp" 02.10.2026): tên bảng, khoảng ngày, nút Ngưỡng màu (chỉ người đặt được ngưỡng) và nút **Giải thích số liệu** nằm một hàng; câu loại tiền, đoạn "Tổng trên toàn bộ kết quả khớp bộ lọc · (TT) = …" (kèm biến thể nộp nhiều lần; biến thể "để trống khi lọc theo Tệp khách hàng" bỏ từ 03.10.2026 vì nguồn Marketing không còn lọc theo tệp, ADR-048) và toàn văn cảnh báo thu vào panel Giải thích số liệu ẩn sẵn, không bỏ chữ nào; cảnh báo dòng chưa có loại tiền còn một dòng (cắt "…", toàn văn ở `title` và trong panel); form ngưỡng là panel thứ hai, `?nguong=1` mở sẵn; hai nút đóng/mở panel, Escape đóng panel và trả focus về nút, Toàn màn hình vẫn có hai nút; ở 1366×768 bộ lọc mở, lúc mở trang thấy trọn hàng tiêu đề cột và các dòng TỔNG CỘNG của khối đầu; Bảng dữ liệu giữ ô Ngưỡng màu mở rộng như cũ | ADR-042 bổ sung 02.10 | Tự động + trình duyệt |
| AC-22.25 | **Kéo ngang không còn cột số bị che** (mockup 02.10.2026): chỉ cột đầu (STT, hay Ngày ở khối Gộp), Nhân sự và Loại tiền đứng yên — `left` chỉ cộng các cột đứng yên trước nó, bóng mép ở cột đứng yên cuối và chỉ hiện khi đã kéo; Team, Leader, Lần nộp giữ chỗ nhưng trôi theo (`report-troi`); dòng TỔNG CỘNG mỗi cột định danh một ô, nhãn ngắn "TỔNG CỘNG" ở ô Nhân sự, mã tiền ở ô Loại tiền, ô trôi vẫn dính theo chiều dọc; kéo ngang xong bảng tự nhích theo hướng đang kéo để không cột số nào vắt qua mép vùng đứng yên của khối đang xem (mũi tên phải vẫn tiến tiếp); ở 1366×768 vùng đứng yên ≤ 262 px; Bảng dữ liệu dạng báo cáo cùng cách; Excel giữ nhãn dài và thứ tự cột; báo cáo Marketing ẩn cột Lần nộp, Loại tiền (từ 03.10.2026, AC-47.6) nên Nhân sự là cột đứng yên cuối, mang bóng mép; báo cáo Sale ẩn cột Lần nộp (từ 04.10.2026, AC-47.7) | ADR-042 bổ sung 02.10 · AC-22.13 · AC-22.21 · AC-47.6 | Tự động + trình duyệt |
| AC-22.26 | **Gộp / Không gộp không tải lại trang** (mockup 02.10.2026, chỉ Báo cáo tổng hợp): bấm thì chỉ khung bảng, phân trang và chip đổi; link Xuất Excel, số bộ lọc, ô `next` của form ngưỡng cập nhật theo; hai nút đổi `aria-pressed` tại chỗ, focus ở lại nút vừa bấm; địa chỉ trang đổi theo (`history.pushState`), Back/Forward và tải lại ra đúng chế độ; bảng giữ đúng ngày đang xem (mốc `data-ngay` trên khối ngày và dòng Gộp) và vị trí kéo ngang; ở chế độ Từng lần nộp link giữ `trang`, `moi_trang` (hai chế độ chia trang như nhau) và bỏ `nguong`; nguồn Vận đơn vẫn về trang 1; máy chủ lỗi, hết phiên hay trang lạ thì tải cả trang như trước; Bảng dữ liệu bấm Gộp vẫn tải cả trang | ADR-042 bổ sung 02.10 · AC-42.7 | Tự động + trình duyệt |
| AC-22.27 | Thống kê KN CRM viết số như ERP: dấu chấm ngăn nghìn, phẩy thập phân, tối đa hai số lẻ, số nguyên không kèm ",00" — ở ô chỉ tiêu, nhãn điểm và chú thích biểu đồ (săn lỗi 06.10.2026, đối soát số liệu) | NFR-6 | Tự động |

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

## 32. Ô ngày DD/MM/YYYY — ADR-032

| Mã | Đạt khi | Yêu cầu | Kiểm bằng |
|---|---|---|---|
| AC-32.1 | **Ô ngày tự chèn "/"** (chủ dự án 28.09.2026): mọi ô ngày ERP/CRM (`date-inputs.js`) chèn "/" sau 2 số ngày và 2 số tháng; dấu cách, chấm, gạch ngang đổi thành "/"; gõ liền 8 số thành DD/MM/YYYY; rời ô thì thêm số 0 cho ngày tháng một chữ số; Backspace không bị chèn lại "/"; ngày sai vẫn báo lỗi; giá trị gửi đi vẫn là ISO | ADR-032 | Trình duyệt |

## 33. Phạm vi Tôi / Toàn bộ và quyền sửa Vận đơn — ADR-033

Thay AC-26 về Chế độ xem bảng (trang, service, trường đã xoá) và vế "nhân
viên Vận đơn chỉ đơn được giao" của AC-20.1. Sale, CSKH, Marketing, Kế toán
giữ tiêu chí cũ.

| Mã | Đạt khi | Yêu cầu | Kiểm bằng |
|---|---|---|---|
| AC-33.1 | Nhân viên Vận đơn thấy mọi dòng bảng Vận đơn kể cả chưa phân công hay người khác phụ trách; sửa được qua lưới JSON và `record_service`; chi tiết mở được; số dòng thư mục đếm đủ | ADR-033 | Tự động |
| AC-33.2 | CSKH được giao chỉ xem (ghi 403); Sale không sửa dòng Sale khác; Admin gõ vào cột `phu_trach_*` vẫn 400, phân công chỉ qua hộp Phân công | ADR-033 · ADR-020 | Tự động |
| AC-33.3 | `cua_toi=1` (bổ sung 28.09.2026, TL-64): dòng tôi lên đơn hoặc tôi là Sale đứng đơn, cộng dòng tôi được phân công ở bất kỳ cột phụ trách nào (Vận đơn, CSKH, Marketing) — áp cho mọi tài khoản, chỉ thu hẹp trong phạm vi quyền; Sale thấy ngay đơn mình vừa lên dù chưa ai phân công; bảng thường bỏ qua; khối dữ liệu đổi phiên bản; 100 dòng không vượt trần 22 truy vấn | ADR-033 | Tự động |
| AC-33.4 | `cua_toi=1` đi theo Tải Excel trực tiếp và nền, và Thống kê | ADR-033 | Tự động |
| AC-33.5 | `che-do-xem/` trả 404; `TableDef` không còn `delivery_view_all` nhưng còn `delivery_view_version`; Cột & cấp quyền không còn khối Chế độ xem bảng | ADR-033 | Tự động |
| AC-33.6 | Nút Tôi / Toàn bộ hiện với mọi tài khoản trên bảng Vận đơn (bổ sung 28.09.2026); không còn nút Chế độ: Xem; `?cua_toi=1` đánh dấu nút Tôi; `config.myScope` bật trên bảng Vận đơn | ADR-033 | Tự động |
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
| AC-36.8 | Khoá so trùng `val_phone_key` (`phone_key`: bỏ ký tự không phải số, lấy 9 chữ số cuối): `+1 (416) 555-0123` và `4165550123` là một khách trên cột Trùng và `?trung=1`; ô hiển thị giữ nguyên chữ gõ; `sync_indexed_columns` và `bulk_save` cùng ra một khoá; migration `forms_builder/0016` xuôi/ngược được và backfill đúng dòng cũ | FR-7.8 · ADR-036 | Tự động |
| AC-36.9 | Lưới Vận đơn: bôi đen có ô Sản phẩm, Số lượng, Giá tiền hay Số tiền thanh toán rồi Delete → hộp hỏi lại (Huỷ / Chỉ xoá ô thường / Bỏ chi tiết và xoá); chọn bỏ → máy chủ (`bo-chi-tiet/`) xoá mềm toàn bộ Chi tiết sản phẩm của dòng, bốn ô tổng trống, Trạng thái thanh toán giữ, có nhật ký; ô thường trong vùng xoá như cũ; Vận đơn Staff, Leader, Manager được, chỉ có quyền Xem hay ngoài phạm vi → 403 không đổi; giá trị cũ lệch → 409; cột khác → 400 | Chủ dự án 02.10.2026 · ADR-036 | Tự động |
| AC-36.10 | Hộp Chi tiết giữ như cũ (đơn chưa có chi tiết mở ra vẫn có một dòng chọn sản phẩm trống); Bỏ dòng xoá được cả dòng cuối, Thêm dòng thêm lại được; Lưu khi không còn dòng → đơn không còn sản phẩm, bốn ô tổng trống (cả đơn nhập từ tệp chỉ có chữ ở ô Sản phẩm); còn dòng chưa chọn sản phẩm (kể cả lỡ bấm Lưu ngay khi mở đơn chưa có chi tiết) → báo "chưa chọn sản phẩm", không đổi gì; Lên đơn mới vẫn bắt ít nhất 1 sản phẩm | Chủ dự án 02.10.2026 · ADR-036 | Tự động |
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
| AC-38.1 | Bảy thị trường US, CA, PH, EU, KR, JP, AU ↔ tám loại tiền; cột Thị trường và Loại tiền của bảng cấu hình trước 18.09 được bổ sung giá trị mới, giữ giá trị cũ, chạy lại không đổi, cột không phải Chọn một thì báo lỗi; nộp Hàn Quốc → KRW, Úc → AUD, quốc gia lạ bị từ chối; báo cáo không quy đổi (ADR-046): lẫn EUR, JPY, KRW thì mỗi loại tiền một dòng tổng đúng số đã nhập, tổng chung chỉ còn số đếm; JPY/KRW không phần lẻ; xếp hạng (còn quy đổi, Q71) quy EUR/AUD được, KRW chưa có tỉ giá thì báo rõ | ADR-031 bổ sung · ADR-046 | Tự động |
| AC-38.2 | DS Chốt (TT) — Doanh thu Marketing suy ra từ vận đơn, đúng số tiền theo loại tiền của đơn, không quy đổi (ADR-046); **từ ADR-047 (03.10.2026) báo cáo MKT bằng tiền Việt nên DS Chốt (TT) trống, Số đơn (TT) vẫn đối soát như dưới đây** (`WaybillItem.paid_amount` của đơn có Phụ trách Marketing là marketer trong phạm vi, cùng kỳ theo ngày lên đơn, cùng sản phẩm/quốc gia khi lọc) đúng ở mọi cách xem (ngày, nhân viên, sản phẩm, thị trường, phòng ban); tổng bằng tổng các dòng; đơn chưa phân công, marketer khác, ngoài kỳ, khác sản phẩm không vào; Staff chỉ thấy tiền của mình; Excel và Tổng quan cùng số; lọc Tệp khách hàng thì Doanh thu trống | ADR-038 | Tự động |
| AC-38.3 | Hóa đơn/DS Chốt (TT) (nhãn cũ Hóa đơn/Doanh thu) = Hóa đơn ÷ DS Chốt (TT) theo đúng nhãn (thay K/J 09.09) ở báo cáo nguồn và đường cũ; thiếu một vế thì trống; từ ADR-047 DS Chốt (TT) của báo cáo MKT trống nên Hóa đơn/DS Chốt (TT) cũng trống, Số đơn (TT) đếm đơn mọi loại tiền; `configure_erp_reports` không tạo cột nhập Doanh thu, gỡ trường đó khỏi biểu mẫu, bỏ cột tính từng dòng, chạy lại không đổi | ADR-038 | Tự động |
| AC-38.4 | Cột Tệp khách hàng (Chọn một) với danh sách mặc định theo sheet MKT có trên bảng Marketing, dữ liệu cũ giữ; **từ 03.10.2026 không còn trên biểu mẫu** (ADR-048); ghi giá trị ngoài danh sách bị từ chối; tầng dịch vụ lọc `segment` đúng giá trị, `__missing__` = chưa có, giá trị lạ → lỗi; màn Báo cáo tổng hợp nguồn Marketing bỏ qua `tep` — không lọc, không lỗi 400, không ô chọn, phụ đề Excel không ghi tệp (AC-48.3); Leader/Manager Marketing thêm giá trị vào cột được, Staff bị từ chối | ADR-038 · ADR-048 | Tự động |
| AC-38.5 | Chọn nhanh kỳ ở Báo cáo tổng hợp: Hôm nay, Hôm qua, 7 ngày (hôm nay − 6 → hôm nay), Tháng này, Tháng trước — đúng ngày theo giờ Việt Nam, điền hai ô ngày và áp ngay; nút khớp khoảng đang lọc được đánh dấu — chỉ một nút (AC-22.22) | ADR-038 | Tự động |

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
| AC-39.5 | Nhóm cột số lượng theo sản phẩm **mặc định ẩn với cả công ty**; thêm sản phẩm mới thì cột của nó cũng vào ở trạng thái ẩn dù chưa ai bấm nút; Lên đơn vẫn ghi số lượng vào cột đang ẩn nên hiện lại là có đủ dữ liệu; quản lý bảng bật lại được cả nhóm | FR-8.10 · ADR-039 | Tự động |
| AC-39.6 | Quản lý bảng thấy mục "Đang ẩn với cả công ty" để bật lại; nhân viên không thấy mục đó và không biết bảng có cột ẩn | FR-8.10 · ADR-039 | Tự động |
| AC-39.7 | Migration `forms_builder/0015` chạy xuôi và ngược đều được, giữ nguyên cột và dữ liệu | FR-8.10 · ADR-039 | Tự động |
| AC-39.8 | Bộ lọc trên URL trỏ tới cột đang ẩn **vẫn lọc đúng dòng** (lưới KN CRM, Bảng dữ liệu KN ERP, tệp Excel xuất ra), không bị bỏ lặng lẽ; KN CRM hiện chip cảnh báo "(cột đang ẩn) …" bỏ được bằng nút ×, KN ERP hiện dòng nhắc kèm tên cột; không lọc cột ẩn thì không có nhắc; lọc cột ẩn không mở đường xem dòng ngoài phạm vi quyền | FR-8.10 · ADR-039 | Tự động |
| AC-39.9 | Cột `sl_*` mọc trước 22.09 được migration `orders/0011` ẩn với cả công ty; chạy ngược không tự hiện lại và không mất dữ liệu ô | FR-8.10 · ADR-039 | Tự động |

## 40. KN CRM chỉ một bảng Vận đơn — ADR-040

| Mã | Tiêu chí | Yêu cầu gốc | Cách kiểm |
|---|---|---|---|
| AC-40.1 | Trang chủ KN CRM (ô số, Bảng gần đây, Hoạt động gần đây) và trang thư mục chỉ nhắc tới bảng vận đơn; bảng thường không xuất hiện dù người xem là Admin hay chính bộ phận sở hữu; sidebar chỉ có mục bộ phận có bảng vận đơn | FR-7.13 · ADR-040 | Tự động |
| AC-40.2 | KN CRM từ chối bảng thường ở mọi cửa như ngoài phạm vi (404/403, kể cả Admin): trang lưới, JSON đọc/ghi/lịch sử, xuất Excel, hộp lọc, màn Cột, Nhập tệp, Cấp quyền, mẫu nhập; bảng vận đơn vẫn phục vụ bình thường — kiểm cả hai chiều | FR-3.6 · ADR-040 | Tự động |
| AC-40.3 | Dữ liệu bảng thường **không đổi một dòng nào**: KN ERP vẫn xem Bảng dữ liệu, sửa cột, báo cáo như cũ; lọc theo cột ẩn/quyền không đổi; Thống kê KN CRM vẫn đọc nguồn Sale/MKT | BR-4 · ADR-040 | Tự động |
| AC-40.4 | Lõi lưới dùng chung không nhận nhầm cột trùng tên nghiệp vụ trên bảng thường (mức dịch vụ — bảng thường không còn cửa HTTP ở KN CRM) | FR-7.8 · ADR-040 | Tự động |
| AC-40.5 | Mục "Nhật ký" trên thanh bên KN CRM chỉ hiện cho Admin, đúng như trang Nhật ký chỉ Admin mở được (AC-44.2); Manager không thấy mục, gọi thẳng vẫn 403 (kiểm toàn diện 04.10.2026) | AC-44.2 · ADR-040 | Tự động |
| AC-40.6 | KN CRM không hiện liên kết dẫn tới trang bị từ chối: người không có bảng vận đơn trong phạm vi (Marketing, Sale chưa có đơn) không thấy "Bảng tính" ở thanh bên và trang chủ, nút ← của Lên đơn và "Quay lại" của đơn gốc về trang mở được; Nhập tệp, Cấp quyền không còn "+ Tạo bảng"; mọi liên kết trên trang chủ và các trang của thanh bên mở ra không 403/404 với 9 vai; quyền không đổi | FR-3.6 · ADR-040 | Tự động |
| AC-40.7 | Bảng dữ liệu KN ERP chỉ có nút "Mở trong KN CRM" và câu "Sửa số liệu ở KN CRM" với bảng vận đơn; bảng thường và bảng báo cáo Sale/MKT không có liên kết nào sang KN CRM (ở đó là 404), bảng báo cáo ghi "Số đã nộp do Leader hoặc quản lý sửa trong Lịch sử báo cáo" | ADR-014 · ADR-040 | Tự động |

## 42. Báo cáo tổng hợp như ảnh mẫu — ADR-042

Chủ dự án 23.09.2026, theo ảnh mẫu LUMI OMS: Báo cáo tổng hợp là màn hình đối tác thích nhất
nên giữ mọi chức năng đang có và nâng cấp cho giống ảnh. Đợt 1 là số liệu: tiền quy ₫ ngay trong
truy vấn rồi mới cộng (thay cách "để trống khi lẫn tiền" của ADR-038), ba cột đối soát từ vận đơn
"(TT)", Tỉ lệ chốt cho BC MKT, và hai lỗi thật (phân trang, chip Kỳ). Các đợt sau bổ sung tiêu chí
tiếp theo trong mục này.

| Mã | Đạt khi | Yêu cầu | Kiểm bằng |
|---|---|---|---|
| AC-42.1 | ~~**Tiền quy về ₫ trước khi cộng:** mọi cột kiểu Tiền nhân tỉ giá cố định (`EXCHANGE_RATES_VND`) theo loại tiền của **từng dòng** ngay trong truy vấn rồi mới cộng; hai báo cáo USD và EUR cùng ngày cùng người thành một dòng CPQC = 10×25.500 + 10×28.500 ₫; CPO, Giá Mess, AOV tính trên ₫; dòng Tổng bằng tổng dòng; ô hiện "540.000 ₫" không phần lẻ, tỉ lệ chốt hiện %; nhãn đơn vị nêu tỉ giá; Excel và Tổng quan cùng số; nguồn không ánh xạ Loại tiền vẫn cộng thô như cũ, không hậu tố ₫~~ **Rút 28.09.2026 — thay bằng AC-46.1 (ADR-046: không quy đổi).** | FR-5.4 · BR-8 · ADR-042 | Bỏ |
| AC-42.2 | ~~**Dòng không quy đổi được** (loại tiền chưa có tỉ giá như KRW, hoặc báo cáo cũ trống loại tiền): tiền của dòng đó không vào tổng, các cột đếm (Số Mess, Số đơn) vẫn tính đủ; cảnh báo nêu số dòng và loại tiền thiếu; dòng khác vẫn ra số ₫~~ **Rút 28.09.2026 — thay bằng AC-46.2 (ADR-046: không quy đổi).** | ADR-031 · ADR-042 | Bỏ |
| AC-42.3 | **Cột đối soát (TT) của BC MKT:** Số đơn (TT) = số vận đơn có Phụ trách Marketing là marketer theo ngày lên đơn, kể cả đơn không có chi tiết sản phẩm (đơn đó không góp tiền); DS Chốt (TT) = tiền đã thu của các đơn đó theo loại tiền của đơn (ADR-046 bỏ quy ₫); Tỉ lệ chốt (TT) = Số đơn (TT) ÷ Số Mess; lọc sản phẩm chỉ đếm đơn có sản phẩm đó; đơn chưa phân công không vào; Theo nhân viên cộng cả kỳ; Staff chỉ thấy của mình; không có đơn thì Số đơn (TT) là 0 chứ không trống | FR-5.1 · ADR-038 · ADR-042 | Tự động |
| AC-42.4 | **Ngân sách truy vấn với nguồn Marketing thật** (quy ₫ + đối soát vận đơn): cách xem Tổng hợp và Theo nhân viên mỗi cách không quá 10 truy vấn | Q2 · ADR-042 | Tự động |
| AC-42.5 | **Phân trang và chip Kỳ:** liên kết phân trang không mang `trang`/`moi_trang` cũ nên từ trang 2 sang trang khác đi đúng; chip Kỳ chỉ có dấu × khi kỳ khác mặc định — gửi đúng kỳ mặc định thì không × và không tính là đang lọc | AC-22.13 · ADR-042 | Tự động |
| AC-42.6 | **Bố cục khối như ảnh mẫu** (Báo cáo tổng hợp; từ 01.10.2026 dòng của khối ngày là từng lần nộp, AC-22.23): khối đầu là **toàn kỳ theo nhân sự** (STT · Team · Nhân sự · Leader, mỗi người một dòng cộng cả kỳ, TỔNG CỘNG toàn kỳ đứng ngay dưới hàng tiêu đề cột — trên màn hình từ 02.10.2026 mỗi cột định danh một ô, nhãn ngắn ở ô Nhân sự, AC-22.25 —, sắp theo mã); rồi **mỗi ngày một bảng riêng** mới nhất trước, tiêu đề ngày đặt trên bảng, không có cột Ngày, TỔNG CỘNG của ngày bằng tổng các dòng con và cột tính tính lại từ tổng, STT đếm lại từ 1; khối toàn kỳ cộng trong bộ nhớ, không thêm truy vấn; ngày bị tách trang thì trang sau ghi "(tiếp)" và lặp TỔNG CỘNG đủ cả ngày; Excel hai sheet "Toan ky theo nhan su" và "Theo ngay" cùng khối, cùng số | FR-5.1 · FR-5.4 · ADR-035 · ADR-042 | Tự động + trình duyệt |
| AC-42.7 | **Gộp / Không gộp** (`gop=1`): nguồn Sale/MKT Gộp là một bảng mọi lần nộp trong kỳ (Ngày · Nhân sự · Lần nộp, thêm Loại tiền khi nguồn tách loại tiền — báo cáo Marketing ẩn cả Lần nộp lẫn Loại tiền từ 03.10.2026, AC-47.6, báo cáo Sale ẩn Lần nộp từ 04.10.2026, AC-47.7; 01.10.2026 — trước đó mỗi ngày một dòng TỔNG CỘNG, nay chỉ còn ở nguồn Vận đơn), khối toàn kỳ vẫn đứng đầu; chip "Gộp" có × để về Không gộp; từ 02.10.2026 bấm Gộp / Không gộp không tải lại trang (AC-22.26); Excel sheet "Theo ngay" cùng khối, cùng số với màn hình | ADR-035 · ADR-042 | Tự động |
| AC-42.8 | **Màu ba bậc theo ngưỡng tuyệt đối:** chỉ tiêu có ngưỡng (`ReportSource.thresholds`) tô xanh khi đạt mốc Tốt, đỏ khi qua mốc Kém, vàng ở giữa, đúng chiều tốt (Tỉ lệ chốt càng cao càng tốt, CPO càng thấp càng tốt); dòng TỔNG CỘNG cũng tô; chỉ tiêu chưa có ngưỡng giữ cách so với dòng Tổng ±10 % (AC-22.16); màu lấy từ token nên đúng ở chế độ sáng và tối; ngưỡng tiền đặt theo ₫ chỉ tô dòng VND (ADR-046, AC-46.6) | FR-8.8 · ADR-042 | Tự động + trình duyệt |
| AC-42.9 | **Form Ngưỡng màu:** chỉ Admin hoặc quản lý (Leader, Manager) của bộ phận sở hữu nguồn thấy và lưu được (302, có nhật ký Sửa); Staff và quản lý bộ phận khác bị 403 có nhật ký từ chối và không thấy form; mốc sai thứ tự theo chiều tốt, thiếu một mốc hay không phải số thì báo lỗi bằng tiếng Việt và không lưu; để trống cả hai mốc thì bỏ ngưỡng của chỉ tiêu đó | FR-8.8 · ADR-042 | Tự động |
| AC-42.10 | Migration `reports/0005` (cột `thresholds`) chạy xuôi và ngược đều được, không đụng dữ liệu nghiệp vụ | ADR-042 | Tự động |
| AC-42.11 | **Lọc nhiều sản phẩm:** tham số `sp` lặp lại (tick nhiều mục có ô tìm nhanh, Chọn tất cả / Bỏ chọn), tổng và phần đối soát (TT) đúng theo các sản phẩm đã chọn; URL cũ một sản phẩm `sp=A` vẫn đúng; danh sách tick chỉ gồm sản phẩm có thật trong phạm vi quyền (Leader không thấy hàng team khác); chip "N sản phẩm"; phụ đề Excel ghi danh sách. Từ 03.10.2026 bộ lọc trên màn chỉ còn ở nguồn Sale — nguồn Marketing bỏ (ADR-048, AC-48.3); tầng dịch vụ vẫn nhận nhiều sản phẩm | FR-5.3 · ADR-042 · ADR-048 | Tự động |
| AC-42.12 | **Chọn nhanh "Tuần này"** (thứ Hai tuần này tới hôm nay, kể cả tuần vắt qua tháng) đứng sau "7 ngày" trong dãy Chọn nhanh của Báo cáo tổng hợp | FR-5.3 · ADR-042 | Tự động |
| AC-42.13 | **Bảng dữ liệu của bảng có nguồn báo cáo Sale/MKT là báo cáo chi tiết theo ngày** dùng chung động cơ với Báo cáo tổng hợp (tiền đúng như nhập theo loại tiền, cột và nhãn theo nguồn, ngưỡng màu, (TT)): mặc định chế độ Từng lần nộp (ADR-046) — **mỗi lần nộp một dòng**, hai lần nộp cùng ngày cùng người là hai dòng với STT riêng và cột Lần nộp; khối toàn kỳ theo nhân sự đứng đầu, mỗi ngày một bảng có TỔNG CỘNG; (TT) trên dòng người chỉ hiện khi bộ (ngày, người, loại tiền) nộp một lần, nộp nhiều lần thì "—" và TỔNG CỘNG ngày vẫn đúng, không cộng đôi; bộ lọc Kỳ, Chọn nhanh, Chế độ, Sản phẩm, Thị trường, Tệp, Team, Nhân sự và Gộp (Từng lần nộp: một khối mọi lần nộp; Cộng theo ngày: mỗi ngày một dòng); mặc định 25 dòng một trang; `?dang=tho` về liệt kê thô có liên kết quay lại và mọi liên kết giữ `dang=tho`; bảng không có nguồn giữ nguyên; Staff chỉ thấy dòng của mình, bộ phận khác 404; Xuất tệp ra Excel cùng khối; form Ngưỡng màu cho quản lý; không quá 10 truy vấn | FR-7.1 · FR-5.4 · ADR-014 · ADR-042 | Tự động |
| AC-42.14 | **Liệt kê thô của Bảng dữ liệu:** liên kết phân trang và sắp xếp giữ tìm kiếm, bộ lọc cột và cỡ trang, cột đang sắp có `aria-sort`; ô Đúng/sai hiện "Có"/"Không"; nút "Sửa cột" chỉ hiện với Admin hoặc quản lý bộ phận sở hữu bảng — quản lý bộ phận khác chỉ được cấp quyền xem không thấy, gọi thẳng vẫn 403; trạng thái rỗng không còn nhắc "phần 3B" | FR-7.2 · FR-7.3 · ADR-015 · ADR-042 | Tự động |
| AC-42.15 | Báo cáo tổng hợp không còn đầu trang "Báo cáo tổng hợp / Kết quả thực tế…" (tên trang ở thanh trên); khung bảng kéo dài tới sát đáy vùng nội dung (`--report-fit` do `report-filters.js` đo; khung nằm thấp thì cao bằng cả vùng nội dung); bộ lọc bên trái đứng yên, cao vừa vùng nội dung, cuộn riêng — lăn trên bộ lọc thì trang và bảng đứng yên; kéo bộ lọc tới cuối là tới nút Áp dụng (AC-42.17) | Chủ dự án 03.10.2026 · ADR-042 | Trình duyệt |
| AC-42.16 | Lệnh `nap_bao_cao_mau` (chỉ khi DEBUG bật): nộp báo cáo Marketing mẫu qua service cho `--nguoi` tài khoản mẫu khoá đăng nhập, `--lan` lần mỗi ngày từ ngày 1 tháng trước tới hôm nay; chạy lại không trùng; `--xoa-cu` chỉ xoá báo cáo mẫu | Chủ dự án 03.10.2026 | Tự động |
| AC-42.17 | Thanh cuộn của bộ lọc kéo được tới nút Áp dụng mà không phải cuộn cả trang: trang đang ở đầu, kéo bộ lọc tới cuối thì đáy bộ lọc không quá đáy vùng nội dung, nút Áp dụng nằm trọn trong vùng nhìn thấy và bấm trúng — bộ lọc cao từ chỗ nó đứng tới đáy vùng nội dung (`--report-panel-fit` do `report-filters.js` đo, như khung bảng); nguồn Sale và MKT, 1366×768 và 1366×600 (TL-73) | Chủ dự án 04.10.2026 · ADR-042 | Trình duyệt |

## 43. Form Nộp báo cáo ngày: chọn Team, bắt buộc, bỏ Hóa đơn, bố cục ngang — ADR-043

Chủ dự án góp ý 24.09.2026 sau khi xem thử trên local. Kết quả tại
[biên bản form nhập báo cáo](kiem-chung-form-nhap-bao-cao-20260924.md).

| Mã | Tiêu chí | Nguồn | Cách kiểm |
|---|---|---|---|
| AC-43.1 | **Dropdown Team trên form nộp báo cáo:** liệt kê team đang hoạt động của bộ phận sở hữu biểu mẫu (không lẫn team bộ phận khác), chọn sẵn team trong hồ sơ; nộp với team khác trong bộ phận thì dòng dữ liệu và báo cáo mang team đó — Leader team ấy xem và sửa được, Leader team khác không thấy; team bộ phận khác hay id lạ bị từ chối nêu rõ, không lưu; để trống thì theo hồ sơ; bộ phận không có team thì không có ô Team | FR-4.8 · ADR-043 | Tự động |
| AC-43.2 | **Bốn trường bắt buộc:** sau `configure_erp_reports` form MKT bắt buộc Số Mess, CPQC, Số đơn, Doanh số (cùng Ngày; Sản phẩm, Thị trường rời form MKT từ 03.10.2026 — ADR-048), form Sale bắt buộc Số Mess, Số đơn, Doanh số cùng Sản phẩm, Thị trường (ô Ngày ra đơn rời form Sale, AC-48.7); trường đã có từ trước cũng bị ép; nộp thiếu bị từ chối nêu tên trường, không tạo dòng; "0" hợp lệ; các ô đó mang `required` phía trình duyệt, ô hệ thống và ô không bắt buộc thì không | FR-4.9 · AC-8.2 · ADR-043 | Tự động |
| AC-43.3 | **Bỏ Hóa đơn khỏi form nhập MKT:** form đang có trường Hóa đơn thì `configure_erp_reports` gỡ và không tạo lại; cột `hoa_don`, ánh xạ `invoice`, hai cột báo cáo "Hóa đơn" và "Hóa đơn/DS Chốt (TT)" vẫn còn cho dữ liệu cũ; giá trị `hoa_don` gửi thẳng lên bị bỏ qua | FR-4.10 · ADR-043 | Tự động |
| AC-43.4 | **Bố cục ngang, ô nhỏ:** form là một thẻ trải hết chiều rộng nội dung — hàng điều khiển Biểu mẫu · Team · Ngày, lưới ô nhập ngang (`bm-ngang`, ô cao ≤ 36 px, nhiều ô một hàng ở 1440, hai cột ở 390, không tràn ngang), cột tính sẵn là dòng chip thay cho ô nhập giả (từ 02.10 là thẻ xem trước chỉ số, AC-43.6); màn Sửa báo cáo cùng lưới; cùng bộ điều khiển và token Solarpunk, sáng và tối | FR-4.11 · ADR-028 · ADR-043 | Tự động + trình duyệt |
| AC-43.5 | **Một ô Team duy nhất:** bảng báo cáo Sale/MKT có sẵn cột Team dạng chữ (mã `team` hay nhãn "Team") thì `configure_erp_reports` gỡ ô nhập của cột đó, không tạo lại và ghi ánh xạ `team`; form chỉ còn một ô Team là dropdown; khi nộp, hệ thống ghi tên team đã chọn (không chọn thì team hồ sơ) vào cột, chữ gõ tay gửi thẳng lên bị bỏ; người chưa có team và không chọn thì cột trống, vẫn nộp được; Bảng dữ liệu vẫn hiện tên team ở cột đó | FR-4.8 · ADR-043 bổ sung 25.09 | Tự động + trình duyệt |
| AC-43.6 | **Xem trước chỉ số khi nộp** (khách hàng yêu cầu, chủ dự án chốt mockup 02.10.2026): form Nộp báo cáo có khối "Xem trước chỉ số" thay dòng chip "Hệ thống tự tính khi nộp" — mỗi cột tính sẵn một thẻ (tên, giá trị, công thức nhỏ); gõ Số Mess, CPQC, Số đơn, Doanh số là thẻ tính ngay theo đúng công thức của cột, làm tròn như máy chủ; tiền ÷ số đếm (CPO, Giá Mess, AOV) hiện hai số lẻ kèm loại tiền theo Thị trường (form Marketing không còn ô Thị trường, Loại tiền: kèm loại tiền cố định VND, ADR-048, AC-48.5), phần trăm hai số lẻ kèm "%", tỉ số khác theo số lẻ của cột; thiếu số hiện "—", chia cho 0 báo rõ; thẻ có ô vừa sửa sáng viền, Tỉ lệ chốt > 100 % tô vàng; nộp thì máy chủ vẫn tự tính và lưu, làm tròn về số lẻ của thẻ trùng số đã xem trước; đơn vị suy một chỗ (`daily_service.preview_columns`), không thêm truy vấn theo số thẻ | FR-4.8 · ADR-043 bổ sung 02.10 | Tự động + trình duyệt |

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


## 44. Team hệ thống và quyền menu ERP — quyết định 25.09.2026

Thay thế quyền chọn Team của Staff/Leader/Manager ở AC-43.1, cùng các kỳ vọng cũ
cho phép các cấp này mở màn ERP bị giới hạn dưới đây. CRM và phạm vi dữ liệu
bản thân/team/bộ phận giữ nguyên; [ADR-045](quyet-dinh/045-team-he-thong-va-quyen-menu-erp.md).

| Mã | Tiêu chí |
|---|---|
| AC-44.1 | Staff/Leader/Manager thấy một Team chỉ đọc theo hồ sơ; POST giả Team/tên Team không chuyển báo cáo sang team khác. Admin giữ chọn Team hợp lệ. Không team vẫn nộp; sửa báo cáo cũ giữ team dù hồ sơ đổi team. CEO không nộp báo cáo. |
| AC-44.2 | Chỉ Admin thấy Quản trị và mở Nhật ký, Ma trận quyền, danh sách Tác vụ ERP; vai trò khác gọi URL trực tiếp bị 403. |
| AC-44.3 | Staff/Leader không thấy mục Bảng dữ liệu ERP và bị chặn cả đọc/xuất/quản lý bảng; Manager trong phạm vi, CEO/Admin toàn công ty; Biểu mẫu & tài liệu giữ quyền. |
| AC-44.4 | Staff/Leader/Manager/CEO mở tiến độ, tải file của chính mình; tác vụ người khác 404. Không hiện liên kết danh sách quản trị bị cấm. |
| AC-44.5 | Leader vẫn quản lý bảng trong phạm vi tại CRM; không siết quyền theo giới hạn ERP, giữ KN CRM và lên đơn theo quyết định hoãn. |
| AC-44.6 | CEO đọc được bảng nhiều bộ phận, không có quyền sửa ô ERP hoặc quyền Quản trị; không hiện lối nộp báo cáo, GET/POST nộp hoặc sửa trực tiếp bị chặn. Kiểm trên bản CEO thật. |

## 46. Chế độ số liệu: không quy đổi, mỗi dòng một loại tiền — ADR-046

Chủ dự án 28.09.2026: CPQC nhập 13 250 000 mà báo cáo hiện số khổng lồ (bị quy ₫ theo loại tiền của
thị trường); "cần con số giữ nguyên, đã có trường đơn vị ngay bên cạnh"; "báo cáo 2 lần trong 1 ngày thì
lần 1 8000 lần 2 7000 thì cứ hiển thị ra như thế". Duyệt mockup "Chế độ xem số liệu" và ba câu hỏi cùng
ngày. Thay AC-42.1, AC-42.2; [ADR-046](quyet-dinh/046-che-do-so-lieu-khong-quy-doi.md); kết quả ở
[biên bản](kiem-chung-che-do-so-lieu-20260928.md).

| Mã | Đạt khi | Yêu cầu | Kiểm bằng |
|---|---|---|---|
| AC-46.1 | **Không quy đổi:** tiền hiện đúng số đã nhập, không nhân tỉ giá, không hậu tố ₫; nguồn có cột Loại tiền thì mỗi dòng một loại tiền (USD và EUR cùng ngày cùng người là hai dòng), CPO/Giá Mess tính trong từng loại tiền; TỔNG CỘNG tách theo loại tiền ("TỔNG CỘNG · USD", ô Loại tiền riêng); tổng chung khi lẫn loại tiền chỉ giữ số đếm; chú thích nói rõ không quy đổi; Excel cùng số; nguồn không ánh xạ Loại tiền thì không tách | FR-5.4 · BR-8 · ADR-046 | Tự động |
| AC-46.2 | **Dòng chưa có loại tiền** (báo cáo cũ) thành nhóm "Chưa rõ" xếp cuối, không cộng vào loại tiền nào, có cảnh báo nêu số dòng và cách sửa; KRW hiện như mọi loại tiền, không còn cảnh báo "chưa quy đổi" | ADR-031 · ADR-046 | Tự động |
| AC-46.3 | **Từng lần nộp trên màn hình** (bổ sung 01.10.2026: bỏ ô Chế độ `che_do`, AC-22.23): Báo cáo tổng hợp và Bảng dữ liệu luôn mỗi lần nộp một dòng số đúng như nhập, cột Lần nộp "Lần N · giờ" đếm theo giờ nộp trong ngày của người đó, khối toàn kỳ vẫn đầu và cộng theo người cùng loại tiền, TỔNG CỘNG ngày theo loại tiền, Gộp là một khối mọi lần nộp; tầng service vẫn có Cộng theo ngày (mỗi người mỗi ngày một dòng mỗi loại tiền, nộp nhiều lần thì cộng cùng loại tiền) cho Tổng quan; nguồn Vận đơn không có lần nộp | FR-4.2 · FR-5.13 · ADR-046 | Tự động |
| AC-46.4 | **Excel như màn hình:** từng lần nộp có cột Lần nộp, Loại tiền (báo cáo Marketing ẩn cột Lần nộp, Loại tiền, AC-47.6), số thô đúng như nhập, TỔNG CỘNG theo loại tiền; Gộp là khối mọi lần nộp; phụ đề không còn "Chế độ:" (01.10.2026) | FR-5.6 · ADR-046 | Tự động |
| AC-46.5 | **(TT) của báo cáo MKT** (thay bởi ADR-047, 03.10.2026): báo cáo MKT bằng tiền Việt nên (TT) không khoá theo loại tiền; đơn mọi loại tiền của marketer vào Số đơn (TT) của dòng VND; DS Chốt (TT) trống vì không quy đổi; TỔNG CỘNG · VND cộng đúng Số đơn (TT) | ADR-038 · ADR-046 · ADR-047 | Tự động |
| AC-46.6 | **Màu theo loại tiền:** so tương đối ±10 % với TỔNG CỘNG cùng loại tiền; ngưỡng tiền (CPO, Giá Mess, AOV) đặt theo ₫ chỉ tô dòng VND, ngưỡng tỉ lệ tô mọi loại tiền; form Ngưỡng màu nói rõ | FR-8.8 · ADR-046 | Tự động |
| AC-46.7 | **Thẻ Tổng quan:** mỗi chỉ tiêu một hàng, mỗi loại tiền một cột có tiêu đề mã tiền; số đúng như nhập, không cộng hai loại tiền | ADR-046 | Tự động |
| AC-46.8 | **Bảng dữ liệu xem thô** in số có dấu chấm ngăn nghìn (13250000 → 13.250.000), giữ nguyên số lẻ đã lưu, không ký hiệu tiền | FR-7.1 · ADR-046 | Tự động |
| AC-46.9 | **Truy vấn:** tách loại tiền và chế độ Từng lần nộp không thêm truy vấn ở đường trong bộ nhớ (≤ 10, như AC-42.4); đường quá trần: tổng theo loại tiền đúng, "Lần N" đếm đúng qua ranh giới trang | Q2 · ADR-046 | Tự động |
| AC-46.10 | **Ô số trên form nộp báo cáo:** gõ toàn chữ số thì dấu chấm tự chèn ngay khi gõ; tự gõ "." hay "," thì rời ô mới viết lại theo luật `parse_money` ("8000.50" → "8.000,5", không thành 800.050); dán "13 250 000" → "13.250.000"; ô số nguyên không phần lẻ; máy chủ lưu đúng số | BR-8 · ADR-046 | Tự động + trình duyệt |

## 47. Báo cáo Marketing nộp bằng tiền Việt — ADR-047

Chủ dự án 03.10.2026: "tất cả số trong báo cáo được nộp đều là tiền Việt"; "cái bảng báo cáo tổng hợp hiện tại
quy ra VND"; không có tỉ giá nào được duyệt; làm Marketing trước. [ADR-047](quyet-dinh/047-bao-cao-mkt-tien-viet.md);
[biên bản](kiem-chung-bao-cao-mkt-tien-viet-20261003.md).

| Mã | Đạt khi | Yêu cầu | Kiểm bằng |
|---|---|---|---|
| AC-47.1 | Một chỗ quyết định loại tiền của báo cáo ngày (`currency_service.report_currency`): Marketing luôn VND dù Thị trường nào (kể cả trống); Sale theo Thị trường như ADR-031 | ADR-047 | Tự động |
| AC-47.2 | Nộp báo cáo MKT chọn Canada → lưu VND; đổi Thị trường trên dòng vẫn VND; form không còn ô Thị trường, Loại tiền (từ 03.10.2026, ADR-048) — loại tiền do hệ thống ghi —, ô tiền ghi "(₫)"; báo cáo Sale vẫn Canada → CAD | ADR-047 · ADR-048 | Tự động |
| AC-47.3 | Tệp chuyển đổi `reports/0006`: dòng báo cáo MKT cũ mang CAD/USD/trống đổi nhãn sang VND, **số giữ nguyên**, VND có trong lựa chọn của cột; bảng Sale không đổi; chạy ngược thì nhãn lấy lại theo Thị trường | ADR-047 · quy tắc 4 | Tự động |
| AC-47.4 | Báo cáo tổng hợp MKT: một dòng TỔNG CỘNG · VND; Số đơn (TT) đếm đúng đơn của marketer dù đơn bằng CAD/USD; DS Chốt (TT) trống (không quy đổi); số tiền đúng như nhập; ngưỡng tiền đặt theo ₫ tô được dòng MKT | ADR-047 | Tự động |
| AC-47.5 | Báo cáo tổng hợp MKT (màn hình, Excel, Tổng quan) không còn cột Hóa đơn và Hóa đơn/DS Chốt (TT); cột dữ liệu Hóa đơn trong bảng giữ nguyên | Chủ dự án 03.10.2026 · ADR-047 | Tự động |
| AC-47.6 | Báo cáo tổng hợp, Bảng dữ liệu dạng báo cáo và Excel của nguồn MKT không còn cột Lần nộp, Loại tiền ở khối toàn kỳ, ngày, Gộp (`layout.HIDDEN_IDENTITY`); hai lần nộp cùng ngày vẫn hai dòng; nguồn Sale giữ cột Loại tiền (cột Lần nộp của Sale ẩn từ 04.10.2026, AC-47.7) | Chủ dự án 03.10.2026 · ADR-047 | Tự động |
| AC-47.7 | Báo cáo tổng hợp, Bảng dữ liệu dạng báo cáo và Excel của nguồn Sale không còn cột Lần nộp ở khối toàn kỳ, ngày, Gộp (`layout.HIDDEN_IDENTITY`) nhưng giữ cột Loại tiền; hai lần nộp cùng ngày vẫn hai dòng; TỔNG CỘNG vẫn tách theo loại tiền | Chủ dự án 04.10.2026 · ADR-047 bổ sung | Tự động |

## 48. Form báo cáo Marketing bỏ bốn ô — ADR-048

Chủ dự án 03.10.2026: "Bỏ cả bốn ô" Sản phẩm, Thị trường, Tệp khách hàng, Loại tiền khỏi form Nộp báo cáo Marketing;
tiền vẫn là VND (ADR-047); cột và dữ liệu cũ giữ. Bổ sung cùng ngày: form Sale bỏ ô Ngày ra đơn (AC-48.7).
[ADR-048](quyet-dinh/048-form-mkt-bo-bon-o.md);
[biên bản](kiem-chung-mkt-bo-bon-o-20261003.md).

| Mã | Đạt khi | Yêu cầu | Kiểm bằng |
|---|---|---|---|
| AC-48.1 | Sau `configure_erp_reports` form Nộp báo cáo Marketing không còn Sản phẩm, Thị trường, Tệp khách hàng, Loại tiền, chạy lại vẫn không đưa về; bốn cột và ánh xạ `market`, `currency`, `segment` của nguồn giữ nguyên cho dòng cũ; trang nộp không còn ô nào của bốn cột; form Sale vẫn bắt buộc Sản phẩm và Thị trường | ADR-048 · ADR-043 | Tự động |
| AC-48.2 | Nộp báo cáo Marketing chỉ với các ô số (không Thị trường, Sản phẩm) lưu được, dòng mang Loại tiền VND; Sửa báo cáo không đòi Thị trường; cờ bắt buộc cấp cột của bốn cột (nếu từng bật tay) bị gỡ khi chạy lệnh cấu hình; dòng tạo qua đường nhập bảng không có Thị trường cũng ra VND; Sale nộp thiếu Thị trường vẫn bị từ chối, không lưu | ADR-048 · ADR-047 | Tự động |
| AC-48.3 | Nguồn Marketing: Báo cáo tổng hợp và Bảng dữ liệu không còn bộ lọc Sản phẩm, Thị trường, Tệp khách hàng; URL cũ có `sp`, `thi_truong`, `tep` (kể cả giá trị lạ) vẫn mở được (200, không lỗi 400), không chip, không lọc mất dòng; tệp Excel của cả hai màn không ghi chúng ở dòng phụ; nguồn Sale vẫn đủ ba bộ lọc | ADR-048 · ADR-042 | Tự động |
| AC-48.4 | Báo cáo Marketing toàn VND: bảng không có cột Loại tiền (ẩn theo AC-47.6), Nhân sự là cột đứng yên cuối (bóng mép ở ô Nhân sự); đơn vị ghi một lần: "Tiền: ₫" ở hàng tiêu đề kết quả và câu "Mọi số tiền là tiền Việt (₫), không quy đổi"; Excel không có cột Loại tiền nhưng giữ nhãn "TỔNG CỘNG · toàn kỳ · VND"; có dòng lỡ mang loại tiền khác (nhãn ghi tay) thì cột vẫn ẩn (chủ dự án 03.10.2026) và hàng tiêu đề không còn ghi "Tiền: ₫" | ADR-048 · ADR-047 · AC-47.6 | Tự động |
| AC-48.5 | Trình duyệt: form Nộp báo cáo Marketing không còn bốn ô; gõ CPQC và Số đơn thì thẻ CPO hiện kèm "VND" (đơn vị lấy từ `data-tien` khi không có ô Loại tiền); bấm Nộp chỉ với các ô số thì lưu được, dòng mang Loại tiền VND; không lỗi JavaScript | ADR-048 · AC-43.6 | Tự động + trình duyệt |
| AC-48.6 | Thống kê KN CRM nguồn Marketing không còn biểu đồ "Đóng góp theo sản phẩm" (biểu đồ theo Marketer vẫn còn); nguồn Sale vẫn có biểu đồ theo sản phẩm | ADR-048 | Tự động |
| AC-48.7 | Sau `configure_erp_reports` form Nộp báo cáo Sale không còn ô Ngày ra đơn, chạy lại vẫn không đưa về; cột Ngày ra đơn và dữ liệu cũ giữ nguyên; cờ bắt buộc cấp cột (nếu từng bật tay) bị gỡ; trang nộp Sale không còn ô đó, nộp Sale đủ các ô còn lại vẫn lưu được | ADR-048 bổ sung · ADR-043 | Tự động |
