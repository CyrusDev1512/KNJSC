"""Biểu mẫu và bảng do người dùng tự tạo.

Đây là phần rủi ro nhất của dự án — nếu mô hình sai thì mọi thứ sau phải làm
lại. Ba quyết định định hình nó:

- **ADR-001** — bảng do người dùng tạo không sinh bảng vật lý. Dữ liệu lưu
  dạng khoá–giá trị trong JSON, cộng thêm cột tách có chỉ mục cho những cột
  mang nhãn ý nghĩa.
- **ADR-006** — bảng dữ liệu chỉ có cột tính sẵn. Công thức thuộc về **cột**,
  áp cho mọi dòng, không thuộc về ô. Nhờ vậy sắp xếp hay lọc không làm sai.
- **ADR-007** — biểu mẫu luôn ghi vào bảng có sẵn, không tự sinh bảng mới.
"""
from decimal import Decimal, DivisionByZero, InvalidOperation

from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.core.exceptions import ValidationError
from django.db import models

from core.models import ScopedModel, SoftDeleteModel, TimestampedModel
from core.money import MONEY_DECIMAL_PLACES, MONEY_MAX_DIGITS

from .managers import (
    AllDataRecordManager, AllFormDefManager, AllTableDefManager,
    DataRecordManager, FormDefManager, TableDefManager,
)
from .meaning import COLUMN_OF, FieldType, Meaning, allows, type_fits

CODE_HELP = "Tên kỹ thuật, tiếng Anh, dùng làm khoá trong cơ sở dữ liệu."


class ComputeOp(models.TextChoices):
    """Phép tính cho cột tính sẵn.

    Danh sách đóng, không cho gõ cú pháp tự do (ADR-006). Bảy công thức trong
    tệp thật của công ty đều là phép chia giữa hai cột.
    """

    ADD = "add", "Cộng — A + B"
    SUBTRACT = "subtract", "Trừ — A − B"
    MULTIPLY = "multiply", "Nhân — A × B"
    DIVIDE = "divide", "Chia — A ÷ B"
    PERCENT = "percent", "Phần trăm — A ÷ B × 100"


# ══ ĐỊNH NGHĨA BẢNG ═══════════════════════════════════════════════

class TableDef(ScopedModel):
    """Một bảng do người dùng tạo.

    Không sinh bảng vật lý; nó chỉ là định nghĩa. Dữ liệu nằm ở `DataRecord`.
    """

    SCOPE_OWNER_FIELD = "created_by"
    SCOPE_TEAM_FIELD = None          # bảng thuộc về bộ phận, không thuộc team
    SCOPE_DEPARTMENT_FIELD = "department"

    # Định nghĩa bảng thì cả bộ phận nhìn thấy; phạm vi theo cấp bậc áp ở
    # `DataRecord`, nơi có dữ liệu thật. Lý do đầy đủ ở forms_builder/managers.py
    objects = TableDefManager()
    all_objects = AllTableDefManager()

    name = models.CharField("Tên bảng", max_length=120)
    code = models.SlugField("Tên kỹ thuật", max_length=60, unique=True, help_text=CODE_HELP)
    description = models.CharField("Mô tả", max_length=300, blank=True)
    department = models.ForeignKey(
        "org.Department", verbose_name="Bộ phận sở hữu",
        on_delete=models.PROTECT, related_name="tables", db_index=True,
    )
    is_active = models.BooleanField("Đang dùng", default=True, db_index=True)
    is_shared = models.BooleanField(
        "Bảng dùng chung", default=False, db_index=True,
        help_text=(
            "Mọi người trong bộ phận sở hữu thấy mọi dòng, không phân biệt cấp bậc. "
            "Dùng cho bảng là hàng đợi việc chung như bảng vận đơn. "
            "Bảng báo cáo thì để tắt, giữ phạm vi theo cấp bậc."
        ),
    )

    class Meta:
        verbose_name = "Bảng dữ liệu"
        verbose_name_plural = "Bảng dữ liệu"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def data_columns(self):
        """Cột nhập tay, theo đúng thứ tự hiển thị."""
        return self.columns.filter(is_computed=False).order_by("order", "id")

    def computed_columns(self):
        """Cột tính sẵn, theo đúng thứ tự hiển thị."""
        return self.columns.filter(is_computed=True).order_by("order", "id")


