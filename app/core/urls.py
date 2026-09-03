"""Đường dẫn của core. Viết bằng tiếng Việt không dấu."""
from django.urls import path

from . import views

urlpatterns = [
    path("dang-nhap/", views.LoginView.as_view(), name="dang_nhap"),
    path("dang-xuat/", views.LogoutView.as_view(), name="dang_xuat"),
    path("doi-mat-khau/", views.PasswordChangeView.as_view(), name="doi_mat_khau"),
    path("nhat-ky/", views.nhat_ky, name="nhat_ky"),
    path("ma-tran-quyen/", views.ma_tran_quyen, name="ma_tran_quyen"),
    path("tac-vu/", views.tac_vu, name="tac_vu"),
    path("tac-vu/<int:pk>/", views.tac_vu_xem, name="tac_vu_xem"),
    path("tac-vu/<int:pk>/tien-do/", views.tac_vu_tien_do, name="tac_vu_tien_do"),
    path("tac-vu/<int:pk>/tai/", views.tac_vu_tai, name="tac_vu_tai"),
]
