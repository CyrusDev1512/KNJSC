"""Biểu mẫu của Tài liệu. Nhãn tiếng Việt."""
from django import forms

from .constants import DESCRIPTION_MAX, TITLE_MAX
from .models import DocumentCategory


class TaiLenForm(forms.Form):
    """Tải lên một tệp hoặc thêm một liên kết."""

    category = forms.ModelChoiceField(label="Mục", queryset=DocumentCategory.objects.none())
    title = forms.CharField(label="Tiêu đề", max_length=TITLE_MAX)
    description = forms.CharField(
        label="Mô tả", max_length=DESCRIPTION_MAX, required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    file = forms.FileField(
        label="Tệp", required=False,
        help_text="PDF, Word, Excel, CSV, ảnh JPG hoặc PNG; tối đa 10 MB.",
    )
    link = forms.URLField(
        label="Hoặc liên kết", required=False, max_length=500, assume_scheme="https",
        help_text="Dán địa chỉ Google Drive, Notion… nếu không tải tệp.",
    )

    def __init__(self, *args, cac_muc=None, **kwargs):
        super().__init__(*args, **kwargs)
        if cac_muc is not None:
            self.fields["category"].queryset = cac_muc
