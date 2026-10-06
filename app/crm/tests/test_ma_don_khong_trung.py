"""Mỗi mã đơn chỉ một dòng sống trên bảng vận đơn — chặn ở tầng cơ sở dữ liệu (06.10.2026).

Trước đây chỉ bước kiểm tệp nhập so mã đơn; lưới, Lên đơn, khôi phục dòng và hai lượt nhập chạy cùng lúc đều để lọt
hai dòng cùng mã — đối soát vận đơn với hãng vận chuyển và kế toán theo mã đơn thì một mã hai dòng là đếm đôi.
Chủ dự án chốt: chặn bằng ràng buộc duy nhất của Postgres trên `(bảng, val_order_code)`, chỉ cho dòng chưa xoá và mã
khác rỗng, chỉ ở bảng vận đơn. Dòng đã xoá không giữ mã: nhập lại mã đó được, nhưng khôi phục dòng cũ khi mã đã có
dòng sống thì bị từ chối.
"""
import uuid
from unittest import mock

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from core.exceptions import BusinessError
from forms_builder.models import DataRecord, TableDef
from forms_builder.services import record_service, table_service
from orders.services import dispatch_service

pytestmark = pytest.mark.django_db


@pytest.fixture
def bang_vd(nguoi_dung, settings):
    settings.GRID_ONLY_TABLES = set()
    return dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])


def _dong(bang, nguoi, ma, **gia_tri):
    mac_dinh = {"ma_don": ma, "ngay": "2026-10-06", "ten_khach": "Khách", "so_dien_thoai": "0900",
                "quoc_gia": "Hoa Kỳ", "loai_tien": "USD"}
    return record_service.create_record(bang, {**mac_dinh, **gia_tri}, actor=nguoi)


def test_hai_dong_song_cung_ma_don_bi_chan(bang_vd, nguoi_dung):
    """AC-36.11 — Bảng vận đơn: tạo dòng thứ hai cùng mã đơn (kể cả khác khoảng trắng hai đầu) bị từ chối bằng lời
    tiếng Việt nêu mã; bảng giữ đúng một dòng; khoá `val_order_code` là mã đã cắt khoảng trắng"""
    vd = nguoi_dung["staff_vd"]
    dau = _dong(bang_vd, vd, "DH-TRUNG-1")
    assert dau.val_order_code == "DH-TRUNG-1"
    with pytest.raises(BusinessError, match="DH-TRUNG-1"):
        _dong(bang_vd, vd, "  DH-TRUNG-1 ")
    assert DataRecord.objects.filter(table=bang_vd, val_order_code="DH-TRUNG-1").count() == 1
    # Lỗi không làm hỏng giao dịch đang mở: ghi tiếp được ngay
    _dong(bang_vd, vd, "DH-TRUNG-2")


def test_ma_rong_va_bang_thuong_khong_bi_rang_buoc(bang_vd, nguoi_dung, departments):
    """AC-36.11 — Mã đơn để trống thì nhiều dòng vẫn được; bảng thường có cột `ma_don` (vd. Sale ghi theo dòng sản
    phẩm) không bị ràng buộc"""
    vd = nguoi_dung["staff_vd"]
    _dong(bang_vd, vd, "")
    _dong(bang_vd, vd, "")
    bang = table_service.create_table(name="Đơn Sale", code="don_sale", department=departments["sale"],
                                      actor=nguoi_dung["admin"])
    table_service.add_column(bang, name="Mã đơn", code="ma_don", field_type="text", actor=nguoi_dung["admin"])
    a = record_service.create_record(bang, {"ma_don": "DH-1"}, actor=nguoi_dung["admin"])
    b = record_service.create_record(bang, {"ma_don": "DH-1"}, actor=nguoi_dung["admin"])
    assert a.val_order_code == b.val_order_code == ""


def test_dong_da_xoa_khong_giu_ma_nhung_khoi_phuc_bi_chan(bang_vd, nguoi_dung):
    """AC-36.11 — Xoá dòng thì mã được dùng lại; khôi phục dòng đã xoá khi mã đã có dòng sống thì bị từ chối, dòng
    vẫn ở trạng thái đã xoá"""
    vd = nguoi_dung["staff_vd"]
    cu = _dong(bang_vd, vd, "DH-XOA")
    record_service.delete_record(cu, actor=vd)
    _dong(bang_vd, vd, "DH-XOA")
    cu = DataRecord.all_objects.get(pk=cu.pk)
    with pytest.raises(BusinessError, match="DH-XOA"):
        record_service.restore_record(cu, actor=vd)
    assert DataRecord.all_objects.get(pk=cu.pk).deleted_at is not None


