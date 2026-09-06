"""Danh tính hiển thị của một tài khoản — FR-4.6, Q55.

Một luật duy nhất cho cả hệ thống: **họ tên trong hồ sơ, không có thì tên đăng
nhập**. Cột Người bán trên bảng vận đơn, trường Marketer trên báo cáo ngày và
tên ở góc màn hình đều lấy từ đây, nên báo cáo tổng hợp nhóm theo nhân viên
mới khớp nhau. `core` không import module nào khác: đọc hồ sơ qua thuộc tính
`user.profile` theo đúng giao ước với `org` (xem `core/scope.py`).
"""


def display_name(user):
    """Họ tên trong hồ sơ, không có thì tên đăng nhập; không có người thì rỗng."""
    if user is None:
        return ""
    ho_so = getattr(user, "profile", None)
    ho_ten = (getattr(ho_so, "full_name", "") or "").strip()
    return ho_ten or user.get_username()
