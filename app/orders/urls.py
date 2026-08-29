"""Đường dẫn của orders, viết bằng tiếng Việt không dấu."""
from django.urls import path

from . import views

urlpatterns = [
    path("len-don/", views.len_don, name="len_don"),
    path("len-don/kiem-khach/", views.kiem_khach, name="kiem_khach"),
    path("don-hang/", views.don_hang, name="don_hang"),
    path("don-hang/<slug:code>/", views.don_xem, name="don_xem"),
    path("don-hang/<slug:code>/bo/", views.don_bo, name="don_bo"),
]
