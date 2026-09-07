"""Đường dẫn của feed, viết bằng tiếng Việt không dấu."""
from django.urls import path

from . import views

urlpatterns = [
    path("bang-tin/", views.bang_tin, name="bang_tin"),
]
