"""Đường dẫn của forms_builder, viết bằng tiếng Việt không dấu."""
from django.urls import path

from . import views

urlpatterns = [
    # Bảng dữ liệu
    path("bang/", views.bang, name="bang"),
    path("bang/moi/", views.bang_moi, name="bang_moi"),
    path("bang/<slug:code>/", views.bang_xem, name="bang_xem"),
    path("bang/<slug:code>/cot/", views.bang_cot, name="bang_cot"),
    path("bang/<slug:code>/nhap/", views.bang_nhap, name="bang_nhap"),
    path("bang/<slug:code>/nhap/<int:pk>/", views.bang_nhap_xem_truoc, name="bang_nhap_xem_truoc"),
    path("bang/<slug:code>/nhap/<int:pk>/xac-nhan/", views.bang_nhap_xac_nhan,
         name="bang_nhap_xac_nhan"),
    path("bang/<slug:code>/xuat/", views.bang_xuat, name="bang_xuat"),
    path("bang/<slug:code>/cot/<int:pk>/bo/", views.bang_xoa_cot, name="bang_xoa_cot"),
    path("bang/<slug:code>/o/<int:pk>/<slug:ma_cot>/", views.bang_sua_o, name="bang_sua_o"),
    path("bang/<slug:code>/cap-quyen/", views.bang_cap_quyen, name="bang_cap_quyen"),
    path("bang/<slug:code>/thu-quyen/<int:pk>/", views.bang_thu_quyen, name="bang_thu_quyen"),

    # Biểu mẫu
    path("bieu-mau/", views.bieu_mau, name="bieu_mau"),
    path("bieu-mau/moi/", views.bieu_mau_moi, name="bieu_mau_moi"),
    path("bieu-mau/truong-moi/", views.truong_moi, name="truong_moi"),
    path("bieu-mau/<slug:code>/dien/", views.bieu_mau_dien, name="bieu_mau_dien"),
    path("bieu-mau/<slug:code>/sua/", views.bieu_mau_sua, name="bieu_mau_sua"),
    path("bieu-mau/<slug:code>/bo-truong/<int:pk>/", views.bieu_mau_bo_truong,
         name="bieu_mau_bo_truong"),
    path("bieu-mau/<slug:code>/cap-quyen/", views.bieu_mau_cap_quyen,
         name="bieu_mau_cap_quyen"),
    path("bieu-mau/<slug:code>/thu-quyen/<int:pk>/", views.bieu_mau_thu_quyen,
         name="bieu_mau_thu_quyen"),
]
