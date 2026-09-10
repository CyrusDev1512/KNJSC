"""Sidebar của app KN CRM — ADR-015, dáng theo Teeze.

Riêng, không dùng chung `core.navigation.NAVIGATION` của KN ERP: ở dịch vụ
8021 phần lớn mục ERP không có đường dẫn, còn KN CRM cần mục **sinh động** —
mỗi bộ phận trong phạm vi là một mục con của "Bảng tính". Lớp CSS tính ở
đây, không đặt điều kiện trong thuộc tính class của template (luật K15).

Mục đang chọn lấy từ `request.nav_current`: `tong_quan`, `thu_muc` (hay `bang`
của các view forms_builder), `bp:<mã bộ phận>` (trang thư mục của một bộ phận),
`nhap_tep`, `cap_quyen`, `tac_vu`, `nhat_ky`.
"""
from dataclasses import dataclass, field

from django.conf import settings
from django.urls import NoReverseMatch, reverse

from core.constants import Rank
from core.permissions import has_rank, in_departments
from core.navigation import SALES_ONLY


@dataclass(frozen=True)
class CrmNavItem:
    code: str
    label: str
    href: str
    icon: str = ""
    current: bool = False
    #: Mục con (bộ phận dưới "Bảng tính"); có thì vẽ thành nhóm gập được
    children: tuple = field(default_factory=tuple)
    #: Nhóm mở sẵn khi chính nó hay một mục con đang chọn
    mo: bool = False
    new_tab: bool = False

    @property
    def lop(self):
        return "nav-muc crm-dang" if self.current else "nav-muc"

    @property
    def lop_con(self):
        return "nav-muc crm-con crm-dang" if self.current else "nav-muc crm-con"


def _url(ten, *args):
    try:
        return reverse(ten, args=args)
    except NoReverseMatch:
        return None


def build(user, current=""):
    """Danh sách mục cho người này. Bộ phận dưới "Bảng tính" lấy từ phạm vi
    quyền (`tree_service.departments_of`), nên Sale không thấy nhánh Vận đơn."""
    from forms_builder.models import TableDef

    from .services import tree_service

    muc = []
    cac_bang = []
    if in_departments(user, SALES_ONLY) and (u := _url("waybill_create")) is not None:
        muc.append(CrmNavItem("waybill_create", "Lên đơn", u, "", current == "waybill_create"))
    if (u := _url("tong_quan")) is not None:
        muc.append(CrmNavItem("tong_quan", "Trang chủ", u, "⌂", current == "tong_quan"))
    if (u := _url("thu_muc")) is not None:
        # Một truy vấn, không kéo cột như `tree_service.all_tables` — sidebar ở mọi trang
        cac_bang = list(TableDef.objects.in_scope(user).select_related("department").only("id", "department", "code"))
        con = tuple(
            CrmNavItem(f"bp:{d.code}", d.name, tree_service.home_url(d), "▸", current == f"bp:{d.code}")
            for d in tree_service.departments_of(user, cac_bang)
        )
        # `bang` là nav_current của các view forms_builder (tạo bảng, sửa cột, nhập)
        dang = current in ("thu_muc", "bang") or any(c.current for c in con)
        muc.append(CrmNavItem("thu_muc", "Bảng tính", u, "▦", current in ("thu_muc", "bang"), con, mo=dang))
    if any(b.code == 'van_don_moi' for b in cac_bang) and (u := _url('crm_statistics')):
        muc.append(CrmNavItem('statistics', 'Thống kê', u, '▥', current == 'statistics'))
    if has_rank(user, Rank.LEADER) and (u := _url("nhap_tep")) is not None:
        muc.append(CrmNavItem("nhap_tep", "Nhập tệp", u, "⇪", current == "nhap_tep"))
    if has_rank(user, Rank.MANAGER) and (u := _url("cap_quyen")) is not None:
        muc.append(CrmNavItem("cap_quyen", "Cấp quyền", u, "✓", current == "cap_quyen"))
    if (u := _url("tac_vu")) is not None:
        muc.append(CrmNavItem("tac_vu", "Tác vụ nền", u, "◔", current == "tac_vu"))
    if has_rank(user, Rank.MANAGER) and (u := _url("nhat_ky")) is not None:
        muc.append(CrmNavItem("nhat_ky", "Nhật ký", u, "≡", current == "nhat_ky"))
    erp = getattr(settings, "MAIN_APP_URL", "")
    if erp:
        muc.append(CrmNavItem("erp", "KN ERP", erp.rstrip("/") + "/", "↗"))
    return muc
