"""Đường dẫn của KN CRM (Bảng tính), viết bằng tiếng Việt không dấu.

Chỉ gắn vào dịch vụ `bangtinh` (ADR-009, ADR-012) — KN ERP không có lưới, chỉ
liên kết sang. Mọi bảng trong phạm vi quyền đều có lưới ở
`bang-tinh/<mã bảng>/` (ADR-010); gốc `/` là trang chủ tổng quan, `thu-muc/`
là cây thư mục (ADR-015).
"""
from django.urls import path

from . import views

urlpatterns = [
    # Trang chủ KN CRM: tổng quan có sidebar (ADR-015); tên `bang_tinh` giữ
    # để mục KN CRM trên thanh bên ERP và các liên kết cũ vẫn đúng
    path("", views.tong_quan, name="bang_tinh"),
    # Mục Bảng tính trên sidebar: trang thư mục, cây Bộ phận ▸ Quý ▸ Tháng ▸ bảng (ADR-012)
    path("thu-muc/", views.thu_muc, name="thu_muc"),
    # Chọn bảng để nhập tệp (Leader trở lên) hay cấp quyền (Manager) — ADR-015
    path("nhap-tep/", views.nhap_tep, name="nhap_tep"),
    path("cap-quyen/", views.cap_quyen, name="cap_quyen"),
    # Mở bảng mặc định (vận đơn, hoặc bảng đầu tiên trong phạm vi)
    path("bang-tinh/", views.bang_tinh, name="bang_tinh_mac_dinh"),
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
    path("bang-tinh/<slug:code>/xoa-dong/", views.bang_tinh_xoa_dong, name="bang_tinh_xoa_dong"),
    path("bang-tinh/<slug:code>/khoi-phuc-dong/", views.bang_tinh_khoi_phuc_dong, name="bang_tinh_khoi_phuc_dong"),
    path("bang-tinh/<slug:code>/them-cot/", views.bang_tinh_them_cot, name="bang_tinh_them_cot"),
    path("bang-tinh/<slug:code>/xoa-cot/", views.bang_tinh_xoa_cot, name="bang_tinh_xoa_cot"),
    path("bang-tinh/<slug:code>/moi-nhat/", views.bang_tinh_moi_nhat, name="bang_tinh_moi_nhat"),
]
