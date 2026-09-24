"""Khoá so trùng số điện thoại — TL-36, ADR-036 bổ sung 22.09.2026.

Cột Trùng trước nay so `val_phone` **đúng như gõ**: `+1 (416) 555-0123` và
`4165550123` bị coi là hai khách. Nay so bằng `val_phone_key` = 9 chữ số cuối sau
khi bỏ ký tự không phải số (`forms_builder.models.phone_key`); ô hiển thị vẫn giữ
nguyên chữ nhân viên gõ.
"""
import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from forms_builder.models import DataRecord, phone_key
from forms_builder.services import record_service
from orders.services import dispatch_service

pytestmark = pytest.mark.django_db


@pytest.fixture
def bang_vd(nguoi_dung, settings):
    settings.GRID_ONLY_TABLES = set()
    return dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])


def _dong(bang, nguoi, **gia_tri):
    mac_dinh = {"ma_don": f"T36-{len(gia_tri)}-{gia_tri.get('so_dien_thoai', '')[:6]}",
                "ngay": "2026-09-22", "loai_tien": "USD"}
    return record_service.create_record(bang, {**mac_dinh, **gia_tri}, actor=nguoi)


def test_khoa_trung_gom_cac_kieu_viet_cua_cung_mot_so(client, bang_vd, nguoi_dung):
    """AC-36.8 — `+1 (416) 555-0123`, `(416) 555-0123` và `4165550123` là một khách: cột
    Trùng đếm 3, `?trung=1` trả cả ba dòng; số khác 9 số cuối không gom nhầm; ô hiển thị
    giữ nguyên chữ gốc; ô trống không tính là trùng với nhau"""
    vd = nguoi_dung["staff_vd"]
    a = _dong(bang_vd, vd, ma_don="T36-A", ten_khach="A", so_dien_thoai="+1 (416) 555-0123")
    b = _dong(bang_vd, vd, ma_don="T36-B", ten_khach="B", so_dien_thoai="(416) 555-0123")
    c = _dong(bang_vd, vd, ma_don="T36-C", ten_khach="C", so_dien_thoai="4165550123")
    khac = _dong(bang_vd, vd, ma_don="T36-D", ten_khach="D", so_dien_thoai="4165550999")
    _dong(bang_vd, vd, ma_don="T36-E", ten_khach="E", so_dien_thoai="")
    _dong(bang_vd, vd, ma_don="T36-F", ten_khach="F", so_dien_thoai="")

    client.force_login(vd)
    data = client.get(f"/bang-tinh/{bang_vd.code}/du-lieu/").json()
    trung = {d["id"]: d["cells"]["__duplicates"]["value"] for d in data["rows"]}
    assert trung[a.pk] == trung[b.pk] == trung[c.pk] == 3
    assert trung[khac.pk] == 1

    # Ô hiển thị vẫn đúng như gõ — chỉ khoá so sánh được chuẩn hoá
    o = {d["id"]: d["cells"]["so_dien_thoai"]["value"] for d in data["rows"]}
    assert o[a.pk] == "+1 (416) 555-0123" and o[c.pk] == "4165550123"

    kq = client.get(f"/bang-tinh/{bang_vd.code}/du-lieu/?trung=1").json()
    assert {d["id"] for d in kq["rows"]} == {a.pk, b.pk, c.pk}


def test_khoa_sinh_o_moi_duong_ghi(bang_vd, nguoi_dung):
    """AC-36.8 — `sync_indexed_columns` và `bulk_save` (danh sách cột mặc định) cùng ra một
    khoá; xoá số về rỗng thì khoá cũng rỗng, không giữ khoá cũ"""
    vd = nguoi_dung["staff_vd"]
    dong = _dong(bang_vd, vd, ma_don="T36-G", ten_khach="G", so_dien_thoai="+1 416-555-0123")
    dong.refresh_from_db()
    assert dong.val_phone_key == phone_key("+1 416-555-0123") == "165550123"

    # Đường bulk: đổi số trong JSON, sync rồi bulk_save với danh sách cột mặc định
    dong.data["so_dien_thoai"] = "099 888 7777"
    dong.sync_indexed_columns()
    DataRecord.bulk_save([dong])
    dong.refresh_from_db()
    assert dong.val_phone == "099 888 7777" and dong.val_phone_key == "998887777"

    dong.data["so_dien_thoai"] = ""
    dong.sync_indexed_columns()
    DataRecord.bulk_save([dong])
    dong.refresh_from_db()
    assert dong.val_phone == "" and dong.val_phone_key == ""


def test_migration_0016_backfill_va_dao_duoc(bang_vd, nguoi_dung):
    """AC-36.8 — Migration `forms_builder/0016` chạy xuôi và ngược đều được; lượt xuôi
    backfill đúng khoá cho dòng đã có từ trước (dòng sống qua lượt lùi rồi tiến lại)"""
    assert connection.settings_dict["NAME"].startswith("test_")
    vd = nguoi_dung["staff_vd"]
    dong = _dong(bang_vd, vd, ma_don="T36-H", ten_khach="H", so_dien_thoai="+1 (416) 555-0123")

    def cot():
        with connection.cursor() as cursor:
            return {c.name for c in connection.introspection.get_table_description(
                cursor, "forms_builder_datarecord")}

    # Trigger ghi nhận thay đổi lưới đang treo trên bảng; chưa xả thì Postgres
    # không cho ALTER TABLE trong cùng giao dịch (như bài AC-39.7)
    with connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
    try:
        MigrationExecutor(connection).migrate([("forms_builder", "0015_columndef_is_hidden")])
        assert "val_phone_key" not in cot()
    finally:
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
    assert "val_phone_key" in cot()

    # Lượt tiến vừa rồi đã chạy backfill: dòng cũ (khoá bị bỏ theo cột) có lại khoá đúng
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT val_phone, val_phone_key FROM forms_builder_datarecord WHERE id = %s",
            [dong.pk])
        so, khoa = cursor.fetchone()
    assert so == "+1 (416) 555-0123" and khoa == "165550123"
