"""Đường dẫn của dashboard."""
from django.urls import path

from . import views

urlpatterns = [
    path("", views.tong_quan, name="tong_quan"),
]
