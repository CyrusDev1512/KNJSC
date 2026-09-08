"""Những chỗ sửa để KN CRM chịu được 100 nghìn dòng và 100 người (K27, ADR-016).

Bài đo tải thật nằm ở `manage.py do_hieu_nang` và `tests/perf/locustfile_kn_crm.py`
(AC-10.8, thủ công). Ở đây chỉ khoá **hình dạng** của các đường đã sửa: số lệnh
truy vấn không phình theo số ô, URL ô ghép chuỗi khớp `reverse()`, cột Trùng
đếm đúng theo trang, tính lại cột chạy nền trên bảng lớn.
"""
import pytest
from django.urls import reverse

from core.constants import JobKind, JobStatus
from core.models import BackgroundJob
from crm.services import grid_service
from forms_builder.models import ColumnDef, DataRecord, TableDef
from forms_builder.services import record_service, table_service
from forms_builder.tests.test_bang_dong import *  # noqa: F401,F403 — fixture bang_mkt
from orders.services import dispatch_service

pytestmark = pytest.mark.django_db


@pytest.fixture
def bang_vd(departments, nguoi_dung):
    return dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])


def _dong_vd(bang, nguoi, i, sdt):
    return record_service.create_record(bang, {
        "ma_don": f"T{i:04d}", "ten_khach": f"Khách {i}", "so_dien_thoai": sdt, "gia_tien": "10",
    }, actor=nguoi)


def test_url_o_ghep_chuoi_khop_reverse(bang_vd, nguoi_dung):
    """AC-11.36 — URL sửa ô ghép chuỗi (`cell_url`) khớp `reverse('bang_tinh_o')`; lưới 100 dòng vẫn ≤ 14 truy vấn"""
    nv = nguoi_dung["staff_vd"]
    d = _dong_vd(bang_vd, nv, 1, "0901")
    goc = grid_service.grid_url(bang_vd)
    assert grid_service.cell_url(goc, d.pk, "ghi_chu") == reverse("bang_tinh_o", args=[bang_vd.code, d.pk, "ghi_chu"])
    assert goc == reverse("bang_tinh_xem", args=[bang_vd.code])
    html = grid_service.cell_html(bang_vd, d, bang_vd.columns.get(code="ten_khach"), gia_tri="A <b>", hien=None,
                                  duoc_sua=True, lop="o-sua", goc=goc)
    assert 'data-goc="A &lt;b&gt;"' in html and f'data-sua-url="{goc}o/{d.pk}/ten_khach/"' in html
    ma_don = bang_vd.columns.get(code="ma_don")
    html = grid_service.cell_html(bang_vd, d, ma_don, gia_tri="T 1", hien=None, duoc_sua=False, lop="o-xem",
                                  qs_giu="tim=a", goc=goc)
    assert 'o-khoa-loc' in html and f'href="{goc}?tim=a&amp;f_ma_don=T%201"' in html and "data-sua-url" not in html


def test_luoi_100_dong_ngan_sach_truy_van(client, bang_vd, nguoi_dung, django_assert_max_num_queries, settings):
    """AC-11.36 — Lưới 100 dòng (3.900 ô) ≤ 13 truy vấn, không truy vấn theo ô hay theo dòng; `trung=1` chỉ trả dòng có số điện thoại trùng, cột Trùng đếm đúng theo trang"""
    settings.GRID_ONLY_TABLES = set()                      # như dịch vụ 8021 chạy thật
    nv = nguoi_dung["staff_vd"]
    for i in range(100):
        _dong_vd(bang_vd, nv, i, "0900" if i % 10 == 0 else f"09{i:06d}")
    client.force_login(nv)
    client.get(f"/bang-tinh/{bang_vd.code}/moi-nhat/")       # lượt đầu ghi mốc phiên (middleware), không tính
    with django_assert_max_num_queries(13):
        kq = client.get(f"/bang-tinh/{bang_vd.code}/")
    assert kq.status_code == 200 and kq.content.count(b"data-sua-url=") >= 100 * 30
    with django_assert_max_num_queries(13):
        kq = client.get(f"/bang-tinh/{bang_vd.code}/?trung=1")
    assert kq.status_code == 200
    dong = grid_service.attach_duplicate_counts(bang_vd, DataRecord.objects.filter(table=bang_vd).order_by("pk")[:20])
    assert [d.so_trung for d in dong] == [10 if i % 10 == 0 else 1 for i in range(20)]
    assert sorted(grid_service.duplicate_phones(bang_vd).values_list("val_phone", flat=True)) == ["0900"]
    import re
    assert len(re.findall(rb'<tr [^>]*data-dong="\d+"', kq.content)) == 10          # đúng 10 dòng trùng


