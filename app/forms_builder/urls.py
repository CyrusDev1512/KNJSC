"""Đường dẫn của forms_builder, viết bằng tiếng Việt không dấu."""
from django.urls import path
from functools import wraps
from django.contrib.auth.decorators import login_required
from core.constants import Rank
from core.permissions import assert_rank

from . import views


def erp_table_view(view):
    """Chỉ gắn vào URL Bảng dữ liệu ERP, không đổi view dùng chung ở CRM."""
    @login_required
    @wraps(view)
    def checked(request, *args, **kwargs):
        assert_rank(request.user, Rank.MANAGER, request)
        return view(request, *args, **kwargs)
    return checked

urlpatterns = [
    # Bảng dữ liệu
    path("bang/", erp_table_view(views.bang), name="bang"),
    path("bang/moi/", erp_table_view(views.bang_moi), name="bang_moi"),
    path("bang/<slug:code>/", erp_table_view(views.bang_xem), name="bang_xem"),
    path("bang/<slug:code>/cot/", erp_table_view(views.bang_cot), name="bang_cot"),
    path("bang/<slug:code>/nhap/", erp_table_view(views.bang_nhap), name="bang_nhap"),
    path("bang/<slug:code>/mau-nhap.xlsx", erp_table_view(views.bang_mau_nhap), name="bang_mau_nhap"),
    path("bang/<slug:code>/nhap/<int:pk>/", erp_table_view(views.bang_nhap_xem_truoc), name="bang_nhap_xem_truoc"),
    path("bang/<slug:code>/nhap/<int:pk>/xac-nhan/", erp_table_view(views.bang_nhap_xac_nhan),
         name="bang_nhap_xac_nhan"),
    path("bang/<slug:code>/xuat/", erp_table_view(views.bang_xuat), name="bang_xuat"),
    path("bang/<slug:code>/cot/<int:pk>/bo/", erp_table_view(views.bang_xoa_cot), name="bang_xoa_cot"),
    path("bang/<slug:code>/cot/<slug:ma_cot>/lua-chon/", erp_table_view(views.bang_them_lua_chon),
         name="bang_them_lua_chon"),
    path("bang/<slug:code>/cap-quyen/", erp_table_view(views.bang_cap_quyen), name="bang_cap_quyen"),
    path("bang/<slug:code>/thu-quyen/<int:pk>/", erp_table_view(views.bang_thu_quyen), name="bang_thu_quyen"),

    # Biểu mẫu
    path("bieu-mau/", views.bieu_mau, name="bieu_mau"),
    path("bieu-mau/moi/", views.bieu_mau_moi, name="bieu_mau_moi"),
    path("bieu-mau/truong-moi/", views.truong_moi, name="truong_moi"),
    path("bieu-mau/<slug:code>/dien/", views.bieu_mau_dien, name="bieu_mau_dien"),
    path("bieu-mau/<slug:code>/sua/", views.bieu_mau_sua, name="bieu_mau_sua"),
    path("bieu-mau/<slug:code>/bo-truong/<int:pk>/", views.bieu_mau_bo_truong,
         name="bieu_mau_bo_truong"),
    path("bieu-mau/<slug:code>/cap-quyen/", views.bieu_mau_cap_quyen,
         name="bieu_mau_cap_quyen"),
    path("bieu-mau/<slug:code>/thu-quyen/<int:pk>/", views.bieu_mau_thu_quyen,
         name="bieu_mau_thu_quyen"),
]
