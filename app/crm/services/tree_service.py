"""Cây trang chủ KN CRM: Bộ phận ▸ Quý ▸ Tháng ▸ bảng — ADR-012.

Tháng là **góc nhìn** trên một bảng, không phải bảng riêng (backlog Q55): nút
tháng mở lưới với `f_<cột Ngày>__lon_bang` và `__nho_bang` đúng ngày đầu và
cuối tháng — cùng tham số thanh bên đang dùng (ADR-010 mục 5), nên chip, phân
trang và Tải Excel hiểu ngay.

Cây chỉ dựng từ `in_scope` (quy tắc 11): bảng nào người này không được xem thì
nhánh đó không có; quyền theo bảng do Manager cấp ở KN ERP (Q56). Số dòng
theo tháng đếm trên cột tách `DataRecord.val_date` (có chỉ mục) qua **một truy
vấn cho cả bộ phận**, không phải mỗi bảng một lệnh — trần 10 lệnh (AC-10.2).
"""
from calendar import monthrange
from dataclasses import dataclass, field
from datetime import date

from django.db.models import Count, Max
from django.db.models.functions import TruncMonth
from django.urls import reverse
from django.utils import timezone

from forms_builder.models import DataRecord, TableDef
from forms_builder.services import folder_service, grant_service

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


@dataclass(frozen=True)
class Quarter:
    year: int
    quarter: int
    months: tuple = field(default_factory=tuple)

    @property
    def key(self):
        return f"{self.year:04d}-{self.quarter}"

    @property
    def label(self):
        return f"Quý {self.quarter}/{self.year}"

    @property
    def count(self):
        return sum(m.count for m in self.months)


def quarter_of(d):
    return d.year, (d.month - 1) // 3 + 1


def parse_month(raw):
    """`"2026-09"` → `(2026, 9)`; sai dạng thì None."""
    try:
        nam, thang = raw.split("-")
        nam, thang = int(nam), int(thang)
    except (AttributeError, ValueError):
        return None
    return (nam, thang) if 1 <= thang <= 12 and 2000 <= nam <= 2100 else None


def parse_quarter(raw):
    """`"2026-3"` → `(2026, 3)`; sai dạng thì None."""
    try:
        nam, quy = raw.split("-")
        nam, quy = int(nam), int(quy)
    except (AttributeError, ValueError):
        return None
    return (nam, quy) if 1 <= quy <= 4 and 2000 <= nam <= 2100 else None


def today():
    return timezone.localdate()


# ── Dữ liệu ──────────────────────────────────────────────────────────

