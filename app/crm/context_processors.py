"""Khung và sidebar KN CRM đưa vào mọi template.

`khung` là tệp khung mà các template dùng chung của `forms_builder` (tạo
bảng, sửa cột, nhập tệp) kế thừa: ở KN ERP là `base.html`, ở KN CRM là
`crm/base_crm.html` có sidebar — ADR-015. Đăng ký chung ở `settings/base.py`
để bộ kiểm (đổi `ROOT_URLCONF` bằng override) cũng có; ở KN ERP không tốn
truy vấn nào.
"""
from django.conf import settings

KHUNG_ERP = "base.html"
KHUNG_CRM = "crm/base_crm.html"
#: Logo (tệp trong static/) — favicon và dấu hiệu ở đầu khung, theo dịch vụ
LOGO_ERP = "img/kn-jsc.svg"
LOGO_CRM = "img/kn-crm.svg"


def khung_crm(request):
    if settings.ROOT_URLCONF != "knjsc.urls_bangtinh":
        return {"khung": KHUNG_ERP, "logo": LOGO_ERP}
    if not request.user.is_authenticated:
        return {"khung": KHUNG_CRM, "logo": LOGO_CRM}
    from .navigation import build

    return {"khung": KHUNG_CRM, "logo": LOGO_CRM, "crm_nav": build(request.user, getattr(request, "nav_current", ""))}
