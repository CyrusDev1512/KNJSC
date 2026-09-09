"""Quy tắc tạo và sửa bảng động.

Tầng dịch vụ, không biết gì về HTTP (điều cấm 2). Mọi thao tác ghi đều ghi
nhật ký hoạt động (BR-5) và nằm trong một giao dịch.

`ColumnDef.clean()` **không** tự chạy khi gọi `save()` — Django chỉ chạy nó qua
`full_clean()`. Nên mọi hàm ở đây gọi `full_clean()` trước khi lưu; bỏ qua là
lọt cấu hình hỏng vào cơ sở dữ liệu.
"""
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime

from django.db import OperationalError, connection, transaction

from core.audit import record
from core.constants import RECOMPUTE_BATCH, RECOMPUTE_SYNC_MAX_ROWS, RECOMPUTE_THREADS, AuditAction, JobKind, JobStatus
from core.models import BackgroundJob

from ..meaning import FieldType
from .. import record_policies
from ..models import COLUMN_OF, ColumnDef, DataRecord, TableDef

logger = logging.getLogger(__name__)
RECOMPUTE_RETRIES = 3


@transaction.atomic
def create_table(*, name, code, department, description="", actor=None, request=None):
    """Tạo một bảng mới. Bảng thuộc về bộ phận, không thuộc về team."""
    bang = TableDef(
        name=name, code=code, department=department,
        description=description, created_by=actor,
    )
    bang.full_clean(exclude=["created_by"])
    bang.save()
    record(
        AuditAction.CREATE, actor=actor, target=bang,
        detail=f"Tạo bảng dữ liệu {code}", request=request,
    )
    return bang


@transaction.atomic
def update_table(table, changes, *, actor=None, request=None):
    """Sửa tên hoặc mô tả bảng. Không đổi được tên kỹ thuật."""
    da_doi = []
    for ten in ("name", "description", "is_active"):
        if ten not in changes:
            continue
        cu, moi = getattr(table, ten), changes[ten]
        if cu == moi:
            continue
        da_doi.append(f"{table._meta.get_field(ten).verbose_name}: {cu} → {moi}")
        setattr(table, ten, moi)

    if not da_doi:
        return table

    table.full_clean(exclude=["created_by"])
    table.save()
    record(
        AuditAction.UPDATE, actor=actor, target=table,
        detail=f"Sửa bảng {table.code} — " + " · ".join(da_doi), request=request,
    )
    return table


# ══ CỘT ═══════════════════════════════════════════════════════════

#: Trường của cột mà người dùng sửa được
COLUMN_FIELDS = (
    "name", "code", "field_type", "meaning", "required", "order", "is_key",
    "options", "highlight", "alert_op", "alert_value",
    "is_computed", "compute_op", "compute_left", "compute_right", "compute_decimals",
)

#: Đổi một trong những trường này thì số liệu đã lưu phải tính lại — ADR-006
RECOMPUTE_FIELDS = frozenset(
    {"is_computed", "compute_op", "compute_left", "compute_right", "compute_decimals"}
)


@transaction.atomic
def add_column(table, *, actor=None, request=None, **fields):
    """Thêm một cột vào bảng.

    Cột mang nhãn ý nghĩa sẽ được tách sang cột riêng có chỉ mục trên
    `DataRecord` (ADR-001). Bản ghi đã có sẽ được đồng bộ ngay, nếu không thì
    lọc theo cột đó sẽ bỏ sót toàn bộ dữ liệu cũ.
    """
    cot = ColumnDef(table=table, **{k: v for k, v in fields.items() if k in COLUMN_FIELDS})
    if not cot.order:
        cot.order = _thu_tu_ke_tiep(table)
    cot.full_clean()
    cot.save()

    if cot.meaning or cot.is_computed:
        cot.resync_job = schedule_resync(table, actor=actor)

    record(
        AuditAction.CREATE, actor=actor, target=cot,
        detail=f"Thêm cột {cot.code} vào bảng {table.code}", request=request,
    )
    return cot


