"""Gốc điều hướng của app **KN CRM** (dịch vụ `bangtinh`) — ADR-009, ADR-012.

Thu hẹp: đăng nhập, đổi mật khẩu, tác vụ nền (để tải tệp xuất lớn) và Bảng
tính. Không có bảng dữ liệu, báo cáo, lên đơn — những thứ đó ở KN ERP. Đây là
nơi **duy nhất** có lưới; KN ERP chỉ liên kết sang.
"""
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="bang_tinh", permanent=False), name="tong_quan"),
    path("", include("core.urls")),
    path("", include("crm.urls")),
]
