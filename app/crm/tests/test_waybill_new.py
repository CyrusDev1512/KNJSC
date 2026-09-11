"""Vận đơn mới theo CRM Tân — ADR-018, không thay thế các bài bảng cũ."""
import json
from datetime import datetime, timezone as dt_timezone
from decimal import Decimal
from io import BytesIO
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import QueryDict
from django.utils import timezone

from core import excel
from core.constants import Rank, Currency, JobStatus
from core.exceptions import BusinessError
from core.models import AuditLog
from forms_builder.models import DataRecord, TableDef, Grant, GrantAction
from forms_builder.services import record_service, grant_service, import_service, export_service
from orders.constants import ACTIVE_WAYBILL_TABLE_CODE, Market, PaymentMethod
from orders.models import Product, Order, OrderLine, WaybillItem, WaybillAssignment
from orders.services import dispatch_service, order_service, waybill_service as service

pytestmark = pytest.mark.django_db
GRID = "/bang-tinh/van_don_moi/"
ENTRY = "/van-don/len-don/"
STATS = "/thong-ke/"


def get_stats(client, params=None):
    return client.get(STATS, {"nguon": "van_don_moi", **(params or {})})


@pytest.fixture
def setup(departments, nguoi_dung, settings):
    settings.GRID_ONLY_TABLES = set()
    old = dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])
    new = TableDef.all_objects.get(code=ACTIVE_WAYBILL_TABLE_CODE)
    products = [Product.objects.create(name="Sản phẩm thử", code=f"new-{i}") for i in range(2)]
    return old, new, products


def lines(products, paid="0.00"):
    return [{"product": p.code, "quantity": 2, "unit_price": "10.10", "paid_amount": paid} for p in products]


def order(setup, user, *, assigned=True):
    result = order_service.create_order(phone="0901234567", customer_name="Khách kiểm thử",
        lines=lines(setup[2]), actor=user, currency=Currency.USD)
    if assigned:
        from django.contrib.auth import get_user_model
        WaybillAssignment.objects.create(record=result.record,
            delivery=get_user_model().objects.get(username='staff_vd'))
    return result


def form_data(products):
    return {"phone": "0901234567", "customer_name": "Khách kiểm thử", "market": Market.US,
            "currency": Currency.USD, "payment_method": PaymentMethod.CARD,
            "product": [p.code for p in products], "quantity": [2, 2], "unit_price": ["10.10", "10.10"]}


def test_initialize_preserves_legacy_and_copies_live_grants_once(departments, nguoi_dung):
    """AC-18.1 — Khởi tạo trên dữ liệu cũ, không chép dòng; quyền chỉ sao một lần."""
    old = TableDef.objects.create(code="van_don", name="Vận đơn trước", department=departments["vd"], is_shared=True)
    historical = DataRecord.objects.create(table=old, data={"ma_don": "LICH-SU"}, department=departments["vd"])
    live = grant_service.grant(table=old, user=nguoi_dung["staff_mkt"], action=GrantAction.VIEW, actor=nguoi_dung["admin"])
    revoked = grant_service.grant(table=old, user=nguoi_dung["manager_mkt"], action=GrantAction.VIEW, actor=nguoi_dung["admin"])
    grant_service.revoke(revoked, actor=nguoi_dung["admin"])
    dispatch_service.ensure_waybill_table()
    new = TableDef.all_objects.get(code=ACTIVE_WAYBILL_TABLE_CODE)
    old.refresh_from_db(); historical.refresh_from_db()
    assert old.name == "Vận đơn cũ" and old.code == "van_don"
    assert historical.table_id == old.pk and historical.data == {"ma_don": "LICH-SU"}
    assert not DataRecord.all_objects.filter(table=new).exists()
    assert list(new.grants.values_list("user_id", flat=True)) == [live.user_id]
    copied = new.grants.get()
    grant_service.revoke(copied, actor=nguoi_dung["admin"])
    dispatch_service.ensure_waybill_table()
    assert TableDef.all_objects.filter(code=ACTIVE_WAYBILL_TABLE_CODE).count() == 1
    assert not new.grants.filter(deleted_at__isnull=True).exists()
    assert old.grants.filter(pk=live.pk, deleted_at__isnull=True).exists()
    assert new.columns.count() == len(service.COLUMNS)


