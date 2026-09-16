"""Quy tắc nộp báo cáo hằng ngày.

Tầng dịch vụ, không biết gì về HTTP (điều cấm 2). Mọi thao tác ghi nhật ký
(BR-5) và nằm trong một giao dịch.

Quyết định 16/09/2026 thay thế khóa tuyệt đối: nhân viên không sửa sau khi
nộp; Leader/Manager/Admin sửa qua amend, kiểm phạm vi và ghi lịch sử.
Ngày, chủ sở hữu và thời điểm nộp của DailyReport vẫn bất biến.
"""
from django.db import IntegrityError, transaction

from core.audit import record
from core.constants import AuditAction
from core.exceptions import BusinessError
from forms_builder.services import form_service, grant_service

from ..models import DailyReport


def protected_values(form, values, fields, day, owner, *, original=None):
    """Ngày/danh tính do server quản lý; sửa giữ danh tính tại lúc nộp."""
    from forms_builder.meaning import Meaning
    from orders.services.currency_service import for_label
    values = form_service.apply_identity(values, fields, owner)
    source = getattr(form.table, 'erp_report', None)
    market = None
    for field in fields:
        column = form_service._cot_dich(field)
        if column is None:
            continue
        if column.meaning == Meaning.DATE:
            values[field.field.code] = day.isoformat()
        if original is not None and form_service.is_identity_field(field):
            values[field.field.code] = original.get(column.code, values[field.field.code])
        if source and source.kind in ('sale', 'mkt') and column.code == source.columns.get('market'):
            market = values.get(field.field.code)
    if source and source.kind in ('sale', 'mkt'):
        currency = for_label(market)
        for field in fields:
            column = form_service._cot_dich(field)
            if column and column.code == source.columns.get('currency', 'loai_tien'):
                values[field.field.code] = currency
    return values


def submit_current(form, values, *, actor, request=None, fields=None):
    """Đường nộp tương tác; submit ngày chỉ định dành cho nhập lịch sử nội bộ."""
    from django.utils import timezone
    fields = fields if fields is not None else list(form.ordered_fields())
    day = timezone.localdate()
    values = protected_values(form, values, fields, day, actor)
    return submit(form, values, report_date=day, actor=actor, request=request, fields=fields)


def can_amend(user, report):
    from core.constants import Rank
    from core.scope import get_user_scope
    if not user.is_active:
        return False
    scope = get_user_scope(user)
    return (scope.is_admin or
            scope.rank == Rank.MANAGER and report.department_id in scope.department_ids or
            scope.rank == Rank.LEADER and report.team_id in scope.team_ids)


def report_widgets(form, fields, values, *, user, day, owner=None):
    widgets = form_service.widgets(form, fields, values, user=user)
    return decorate_widgets(widgets, form, values, user=user, day=day, owner=owner)


def decorate_widgets(widgets, form, values, *, user, day, owner=None):
    from forms_builder.meaning import Meaning
    from core.identity import employee_code
    source = getattr(form.table, 'erp_report', None)
    for widget in widgets:
        if widget.danh_tinh:
            widget.ten_nguoi_dung = employee_code(owner or user)
        if widget.cot and widget.cot.meaning == Meaning.DATE:
            widget.system_value = day.strftime('%d/%m/%Y')
            widget.report_date = True
        if source and source.kind in ('sale', 'mkt') and widget.cot:
            if widget.cot.code == source.columns.get('market'):
                widget.report_market = True
                from orders.services.currency_service import MARKET_CURRENCIES
                widget.currency_map = {market.label:str(currency) for market, currency in MARKET_CURRENCIES.items()}
                widget.cac_muc = [(label, label) for label in widget.currency_map]
                widget.chat, widget.co_them = True, False
            if widget.cot.code == source.columns.get('currency', 'loai_tien'):
                widget.system_value = values.get(widget.t.field.code) or 'Chọn quốc gia'
                widget.report_currency = True
    return widgets


class ReportConflict(BusinessError):
    pass