def test_dan_500_o_va_moi_nhat_ngan_sach_truy_van(client, bang_vd, nguoi_dung, django_assert_max_num_queries, settings):
    """AC-11.36 — Dán 500 ô (100 dòng × 5 cột) ghi bằng bulk_update: ≤ 25 truy vấn thay vì mỗi dòng một UPDATE; `moi-nhat/` ≤ 8 truy vấn, không COUNT toàn bảng"""
    settings.GRID_ONLY_TABLES = set()
    nv = nguoi_dung["staff_vd"]
    dong = [_dong_vd(bang_vd, nv, i, f"09{i:06d}") for i in range(100)]
    client.force_login(nv)
    client.get(f"/bang-tinh/{bang_vd.code}/moi-nhat/")       # lượt đầu ghi mốc phiên, không tính
    o, gt = [], []
    for d in dong:
        for cot in ("ghi_chu", "thanh_pho", "bang", "zipcode", "pttt"):
            o.append(f"{d.pk}:{cot}")
            gt.append(f"x {d.pk}")
    with django_assert_max_num_queries(25):
        kq = client.post(f"/bang-tinh/{bang_vd.code}/luu-o/", {"o": o, "gt": gt})
    assert kq.status_code == 200, kq.content[:200]
    assert DataRecord.objects.get(pk=dong[7].pk).data["zipcode"] == f"x {dong[7].pk}"
    with django_assert_max_num_queries(8):
        kq = client.get(f"/bang-tinh/{bang_vd.code}/moi-nhat/")
    assert kq.status_code == 200 and "so" not in kq.json()


def test_tinh_lai_cot_bang_lon_chay_nen(client, bang_mkt, nguoi_dung, monkeypatch):
    """AC-11.35 — Đổi cột tính sẵn trên bảng nhiều hơn RECOMPUTE_SYNC_MAX_ROWS dòng thì tính lại ở tác vụ nền (BackgroundJob "Tính lại cột"): cột hiện ngay, `moi-nhat/` báo tiến độ khi đang chạy, giá trị đúng khi xong; bảng nhỏ tính ngay không có tác vụ"""
    ql = nguoi_dung["manager_mkt"]
    for i in range(1, 6):
        record_service.create_record(bang_mkt, {"ngay": "2026-09-01", "cpqc": str(100 * i), "so_don": str(i)}, actor=ql)
    # Bảng nhỏ: tính ngay
    cot = table_service.add_column(bang_mkt, name="Gấp đôi", code="gap_doi", field_type="money", order=20,
                                   is_computed=True, compute_op="multiply", compute_left="cpqc", compute_right="so_don",
                                   actor=ql)
    assert getattr(cot, "resync_job", None) is None
    assert not BackgroundJob.objects.filter(kind=JobKind.RECOMPUTE).exists()
    assert {d.data["gap_doi"] for d in DataRecord.objects.filter(table=bang_mkt)} == {"100.00", "400.00", "900.00", "1600.00", "2500.00"}

    # Bảng "lớn": ngưỡng hạ xuống 2 dòng — chạy nền (kiểm thử chạy eager nên xong ngay)
    monkeypatch.setattr(table_service, "RECOMPUTE_SYNC_MAX_ROWS", 2)
    table_service.update_column(cot, {"compute_op": "add"}, actor=ql)
    job = BackgroundJob.objects.get(kind=JobKind.RECOMPUTE, target_id=bang_mkt.code)
    assert job.status == JobStatus.DONE and job.total == 5 and job.progress == 5 and job.summary["da_tinh"] == 5
    assert {d.data["gap_doi"] for d in DataRecord.objects.filter(table=bang_mkt)} == {"101.00", "202.00", "303.00", "404.00", "505.00"}

    # Đang chạy thì moi-nhat/ báo tiến độ; xong thì hết
    client.force_login(ql)
    goc = f"/bang-tinh/{bang_mkt.code}/"
    assert client.get(f"{goc}moi-nhat/").json()["tinh_lai"] is None
    dang = BackgroundJob.objects.create(kind=JobKind.RECOMPUTE, status=JobStatus.RUNNING, created_by=ql,
                                        target_type="table", target_id=bang_mkt.code, total=5, progress=2)
    assert client.get(f"{goc}moi-nhat/").json()["tinh_lai"] == {"pk": dang.pk, "progress": 2, "total": 5}
    dang.mark_done()
    assert client.get(f"{goc}moi-nhat/").json()["tinh_lai"] is None

    # Màn Sửa cột nói rõ có tác vụ nền
    kq = client.post(f"/bang/{bang_mkt.code}/cot/", {
        "name": "Gấp ba", "code": "gap_ba", "field_type": "money", "order": "21", "is_computed": "on",
        "compute_op": "multiply", "compute_left": "cpqc", "compute_right": "so_don", "compute_decimals": "2",
    }, follow=True)
    assert kq.status_code == 200 and "tác vụ nền" in kq.content.decode()
    assert BackgroundJob.objects.filter(kind=JobKind.RECOMPUTE, target_id=bang_mkt.code, status=JobStatus.DONE).count() == 3
    assert ColumnDef.objects.filter(table=bang_mkt, code="gap_ba").exists()
