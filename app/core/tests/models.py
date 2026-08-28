"""Model dùng để kiểm thử phạm vi quyền.

Chỉ tồn tại khi chạy kiểm thử — app `core.tests` chỉ nằm trong
`knjsc.settings.test`, không có trong cấu hình máy chủ.

Nhờ có model này, `ScopedManager` được kiểm trên một bảng thật thay vì
kiểm gián tiếp, mà không phải đợi module nghiệp vụ nào viết xong.
"""
from django.db import models

from core.models import ScopedModel


class ScopeProbe(ScopedModel):
    """Bản ghi có đủ ba cột người tạo, team, bộ phận."""

    title = models.CharField("Tiêu đề", max_length=100)
    department = models.ForeignKey(
        "org.Department", verbose_name="Bộ phận",
        null=True, blank=True, on_delete=models.CASCADE, related_name="+",
    )
    team = models.ForeignKey(
        "org.Team", verbose_name="Team",
        null=True, blank=True, on_delete=models.CASCADE, related_name="+",
    )

    class Meta:
        verbose_name = "Bản ghi thử phạm vi"

    def __str__(self):
        return self.title