@transaction.atomic
def amend(report, values, *, version, actor, request=None):
    """Khóa dòng + so phiên bản; giữ chủ sở hữu, ngày và thời điểm nộp gốc."""
    from copy import deepcopy
    from decimal import Decimal
    from core.exceptions import OutOfScopeError
    from forms_builder.models import DataRecord
    from forms_builder.services import record_service, lifecycle_service
    from ..models import ReportRevision
    lifecycle_service.lock(report.form.table)
    current = DailyReport.objects.select_for_update().filter(pk=report.pk).first()
    if current is None or not can_amend(actor, current):
        raise OutOfScopeError()
    row = DataRecord.objects.select_for_update().get(pk=current.record_id)
    if str(version) != row.updated_at.isoformat():
        raise ReportConflict('Báo cáo vừa được người khác sửa. Mở lại bản mới để đối chiếu; nội dung bạn đang nhập vẫn được giữ.')
    fields = list(report.form.ordered_fields())
    # Giá trị không có trong form gửi lên giữ nguyên; không làm rỗng trường cũ.
    merged = {f.field.code: row.data.get(f.link.column.code) for f in fields if getattr(f, 'link', None)}
    for field in fields:
        if field.field.field_type in ('money', 'decimal') and merged.get(field.field.code) not in (None, ''):
            merged[field.field.code] = Decimal(str(merged[field.field.code]))
    merged.update(values)
    merged = protected_values(report.form, merged, fields, current.report_date, current.created_by, original=row.data)
    missing = form_service.missing_required(report.form, merged, fields)
    if missing:
        raise BusinessError('Chưa điền các trường bắt buộc: ' + ', '.join(missing))
    before = deepcopy(row.data)
    columns = list(report.form.table.columns.all())
    mapped = form_service.values_by_column(report.form, merged, fields)
    for column in columns:
        if column.code in mapped and not column.is_computed:
            row.data[column.code] = record_service.parse_value(column, mapped[column.code])
    compute_report(row, report.form.table, columns)
    row.sync_indexed_columns(columns)
    if row.data != before:
        row.save(skip_sync=True)
        ReportRevision.objects.create(report=current, actor=actor, before=before, after=row.data)
        record(AuditAction.UPDATE, actor=actor, target=current,
               detail='Sửa nội dung báo cáo; giữ nguyên người nộp và ngày báo cáo.', request=request)
    return current


def forms_for(user):
    """Các biểu mẫu người này nộp báo cáo được — FR-4.1.

    Chính là biểu mẫu trong phạm vi quyền của họ, đang dùng. Bộ phận nào thấy
    biểu mẫu bộ phận đó; không phải viết lại điều kiện lọc ở đây (quy tắc 11).
    """
    from forms_builder.models import FormDef

    return (FormDef.objects.in_scope(user)
            .filter(is_active=True)
            .select_related("department", "table", "table__erp_report")
            .order_by("name"))


def already_submitted(form, user, report_date):
    """Người này đã nộp biểu mẫu đó cho ngày đó chưa."""
    return DailyReport.objects.filter(
        form=form, created_by=user, report_date=report_date,
    ).exists()


