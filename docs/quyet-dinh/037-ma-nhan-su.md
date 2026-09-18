# ADR-037 — Mã nhân sự theo quy ước THUANLT, cố định, là tên đăng nhập của tài khoản mới

| Mục | Nội dung |
|---|---|
| Trạng thái | Đã áp dụng local (chờ phát hành VPS kèm lệnh gán mã cũ) |
| Ngày | 18.09.2026 |
| Người quyết định | Chủ dự án (tệp `Quản trị nội bộ.xlsx`, sheet Quy ước-Định nghĩa mục 1.0 và 2.0; ba câu hỏi trả lời trong phiên Claude Code) |
| Bổ sung cho | ADR-013 (danh tính người điền do hệ thống ghi), ADR-035 (cột Nhân sự/Leader) |

## Bối cảnh

Sheet Quy ước-Định nghĩa chốt: tài khoản đăng nhập `User = MÃ_NV`; mã nhân sự là **TÊN +
chữ cái đầu họ + chữ cái đầu tên đệm**, viết hoa không dấu, viết liền — Lê Thưởng Thuận
→ `THUANLT`; đã có thì người sau thêm số từ 2: `THUANLT2`, `THUANLT3`. Sheet MKT ghi mọi
dòng báo cáo theo mã (`D14 = THUANLT`).

Hệ thống tới 18.09 chưa có trường mã: `core/identity.employee_code()` trả tên đăng nhập,
ô Người bán/Marketer chụp tên đăng nhập lúc tạo dòng, Báo cáo tổng hợp hiện
"username — họ tên", và có hơn mười chỗ tự ghép `username` thay vì đi qua `core/identity`.
Tài khoản đang dùng trên VPS có tên đăng nhập kiểu `sale.staff`; đổi tên đăng nhập của
người đang dùng là đổi thói quen và đổi dữ liệu đã chụp.

## Các lựa chọn đã cân nhắc

| Lựa chọn | Ưu | Nhược |
|---|---|---|
| A. Mã chính là tên đăng nhập, đổi tên đăng nhập người cũ theo quy tắc | Một trường, đúng "User = MÃ_NV" | Đổi tên đăng nhập trên VPS của mọi người; phải đổi cả dữ liệu chụp; không có chỗ giữ tên cũ |
| B. Trường riêng `staff_code`; tài khoản mới có tên đăng nhập = mã; tài khoản cũ giữ tên, chỉ gán mã | Không phá đăng nhập đang dùng; mã cố định độc lập với tài khoản; vẫn đúng "User = MÃ_NV" cho người mới | Hai trường cùng tồn tại; cần lệnh gán mã cho hồ sơ cũ và đổi dữ liệu chụp |
| C. Không lưu, suy mã từ họ tên mỗi lần hiển thị | Không migration | Trùng họ tên thì mã đổi theo thứ tự tạo; đổi họ tên là đổi mã — trái yêu cầu cố định |

## Quyết định

Chọn **B**.

1. `UserProfile.staff_code` (CharField 20, viết hoa không dấu, chỉ `A–Z0–9`, bắt đầu bằng
   chữ), duy nhất khi khác rỗng. **Cố định**: đã có thì không đổi được, kể cả Admin; hồ sơ
   lưu mà mã rỗng thì hệ thống tự gán theo quy tắc, nên **mọi hồ sơ luôn có mã**.
2. Quy tắc gợi ý ở `org/services/staff_code_service.py`: từ cuối của họ tên là TÊN, cộng
   chữ cái đầu của từng từ đứng trước; bỏ dấu (`đ → d`), viết hoa; trùng thì thêm `2, 3…`;
   trùng cả với tên đăng nhập của người khác cũng phải nhảy số, vì tài khoản mới dùng mã làm
   tên đăng nhập. Họ tên không cho ra mã hợp lệ thì lấy chữ và số của tên đăng nhập.
3. **Tài khoản mới: tên đăng nhập = mã** (Admin có thể gõ tên đăng nhập khác khi cần).
   **Tài khoản đã có giữ tên đăng nhập**, chỉ được gán mã. Đăng nhập không phân biệt
   hoa/thường (`core/auth_backends.CaseInsensitiveModelBackend`; tạo tài khoản đã kiểm
   `username__iexact` nên không có hai tài khoản chỉ khác hoa/thường).
4. **Một nguồn danh tính** `core/identity.py`: `employee_code()` trả mã; `identity_label()`
   trả `MÃ · Họ tên`; `code_expression()`/`label_expression()` cho truy vấn ORM. Mọi màn
   hình, danh sách, lịch sử, Excel, nhật ký hiện **mã trước, tên sau**; lời chào và avatar
   giữ họ tên (`|ten`). Không chỗ nào tự ghép `username` nữa; lọc/tìm theo mã.
5. Ô danh tính chụp vào bảng động (`nguoi_ban`, `marketer`, `sale`) ghi mã. Dữ liệu cũ đang
   chứa tên đăng nhập được đổi bằng lệnh chạy một lần `gan_ma_nhan_su_cu` (có `--thu`, chỉ đổi
   giá trị khớp đúng một tên đăng nhập, chạy lại không đổi thêm), chạy trên VPS sau khi gán mã.

## Lý do

Quy ước là của công ty và đã có trong tệp thật; hệ thống chỉ cần một chỗ giữ và một chỗ
hiển thị. Trường riêng giữ được người đang dùng, còn "mã = tên đăng nhập" áp cho người mới
để đúng sheet mà không phải đổi ai. Tự gán khi rỗng để không có hồ sơ "nửa vời" khiến lọc
theo mã hụt dòng.

## Hệ quả

**Được gì:** định danh thống nhất toàn hệ thống; báo cáo, vận đơn, nhật ký cùng một mã;
tìm theo mã; Excel xuất đúng như sheet.

**Mất gì:** thêm một migration và một lệnh phát hành; bài kiểm so chuỗi tên đăng nhập
phải đổi sang mã; nhãn "username — họ tên" thành "MÃ · Họ tên".

**Chỗ cần cẩn thận về sau:** đổi họ tên **không** đổi mã (cố ý); mã trùng phải nhảy số,
không sửa tay; lệnh gán mã cũ không đụng giá trị lạ; `EXECUTIVE_OWNER_USERNAMES` vẫn là tên
đăng nhập (cấu hình, không phải định danh nghiệp vụ).

## Bổ sung 18.09.2026 (tối) — bảng Báo cáo tổng hợp chỉ hiện mã

Chủ dự án so bản local với VPS và chốt: trong **bảng và Excel của Báo cáo tổng hợp**, cột Nhân sự,
Leader và dòng ở cách xem Theo nhân viên **chỉ hiện mã** (`code_expression`; chưa gán mã thì tên
đăng nhập, sau `gan_ma_nhan_su_cu` sẽ là mã), không kèm họ tên — vì ô hẹp, cách xem Tổng hợp gộp
nhiều người trong một ô, kèm tên thì xuống dòng và bảng tràn. Ô chọn Nhân sự, chip bộ lọc, ô Tìm nhân
sự và mọi màn hình khác **giữ nguyên `MÃ · Họ tên`** theo mục 4. Khoá nối Doanh thu suy ra
(`marketing_revenue`) đổi cùng biểu thức để vẫn khớp dòng. Không đổi `identity_label()`.

## Điều kiện xem lại

Khi công ty đổi quy ước mã, hoặc khi cần nhập nhân sự hàng loạt từ HCNS (khi đó gợi ý mã
chuyển sang tệp nhập).
