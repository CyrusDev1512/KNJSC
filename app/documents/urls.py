"""Đường dẫn của documents, viết bằng tiếng Việt không dấu."""
from django.urls import path

from . import views

urlpatterns = [
    path("tai-lieu/", views.tai_lieu, name="tai_lieu"),
]
