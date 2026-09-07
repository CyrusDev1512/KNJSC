# ADR-015 — KN CRM có khung sidebar theo Teeze, trang chủ là tổng quan, Leader như Manager trong bộ phận

| Mục | Nội dung |
|---|---|
| Trạng thái | Đã áp dụng |
| Ngày | 07.09.2026 |
| Người quyết định | Anh/chị chủ dự án, qua bốn điểm chưa hợp lý nêu tối 06.09.2026 và ba câu hỏi chốt |
| Thay thế cho | **ADR-012 mục 1** phần "cùng một khung cho trang chủ lẫn lưới; nút ← từ trang chủ về KN ERP" · **ADR-012 mục 2** phần "trang chủ là cây" (cây chuyển sang mục Bảng tính) · **ADR-012 mục 5** phần "Manager cấp quyền ở KN ERP, KN CRM chỉ hiển thị" · **ADR-010 mục 6, ADR-011 mục chuột phải** phần "Manager" → quản lý của bộ phận |
| Liên quan | ADR-009 · ADR-010 · ADR-011 · ADR-012 · FR-7.14 · FR-7.15 · backlog Q63 → Q65 |

---

## Bối cảnh

Sau khi PR #5 (ADR-012) vào `main`, anh/chị mở KN CRM trên máy mình và nêu bốn
điểm chưa hợp lý:

1. Bấm ← liên tục thì rơi về KN ERP, dù đã có nút KN ERP.
2. KN CRM **chưa có trang chủ, chưa có sidebar menu** — vào là gặp cây thư mục.
3. Thư mục Marketing, Vận đơn phải là **một tính năng nằm trên sidebar**, bấm
   vào mới mở view có thư mục.
4. Trong KN CRM, **Manager và Leader** được thêm, sửa, xoá, tạo, nhập, xuất
   trong các view bảng tính.

Ba câu hỏi chốt thêm: trang chủ là **tổng quan như KN ERP**; sidebar dáng
**tham khảo Teeze** (ảnh anh/chị gửi: menu trái sáng có avatar + tên + vai
trò, nhóm gập được, mục đang chọn tô xanh nhạt, nút thu gọn; trang danh sách
có tiêu đề, bộ lọc, nút hành động xanh, dòng "Tổng cộng N"); Leader được
**như Manager trong bộ phận mình**, chỉ cấp quyền cho người khác vẫn là
Manager. Và một ràng buộc nêu rõ khi duyệt: **lưới vẫn phải full như Excel
như hiện tại; chỉ khi chủ động quay về mới thấy menu trái; bấm "Bảng tính"
từ menu trái → chỗ thư mục → vào lưới như KN CRM hiện tại.**

---

## Quyết định

1. **Hai khung, một app.** Trang có sidebar dùng `templates/crm/base_crm.html`
   (sáng theo Teeze khi chưa chọn nền, dùng lại `.nav`, `.nav-muc`, `.topbar`
   của `main.css`); lưới giữ `base_bang_tinh.html` toàn màn hình (ADR-011,
   tối). Chỉ lưới có nút ←, và nó về **trang thư mục đúng nhánh**, không bao
   giờ về ERP; về ERP bằng mục KN ERP trên sidebar hoặc nút trên thanh trên.
2. **Sidebar riêng của KN CRM** — `crm/navigation.py`, không dùng chung
   `NAVIGATION` của ERP (ở 8021 phần lớn mục ERP không có đường dẫn, và KN CRM
   cần mục sinh động). Mục: **Trang chủ**; **Bảng tính** gập được, mục con là
   **từng bộ phận trong phạm vi** (Sale không thấy Vận đơn); **Nhập tệp**
   (Leader trở lên); **Cấp quyền** (Manager); **Tác vụ nền**; **Nhật ký**
   (Manager); **KN ERP**. Lớp CSS tính ở Python (luật K15). Đưa vào template
   bằng context processor `crm.context_processors.khung_crm`, đăng ký chung
   nhưng chỉ chạy khi `ROOT_URLCONF` là của 8021 — để bộ kiểm đổi URLconf
   bằng override cũng có.
3. **Trang chủ `/` là tổng quan theo phạm vi** (`crm/services/tong_quan_service.py`
   theo mẫu `dashboard_service`, khối nào hỏng báo "tạm chưa khả dụng"): dòng
   nhập tháng này và hôm nay, số bảng, tổng dòng, bảng cập nhật gần nhất, danh
   sách bảng có nút Mở, hoạt động gần đây — mọi số qua `in_scope`, một truy
   vấn đếm ba số dòng. Leader trở lên có nút Tạo bảng.
4. **Cây Bộ phận ▸ Quý ▸ Tháng ▸ bảng chuyển sang `/thu-muc/`** (tên `thu_muc`),
   là mục Bảng tính trên sidebar, giữ nguyên tham số `bp/quy/thang/tat-ca` và
   toàn bộ `tree_service`; `home_url` trỏ về đó. Luồng chốt: Trang chủ → Bảng
   tính → trang thư mục → bấm bảng → lưới full → ← → trang thư mục.
