"""Gốc điều hướng.

Đường dẫn hiển thị cho người dùng viết bằng tiếng Việt không dấu.
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
]