class ColumnDef(TimestampedModel):
    """Một cột trong bảng.

    Cột thường thì người dùng nhập. Cột tính sẵn thì hệ thống tính từ hai cột
    khác — công thức lưu dạng cấu trúc, không lưu chuỗi.
    """

    table = models.ForeignKey(
        TableDef, verbose_name="Bảng", on_delete=models.CASCADE,
        related_name="columns", db_index=True,
    )
    name = models.CharField("Nhãn hiển thị", max_length=120)
    code = models.SlugField("Tên kỹ thuật", max_length=60, help_text=CODE_HELP)
    field_type = models.CharField(
        "Kiểu dữ liệu", max_length=20, choices=FieldType.choices, default=FieldType.TEXT,
    )
    meaning = models.CharField(
        "Nhãn ý nghĩa", max_length=20, choices=Meaning.choices, blank=True, db_index=True,
        help_text="Cột có nhãn được tách ra cột riêng có chỉ mục, và vào được báo cáo tổng hợp.",
    )
    required = models.BooleanField("Bắt buộc nhập", default=False)
    order = models.PositiveSmallIntegerField("Thứ tự", default=0)

    # ── Cột tính sẵn — ADR-006 ──
    is_computed = models.BooleanField("Là cột tính sẵn", default=False)
    compute_op = models.CharField(
        "Phép tính", max_length=12, choices=ComputeOp.choices, blank=True,
    )
    compute_left = models.SlugField("Toán hạng A", max_length=60, blank=True)
    compute_right = models.SlugField("Toán hạng B", max_length=60, blank=True)
    compute_decimals = models.PositiveSmallIntegerField("Số chữ số thập phân", default=2)

    class Meta:
        verbose_name = "Cột"
        verbose_name_plural = "Cột"
        ordering = ["table", "order", "id"]
        constraints = [
            models.UniqueConstraint(fields=["table", "code"], name="column_code_unique_per_table"),
            # Mỗi nhãn ý nghĩa chỉ được gán cho một cột trong mỗi bảng. Hai cột
            # cùng mang nhãn Doanh thu thì `sync_indexed_columns` ghi đè lẫn
            # nhau và số liệu mất âm thầm — xem meaning.UNIQUE_PER_TABLE
            models.UniqueConstraint(
                fields=["table", "meaning"], name="column_meaning_unique_per_table",
                condition=~models.Q(meaning=""),
            ),
        ]

    def __str__(self):
        return f"{self.name}"

    @property
    def storage_column(self):
        """Cột vật lý trên `DataRecord`, hoặc None nếu giá trị nằm trong JSON."""
        return COLUMN_OF.get(self.meaning) if self.meaning else None

    def clean(self):
        """Chặn những cấu hình không chạy được, ngay lúc lưu định nghĩa."""
        loi = {}

        if self.meaning and not allows(self.meaning, self.field_type):
            loi["meaning"] = ValidationError(
                "Nhãn %(nhan)s không nhận kiểu dữ liệu %(kieu)s.",
                params={
                    "nhan": Meaning(self.meaning).label,
                    "kieu": FieldType(self.field_type).label,
                },
            )

        if self.meaning:
            trung = (
                ColumnDef.objects.filter(table_id=self.table_id, meaning=self.meaning)
                .exclude(pk=self.pk)
                .first()
            )
            if trung is not None:
                loi["meaning"] = ValidationError(
                    'Nhãn %(nhan)s đã gán cho cột "%(cot)s" trong bảng này.',
                    params={"nhan": Meaning(self.meaning).label, "cot": trung.name},
                )

        if self.is_computed:
            if not self.compute_op:
                loi["compute_op"] = ValidationError("Cột tính sẵn phải chọn phép tính.")
            if not self.compute_left or not self.compute_right:
                loi["compute_left"] = ValidationError("Cột tính sẵn phải chọn đủ hai toán hạng.")
            if self.compute_left and self.compute_left == self.compute_right:
                loi["compute_right"] = ValidationError("Hai toán hạng phải là hai cột khác nhau.")
            if self.compute_left == self.code or self.compute_right == self.code:
                loi["compute_left"] = ValidationError("Cột không tính được từ chính nó.")
            if self.required:
                loi["required"] = ValidationError(
                    "Cột tính sẵn không nhập tay được nên không đánh dấu bắt buộc."
                )
        elif self.compute_op or self.compute_left or self.compute_right:
            loi["is_computed"] = ValidationError(
                "Đã điền công thức thì phải đánh dấu là cột tính sẵn."
            )

        if loi:
            raise ValidationError(loi)

    def compute(self, values):
        """Tính giá trị của cột này từ một dòng dữ liệu.

        `values` là dict tên kỹ thuật sang giá trị. Thiếu toán hạng hoặc chia
        cho không thì trả None — để trống rõ ràng hơn là hiện số sai.
        """
        if not self.is_computed:
            return None
        a, b = _to_decimal(values.get(self.compute_left)), _to_decimal(values.get(self.compute_right))
        if a is None or b is None:
            return None
        try:
            if self.compute_op == ComputeOp.ADD:
                kq = a + b
            elif self.compute_op == ComputeOp.SUBTRACT:
                kq = a - b
            elif self.compute_op == ComputeOp.MULTIPLY:
                kq = a * b
            elif self.compute_op == ComputeOp.DIVIDE:
                kq = a / b
            elif self.compute_op == ComputeOp.PERCENT:
                kq = a / b * 100
            else:
                return None
        except (DivisionByZero, InvalidOperation, ZeroDivisionError):
            return None
        return kq.quantize(Decimal(1).scaleb(-self.compute_decimals))


