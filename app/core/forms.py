"""Biểu mẫu của core. Thông báo lỗi viết bằng tiếng Việt."""
from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .services import auth_service


class LoginForm(AuthenticationForm):
    """Đăng nhập, có kiểm khoá tạm (FR-1.2).

    Thông báo lỗi cố tình không phân biệt sai email và sai mật khẩu, để
    không lộ ra tài khoản nào có tồn tại.
    """

    error_messages = {
        "invalid_login": "Email hoặc mật khẩu không đúng.",
        "inactive": "Tài khoản đã bị khoá. Liên hệ quản trị viên.",
    }

    username = forms.CharField(
        label="Email", widget=forms.TextInput(attrs={"autofocus": True, "autocomplete": "username"}),
    )
    password = forms.CharField(
        label="Mật khẩu", strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )

    def clean(self):
        username = self.cleaned_data.get("username")
        if username:
            nguoi_dung = auth_service.find_user(username)
            if nguoi_dung and auth_service.is_locked(nguoi_dung):
                phut = max(1, round(auth_service.lock_remaining(nguoi_dung) / 60))
                raise forms.ValidationError(
                    f"Tài khoản đang bị khoá tạm. Vui lòng thử lại sau {phut} phút."
                )
        return super().clean()
