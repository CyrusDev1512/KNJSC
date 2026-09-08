"""Gốc điều hướng của dịch vụ chính (KN ERP).

Đường dẫn hiển thị cho người dùng viết bằng tiếng Việt không dấu. Lưới Bảng
tính **không** nằm ở đây: nó là app riêng KN CRM (`knjsc/urls_bangtinh.py`,
ADR-012); thanh bên chỉ có liên kết sang đó.
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
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
