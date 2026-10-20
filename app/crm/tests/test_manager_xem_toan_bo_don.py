"""19.10.2026: Manager xem mọi đơn/vận đơn, không mở rộng dữ liệu khác hoặc quyền ghi."""
import uuid

import pytest
from django.urls import reverse

from crm.tests.test_waybill_new import setup, order  # noqa: F401
from forms_builder.models import DataRecord, TableDef
from orders.services.order_service import orders_of

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("role", ["manager_sale", "manager_mkt", "manager_vd"])
def test_manager_doc_toan_bo_don_va_bang(client, settings, setup, nguoi_dung, role):
    """AC-3.4 — Ngoại lệ đơn hàng: Manager mọi bộ phận đọc đơn, dòng, bảng dù chưa tự lên đơn nào."""
    settings.ROOT_URLCONF = "knjsc.urls_bangtinh"
    orders = [order(setup, nguoi_dung[name]) for name in ("staff_sale_1", "staff_sale_2")]
    user = nguoi_dung[role]
    table = setup[0]
    assert set(orders_of(user).values_list("pk", flat=True)) == {o.pk for o in orders}
    assert TableDef.objects.in_scope(user).filter(pk=table.pk).exists()
    assert set(DataRecord.objects.in_scope(user, table=table).values_list("pk", flat=True)) == {o.record_id for o in orders}
    client.force_login(user)
    assert client.get(f"/bang-tinh/{table.code}/").status_code == 200
    response = client.get(f"/bang-tinh/{table.code}/du-lieu/")
    assert response.status_code == 200
    assert {r["id"] for r in response.json()["rows"]} == {o.record_id for o in orders}
    for item in orders:
        assert client.get(reverse("don_xem", args=[item.code])).status_code == 200


@pytest.mark.parametrize("role", ["manager_sale", "manager_mkt"])
def test_doc_toan_cong_ty_khong_cap_them_quyen_sua(client, settings, setup, nguoi_dung, role):
    """AC-3.7 — Quyền đọc mới không cho sửa dòng của người khác hoặc phân công."""
    settings.ROOT_URLCONF = "knjsc.urls_bangtinh"
    item = order(setup, nguoi_dung["staff_sale_2"])
    user = nguoi_dung[role]
    client.force_login(user)
    base = f"/bang-tinh/{setup[0].code}/"
    response = client.get(base + "du-lieu/")
    assert response.status_code == 200
    assert response.json()["rows"][0]["editable"] is False
    saved = client.post(base + "luu-json/", {
        "operation": str(uuid.uuid4()), "cells": [{"id": item.record_id,
        "column": "ghi_chu", "old": item.record.data.get("ghi_chu"), "value": "không được ghi"}]
    }, content_type="application/json")
    assert saved.status_code == 403
    item.record.refresh_from_db()
    assert item.record.data.get("ghi_chu") != "không được ghi"


def test_manager_khong_mo_rong_bang_bao_cao(setup, nguoi_dung, departments):
    """AC-3.5 — Ngoại lệ đơn/vận đơn không thay phạm vi bảng nghiệp vụ khác."""
    other = TableDef.objects.create(code="mkt-private-test", name="Bảng Marketing",
                                   department=departments["mkt"], created_by=nguoi_dung["staff_mkt"])
    row = DataRecord.objects.create(table=other, department=departments["mkt"],
                                   created_by=nguoi_dung["staff_mkt"], data={})
    user = nguoi_dung["manager_sale"]
    assert not TableDef.objects.in_scope(user).filter(pk=other.pk).exists()
    assert not DataRecord.objects.in_scope(user).filter(pk=row.pk).exists()
