"""Biểu mẫu của org. Nhãn và thông báo lỗi bằng tiếng Việt."""
from django import forms
from django.contrib.auth import get_user_model

from core.constants import Rank
from core.exceptions import BusinessError

from .models import Department, Team, UserProfile
from .services import staff_code_service


class TaoTaiKhoanForm(forms.Form):
    """Tạo tài khoản mới kèm hồ sơ nhân sự.

    ADR-037: mã nhân sự gợi ý từ họ tên theo quy ước THUANLT, Admin sửa được trước
    khi lưu; tên đăng nhập để trống thì chính là mã.
    """

    full_name = forms.CharField(label="Họ tên", max_length=150)
    staff_code = forms.CharField(
        label="Mã nhân sự", max_length=20, required=False,
        help_text="Tự gợi ý từ họ tên (Lê Thưởng Thuận → THUANLT, trùng thì THUANLT2). "
                  "Sửa được trước khi lưu; đã lưu thì cố định.",
    )
    username = forms.CharField(
        label="Tên đăng nhập", max_length=150, required=False,
        help_text="Để trống thì tên đăng nhập là mã nhân sự.",
    )
    # Không hỏi email và ngày sinh khi tạo (chốt 24.09.2026): đăng nhập bằng mã nhân sự,
    # không gửi mail cho nhân viên; ngày sinh bổ sung sau ở màn Sửa hồ sơ (SuaHoSoForm)
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
        label="Mật khẩu tạm", min_length=10, required=False, strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text="Để trống để hệ thống tự sinh. Người dùng bắt buộc đổi ở lần đăng nhập đầu tiên.",
    )

    def clean_staff_code(self):
        ma = staff_code_service.normalise(self.cleaned_data.get("staff_code", ""))
        if not ma:
            return ""
        try:
            staff_code_service.validate(ma)
        except BusinessError as loi:
            raise forms.ValidationError(str(loi))
        if staff_code_service._taken(ma):
            raise forms.ValidationError("Mã nhân sự này đã có người dùng.")
        return ma

    def clean_username(self):
        ten = (self.cleaned_data.get("username") or "").strip()
        if ten and get_user_model().objects.filter(username__iexact=ten).exists():
            raise forms.ValidationError("Tên đăng nhập này đã có người dùng.")
        return ten

    def clean(self):
        du_lieu = super().clean()
        team, bo_phan = du_lieu.get("team"), du_lieu.get("department")
        if team and bo_phan and team.department_id != bo_phan.id:
            raise forms.ValidationError(
                f"Team {team} thuộc bộ phận {team.department}, không thuộc {bo_phan}."
            )
        if du_lieu.get("rank") not in (Rank.ADMIN, Rank.CEO) and not bo_phan:
            raise forms.ValidationError("Phải chọn bộ phận, trừ khi cấp bậc là Giám đốc hoặc Quản trị viên.")
        if "staff_code" in du_lieu and "username" in du_lieu and du_lieu.get("full_name"):
            if not du_lieu["staff_code"]:
                du_lieu["staff_code"] = staff_code_service.suggest(
                    du_lieu["full_name"], du_lieu["username"])
            if not du_lieu["username"]:
                # Tài khoản mới: tên đăng nhập = mã (sheet Quy ước 1.0)
                du_lieu["username"] = du_lieu["staff_code"]
                if get_user_model().objects.filter(username__iexact=du_lieu["username"]).exists():
                    raise forms.ValidationError("Tên đăng nhập này đã có người dùng.")
        return du_lieu


class SuaHoSoForm(forms.ModelForm):
    """Sửa hồ sơ. Đổi cấp bậc, bộ phận hoặc team làm phiên đang mở mất hiệu lực."""

    class Meta:
        model = UserProfile
        fields = ("full_name", "staff_code", "rank", "department", "team", "birthday")
        labels = {
            "full_name": "Họ tên", "staff_code": "Mã nhân sự", "rank": "Cấp bậc",
            "department": "Bộ phận", "team": "Team", "birthday": "Ngày sinh",
        }
        widgets = {"birthday": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["department"].queryset = Department.objects.all()
        self.fields["team"].queryset = Team.objects.all()
        self.fields["department"].empty_label = "Không thuộc bộ phận nào"
        self.fields["team"].empty_label = "Chưa gán team"
        # ADR-037: mã cố định sau khi gán; hồ sơ cũ chưa có mã thì Admin gán một lần
        ma = self.fields["staff_code"]
        ma.required = False
        if self.instance.pk and self.instance.staff_code:
            ma.disabled = True
            ma.help_text = "Mã nhân sự cố định, không đổi được."
        else:
            ma.help_text = "Để trống thì hệ thống tự gợi ý theo họ tên (quy ước THUANLT)."

    def clean_staff_code(self):
        if self.fields["staff_code"].disabled:
            return self.instance.staff_code
        ma = staff_code_service.normalise(self.cleaned_data.get("staff_code", ""))
        if not ma:
            return ""
        try:
            staff_code_service.validate(ma)
        except BusinessError as loi:
            raise forms.ValidationError(str(loi))
        if staff_code_service._taken(ma, exclude_pk=self.instance.pk,
                                     exclude_user_pk=self.instance.user_id):
            raise forms.ValidationError("Mã nhân sự này đã có người dùng.")
        return ma

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
            profile__rank=Rank.LEADER, profile__deleted_at__isnull=True, is_active=True,
        ).select_related("profile")
        self.fields["leader"].empty_label = "Chưa có trưởng nhóm"
