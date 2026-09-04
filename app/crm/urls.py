"""Đường dẫn của Bảng tính, viết bằng tiếng Việt không dấu.

Mở ở cả hai dịch vụ: dịch vụ chính và dịch vụ `bangtinh` (ADR-009). Mọi bảng
trong phạm vi quyền đều có lưới ở `bang-tinh/<mã bảng>/` (ADR-010).
"""
from django.urls import path

from . import views

urlpatterns = [
    path("bang-tinh/", views.bang_tinh, name="bang_tinh"),
    # Thư mục đứng trước `<slug:code>` để "thu-muc" không bị hiểu là mã bảng
    path("bang-tinh/thu-muc/moi/", views.thu_muc_moi, name="thu_muc_moi"),
    path("bang-tinh/thu-muc/<int:pk>/sua/", views.thu_muc_sua, name="thu_muc_sua"),
    path("bang-tinh/thu-muc/<int:pk>/xoa/", views.thu_muc_xoa, name="thu_muc_xoa"),
    path("bang-tinh/<slug:code>/", views.bang_tinh_xem, name="bang_tinh_xem"),
    path("bang-tinh/<slug:code>/chuyen-thu-muc/", views.bang_tinh_chuyen_thu_muc, name="bang_tinh_chuyen_thu_muc"),
    path("bang-tinh/<slug:code>/loc/<slug:ma_cot>/", views.bang_tinh_loc_cot, name="bang_tinh_loc_cot"),
    path("bang-tinh/<slug:code>/o/<int:pk>/<slug:ma_cot>/", views.bang_tinh_o, name="bang_tinh_o"),
    path("bang-tinh/<slug:code>/xuat/", views.bang_tinh_xuat, name="bang_tinh_xuat"),
    path("bang-tinh/<slug:code>/dong-moi/", views.bang_tinh_dong_moi, name="bang_tinh_dong_moi"),
    path("bang-tinh/<slug:code>/dinh-dang/", views.bang_tinh_dinh_dang, name="bang_tinh_dinh_dang"),
    path("bang-tinh/<slug:code>/luu-o/", views.bang_tinh_luu_o, name="bang_tinh_luu_o"),
]