def test_erp_and_crm_each_create_one_new_snapshot(client, setup, nguoi_dung):
    """AC-18.2 — ERP và CRM dùng một dịch vụ, một dòng mới, ngày Việt Nam, người bán tự lấy."""
    actor = nguoi_dung["staff_sale_1"]
    instant = datetime(2026, 9, 8, 18, 30, tzinfo=dt_timezone.utc)
    with patch("django.utils.timezone.now", return_value=instant):
        original = order(setup, actor)
    assert original.record.data["ngay"] == "2026-09-09"
    client.force_login(actor)
    response = client.post(ENTRY, {**form_data(setup[2]), "seller": nguoi_dung["admin"].pk})
    assert response.status_code == 400  # Không âm thầm bỏ qua giả mạo Sale nữa.
    response = client.post(ENTRY, form_data(setup[2]))
    assert response.status_code == 200, response.content.decode()
    assert Order.objects.count() == 2
    assert DataRecord.objects.filter(table=setup[1]).count() == 2
    assert not DataRecord.objects.filter(table=setup[0]).exists()
    assert WaybillItem.objects.count() == 4
    assert Order.objects.latest("pk").seller_id == actor.pk
    assert all("black_list" not in r.data for r in DataRecord.objects.filter(table=setup[1]))


def test_snapshot_failure_rolls_back_all_rows(client, setup, nguoi_dung):
    """AC-18.2 — Lỗi ghi chi tiết hoàn tác đơn, dòng gốc và dòng vận đơn trong cùng giao dịch."""
    with patch.object(service, "after_create", side_effect=BusinessError("Lỗi ghi chi tiết")):
        with pytest.raises(BusinessError):
            order(setup, nguoi_dung["staff_sale_1"])
    assert not Order.objects.exists() and not OrderLine.objects.exists()
    assert not DataRecord.objects.filter(table=setup[1]).exists()
    assert not WaybillItem.objects.exists()


@pytest.mark.parametrize("paid,status", [("0.00", "Chưa thanh toán"), ("1.25", "Thanh toán 1 phần"), ("20.20", "Đã thanh toán")])
def test_detail_totals_and_original_immutable(setup, nguoi_dung, paid, status):
    """AC-18.3 — Tiền nhập từng sản phẩm, tổng tự cộng và trạng thái tự tính; ERP không đổi."""
    original = order(setup, nguoi_dung["staff_sale_1"])
    row = original.record
    service.update_items(nguoi_dung["staff_vd"], row.pk, lines(setup[2], paid), row.updated_at.isoformat())
    row.refresh_from_db(); original.refresh_from_db()
    assert row.data["so_tien_tt"] == str(Decimal(paid) * 2)
    assert row.data["trang_thai_tt"] == status
    assert row.data["gia_tien"] == "40.40" and row.data["so_luong"] == 4
    assert original.total == Decimal("40.40") and original.lines.count() == 2
    assert WaybillItem.objects.in_scope(nguoi_dung["staff_vd"]).count() == 2
    assert WaybillItem.objects.filter(deleted_at__isnull=False).count() == 2


