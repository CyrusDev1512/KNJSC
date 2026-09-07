"""Đường dẫn của resources, viết bằng tiếng Việt không dấu."""
from django.urls import path

from . import views

urlpatterns = [
    path("tai-nguyen/", views.tai_nguyen, name="tai_nguyen"),
    path("tai-nguyen/moi/", views.tai_nguyen_moi, name="tai_nguyen_moi"),
    path("tai-nguyen/muc-moi/", views.tai_nguyen_muc_moi, name="tai_nguyen_muc_moi"),
    path("tai-nguyen/<int:pk>/sua/", views.tai_nguyen_sua, name="tai_nguyen_sua"),
    path("tai-nguyen/<int:pk>/go/", views.tai_nguyen_go, name="tai_nguyen_go"),
]
