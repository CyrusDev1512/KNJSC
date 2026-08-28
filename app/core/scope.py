"""Hàm phạm vi duy nhất của toàn hệ thống.

Đây là chỗ duy nhất trả lời câu "người này được thấy dữ liệu của ai".
Không màn hình nào được tự viết điều kiện lọc riêng — mỗi màn hình mới lại
phải nhớ lọc, và đó là chỗ dễ sót nhất dẫn tới rò rỉ dữ liệu.

**Giao ước với module org.** core không import module nào khác, nên hàm này
đọc hồ sơ nhân sự qua thuộc tính `user.profile` mà không import lớp đó.
Hồ sơ phải có đủ ba thứ:

    profile.rank            chuỗi, một trong core.constants.Rank
    profile.department_id   khoá của bộ phận, có thể None
    profile.scope_team_ids()  trả về các khoá team người đó phụ trách

Module org chịu trách nhiệm cung cấp đúng giao ước này.
"""
from dataclasses import dataclass, field

from .constants import Rank
from .exceptions import NoProfileError


@dataclass(frozen=True)
class Scope:
    """Phạm vi quyền đã tính xong của một người dùng."""

    user_id: int
    rank: str
    department_ids: frozenset = field(default_factory=frozenset)
    team_ids: frozenset = field(default_factory=frozenset)
    all_departments: bool = False

    @property
    def is_admin(self):
        return self.all_departments


def _granted_scope(profile):
    """Phần phạm vi được cấp thêm ngoài cấp bậc.

    Thiết kế mở rộng ở mục 3.4: phạm vi = phần theo cấp bậc + phần được cấp
    riêng. Phase 1 phần thứ hai luôn rỗng. Thêm sau không phải sửa chỗ nào
    khác ngoài hàm này.
    """
    return frozenset(), frozenset()


def get_user_scope(user):
    """Tính phạm vi quyền của một người dùng.

    Cấp bậc quyết định phạm vi rộng bao nhiêu, bộ phận quyết định phạm vi
    ở đâu (ADR-003).

        Staff    chỉ bản ghi do chính người đó tạo
        Leader   toàn bộ team người đó phụ trách, cộng bản ghi của mình
        Manager  toàn bộ bộ phận của mình
        Admin    tất cả các bộ phận
    """
    if user is None or not getattr(user, "is_authenticated", False):
        raise NoProfileError("Cần đăng nhập để xem dữ liệu.")

    profile = getattr(user, "profile", None)
    if profile is None:
        # Superuser tạo bằng dòng lệnh có thể chưa có hồ sơ nhân sự
        if getattr(user, "is_superuser", False):
            return Scope(user_id=user.pk, rank=Rank.ADMIN, all_departments=True)
        raise NoProfileError()

    rank = profile.rank
    granted_departments, granted_teams = _granted_scope(profile)

    if rank == Rank.ADMIN:
        return Scope(user_id=user.pk, rank=rank, all_departments=True)

    department_ids = frozenset(
        x for x in (profile.department_id,) if x is not None
    ) | granted_departments

    if rank == Rank.MANAGER:
        return Scope(user_id=user.pk, rank=rank, department_ids=department_ids)

    if rank == Rank.LEADER:
        team_ids = frozenset(profile.scope_team_ids()) | granted_teams
        return Scope(
            user_id=user.pk, rank=rank,
            department_ids=department_ids, team_ids=team_ids,
        )

    # Staff: chỉ dữ liệu của chính mình
    return Scope(user_id=user.pk, rank=rank, department_ids=department_ids)
