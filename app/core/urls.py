"""Đường dẫn của core. Viết bằng tiếng Việt không dấu."""
from django.urls import path

from . import views

urlpatterns = [
    path("dang-nhap/", views.LoginView.as_view(), name="dang_nhap"),
    path("dang-xuat/", views.LogoutView.as_view(), name="dang_xuat"),
    path("doi-mat-khau/", views.PasswordChangeView.as_view(), name="doi_mat_khau"),
    path("nhat-ky/", views.nhat_ky, name="nhat_ky"),
    path("ma-tran-quyen/", views.ma_tran_quyen, name="ma_tran_quyen"),
]
