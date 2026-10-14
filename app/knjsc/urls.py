"""Gốc điều hướng của dịch vụ chính (KN ERP).

Đường dẫn hiển thị cho người dùng viết bằng tiếng Việt không dấu. Lưới Bảng
tính **không** nằm ở đây: nó là app riêng KN CRM (`knjsc/urls_bangtinh.py`,
ADR-012); thanh bên chỉ có liên kết sang đó.
"""
from django.contrib import admin
from django.urls import include, path

from core import views as core_views

urlpatterns = [
    # Trang quản trị Django dùng chung cửa đăng nhập và đăng xuất của hệ thống (TL-93, FR-1.2): hai đường này
    # phải đứng TRƯỚC admin.site.urls; reverse("admin:login"/"admin:logout") vẫn ra đúng chuỗi nên trang quản
    # trị tự đi vào view của dự án
    path("quan-tri/login/", core_views.quan_tri_dang_nhap, name="quan_tri_dang_nhap"),
    path("quan-tri/logout/", core_views.LogoutView.as_view(), name="quan_tri_dang_xuat"),
    path("quan-tri/", admin.site.urls),
    path("", include("core.urls")),
    path("", include("org.urls")),
    path("", include("dashboard.urls")),
    path("", include("forms_builder.urls")),
    path("", include("reports.urls")),
    path("", include("orders.urls")),
    # Nhóm Nội bộ — ADR-017
    path("", include("feed.urls")),
    path("", include("documents.urls")),
    path("", include("taskboard.urls")),
    path("", include("culture.urls")),
    path("", include("resources.urls")),
]
