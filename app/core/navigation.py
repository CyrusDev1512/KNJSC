"""Điều hướng chung.

Khai báo ở một chỗ duy nhất (quy tắc 7). Mỗi mục ghi cấp bậc tối thiểu để
vào được; thanh bên chỉ hiện những mục người dùng có quyền.

Ẩn mục trên giao diện **không phải** là kiểm quyền — nguyên tắc P1 nói
quyền phải kiểm ở máy chủ. Ẩn ở đây chỉ để đỡ rối mắt; view vẫn tự chặn.
"""
from dataclasses import dataclass, field

from django.conf import settings
from django.urls import NoReverseMatch, reverse

from .constants import Rank
from .permissions import has_rank, in_departments

#: Lên đơn là chức năng của bộ phận Sale — `docs/04` mục 3 ghi rõ Vận đơn
#: bị từ chối ở màn hình này.
SALES_ONLY = ("sale",)
#: Bảng tính là chỗ làm việc của bộ phận Vận đơn — AC-11.4
WAYBILL_ONLY = ("van-don",)


@dataclass(frozen=True)
class NavItem:
    code: str
    label: str
    url_name: str
    min_rank: str = Rank.STAFF
    #: Tên kỹ thuật của các bộ phận vào được. None nghĩa là mọi bộ phận.
    #: Dùng cho màn hình chỉ thuộc về một bộ phận, ví dụ Lên đơn là của Sale
    #: — xem ma trận kiểm chéo ở `docs/04` mục 3.
    departments: tuple = None
    #: Tên biến settings chứa địa chỉ ngoài. Có giá trị thì mục này trỏ ra
    #: dịch vụ khác (Bảng tính chạy riêng — ADR-009); rỗng thì dùng url_name.
    external_setting: str = ""

    def href(self):
        """Địa chỉ thật của mục, hoặc None nếu dịch vụ hiện tại không có nó.

        Dịch vụ `bangtinh` dùng URLconf thu hẹp: mục nào không có ở đó thì
        thanh bên không vẽ — thay vì nổ NoReverseMatch trên mọi trang.
        """
        if self.external_setting and getattr(settings, self.external_setting, ""):
            return getattr(settings, self.external_setting)
        try:
            return reverse(self.url_name)
        except NoReverseMatch:
            return None


@dataclass(frozen=True)
class NavGroup:
    label: str
    items: tuple = field(default_factory=tuple)


NAVIGATION = (
    NavGroup("Tổng quan", (
        NavItem("tong_quan", "Tổng quan", "tong_quan"),
    )),
    NavGroup("Tổ chức", (
        NavItem("nhan_su", "Nhân sự", "nhan_su", Rank.LEADER),
        NavItem("bo_phan", "Bộ phận và team", "bo_phan", Rank.ADMIN),
    )),
    NavGroup("Báo cáo", (
        NavItem("bao_cao_ngay", "Nộp báo cáo ngày", "bao_cao_ngay"),
        NavItem("bao_cao_lich_su", "Lịch sử báo cáo", "bao_cao_lich_su"),
        # Mọi cấp bậc, mọi bộ phận — FR-5.5 lọc bằng phạm vi, không bằng cấp bậc
        NavItem("bao_cao_tong_hop", "Báo cáo tổng hợp", "bao_cao_tong_hop"),
    )),
    NavGroup("Đơn hàng", (
        NavItem("len_don", "Lên đơn", "len_don", departments=SALES_ONLY),
        NavItem("don_hang", "Đơn hàng", "don_hang", departments=SALES_ONLY),
    )),
    NavGroup("Dữ liệu", (
        NavItem("bang", "Bảng dữ liệu", "bang"),
        NavItem("bang_tinh", "Bảng tính", "bang_tinh", departments=WAYBILL_ONLY,
                external_setting="BANGTINH_URL"),
        NavItem("bieu_mau", "Biểu mẫu", "bieu_mau", Rank.MANAGER),
        NavItem("tac_vu", "Tác vụ nền", "tac_vu"),
    )),
    NavGroup("Quản trị", (
        NavItem("nhat_ky", "Nhật ký hoạt động", "nhat_ky", Rank.MANAGER),
        NavItem("ma_tran_quyen", "Ma trận phân quyền", "ma_tran_quyen", Rank.MANAGER),
    )),
)


def visible_navigation(user):
    """Các nhóm và mục người này được vào. Nhóm rỗng thì bỏ luôn."""
    ket_qua = []
    for group in NAVIGATION:
        items = [
            {"code": m.code, "label": m.label, "href": href}
            for m in group.items
            if has_rank(user, m.min_rank) and in_departments(user, m.departments)
            and (href := m.href())
        ]
        if items:
            ket_qua.append({"label": group.label, "items": items})
    return ket_qua
