"""Cấu hình metadata; không sinh bản ghi báo cáo hoặc đơn hàng."""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from forms_builder.models import ColumnDef, FieldDef, FormDef, FormField, FormTableLink, TableDef
from orders.constants import Market
from org.models import Department
from reports.models import ReportSource

SALE_COLUMNS = (
    ("ngay", "Ngày", "date", "date"),
    ("sale", "Sale", "text", "seller"),
    ("san_pham", "Sản phẩm", "choice", "product"),
    ("so_mess", "Số Mess", "integer", ""),
    ("so_don", "Số đơn", "integer", ""),
    ("doanh_so", "Doanh số", "money", "revenue"),
    ("ngay_ra_don", "Ngày ra đơn", "date", ""),
)
SOURCES = (("bao_cao_sale", "sale"), ("bao_cao_mkt", "mkt"), ("van_don_moi", "delivery"))


def ensure_sale():
    department = Department.objects.filter(code="sale").first()
    if department is None:
        return
    table, created = TableDef.objects.get_or_create(
        code="bao_cao_sale", defaults={"name": "Báo cáo Sale", "department": department})
    if not created:
        return
    for order, (code, name, field_type, meaning) in enumerate(SALE_COLUMNS):
        ColumnDef.objects.create(table=table, code=code, name=name,
                                 field_type=field_type, meaning=meaning, order=order)
    # Sản phẩm kiểu choice/meaning=product đọc danh mục Product qua registry.
    FormDef.objects.create(table=table, department=department,
                           code="bc_sale_ngay", name="Báo cáo Sale ngày")


def configure_forms(table):
    for form in table.forms.filter(is_active=True):
        for column in table.columns.filter(is_computed=False):
            link = FormTableLink.objects.filter(form_field__form=form, column=column).first()
            if link is not None:
                if column.code in ("san_pham", "thi_truong"):
                    FormField.objects.filter(pk=link.form_field_id).update(required=True)
                continue
            field, _ = FieldDef.objects.get_or_create(
                department=table.department, code=f"erp_{table.pk}_{column.code}",
                defaults={"name": column.name, "field_type": column.field_type,
                          "meaning": column.meaning})
            form_field = FormField.objects.create(
                form=form, field=field, order=column.order,
                required=column.code in ("ngay", "san_pham", "thi_truong"))
            FormTableLink.objects.create(form_field=form_field, column=column)


def configure_source(table, kind):
    if kind == "delivery":
        mapping = {"market": "quoc_gia"}
    else:
        required = {"so_mess", "so_don", "doanh_so", "san_pham", "ngay"}
        if kind == "mkt":
            required.add("cpqc")
        missing = required - set(table.columns.values_list("code", flat=True))
        if missing:
            raise CommandError(f"{table.code}: thiếu cột {sorted(missing)}; không tự suy ánh xạ")
        market, _ = ColumnDef.objects.get_or_create(
            table=table, code="thi_truong", defaults={"name": "Thị trường",
            "field_type": "choice", "options": list(Market.labels), "order": 90})
        if market.field_type != "choice":
            raise CommandError(f"{table.code}: thi_truong phải là choice")
        mapping = {"mess": "so_mess", "orders": "so_don", "sales": "doanh_so",
                   "cost": "cpqc", "market": "thi_truong"}
        for key, name in (("revenue", "Doanh thu"), ("invoice", "Hóa đơn")):
            candidates = list(table.columns.filter(name=name, is_computed=False,
                              field_type__in=["money", "decimal", "integer"]))
            if len(candidates) > 1:
                raise CommandError(f"{table.code}: nhiều cột {name}, cần xác định nguồn riêng")
            if candidates:
                mapping[key] = candidates[0].code
        configure_forms(table)
    ReportSource.objects.update_or_create(table=table, defaults={"kind": kind, "columns": mapping})


class Command(BaseCommand):
    help = "Thiết lập nguồn Sale/Marketing/Vận đơn và trường thị trường; không ghi dữ liệu nghiệp vụ."

    @transaction.atomic
    def handle(self, *args, **options):
        ensure_sale()
        for code, kind in SOURCES:
            table = TableDef.objects.filter(code=code, is_active=True).first()
            if table is not None:
                configure_source(table, kind)
                self.stdout.write(f"Configured {code}; existing report rows unchanged")
