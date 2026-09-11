"""URL ERP cũ chỉ chuyển trang; nghiệp vụ nhập và xem đơn thuộc CRM."""
from django.urls import path
from .handoff import handoff

urlpatterns = [
    path("len-don/", handoff, {"destination": "waybill_create"}, name="len_don"),
    path("len-don/kiem-khach/", handoff, {"destination": "kiem_khach"}, name="kiem_khach"),
    path("len-don/san-pham-moi/", handoff, {"destination": "san_pham_moi"}, name="san_pham_moi"),
    path("don-hang/", handoff, {"destination": "thu_muc"}, name="don_hang"),
    path("don-hang/<slug:code>/", handoff, {"destination": "don_xem"}, name="don_xem"),
    path("don-hang/<slug:code>/bo/", handoff, {"destination": "don_xem"}, name="don_bo"),
]
