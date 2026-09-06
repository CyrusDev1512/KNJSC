"""Mọi bài trong `crm/tests` chạy ở **app KN CRM** — ADR-012.

Lưới Bảng tính chỉ tồn tại ở dịch vụ `bangtinh` (URLconf `knjsc.urls_bangtinh`,
cổng 8021); ở KN ERP chỉ còn liên kết sang. Bài nào cần gọi màn hình ERP
(Bảng dữ liệu, Sửa cột…) tự đặt lại `settings.ROOT_URLCONF = "knjsc.urls"`.

`GRID_ONLY_TABLES` giữ mặc định (`van_don` chỉ xem) để các bài phân quyền
kiểm được cả hai chiều: bảng chỉ xem thì 403, bật `SUA_DUOC` (tập rỗng — đúng
cấu hình dịch vụ 8021 khi chạy thật) thì sửa được.
"""
import pytest


@pytest.fixture(autouse=True)
def dich_vu_kn_crm(settings):
    settings.ROOT_URLCONF = "knjsc.urls_bangtinh"
    settings.BANGTINH_URL = ""       # ở chính KN CRM, mục KN CRM là liên kết trong
