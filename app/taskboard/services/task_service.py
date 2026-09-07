"""Quy tắc của Công việc — FR-11.1 tới FR-11.5, ADR-015.

Tầng dịch vụ, không biết gì về HTTP (điều cấm 2). Mọi thao tác ghi đều ghi
nhật ký (BR-5) và nằm trong một giao dịch.
"""
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from core.audit import record
from core.constants import AuditAction, Rank
from core.exceptions import BusinessError, OutOfScopeError
from core.identity import display_name
from core.permissions import has_rank
from org.models import UserProfile

from ..constants import (
    DESCRIPTION_MAX,
    STATUS_TRANSITIONS, TASK_FIELD_LABELS, TITLE_MAX, TaskPriority, TaskStatus,
)
from ..models import Task


# ══ QUYỀN ═════════════════════════════════════════════════════════

def assignable_users(actor):
    """Ai được giao việc cho ai — đúng luật phạm vi hồ sơ nhân sự (FR-11.1):
    Staff chỉ mình, Leader team mình, Manager cả bộ phận, Admin tất cả."""
    return (
        get_user_model().objects
        .filter(profile__in=UserProfile.objects.in_scope(actor), is_active=True)
        .select_related("profile")
        .order_by("profile__full_name", "username")
    )


def can_change_status(user, task):
    """Người làm, người tạo, hoặc Leader trở lên (đã nằm trong phạm vi)."""
    return (
        task.assignee_id == user.pk or task.created_by_id == user.pk
        or has_rank(user, Rank.LEADER)
    )


def can_edit(user, task):
    return task.created_by_id == user.pk or has_rank(user, Rank.LEADER)


def can_delete(user, task):
    return task.created_by_id == user.pk or has_rank(user, Rank.MANAGER)


# ══ ĐỌC ═══════════════════════════════════════════════════════════

def tasks_of(user):
    return (
        Task.objects.in_scope(user)
        .select_related("assignee", "assignee__profile", "created_by", "created_by__profile", "department")
    )


def next_statuses(task):
    """[(mã, nhãn)] các trạng thái chuyển được từ trạng thái hiện tại."""
    return [(m, TaskStatus(m).label) for m in STATUS_TRANSITIONS.get(task.status, ())]


# ══ GHI ═══════════════════════════════════════════════════════════

def _kiem_nguoi_lam(actor, assignee):
    if assignee is None or assignee.pk == actor.pk:
        return actor
    if not assignable_users(actor).filter(pk=assignee.pk).exists():
        raise BusinessError("Chỉ giao việc cho người trong phạm vi của bạn.")
    return assignee


def _phai_duoc(actor, task, kiem, loi):
    """Việc phải trong phạm vi và người gọi phải có quyền — kiểm ở dịch vụ, không
    trông vào view (điều cấm 2)."""
    if not Task.objects.can_view(actor, task) or not kiem(actor, task):
        raise OutOfScopeError(loi)


def _mo_ta(description):
    description = (description or "").strip()
    if len(description) > DESCRIPTION_MAX:
        raise BusinessError(f"Mô tả dài quá {DESCRIPTION_MAX} ký tự.")
    return description


def _bo_phan_cua(actor, assignee):
    """Việc thuộc bộ phận của người làm; không có thì của người tạo."""
    for nguoi in (assignee, actor):
        ho_so = getattr(nguoi, "profile", None)
        if ho_so is not None and ho_so.department_id is not None:
            return ho_so.department
    raise BusinessError("Người làm hoặc người tạo phải thuộc một bộ phận.")


