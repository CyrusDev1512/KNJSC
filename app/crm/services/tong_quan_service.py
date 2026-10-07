"""Số liệu cho **Trang chủ KN CRM** (tổng quan) — ADR-015, AC-11.31.

Theo mẫu `dashboard_service` của KN ERP: mỗi khối chạy trong lớp bọc riêng,
một khối hỏng thì báo "tạm chưa khả dụng", khối khác vẫn hiện. Mọi số liệu
đi qua manager `in_scope` (quy tắc 11): Staff chỉ đếm dòng của mình, Leader
cả team, Manager cả bộ phận.
"""
import logging
from datetime import datetime, time, timedelta

from django.db.models import Count, Max, Q
from django.urls import reverse
from django.utils import timezone

from core.models import AuditLog
from forms_builder.models import DataRecord, TableDef
from orders.constants import waybill_condition

logger = logging.getLogger(__name__)


def _khoi(ten, ham):
    try:
        return {"ok": True, "data": ham()}
    except Exception:
        logger.exception("Khối Trang chủ KN CRM '%s' lỗi", ten)
        return {"ok": False, "data": None}


def _bang_van_don():
    """Mọi bảng vận đơn đang dùng — ít (thường một), nên đếm từng bảng theo phạm vi riêng của bảng đó."""
    return list(TableDef.objects.filter(waybill_condition(""), is_active=True).order_by("name"))


def _dem_bang(user, bang, nho):
    """Số dòng trong phạm vi, số dòng tạo tháng này / hôm nay và mốc sửa mới nhất của một bảng — một truy vấn, nhớ
    trong `nho` để hai khối của trang chủ dùng chung. `in_scope(user, table=...)` cho cùng tập dòng với
    `in_scope(user).filter(table=...)` (`test_master_nine`) nhưng đi nhánh gọn cho bảng vận đơn (AC-10.24).
    Mốc ngày giờ Việt Nam thành khoảng thời gian: so thẳng `created_at` dùng được chỉ mục, cùng nghĩa với `__date`."""
    if bang.pk not in nho:
        hom_nay = timezone.localdate()
        luc = lambda ngay: timezone.make_aware(datetime.combine(ngay, time.min))
        nho[bang.pk] = DataRecord.objects.in_scope(user, table=bang).aggregate(
            n=Count("id"), moc=Max("updated_at"),
            thang=Count("id", filter=Q(created_at__gte=luc(hom_nay.replace(day=1)))),
            hom_nay=Count("id", filter=Q(created_at__gte=luc(hom_nay), created_at__lt=luc(hom_nay + timedelta(days=1)))))
    return nho[bang.pk]


def _bang_trong_pham_vi(user, nho):
    """Bảng vận đơn trong phạm vi (cả bảng đang tắt, như số "Bảng" cũ) — một truy vấn, hai khối dùng chung."""
    if "bang" not in nho:
        nho["bang"] = list(TableDef.objects.in_scope(user).filter(waybill_condition(""))
                           .select_related("department").order_by("name"))
    return nho["bang"]


def _so_lieu(user, nho):
    """Bốn ô số: dòng nhập tháng này, dòng hôm nay, số bảng, tổng dòng — theo
    lúc tạo (`created_at`, giờ Việt Nam) để bảng không có cột Ngày vẫn đếm được."""
    hom_nay = timezone.localdate()
    # KN CRM chỉ phục vụ bảng vận đơn (ADR-040) — số liệu trang chủ cũng vậy
    dem = {"so_dong": 0, "dong_thang": 0, "dong_hom_nay": 0}
    for bang in _bang_van_don():
        d = _dem_bang(user, bang, nho)
        dem["so_dong"] += d["n"]
        dem["dong_thang"] += d["thang"]
        dem["dong_hom_nay"] += d["hom_nay"]
    return {
        **dem,
        "so_bang": len(_bang_trong_pham_vi(user, nho)),
        "thang": hom_nay.month, "nam": hom_nay.year,
    }


def _bang_gan_day(user, nho):
    """Bảng trong phạm vi, mới cập nhật trước; kèm số dòng và địa chỉ lưới.

    Trước đây một truy vấn `COUNT(DISTINCT)` + `MAX` qua `records__pk__in=<phạm vi>` trên mọi dòng: 150–258 giây ở
    385.000 dòng. Nay đếm từng bảng (thường một) theo phạm vi của bảng đó; thứ tự giữ như cũ."""
    cac_bang = list(_bang_trong_pham_vi(user, nho))
    for b in cac_bang:
        d = _dem_bang(user, b, nho) if b.is_active else {"n": 0, "moc": None}
        b.so_dong, b.cap_nhat = d["n"], d["moc"]

    def thu_tu(b):
        # Như `ORDER BY cap_nhat DESC, name` của Postgres: mốc rỗng (bảng chưa có dòng) đứng đầu, rồi mốc mới trước;
        # sort ổn định nên cùng mốc vẫn theo tên như truy vấn trên
        return (0, 0) if b.cap_nhat is None else (1, -b.cap_nhat.timestamp())

    cac_bang = sorted(cac_bang, key=thu_tu)[:6]
    for b in cac_bang:
        b.url = reverse("bang_tinh_xem", args=[b.code])
    return cac_bang


#: Hoạt động gần đây đọc theo lô, tối đa bấy nhiêu lô — đủ 8 mục là dừng
HOAT_DONG_LO, HOAT_DONG_TOI_DA_LO = 200, 20


def _hoat_dong(user):
    """Hoạt động gần đây — chỉ việc trên bảng vận đơn (ADR-040, chủ dự án chốt
    24.09.2026): dòng, bảng/cột vận đơn và đơn gốc; việc trên bảng MKT/Sale bên
    ERP không hiện ở trang chủ KN CRM.

    Trước đây so `target_id` với mọi mã dòng vận đơn đã chuyển thành chữ (385.000 mã, 1,3 s). Nay đọc nhật ký mới
    nhất theo lô rồi hỏi đúng những mã trong lô có thuộc bảng vận đơn không (AC-10.24)."""
    from forms_builder.models import ColumnDef
    nguon = {"DataRecord": DataRecord.all_objects.filter(waybill_condition()),
             "TableDef": TableDef.objects.filter(waybill_condition("")),
             "ColumnDef": ColumnDef.objects.filter(waybill_condition())}
    ds = (AuditLog.objects.in_scope(user).filter(target_type__in=[*nguon, "Order"])
          .select_related("actor").order_by("-created_at", "-pk"))
    ket_qua = []
    for i in range(HOAT_DONG_TOI_DA_LO):
        lo = list(ds[i * HOAT_DONG_LO:(i + 1) * HOAT_DONG_LO])
        if not lo:
            break
        thuoc = {}
        for loai, qs in nguon.items():
            ma = {int(a.target_id) for a in lo if a.target_type == loai and str(a.target_id).isdigit()}
            thuoc[loai] = {str(pk) for pk in qs.filter(pk__in=ma).values_list("pk", flat=True)} if ma else set()
        for a in lo:
            if a.target_type == "Order" or str(a.target_id) in thuoc.get(a.target_type, ()):
                ket_qua.append(a)
                if len(ket_qua) == 8:
                    return ket_qua
    return ket_qua


def tong_quan(user):
    nho = {}        # số đếm từng bảng, hai khối dùng chung
    return {
        "so_lieu": _khoi("so_lieu", lambda: _so_lieu(user, nho)),
        "bang": _khoi("bang", lambda: _bang_gan_day(user, nho)),
        "hoat_dong": _khoi("hoat_dong", lambda: _hoat_dong(user)),
    }