def _to_decimal(gia_tri):
    """Đổi một giá trị bất kỳ sang Decimal. Không đổi được thì trả None."""
    if gia_tri is None or gia_tri == "":
        return None
    try:
        return Decimal(str(gia_tri))
    except (InvalidOperation, TypeError, ValueError):
        return None


# ══ BẢN GHI ═══════════════════════════════════════════════════════

class DataRecord(ScopedModel):
    """Một dòng trong bảng do người dùng tạo.

    Giá trị nằm ở hai chỗ:

    - `data` — JSON, chứa **mọi** cột, kể cả cột có nhãn. Đây là nguồn đầy đủ.
    - `val_*` — bản sao của những cột mang nhãn ý nghĩa, để lọc và thống kê
      nhanh. Bảy cột này có chỉ mục; JSON thì có chỉ mục GIN.

    Ghi hai chỗ là cố ý (ADR-001): JSON đủ linh hoạt, cột tách đủ nhanh.
    `sync_indexed_columns()` giữ hai bên khớp nhau.
    """

    SCOPE_OWNER_FIELD = "created_by"
    SCOPE_TEAM_FIELD = "team"
    SCOPE_DEPARTMENT_FIELD = "department"

    # Phạm vi theo cấp bậc như mọi model khác, cộng thêm bảng được cấp quyền
    # riêng — xem forms_builder/managers.py
    objects = DataRecordManager()
    all_objects = AllDataRecordManager()

    table = models.ForeignKey(
        TableDef, verbose_name="Bảng", on_delete=models.PROTECT,
        related_name="records", db_index=True,
    )
    data = models.JSONField("Dữ liệu", default=dict, blank=True)

    department = models.ForeignKey(
        "org.Department", verbose_name="Bộ phận",
        null=True, blank=True, on_delete=models.PROTECT,
        related_name="+", db_index=True,
    )
    team = models.ForeignKey(
        "org.Team", verbose_name="Team",
        null=True, blank=True, on_delete=models.SET_NULL,
        related_name="+", db_index=True,
    )

    # ── Bảy cột tách, ứng với bảy nhãn ý nghĩa ──
    val_date = models.DateField("Ngày", null=True, blank=True, db_index=True)
    val_customer = models.CharField("Khách hàng", max_length=200, blank=True, db_index=True)
    val_phone = models.CharField("Số điện thoại", max_length=40, blank=True, db_index=True)
    val_revenue = models.DecimalField(
        "Doanh thu", max_digits=MONEY_MAX_DIGITS, decimal_places=MONEY_DECIMAL_PLACES,
        null=True, blank=True, db_index=True,
    )
    val_seller = models.CharField("Người bán", max_length=200, blank=True, db_index=True)
    val_product = models.CharField("Sản phẩm", max_length=200, blank=True, db_index=True)
    val_status = models.CharField("Trạng thái", max_length=100, blank=True, db_index=True)

    class Meta:
        verbose_name = "Bản ghi"
        verbose_name_plural = "Bản ghi"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["table", "-created_at"], name="record_table_time_idx"),
            models.Index(fields=["table", "val_date"], name="record_table_date_idx"),
            # Cột JSON dùng để lọc phải có chỉ mục GIN — quy tắc 12
            GinIndex(fields=["data"], name="record_data_gin"),
        ]

    def __str__(self):
        return f"{self.table.code} #{self.pk}"

    # ── Cột tính sẵn ──
    def apply_computed_columns(self, columns=None):
        """Tính lại mọi cột tính sẵn và ghi kết quả vào `data`.

        Lưu kết quả chứ không tính lúc hiển thị, vì có lưu thì mới sắp xếp và
        lọc theo cột đó được ở tầng cơ sở dữ liệu. Đổi công thức thì phải
        tính lại cả bảng — việc đó chạy nền.
        """
        columns = columns if columns is not None else list(self.table.columns.all())
        for cot in columns:
            if not cot.is_computed:
                continue
            kq = cot.compute(self.data)
            self.data[cot.code] = None if kq is None else str(kq)
        return self

    # ── Giữ JSON và cột tách khớp nhau ──
    def sync_indexed_columns(self, columns=None):
        """Chép giá trị của cột mang nhãn từ JSON sang cột tách.

        Gọi trước mỗi lần lưu. Không gọi thì lọc và thống kê sẽ ra sai, mà
        màn hình vẫn hiện đúng — kiểu lỗi khó phát hiện nhất.
        """
        columns = columns if columns is not None else self.table.columns.all()
        con_dung = set()
        for cot in columns:
            dich = COLUMN_OF.get(cot.meaning) if cot.meaning else None
            if not dich:
                continue
            setattr(self, dich, _normalise(self.data.get(cot.code), dich))
            con_dung.add(dich)

        # Nhãn không còn cột nào mang thì cột tách phải trả về rỗng. Bỏ bước
        # này thì gỡ cột Doanh thu xong, val_revenue vẫn giữ số cũ và báo cáo
        # tổng hợp vẫn cộng nó vào
        for dich in COLUMN_OF.values():
            if dich not in con_dung:
                setattr(self, dich, _normalise(None, dich))
        return self

    def save(self, *args, **kwargs):
        if self.table_id and not kwargs.pop("skip_sync", False):
            # Thứ tự bắt buộc: tính cột tính sẵn trước, rồi mới chép sang cột
            # tách — cột tính sẵn cũng mang nhãn ý nghĩa được
            cot = list(self.table.columns.all())
            self.apply_computed_columns(cot)
            self.sync_indexed_columns(cot)
        return super().save(*args, **kwargs)


