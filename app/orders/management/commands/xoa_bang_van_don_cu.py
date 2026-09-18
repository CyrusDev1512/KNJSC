"""Xoá CỨNG hai bảng vận đơn cũ crmThuận (`van_don_moi`) và Vận đơn DB (`van_don_db`)
cùng mọi thứ dính theo — quyết định của chủ dự án 18.09.2026 (ADR-036), là ngoại lệ
có chủ ý của quy tắc BR-4 "xoá là đánh dấu".

    python manage.py xoa_bang_van_don_cu --dong-y-xoa-cung --backup-da-lam

Chạy được cả khi DEBUG tắt (để dùng trên VPS) nhưng bắt buộc hai cờ: không có
backup thì không chạy. Một giao dịch: lỗi giữa chừng là không mất gì. Đơn ERP đang
trỏ tới dòng bị xoá thì giữ đơn, bỏ liên kết. Từ chối khi còn Biểu mẫu hay Báo cáo
ngày trỏ tới bảng — hai thứ đó phải được chuyển đi trước, không tự đoán.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.audit import record
from core.constants import AuditAction
from crm.models import GridCellHistory, GridMutationReceipt
from forms_builder.models import DataRecord, FormDef, Grant, TableDef
from orders.constants import WAYBILL_TABLE_CODE
from orders.models import Order, WaybillAssignment, WaybillItem
from orders.payment_models import PaymentDocument, PaymentImage
from reports.models import DailyReport

BANG_CU = ("van_don_moi", "van_don_db")


def _raw_delete(queryset):
    count = queryset.count()
    if count:
        queryset._raw_delete(queryset.db)
    return count


@transaction.atomic
def xoa_cung(code, *, actor=None):
    """Xoá cứng một bảng động và mọi bản ghi phụ thuộc. Trả về dict số lượng đã xoá,
    None nếu bảng không tồn tại."""
    if code == WAYBILL_TABLE_CODE:
        raise CommandError(f"Không xoá bảng vận đơn duy nhất `{WAYBILL_TABLE_CODE}`.")
    table = TableDef.all_objects.select_for_update().filter(code=code).first()
    if table is None:
        return None
    rows = DataRecord._base_manager.filter(table=table)
    if FormDef.objects.filter(table=table).exists():
        raise CommandError(f"`{code}` còn biểu mẫu trỏ tới; chuyển biểu mẫu trước khi xoá.")
    if DailyReport.objects.filter(record__table=table).exists():
        raise CommandError(f"`{code}` còn báo cáo ngày trỏ tới; không xoá.")
    row_ids = rows.values("pk")
    so = {}
    so["anh_chung_tu"] = _raw_delete(PaymentImage._base_manager.filter(document__record__in=row_ids))
    so["chung_tu"] = _raw_delete(PaymentDocument._base_manager.filter(record__in=row_ids))
    so["lich_su_o"] = _raw_delete(GridCellHistory.objects.filter(record__in=row_ids))
    so["bien_nhan"] = _raw_delete(GridMutationReceipt.objects.filter(table=table))
    so["chi_tiet"] = _raw_delete(WaybillItem._base_manager.filter(record__in=row_ids))
    so["phan_cong"] = _raw_delete(WaybillAssignment.objects.filter(record__in=row_ids))
    so["don_bo_lien_ket"] = Order.objects.filter(record__in=row_ids).update(record=None)
    so["dong"] = _raw_delete(rows)
    so["quyen"] = _raw_delete(Grant._base_manager.filter(table=table))
    so["cot"] = table.columns.count()
    ten = table.name
    table.hard_delete()   # TableDef là SoftDeleteModel; ColumnDef, GridRevision, GridChange, ReportSource: CASCADE
    record(AuditAction.DELETE, actor=actor, target=("TableDef", code),
           detail=f"Xoá cứng bảng {ten} ({code}) theo ADR-036: " + ", ".join(f"{k}={v}" for k, v in so.items()))
    return so


class Command(BaseCommand):
    help = "Xoá cứng crmThuận và Vận đơn DB cùng dữ liệu phụ thuộc (ADR-036); cần backup trước"

    def add_arguments(self, parser):
        parser.add_argument("--bang", nargs="*", default=list(BANG_CU), help="Mã bảng cần xoá")
        parser.add_argument("--dong-y-xoa-cung", action="store_true", dest="dong_y",
                            help="Xác nhận hiểu rằng dữ liệu mất vĩnh viễn")
        parser.add_argument("--backup-da-lam", action="store_true", dest="backup",
                            help="Xác nhận đã backup cơ sở dữ liệu và kiểm phục hồi")

    def handle(self, *args, **options):
        if not (options["dong_y"] and options["backup"]):
            raise CommandError("Lệnh xoá cứng: cần cả --dong-y-xoa-cung và --backup-da-lam.")
        for code in options["bang"]:
            so = xoa_cung(code)
            if so is None:
                self.stdout.write(f"{code}: không có gì để xoá.")
                continue
            self.stdout.write(self.style.SUCCESS(
                f"{code}: đã xoá cứng — " + ", ".join(f"{k} {v}" for k, v in so.items())))
