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


def test_ma_don_moi_bo_qua_ma_da_co_tren_bang(bang_vd, nguoi_dung):
    """AC-36.11 — Bảng đã có dòng mang đúng mã kế tiếp của hôm nay mà không có đơn (nhập từ hệ thống cũ): Lên đơn nhảy
    qua mã đó, không đụng mã và không hỏng"""
    from django.utils import timezone
    from orders.models import Product, ProductGroup
    from orders.tests.test_len_don import _len_don

    dau = f"DH-{timezone.localdate():%d%m}-"
    _dong(bang_vd, nguoi_dung["staff_vd"], f"{dau}0001")
    _dong(bang_vd, nguoi_dung["staff_vd"], f"{dau}0002")
    nhom = ProductGroup.objects.create(name="Nhóm thử")
    sp = {"massage": Product.objects.create(name="Máy thử", code="may_thu", group=nhom)}
    assert _len_don(nguoi_dung["staff_sale_1"], sp).code == f"{dau}0003"


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


def _ve_0016_co_trung(bang_vd, nguoi_dung):
    """Lùi `forms_builder` về 0016 (mã mới chạy trên DB cũ, như lúc vừa cập nhật) rồi tạo trùng có từ trước: dòng thường
    tạo trước (số dòng nhỏ hơn) mang mã của dòng gắn đơn gốc tạo sau. Trả (dòng thường, dòng gắn đơn, đơn)."""
    from orders.models import Product, ProductGroup
    from orders.tests.test_len_don import _len_don

    thuong = _dong(bang_vd, nguoi_dung["staff_vd"], "DH-TAM")
    nhom = ProductGroup.objects.create(name="Nhóm thử")
    don = _len_don(nguoi_dung["staff_sale_1"], {"massage": Product.objects.create(name="Máy thử", code="may_thu", group=nhom)})
    with connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
    MigrationExecutor(connection).migrate([("forms_builder", "0016_datarecord_val_phone_key")])
    DataRecord.objects.filter(pk=thuong.pk).update(data={**thuong.data, "ma_don": f" {don.code} "})
    return thuong, don.record, don


def _ve_moi_nhat():
    executor = MigrationExecutor(connection)
    executor.migrate(executor.loader.graph.leaf_nodes())


def _cot_khoa_ma_don():
    with connection.cursor() as cursor:
        return "val_order_code" in {c.name for c in connection.introspection.get_table_description(
            cursor, DataRecord._meta.db_table)}


def test_kiem_tra_du_lieu_truoc_0017_liet_ke_va_doi_ma_trung(bang_vd, nguoi_dung, capsys):
    """AC-36.15 — DB chưa chạy `forms_builder/0017` (mã mới vừa cập nhật): `kiem_tra_du_lieu` không đổ, chỉ rà mã đơn
    trùng đúng như migration sẽ rà, liệt kê và thoát mã 1; `--sua` giữ dòng gắn đơn gốc, đổi mã dòng thừa thành
    `TRUNG-<số dòng>-<mã cũ>`, ghi nhật ký từng dòng; sau đó migrate chạy được (TL-76)"""
    from django.core.management import call_command

    from core.models import AuditLog

    try:
        thuong, gan_don, don = _ve_0016_co_trung(bang_vd, nguoi_dung)
        assert not _cot_khoa_ma_don()
        with pytest.raises(SystemExit) as thoat:
            call_command("kiem_tra_du_lieu")
        ra = capsys.readouterr().out
        assert thoat.value.code == 1
        assert "chưa chạy migration forms_builder 0017" in ra and f"{don.code} (2 dòng)" in ra and "--sua" in ra

        call_command("kiem_tra_du_lieu", "--sua")
        ra = capsys.readouterr().out
        moi = f"TRUNG-{thuong.pk}-{don.code}"
        assert moi in ra and "Dữ liệu khớp." in ra
        ma = dict(DataRecord.all_objects.filter(pk__in=[thuong.pk, gan_don.pk]).values_list("pk", "data__ma_don"))
        assert ma == {thuong.pk: moi, gan_don.pk: don.code}
        nhat_ky = AuditLog.objects.filter(target_type="DataRecord", target_id=str(thuong.pk), actor_label="kiem_tra_du_lieu")
        assert nhat_ky.count() == 1 and don.code in nhat_ky.get().detail and moi in nhat_ky.get().detail
        _ve_moi_nhat()
    finally:
        _ve_moi_nhat()
    assert _cot_khoa_ma_don()
    assert DataRecord.objects.get(pk=thuong.pk).val_order_code == moi


def test_migrate_dung_truoc_khi_ap_khi_con_ma_trung(bang_vd, nguoi_dung):
    """AC-36.16 — `manage.py migrate` trên DB còn mã đơn trùng dừng trước khi áp bất cứ migration nào, nêu mã trùng và
    cách gỡ chạy được trên DB cũ (`kiem_tra_du_lieu --sua`), không bảo sửa trên lưới; gỡ xong thì migrate chạy được (TL-76)"""
    from django.core.management import call_command
    from django.core.management.base import CommandError
    from django.db.migrations.recorder import MigrationRecorder

    try:
        _, _, don = _ve_0016_co_trung(bang_vd, nguoi_dung)
        with pytest.raises(CommandError) as loi:
            call_command("migrate", "forms_builder", verbosity=0)
        assert don.code in str(loi.value) and "kiem_tra_du_lieu --sua" in str(loi.value)
        assert "trên lưới" not in str(loi.value)
        assert not MigrationRecorder(connection).migration_qs.filter(
            app="forms_builder", name="0017_datarecord_val_order_code").exists()
        assert not _cot_khoa_ma_don()
        call_command("kiem_tra_du_lieu", "--sua", stdout=__import__("io").StringIO())
        call_command("migrate", "forms_builder", verbosity=0)
        assert _cot_khoa_ma_don()
    finally:
        _ve_moi_nhat()
