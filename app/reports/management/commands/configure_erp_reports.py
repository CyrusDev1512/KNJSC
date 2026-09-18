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
        if kind == 'mkt':
            configure_marketing(table)
        from orders.services.currency_service import MARKET_CURRENCIES
        currencies = [str(c) for c in MARKET_CURRENCIES.values()]
        currency, _ = ColumnDef.objects.get_or_create(table=table, code='loai_tien', defaults={
            'name':'Loại tiền', 'field_type':'choice', 'options':currencies, 'order':91})
        # Cột có sẵn (kịch bản mẫu 15.09 tạo "Đơn vị tiền" chỉ có VND) phải nhận đủ ba mã
        # tiền theo quốc gia (ADR-031), vì báo cáo ngày tự điền USD/CAD/PHP; giữ giá trị cũ
        # để dòng lịch sử vẫn hợp lệ — bổ sung, không thay thế (TL-41).
        if currency.field_type != 'choice':
            raise CommandError(f"{table.code}: loai_tien phải là choice")
        missing = [c for c in currencies if c not in (currency.options or [])]
        if missing:
            currency.options = list(currency.options or []) + missing
            currency.save(update_fields=['options'])
        market, _ = ColumnDef.objects.get_or_create(
            table=table, code="thi_truong", defaults={"name": "Thị trường",
            "field_type": "choice", "options": list(Market.labels), "order": 90})
        if market.field_type != "choice":
            raise CommandError(f"{table.code}: thi_truong phải là choice")
        mapping = {"mess": "so_mess", "orders": "so_don", "sales": "doanh_so",
                   "cost": "cpqc", "market": "thi_truong", "currency":"loai_tien"}
        for key, name in (("revenue", "Doanh thu"), ("invoice", "Hóa đơn")):
            candidates = list(table.columns.filter(name=name, is_computed=False,
                              field_type__in=["money", "decimal", "integer"]))
            if len(candidates) > 1:
                raise CommandError(f"{table.code}: nhiều cột {name}, cần xác định nguồn riêng")
            if candidates:
                mapping[key] = candidates[0].code
        configure_forms(table)
    ReportSource.objects.update_or_create(table=table, defaults={"kind": kind, "columns": mapping})


def configure_marketing(table):
    """Bổ sung mẫu đã duyệt; giữ nguyên dữ liệu lịch sử và trường nghiệp vụ phụ."""
    from forms_builder.models import ComputeOp
    for code, name in (('doanh_thu','Doanh thu'), ('hoa_don','Hóa đơn')):
        existing = table.columns.filter(name=name, is_computed=False).first()
        if existing is None:
            column, _ = ColumnDef.objects.get_or_create(table=table, code=code,
                defaults={'name':name, 'field_type':'money'})
            if column.is_computed or column.field_type not in ('money','decimal','integer'):
                raise CommandError(f'{table.code}.{code}: cấu hình không tương thích.')
    formulas = (
        ('cpo','CPO','cpqc','so_don'), ('gia_mess','Giá Mess','cpqc','so_mess'),
        ('cpqc_doanh_so','CPQC/Doanh số','cpqc','doanh_so'),
        ('hoa_don_doanh_thu','Hóa đơn/Doanh thu','gia_mess','cpo'),
        ('aov','AOV','doanh_so','so_don'))
    for order, (code, name, left, right) in enumerate(formulas, 8):
        ColumnDef.objects.update_or_create(table=table, code=code, defaults={
            'name':name, 'field_type':'decimal', 'is_computed':True,
            'compute_op':ComputeOp.DIVIDE, 'compute_left':left, 'compute_right':right,
            'compute_decimals':4, 'order':order})
    for order, code in enumerate(('ngay','marketer','so_mess','cpqc','so_don','doanh_so','doanh_thu','hoa_don')):
        table.columns.filter(code=code).update(order=order)
    # Sản phẩm, quốc gia và các trường riêng vẫn được giữ để lọc báo cáo.
    table.columns.filter(code='san_pham').update(order=80)
    table.columns.filter(code='ti_le_chot').update(order=92)
    for field in FormField.objects.filter(form__table=table).select_related('link__column'):
        if getattr(field, 'link', None):
            field.order = field.link.column.order
            field.save(update_fields=['order'])


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
