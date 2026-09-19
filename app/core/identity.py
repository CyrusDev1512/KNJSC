"""Nhãn giao diện và mã nhân sự cho định danh nghiệp vụ — một nguồn duy nhất (ADR-037).

Quy ước hiển thị: chỗ nào cần **định danh** (bảng, danh sách, lịch sử, Excel, nhật ký)
thì **mã trước, tên sau** — `THUANLT · Lê Thưởng Thuận`; lời chào và avatar dùng họ tên.
Không màn hình hay truy vấn nào tự ghép `username`: dùng các hàm ở đây.
"""
from django.db.models import Case, CharField, F, Q, Value, When
from django.db.models.functions import Coalesce, Concat, NullIf

#: Dấu nối giữa mã và họ tên trên mọi màn hình
SEPARATOR = " · "
#: Dấu nối giữa **nhiều người** trong cùng một ô (báo cáo gộp theo ngày dùng `StringAgg`)
JOIN = ", "


def split_labels(joined):
    """Tách chuỗi nhiều định danh do `JOIN` nối thành danh sách, bỏ phần rỗng.

    Màn hình liệt kê mỗi người một dòng cho dễ đọc; Excel và bộ lọc vẫn dùng chuỗi nối."""
    return [part for part in (joined or "").split(JOIN) if part]


def display_name(user):
    """Họ tên trong hồ sơ, không có thì tên đăng nhập; không có người thì rỗng."""
    if user is None:
        return ""
    ho_so = getattr(user, "profile", None)
    ho_ten = (getattr(ho_so, "full_name", "") or "").strip()
    return ho_ten or user.get_username()


def employee_code(user):
    """Mã nhân sự (`UserProfile.staff_code`); hồ sơ chưa gán hoặc không có hồ sơ thì tên
    đăng nhập. Không suy danh tính từ họ tên có thể trùng."""
    if user is None:
        return ""
    ho_so = getattr(user, "profile", None)
    ma = (getattr(ho_so, "staff_code", "") or "").strip()
    return ma or user.get_username()


def identity_label(user):
    """`MÃ · Họ tên`; không có họ tên thì chỉ mã; không có người thì rỗng."""
    if user is None:
        return ""
    ma = employee_code(user)
    ho_so = getattr(user, "profile", None)
    ho_ten = (getattr(ho_so, "full_name", "") or "").strip()
    return f"{ma}{SEPARATOR}{ho_ten}" if ho_ten else ma


def _path(prefix, name):
    return f"{prefix}__{name}" if prefix else name


def code_expression(prefix=""):
    """Biểu thức ORM cho `employee_code` trên quan hệ tới User (`prefix` là đường dẫn
    tới User, rỗng nếu chính model User)."""
    return Coalesce(
        NullIf(F(_path(prefix, "profile__staff_code")), Value("")),
        F(_path(prefix, "username")),
        output_field=CharField(),
    )


def label_expression(prefix=""):
    """Biểu thức ORM cho `identity_label`. Người không tồn tại (quan hệ NULL) → NULL,
    để tầng gọi tự đặt nhãn "Chưa phân công"."""
    name = _path(prefix, "profile__full_name")
    code = code_expression(prefix)
    return Case(
        When(Q(**{f"{name}__isnull": True}) | Q(**{name: ""}), then=code),
        default=Concat(code, Value(SEPARATOR), F(name), output_field=CharField()),
        output_field=CharField(),
    )
