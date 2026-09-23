"""Đường dẫn của reports, viết bằng tiếng Việt không dấu."""
from django.urls import path

from . import views, activity_views

urlpatterns = [
    path("bao-cao/hoat-dong/", activity_views.legacy_redirect, name="bao_cao_hoat_dong"),
    path("bao-cao/hoat-dong/xuat/", activity_views.legacy_redirect, {"export": True}, name="bao_cao_hoat_dong_xuat"),
    path("bao-cao/", views.bao_cao_ngay, name="bao_cao_ngay"),
    path("bao-cao/lich-su/", views.bao_cao_lich_su, name="bao_cao_lich_su"),
    path("bao-cao/tong-hop/", views.bao_cao_tong_hop, name="bao_cao_tong_hop"),
    path("bao-cao/tong-hop/xuat/", views.bao_cao_tong_hop_xuat,
         name="bao_cao_tong_hop_xuat"),
    # Manager bộ phận sở hữu nguồn đặt ngưỡng màu ba bậc (ADR-040 đợt 3)
    path("bao-cao/tong-hop/nguong/", activity_views.thresholds, name="bao_cao_tong_hop_nguong"),
    path("bao-cao/<int:pk>/", views.bao_cao_xem, name="bao_cao_xem"),
    path("bao-cao/<int:pk>/sua/", views.bao_cao_sua, name="bao_cao_sua"),
    path("bao-cao/<int:pk>/bo/", views.bao_cao_bo, name="bao_cao_bo"),
]