def _normalise(gia_tri, cot_dich):
    """Đưa giá trị về đúng kiểu của cột tách."""
    if gia_tri is None or gia_tri == "":
        return None if cot_dich in ("val_date", "val_revenue") else ""
    if cot_dich == "val_revenue":
        return _to_decimal(gia_tri)
    if cot_dich == "val_date":
        return gia_tri            # Django tự phân tích chuỗi ngày dạng ISO
    return str(gia_tri)[:200]


# ══ BIỂU MẪU ══════════════════════════════════════════════════════
#
# Bốn bảng theo `docs/03` mục 2.2 và 2.3:
#
#     FieldDef  ──n:m──  FormDef  ──ghi vào──▶  TableDef
#        │                  │                       │
#        └── FormField ─────┘                       │
#                │                                  │
#                └── FormTableLink ──▶ ColumnDef ───┘
#
# Vì sao trường biểu mẫu tách khỏi cột bảng: hai bên có kiểu dữ liệu riêng, nên
# lúc nối mới có cái để kiểm khớp (FR-8.6). Nếu trường chính là cột thì kiểu
# luôn khớp sẵn và tiêu chí AC-8.6 thành vô nghĩa.


class FieldDef(TimestampedModel):
    """Một định nghĩa trường trong thư viện dùng chung.

    Dùng lại được cho nhiều biểu mẫu: "Ngày" khai một lần, mọi biểu mẫu của bộ
    phận đều lấy ra dùng, nhờ vậy tên hiển thị và kiểu dữ liệu thống nhất.
    """

    name = models.CharField("Nhãn hiển thị", max_length=120)
    code = models.SlugField("Tên kỹ thuật", max_length=60, help_text=CODE_HELP)
    field_type = models.CharField(
        "Kiểu dữ liệu", max_length=20, choices=FieldType.choices, default=FieldType.TEXT,
    )
    meaning = models.CharField(
        "Nhãn ý nghĩa", max_length=20, choices=Meaning.choices, blank=True, db_index=True,
    )
    hint = models.CharField("Câu gợi ý dưới ô nhập", max_length=200, blank=True)
    default_value = models.CharField(
        "Giá trị mặc định", max_length=200, blank=True,
        help_text="Điền sẵn vào ô khi mở biểu mẫu. Để trống nếu không có.",
    )
    department = models.ForeignKey(
        "org.Department", verbose_name="Bộ phận",
        on_delete=models.PROTECT, related_name="field_defs", db_index=True,
    )

    class Meta:
        verbose_name = "Định nghĩa trường"
        verbose_name_plural = "Định nghĩa trường"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["department", "code"], name="field_code_unique_per_department",
            ),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        """Nhãn ý nghĩa phải hợp với kiểu dữ liệu, giống hệt bên cột."""
        if self.meaning and not allows(self.meaning, self.field_type):
            raise ValidationError({"meaning": ValidationError(
                "Nhãn %(nhan)s không nhận kiểu dữ liệu %(kieu)s.",
                params={
                    "nhan": Meaning(self.meaning).label,
                    "kieu": FieldType(self.field_type).label,
                },
            )})


