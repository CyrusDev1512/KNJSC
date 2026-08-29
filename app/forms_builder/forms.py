"""Biểu mẫu của forms_builder. Nhãn và thông báo lỗi bằng tiếng Việt."""
from django import forms

from .meaning import ALLOWED_TYPES, FieldType, Meaning, choices_with_hint
from .models import (
    ColumnDef, ComputeOp, FieldDef, FormDef, GrantAction, TableDef,
)
from .services import link_service


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


# ══ BIỂU MẪU ══════════════════════════════════════════════════════

class FormForm(forms.ModelForm):
    """Tạo hoặc sửa một biểu mẫu — FR-8.1."""

    class Meta:
        model = FormDef
        fields = ["name", "code", "description", "table"]
        labels = {
            "name": "Tên biểu mẫu", "code": "Tên kỹ thuật",
            "description": "Mô tả", "table": "Bảng đích",
        }
        help_texts = {
            "code": "Tiếng Anh, không dấu. Không đổi được về sau.",
            "table": "Dữ liệu nhập vào biểu mẫu này sẽ ghi vào bảng đó — ADR-007.",
        }

    def __init__(self, *args, department=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.department = department or getattr(self.instance, "department", None)
        # Chỉ chọn được bảng của chính bộ phận mình — ghi chéo bộ phận là một
        # đường vòng qua phạm vi quyền
        self.fields["table"].queryset = TableDef.objects.filter(
            department=self.department, is_active=True,
        )
        self.fields["table"].empty_label = "— chọn bảng đích —"
        if self.instance.pk:
            # Đổi bảng đích thì mọi liên kết trường–cột thành vô nghĩa
            self.fields["code"].disabled = True
            self.fields["table"].disabled = True

    def clean(self):
        du_lieu = super().clean()
        if self.department is not None:
            self.instance.department = self.department
        return du_lieu


class FieldDefForm(forms.ModelForm):
    """Thêm hoặc sửa một định nghĩa trường trong thư viện dùng chung."""

    class Meta:
        model = FieldDef
        fields = ["name", "code", "field_type", "meaning", "hint"]
        labels = {
            "name": "Nhãn hiển thị", "code": "Tên kỹ thuật",
            "field_type": "Kiểu dữ liệu", "meaning": "Nhãn ý nghĩa",
            "hint": "Câu gợi ý dưới ô nhập",
        }
        help_texts = {
            "name": "Tiếng Việt, người dùng nhìn thấy.",
            "code": "Tiếng Anh, không dấu.",
        }

    def __init__(self, *args, department=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.department = department or getattr(self.instance, "department", None)
        self.fields["meaning"].choices = choices_with_hint()
        self.fields["meaning"].required = False
        if self.instance.pk:
            self.fields["code"].disabled = True

    def clean(self):
        du_lieu = super().clean()
        if self.department is not None:
            self.instance.department = self.department
        return du_lieu


class FormFieldForm(forms.Form):
    """Đưa một trường vào biểu mẫu và nối vào cột đích."""

    field = forms.ModelChoiceField(
        label="Định nghĩa trường", queryset=FieldDef.objects.none(),
        empty_label="— chọn trường —",
    )
    column = forms.ModelChoiceField(
        label="Ghi vào cột", queryset=ColumnDef.objects.none(), required=False,
        empty_label="— chưa nối cột —",
        help_text="Trường chưa nối cột thì chỉ hiện trên biểu mẫu, không lưu vào bảng.",
    )
    required = forms.BooleanField(label="Bắt buộc nhập", required=False)

    def __init__(self, *args, form_def=None, instance=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_def = form_def
        self.instance = instance

        da_dung = set(
            form_def.fields.exclude(pk=getattr(instance, "pk", None))
            .values_list("field_id", flat=True)
        )
        self.fields["field"].queryset = FieldDef.objects.filter(
            department=form_def.department,
        ).exclude(pk__in=da_dung)

        # Cột tính sẵn không nhận dữ liệu nhập tay nên không cho chọn
        self.fields["column"].queryset = ColumnDef.objects.filter(
            table=form_def.table, is_computed=False,
        ).order_by("order", "id")

        if instance is not None:
            self.fields["field"].disabled = True
            self.initial.setdefault("field", instance.field_id)
            self.initial.setdefault("required", instance.required)
            lien_ket = getattr(instance, "link", None)
            self.initial.setdefault("column", getattr(lien_ket, "column_id", None))

    def clean(self):
        """Kiểm khớp kiểu ngay ở biểu mẫu để lỗi hiện đúng chỗ — AC-8.6."""
        du_lieu = super().clean()
        truong, cot = du_lieu.get("field"), du_lieu.get("column")
        if truong is not None and cot is not None:
            cau = link_service.check(truong, cot)
            if cau:
                self.add_error("column", cau)
        return du_lieu


class GrantForm(forms.Form):
    """Cấp quyền riêng cho một người hoặc một team — FR-8.4."""

    user = forms.ModelChoiceField(
        label="Cấp cho người", queryset=None, required=False,
        empty_label="— không chọn —",
    )
    team = forms.ModelChoiceField(
        label="Hoặc cả team", queryset=None, required=False,
        empty_label="— không chọn —",
    )
    action = forms.ChoiceField(label="Được làm gì", choices=())

    def __init__(self, *args, cho_bang=True, **kwargs):
        super().__init__(*args, **kwargs)
        from django.contrib.auth import get_user_model
        from org.models import Team

        self.fields["user"].queryset = get_user_model().objects.filter(
            is_active=True).order_by("username")
        self.fields["team"].queryset = Team.objects.all()
        self.fields["action"].choices = (
            [(GrantAction.VIEW, GrantAction.VIEW.label),
             (GrantAction.EDIT, GrantAction.EDIT.label)]
            if cho_bang else
            [(GrantAction.FILL, GrantAction.FILL.label)]
        )

    def clean(self):
        du_lieu = super().clean()
        nguoi, team = du_lieu.get("user"), du_lieu.get("team")
        if bool(nguoi) == bool(team):
            raise forms.ValidationError(
                "Chọn đúng một bên: một người, hoặc một team."
            )
        return du_lieu
