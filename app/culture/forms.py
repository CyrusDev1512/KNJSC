"""Biểu mẫu ghi nhận. Nhãn tiếng Việt."""
from django import forms

from .constants import MESSAGE_MAX, CoreValue


class GhiNhanForm(forms.Form):
    receiver = forms.IntegerField(label="Đồng nghiệp", min_value=1)
    value = forms.ChoiceField(label="Giá trị văn hoá", choices=CoreValue.choices)
    message = forms.CharField(
        label="Lời nhắn", max_length=MESSAGE_MAX, widget=forms.Textarea(attrs={"rows": 3}),
    )