@transaction.atomic
def submit(form, values, *, report_date, actor, request=None, fields=None):
    """Nộp một báo cáo. Ghi dữ liệu vào bảng đích rồi khoá lại.

    `values` là dict `{tên trường biểu mẫu: giá trị}`, đúng như màn hình điền
    biểu mẫu ở Giai đoạn 3.
    """
    if not grant_service.can_fill(actor, form):
        raise BusinessError("Bạn không được phân quyền nộp biểu mẫu này.")
    if not form.is_active:
        raise BusinessError("Biểu mẫu này đã ngừng dùng.")

    source = getattr(form.table, "erp_report", None)
    if source is not None and source.kind in ("sale", "mkt"):
        from forms_builder.meaning import Meaning
        from orders.constants import Market

        fields = fields if fields is not None else list(form.ordered_fields())
        linked = {f.link.column.code: (f, values.get(f.field.code, ""))
                  for f in fields if getattr(f, "link", None)}
        selected = linked.get(source.columns["market"])
        if selected is None or selected[1] not in Market.labels:
            raise BusinessError("Hãy chọn thị trường trong danh mục quốc gia.")
        for field, value in linked.values():
            if field.link.column.meaning == Meaning.DATE and str(value) != report_date.isoformat():
                raise BusinessError("Ngày trong biểu mẫu phải trùng ngày báo cáo; Ngày ra đơn là thông tin riêng.")

    # Cùng một đường với màn hình điền biểu mẫu: ép danh tính người nộp vào
    # trường Người bán (FR-4.6), kiểm bắt buộc, rồi ghi vào bảng đích
    ban_ghi = form_service.fill(
        form, values, actor=actor, request=request, fields=fields, system_day=report_date,
    )
    columns = list(form.table.columns.all())
    old_data = dict(ban_ghi.data)
    compute_report(ban_ghi, form.table, columns)
    if old_data != ban_ghi.data:
        ban_ghi.save(skip_sync=True)

    ho_so = getattr(actor, "profile", None)
    bao_cao = DailyReport(
        form=form, record=ban_ghi, report_date=report_date, created_by=actor,
        department=getattr(ho_so, "department", None) or form.department,
        team=getattr(ho_so, "team", None),
    )
    try:
        bao_cao.save()
    except IntegrityError:
        # Ràng buộc duy nhất trong cơ sở dữ liệu là chỗ chặn cuối của BR-2
        raise BusinessError(
            f"Bạn đã nộp biểu mẫu này cho ngày {report_date:%d.%m.%Y} rồi."
        )

    record(
        AuditAction.CREATE, actor=actor, target=bao_cao,
        detail=f"Nộp báo cáo {form.code} cho ngày {report_date:%d.%m.%Y}",
        request=request,
    )
    return bao_cao


@transaction.atomic
def withdraw(bao_cao, *, actor=None, request=None):
    """Bỏ một báo cáo đã nộp. Đánh dấu xoá, không xoá cứng (BR-4).

    Không phải "sửa" — nội dung cũ giữ nguyên trong nhật ký và trong cơ sở dữ
    liệu. Nộp lại là một bản ghi mới, có thời điểm nộp mới.
    """
    mo_ta = str(bao_cao)
    bao_cao.delete(by=actor)
    bao_cao.record.delete(by=actor)
    record(
        AuditAction.DELETE, actor=actor, target=bao_cao,
        detail=f"Bỏ báo cáo đã nộp — {mo_ta}", request=request,
    )
    return bao_cao


def history(user):
    """Báo cáo trong phạm vi quyền của người này — FR-4.3, FR-4.5.

    Nhân viên thấy báo cáo của mình, trưởng nhóm thấy cả team, quản lý thấy cả
    bộ phận. Phạm vi do `ScopedManager` lo, không viết điều kiện ở đây.
    """
    return (DailyReport.objects.in_scope(user)
            .select_related("form", "form__table", "form__table__erp_report", "record", "created_by", "created_by__profile", "department", "team"))


def read_report(bao_cao):
    """Đọc nội dung một báo cáo ra dạng `[(cột, giá trị), ...]` để hiển thị.

    Đọc theo **cột của bảng đích**, không theo trường biểu mẫu — nhờ vậy cột
    tính sẵn như CPO hay tỉ lệ chốt cũng hiện ra, dù người nộp không gõ chúng.
    """
    from forms_builder.query import read_row

    cot = list(bao_cao.form.table.columns.order_by("order", "id"))
    return read_row(bao_cao.record, cot)


def read_report_cells(bao_cao):
    """Như `read_report` nhưng kèm lớp CSS từng ô — màu cột và ngưỡng cảnh báo
    của bảng đích hiện cả ở màn hình xem báo cáo (FR-8.8)."""
    from forms_builder import styling

    cot = styling.decorate_columns(list(bao_cao.form.table.columns.order_by("order", "id")))
    from copy import copy
    row = copy(bao_cao.record)
    row.data = dict(row.data)
    compute_report(row, bao_cao.form.table, cot)
    return [(column, display_report_value(column, value), css)
            for column, value, css in styling.row_cells(row, cot)]


