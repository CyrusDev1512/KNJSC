"""Điều hướng chung.

Khai báo ở một chỗ duy nhất (quy tắc 7). Mỗi mục ghi cấp bậc tối thiểu để
vào được; thanh bên chỉ hiện những mục người dùng có quyền.

Ẩn mục trên giao diện **không phải** là kiểm quyền — nguyên tắc P1 nói
quyền phải kiểm ở máy chủ. Ẩn ở đây chỉ để đỡ rối mắt; view vẫn tự chặn.
"""
from dataclasses import dataclass, field

from .constants import Rank
from .permissions import has_rank


@dataclass(frozen=True)
class NavItem:
    code: str
    label: str
    url_name: str
    min_rank: str = Rank.STAFF


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
    )),
    NavGroup("Đơn hàng", (
        NavItem("len_don", "Lên đơn", "len_don"),
        NavItem("don_hang", "Đơn hàng", "don_hang"),
    )),
    NavGroup("Dữ liệu", (
        NavItem("bang", "Bảng dữ liệu", "bang"),
        NavItem("bieu_mau", "Biểu mẫu", "bieu_mau"),
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
        items = [m for m in group.items if has_rank(user, m.min_rank)]
        if items:
            ket_qua.append({"label": group.label, "items": items})
    return ket_qua
