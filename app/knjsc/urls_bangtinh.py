"""Gốc điều hướng của app **KN CRM** (dịch vụ `bangtinh`) — ADR-009, ADR-012.

Thu hẹp: đăng nhập, đổi mật khẩu, tác vụ nền (để tải tệp xuất lớn) và Bảng
tính. Không có bảng dữ liệu, báo cáo, lên đơn — những thứ đó ở KN ERP. Đây là
nơi **duy nhất** có lưới; KN ERP chỉ liên kết sang.
"""
from django.urls import include, path

from crm import views as crm_views

urlpatterns = [
    # Cùng một trang chủ mang hai tên: `tong_quan` để khung và thanh bên dùng
    # chung với ERP không nổ, `bang_tinh` (trong crm.urls) là tên chính thức
    path("", crm_views.tong_quan, name="tong_quan"),
    path("", include("core.urls")),
    path("", include("crm.urls")),
]