def test_concurrent_stale_editor_and_regular_cell(setup, nguoi_dung):
    """AC-18.3 — Editor cũ bị từ chối; sửa ô từ bản đọc cũ không làm mất tổng vừa lưu."""
    row = order(setup, nguoi_dung["staff_sale_1"]).record
    version = row.updated_at.isoformat()
    service.update_items(nguoi_dung["staff_vd"], row.pk, lines(setup[2], "3.33"), version)
    with pytest.raises(BusinessError, match="vừa được"):
        service.update_items(nguoi_dung["staff_vd"], row.pk, lines(setup[2]), version)
    record_service.update_cell(row, "ghi_chu", "Lời nhắn riêng 0901234567", actor=nguoi_dung["staff_vd"])
    row.refresh_from_db()
    assert row.data["so_tien_tt"] == "6.66"
    assert not AuditLog.objects.filter(detail__contains="0901234567").exists()


@pytest.mark.parametrize("rank", [Rank.STAFF, Rank.LEADER, Rank.MANAGER, Rank.ADMIN])
def test_direct_routes_permissions_both_directions(client, setup, departments, make_user, nguoi_dung, rank):
    """AC-18.4 — Ba cấp bậc và Admin: lên đơn, chi tiết, thống kê đều kiểm quyền máy chủ."""
    row = order(setup, nguoi_dung["staff_sale_1"]).record
    detail = f"/van-don/chi-tiet/{row.pk}/"
    sale = make_user(f"sale_{rank}", rank, departments["sale"])
    client.force_login(sale)
    assert client.get(ENTRY).status_code == 200
    data = form_data(setup[2])
    if rank == Rank.ADMIN:
        data['seller'] = nguoi_dung['staff_sale_1'].pk
    assert client.post(ENTRY, data).status_code == 200
    expected = 200 if rank == Rank.ADMIN else 403
    assert client.get(detail).status_code == expected
    assert get_stats(client).status_code == 200  # Sale vừa tạo đơn được xem/thống kê đơn của mình.
    post = {**form_data(setup[2]), "paid_amount": ["1.00", "0.00"], "version": row.updated_at.isoformat()}
    assert client.post(detail, post).status_code == expected
    if rank != Rank.ADMIN:
        response = client.get(GRID)
        assert response.status_code == 200
        vd = make_user(f"vd_{rank}", rank, departments["vd"])
        WaybillAssignment.objects.filter(record=row).update(delivery=vd)
        client.force_login(vd)
        assert client.get(ENTRY).status_code == 403
        assert client.post(ENTRY, form_data(setup[2])).status_code == 403
        assert client.get(detail).status_code == 200
        assert get_stats(client).status_code == 200
        row.refresh_from_db(); post["version"] = row.updated_at.isoformat()
        assert client.post(detail, post).status_code == 200


def test_view_grant_cannot_edit_or_enter_orders(client, setup, nguoi_dung):
    """AC-18.4 — Cấp xem không thành quyền sửa; thu quyền chặn cả đường chi tiết và thống kê."""
    row = order(setup, nguoi_dung["staff_sale_1"]).record
    user = nguoi_dung["staff_mkt"]
    grant = grant_service.grant(table=setup[1], user=user, action=GrantAction.VIEW, actor=nguoi_dung["admin"])
    client.force_login(user)
    detail = f"/van-don/chi-tiet/{row.pk}/"
    assert client.get(detail).status_code == 200 and get_stats(client).status_code == 200
    assert client.post(detail, form_data(setup[2])).status_code == 403
    assert client.post(ENTRY, form_data(setup[2])).status_code == 403
    grant_service.revoke(grant, actor=nguoi_dung["admin"])
    assert client.get(detail).status_code == 403 and get_stats(client).status_code == 403


@pytest.mark.parametrize("column", sorted(service.PROTECTED))
def test_paste_and_cell_cannot_override_totals(client, setup, nguoi_dung, column):
    """AC-18.5 — Chặn sửa ô và dán tổng, hoàn tác cả gói nếu chứa cột bảo vệ."""
    row = order(setup, nguoi_dung["staff_sale_1"]).record
    before = row.data.copy()
    client.force_login(nguoi_dung["staff_vd"])
    import uuid
    locked={'id':row.pk,'column':column,'old':row.data.get(column),'value':'999'}
    assert client.post(GRID+'luu-json/',{'operation':str(uuid.uuid4()),'cells':[locked]}, content_type='application/json').status_code==400
    assert client.post(GRID+'luu-json/',{'operation':str(uuid.uuid4()),'cells':[
        {'id':row.pk,'column':'ghi_chu','old':row.data.get('ghi_chu'),'value':'không lưu'},locked]}, content_type='application/json').status_code==400
    row.refresh_from_db()
    assert row.data == before