@transaction.atomic
def create_task(*, title, description="", assignee=None, priority=TaskPriority.VUA,
                due_date=None, actor, request=None):
    """Tạo việc, giao cho người trong phạm vi; không chọn ai thì tự nhận — FR-11.1."""
    title = (title or "").strip()
    if not title:
        raise BusinessError("Tiêu đề không được để trống.")
    if len(title) > TITLE_MAX:
        raise BusinessError(f"Tiêu đề dài quá {TITLE_MAX} ký tự.")
    if priority not in TaskPriority.values:
        raise BusinessError("Mức ưu tiên không hợp lệ.")
    nguoi_lam = _kiem_nguoi_lam(actor, assignee)
    viec = Task.objects.create(
        title=title, description=_mo_ta(description),
        department=_bo_phan_cua(actor, nguoi_lam), assignee=nguoi_lam,
        priority=priority, due_date=due_date, created_by=actor,
    )
    record(
        AuditAction.CREATE, actor=actor, target=viec,
        detail=f"Tạo việc #{viec.pk} — giao {display_name(nguoi_lam)}", request=request,
    )
    return viec


def _hien(ten, gia_tri):
    if gia_tri in (None, ""):
        return "—"
    if ten == "assignee":
        return display_name(gia_tri)
    if ten == "priority":
        return TaskPriority(gia_tri).label
    if ten == "due_date":
        return gia_tri.strftime("%d.%m.%Y")
    if ten == "description":
        return "…"
    return str(gia_tri)


@transaction.atomic
def update_task(task, changes, *, actor, request=None):
    """Sửa tiêu đề, mô tả, người làm, ưu tiên, hạn — ghi rõ trường nào đổi.

    Người làm để trống nghĩa là **giữ nguyên**, không âm thầm giao lại cho
    người sửa; đổi người làm thì việc chuyển sang bộ phận của người đó."""
    _phai_duoc(actor, task, can_edit, "Bạn không có quyền sửa việc này.")
    da_doi = []
    for ten, moi in changes.items():
        if ten not in TASK_FIELD_LABELS:
            continue
        if ten == "title":
            moi = (moi or "").strip()
            if not moi:
                raise BusinessError("Tiêu đề không được để trống.")
            if len(moi) > TITLE_MAX:
                raise BusinessError(f"Tiêu đề dài quá {TITLE_MAX} ký tự.")
        if ten == "description":
            moi = _mo_ta(moi)
        if ten == "assignee":
            if moi is None:
                continue
            moi = _kiem_nguoi_lam(actor, moi)
        if ten == "priority" and moi not in TaskPriority.values:
            raise BusinessError("Mức ưu tiên không hợp lệ.")
        cu = getattr(task, ten)
        if cu == moi:
            continue
        da_doi.append(f"{TASK_FIELD_LABELS[ten]}: {_hien(ten, cu)} → {_hien(ten, moi)}")
        setattr(task, ten, moi)
        if ten == "assignee":
            task.department = _bo_phan_cua(actor, moi)
    if not da_doi:
        return task
    task.save()
    record(
        AuditAction.UPDATE, actor=actor, target=task,
        detail=f"Sửa việc #{task.pk} — " + " · ".join(da_doi), request=request,
    )
    return task


@transaction.atomic
def change_status(task, new_status, *, actor, request=None):
    """Chuyển trạng thái theo bảng cố định — FR-11.2."""
    _phai_duoc(actor, task, can_change_status, "Bạn không có quyền đổi trạng thái việc này.")
    if new_status not in STATUS_TRANSITIONS.get(task.status, ()):
        cu = TaskStatus(task.status).label
        moi = TaskStatus(new_status).label if new_status in TaskStatus.values else new_status
        raise BusinessError(f"Không chuyển được từ {cu} sang {moi}.")
    cu = task.status
    task.status = new_status
    task.done_at = timezone.now() if new_status == TaskStatus.XONG else None
    task.save(update_fields=["status", "done_at", "updated_at"])
    record(
        AuditAction.UPDATE, actor=actor, target=task,
        detail=f"Việc #{task.pk}: {TaskStatus(cu).label} → {TaskStatus(new_status).label}",
        request=request,
    )
    return task


@transaction.atomic
def delete_task(task, *, actor, request=None):
    """Gỡ việc: xoá mềm — FR-11.5."""
    _phai_duoc(actor, task, can_delete, "Bạn không có quyền gỡ việc này.")
    task.delete(by=actor)
    record(AuditAction.DELETE, actor=actor, target=task,
           detail=f"Gỡ việc #{task.pk}", request=request)
    return task
