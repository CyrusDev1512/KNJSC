"""Quy tắc nộp báo cáo hằng ngày.

Tầng dịch vụ, không biết gì về HTTP (điều cấm 2). Mọi thao tác ghi nhật ký
(BR-5) và nằm trong một giao dịch.

**Nộp xong là khoá.** BR-2 và FR-4.4 nói rõ báo cáo đã nộp không sửa và không
xoá được. Nên tệp này **không có hàm sửa** — thiếu hàm là cách chặn chắc nhất.
Nộp nhầm thì đánh dấu bỏ rồi nộp lại, và cả hai việc đều để lại dấu vết.
"""
from django.db import IntegrityError, transaction

from core.audit import record
from core.constants import AuditAction
from core.exceptions import BusinessError
from forms_builder.services import form_service, grant_service

from ..models import DailyReport


def forms_for(user):
    """Các biểu mẫu người này nộp báo cáo được — FR-4.1.

    Chính là biểu mẫu trong phạm vi quyền của họ, đang dùng. Bộ phận nào thấy
    biểu mẫu bộ phận đó; không phải viết lại điều kiện lọc ở đây (quy tắc 11).
    """
    from forms_builder.models import FormDef

    return (FormDef.objects.in_scope(user)
            .filter(is_active=True)
            .select_related("department", "table")
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

    # Cùng một đường với màn hình điền biểu mẫu: ép danh tính người nộp vào
    # trường Người bán (FR-4.6), kiểm bắt buộc, rồi ghi vào bảng đích
    ban_ghi = form_service.fill(form, values, actor=actor, request=request, fields=fields)

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
            .select_related("form", "form__table", "record", "created_by", "created_by__profile", "department", "team"))


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
    return styling.row_cells(bao_cao.record, cot)


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

    page.object_list = page.object_list.prefetch_related("form__table__columns")
    allowed_forms = {form.pk for form in forms if form.report_source_allowed}
    table_cache = {}
    for report in page:
        table = report.form.table
        if table.pk not in table_cache:
            table_cache[table.pk] = marketing.is_marketing(list(table.columns.all()))
        if report.form_id in allowed_forms and table_cache[table.pk]:
            report.thong_ke_qs = urlencode({"nguon": table.code, "nhom": "tong-hop",
                "tu": date_from or report.report_date.isoformat(),
                "den": date_to or report.report_date.isoformat()})
