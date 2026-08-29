"""Đơn hàng, khách hàng và danh mục sản phẩm.

Đơn hàng là **bảng cố định**, bảng vận đơn là **bảng động** — chốt ở
`kien-truc.md`. Đơn chảy một chiều sang bảng vận đơn, không ghi ngược.

Ba quy tắc định hình module này:

- **BR-3** — đơn đã lưu không sửa và không xoá. Chặn ngay ở `Order.save()`,
  giống hệt cách `DailyReport` làm ở Giai đoạn 4
- **BR-8** — mọi số tiền là số thập phân chính xác, không dùng số thực
- **FR-6.7** — nhận diện khách mua lại theo số điện thoại, nên số điện thoại
  là khoá định danh của khách và bắt buộc có chỉ mục
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from core.constants import Currency
from core.models import ScopedModel, TimestampedModel
from core.money import money_field

from .constants import Market, PaymentMethod


# ══ DANH MỤC SẢN PHẨM ═════════════════════════════════════════════

class ProductGroup(TimestampedModel):
    """Nhóm sản phẩm. Danh mục dùng chung cả công ty, quản lý tự thêm."""

    name = models.CharField("Tên nhóm", max_length=120, unique=True)
    is_active = models.BooleanField("Đang dùng", default=True, db_index=True)

    class Meta:
        verbose_name = "Nhóm sản phẩm"
        verbose_name_plural = "Nhóm sản phẩm"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(TimestampedModel):
    """Một sản phẩm trong danh mục.

    Không áp phạm vi quyền: danh mục là dữ liệu tra cứu, cả ba bộ phận đều
    cần thấy. Quyền *thêm sửa* mới giới hạn ở cấp quản lý, và việc đó kiểm ở
    tầng view.
    """

    name = models.CharField("Tên sản phẩm", max_length=200)
    code = models.SlugField("Mã sản phẩm", max_length=60, unique=True)
    group = models.ForeignKey(
        ProductGroup, verbose_name="Nhóm", null=True, blank=True,
        on_delete=models.PROTECT, related_name="products", db_index=True,
    )
    unit = models.CharField("Đơn vị tính", max_length=40, default="cái")
    is_active = models.BooleanField("Đang bán", default=True, db_index=True)

    class Meta:
        verbose_name = "Sản phẩm"
        verbose_name_plural = "Sản phẩm"
        ordering = ["name"]

    def __str__(self):
        return self.name


# ══ KHÁCH HÀNG ════════════════════════════════════════════════════

class Customer(TimestampedModel):
    """Khách hàng, định danh bằng số điện thoại — FR-6.7.

    Danh sách đen (`is_blacklisted`) chốt ở backlog Q25: hệ thống **cảnh báo,
    không chặn**. Chưa có yêu cầu nào cho phép chặn lên đơn, mà chặn nhầm thì
    mất đơn thật.
    """

    phone = models.CharField("Số điện thoại", max_length=40, unique=True, db_index=True)
    name = models.CharField("Tên khách", max_length=200)
    facebook = models.CharField("Facebook", max_length=200, blank=True)
    email = models.EmailField("Email", blank=True)
    is_blacklisted = models.BooleanField("Trong danh sách đen", default=False, db_index=True)
    blacklist_reason = models.CharField("Lý do", max_length=300, blank=True)

    class Meta:
        verbose_name = "Khách hàng"
        verbose_name_plural = "Khách hàng"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} · {self.phone}"

    def order_count(self):
        """Số đơn đã mua. Dùng để báo khách mua lại — FR-6.7."""
        return self.orders.count()


# ══ ĐƠN HÀNG ══════════════════════════════════════════════════════

class Order(ScopedModel):
    """Một đơn hàng. Lưu xong là khoá — BR-3.

    Địa chỉ tách năm cấp (quốc gia, bang, thành phố, mã bưu chính, chi tiết)
    để lọc và thống kê theo thị trường được. Gộp thành một chuỗi thì không
    nhóm theo bang hay thành phố được nữa.
    """

    SCOPE_OWNER_FIELD = "created_by"
    SCOPE_TEAM_FIELD = "team"
    SCOPE_DEPARTMENT_FIELD = "department"

    code = models.SlugField("Mã đơn", max_length=30, unique=True, db_index=True)
    customer = models.ForeignKey(
        Customer, verbose_name="Khách hàng",
        on_delete=models.PROTECT, related_name="orders", db_index=True,
    )

    # ── Địa chỉ giao hàng, năm cấp ──
    market = models.CharField(
        "Quốc gia", max_length=4, choices=Market.choices,
        default=Market.US, db_index=True,
    )
    state = models.CharField("Bang", max_length=120, blank=True, db_index=True)
    city = models.CharField("Thành phố", max_length=120, blank=True)
    zipcode = models.CharField("Mã bưu chính", max_length=20, blank=True)
    address_line = models.CharField("Số nhà, đường", max_length=300, blank=True)

    # ── Thanh toán và người bán ──
    payment_method = models.CharField(
        "Phương thức thanh toán", max_length=12, choices=PaymentMethod.choices,
        default=PaymentMethod.CARD,
    )
    currency = models.CharField(
        "Loại tiền tệ", max_length=3, choices=Currency.choices, default=Currency.USD,
    )
    seller = models.ForeignKey(
        "auth.User", verbose_name="Người bán", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="orders_sold", db_index=True,
    )
    sub_unit = models.CharField("Đơn vị phụ", max_length=120, blank=True)
    note = models.CharField("Ghi chú", max_length=500, blank=True)

    total = money_field("Tổng tiền", default=Decimal("0.00"))

    department = models.ForeignKey(
        "org.Department", verbose_name="Bộ phận",
        on_delete=models.PROTECT, related_name="orders", db_index=True,
    )
    team = models.ForeignKey(
        "org.Team", verbose_name="Team", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="orders", db_index=True,
    )

    #: Dòng tương ứng trên bảng vận đơn — FR-6.4. Đây chính là "mã liên kết"
    record = models.OneToOneField(
        "forms_builder.DataRecord", verbose_name="Dòng trên bảng vận đơn",
        null=True, blank=True, on_delete=models.PROTECT, related_name="order",
    )

    class Meta:
        verbose_name = "Đơn hàng"
        verbose_name_plural = "Đơn hàng"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["department", "-created_at"], name="order_dept_time_idx"),
            models.Index(fields=["created_by", "-created_at"], name="order_owner_time_idx"),
            models.Index(fields=["market", "-created_at"], name="order_market_time_idx"),
        ]

    def __str__(self):
        return self.code

    #: Cột được phép ghi sau khi đã lưu — chỉ để nối bảng vận đơn và xoá mềm
    SAU_KHI_LUU = frozenset(
        {"record", "record_id", "total", "deleted_at", "deleted_by", "updated_at"}
    )

    def save(self, *args, **kwargs):
        """Chặn sửa ở mức đối tượng — BR-3, FR-6.6.

        Không dựa vào view nhớ kiểm. Cho ghi `record` vì đơn được lưu trước
        rồi mới nối sang bảng vận đơn, cả hai trong cùng một giao dịch.
        """
        cot = kwargs.get("update_fields")
        duoc_phep = cot is not None and set(cot) <= self.SAU_KHI_LUU
        if self.pk is not None and not duoc_phep:
            raise RuntimeError(
                "Đơn đã lưu không sửa được — BR-3. "
                "Muốn bỏ thì đánh dấu xoá qua order_service."
            )
        return super().save(*args, **kwargs)

    def recalculate_total(self):
        """Cộng lại tổng tiền từ các dòng sản phẩm.

        Cộng bằng Decimal, không qua số thực — BR-8. Cộng 1.000 dòng vẫn
        chính xác tuyệt đối.
        """
        tong = sum((d.line_total for d in self.lines.all()), Decimal("0.00"))
        self.total = tong
        return tong


class OrderLine(TimestampedModel):
    """Một dòng sản phẩm trong đơn. Một đơn nhiều dòng — FR-6.2."""

    order = models.ForeignKey(
        Order, verbose_name="Đơn hàng",
        on_delete=models.CASCADE, related_name="lines", db_index=True,
    )
    product = models.ForeignKey(
        Product, verbose_name="Sản phẩm",
        on_delete=models.PROTECT, related_name="order_lines", db_index=True,
    )
    quantity = models.PositiveIntegerField("Số lượng", default=1)
    unit_price = money_field("Đơn giá")

    class Meta:
        verbose_name = "Dòng sản phẩm"
        verbose_name_plural = "Dòng sản phẩm"
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.product} × {self.quantity}"

    def clean(self):
        if self.quantity < 1:
            raise ValidationError({"quantity": "Số lượng phải từ 1 trở lên."})
        if self.unit_price is not None and self.unit_price < 0:
            raise ValidationError({"unit_price": "Đơn giá không âm."})

    @property
    def line_total(self):
        """Thành tiền của dòng. Decimal nhân số nguyên vẫn là Decimal — BR-8."""
        return (self.unit_price or Decimal("0.00")) * self.quantity