@transaction.atomic
def update_column(column, changes, *, actor=None, request=None):
    """Sửa một cột. Đổi công thức thì tính lại toàn bộ bản ghi cũ."""
    policy = record_policies.for_table(column.table)
    if policy:
        policy.assert_column_change(column, changes)
    da_doi, phai_tinh_lai = [], False
    for ten in COLUMN_FIELDS:
        if ten not in changes:
            continue
        cu, moi = getattr(column, ten), changes[ten]
        if cu == moi:
            continue
        da_doi.append(f"{column._meta.get_field(ten).verbose_name}: {cu} → {moi}")
        setattr(column, ten, moi)
        if ten in RECOMPUTE_FIELDS or ten == "meaning":
            phai_tinh_lai = True

    if not da_doi:
        return column

    column.full_clean()
    column.save()

    # ADR-006: đổi công thức mà không tính lại thì bản ghi cũ giữ số cũ, bản
    # ghi mới có số mới, cùng một cột — không ai phát hiện ra cho tới lúc đối
    # chiếu báo cáo
    if phai_tinh_lai:
        column.resync_job = schedule_resync(column.table, actor=actor)

    record(
        AuditAction.UPDATE, actor=actor, target=column,
        detail=f"Sửa cột {column.code} — " + " · ".join(da_doi), request=request,
    )
    return column


@transaction.atomic
def remove_column(column, *, actor=None, request=None):
    """Bỏ một cột khỏi bảng.

    Xoá định nghĩa cột, nhưng **không** xoá giá trị đã nhập trong JSON — dữ
    liệu người dùng gõ vào không tự biến mất (tinh thần BR-4). Cột không còn
    hiển thị, và gán lại đúng tên kỹ thuật đó thì dữ liệu cũ hiện trở lại.
    """
    policy = record_policies.for_table(column.table)
    if policy:
        policy.assert_column_change(column)
    bang, ma = column.table, column.code
    column.delete()
    schedule_resync(bang, actor=actor)
    record(
        AuditAction.DELETE, actor=actor, target=bang,
        detail=f"Bỏ cột {ma} khỏi bảng {bang.code}", request=request,
    )
    return bang


@transaction.atomic
def insert_columns(table, *, count=1, anchor=None, after=True, actor=None, request=None):
    """Chèn `count` cột chữ ngắn "Cột mới k" cạnh cột `anchor` (trước hay sau) —
    menu chuột phải của Bảng tính, ADR-011. Không có `anchor` thì chèn cuối.
    Đánh lại `order` của mọi cột theo vị trí mới. Trả về các cột vừa tạo."""
    cac_cot = list(table.columns.order_by("order", "id"))
    vi_tri = len(cac_cot)
    for i, c in enumerate(cac_cot):
        if anchor and c.code == anchor:
            vi_tri = i + 1 if after else i
            break
    da_co = {c.code for c in cac_cot}
    moi = []
    n = 1
    for _ in range(count):
        while f"cot_moi_{n}" in da_co:
            n += 1
        da_co.add(f"cot_moi_{n}")
        moi.append(ColumnDef(table=table, name=f"Cột mới {n}", code=f"cot_moi_{n}", field_type=FieldType.TEXT))
        n += 1
    thu_tu = cac_cot[:vi_tri] + moi + cac_cot[vi_tri:]
    for i, c in enumerate(thu_tu, start=1):
        if c.pk is None:
            c.order = i
            c.full_clean()
            c.save()
            record(
                AuditAction.CREATE, actor=actor, target=c,
                detail=f"Chèn cột {c.code} vào bảng {table.code} ở vị trí {i}", request=request,
            )
        elif c.order != i:
            c.order = i
            c.save(update_fields=["order", "updated_at"])
    return moi


