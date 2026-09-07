"""Đường dẫn của taskboard, viết bằng tiếng Việt không dấu."""
from django.urls import path

from . import views

urlpatterns = [
    path("cong-viec/", views.cong_viec, name="cong_viec"),
]