def test_statistics_full_filter_currency_product_and_soft_delete(client, setup, nguoi_dung):
    """AC-18.6 — Toàn bộ bộ lọc, không chỉ trang; tách tiền, nhóm mã sản phẩm và xoá/khôi phục."""
    actor = nguoi_dung["staff_vd"]
    row = order(setup, nguoi_dung["staff_sale_1"]).record
    service.update_items(actor, row.pk, lines(setup[2], "1.11"), row.updated_at.isoformat())
    row.refresh_from_db()
    for i in range(26):
        copy = record_service.create_record(setup[1], {**row.data, "ma_don": f"COPY-{i}",
            "loai_tien": "CAD" if i == 0 else "USD", service.DETAIL_CODE: lines(setup[2], "1.11")}, actor=actor)
        WaybillAssignment.objects.create(record=copy, delivery=actor)
    record_service.update_cell(row, "trang_thai_vc", "Hoàn đơn", actor=actor)
    client.force_login(actor)
    results = get_stats(client, {"moi_trang": 25, "trang": 2}).context["results"]
    assert sum(r["orders"] for r in results) == 27
    usd = next(r for r in results if r["currency"] == "USD")
    assert usd["value"] == Decimal("40.40") * 26 and usd["paid"] == Decimal("2.22") * 26
    params = {"f_ma_don__trong": row.data["ma_don"], "group": "product"}
    response = get_stats(client, params)
    assert len(response.context["results"]) == 2  # tên trùng nhau nhưng khác mã
    assert all(r["orders"] == 1 and r["paid"] == Decimal("1.11") for r in response.context["results"])
    assert ('f_ma_don__trong', row.data['ma_don']) in response.context['filters']
    record_service.delete_record(row, actor=actor)
    assert not get_stats(client, params).context["results"]
    record_service.restore_record(row, actor=actor)
    assert len(get_stats(client, params).context["results"]) == 2


def test_export_import_roundtrip_and_preview_ambiguous(client, setup, nguoi_dung, settings, tmp_path):
    """AC-18.7 — Xuất chi tiết JSON, nhập lại đúng; lỗi chi tiết xuất hiện ngay ở xem trước."""
    settings.STORAGE_DIR = tmp_path
    row = order(setup, nguoi_dung["staff_sale_1"], assigned=False).record
    service.update_items(nguoi_dung["admin"], row.pk, lines(setup[2], "1.11"), row.updated_at.isoformat())
    columns = list(setup[1].columns.all())
    workbook = export_service.build_workbook(DataRecord.objects.in_scope(nguoi_dung["admin"]).filter(pk=row.pk), columns, title="Vận đơn")
    buffer = BytesIO(); workbook.save(buffer)
    upload = SimpleUploadedFile("roundtrip.xlsx", buffer.getvalue())
    job = import_service.prepare(setup[1], upload, actor=nguoi_dung["admin"])
    assert job.summary["preview_error_count"] == 0
    job.status = JobStatus.PENDING; job.save()
    import_service.run(job.pk); job.refresh_from_db()
    assert job.summary["created"] == 1 and job.summary["error_count"] == 0
    copy = DataRecord.objects.filter(table=setup[1]).exclude(pk=row.pk).get()
    assert copy.data["so_tien_tt"] == "2.22" and copy.waybill_items.count() == 2
    workbook.active.cell(2, len(columns) + 1, "nhiều sản phẩm chưa tách")
    buffer = BytesIO(); workbook.save(buffer)
    job = import_service.prepare(setup[1], SimpleUploadedFile("bad.xlsx", buffer.getvalue()), actor=nguoi_dung["admin"])
    assert job.summary["preview_error_count"] == 1 and job.summary["preview_errors"][0][0] == 2
    client.force_login(nguoi_dung["admin"])
    html = client.get(f"/bang/van_don_moi/nhap/{job.pk}/").content.decode()
    assert "chi tiết sản phẩm không hợp lệ" in html


