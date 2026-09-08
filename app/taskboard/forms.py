"""Biểu mẫu của Công việc. Nhãn tiếng Việt."""
from django import forms
from django.contrib.auth import get_user_model

from core.identity import display_name

from .constants import TITLE_MAX, TaskPriority


class NguoiLamField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return display_name(obj)


class CongViecForm(forms.Form):
    title = forms.CharField(label="Tiêu đề", max_length=TITLE_MAX)
    description = forms.CharField(
        label="Mô tả", required=False, widget=forms.Textarea(attrs={"rows": 4}),
    )
    assignee = NguoiLamField(
        label="Người làm", queryset=get_user_model().objects.none(),
        required=False, empty_label="Chính tôi",
        help_text="Chỉ hiện người trong phạm vi của bạn.",
    )
    priority = forms.ChoiceField(label="Ưu tiên", choices=TaskPriority.choices, initial=TaskPriority.VUA)
    due_date = forms.DateField(
        label="Hạn", required=False, widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )

    def __init__(self, *args, nguoi=None, sua=False, **kwargs):
        super().__init__(*args, **kwargs)
        if nguoi is not None:
            self.fields["assignee"].queryset = nguoi
        if sua:
            # Trang sửa: để trống là giữ nguyên người làm, không phải giao lại cho mình
            self.fields["assignee"].empty_label = "— giữ nguyên người làm —"
            self.fields["assignee"].help_text = "Để trống thì giữ nguyên; đổi người thì việc chuyển sang bộ phận của người đó."