def compute_report(row, table, columns):
    """Chỉ làm tròn kết quả cuối, không chia các trung gian đã làm tròn về 0."""
    from decimal import Decimal
    from reports.services.activity_service import FORMULAS
    from reports.marketing import Metric
    row.apply_computed_columns(columns)
    source = getattr(table, 'erp_report', None)
    if not source or source.kind != 'mkt':
        return
    by_code = {column.code:column for column in columns}
    names = {'cpo':'cpo', 'mess_cost':'gia_mess', 'cost_sales':'cpqc_doanh_so',
             'invoice_revenue':'hoa_don_doanh_thu', 'aov':'aov'}
    values = {code:Decimal(str(row.data[code])) if row.data.get(code) not in (None, '') else None
              for code in {source.columns[key] for key in ('cost','orders','mess','sales') if key in source.columns}}
    for metric, code in names.items():
        column = by_code.get(code)
        if column is None or not column.is_computed:
            continue
        _, inputs, kind = FORMULAS[metric]
        value = Metric(code, tuple(source.columns.get(key, '__missing') for key in inputs), kind).compute(values)
        row.data[code] = str(value.quantize(Decimal(1).scaleb(-column.compute_decimals))) if value is not None else None


def display_report_value(column, value):
    from datetime import date, datetime
    from django.utils import timezone
    from reports.aggregations import format_number
    if value in (None, ''):
        return '—'
    try:
        if column.field_type == 'date':
            return date.fromisoformat(str(value)).strftime('%d/%m/%Y')
        if column.field_type == 'datetime':
            moment = datetime.fromisoformat(str(value))
            if timezone.is_aware(moment):
                moment = timezone.localtime(moment)
            return moment.strftime('%d/%m/%Y %H:%M')
        if column.field_type in ('money', 'decimal', 'integer'):
            return format_number(value, column.compute_decimals if column.is_computed else (0 if column.field_type == 'integer' else 2))
    except (ValueError, TypeError):
        pass
    return value


def history_choices(user):
    """Danh mục lọc chỉ lấy từ báo cáo người xem có quyền đọc."""
    from django.db.models import Exists, OuterRef
    from org.models import Department
    from forms_builder.models import FormDef, TableDef

    reports = history(user)
    allowed = TableDef.objects.in_scope(user).filter(is_active=True)
    forms = FormDef.objects.filter(pk__in=reports.values("form_id")).annotate(
        report_source_allowed=Exists(allowed.filter(pk=OuterRef("table_id")))
    ).order_by("name")
    departments = Department.objects.filter(pk__in=reports.values("department_id")).order_by("name")
    return forms, departments


def attach_marketing_links(page, forms, date_from, date_to):
    """Gắn đường sang thống kê sau phân trang; không đọc cột theo từng dòng."""
    from urllib.parse import urlencode
    from .. import marketing

    from django.db.models import prefetch_related_objects

    page.object_list = list(page.object_list)
    legacy = [r for r in page.object_list if getattr(r.form.table, "erp_report", None) is None]
    prefetch_related_objects(legacy, "form__table__columns")
    allowed_forms = {form.pk for form in forms if form.report_source_allowed}
    table_cache = {}
    for report in page:
        table = report.form.table
        configured = getattr(table, "erp_report", None)
        if configured is None and table.pk not in table_cache:
            table_cache[table.pk] = marketing.is_marketing(list(table.columns.all()))
        if report.form_id in allowed_forms and configured is not None:
            report.activity_qs = urlencode({"nguon": table.code,
                "tu": date_from or report.report_date.isoformat(),
                "den": date_to or report.report_date.isoformat()})
        elif report.form_id in allowed_forms and table_cache[table.pk]:
            report.thong_ke_qs = urlencode({"nguon": table.code, "nhom": "tong-hop",
                "tu": date_from or report.report_date.isoformat(),
                "den": date_to or report.report_date.isoformat()})
