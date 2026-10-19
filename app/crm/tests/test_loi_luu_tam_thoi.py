"""TL-24/119: lỗi giao dịch có thể thử lại phải trả JSON rõ, không giả báo thành công."""
import uuid
from unittest.mock import patch

import pytest
from django.db import OperationalError
from psycopg.errors import DeadlockDetected, SerializationFailure, LockNotAvailable

from crm.tests.test_waybill_feedback import feedback  # noqa: F401
from crm.models import GridMutationReceipt
from forms_builder.models import DataRecord

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("pg_error", [DeadlockDetected, SerializationFailure, LockNotAvailable])
def test_loi_giao_dich_tra_json_thu_lai_va_khong_ghi_do(client, feedback, nguoi_dung, pg_error):
    """AC-11.19 — Deadlock/serialization/lock timeout huỷ toàn lượt, trả 503 JSON, cùng operation thử lại được."""
    table, _, rows = feedback
    client.force_login(nguoi_dung["staff_vd"])
    row = rows[0]
    operation = str(uuid.uuid4())
    payload = {"operation": operation, "cells": [{"id": row.pk, "column": "ghi_chu",
                "old": row.data.get("ghi_chu"), "value": "nháp cần giữ"}]}
    error = OperationalError("database transient test")
    error.__cause__ = pg_error("test")
    client.raise_request_exception = False
    with patch.object(DataRecord, "bulk_save", side_effect=error):
        response = client.post(f"/bang-tinh/{table.code}/luu-json/", payload, content_type="application/json")
    assert response.status_code == 503
    assert response.json()["code"] == "retryable_save"
    assert response["Retry-After"] == "1"
    assert not GridMutationReceipt.objects.filter(operation=operation).exists()
    row.refresh_from_db()
    assert row.data.get("ghi_chu") != "nháp cần giữ"
    retry = client.post(f"/bang-tinh/{table.code}/luu-json/", payload, content_type="application/json")
    assert retry.status_code == 200
    row.refresh_from_db()
    assert row.data["ghi_chu"] == "nháp cần giữ"
