"""Đường dẫn của reports, viết bằng tiếng Việt không dấu."""
from django.urls import path

from . import views

urlpatterns = [
    path("bao-cao/", views.bao_cao_ngay, name="bao_cao_ngay"),
    path("bao-cao/lich-su/", views.bao_cao_lich_su, name="bao_cao_lich_su"),
    path("bao-cao/tong-hop/", views.bao_cao_tong_hop, name="bao_cao_tong_hop"),
    path("bao-cao/tong-hop/xuat/", views.bao_cao_tong_hop_xuat,
         name="bao_cao_tong_hop_xuat"),
    path("bao-cao/<int:pk>/", views.bao_cao_xem, name="bao_cao_xem"),
    path("bao-cao/<int:pk>/bo/", views.bao_cao_bo, name="bao_cao_bo"),
]
