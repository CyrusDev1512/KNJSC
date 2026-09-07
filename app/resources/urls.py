"""Đường dẫn của resources, viết bằng tiếng Việt không dấu."""
from django.urls import path

from . import views

urlpatterns = [
    path("tai-nguyen/", views.tai_nguyen, name="tai_nguyen"),
]