5. **Leader như Manager trong bộ phận mình** — sửa **một chỗ**:
   `grant_service._quan_ly_bo_phan(user, department_id)` = Admin, hoặc
   Leader/Manager đúng bộ phận; `can_import`, `can_manage_folders`,
   `can_manage_columns`, `can_edit_record` (nhánh "cùng bộ phận") và
   `choice_service.can_manage_options` dùng nó. Các view đổi `assert_rank(MANAGER)`
   → `LEADER`: thư mục, chèn/bỏ cột trên lưới, tạo bảng, Sửa cột, nhập tệp.
   Màn Sửa cột ở ERP kiểm thêm `can_manage_columns` — bảng chỉ được cấp quyền
   xem từ bộ phận khác không đổi cấu trúc được (trước đây Manager bộ phận khác
   lọt). **Cấp quyền cho người khác** (`bang_cap_quyen`, `grant()`) và biểu
   mẫu **vẫn Manager**. Phạm vi xem của Leader không đổi (team mình, ADR-003).
6. **Tạo bảng, sửa cột kèm cấp quyền, nhập tệp chạy ngay trong KN CRM**:
   `urls_bangtinh.py` gắn thêm chính các view của `forms_builder` (`bang/moi/`,
   `bang/<mã>/cot/`, `nhap/` ba bước, `cap-quyen/`, `thu-quyen/`); bốn template
   của chúng đổi `{% extends "base.html" %}` thành `{% extends khung %}` — biến
   `khung` do context processor đặt (`base.html` ở ERP, `crm/base_crm.html` ở
   KN CRM). Tên `bang` và `bang_xem` ở KN CRM là chuyển hướng có đăng nhập về
   trang thư mục và lưới; Bảng dữ liệu `/bang/` **vẫn không có** ở KN CRM.
   Hai trang chọn bảng `/nhap-tep/` và `/cap-quyen/` (một template
   `crm/chon_bang.html`, dáng Teeze) là điểm vào từ sidebar.

### Không làm

| Việc | Vì sao |
|---|---|
| Sidebar trên lưới | Anh/chị chốt lưới full như Excel; menu chỉ hiện khi chủ động quay về |
| Trang "Danh sách bảng" kiểu bảng nhiều cột như Teeze | Trang thư mục đã liệt kê bảng; làm thêm là hai chỗ một việc |
| Mục Cài đặt, Báo cáo, Quản lý tổ chức như Teeze | Chưa có tính năng tương ứng ở KN CRM; không dựng vỏ (Q22) |
| Leader cấp quyền cho người khác | Anh/chị chốt chỉ Manager |
| Leader thấy dòng ngoài team mình | Phạm vi xem theo ADR-003 không đổi; "như Manager" là về thao tác, không về phạm vi |
| Mở biểu mẫu, báo cáo ngày, Lên đơn trong KN CRM | KN CRM là nơi làm việc trên bảng; nghiệp vụ ở KN ERP (ADR-012) |

---

## Đã cân nhắc và bỏ

| Cách | Vì sao bỏ |
|---|---|
| Dùng chung `NAVIGATION` của ERP, lọc bằng `href()` như trước | Ở 8021 chỉ còn Tổng quan, KN CRM, Tác vụ nền; không sinh được mục con theo bộ phận |
| Sidebar tối cùng tông với lưới | Anh/chị đưa ảnh Teeze (sáng) làm mẫu; lưới tối vẫn giữ vì đó là "full như Excel" |
| Sao chép view nhập tệp, tạo bảng sang `crm` | Hai bản của một luồng bốn bước; đổi `extends` thành biến `khung` rẻ hơn nhiều |
| Đăng ký context processor chỉ trong `settings/bangtinh.py` | Bộ kiểm dùng `settings.test` rồi override URLconf, sẽ thiếu `khung` và `crm_nav` |
| Thêm cấp bậc hay cờ mới cho "Leader được như Manager" | Một hàm `_quan_ly_bo_phan` đủ; thêm cờ là thêm chỗ cài luật (điều cấm 11) |

---

## Hệ quả

| Được | Mất |
|---|---|
| KN CRM có trang chủ và menu trái như một app; không còn "bấm ← mãi rơi về ERP" | Hai khung phải giữ đồng bộ (thanh trên, menu tài khoản, nền sáng/tối) |
| Leader của bộ phận tự lo thư mục, cột, nhập tệp mà không chờ Manager | Leader làm hỏng cột thì cũng như Manager — nhật ký ghi ai làm (BR-6) |
| Tạo bảng, nhập tệp, cấp quyền không phải bật sang ERP | `forms_builder` template phụ thuộc biến `khung` từ context processor |
| Sidebar sinh từ phạm vi nên không thể lộ bộ phận ngoài quyền | Mỗi trang có sidebar tốn thêm một truy vấn bảng trong phạm vi |

Tiêu chí nghiệm thu: `docs/04` mục 11, AC-11.31 → AC-11.34; sửa AC-8.8, AC-8.9,
AC-11.17, AC-11.19, AC-11.21, AC-11.22, AC-3.6 và ma trận mục 3 theo luật Leader.
Xem lại khi: anh/chị muốn Leader cấp quyền; muốn sidebar trên lưới; hoặc KN CRM
có thêm màn hình nghiệp vụ riêng (khi đó xem lại ADR-004).
