"""Đường dẫn của org, viết bằng tiếng Việt không dấu."""
from django.urls import path

from . import views

urlpatterns = [
    path("nhan-su/", views.nhan_su, name="nhan_su"),
    path("nhan-su/moi/", views.nhan_su_moi, name="nhan_su_moi"),
    path("nhan-su/goi-y-ma/", views.nhan_su_goi_y_ma, name="nhan_su_goi_y_ma"),
    path("nhan-su/<int:pk>/sua/", views.nhan_su_sua, name="nhan_su_sua"),
    path("nhan-su/<int:pk>/dat-lai-mat-khau/", views.nhan_su_dat_lai_mat_khau, name="nhan_su_dat_lai_mat_khau"),
    path("nhan-su/<int:pk>/xoa/", views.nhan_su_xoa, name="nhan_su_xoa"),
    path("nhan-su/<int:pk>/doi-trang-thai/", views.nhan_su_doi_trang_thai,
         name="nhan_su_doi_trang_thai"),
    path("bo-phan/", views.bo_phan, name="bo_phan"),
]
