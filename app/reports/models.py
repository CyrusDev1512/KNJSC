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
from django.conf import settings

from core.models import ScopedModel

from .managers import AllDailyReportManager, DailyReportManager


class DailyReport(ScopedModel):
    """Một lần nộp báo cáo của một người, cho một ngày — có thể nhiều lần một ngày (ADR-038).

    Danh tính, ngày và thời điểm nộp bất biến. Nội dung được quản lý sửa qua
    daily_service.amend theo quyết định 16/09/2026, có ReportRevision.
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

    # Kế toán thấy mọi báo cáo (ADR-038); phần còn lại là thang cấp bậc chuẩn
    objects = DailyReportManager()
    all_objects = AllDailyReportManager()

    class Meta:
        verbose_name = "Báo cáo hằng ngày"
        verbose_name_plural = "Báo cáo hằng ngày"
        ordering = ["-report_date", "-submitted_at"]
        # Không còn ràng buộc một bản/người/ngày (ADR-038, migration 0004): nộp lại
        # là thêm bản mới, sửa số qua luồng có lịch sử của ADR-032
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


class ReportSource(models.Model):
    """Ánh xạ báo cáo ERP tường minh; không dò tên trường ở mỗi yêu cầu."""
    table = models.OneToOneField("forms_builder.TableDef", on_delete=models.CASCADE,
                                related_name="erp_report")
    kind = models.CharField(max_length=12, choices=[("sale", "Sale"), ("mkt", "Marketing"), ("delivery", "Vận đơn")])
    columns = models.JSONField(default=dict)
    #: Ngưỡng màu ba bậc theo mã chỉ tiêu (ADR-040 đợt 3), Manager bộ phận sở hữu đặt:
    #: `{"cpo": {"tot": "150000", "kem": "300000"}}` — chuỗi Decimal; chỉ tiêu chưa có ngưỡng
    #: rơi về cách tô tương đối ±10 % so với dòng Tổng (AC-22.16). Không có số mặc định.
    thresholds = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Nguồn báo cáo ERP"


class RevisionQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise RuntimeError('Lịch sử báo cáo chỉ được ghi thêm.')

    def delete(self):
        raise RuntimeError('Lịch sử báo cáo chỉ được ghi thêm.')

    def bulk_create(self, objs, **kwargs):
        if kwargs.get('update_conflicts'):
            raise RuntimeError('Lịch sử báo cáo chỉ được ghi thêm.')
        return super().bulk_create(objs, **kwargs)


class ReportRevision(models.Model):
    """Lịch sử nghiệp vụ, chỉ đọc trong phạm vi của báo cáo gốc."""
    report = models.ForeignKey(DailyReport, on_delete=models.PROTECT, related_name='revisions')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    before = models.JSONField()
    after = models.JSONField()
    objects = RevisionQuerySet.as_manager()

    class Meta:
        ordering = ['-id']

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise RuntimeError('Lịch sử báo cáo chỉ được ghi thêm.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RuntimeError('Lịch sử báo cáo chỉ được ghi thêm.')
