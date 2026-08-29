"""Báo cáo hằng ngày.

**Nội dung báo cáo không lưu ở đây.** Giai đoạn 3 đã dựng sẵn bộ máy biểu mẫu
và bảng động, nên `DailyReport` chỉ bọc thêm bốn thứ mà bảng động không có:

    ai nộp  ·  báo cáo cho ngày nào  ·  nộp lúc mấy giờ  ·  đã khoá chưa

Nội dung nằm trong `DataRecord` do biểu mẫu sinh ra, đúng như mọi dòng dữ liệu
khác. Nhờ vậy báo cáo tự động vào được báo cáo tổng hợp ở Giai đoạn 6, không
phải viết đường ống thứ hai.

Vì sao không cho `DailyReport` tự giữ nội dung: sẽ có hai chỗ lưu dữ liệu người
dùng nhập, hai bộ quy tắc kiểm, và hai đường tính thống kê — đúng thứ điều cấm
1 và 11 muốn ngăn.

FR-4.1 "mỗi bộ phận có biểu mẫu báo cáo riêng" chính là `FormDef.department`,
đã có sẵn từ Giai đoạn 3.
"""
from django.db import models

from core.models import ScopedModel


class DailyReport(ScopedModel):
    """Một lần nộp báo cáo của một người, cho một ngày.

    Nộp xong là khoá — BR-2 và FR-4.4. Không có đường sửa, kể cả gọi thẳng
    đường dẫn; xem `services/daily_service.py`.
    """

    SCOPE_OWNER_FIELD = "created_by"
    SCOPE_TEAM_FIELD = "team"
    SCOPE_DEPARTMENT_FIELD = "department"

    form = models.ForeignKey(
        "forms_builder.FormDef", verbose_name="Biểu mẫu",
        on_delete=models.PROTECT, related_name="daily_reports", db_index=True,
    )
    record = models.OneToOneField(
        "forms_builder.DataRecord", verbose_name="Dòng dữ liệu",
        on_delete=models.PROTECT, related_name="daily_report",
    )
    report_date = models.DateField("Báo cáo cho ngày", db_index=True)
    submitted_at = models.DateTimeField(
        "Thời điểm nộp", auto_now_add=True, db_index=True,
        help_text="Lưu theo giờ quốc tế, hiển thị theo giờ Việt Nam — BR-7.",
    )
    department = models.ForeignKey(
        "org.Department", verbose_name="Bộ phận",
        on_delete=models.PROTECT, related_name="daily_reports", db_index=True,
    )
    team = models.ForeignKey(
        "org.Team", verbose_name="Team", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="daily_reports", db_index=True,
    )

    class Meta:
        verbose_name = "Báo cáo hằng ngày"
        verbose_name_plural = "Báo cáo hằng ngày"
        ordering = ["-report_date", "-submitted_at"]
        constraints = [
            # Một người nộp một biểu mẫu một lần cho mỗi ngày. Ràng buộc này
            # là chỗ chặn cuối của BR-2: không nộp đè lên bản đã có
            models.UniqueConstraint(
                fields=["form", "created_by", "report_date"],
                condition=models.Q(deleted_at__isnull=True),
                name="report_unique_per_person_per_day",
            ),
        ]
        indexes = [
            models.Index(fields=["department", "-report_date"], name="report_dept_date_idx"),
            models.Index(fields=["created_by", "-report_date"], name="report_owner_date_idx"),
        ]

    def __str__(self):
        return f"{self.form.code} · {self.report_date}"

    #: Những cột được phép ghi sau khi đã nộp — chỉ để đánh dấu xoá (BR-4)
    XOA_MEM = frozenset({"deleted_at", "deleted_by", "updated_at"})

    def save(self, *args, **kwargs):
        """Chặn sửa ở mức đối tượng — BR-2, FR-4.4.

        Không dựa vào view nhớ kiểm. Ai gọi `save()` trên một báo cáo đã nộp
        thì nổ ngay, kể cả tác vụ nền hay dòng lệnh.

        Riêng đánh dấu xoá vẫn cho, vì `SoftDeleteModel.delete()` đi qua đúng
        `save()` này — chặn cả nó thì mất luôn xoá mềm.
        """
        cot = kwargs.get("update_fields")
        chi_xoa_mem = cot is not None and set(cot) <= self.XOA_MEM
        if self.pk is not None and not chi_xoa_mem:
            raise RuntimeError(
                "Báo cáo đã nộp không sửa được — BR-2. "
                "Muốn bỏ thì đánh dấu xoá qua daily_service."
            )
        return super().save(*args, **kwargs)
