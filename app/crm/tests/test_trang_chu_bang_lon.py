"""Trang chủ KN CRM hỏi nhẹ mà số liệu y nguyên — AC-10.24 (07.10.2026).

Ở 385.000 dòng vận đơn trang chủ (trang mở ra sau đăng nhập KN CRM) mất 150–258 giây: khối "Bảng gần đây" đếm
`COUNT(DISTINCT)` qua `records__pk__in=<phạm vi>` trên mọi dòng, khối "Hoạt động" so `target_id` với 385.000 mã dòng đã
chuyển thành chữ, ô số đếm theo `created_at::date` không dùng được chỉ mục. Nay đếm từng bảng vận đơn bằng phạm vi
theo bảng, lọc hoạt động theo lô, so mốc ngày bằng khoảng thời gian. Bài so với cách tính cũ (chép nguyên làm mốc).
"""
import pytest
from django.db import connection
from django.db.models import CharField, Count, Max, Q
from django.db.models.functions import Cast
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from core.models import AuditLog
from crm.services import tong_quan_service
from forms_builder.managers import record_count_scope
from forms_builder.models import ColumnDef, DataRecord, TableDef
from forms_builder.tests.test_pham_vi_bang_nhanh import the_gioi  # noqa: F401 — cùng thế giới dữ liệu
from orders.constants import waybill_condition

pytestmark = pytest.mark.django_db


def _cu(user):
    """Ba khối theo cách tính trước 07.10.2026, chép nguyên — mốc để so."""
    hom_nay = timezone.localdate()
    dau_thang = hom_nay.replace(day=1)
    so = DataRecord.objects.in_scope(user).filter(waybill_condition()).filter(table__deleted_at__isnull=True).aggregate(
        so_dong=Count("id"), dong_thang=Count("id", filter=Q(created_at__date__gte=dau_thang)),
        dong_hom_nay=Count("id", filter=Q(created_at__date=hom_nay)))
    so["so_bang"] = TableDef.objects.in_scope(user).filter(waybill_condition("")).count()
    allowed = record_count_scope(user)
    bang = [(b.pk, b.so_dong, b.cap_nhat) for b in TableDef.objects.in_scope(user).filter(waybill_condition(""))
            .annotate(so_dong=Count('records', filter=allowed, distinct=True), cap_nhat=Max('records__updated_at', filter=allowed))
            .order_by("-cap_nhat", "name")[:6]]
    ma = lambda qs: qs.annotate(ma=Cast("pk", CharField())).values("ma")
    ve = (Q(target_type="DataRecord", target_id__in=ma(DataRecord.all_objects.filter(waybill_condition())))
          | Q(target_type="TableDef", target_id__in=ma(TableDef.objects.filter(waybill_condition(""))))
          | Q(target_type="ColumnDef", target_id__in=ma(ColumnDef.objects.filter(waybill_condition())))
          | Q(target_type="Order"))
    hd = list(AuditLog.objects.in_scope(user).filter(ve).order_by("-created_at", "-pk").values_list("pk", flat=True)[:8])
    return so, bang, hd


def test_trang_chu_moi_trung_cach_cu_moi_vai(the_gioi):
    """AC-10.24 — Mọi vai: bốn ô số, danh sách "Bảng gần đây" (thứ tự, số dòng, mốc cập nhật) và tám hoạt động gần
    đây trùng đúng cách tính cũ"""
    for ten, user in the_gioi.items():
        so_cu, bang_cu, hd_cu = _cu(user)
        moi = tong_quan_service.tong_quan(user)
        so = moi["so_lieu"]["data"]
        assert {k: so[k] for k in so_cu} == so_cu, ten
        assert [(b.pk, b.so_dong, b.cap_nhat) for b in moi["bang"]["data"]] == bang_cu, ten
        assert [a.pk for a in moi["hoat_dong"]["data"]] == hd_cu, ten


def test_trang_chu_khong_dem_qua_join_tren_moi_dong(the_gioi):
    """AC-10.24 — Trang chủ không còn `COUNT(DISTINCT` qua bảng dòng, không chuyển mã dòng thành chữ để so hoạt động,
    không so ngày bằng `::date`"""
    with CaptureQueriesContext(connection) as q:
        tong_quan_service.tong_quan(the_gioi["staff_vd"])
    sql = " ".join(x["sql"] for x in q.captured_queries)
    assert "COUNT(DISTINCT" not in sql
    assert '"forms_builder_datarecord"."id")::varchar' not in sql and "::date" not in sql


def test_thong_ke_thu_muc_trung_cach_cu_moi_vai(the_gioi):
    """AC-10.25 — Số dòng và mốc cập nhật từng bảng ở trang thư mục trùng cách tính cũ (phạm vi chung lọc theo bộ
    phận) cho mọi vai và mọi bộ phận; vẫn một truy vấn đếm"""
    from crm.services import tree_service
    from org.models import Department
    for ten, user in the_gioi.items():
        for bp in Department.objects.all():
            cu = {d["table_id"]: (d["n"], d["moc"]) for d in DataRecord.objects.in_scope(user).filter(
                table__department=bp, table__deleted_at__isnull=True).values("table_id")
                .annotate(n=Count("id"), moc=Max("updated_at")).order_by()}
            assert tree_service.table_stats(user, bp) == cu, (ten, bp.code)


def test_so_dem_panel_bo_loc_trung_cach_cu_moi_vai(the_gioi):
    """AC-10.25 — Số đếm của panel Bộ lọc lưới (sản phẩm, thị trường, marketer) trùng cách tính cũ (phạm vi chung lọc
    theo bảng) cho mọi vai; nay đi phạm vi theo bảng"""
    from crm.services import grid_service, sidebar_service
    from orders.models import WaybillItem
    for code in ("van_don", "vd_mkt"):
        bang = TableDef.objects.get(code=code)
        cot = {c.code: c for c in bang.columns.all()}
        for ten, user in the_gioi.items():
            cu_sp = list(WaybillItem.objects.in_scope(user).filter(record__table=bang).order_by()
                         .values('product__code').annotate(n=Count('record_id', distinct=True)).order_by('product__code'))
            moi_sp = sidebar_service.product_options(user, bang, list(bang.columns.all()), _qd())["items"]
            assert [(i["product__code"], i["n"]) for i in cu_sp] == [(gt, n) for gt, _, n, _ in moi_sp], (ten, code)
            for ma in ("quoc_gia", "phu_trach_mkt"):
                if ma not in cot:
                    continue
                ds_cu = DataRecord.objects.in_scope(user).filter(table=bang)
                moi = grid_service.filter_options(user, bang, cot[ma])
                path, _ = grid_service._nguon_gia_tri(user, bang, cot[ma], queryset=ds_cu)
                cu = [((('__unassigned__' if ma == "phu_trach_mkt" else '') if h['gt'] is None else str(h['gt'])), h['n'])
                      for h in path.order_by().values("gt").annotate(n=Count("id")).order_by("-n", "gt")]
                assert moi == cu, (ten, code, ma)


def _qd():
    from django.http import QueryDict
    return QueryDict("")