class FormDef(ScopedModel):
    """Một biểu mẫu nhập liệu. Luôn ghi vào một bảng có sẵn (ADR-007)."""

    SCOPE_OWNER_FIELD = "created_by"
    SCOPE_TEAM_FIELD = None          # biểu mẫu thuộc bộ phận, không thuộc team
    SCOPE_DEPARTMENT_FIELD = "department"

    # Cùng cái bẫy của TableDef: không có cột team nên `apply_scope` cho Leader
    # rơi xuống nhánh "chỉ thấy của mình". Lý do đầy đủ ở managers.py
    objects = FormDefManager()
    all_objects = AllFormDefManager()

    name = models.CharField("Tên biểu mẫu", max_length=120)
    code = models.SlugField("Tên kỹ thuật", max_length=60, unique=True, help_text=CODE_HELP)
    description = models.CharField("Mô tả", max_length=300, blank=True)
    department = models.ForeignKey(
        "org.Department", verbose_name="Bộ phận áp dụng",
        on_delete=models.PROTECT, related_name="forms", db_index=True,
    )
    table = models.ForeignKey(
        TableDef, verbose_name="Bảng đích",
        on_delete=models.PROTECT, related_name="forms", db_index=True,
    )
    is_active = models.BooleanField("Đang dùng", default=True, db_index=True)

    class Meta:
        verbose_name = "Biểu mẫu"
        verbose_name_plural = "Biểu mẫu"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def clean(self):
        """Bảng đích phải cùng bộ phận với biểu mẫu.

        Cho ghi chéo bộ phận là mở một đường vòng qua phạm vi quyền: ai điền
        được biểu mẫu là ghi được vào bảng của bộ phận khác.
        """
        if self.table_id and self.department_id and self.table.department_id != self.department_id:
            raise ValidationError({"table": ValidationError(
                "Bảng đích thuộc bộ phận %(bang)s, không cùng bộ phận với biểu mẫu.",
                params={"bang": self.table.department},
            )})

    def ordered_fields(self):
        """Các trường theo đúng thứ tự hiển thị, lấy sẵn định nghĩa và cột đích."""
        return (self.fields.select_related("field", "link", "link__column")
                .order_by("order", "id"))


