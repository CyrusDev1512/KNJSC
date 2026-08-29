"""Manager áp phạm vi cho bảng động.

Có hai tầng phạm vi khác nhau trong module này, và trộn chúng lại là hỏng:

**Định nghĩa bảng — `TableDef`.** Cả bộ phận nhìn thấy, không phân biệt cấp
bậc. Tên bảng và tên cột không phải dữ liệu nghiệp vụ; giấu chúng đi thì Leader
và Staff không mở nổi màn hình nào.

**Bản ghi trong bảng — `DataRecord`.** Đây mới là dữ liệu thật, áp phạm vi theo
cấp bậc như mọi nơi khác: Staff thấy bản ghi của mình, Leader thấy team mình,
Manager thấy cả bộ phận (FR-3.1 tới FR-3.3). `DataRecord` kế thừa `ScopedModel`
nên đã có sẵn, không cần viết gì ở đây.

Vì sao `TableDef` không dùng `ScopedManager` mặc định: nó không có cột team
(một bảng thuộc về bộ phận, không thuộc về team nào). `apply_scope` chỉ chạy
nhánh Leader khi có cột team, nên Leader sẽ rơi xuống nhánh cuối và chỉ thấy
bảng do chính mình tạo — mà Leader thì không được tạo bảng (FR-8.1 giao quyền
đó cho Manager). Kết quả là Leader thấy danh sách rỗng.
"""
from django.db import models
from django.db.models import Q

from core.managers import ScopedQuerySet, apply_department_scope, apply_scope
from core.scope import get_user_scope


def _cap_them(user, action):
    """Khoá chính các bảng người này được cấp quyền riêng — FR-3.4, FR-8.4.

    Nhập muộn để tránh vòng nhập: `grant_service` cần `models`, mà `models`
    cần tệp này.
    """
    from .services import grant_service

    return grant_service.granted_table_ids(user, action)


class TableDefQuerySet(ScopedQuerySet):
    """Giữ nguyên xoá mềm và `can_view` của `ScopedQuerySet`, chỉ đổi `in_scope`."""

    def in_scope(self, user):
        """Bảng của bộ phận mình, cộng bảng được cấp quyền xem riêng."""
        from .models import GrantAction

        trong_bo_phan = apply_department_scope(self, user, field="department_id")
        if get_user_scope(user).all_departments:
            return trong_bo_phan

        duoc_cap = _cap_them(user, GrantAction.VIEW)
        if not duoc_cap:
            return trong_bo_phan
        return self.filter(
            Q(pk__in=trong_bo_phan.values("pk")) | Q(pk__in=duoc_cap)
        )


class TableDefManager(models.Manager.from_queryset(TableDefQuerySet)):
    """Loại sẵn bảng đã đánh dấu xoá, giống `ScopedManager`."""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class AllTableDefManager(models.Manager.from_queryset(TableDefQuerySet)):
    """Gồm cả bảng đã xoá. Dùng cho tệp chuyển đổi dữ liệu và kiểm thử."""


class FormDefQuerySet(ScopedQuerySet):
    """Biểu mẫu cũng không có cột team, nên dính đúng cái bẫy của bảng."""

    def in_scope(self, user):
        """Biểu mẫu của bộ phận mình, cộng biểu mẫu được cấp quyền điền.

        Phải cộng phần được cấp quyền ngay ở đây: view lấy biểu mẫu qua
        `in_scope` **trước** khi gọi `can_fill`, nên thiếu nhánh này thì người
        được cấp quyền nhận 404 và không bao giờ tới được phép kiểm kia.
        """
        from .models import GrantAction
        from .services import grant_service

        trong_bo_phan = apply_department_scope(self, user, field="department_id")
        if get_user_scope(user).all_departments:
            return trong_bo_phan

        duoc_cap = grant_service.granted_form_ids(user, GrantAction.FILL)
        if not duoc_cap:
            return trong_bo_phan
        return self.filter(
            Q(pk__in=trong_bo_phan.values("pk")) | Q(pk__in=duoc_cap)
        )


class FormDefManager(models.Manager.from_queryset(FormDefQuerySet)):
    """Loại sẵn biểu mẫu đã đánh dấu xoá."""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class AllFormDefManager(models.Manager.from_queryset(FormDefQuerySet)):
    """Gồm cả biểu mẫu đã xoá."""


class DataRecordQuerySet(ScopedQuerySet):
    """Bản ghi vẫn theo phạm vi cấp bậc, cộng thêm bảng được cấp quyền riêng.

    Khác `TableDef` ở chỗ đây là dữ liệu thật, nên phần theo cấp bậc giữ nguyên
    như cũ: nhân viên thấy dòng của mình, trưởng nhóm thấy team, quản lý thấy
    cả bộ phận. Cấp quyền chỉ **cộng thêm**, không thay thế.
    """

    def in_scope(self, user):
        from .models import GrantAction

        theo_cap_bac = apply_scope(
            self, user, owner="created_by", team="team", department="department",
        )
        scope = get_user_scope(user)
        if scope.all_departments:
            return theo_cap_bac

        them = Q(pk__in=[])

        # Bảng dùng chung: cả bộ phận sở hữu thấy mọi dòng, không phân biệt
        # cấp bậc. Bảng vận đơn là hàng đợi việc chung — nhân viên Vận đơn
        # không tạo dòng nào nên phạm vi theo cấp bậc sẽ cho họ thấy rỗng
        if scope.department_ids:
            them |= Q(table__is_shared=True, table__department_id__in=scope.department_ids)

        duoc_cap = _cap_them(user, GrantAction.VIEW) | _cap_them(user, GrantAction.EDIT)
        if duoc_cap:
            them |= Q(table_id__in=duoc_cap)

        return self.filter(Q(pk__in=theo_cap_bac.values("pk")) | them)


class DataRecordManager(models.Manager.from_queryset(DataRecordQuerySet)):
    """Loại sẵn bản ghi đã đánh dấu xoá."""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class AllDataRecordManager(models.Manager.from_queryset(DataRecordQuerySet)):
    """Gồm cả bản ghi đã xoá."""
