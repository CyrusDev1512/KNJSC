"""Đường dẫn của Bảng tính, viết bằng tiếng Việt không dấu.

Mở ở cả hai dịch vụ: dịch vụ chính và dịch vụ `bangtinh` (ADR-009). Mọi bảng
trong phạm vi quyền đều có lưới ở `bang-tinh/<mã bảng>/` (ADR-010).
"""
from django.urls import path

from . import views

urlpatterns = [
    path("bang-tinh/", views.bang_tinh, name="bang_tinh"),
    path("bang-tinh/<slug:code>/", views.bang_tinh_xem, name="bang_tinh_xem"),
    path("bang-tinh/<slug:code>/loc/<slug:ma_cot>/", views.bang_tinh_loc_cot, name="bang_tinh_loc_cot"),
    path("bang-tinh/<slug:code>/o/<int:pk>/<slug:ma_cot>/", views.bang_tinh_o, name="bang_tinh_o"),
    path("bang-tinh/<slug:code>/xuat/", views.bang_tinh_xuat, name="bang_tinh_xuat"),
    path("bang-tinh/<slug:code>/dong-moi/", views.bang_tinh_dong_moi, name="bang_tinh_dong_moi"),
]
