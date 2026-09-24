"""Đăng nhập không phân biệt hoa/thường ở tên đăng nhập — ADR-037.

Tài khoản mới có tên đăng nhập = mã nhân sự viết hoa (`THUANLT`); người dùng gõ
`thuanlt` vẫn phải vào được. `account_service.create_account` đã chặn hai tài khoản
chỉ khác hoa/thường (`username__iexact`), nên tra `iexact` không bao giờ nhập nhằng.
Kiểm mật khẩu, khoá tạm, phiên giữ nguyên của `ModelBackend`.

`get_user` lấy kèm hồ sơ nhân sự và bộ phận trong **cùng một lượt hỏi**: mọi yêu cầu
đã đăng nhập đều đọc `user.profile` (phạm vi quyền, nhãn mã nhân sự) và
`profile.department` (`is_accountant`), nên để lười thì mỗi trang trả thêm hai lượt
hỏi cơ sở dữ liệu (K24). Không lấy kèm team: phạm vi quyền đọc `department_id` và
`scope_team_ids()` (truy vấn riêng của Leader), số đo K24 không thấy team bị nạp lười.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class CaseInsensitiveModelBackend(ModelBackend):
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

    def get_user(self, user_id):
        """Người dùng của phiên, kèm hồ sơ và bộ phận trong một lượt hỏi."""
        User = get_user_model()
        try:
            user = (User._default_manager
                    .select_related("profile__department")
                    .get(pk=user_id))
        except User.DoesNotExist:
            return None
        return user if self.user_can_authenticate(user) else None
