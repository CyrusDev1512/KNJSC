"""Lỗi nghiệp vụ có mã.

Thông báo cho người dùng viết bằng tiếng Việt. Mã lỗi bằng tiếng Anh để
tra trong nhật ký.
"""
from django.core.exceptions import PermissionDenied


class BusinessError(Exception):
    """Vi phạm một quy tắc nghiệp vụ. Tầng dịch vụ ném ra, view bắt lại."""

    code = "business_error"
    message = "Thao tác không hợp lệ."

    def __init__(self, message=None, code=None):
        self.message = message or self.message
        self.code = code or self.code
        super().__init__(self.message)


class OutOfScopeError(PermissionDenied):
    """Truy cập ra ngoài phạm vi quyền.

    Kế thừa PermissionDenied để Django trả về 403. Quy tắc 8 và FR-3.5:
    phải trả lỗi từ chối, tuyệt đối không trả danh sách rỗng — trả rỗng
    khiến người dùng tưởng là không có dữ liệu.
    """

    code = "out_of_scope"

    def __init__(self, message="Bạn không có quyền truy cập dữ liệu này."):
        self.message = message
        super().__init__(message)


class AccountLockedError(BusinessError):
    """Tài khoản bị khoá tạm sau nhiều lần đăng nhập sai (FR-1.2)."""

    code = "account_locked"
    message = "Tài khoản đang bị khoá tạm. Vui lòng thử lại sau."


class NoProfileError(PermissionDenied):
    """Tài khoản chưa được gán hồ sơ nhân sự nên không suy ra được phạm vi.

    Kế thừa `PermissionDenied` chứ không phải `BusinessError`: không suy ra được
    phạm vi thì phải trả **403 kèm thông báo tiếng Việt**, không được để Django
    trả lỗi 500 trang trắng (FR-3.5 và NFR-6).

    Xảy ra thật với tài khoản tạo bằng dòng lệnh chưa gán hồ sơ, hoặc người vừa
    bị gỡ khỏi bộ phận.
    """

    code = "no_profile"

    def __init__(self, message="Tài khoản chưa được gán bộ phận và cấp bậc. Liên hệ quản trị viên."):
        self.message = message
        super().__init__(message)
