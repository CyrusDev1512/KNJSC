"""Đường dẫn của culture, viết bằng tiếng Việt không dấu."""
from django.urls import path

from . import views

urlpatterns = [
    path("van-hoa/", views.van_hoa, name="van_hoa"),
]
