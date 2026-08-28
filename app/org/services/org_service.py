"""Quy tắc nghiệp vụ về bộ phận và team."""
from django.db import transaction

from core.audit import record
from core.constants import AuditAction
from core.exceptions import BusinessError

from ..models import Department, Team


@transaction.atomic
def create_department(*, name, code, actor=None, request=None):
    bo_phan = Department.objects.create(name=name, code=code)
    record(AuditAction.CREATE, actor=actor, target=bo_phan,
           detail=f"Tạo bộ phận {name}", request=request)
    return bo_phan


@transaction.atomic
def create_team(*, name, department, leader=None, actor=None, request=None):
    team = Team.objects.create(name=name, department=department, leader=leader)
    record(AuditAction.CREATE, actor=actor, target=team,
           detail=f"Tạo team {name} thuộc {department}", request=request)
    return team


@transaction.atomic
def assign_member(profile, *, department=None, team=None, actor=None, request=None):
    """Gán người vào bộ phận và team.

    Team phải thuộc đúng bộ phận đang gán. Đổi bộ phận hoặc team làm phiên
    đang mở mất hiệu lực ngay (P4) — việc đó do `UserProfile.save()` lo.
    """
    if team is not None and department is not None and team.department_id != department.id:
        raise BusinessError(
            f"Team {team} không thuộc bộ phận {department}.", code="team_sai_bo_phan",
        )
    cu = f"{profile.department or '—'} / {profile.team or '—'}"
    profile.department = department
    profile.team = team
    profile.save(update_fields=["department", "team"])
    record(
        AuditAction.PERMISSION, actor=actor, target=profile,
        detail=f"Chuyển từ {cu} sang {department or '—'} / {team or '—'}",
        request=request,
    )
    return profile


@transaction.atomic
def deactivate_department(department, *, actor=None, request=None):
    """Ngừng dùng một bộ phận. Xoá là đánh dấu, không xoá cứng (BR-4)."""
    if department.members.exists():
        raise BusinessError(
            "Bộ phận vẫn còn nhân sự, chuyển họ đi trước khi ngừng dùng.",
            code="bo_phan_con_nguoi",
        )
    department.is_active = False
    department.save(update_fields=["is_active"])
    record(AuditAction.UPDATE, actor=actor, target=department,
           detail="Ngừng dùng bộ phận", request=request)
    return department