@pytest.mark.parametrize("value", [None, "", "NaN", "Infinity", "-0.01"])
def test_invalid_money_is_business_error(value):
    """AC-18.3 — Tiền thiếu, âm hoặc không hữu hạn báo lỗi nghiệp vụ, không lỗi máy chủ."""
    with pytest.raises(BusinessError):
        service.money(value)


@pytest.mark.parametrize("role", ["admin", "staff_sale_1", "staff_vd"])
def test_grid_and_statistics_without_embedded_entry(client, setup, nguoi_dung, role):
    """AC-18.8, ADR-019 — Chỉ lưới và thống kê; không tải form Lên đơn nhúng."""
    order(setup, nguoi_dung["staff_sale_1"])
    user = nguoi_dung[role]
    if role == "staff_sale_1":
        grant_service.grant(table=setup[1], user=user, action=GrantAction.VIEW, actor=nguoi_dung["admin"])
    client.force_login(user)
    response = client.get(GRID)
    html = response.content.decode()
    for text in ("master-grid", "thống kê", "Bộ lọc", "master-grid.js"):
        assert text in html
    assert 'id="vd-entry"' not in html and '<summary>Lên đơn</summary>' not in html
    assert 'hx-get="' + ENTRY not in html and 'hx-post="' + ENTRY not in html
    assert "can_enter_order" not in response.context
    assert "black_list" not in html and 'id="vd-statistics"' not in html
    row = DataRecord.objects.filter(table=setup[1]).get()
    detail = client.get(f"/van-don/chi-tiet/{row.pk}/").content.decode()
    assert "Đã thanh toán" in detail and 'name="paid_amount"' in detail


def test_standalone_entry_htmx_success_and_validation(client, setup, nguoi_dung):
    """ADR-019 — Form riêng giữ lỗi/thành công, không phát sự kiện tải lại bảng."""
    client.force_login(nguoi_dung["staff_sale_1"])
    assert 'id="vd-entry"' in client.get(ENTRY).content.decode()
    invalid = client.post(ENTRY, {**form_data(setup[2]), "customer_name": ""}, HTTP_HX_REQUEST="true")
    assert invalid.status_code == 400 and 'id="vd-entry"' in invalid.content.decode()
    assert not Order.objects.exists()
    response = client.post(ENTRY, form_data(setup[2]), HTTP_HX_REQUEST="true")
    assert response.status_code == 200 and "Đã lưu đơn" in response.content.decode()
    assert 'id="vd-entry"' in response.content.decode()
    assert "HX-Trigger" not in response
    assert Order.objects.count() == 1 and DataRecord.objects.filter(table=setup[1]).count() == 1


def test_erp_entry_still_dispatches_to_new_table(client, setup, nguoi_dung, settings):
    """ADR-019 — Gỡ form nhúng không đổi nơi nhận của trang Lên đơn ERP."""
    settings.ROOT_URLCONF = "knjsc.urls"
    client.force_login(nguoi_dung["staff_sale_1"])
    response = client.post("/len-don/", {
        "phone": "2025550199", "customer_name": "Khách kiểm thử ERP",
        "sp_0": setup[2][0].code, "sl_0": "2", "gia_0": "10.10",
        "market": Market.US, "currency": Currency.USD,
    })
    assert response.status_code == 302
    assert Order.objects.get().record.table_id == setup[1].pk
    assert DataRecord.objects.filter(table=setup[1]).count() == 1
