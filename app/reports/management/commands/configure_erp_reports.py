"""Cấu hình metadata; không sinh bản ghi báo cáo hoặc đơn hàng."""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q

from forms_builder.models import ColumnDef, FieldDef, FormDef, FormField, FormTableLink, TableDef
from orders.constants import Market
from org.models import Department
from reports.constants import (CUSTOMER_SEGMENT_COLUMN, CUSTOMER_SEGMENT_DEFAULTS,
                               CUSTOMER_SEGMENT_LABEL, LEGACY_REVENUE_INPUT, LEGACY_ROW_FORMULA,
                               TEAM_COLUMN_CODE, TEAM_COLUMN_LABEL)
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
SOURCES = (("bao_cao_sale", "sale"), ("bao_cao_mkt", "mkt"), ("van_don", "delivery"))


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


#: Trường bắt buộc trên biểu mẫu báo cáo Sale/MKT (chủ dự án 24.09.2026, ADR-043): Số Mess, CPQC,
#: Số đơn, Doanh số cùng Ngày, Sản phẩm, Thị trường. Sale không có `cpqc` nên tự ra ba trường số.
REQUIRED_INPUTS = ("ngay", "san_pham", "thi_truong", "so_mess", "cpqc", "so_don", "doanh_so")
#: Cột nhập cố ý KHÔNG đưa lên biểu mẫu MKT: Doanh thu nhập tay cũ (ADR-038) và Hóa đơn (ADR-043 —
#: bỏ khỏi form nhập; cột và hai cột báo cáo Hóa đơn, Hóa đơn/DS Chốt (TT) giữ cho dữ liệu cũ)
MKT_FORM_SKIP = (LEGACY_REVENUE_INPUT, "hoa_don")


def team_column(table):
    """Cột Team dạng chữ của bảng báo cáo (mã `team` hoặc nhãn "Team", không phải cột tính),
    hoặc None. Dữ liệu thật có cột này từ sheet gốc nên `configure_forms` từng tự đưa nó lên
    form thành ô gõ tay đứng cạnh dropdown Team (ADR-043 bổ sung 25.09): nay cột rời form,
    hệ thống ghi tên team của dòng vào đó khi nộp. Nhiều cột như thế thì ưu tiên mã `team`."""
    candidates = [
        column for column in table.columns.filter(is_computed=False).filter(
            Q(code__iexact=TEAM_COLUMN_CODE) | Q(name__iexact=TEAM_COLUMN_LABEL))
        if column.field_type in ("text", "long_text", "choice")
    ]
    candidates.sort(key=lambda column: (column.code.lower() != TEAM_COLUMN_CODE, column.order, column.pk))
    return candidates[0] if candidates else None


def configure_forms(table, skip=()):
    """Mọi cột nhập của bảng có trường trên biểu mẫu; `skip` là cột cố ý không đưa lên
    biểu mẫu (Doanh thu nhập tay cũ — ADR-038, Hóa đơn và cột Team dạng chữ — ADR-043),
    gỡ luôn trường đã có.
    Trường trong `REQUIRED_INPUTS` luôn bắt buộc, kể cả trường đã có từ trước."""
    if skip:
        FormField.objects.filter(form__table=table, link__column__code__in=list(skip)).delete()
    for form in table.forms.filter(is_active=True):
        for column in table.columns.filter(is_computed=False).exclude(code__in=list(skip)):
            link = FormTableLink.objects.filter(form_field__form=form, column=column).first()
            if link is not None:
                if column.code in REQUIRED_INPUTS:
                    FormField.objects.filter(pk=link.form_field_id).update(required=True)
                continue
            field, _ = FieldDef.objects.get_or_create(
                department=table.department, code=f"erp_{table.pk}_{column.code}",
                defaults={"name": column.name, "field_type": column.field_type,
                          "meaning": column.meaning})
            form_field = FormField.objects.create(
                form=form, field=field, order=column.order,
                required=column.code in REQUIRED_INPUTS)
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
        # Cột có sẵn (kịch bản mẫu 15.09 tạo "Đơn vị tiền" chỉ có VND) phải nhận đủ mã tiền
        # theo quốc gia (ADR-031), vì báo cáo ngày tự điền theo Quốc gia; giữ giá trị cũ để
        # dòng lịch sử vẫn hợp lệ — bổ sung, không thay thế (TL-41). Thị trường cũng vậy:
        # bảng cấu hình trước 18.09 chỉ có ba nước, phải nhận thêm bốn (ADR-031 bổ sung).
        _ensure_options(table, currency, currencies)
        market, _ = ColumnDef.objects.get_or_create(
            table=table, code="thi_truong", defaults={"name": "Thị trường",
            "field_type": "choice", "options": list(Market.labels), "order": 90})
        _ensure_options(table, market, list(Market.labels))
        mapping = {"mess": "so_mess", "orders": "so_don", "sales": "doanh_so",
                   "cost": "cpqc", "market": "thi_truong", "currency":"loai_tien"}
        # Marketing: Doanh thu suy ra từ vận đơn (ADR-038), không ánh xạ cột nhập tay
        keys = (("invoice", "Hóa đơn"),) if kind == "mkt" else (("revenue", "Doanh thu"), ("invoice", "Hóa đơn"))
        for key, name in keys:
            candidates = list(table.columns.filter(name=name, is_computed=False,
                              field_type__in=["money", "decimal", "integer"]))
            if len(candidates) > 1:
                raise CommandError(f"{table.code}: nhiều cột {name}, cần xác định nguồn riêng")
            if candidates:
                mapping[key] = candidates[0].code
        if kind == "mkt":
            mapping["segment"] = CUSTOMER_SEGMENT_COLUMN
        skip = set(MKT_FORM_SKIP) if kind == "mkt" else set()
        team = team_column(table)
        if team is not None:
            # Một ô Team duy nhất trên form (dropdown, ADR-043): cột Team dạng chữ rời form nhập;
            # `record_service.create_record` ghi tên team của dòng vào nó theo ánh xạ này
            mapping["team"] = team.code
            skip.add(team.code)
        configure_forms(table, skip=skip)
    ReportSource.objects.update_or_create(table=table, defaults={"kind": kind, "columns": mapping})


