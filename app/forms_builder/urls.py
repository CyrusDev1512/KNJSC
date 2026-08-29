"""Đường dẫn của forms_builder, viết bằng tiếng Việt không dấu."""
from django.urls import path

from . import views

urlpatterns = [
    path("bang/", views.bang, name="bang"),
    path("bang/moi/", views.bang_moi, name="bang_moi"),
    path("bang/<slug:code>/", views.bang_xem, name="bang_xem"),
    path("bang/<slug:code>/cot/", views.bang_cot, name="bang_cot"),
    path("bang/<slug:code>/cot/<int:pk>/bo/", views.bang_xoa_cot, name="bang_xoa_cot"),
    path("bang/<slug:code>/o/<int:pk>/<slug:ma_cot>/", views.bang_sua_o, name="bang_sua_o"),
]