def all_tables(user):
    """Mọi bảng trong phạm vi, kèm bộ phận và cột — hai truy vấn cho cả trang."""
    return list(
        TableDef.objects.in_scope(user)
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


def month_counts(user, department):
    """`{(bảng_id, năm, tháng): số dòng}` theo cột Ngày — một truy vấn."""
    dong = (
        _records(user, department)
        .filter(val_date__isnull=False)
        .annotate(thang=TruncMonth("val_date"))
        .values("table_id", "thang")
        .annotate(n=Count("id"))
        .order_by()
    )
    return {(d["table_id"], d["thang"].year, d["thang"].month): d["n"] for d in dong}


def table_stats(user, department):
    """`{bảng_id: (tổng dòng, cập nhật gần nhất)}` — một truy vấn."""
    dong = (
        _records(user, department)
        .values("table_id")
        .annotate(n=Count("id"), moc=Max("updated_at"))
        .order_by()
    )
    return {d["table_id"]: (d["n"], d["moc"]) for d in dong}


def quarters(dem, *, hom_nay=None):
    """Từ bảng đếm theo tháng dựng danh sách Quý (mới trước), mỗi quý đủ ba
    tháng; quý hiện tại luôn có dù trống."""
    hom_nay = hom_nay or today()
    theo_thang = {}
    for (_, nam, thang), n in dem.items():
        theo_thang[(nam, thang)] = theo_thang.get((nam, thang), 0) + n
    cac_quy = {quarter_of(date(nam, thang, 1)) for nam, thang in theo_thang}
    cac_quy.add(quarter_of(hom_nay))
    ket_qua = []
    for nam, quy in sorted(cac_quy, reverse=True):
        thang_dau = (quy - 1) * 3 + 1
        months = tuple(
            Month(nam, t, theo_thang.get((nam, t), 0))
            for t in range(thang_dau + 2, thang_dau - 1, -1)      # mới trước, như quý
        )
        ket_qua.append(Quarter(nam, quy, months))
    return ket_qua


# ── Liên kết ─────────────────────────────────────────────────────────

def home_url(department=None, quarter=None, month=None, *, all_tables=False):
    """Địa chỉ trang thư mục (mục Bảng tính) với cây mở đúng nút — ADR-015."""
    cap = []
    if department is not None:
        cap.append(("bp", department.code))
    if month is not None:
        cap.append(("thang", month.key))
    elif quarter is not None:
        cap.append(("quy", quarter.key))
    if all_tables:
        cap.append(("tat-ca", "1"))
    duoi = "&".join(f"{k}={v}" for k, v in cap)
    return reverse("thu_muc") + ("?" + duoi if duoi else "")


def grid_url(table, month=None):
    """Địa chỉ lưới của bảng, lọc sẵn theo tháng nếu bảng có cột Ngày."""
    url = reverse("bang_tinh_xem", args=[table.code])
    cot = date_column(list(table.columns.all())) if month is not None else None
    if cot is None:
        return url
    return f"{url}?f_{cot.code}__lon_bang={month.first.isoformat()}&f_{cot.code}__nho_bang={month.last.isoformat()}"


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


def _dong_bang(user, table, *, so_dong, cap_nhat, month):
    quyen, lop = permission_label(user, table)
    co_ngay = date_column(list(table.columns.all())) is not None
    return {
        "bang": table, "so_dong": so_dong, "cap_nhat": cap_nhat,
        "quyen": quyen, "lop_quyen": lop, "khong_ngay": not co_ngay,
        "url": grid_url(table, month),
    }


def build(user, *, bp_code="", quy_raw="", thang_raw="", tat_ca=False, hom_nay=None):
    """Toàn bộ dữ liệu của trang chủ. Trả None nếu người này không thấy bảng
    nào; ném `LookupError` nếu `bp` ngoài phạm vi (view trả 404, quy tắc 8)."""
    hom_nay = hom_nay or today()
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

    dem = month_counts(user, bp)
    cac_quy = quarters(dem, hom_nay=hom_nay)
    thang_chon = parse_month(thang_raw)
    quy_chon = parse_quarter(quy_raw)
    if thang_chon is not None:
        quy_chon = quarter_of(date(thang_chon[0], thang_chon[1], 1))
    if not tat_ca and thang_chon is None and quy_chon is None:
        thang_chon = (hom_nay.year, hom_nay.month)
        quy_chon = quarter_of(hom_nay)
    if quy_chon is not None and quy_chon not in {(q.year, q.quarter) for q in cac_quy}:
        # Quý được gõ tay mà chưa có dữ liệu: vẫn mở, ba tháng trống
        cac_quy.append(Quarter(quy_chon[0], quy_chon[1], tuple(
            Month(quy_chon[0], t) for t in range((quy_chon[1] - 1) * 3 + 3, (quy_chon[1] - 1) * 3, -1))))
        cac_quy.sort(key=lambda q: (q.year, q.quarter), reverse=True)

    month = None
    if thang_chon is not None:
        for q in cac_quy:
            for m in q.months:
                if (m.year, m.month) == thang_chon:
                    month = m
    bang = tables_of(user, bp, moi_bang)
    thong_ke = table_stats(user, bp)

    if month is not None:
        cac_nhom = [{"ten": "", "cac_bang": [
            _dong_bang(user, t, so_dong=sum(n for (tid, y, mo), n in dem.items()
                                             if tid == t.pk and (y, mo) == (month.year, month.month)),
                       cap_nhat=thong_ke.get(t.pk, (0, None))[1], month=month)
            for t in bang if date_column(list(t.columns.all())) is not None
        ]}]
        tieu_de = f"{bp.name} · {month.label}"
        mo_ta = "Mỗi bảng mở với bộ lọc đúng tháng này. Bảng không có cột Ngày nằm ở Toàn bộ bảng."
        rong_mo_ta = "Chưa bảng nào của bộ phận này có cột Ngày, nên không xếp theo tháng được."
        nhan_nut = "Góc nhìn theo tháng"
    else:
        cay = [(tm, ds) for tm, ds in folder_service.tree(user)
               if any(b.department_id == bp.pk for b in ds) or (tm is not None and tm.department_id == bp.pk)]
        cac_nhom = [{
            "ten": tm.name if tm is not None else ("Không thư mục" if len(cay) > 1 else ""),
            "cac_bang": [
                _dong_bang(user, t, so_dong=thong_ke.get(t.pk, (0, None))[0],
                           cap_nhat=thong_ke.get(t.pk, (0, None))[1], month=None)
                for t in ds if t.department_id == bp.pk
            ],
        } for tm, ds in cay]
        cac_nhom = [n for n in cac_nhom if n["cac_bang"] or n["ten"]]
        tieu_de = f"{bp.name} · Toàn bộ bảng"
        mo_ta = "Mọi bảng của bộ phận trong phạm vi của bạn, không lọc thời gian."
        rong_mo_ta = "Bộ phận này chưa có bảng nào bạn được xem."
        nhan_nut = "Toàn bộ"

    cac_bo_phan = []
    for b in cac_bp:
        dang = b.pk == bp.pk
        quy_cua_b = []
        if dang:
            for q in cac_quy:
                q_chon = quy_chon == (q.year, q.quarter)
                quy_cua_b.append({
                    "label": q.label, "count": q.count, "dang_chon": q_chon,
                    "lop": "crm-quy-ten on" if q_chon else "crm-quy-ten",
                    "months": [{
                        "label": m.label, "count": m.count,
                        "dang_chon": month is not None and (m.year, m.month) == (month.year, month.month),
                        "lop": "crm-thang-lk on" if month is not None and (m.year, m.month) == (month.year, month.month) else "crm-thang-lk",
                        "url": home_url(b, q, m),
                    } for m in q.months],
                })
        cac_bo_phan.append({
            "bp": b, "dang_chon": dang, "quy": quy_cua_b,
            "lop": "crm-bp-ten on" if dang else "crm-bp-ten",
            "tat_ca_chon": dang and month is None,
            "lop_tat_ca": "crm-tat-ca on" if dang and month is None else "crm-tat-ca",
            "url_tat_ca": home_url(b, all_tables=True),
            "so_bang": len(bang) if dang else "",
        })

    return {
        "bp": bp, "thang": month, "quy": quy_chon, "cac_bo_phan": cac_bo_phan,
        "cac_nhom": cac_nhom, "tieu_de": tieu_de, "mo_ta": mo_ta,
        "rong_mo_ta": rong_mo_ta, "nhan_nut": nhan_nut,
    }
