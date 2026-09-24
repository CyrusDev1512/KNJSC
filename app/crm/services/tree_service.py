"""Trang thư mục KN CRM: Bộ phận ▸ thư mục ▸ bảng — ADR-012, thu gọn ở ADR-040.

Từ 24.09.2026 (ADR-040) KN CRM chỉ phục vụ **bảng vận đơn** và không còn cấp
Quý ▸ Tháng: lọc thời gian là việc của bộ lọc trên lưới. `Month` và
`month_of_params` giữ lại cho nhãn "Tháng x/nnnn" trên thanh lưới khi bộ lọc
ngày trên URL vừa đúng một tháng.

Trang chỉ dựng từ `in_scope` (quy tắc 11): bảng nào người này không được xem
thì không có; quyền theo bảng do Manager cấp ở KN ERP (Q56).
"""
from calendar import monthrange
from dataclasses import dataclass, field
from datetime import date

from django.db.models import Count, Max

from django.urls import reverse
from django.utils import timezone

from forms_builder.models import DataRecord, TableDef
from forms_builder.services import folder_service, grant_service
from orders.constants import is_waybill_table

from .sidebar_service import date_column

#: Nhãn quyền của người xem trên một bảng — lớp CSS tính ở đây vì bài quét
#: lớp CSS không đọc điều kiện trong template.
QUYEN_SUA = ("Sửa", "chip chip-nhan")
QUYEN_XEM = ("Xem", "chip")


@dataclass(frozen=True)
class Month:
    year: int
    month: int
    count: int = 0

    @property
    def key(self):
        return f"{self.year:04d}-{self.month:02d}"

    @property
    def label(self):
        return f"Tháng {self.month}/{self.year}"

    @property
    def first(self):
        return date(self.year, self.month, 1)

    @property
    def last(self):
        return date(self.year, self.month, monthrange(self.year, self.month)[1])


def today():
    return timezone.localdate()


# ── Dữ liệu ──────────────────────────────────────────────────────────

def all_tables(user):
    """Bảng KN CRM phục vụ trong phạm vi (chỉ vận đơn — ADR-040), kèm bộ phận
    và cột — hai truy vấn cho cả trang."""
    from . import catalog
    return list(
        catalog.chi_van_don(TableDef.objects.in_scope(user))
        .select_related("department")
        .prefetch_related("columns")
        .order_by("name")
    )


def departments_of(user, tables=None):
    """Bộ phận có ít nhất một bảng trong phạm vi, theo tên. Admin thấy mọi bộ
    phận có bảng; người được cấp quyền xem bảng của bộ phận khác thấy cả bộ
    phận đó (chỉ với bảng được cấp)."""
    tables = all_tables(user) if tables is None else tables
    theo_pk = {}
    for t in tables:
        theo_pk.setdefault(t.department_id, t.department)
    return sorted(theo_pk.values(), key=lambda d: d.name)


def tables_of(user, department, tables=None):
    """Bảng của một bộ phận trong phạm vi, kèm cột."""
    tables = all_tables(user) if tables is None else tables
    return [t for t in tables if t.department_id == department.pk]


def _records(user, department):
    return DataRecord.objects.in_scope(user).filter(
        table__department=department, table__deleted_at__isnull=True,
    )


def table_stats(user, department):
    """`{bảng_id: (tổng dòng, cập nhật gần nhất)}` — một truy vấn."""
    dong = (
        _records(user, department)
        .values("table_id")
        .annotate(n=Count("id"), moc=Max("updated_at"))
        .order_by()
    )
    return {d["table_id"]: (d["n"], d["moc"]) for d in dong}


# ── Liên kết ─────────────────────────────────────────────────────────

def home_url(department=None, quarter=None, month=None, *, all_tables=False):
    """Địa chỉ trang thư mục (mục Bảng tính) mở đúng bộ phận — ADR-015.

    `quarter`/`month`/`all_tables` giữ trong chữ ký cho chỗ gọi cũ nhưng
    không sinh tham số nữa: cấp Quý ▸ Tháng đã bỏ (ADR-040)."""
    if department is not None:
        return reverse("thu_muc") + f"?bp={department.code}"
    return reverse("thu_muc")


