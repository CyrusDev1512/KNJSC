"""Đường dẫn của culture, viết bằng tiếng Việt không dấu."""
from django.urls import path

from . import views

urlpatterns = [
    path("van-hoa/", views.van_hoa, name="van_hoa"),
    path("van-hoa/ghi-nhan/", views.van_hoa_ghi_nhan, name="van_hoa_ghi_nhan"),
    path("van-hoa/thanh-vien/<int:pk>/", views.van_hoa_thanh_vien, name="van_hoa_thanh_vien"),
]