class FormField(TimestampedModel):
    """Một trường nằm trong một biểu mẫu — quan hệ n:m, kèm thứ tự và cờ bắt buộc.

    FR-8.2: Manager chọn được các trường, thứ tự hiển thị và trường nào bắt buộc.
    """

    form = models.ForeignKey(
        FormDef, verbose_name="Biểu mẫu",
        on_delete=models.CASCADE, related_name="fields", db_index=True,
    )
    field = models.ForeignKey(
        FieldDef, verbose_name="Định nghĩa trường",
        on_delete=models.PROTECT, related_name="used_in", db_index=True,
    )
    order = models.PositiveSmallIntegerField("Thứ tự", default=0)
    required = models.BooleanField("Bắt buộc nhập", default=False)

    class Meta:
        verbose_name = "Trường trong biểu mẫu"
        verbose_name_plural = "Trường trong biểu mẫu"
        ordering = ["form", "order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["form", "field"], name="form_field_unique_per_form",
            ),
        ]

    def __str__(self):
        return f"{self.form.code}.{self.field.code}"


class FormTableLink(TimestampedModel):
    """Trường nào của biểu mẫu ghi vào cột nào của bảng — FR-8.3.

    Tách khỏi `FormField` theo đúng `docs/03` mục 2.2: một bên là "biểu mẫu
    trông thế nào", một bên là "dữ liệu chảy đi đâu".

    Kiểm khớp kiểu nằm ở `clean()` — đây là chỗ tiêu chí AC-8.6 kiểm.
    """

    form_field = models.OneToOneField(
        FormField, verbose_name="Trường biểu mẫu",
        on_delete=models.CASCADE, related_name="link",
    )
    column = models.ForeignKey(
        ColumnDef, verbose_name="Cột đích",
        on_delete=models.PROTECT, related_name="links", db_index=True,
    )

    class Meta:
        verbose_name = "Liên kết trường và cột"
        verbose_name_plural = "Liên kết trường và cột"

    def __str__(self):
        return f"{self.form_field} → {self.column.code}"

    def clean(self):
        """Chặn nối sai ngay lúc lưu, và nói rõ trường nào lệch."""
        if not self.form_field_id or not self.column_id:
            return

        truong = self.form_field.field
        cot = self.column
        loi = None

        if cot.table_id != self.form_field.form.table_id:
            loi = ValidationError(
                "Cột %(cot)s không thuộc bảng đích của biểu mẫu.",
                params={"cot": cot.name},
            )
        elif cot.is_computed:
            loi = ValidationError(
                "Cột %(cot)s là cột tính sẵn, không nhận dữ liệu nhập tay.",
                params={"cot": cot.name},
            )
        elif not type_fits(truong.field_type, cot.field_type):
            loi = ValidationError(
                "Trường %(truong)s kiểu %(kt)s không ghi được vào "
                "cột %(cot)s kiểu %(kc)s.",
                params={
                    "truong": truong.name, "kt": FieldType(truong.field_type).label,
                    "cot": cot.name, "kc": FieldType(cot.field_type).label,
                },
            )

        if loi is not None:
            raise ValidationError({"column": loi})