def grid_url(table, month=None):
    """Địa chỉ lưới của bảng (tham số `month` đã bỏ theo ADR-040)."""
    return reverse("bang_tinh_xem", args=[table.code])


def month_of_params(params, columns):
    """Bộ lọc khoảng ngày trên URL đúng trọn một tháng thì trả `Month`, không
    thì None — để thanh trên của lưới ghi "Tháng 9/2026" và nút ← mở đúng nhánh."""
    cot = date_column(columns)
    if cot is None:
        return None
    try:
        tu = date.fromisoformat(params.get(f"f_{cot.code}__lon_bang", ""))
        den = date.fromisoformat(params.get(f"f_{cot.code}__nho_bang", ""))
    except ValueError:
        return None
    m = Month(tu.year, tu.month)
    return m if tu == m.first and den == m.last else None


# ── Toàn bộ trang ────────────────────────────────────────────────────

def permission_label(user, table):
    """Nhãn quyền của người xem trên bảng: Sửa hay Xem (ADR-012, Q56)."""
    if grant_service.can_create_record(user, table) and not grant_service.is_grid_only(table):
        return QUYEN_SUA
    return QUYEN_XEM


def _dong_bang(user, table, *, so_dong, cap_nhat):
    quyen, lop = permission_label(user, table)
    from forms_builder.services.lifecycle_service import can_delete as may_delete
    can_delete=may_delete(user,table)
    return {
        "can_delete":can_delete, "bang": table, "so_dong": so_dong, "cap_nhat": cap_nhat,
        "can_download_template": is_waybill_table(table) and grant_service.can_import(user, table),
        "quyen": quyen, "lop_quyen": lop,
        "url": grid_url(table),
    }


def build(user, *, bp_code="", hom_nay=None):
    """Toàn bộ dữ liệu của trang thư mục. Trả None nếu người này không thấy
    bảng nào; ném `LookupError` nếu `bp` ngoài phạm vi (view trả 404, quy tắc 8).

    Từ ADR-040 (24.09.2026) không còn cấp Quý ▸ Tháng: trang liệt kê thẳng
    các bảng (chỉ vận đơn) theo thư mục; lọc thời gian là việc của bộ lọc
    trên lưới."""
    moi_bang = all_tables(user)
    cac_bp = departments_of(user, moi_bang)
    if not cac_bp:
        return None
    theo_ma = {b.code: b for b in cac_bp}
    if bp_code and bp_code not in theo_ma:
        raise LookupError(bp_code)
    ho_so = getattr(user, "profile", None)
    bp = theo_ma.get(bp_code) or next(
        (b for b in cac_bp if ho_so is not None and b.pk == ho_so.department_id), cac_bp[0]
    )

    bang = tables_of(user, bp, moi_bang)
    thong_ke = table_stats(user, bp)
    cay = [(tm, ds) for tm, ds in folder_service.tree(user)
           if any(b.department_id == bp.pk for b in ds) or (tm is not None and tm.department_id == bp.pk)]
    cac_nhom = [{
        "ten": tm.name if tm is not None else ("Không thư mục" if len(cay) > 1 else ""),
        "cac_bang": [
            _dong_bang(user, t, so_dong=thong_ke.get(t.pk, (0, None))[0],
                       cap_nhat=thong_ke.get(t.pk, (0, None))[1])
            for t in ds if t.department_id == bp.pk
        ],
    } for tm, ds in cay]
    cac_nhom = [n for n in cac_nhom if n["cac_bang"] or n["ten"]]

    cac_bo_phan = [{
        "bp": b, "dang_chon": b.pk == bp.pk,
        "lop": "crm-bp-ten on" if b.pk == bp.pk else "crm-bp-ten",
        "url": home_url(b),
        "so_bang": len(bang) if b.pk == bp.pk else "",
    } for b in cac_bp]

    return {
        "bp": bp, "thang": None, "cac_bo_phan": cac_bo_phan,
        "cac_nhom": cac_nhom, "tieu_de": bp.name,
        "mo_ta": "Các bảng vận đơn trong phạm vi của bạn. Lọc theo thời gian ngay trên lưới.",
        "rong_mo_ta": "Bộ phận này chưa có bảng nào bạn được xem.",
        "nhan_nut": "Bảng tính",
    }