def _ensure_options(table, column, wanted):
    """Cột Chọn một nhận đủ các giá trị `wanted`, giữ giá trị cũ; chạy lại không đổi."""
    if column.field_type != "choice":
        raise CommandError(f"{table.code}: {column.code} phải là choice")
    missing = [value for value in wanted if value not in (column.options or [])]
    if missing:
        column.options = list(column.options or []) + missing
        column.save(update_fields=["options"])


def configure_marketing(table):
    """Bổ sung mẫu đã duyệt (ADR-032, ADR-038); giữ nguyên dữ liệu lịch sử và trường nghiệp vụ phụ.

    Doanh thu không còn là cột nhập: suy ra từ vận đơn ở mức báo cáo, nên cột tính từng
    dòng Hóa đơn/Doanh thu cũng bỏ (không tính được từ một dòng). Cột nhập cũ `doanh_thu`
    giữ để đọc báo cáo lịch sử. Thêm cột Tệp khách hàng (Chọn một) với danh sách mặc định.
    """
    from forms_builder.models import ComputeOp
    existing = table.columns.filter(name='Hóa đơn', is_computed=False).first()
    if existing is None:
        column, _ = ColumnDef.objects.get_or_create(table=table, code='hoa_don',
            defaults={'name':'Hóa đơn', 'field_type':'money'})
        if column.is_computed or column.field_type not in ('money','decimal','integer'):
            raise CommandError(f'{table.code}.hoa_don: cấu hình không tương thích.')
    segment, _ = ColumnDef.objects.get_or_create(table=table, code=CUSTOMER_SEGMENT_COLUMN,
        defaults={'name': CUSTOMER_SEGMENT_LABEL, 'field_type': 'choice',
                  'options': list(CUSTOMER_SEGMENT_DEFAULTS), 'order': 81})
    _ensure_options(table, segment, list(CUSTOMER_SEGMENT_DEFAULTS))
    formulas = (
        ('cpo','CPO','cpqc','so_don'), ('gia_mess','Giá Mess','cpqc','so_mess'),
        ('cpqc_doanh_so','CPQC/Doanh số','cpqc','doanh_so'),
        ('aov','AOV','doanh_so','so_don'))
    for order, (code, name, left, right) in enumerate(formulas, 8):
        ColumnDef.objects.update_or_create(table=table, code=code, defaults={
            'name':name, 'field_type':'decimal', 'is_computed':True,
            'compute_op':ComputeOp.DIVIDE, 'compute_left':left, 'compute_right':right,
            'compute_decimals':4, 'order':order})
    # Cột tính từng dòng cũ: bỏ định nghĩa, giá trị đã ghi trong JSON không đụng (BR-4)
    table.columns.filter(code=LEGACY_ROW_FORMULA, is_computed=True).delete()
    for order, code in enumerate(('ngay','marketer','so_mess','cpqc','so_don','doanh_so','hoa_don')):
        table.columns.filter(code=code).update(order=order)
    # Sản phẩm, tệp khách hàng, quốc gia và các trường riêng vẫn được giữ để lọc báo cáo.
    table.columns.filter(code='san_pham').update(order=80)
    table.columns.filter(code=CUSTOMER_SEGMENT_COLUMN).update(order=81)
    table.columns.filter(code=LEGACY_REVENUE_INPUT).update(order=93)
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