def test_luoi_doi_ma_trung_tra_loi_tieng_viet(client, bang_vd, nguoi_dung):
    """AC-36.11 — Lưới: sửa ô Mã đơn thành mã đã có → 400 với lời tiếng Việt, ô giữ giá trị cũ; dán hai ô cùng mã
    trong một lượt cũng bị chặn, không ô nào đổi"""
    vd = nguoi_dung["staff_vd"]
    a, b, c = _dong(bang_vd, vd, "DH-L1"), _dong(bang_vd, vd, "DH-L2"), _dong(bang_vd, vd, "DH-L3")
    client.force_login(vd)

    def luu(*o):
        cells = [{"id": pk, "column": "ma_don", "old": DataRecord.objects.get(pk=pk).data["ma_don"], "value": v}
                 for pk, v in o]
        return client.post(f"/bang-tinh/{bang_vd.code}/luu-json/", {"operation": str(uuid.uuid4()), "cells": cells},
                           content_type="application/json")

    r = luu((b.pk, "DH-L1"))
    assert r.status_code == 400 and "DH-L1" in r.json()["error"], r.content
    r = luu((b.pk, "DH-MOI"), (c.pk, "DH-MOI"))
    assert r.status_code == 400 and "DH-MOI" in r.json()["error"], r.content
    assert [DataRecord.objects.get(pk=x.pk).data["ma_don"] for x in (a, b, c)] == ["DH-L1", "DH-L2", "DH-L3"]
    assert luu((b.pk, "DH-L9")).status_code == 200


def test_len_don_trung_ma_thi_khong_luu_don(bang_vd, nguoi_dung):
    """AC-36.11 — Lên đơn: mã đơn mới trùng một dòng đang có (do ai đó gõ tay trên lưới) thì `dispatch_service.push`
    báo lỗi nêu mã, đơn không được lưu (AC-6.5)"""
    from orders.models import Order, Product, ProductGroup
    from orders.tests.test_len_don import _len_don

    nhom = ProductGroup.objects.create(name="Nhóm thử")
    sp = {"massage": Product.objects.create(name="Máy thử", code="may_thu", group=nhom)}
    _dong(bang_vd, nguoi_dung["staff_vd"], "DH-0610-9999")
    with mock.patch("orders.services.order_service._sinh_ma_don", return_value="DH-0610-9999"):
        with pytest.raises(BusinessError, match="DH-0610-9999"):
            _len_don(nguoi_dung["staff_sale_1"], sp)
    assert not Order.all_objects.filter(code="DH-0610-9999").exists()


def test_migration_dung_khi_con_ma_trung_va_dao_duoc(bang_vd, nguoi_dung):
    """AC-36.12 — Migration `forms_builder/0017` lùi rồi tiến: điền lại khoá cho dòng cũ; còn hai dòng sống cùng mã
    thì dừng với lời liệt kê mã trùng, không tạo ràng buộc nửa vời; dọn trùng xong thì chạy được"""
    assert connection.settings_dict["NAME"].startswith("test_")
    vd = nguoi_dung["staff_vd"]
    a = _dong(bang_vd, vd, "DH-MG-1")
    b = _dong(bang_vd, vd, "DH-MG-2")
    with connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
    try:
        MigrationExecutor(connection).migrate([("forms_builder", "0016_datarecord_val_phone_key")])
        # Không còn ràng buộc: giả lập dữ liệu trùng có từ trước khi nâng cấp
        DataRecord.objects.filter(pk=b.pk).update(data={**b.data, "ma_don": "DH-MG-1"})
        with pytest.raises(Exception, match="DH-MG-1"):
            MigrationExecutor(connection).migrate([("forms_builder", "0017_datarecord_val_order_code")])
        DataRecord.objects.filter(pk=b.pk).update(data={**b.data, "ma_don": "DH-MG-2"})
    finally:
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
    assert sorted(DataRecord.objects.filter(pk__in=[a.pk, b.pk]).values_list("val_order_code", flat=True)) == [
        "DH-MG-1", "DH-MG-2"]
    with pytest.raises(BusinessError):
        _dong(bang_vd, vd, "DH-MG-2")
    assert TableDef.all_objects.filter(pk=bang_vd.pk).exists()
