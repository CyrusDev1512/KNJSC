"""Gốc điều hướng của app **KN CRM** (dịch vụ `bangtinh`) — ADR-009, ADR-012, ADR-014.

Thu hẹp: đăng nhập, đổi mật khẩu, tác vụ nền (để tải tệp xuất lớn), trang
chủ tổng quan, Bảng tính (thư mục + lưới), và **ba việc của quản lý bộ phận
làm ngay tại đây**: tạo bảng, sửa cột kèm cấp quyền, nhập tệp (ADR-014) —
dùng chung view của `forms_builder`, template kế thừa khung KN CRM qua biến
`khung`. Không có Bảng dữ liệu, báo cáo, lên đơn, biểu mẫu — những thứ đó ở
KN ERP. Đây là nơi **duy nhất** có lưới; KN ERP chỉ liên kết sang.
"""
from django.contrib.auth.decorators import login_required
from django.urls import include, path
from django.views.generic import RedirectView

from crm import views as crm_views
from forms_builder import views as fb

urlpatterns = [
    # Cùng một trang chủ mang hai tên: `tong_quan` để khung và thanh bên dùng
    # chung với ERP không nổ, `bang_tinh` (trong crm.urls) là tên chính thức
    path("", crm_views.tong_quan, name="tong_quan"),
    # Tên `bang` và `bang_xem` để template của forms_builder dùng chung không
    # nổ; ở KN CRM chúng dẫn về trang thư mục và lưới (không có Bảng dữ liệu)
    path("danh-sach-bang/", login_required(RedirectView.as_view(pattern_name="thu_muc")), name="bang"),
    path("bang/<slug:code>/mo/", login_required(RedirectView.as_view(pattern_name="bang_tinh_xem")), name="bang_xem"),
    # Tạo bảng, sửa cột + cấp quyền, nhập tệp — view của forms_builder, quyền
    # kiểm trong view (Leader trở lên cùng bộ phận; cấp quyền: Manager)
    path("bang/moi/", fb.bang_moi, name="bang_moi"),
    path("bang/<slug:code>/cot/", fb.bang_cot, name="bang_cot"),
    path("bang/<slug:code>/cot/<int:pk>/bo/", fb.bang_xoa_cot, name="bang_xoa_cot"),
    path("bang/<slug:code>/nhap/", fb.bang_nhap, name="bang_nhap"),
    path("bang/<slug:code>/nhap/<int:pk>/", fb.bang_nhap_xem_truoc, name="bang_nhap_xem_truoc"),
    path("bang/<slug:code>/nhap/<int:pk>/xac-nhan/", fb.bang_nhap_xac_nhan, name="bang_nhap_xac_nhan"),
    path("bang/<slug:code>/cap-quyen/", fb.bang_cap_quyen, name="bang_cap_quyen"),
    path("bang/<slug:code>/thu-quyen/<int:pk>/", fb.bang_thu_quyen, name="bang_thu_quyen"),
    path("", include("core.urls")),
    path("", include("crm.urls")),
]
