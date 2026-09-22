"""Xoá dữ liệu giả theo lô — TL-43.

Bản cũ xoá cả 50.000 dòng trong **một** lệnh `DELETE`: có lần đứng hơn 17 phút vì
chờ khoá, màn hình không in gì nên người chạy tưởng máy chết. Nay mỗi lô là một
giao dịch ngắn có hạn chờ khoá, và có tiến độ.

Bài dùng đúng vài dòng chứ không phải 50.000: cái cần khoá là **cách xoá** (chia lô,
xoá con trước cha, báo tiến độ), không phải tốc độ.
"""
import pytest

from core.management.commands import seed_perf
from forms_builder.models import DataRecord
from orders.models import WaybillAssignment, WaybillItem
from orders.services import dispatch_service, product_service

pytestmark = pytest.mark.django_db


@pytest.fixture
def dong_gia(nguoi_dung, settings):
    """Năm dòng mang mã `PERF-*` trên bảng vận đơn, dòng đầu có chi tiết và phân công —
    dựng đúng như `seed_perf` và `nap_khach_mau` dựng: bản ghi cộng hai bảng con, **không**
    qua `order_service` nên không có `Order` đi kèm."""
    settings.GRID_ONLY_TABLES = set()
    bang = dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])
    san_pham = product_service.create_product(name="Hàng đo tải", actor=nguoi_dung["admin"])

    dong = [DataRecord.objects.create(
        table=bang, created_by=nguoi_dung["admin"], department=bang.department,
        data={"ma_don": f"{seed_perf.PERF_PREFIX}{i:05d}", "ten_khach": f"Giả {i}"},
    ) for i in range(1, 6)]

    WaybillItem.objects.create(record=dong[0], product=san_pham, quantity=1,
                               unit_price="1.00", paid_amount="0.00")
    WaybillAssignment.objects.create(record=dong[0], delivery=nguoi_dung["staff_vd"], version=1)
    return bang


def test_xoa_du_lieu_gia_theo_lo_co_tien_do(dong_gia, monkeypatch):
    """AC-10.10 — `seed_perf.clear()` xoá theo lô, gọi `on_progress` từng lô, xoá cả chi tiết
    và phân công của dòng; không sót dòng `PERF-*` nào"""
    bang = dong_gia
    monkeypatch.setattr(seed_perf, "DELETE_BATCH_SIZE", 2)   # 5 dòng → 3 lô
    truoc = DataRecord.all_objects.filter(
        table=bang, data__ma_don__startswith=seed_perf.PERF_PREFIX).count()
    assert truoc == 5
    assert WaybillItem._base_manager.filter(record__table=bang).exists()

    buoc = []
    so = seed_perf.clear(on_progress=lambda da, tong: buoc.append((da, tong)))

    assert so == 5
    assert not DataRecord.all_objects.filter(
        table=bang, data__ma_don__startswith=seed_perf.PERF_PREFIX).exists()
    assert not WaybillItem._base_manager.filter(record__table=bang).exists(), "chi tiết phải đi theo dòng"
    assert not WaybillAssignment.objects.filter(record__table=bang).exists(), "phân công phải đi theo dòng"

    assert [da for da, _ in buoc] == [2, 4, 5], f"phải báo tiến độ từng lô, nhận {buoc}"
    assert all(tong == 5 for _, tong in buoc)


def test_xoa_khong_dung_dong_that(dong_gia, nguoi_dung):
    """AC-10.10 — Dòng nghiệp vụ thật (mã đơn không phải `PERF-*`) không bị xoá lây"""
    bang = dong_gia
    that = DataRecord.objects.create(
        table=bang, created_by=nguoi_dung["admin"], department=bang.department,
        data={"ma_don": "DH-2209-9999", "ten_khach": "Khách thật"},
    )

    seed_perf.clear()

    assert DataRecord.objects.filter(pk=that.pk).exists()
    assert DataRecord.objects.get(pk=that.pk).data["ten_khach"] == "Khách thật"


def test_moi_lo_dat_han_cho_khoa(dong_gia, monkeypatch):
    """AC-10.10 — Mỗi lô là một giao dịch riêng có `SET LOCAL lock_timeout`; bỏ dòng đó đi
    là mất chính cái chặn treo của TL-43, nên bài này canh nó theo từng lô"""
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    monkeypatch.setattr(seed_perf, "DELETE_BATCH_SIZE", 2)   # 5 dòng → 3 lô
    with CaptureQueriesContext(connection) as ctx:
        seed_perf.clear()
    dat_han = [q["sql"] for q in ctx.captured_queries if "lock_timeout" in q["sql"]]
    assert len(dat_han) == 3, f"phải một lần đặt hạn chờ khoá cho mỗi lô, thấy {len(dat_han)}"


def test_het_han_cho_khoa_bao_ro_da_xoa_bao_nhieu(dong_gia, monkeypatch):
    """AC-10.10 — Hết hạn chờ khoá thì lỗi nói rõ đã xoá được bao nhiêu dòng, thay vì
    ném nguyên lỗi Postgres trần"""
    from django.db.utils import OperationalError

    from django.db.models.query import QuerySet

    monkeypatch.setattr(seed_perf, "DELETE_BATCH_SIZE", 2)
    goc = QuerySet._raw_delete
    dem = {"lan": 0}

    def gia_vo_het_han(self, using):
        # Lô đầu (3 lượt _raw_delete: chi tiết, phân công, bản ghi) cho qua;
        # sang lô hai thì giả vờ Postgres hết hạn chờ khoá
        dem["lan"] += 1
        if dem["lan"] > 3:
            raise OperationalError("canceling statement due to lock timeout")
        return goc(self, using)

    # Vá ở lớp QuerySet gốc để bắt cả ba queryset (chi tiết, phân công, bản ghi)
    monkeypatch.setattr(QuerySet, "_raw_delete", gia_vo_het_han)
    with pytest.raises(OperationalError, match=r"được 2/5 dòng"):
        seed_perf.clear()


def test_nap_khach_mau_cung_di_duong_xoa_theo_lo(dong_gia, nguoi_dung, monkeypatch):
    """AC-10.10 — `nap_khach_mau.clear()` đi cùng đường xoá theo lô: bộ 375.000 dòng KH-*
    không còn là một lệnh DELETE trần như cái treo TL-43 mô tả"""
    from orders.management.commands import nap_khach_mau

    bang = dong_gia
    for i in range(1, 4):
        DataRecord.objects.create(
            table=bang, created_by=nguoi_dung["admin"], department=bang.department,
            data={"ma_don": f"{nap_khach_mau.PREFIX}{i:05d}", "ten_khach": f"KH {i}"},
        )
    monkeypatch.setattr(seed_perf, "DELETE_BATCH_SIZE", 2)
    buoc = []
    so = nap_khach_mau.clear(bang.code, on_progress=lambda da, tong: buoc.append((da, tong)))
    assert so == 3
    assert [da for da, _ in buoc] == [2, 3]
    assert not DataRecord.all_objects.filter(
        table=bang, data__ma_don__startswith=nap_khach_mau.PREFIX).exists()
    # Dòng PERF-* của fixture không bị xoá lây
    assert DataRecord.all_objects.filter(
        table=bang, data__ma_don__startswith=seed_perf.PERF_PREFIX).count() == 5
