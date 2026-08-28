"""Biểu mẫu của org. Nhãn và thông báo lỗi bằng tiếng Việt."""
from django import forms
from django.contrib.auth import get_user_model

from core.constants import Rank

from .models import Department, Team, UserProfile


class TaoTaiKhoanForm(forms.Form):
    """Tạo tài khoản mới kèm hồ sơ nhân sự."""

    username = forms.CharField(label="Tên đăng nhập", max_length=150)
    email = forms.EmailField(label="Email")
    full_name = forms.CharField(label="Họ tên", max_length=150)
    rank = forms.ChoiceField(label="Cấp bậc", choices=Rank.choices, initial=Rank.STAFF)
    department = forms.ModelChoiceField(
        label="Bộ phận", queryset=Department.objects.all(),
        required=False, empty_label="Không thuộc bộ phận nào",
    )
    team = forms.ModelChoiceField(
        label="Team", queryset=Team.objects.all(),
        required=False, empty_label="Chưa gán team",
    )
    password = forms.CharField(
        label="Mật khẩu tạm", min_length=10, widget=forms.PasswordInput,
        help_text="Người dùng bắt buộc đổi ở lần đăng nhập đầu tiên.",
    )

    def clean_username(self):
        ten = self.cleaned_data["username"]
        if get_user_model().objects.filter(username__iexact=ten).exists():
            raise forms.ValidationError("Tên đăng nhập này đã có người dùng.")
        return ten

    def clean(self):
        du_lieu = super().clean()
        team, bo_phan = du_lieu.get("team"), du_lieu.get("department")
        if team and bo_phan and team.department_id != bo_phan.id:
            raise forms.ValidationError(
                f"Team {team} thuộc bộ phận {team.department}, không thuộc {bo_phan}."
            )
        if du_lieu.get("rank") != Rank.ADMIN and not bo_phan:
            raise forms.ValidationError("Phải chọn bộ phận, trừ khi cấp bậc là Quản trị viên.")
        return du_lieu


class SuaHoSoForm(forms.ModelForm):
    """Sửa hồ sơ. Đổi cấp bậc, bộ phận hoặc team làm phiên đang mở mất hiệu lực."""

    class Meta:
        model = UserProfile
        fields = ("full_name", "rank", "department", "team")
        labels = {
            "full_name": "Họ tên", "rank": "Cấp bậc",
            "department": "Bộ phận", "team": "Team",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["department"].queryset = Department.objects.all()
        self.fields["team"].queryset = Team.objects.all()
        self.fields["department"].empty_label = "Không thuộc bộ phận nào"
        self.fields["team"].empty_label = "Chưa gán team"

    def clean(self):
        du_lieu = super().clean()
        team, bo_phan = du_lieu.get("team"), du_lieu.get("department")
        if team and bo_phan and team.department_id != bo_phan.id:
            raise forms.ValidationError(
                f"Team {team} thuộc bộ phận {team.department}, không thuộc {bo_phan}."
            )
        return du_lieu


class BoPhanForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ("name", "code", "is_active")
        labels = {"name": "Tên bộ phận", "code": "Mã", "is_active": "Đang hoạt động"}


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ("name", "department", "leader", "is_active")
        labels = {
            "name": "Tên team", "department": "Bộ phận",
            "leader": "Trưởng nhóm", "is_active": "Đang hoạt động",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["department"].queryset = Department.objects.all()
        self.fields["department"].empty_label = "Chọn bộ phận"
        # Chỉ người có cấp bậc Trưởng nhóm mới được chọn làm leader
        self.fields["leader"].queryset = get_user_model().objects.filter(
            profile__rank=Rank.LEADER
        ).select_related("profile")
        self.fields["leader"].empty_label = "Chưa có trưởng nhóm"
