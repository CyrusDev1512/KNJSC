"""Xuất bảng động ra tệp Excel — FR-7.6, FR-7.7.

Hai điều bắt buộc:

- **Xuất đúng thứ đang hiện, kèm bộ lọc đang bật** (ADR-002): bộ lọc, tìm
  kiếm, sắp xếp đọc bằng đúng bộ đọc của màn hình bảng (`query.read_filters`).
- **Tệp xuất ra nhập lại được** (AC-7.7): tiêu đề cột là tên cột của bảng,
  giá trị giữ đúng kiểu (Decimal, ngày thật), không thêm cột lạ.

Dưới `EXPORT_SYNC_MAX_ROWS` thì trả tệp ngay; lớn hơn thì chạy nền, tệp nằm
ở `storage/exports/` 24 giờ (NFR-16). Mọi lần xuất ghi nhật ký trước khi trả
— nguyên tắc P5.
"""
import logging
import uuid
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.http import QueryDict

from core import excel
from core.audit import record
from core.constants import (
    EXPORT_SYNC_MAX_ROWS, AuditAction, JobKind, JobStatus,
)
from core.exceptions import BusinessError
from core.models import BackgroundJob

from .. import query
from ..meaning import FieldType
from ..models import DataRecord, TableDef

logger = logging.getLogger(__name__)

EXPORT_SUBDIR = "exports"
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def build_queryset(user, table, params, columns=None):
    """Queryset đúng như màn hình bảng đang hiện — cùng bộ lọc, tìm, sắp xếp."""
    columns = columns if columns is not None else list(table.columns.order_by("order", "id"))
    bo_loc = query.read_filters(params, columns)
    ds, _ = query.build(
        DataRecord.objects.in_scope(user),
        table, filters=bo_loc,
        search=(params.get("tim") or "").strip(),
        sort=params.get("sap") or "",
        descending=params.get("chieu") == "giam",
        columns=columns,
    )
    return ds, columns, bo_loc


def cell_value(cot, gia_tri):
    """Giá trị ô Excel theo kiểu cột — để tệp mở ra là số thật, ngày thật."""
    if gia_tri in (None, ""):
        return None
    kieu = cot.field_type
    try:
        if kieu in (FieldType.MONEY, FieldType.DECIMAL):
            return Decimal(str(gia_tri))
        if kieu == FieldType.INTEGER:
            return int(gia_tri)
        if kieu == FieldType.DATE:
            return date.fromisoformat(str(gia_tri))
        if kieu == FieldType.DATETIME:
            return datetime.fromisoformat(str(gia_tri))
    except (InvalidOperation, ValueError, TypeError):
        return str(gia_tri)
    return gia_tri


def rows_of(queryset, columns):
    """Sinh từng dòng theo thứ tự cột, đọc theo lô để không nạp hết vào RAM."""
    for ban_ghi in queryset.iterator(chunk_size=500):
        yield [cell_value(cot, ban_ghi.data.get(cot.code)) for cot in columns]


def build_workbook(queryset, columns, *, title):
    return excel.write_table(
        [c.name for c in columns], rows_of(queryset, columns), sheet_title=title,
    )


def file_name(table):
    return f"{table.code}-{datetime.now():%Y%m%d-%H%M}.xlsx"


def export(user, table, params, *, request=None):
    """Xuất bảng. Trả `("file", Workbook)` hoặc `("job", BackgroundJob)`.

    Vượt `EXPORT_MAX_ROWS` (NFR-14) thì từ chối trước khi làm gì nặng.
    """
    ds, columns, bo_loc = build_queryset(user, table, params)
    so_dong = ds.count()
    tran = getattr(settings, "EXPORT_MAX_ROWS", 50_000)
    if so_dong > tran:
        raise BusinessError(
            f"Kết quả có {so_dong:,} dòng, vượt giới hạn xuất {tran:,} dòng. "
            "Thu hẹp bộ lọc rồi xuất lại.".replace(",", ".")
        )

    # Ghi nhật ký TRƯỚC khi trả tệp — P5. Chi tiết chỉ có tham số, không số liệu
    record(
        AuditAction.EXPORT, actor=user, target=table,
        detail=(f"Xuất Excel bảng {table.code}: {so_dong} dòng"
                + (f", lọc {', '.join(sorted(bo_loc))}" if bo_loc else "")),
        request=request,
    )

    if so_dong <= EXPORT_SYNC_MAX_ROWS:
        return "file", build_workbook(ds, columns, title=table.name)

    job = BackgroundJob.objects.create(
        kind=JobKind.EXPORT, status=JobStatus.PENDING, created_by=user,
        title=f"Xuất bảng {table.name} ({so_dong} dòng)",
        target_type="table", target_id=table.code, total=so_dong,
        summary={"params": {k: params.getlist(k) if hasattr(params, "getlist") else [params[k]]
                            for k in params.keys()},
                 "file_name": file_name(table)},
    )
    from ..tasks import chay_tac_vu_xuat
    from .import_service import _day_vao_hang_doi

    _day_vao_hang_doi(chay_tac_vu_xuat, job.pk)
    return "job", job


def run(job_id):
    """Worker: dựng lại đúng truy vấn đã xuất, ghi tệp vào storage/exports."""
    job = BackgroundJob.objects.filter(pk=job_id, kind=JobKind.EXPORT).first()
    if job is None or job.status != JobStatus.PENDING:
        return None
    job.mark_running()
    try:
        table = TableDef.objects.get(code=job.target_id)
        params = QueryDict("", mutable=True)
        for k, v in (job.summary.get("params") or {}).items():
            params.setlist(k, v)
        ds, columns, _ = build_queryset(job.created_by, table, params)
        wb = build_workbook(ds, columns, title=table.name)

        thu_muc = Path(settings.EXPORT_DIR)
        thu_muc.mkdir(parents=True, exist_ok=True)
        ten = f"{uuid.uuid4().hex}.xlsx"
        wb.save(thu_muc / ten)
        job.set_progress(job.total, job.total)
        job.mark_done(result_path=f"{EXPORT_SUBDIR}/{ten}")
    except BusinessError as loi:
        job.mark_failed(str(loi))
    except Exception:
        logger.exception("Tác vụ xuất #%s thất bại", job.pk)
        job.mark_failed("Xuất thất bại vì lỗi hệ thống. Hãy thử lại sau.")
    return job


def result_file(job):
    """Đường dẫn tuyệt đối của tệp kết quả, hoặc None nếu đã bị dọn."""
    if not job.result_path:
        return None
    duong_dan = Path(settings.STORAGE_DIR) / job.result_path
    return duong_dan if duong_dan.exists() else None
