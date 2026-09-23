"""Đăng nhập không phân biệt hoa/thường ở tên đăng nhập — ADR-037.

Tài khoản mới có tên đăng nhập = mã nhân sự viết hoa (`THUANLT`); người dùng gõ
`thuanlt` vẫn phải vào được. `account_service.create_account` đã chặn hai tài khoản
chỉ khác hoa/thường (`username__iexact`), nên tra `iexact` không bao giờ nhập nhằng.
Kiểm mật khẩu, khoá tạm, phiên giữ nguyên của `ModelBackend`.

`get_user` lấy kèm hồ sơ nhân sự trong cùng một lệnh: mọi yêu cầu đã đăng nhập đều đọc
`user.profile` (mốc phiên ở `SessionTimeoutMiddleware`, phạm vi quyền ở `core.scope`), nên
tách hai lệnh là tốn một truy vấn ở mọi màn hình (AC-10.2). Không có hồ sơ thì `user.profile`
vẫn báo thiếu như trước.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class CaseInsensitiveModelBackend(ModelBackend):
    def get_user(self, user_id):
        User = get_user_model()
        try:
            user = User._default_manager.select_related("profile").get(pk=user_id)
        except User.DoesNotExist:
            return None
        return user if self.user_can_authenticate(user) else None

    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        if username is None or password is None:
            return None
        try:
            user = User._default_manager.get(**{f"{User.USERNAME_FIELD}__iexact": username})
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            # Chạy băm một lần để thời gian trả lời không lộ tài khoản có tồn tại hay không
            User().set_password(password)
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
