"""Mã nhân viên, ngày Việt Nam và đơn vị chụp tại lúc lên đơn."""
import json
from datetime import datetime, timezone as utc
from unittest.mock import patch

import pytest
from core.models import AuditLog
from orders.models import Order, WaybillItem
from orders.services import order_service, waybill_service
from .test_waybill_new import setup, form_data, ENTRY

pytestmark = pytest.mark.django_db


def test_entry_date_and_units_snapshot(client, setup, nguoi_dung):
    actor = nguoi_dung["staff_sale_1"]
    actor.profile.full_name = "Họ tên không phải mã"
    actor.profile.save()
    actor.first_name = "Tên trong auth"
    actor.save()
    client.force_login(actor)
    instant = datetime(2026, 9, 11, 18, 30, tzinfo=utc.utc)
    with patch("django.utils.timezone.now", return_value=instant):
        response = client.get(ENTRY)
        assert 'value="12/09/2026 01:30"' in response.content.decode()
        payload = {**form_data(setup[2]), "unit": ["hộp", "túi"], "order_date": "1999-01-01"}
        response = client.post(ENTRY, payload)
    assert response.status_code == 200
    order = Order.objects.get()
    assert order.record.data["ngay"] == "2026-09-12"
    assert order.record.data["nguoi_ban"] == actor.username
    assert list(order.lines.values_list("unit", flat=True)) == ["hộp", "túi"]
    assert list(WaybillItem.objects.filter(record=order.record).values_list("unit", flat=True)) == ["hộp", "túi"]
    assert AuditLog.objects.filter(actor=actor, target_type="Order").get().actor_label == actor.username
    setup[2][0].unit = "chiếc"
    setup[2][0].save()
    assert order.lines.first().unit == "hộp"
    exported = waybill_service.export_queryset(type(order.record).objects.filter(pk=order.record_id)).get()
    assert json.loads(waybill_service.export_detail(exported))[0]["unit"] == "hộp"


def test_invalid_unit_rolls_back(client, setup, nguoi_dung):
    client.force_login(nguoi_dung["staff_sale_1"])
    response = client.post(ENTRY, {**form_data(setup[2]), "unit": ["INVALID", "cái"]})
    assert response.status_code == 400
    assert not Order.objects.exists()
    assert not WaybillItem.objects.exists()


def test_default_unit_and_legacy_edit_preserve_snapshot(setup, nguoi_dung):
    actor = nguoi_dung["staff_sale_1"]
    product = setup[2][0]
    product.unit = "bộ"
    product.save()
    raw = [{"product": product.code, "quantity": 1, "unit_price": "3.00"}]
    order = order_service.create_order(phone="09000", customer_name="Test", lines=raw, actor=actor)
    assert order.lines.get().unit == "bộ"
    product.unit = "chiếc"
    product.save()
    waybill_service.update_items(nguoi_dung["admin"], order.record_id, raw, order.record.updated_at.isoformat())
    assert WaybillItem.objects.filter(record=order.record, deleted_at__isnull=True).get().unit == "bộ"
    assert order.lines.get().unit == "bộ"


@pytest.mark.django_db(transaction=True)
def test_unit_migration_roundtrip_preserves_old_order(setup, nguoi_dung):
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor
    assert connection.settings_dict["NAME"].startswith("test_")
    product = setup[2][0]
    order = order_service.create_order(phone="09001", customer_name="Test", actor=nguoi_dung["staff_sale_1"],
        lines=[{"product": product.code, "quantity": 2, "unit_price": "4.00"}])
    expected = order.record.data.copy()
    try:
        MigrationExecutor(connection).migrate([("orders", "0005_assignment_columns")])
        MigrationExecutor(connection).migrate([("orders", "0006_line_unit_snapshot")])
        order.refresh_from_db()
        assert order.record.data == expected
        assert order.total == 8
        assert order.lines.get().unit == ""
        assert WaybillItem.objects.get(record=order.record).unit == ""
    finally:
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())


def test_custom_unit_export_survives_catalog_change(setup, nguoi_dung):
    product = setup[2][0]
    product.unit = "bộ"
    product.save()
    order = order_service.create_order(phone="09002", customer_name="Test", actor=nguoi_dung["staff_sale_1"],
        lines=[{"product": product.code, "quantity": 1, "unit_price": "4.00"}])
    product.unit = "cái"
    product.save()
    row = waybill_service.export_queryset(type(order.record).objects.filter(pk=order.record_id)).get()
    assert waybill_service.validate_items(waybill_service.export_detail(row))[0].unit == "bộ"


def test_admin_automatically_stands_order(client, setup, nguoi_dung):
    actor = nguoi_dung["admin"]
    client.force_login(actor)
    assert 'name="seller"' not in client.get(ENTRY).content.decode()
    response = client.post(ENTRY, {**form_data(setup[2]), "unit": ["cái", "chiếc"]})
    assert response.status_code == 200
    order = Order.objects.get()
    assert order.seller == actor and order.created_by == actor
    assert order.department.code == "sale" and order.team_id is None
    assert order.record.data["nguoi_ban"] == actor.username
    assert AuditLog.objects.get(target_type="Order", target_id=str(order.pk)).actor_label == actor.username
    client.force_login(nguoi_dung["staff_sale_1"])
    assert client.get(f"/van-don/don-goc/{order.code}/").status_code == 404


def test_admin_cannot_override_automatic_seller_in_post(client, setup, nguoi_dung):
    client.force_login(nguoi_dung["admin"])
    response = client.post(ENTRY, {**form_data(setup[2]), "seller": nguoi_dung["staff_sale_1"].pk})
    assert response.status_code == 400
    assert not Order.objects.exists()


def test_entry_and_original_query_budget(client, setup, nguoi_dung, django_assert_max_num_queries):
    client.force_login(nguoi_dung["staff_sale_1"])
    with django_assert_max_num_queries(10):
        assert client.get(ENTRY).status_code == 200
    assert client.post(ENTRY, form_data(setup[2])).status_code == 200
    order = Order.objects.get()
    with django_assert_max_num_queries(10):
        assert client.get(f"/van-don/don-goc/{order.code}/").status_code == 200


def test_old_client_removing_first_line_preserves_remaining_unit(setup, nguoi_dung):
    products = setup[2]
    raw = [{"product": p.code, "quantity": 1, "unit_price": "1.00", "unit": u}
           for p, u in zip(products, ("hộp", "túi"))]
    order = order_service.create_order(phone="09003", customer_name="Test", actor=nguoi_dung["staff_sale_1"], lines=raw)
    remaining = {k: v for k, v in raw[1].items() if k != "unit"}
    waybill_service.update_items(nguoi_dung["admin"], order.record_id, [remaining], order.record.updated_at.isoformat())
    assert WaybillItem.objects.filter(record=order.record, deleted_at__isnull=True).get().unit == "túi"


def test_order_time_uses_save_instant_not_open_form(client, setup, nguoi_dung):
    client.force_login(nguoi_dung["staff_sale_1"])
    opened = datetime(2026, 9, 11, 3, 32, 0, tzinfo=utc.utc)
    saved = datetime(2026, 9, 11, 3, 33, 47, tzinfo=utc.utc)
    with patch("django.utils.timezone.now", return_value=opened):
        response = client.get(ENTRY)
        assert 'value="11/09/2026 10:32"' in response.content.decode()
    with patch("django.utils.timezone.now", return_value=saved):
        response = client.post(ENTRY, {**form_data(setup[2]), "order_time": "10:32"})
    assert response.status_code == 200
    assert Order.objects.get().created_at == saved
    assert "lúc 10:33 ngày 11/09/2026" in response.content.decode()
