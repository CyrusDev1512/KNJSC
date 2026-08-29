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

from core.managers import ScopedQuerySet, apply_department_scope


class TableDefQuerySet(ScopedQuerySet):
    """Giữ nguyên xoá mềm và `can_view` của `ScopedQuerySet`, chỉ đổi `in_scope`."""

    def in_scope(self, user):
        """Mọi cấp bậc thấy bảng của bộ phận mình. Quản trị viên thấy tất cả."""
        return apply_department_scope(self, user, field="department_id")


class TableDefManager(models.Manager.from_queryset(TableDefQuerySet)):
    """Loại sẵn bảng đã đánh dấu xoá, giống `ScopedManager`."""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class AllTableDefManager(models.Manager.from_queryset(TableDefQuerySet)):
    """Gồm cả bảng đã xoá. Dùng cho tệp chuyển đổi dữ liệu và kiểm thử."""
