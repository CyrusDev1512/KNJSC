"""Đường dẫn của taskboard, viết bằng tiếng Việt không dấu."""
from django.urls import path

from . import views

urlpatterns = [
    path("cong-viec/", views.cong_viec, name="cong_viec"),
    path("cong-viec/moi/", views.cong_viec_moi, name="cong_viec_moi"),
    path("cong-viec/<int:pk>/", views.cong_viec_xem, name="cong_viec_xem"),
    path("cong-viec/<int:pk>/sua/", views.cong_viec_sua, name="cong_viec_sua"),
    path("cong-viec/<int:pk>/trang-thai/", views.cong_viec_trang_thai, name="cong_viec_trang_thai"),
    path("cong-viec/<int:pk>/go/", views.cong_viec_go, name="cong_viec_go"),
]
