"""Nhãn giao diện và mã tài khoản cho định danh nghiệp vụ."""


def display_name(user):
    """Họ tên trong hồ sơ, không có thì tên đăng nhập; không có người thì rỗng."""
    if user is None:
        return ""
    ho_so = getattr(user, "profile", None)
    ho_ten = (getattr(ho_so, "full_name", "") or "").strip()
    return ho_ten or user.get_username()


def employee_code(user):
    """Mã đăng nhập; không suy danh tính từ họ tên có thể trùng."""
    return user.get_username() if user is not None else ""