def removable_reason(column):
    """Vì sao không bỏ được cột này ngay trên lưới; trống nghĩa là bỏ được.
    Cột khoá và cột đang là vế của một cột tính sẵn thì giữ."""
    policy = record_policies.for_table(column.table)
    if policy:
        try:
            policy.assert_column_change(column)
        except BusinessError as error:
            return str(error)
    if column.is_key:
        return f'"{column.name}" là cột khoá của bảng — đổi cột khoá ở Sửa cột trước.'
    dung_o = [
        c.name for c in column.table.columns.filter(is_computed=True)
        if column.code in (c.compute_left, c.compute_right)
    ]
    if dung_o:
        return f'"{column.name}" đang là vế của cột tính sẵn {", ".join(dung_o)}.'
    return ""


def _thu_tu_ke_tiep(table):
    cuoi = table.columns.order_by("-order").values_list("order", flat=True).first()
    return (cuoi or 0) + 1


def resync_table(table, *, batch=RECOMPUTE_BATCH, on_progress=None):
    """Tính lại cột tính sẵn và cột tách cho mọi bản ghi của một bảng.

    Gọi sau khi đổi công thức hoặc đổi nhãn ý nghĩa. Lấy danh sách cột **một
    lần** rồi truyền vào từng bản ghi — để `DataRecord.save()` tự lấy thì mỗi
    dòng tốn thêm một lệnh truy vấn (quy tắc Q2). Làm theo lô `batch` dòng:
    khoá lô (`select_for_update`) → tính trong bộ nhớ → một `bulk_update`,
    nên 100.000 dòng là ~100 giao dịch ngắn thay vì 100.000 lệnh UPDATE (K27);
    người đang sửa ô trong lúc đó không mất dữ liệu — lệnh của họ chờ lô xong
    rồi ghi đè bằng bản đã tính đủ cột (`DataRecord.save`). `on_progress(n)`
    báo sau mỗi lô. Trả về số dòng đã tính.

    Không ghi nhật ký: đây là hệ quả của một thao tác đã được ghi, không phải
    thao tác của người dùng. Bảng lớn thì đừng gọi thẳng — `schedule_resync`.
    """
    from .record_service import save_rows

    cot = list(table.columns.all())
    pks = list(DataRecord.all_objects.filter(table=table).order_by("pk").values_list("pk", flat=True))
    da_sua = 0
    khoa = threading.Lock()

    def mot_lo(i):
        for lan in range(RECOMPUTE_RETRIES):
            try:
                with transaction.atomic():
                    # Khoá theo thứ tự khoá chính, cùng chiều với `bulk_save` của người đang dán ô
                    lo = list(DataRecord.all_objects.select_for_update().filter(pk__in=pks[i:i + batch]).order_by("pk"))
                    doi, cot_doi = [], set()
                    for ban_ghi in lo:
                        truoc = (dict(ban_ghi.data), *(getattr(ban_ghi, c) for c in COLUMN_OF.values()))
                        ban_ghi.apply_computed_columns(cot)
                        ban_ghi.sync_indexed_columns(cot)
                        sau = (ban_ghi.data, *(getattr(ban_ghi, c) for c in COLUMN_OF.values()))
                        khac = [c for c, a, b in zip(("data", *COLUMN_OF.values()), truoc, sau) if not _giong(a, b)]
                        if not khac:
                            continue                   # dòng không đổi thì không ghi, không đổi mốc
                        doi.append(ban_ghi)
                        cot_doi.update(khac)
                    if doi:
                        save_rows(doi, fields=sorted(cot_doi))
                return len(lo)
            except OperationalError as loi:
                # Deadlock với một lượt dán ô: worker là bên nhường, thử lại lô này
                if "deadlock" not in str(loi).lower() or lan == RECOMPUTE_RETRIES - 1:
                    raise
                time.sleep(0.5)

    def bao(n):
        nonlocal da_sua
        with khoa:
            da_sua += n
            if on_progress:
                on_progress(da_sua)

    dau_lo = range(0, len(pks), batch)
    # Ở worker (ngoài giao dịch) chạy song song vài lô: phần nặng là Postgres ghi
    # lại chỉ mục GIN của JSON, hai kết nối là hai nhân. Trong giao dịch (bảng nhỏ
    # tính tại chỗ, bài kiểm) thì tuần tự — luồng khác không thấy dữ liệu chưa commit.
    if RECOMPUTE_THREADS > 1 and not connection.in_atomic_block and len(dau_lo) > 1:
        def chay(i):
            try:
                return mot_lo(i)
            finally:
                connection.close()                     # mỗi luồng một kết nối riêng, đóng khi xong
        with ThreadPoolExecutor(max_workers=RECOMPUTE_THREADS) as pool:
            for n in pool.map(chay, dau_lo):
                bao(n)
    else:
        for i in dau_lo:
            bao(mot_lo(i))
    return da_sua


