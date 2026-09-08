"""Đường dẫn của feed, viết bằng tiếng Việt không dấu."""
from django.urls import path

from . import views

urlpatterns = [
    path("bang-tin/", views.bang_tin, name="bang_tin"),
    path("bang-tin/dang/", views.bang_tin_dang, name="bang_tin_dang"),
    path("bang-tin/binh-luan/<int:pk>/go/", views.bang_tin_binh_luan_go, name="bang_tin_binh_luan_go"),
    path("bang-tin/<int:pk>/", views.bang_tin_xem, name="bang_tin_xem"),
    path("bang-tin/<int:pk>/thich/", views.bang_tin_thich, name="bang_tin_thich"),
    path("bang-tin/<int:pk>/binh-luan/", views.bang_tin_binh_luan, name="bang_tin_binh_luan"),
    path("bang-tin/<int:pk>/ghim/", views.bang_tin_ghim, name="bang_tin_ghim"),
    path("bang-tin/<int:pk>/go/", views.bang_tin_go, name="bang_tin_go"),
]
