"""Sổ danh sách và quy tắc hiển thị của Bảng tính vận đơn — ADR-009.

Khai ở một chỗ duy nhất (quy tắc 7). Cột nào là danh sách chọn, danh sách
lấy từ đâu, dòng nào tô màu, cột nào đứng trước — tất cả ở đây; lưới, ô sửa
và luồng nhập tệp đều đọc từ đây.
"""
from forms_builder import choice_registry
from orders.constants import (
    WAYBILL_DEPARTMENT_CODE, WAYBILL_TABLE_CODE, Market, PaymentStatus,
    Reconciliation, ShippingStatus,
)


def _nhan(choices):
    return [c.label for c in choices]


def nhan_vien_van_don():
    """Mã tài khoản của người đang làm ở bộ phận Vận đơn — như cột
    "Nhân viên Vận đơn được giao" trong tệp thật ghi PHUONGVH, TIENNLT."""
    from org.models import UserProfile

    return list(
        UserProfile.objects.filter(
            department__code=WAYBILL_DEPARTMENT_CODE, user__is_active=True,
        ).order_by("user__username").values_list("user__username", flat=True)
    )


#: Cột → (hàm danh sách, chặt hay gợi ý). Đăng ký vào sổ chung lúc app khởi động.
DANH_SACH = {
    "trang_thai_vc": (lambda: _nhan(ShippingStatus), True),
    "trang_thai_tt": (lambda: _nhan(PaymentStatus), True),
    "doi_soat": (lambda: _nhan(Reconciliation), True),
    "quoc_gia": (lambda: _nhan(Market), True),
    # Gợi ý, không chặt: tệp cũ ghi mã người đã nghỉ, không vì thế mà bỏ dòng
    "nv_van_don": (nhan_vien_van_don, False),
}


def register_all():
    for ma_cot, (ham, chat) in DANH_SACH.items():
        choice_registry.register(WAYBILL_TABLE_CODE, ma_cot, ham, strict=chat)


def options(column_code):
    return choice_registry.options_for(WAYBILL_TABLE_CODE, column_code)


#: Dòng có trạng thái này được tô màu "xấu" — như tệp thật tô đỏ đơn Hủy.
STATUS_HIGHLIGHT = {
    ShippingStatus.HUY_TRUOC_GIAO.label: "dong-xau",
    ShippingStatus.HUY_SAU_GIAO.label: "dong-xau",
    ShippingStatus.HOAN_DON.label: "dong-xau",
    ShippingStatus.DA_NHAN_HANG.label: "dong-tot",
}


def row_class(trang_thai):
    return STATUS_HIGHLIGHT.get(trang_thai or "", "")


#: Số cột đầu cố định khi cuộn ngang — như tệp thật cố định Lọc trùng + Name.
#: Giá trị thật lấy từ `core.constants.GRID_FROZEN_COLUMNS`; đây chỉ là tên.
FROZEN_FIRST = ("ma_don", "ngay", "ten_khach", "so_dien_thoai")
#: Độ rộng (px) từng cột cố định — cột `position: sticky` cần biết `left`
FROZEN_WIDTHS = (110, 100, 170, 130)
