# ADR-023 — Điều hướng ERP, thư viện hai tab và một nơi lên đơn tại CRM

Ngày: 11.09.2026. Chủ dự án duyệt kế hoạch trong hội thoại. Đã triển khai local.

## Quyết định thay thế

- Thay phần giữ hai trang Lên đơn của ADR-019: CRM là nơi lên đơn duy nhất. ERP giữ URL GET chuyển tiếp; POST cũ bị từ chối, không chuyển tiếp yêu cầu ghi.
- Không có menu danh sách Đơn hàng riêng. Sau khi tạo và trong chi tiết vận đơn có liên kết Xem đơn gốc; mở từ lưới sang tab mới để giữ nháp. Đơn gốc vẫn bất biến; thao tác bỏ đơn giữ quyền người tạo và soft delete hiện có.
- Quyền xem đơn gốc tiếp tục dùng phạm vi Order. Quyền xem dòng vận đơn không tự cấp quyền đọc đơn gốc; dòng không có liên kết hoặc ngoài quyền không có nút và truy cập trực tiếp bị từ chối.
- Bảng dữ liệu ERP tiếp tục chỉ đọc theo ADR-014. Không chuyển hoặc xóa dữ liệu, model, service orders/forms_builder. ERP và CRM vẫn cùng codebase/database.
- ERP: Tổng quan gồm Tổng quan/Bảng tin; Nội bộ gồm Quản lý task/Tài nguyên; Tổ chức thêm Đánh giá nhân sự; Dữ liệu gồm Bảng dữ liệu/Biểu mẫu & tài liệu; Tác vụ nền ở cuối Quản trị. Quyền từng mục giữ riêng.
- KN CRM chuyển khỏi sidebar chính lên cụm Nền/Đăng xuất, có icon SVG và mở tab mới bằng BANGTINH_URL.
- Biểu mẫu & tài liệu dùng `/bieu-mau/?tab=forms|documents`. Manager/Admin mặc định forms; Staff/Leader mặc định documents, gọi forms trực tiếp nhận 403. Chỉ truy vấn tab đang mở. `/tai-lieu/` giữ bookmark bằng chuyển tiếp kèm bộ lọc.
- Tài liệu vẫn theo phạm vi hiện có; không nhân bản file hoặc service. Biểu mẫu không có người tạo hiển thị dấu —, không sửa dữ liệu lịch sử.

## Giao diện kỹ thuật

CRM dùng `/van-don/len-don/`, `/van-don/don-goc/<code>/` và đường bỏ đơn POST tương ứng. Các endpoint kiểm khách, thêm sản phẩm và tóm tắt là nội bộ có đăng nhập/kiểm quyền. Tóm tắt là POST chỉ đọc, dùng Decimal và phép tính vận đơn; không tạo Order. Không thêm API công khai, dependency hay migration.

## Giới hạn

Không đồng nhất quyền đơn gốc với quyền phân công vận đơn, không thay trách nhiệm tiền, không thay grid autosave hoặc báo cáo. Việc sắp xếp màn hình không phải tách database/process hay chứng minh sức chịu tải CRM ở quy mô lớn.

Kiểm chứng và hướng dẫn: [báo cáo nghiệm thu](../kiem-chung-erp-hub-20260911.md).


## Bổ sung được duyệt 11.09.2026 — Ngày, đơn vị và định danh

Quyết định này bổ sung sau đợt sắp xếp màn hình ở trên, thay giới hạn không có migration riêng cho phần đơn vị:

- Ngày hiển thị chỉ đọc, tự lấy ngày hiện tại theo giờ Việt Nam. Khi lưu, server quyết định thời điểm tạo; không thêm ngày nghiệp vụ cho phép lùi/ngày tương lai.
- OrderLine và WaybillItem có bản chụp đơn vị (migration orders.0006). Lên đơn chọn hộp/cái/chiếc/túi, mặc định theo Product.unit; giữ đơn vị danh mục khác đã có. Dữ liệu lịch sử thiếu đơn vị giữ rỗng. Xuất chi tiết mang đơn vị đã lưu; không suy lại từ danh mục khi đọc đơn cũ. Đơn vị phụ vẫn riêng.
- Mã đăng nhập là định danh nghiệp vụ cho Sale/Marketer và phân công, audit. Admin chọn Sale không đổi người thực hiện. Không sửa dữ liệu báo cáo/audit cũ. Họ tên vẫn dùng cho nhãn giao diện thông thường, không đổi display_name toàn hệ thống.
- Chống lặp/gộp khách mua nhiều lần hoãn theo chủ dự án; không thay quan hệ đơn–vận đơn hay gộp các giao dịch.

Bằng chứng: [kiểm chứng Lên đơn](../kiem-chung-len-don-20260911.md).


## Quyết định thay thế tiếp theo — 11.09.2026, giờ lưu và Admin tự đứng đơn

Chủ dự án yêu cầu ngày có giờ dạng HH:mm và chốt Admin cũng tự đứng đơn bằng mã của mình; Admin lên đơn để thử, giá trị bộ phận có thể dùng placeholder. Thay ngoại lệ chọn Sale trên giao diện ở các đoạn trước:

- Form hiển thị ngày giờ Việt Nam tới phút, đồng hồ tham khảo cập nhật ngay tại trình duyệt từ thời gian server, không gọi mạng mỗi nhịp. Lưu vẫn lấy Order.created_at phía server, giữ giây/microsecond trong database; thông báo thành công và đơn gốc hiển thị HH:mm. Không dùng thời điểm mở form hoặc giờ người dùng gửi lên để ghi đơn.
- Không còn ô chọn Sale cho bất kỳ tài khoản nào. Form luôn dùng tài khoản đăng nhập; gửi seller qua POST bị từ chối. Admin không thuộc Sale dùng bộ phận Sale hiện có và team trống làm phạm vi nội bộ cho đơn thử, không sửa hồ sơ Admin hay tạo bộ phận mới. Thiếu Sale đang hoạt động thì báo lỗi.
- Không có cơ chế sandbox đơn thử mới: vẫn là luồng lưu hiện có. Không chuyển người đứng đơn trên dữ liệu cũ. Hợp đồng service nội bộ nhận seller tường minh còn giữ cho caller cũ; giao diện không còn cung cấp đường lên đơn hộ.
- Sale thường giữ bộ phận/team và phạm vi hiện hành. Không thêm migration hoặc dependency cho phần này.

Bằng chứng: [kiểm chứng ngày giờ và Admin](../kiem-chung-len-don-gio-admin-20260911.md).


Bổ sung theo ảnh feedback 11.09.2026: Quốc gia, Loại tiền và PTTT lên đơn không chọn sẵn; bắt buộc chọn option hợp lệ trước khi lưu, cả trình duyệt và server. Form sau lưu cũng trở về chưa chọn. Giữ mặc định service nội bộ, không sửa dữ liệu cũ.