# ══ CẤP QUYỀN RIÊNG ═══════════════════════════════════════════════

class GrantAction(models.TextChoices):
    """Cấp quyền làm gì. Danh sách đóng."""

    VIEW = "view", "Xem bảng"
    FILL = "fill", "Điền biểu mẫu"
    EDIT = "edit", "Sửa dữ liệu"


class Grant(TimestampedModel, SoftDeleteModel):
    """Quyền cấp thêm cho một người hoặc một team, ngoài phạm vi cấp bậc.

    `docs/03` mục 3.4: phạm vi = phần theo cấp bậc + phần được cấp thêm.
    FR-3.4 nói rõ "trừ khi được cấp quyền riêng" — đây chính là phần đó.

    **Không đi qua `core.managers.apply_scope`.** Hàm đó chỉ biết ba đường dẫn
    người sở hữu, team và bộ phận — không có chỗ cho danh tính của thứ được
    cấp. Cấp quyền là cơ chế thứ hai, chạy song song; xem `services/grant_service.py`.
    """

    table = models.ForeignKey(
        TableDef, verbose_name="Bảng dữ liệu", null=True, blank=True,
        on_delete=models.CASCADE, related_name="grants", db_index=True,
    )
    form = models.ForeignKey(
        FormDef, verbose_name="Biểu mẫu", null=True, blank=True,
        on_delete=models.CASCADE, related_name="grants", db_index=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Cấp cho người", null=True, blank=True,
        on_delete=models.CASCADE, related_name="grants", db_index=True,
    )
    team = models.ForeignKey(
        "org.Team", verbose_name="Cấp cho team", null=True, blank=True,
        on_delete=models.CASCADE, related_name="grants", db_index=True,
    )
    action = models.CharField(
        "Được làm gì", max_length=10, choices=GrantAction.choices, db_index=True,
    )
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Người cấp", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+",
    )

    class Meta:
        verbose_name = "Quyền cấp thêm"
        verbose_name_plural = "Quyền cấp thêm"
        ordering = ["-created_at"]
        constraints = [
            # Đúng một đối tượng: hoặc bảng, hoặc biểu mẫu
            models.CheckConstraint(
                name="grant_exactly_one_target",
                condition=(
                    models.Q(table__isnull=False, form__isnull=True)
                    | models.Q(table__isnull=True, form__isnull=False)
                ),
            ),
            # Đúng một người nhận: hoặc một người, hoặc một team
            models.CheckConstraint(
                name="grant_exactly_one_holder",
                condition=(
                    models.Q(user__isnull=False, team__isnull=True)
                    | models.Q(user__isnull=True, team__isnull=False)
                ),
            ),
        ]
        indexes = [
            models.Index(fields=["user", "action"], name="grant_user_action_idx"),
            models.Index(fields=["team", "action"], name="grant_team_action_idx"),
        ]

    def __str__(self):
        doi_tuong = self.table or self.form
        nguoi = self.user or self.team
        return f"{nguoi} · {self.get_action_display()} · {doi_tuong}"

    def clean(self):
        if bool(self.table_id) == bool(self.form_id):
            raise ValidationError("Cấp quyền cho đúng một bảng hoặc một biểu mẫu.")
        if bool(self.user_id) == bool(self.team_id):
            raise ValidationError("Cấp quyền cho đúng một người hoặc một team.")
        if self.form_id and self.action != GrantAction.FILL:
            raise ValidationError({"action": "Biểu mẫu chỉ cấp được quyền điền."})
        if self.table_id and self.action == GrantAction.FILL:
            raise ValidationError({"action": "Bảng chỉ cấp được quyền xem hoặc sửa."})
