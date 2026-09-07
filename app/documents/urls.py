"""Đường dẫn của documents, viết bằng tiếng Việt không dấu."""
from django.urls import path

from . import views

urlpatterns = [
    path("tai-lieu/", views.tai_lieu, name="tai_lieu"),
    path("tai-lieu/tai-len/", views.tai_lieu_tai_len, name="tai_lieu_tai_len"),
    path("tai-lieu/muc-moi/", views.tai_lieu_muc_moi, name="tai_lieu_muc_moi"),
    path("tai-lieu/<int:pk>/tai/", views.tai_lieu_tai, name="tai_lieu_tai"),
    path("tai-lieu/<int:pk>/go/", views.tai_lieu_go, name="tai_lieu_go"),
]
