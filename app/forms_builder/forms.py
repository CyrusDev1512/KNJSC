"""Biểu mẫu của forms_builder. Nhãn và thông báo lỗi bằng tiếng Việt."""
from django import forms

from .meaning import ALLOWED_TYPES, FieldType, Meaning, choices_with_hint
from .models import ColumnDef, ComputeOp, TableDef


class TableForm(forms.ModelForm):
    """Tạo hoặc sửa một bảng — FR-8.1."""

    class Meta:
        model = TableDef
        fields = ["name", "code", "description"]
        labels = {"name": "Tên bảng", "code": "Tên kỹ thuật", "description": "Mô tả"}
        help_texts = {
            "code": "Tiếng Anh, không dấu, dùng làm khoá trong cơ sở dữ liệu. Không đổi được về sau.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tên kỹ thuật đã vào dữ liệu thì không cho đổi — mọi bản ghi tham
        # chiếu tới nó
        if self.instance.pk:
            self.fields["code"].disabled = True


class ColumnForm(forms.ModelForm):
    """Thêm hoặc sửa một cột.

    `ColumnDef.clean()` lo phần kiểm chéo giữa nhãn, kiểu và công thức; biểu
    mẫu này chỉ lo phần hiển thị.
    """

    class Meta:
        model = ColumnDef
        fields = [
            "name", "code", "field_type", "meaning", "required", "order",
            "is_computed", "compute_op", "compute_left", "compute_right",
            "compute_decimals",
        ]
        labels = {
            "name": "Nhãn hiển thị", "code": "Tên kỹ thuật",
            "field_type": "Kiểu dữ liệu", "meaning": "Nhãn ý nghĩa",
            "required": "Bắt buộc nhập", "order": "Thứ tự",
            "is_computed": "Là cột tính sẵn", "compute_op": "Phép tính",
            "compute_left": "Toán hạng A", "compute_right": "Toán hạng B",
            "compute_decimals": "Số chữ số thập phân",
        }
        help_texts = {
            "name": "Tiếng Việt, người dùng nhìn thấy.",
            "code": "Tiếng Anh, không dấu.",
        }

    def __init__(self, *args, table=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.table = table or self.instance.table
        if self.instance.pk:
            self.fields["code"].disabled = True

        # Nhãn ý nghĩa kèm mô tả ngắn, và bỏ những nhãn đã có cột khác giữ
        da_dung = set(
            self.table.columns.exclude(pk=self.instance.pk)
            .exclude(meaning="").values_list("meaning", flat=True)
        )
        self.fields["meaning"].choices = [
            (ma, nhan) for ma, nhan in choices_with_hint()
            if ma == "" or ma not in da_dung
        ]
        self.fields["meaning"].required = False

        # Toán hạng chỉ chọn được trong các cột của chính bảng này, và không
        # chọn được cột tính sẵn khác (tránh phụ thuộc vòng)
        chon = [("", "— chọn cột —")] + [
            (c.code, c.name)
            for c in self.table.columns.filter(is_computed=False).order_by("order", "id")
            if c.pk != self.instance.pk
        ]
        for ten in ("compute_left", "compute_right"):
            self.fields[ten] = forms.ChoiceField(
                label=self.fields[ten].label, choices=chon, required=False,
            )
        self.fields["compute_op"] = forms.ChoiceField(
            label="Phép tính", choices=[("", "— chọn phép tính —")] + ComputeOp.choices,
            required=False,
        )

    def clean(self):
        du_lieu = super().clean()
        self.instance.table = self.table
        return du_lieu


#: Kiểu dữ liệu mà mỗi nhãn nhận, đưa xuống giao diện để hiện gợi ý
TYPES_FOR_MEANING = {
    ma.value: sorted(FieldType(k).label for k in ALLOWED_TYPES[ma])
    for ma in Meaning
}
