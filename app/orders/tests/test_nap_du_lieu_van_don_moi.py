from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from core.constants import AuditAction
from core.models import AuditLog
from forms_builder.models import DataRecord
from forms_builder.models import TableDef
from orders.constants import ACTIVE_WAYBILL_TABLE_CODE
from forms_builder.services import record_service
from orders.models import Customer, Order, OrderLine, Product, ProductGroup, WaybillAssignment, WaybillItem
from orders.services import dispatch_service, waybill_service


pytestmark = pytest.mark.django_db
PREFIX = "MAU-20260910-"


@pytest.fixture
def du_lieu_nap(nguoi_dung):
    nhom = ProductGroup.objects.create(name="Mỹ phẩm thử nghiệm")
    products = [
        Product.objects.create(name="Retinol Cream", code="retinol-cream", group=nhom),
        Product.objects.create(name="Vitamin C Serum", code="vitamin-c-serum", group=nhom),
        Product.objects.create(name="Sữa rửa mặt", code="sua-rua-mat", group=nhom),
    ]
    dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])
    table = TableDef.objects.get(code=ACTIVE_WAYBILL_TABLE_CODE)
    rows = []
    for i in range(1, 3):
        rows.append(record_service.create_record(table, {
            "ma_don": f"{PREFIX}{i:04d}",
            "ten_khach": f"Khách cũ {i}",
            "so_dien_thoai": f"+1 416 555 01{i:02d}",
            "ngay": "2026-09-10",
            "loai_tien": "CAD",
            "ghi_chu": "D??? li???u hỏng",
            waybill_service.DETAIL_CODE: [{
                "product": products[0].code,
                "quantity": 1,
                "unit_price": "0.00",
                "paid_amount": "0.00",
            }],
        }, actor=nguoi_dung["admin"]))
    outside = record_service.create_record(table, {
        "ma_don": "DON-THAT-001",
        "ten_khach": "Không được sửa",
        "so_dien_thoai": "+1 604 555 0199",
        "ngay": "2026-09-10",
        "loai_tien": "CAD",
        "ghi_chu": "Giữ nguyên",
        waybill_service.DETAIL_CODE: [{
            "product": products[0].code,
            "quantity": 1,
            "unit_price": "99.00",
            "paid_amount": "0.00",
        }],
    }, actor=nguoi_dung["admin"])
    return table, rows, outside


@override_settings(DEBUG=True)
def test_dry_run_khong_ghi_du_lieu(du_lieu_nap):
    table, rows, outside = du_lieu_nap
    ids = [row.pk for row in rows]
    output = StringIO()

    call_command("nap_du_lieu_van_don_moi", tong_so=5, seed=20260911,
                 dry_run=True, stdout=output)

    assert "2 dòng cập nhật, 3 dòng tạo mới" in output.getvalue()
    assert sorted(DataRecord.objects.filter(table=table, data__ma_don__startswith=PREFIX)
                  .values_list("pk", flat=True)) == ids
    assert not WaybillAssignment.objects.exists()
    outside.refresh_from_db()
    assert outside.data["ghi_chu"] == "Giữ nguyên"


