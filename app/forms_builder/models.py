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

from django.contrib.postgres.indexes import GinIndex
from django.core.exceptions import ValidationError
from django.db import models

from core.models import ScopedModel, TimestampedModel
from core.money import MONEY_DECIMAL_PLACES, MONEY_MAX_DIGITS

from .managers import AllTableDefManager, TableDefManager
from .meaning import COLUMN_OF, FieldType, Meaning, allows

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
