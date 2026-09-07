"""Biểu mẫu của Tài nguyên. Nhãn tiếng Việt."""
from django import forms
from django.contrib.auth import get_user_model

from core.identity import display_name
from org.models import Department

from .constants import LINK_MAX, NAME_MAX, NOTE_MAX, ResourceStatus
from .models import ResourceCategory


class NguoiGiuField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return display_name(obj)


class TaiNguyenForm(forms.Form):
    category = forms.ModelChoiceField(label="Mục", queryset=ResourceCategory.objects.none())
    name = forms.CharField(label="Tên", max_length=NAME_MAX, help_text="Ví dụ: BM Kim Ngân 03, Page KN Beauty CA.")
    status = forms.ChoiceField(label="Trạng thái", choices=ResourceStatus.choices, initial=ResourceStatus.TRONG)
    holder = NguoiGiuField(
        label="Người giữ", queryset=get_user_model().objects.none(), required=False, empty_label="— chưa ai —",
    )
    department = forms.ModelChoiceField(
        label="Bộ phận dùng", queryset=Department.objects.none(), required=False, empty_label="— chưa rõ —",
    )
    link = forms.URLField(
        label="Liên kết", required=False, max_length=LINK_MAX, assume_scheme="https",
        help_text="Địa chỉ trang, trình quản lý quảng cáo… nếu có.",
    )
    note = forms.CharField(
        label="Ghi chú", max_length=NOTE_MAX, required=False, widget=forms.Textarea(attrs={"rows": 3}),
        help_text="Không ghi mật khẩu hay mã bí mật ở đây.",
    )

    def __init__(self, *args, cac_muc=None, nguoi=None, bo_phan=None, **kwargs):
        super().__init__(*args, **kwargs)
        if cac_muc is not None:
            self.fields["category"].queryset = cac_muc
        if nguoi is not None:
            self.fields["holder"].queryset = nguoi
        if bo_phan is not None:
            self.fields["department"].queryset = bo_phan