@override_settings(DEBUG=True)
def test_nap_du_lieu_day_du_giu_id_va_chay_lai_an_toan(du_lieu_nap, nguoi_dung):
    table, old_rows, outside = du_lieu_nap
    old_identity = {row.pk: (row.data["ma_don"], row.data["ten_khach"], row.data["so_dien_thoai"])
                    for row in old_rows}
    output = StringIO()
    erp_counts = (Customer.objects.count(), Order.objects.count(), OrderLine.objects.count())

    call_command("nap_du_lieu_van_don_moi", tong_so=5, seed=20260911,
                 dry_run=False, stdout=output)

    cohort = list(DataRecord.objects.filter(table=table, data__ma_don__startswith=PREFIX)
                  .order_by("data__ma_don"))
    assert len(cohort) == 5
    assert {row.pk: (row.data["ma_don"], row.data["ten_khach"], row.data["so_dien_thoai"])
            for row in cohort if row.pk in old_identity} == old_identity
    assert len({row.data["ma_don"] for row in cohort}) == 5
    assert len({row.data["so_dien_thoai"] for row in cohort}) == 5
    assert {row.data["trang_thai_tt"] for row in cohort} == {
        "Chưa thanh toán", "Thanh toán 1 phần", "Đã thanh toán",
    }

    for row in cohort:
        assert all(row.data.get(code) not in (None, "") for code in (
            "bang", "thanh_pho", "zipcode", "dia_chi", "san_pham", "so_luong",
            "gia_tien", "pttt", "nguoi_ban", "trang_thai_vc", "ghi_chu",
        ))
        assert "???" not in row.data["ghi_chu"]
        items = list(WaybillItem.objects.filter(record=row, deleted_at__isnull=True))
        totals = waybill_service.totals(items)
        assert 1 <= len(items) <= 3
        assert row.data["so_luong"] == totals["so_luong"]
        assert row.data["gia_tien"] == totals["gia_tien"]
        assert row.data["so_tien_tt"] == totals["so_tien_tt"]
        assert row.data["trang_thai_tt"] == totals["trang_thai_tt"]
        assignment = WaybillAssignment.objects.select_related(
            "delivery__profile__department", "care__profile__department"
        ).get(record=row)
        assert assignment.delivery.profile.department.code == "van-don"
        assert assignment.care.profile.department.code == "sale"
        assert assignment.marketing_id is None

    outside.refresh_from_db()
    assert outside.data["ghi_chu"] == "Giữ nguyên"
    assert AuditLog.objects.filter(action=AuditAction.IMPORT, target_type="TableDef",
                                   target_id=str(table.pk)).count() == 1
    assert (Customer.objects.count(), Order.objects.count(), OrderLine.objects.count()) == erp_counts

    ids = list(DataRecord.objects.filter(table=table, data__ma_don__startswith=PREFIX)
               .order_by("pk").values_list("pk", flat=True))
    item_ids = list(WaybillItem.objects.filter(record__in=cohort, deleted_at__isnull=True)
                    .order_by("pk").values_list("pk", flat=True))
    assignment_versions = dict(WaybillAssignment.objects.filter(record__in=cohort)
                               .values_list("record_id", "version"))
    call_command("nap_du_lieu_van_don_moi", tong_so=5, seed=20260911,
                 dry_run=False, stdout=StringIO())
    assert list(DataRecord.objects.filter(table=table, data__ma_don__startswith=PREFIX)
                .order_by("pk").values_list("pk", flat=True)) == ids
    assert list(WaybillItem.objects.filter(record__in=cohort, deleted_at__isnull=True)
                .order_by("pk").values_list("pk", flat=True)) == item_ids
    assert dict(WaybillAssignment.objects.filter(record__in=cohort)
                .values_list("record_id", "version")) == assignment_versions
    assert AuditLog.objects.filter(action=AuditAction.IMPORT, target_type="TableDef",
                                   target_id=str(table.pk)).count() == 1


@override_settings(DEBUG=True)
def test_thieu_nhan_su_van_don_thi_khong_thay_doi_gi(du_lieu_nap, nguoi_dung):
    table, rows, outside = du_lieu_nap
    nguoi_dung["staff_vd"].is_active = False
    nguoi_dung["staff_vd"].save(update_fields=["is_active"])
    before = list(DataRecord.objects.filter(table=table).values_list("pk", "data"))

    with pytest.raises(CommandError, match="nhân sự Vận đơn"):
        call_command("nap_du_lieu_van_don_moi", tong_so=5, seed=20260911,
                     dry_run=False, stdout=StringIO())

    assert list(DataRecord.objects.filter(table=table).values_list("pk", "data")) == before
    assert not WaybillAssignment.objects.exists()


@override_settings(DEBUG=True)
def test_loi_giua_luot_thi_rollback_toan_bo(du_lieu_nap, monkeypatch):
    table, rows, outside = du_lieu_nap
    before = list(DataRecord.objects.filter(table=table).values_list("pk", "data"))

    def fail_items(*args, **kwargs):
        raise RuntimeError("lỗi giả lập giữa giao dịch")

    monkeypatch.setattr(WaybillItem.objects, "bulk_create", fail_items)
    with pytest.raises(RuntimeError, match="lỗi giả lập"):
        call_command("nap_du_lieu_van_don_moi", tong_so=5, seed=20260911,
                     dry_run=False, stdout=StringIO())

    assert list(DataRecord.objects.filter(table=table).values_list("pk", "data")) == before
    assert not WaybillAssignment.objects.exists()