def _giong(a, b):
    """Giá trị cột tách trước và sau đồng bộ có như nhau không. Cột ngày đọc từ
    DB là `date`, còn `sync_indexed_columns` đặt lại chuỗi ISO từ JSON — so bằng
    chuỗi; số tiền so bằng Decimal (120 == 120.00)."""
    if a is None or b is None:
        return a is b or (a in ("", None) and b in ("", None))
    if isinstance(a, (date, datetime)) or isinstance(b, (date, datetime)):
        return str(a) == str(b)
    return a == b


def schedule_resync(table, *, actor=None):
    """Tính lại cột của bảng: ngay tại chỗ khi bảng có tới `RECOMPUTE_SYNC_MAX_ROWS`
    dòng, còn không thì giao **tác vụ nền** (ADR-016) — cột hiện ngay, giá trị
    điền dần, lưới báo "đang tính" qua `moi-nhat/`, Manager không phải đợi và
    worker web không bị chiếm hàng phút. Trả về `BackgroundJob` nếu chạy nền,
    None nếu đã tính xong tại chỗ."""
    so_dong = DataRecord.all_objects.filter(table=table).count()
    if so_dong <= RECOMPUTE_SYNC_MAX_ROWS:
        resync_table(table)
        return None
    job = BackgroundJob.objects.create(
        kind=JobKind.RECOMPUTE, status=JobStatus.PENDING, created_by=actor,
        title=f"Tính lại cột của bảng {table.name} ({so_dong} dòng)",
        target_type="table", target_id=table.code, total=so_dong,
    )
    from ..tasks import chay_tac_vu_tinh_lai
    from .import_service import _day_vao_hang_doi

    _day_vao_hang_doi(chay_tac_vu_tinh_lai, job.pk)
    return job


def recompute_job_of(table):
    """Tác vụ tính lại đang chờ hoặc đang chạy của bảng — để lưới báo tiến độ."""
    return (
        BackgroundJob.objects.filter(
            kind=JobKind.RECOMPUTE, target_type="table", target_id=table.code,
            status__in=[JobStatus.PENDING, JobStatus.RUNNING],
        ).order_by("-pk").values("pk", "progress", "total").first()
    )


def run_resync_job(job_id):
    """Worker: tính lại cột theo lô, báo tiến độ sau mỗi lô."""
    job = BackgroundJob.objects.filter(pk=job_id, kind=JobKind.RECOMPUTE).first()
    if job is None or job.status != JobStatus.PENDING:
        return None
    job.mark_running()
    try:
        table = TableDef.all_objects.get(code=job.target_id)
        da_tinh = resync_table(table, on_progress=lambda n: job.set_progress(n))
        job.set_progress(da_tinh, da_tinh)
        job.mark_done(summary={"da_tinh": da_tinh})
    except Exception:
        logger.exception("Tác vụ tính lại cột #%s thất bại", job.pk)
        job.mark_failed("Tính lại cột thất bại vì lỗi hệ thống. Sửa lại cột để chạy lại.")
    return job
