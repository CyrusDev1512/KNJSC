"""Đường dẫn của Bảng tính, viết bằng tiếng Việt không dấu.

Mở ở cả hai dịch vụ: dịch vụ chính (chỉ xem) và dịch vụ `bangtinh` (sửa được).
"""
from django.urls import path

from . import views

urlpatterns = [
    path("bang-tinh/", views.bang_tinh, name="bang_tinh"),
    path("bang-tinh/loc/<slug:ma_cot>/", views.bang_tinh_loc_cot, name="bang_tinh_loc_cot"),
    path("bang-tinh/o/<int:pk>/<slug:ma_cot>/", views.bang_tinh_o, name="bang_tinh_o"),
    path("bang-tinh/xuat/", views.bang_tinh_xuat, name="bang_tinh_xuat"),
]
