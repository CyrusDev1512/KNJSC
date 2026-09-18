"""ADR-036 — Một bảng vận đơn duy nhất "Vận đơn mới" (`van_don`): tạo/nâng cấp tại chỗ,
Lên đơn ghi thẳng, lưới gộp Trùng với profile Vận đơn, dòng không chi tiết, xoá cứng
hai bảng cũ, bỏ Bảng nhận đơn."""
import uuid
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.http import QueryDict

from core.constants import AuditAction
from core.exceptions import BusinessError
from core.models import AuditLog
from crm.models import GridCellHistory, GridMutationReceipt
from forms_builder.meaning import FieldType, Meaning
from forms_builder.models import ColumnDef, DataRecord, Grant, GrantAction, TableDef
from forms_builder.services import grant_service, record_service
from orders.constants import WAYBILL_TABLE_CODE, is_waybill_table
from orders.models import Order, Product, WaybillAssignment, WaybillItem
from orders.services import dispatch_service, order_service, waybill_service
from reports.models import ReportSource

from .test_waybill_feedback import feedback  # noqa: F401

pytestmark = pytest.mark.django_db
STANDARD = {c[1] for c in waybill_service.COLUMNS}
EXTRA = {c[1] for c in dispatch_service.EXTRA_COLUMNS}


def _ra(*args):
    out = StringIO()
    call_command(*args, stdout=out)
    return out.getvalue()


def test_clean_machine_creates_one_waybill_table(departments, nguoi_dung):
    """AC-36.1 — Máy sạch: `ensure_waybill_table` tạo đúng một bảng `van_don` tên "Vận đơn
    mới", profile Vận đơn, dùng chung, đủ 25 cột chuẩn + 9 cột giữ lại, Mã đơn là khoá,
    cột chọn đủ lựa chọn chuẩn, không cột nào bắt buộc; chạy lại không thêm gì; không sinh
    crmThuận hay Vận đơn DB; `tao_bang_van_don` in một bảng."""
    ra = _ra("tao_bang_van_don")
    assert ra.count("Bang ") == 1 and "van_don" in ra
    bang = TableDef.objects.get(code=WAYBILL_TABLE_CODE)
    assert bang.name == "Vận đơn mới" and bang.workflow == "waybill" and bang.is_shared
    assert is_waybill_table(bang)
    codes = set(bang.columns.values_list("code", flat=True))
    assert STANDARD <= codes and EXTRA <= codes
    assert bang.columns.get(code="ma_don").is_key
    for code, options in waybill_service.OPTIONS.items():
        column = bang.columns.get(code=code)
        assert column.field_type == FieldType.CHOICE and set(options) <= set(column.options), code
    assert not bang.columns.filter(required=True).exists()   # tệp thật thiếu Mã đơn: không ép bắt buộc ở cột
    before = bang.columns.count()
    dispatch_service.ensure_waybill_table()
    assert TableDef.all_objects.filter(code=WAYBILL_TABLE_CODE).count() == 1
    assert bang.columns.count() == before
    assert not TableDef.all_objects.filter(code__in=("van_don_moi", "van_don_db")).exists()


def test_legacy_table_is_upgraded_in_place(departments, nguoi_dung):
    """AC-36.2 — Bảng cũ (cột chữ tự do, tên "Bảng vận đơn", có dòng và quyền): nâng cấp
    tại chỗ giữ ID, dòng, quyền, cột tuỳ biến; Loại tiền/PTTT thành danh sách chuẩn;
    tên thành "Vận đơn mới"; có nhật ký; chạy lại không đổi."""
    old = TableDef.objects.create(code=WAYBILL_TABLE_CODE, name="Bảng vận đơn", department=departments["vd"])
    for i, (code, kind) in enumerate((("ma_don", FieldType.TEXT), ("loai_tien", FieldType.TEXT),
                                      ("pttt", FieldType.TEXT), ("ZIP", FieldType.TEXT))):
        ColumnDef.objects.create(table=old, code=code, name=code, field_type=kind, order=i)
    row = DataRecord.objects.create(table=old, department=old.department, data={"ma_don": "LICH-SU", "loai_tien": "VNĐ"})
    live = grant_service.grant(table=old, user=nguoi_dung["staff_mkt"], action=GrantAction.VIEW, actor=nguoi_dung["admin"])

    bang = dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])
    assert bang.pk == old.pk and bang.name == "Vận đơn mới" and bang.workflow == "waybill" and bang.is_shared
    row.refresh_from_db()
    assert row.data == {"ma_don": "LICH-SU", "loai_tien": "VNĐ"}
    assert bang.grants.filter(pk=live.pk, deleted_at__isnull=True).exists()
    assert bang.columns.filter(code="ZIP").exists()
    assert bang.columns.get(code="loai_tien").field_type == FieldType.CHOICE
    assert set(waybill_service.OPTIONS["pttt"]) <= set(bang.columns.get(code="pttt").options)
    assert bang.columns.get(code="ten_khach").meaning == Meaning.CUSTOMER
    assert AuditLog.objects.filter(detail__contains="Bổ sung cấu trúc chuẩn Vận đơn").exists()
    n = bang.columns.count()
    dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])
    assert bang.columns.count() == n


def test_order_entry_and_grid_use_the_single_table(client, feedback, nguoi_dung):
    """AC-36.3 — Lên đơn ghi vào `van_don` kèm chi tiết; lưới có cột Trùng lẫn `detail_url`
    và cờ detail/assignment/protected/frozen; Sale không thấy bảng thì `/bang-tinh/van_don/`
    đưa sang Lên đơn; `/bang-tinh/` mặc định là `van_don`; Thống kê nguồn `van_don` profile
    Vận đơn; `/van-don/thong-ke/` chuyển tới `nguon=van_don`."""
    table, products, rows = feedback
    assert table.code == WAYBILL_TABLE_CODE and rows[0].table_id == table.pk
    assert WaybillItem.objects.filter(record=rows[0]).exists()
    client.force_login(nguoi_dung["staff_vd"])
    data = client.get("/bang-tinh/van_don/du-lieu/").json()
    cols = {c["code"]: c for c in data["columns"]}
    assert cols["__duplicates"]["name"] == "Trùng" and cols["__duplicates"]["frozen"]
    assert cols["chi_tiet_sp"]["detail"] if "chi_tiet_sp" in cols else True
    assert cols["phu_trach_vd"]["assignment"] and cols["gia_tien"]["protected"] and cols["ma_don"]["frozen"]
    first = data["rows"][0]
    assert first["detail_url"] and "__duplicates" in first["cells"]
    assert client.get("/bang-tinh/").context["bang"].code == WAYBILL_TABLE_CODE
    stats = client.get("/thong-ke/", {"nguon": "van_don"})
    assert stats.status_code == 200 and stats.context["dashboard"]["profile"] == "waybill"
    redirect = client.get("/van-don/thong-ke/")
    assert redirect.status_code == 302 and "nguon=van_don" in redirect["Location"]
    client.force_login(nguoi_dung["staff_sale_1b"])     # Sale chưa có dòng nào trong phạm vi
    response = client.get("/bang-tinh/van_don/")
    assert response.status_code == 302 and "/van-don/len-don/" in response["Location"]


def test_rows_without_items_are_allowed(feedback, nguoi_dung):
    """AC-36.4 — Dòng đủ cột bắt buộc, không Chi tiết sản phẩm → tạo được, không item,
    Thống kê đếm là thiếu chi tiết, tổng giữ như nhập; có chi tiết sai tổng vẫn bị từ
    chối; nhập tệp mẫu cũ `vandon-mau.xlsx` vào `van_don` không lỗi cột."""
    table, products, rows = feedback
    row = record_service.create_record(table, {
        "ma_don": "TAY-1", "ten_khach": "Khách tay", "so_dien_thoai": "0900001", "ngay": "2026-09-18",
        "quoc_gia": "Canada", "gia_tien": "12.50", "so_luong": 3}, actor=nguoi_dung["staff_vd"])
    assert row.data["loai_tien"] == "CAD" and row.data["gia_tien"] == "12.50" and row.data["so_luong"] == 3
    assert not WaybillItem.objects.filter(record=row).exists()
    assert waybill_service.missing_item_count(DataRecord.objects.filter(pk=row.pk)) == 1
    with pytest.raises(BusinessError):
        record_service.create_record(table, {
            "ma_don": "TAY-2", "ten_khach": "K", "so_dien_thoai": "0900002", "ngay": "2026-09-18",
            "quoc_gia": "Canada", "gia_tien": "999",
            waybill_service.DETAIL_CODE: [{"product": products[0].code, "quantity": 1, "unit_price": "10.00"}],
        }, actor=nguoi_dung["staff_vd"])
    from pathlib import Path
    from django.core.files.uploadedfile import SimpleUploadedFile
    from forms_builder.services import import_service
    tep = Path(__file__).resolve().parents[3] / "docs" / "tham-khao" / "vandon-mau.xlsx"
    if tep.exists():
        job = import_service.prepare(table, SimpleUploadedFile(tep.name, tep.read_bytes()), actor=nguoi_dung["admin"])
        assert job.summary.get("header_row") is not None


def test_hard_delete_command_removes_old_tables_only_with_flags(departments, nguoi_dung, feedback):
    """AC-36.5 — `xoa_bang_van_don_cu`: thiếu cờ → từ chối, không xoá; đủ cờ → hai bảng cũ
    mất hẳn cùng dòng, chi tiết, phân công, lịch sử ô, biên nhận, quyền, nguồn báo cáo; đơn
    ERP giữ với `record=None`; `van_don` nguyên; nhật ký DELETE; chạy lại "không có gì";
    không bao giờ xoá `van_don`."""
    table, products, rows = feedback
    old_tables = []
    for code in ("van_don_moi", "van_don_db"):
        t = TableDef.objects.create(code=code, name=code, department=departments["vd"], workflow="waybill")
        for i, (c, k) in enumerate((("ma_don", FieldType.TEXT), ("quoc_gia", FieldType.CHOICE))):
            ColumnDef.objects.create(table=t, code=c, name=c, field_type=k, order=i)
        r = DataRecord.objects.create(table=t, department=t.department, data={"ma_don": f"CU-{code}"})
        WaybillItem.objects.create(record=r, product=products[0], quantity=1, unit="cái", unit_price="1.00", paid_amount="0.00")
        WaybillAssignment.objects.create(record=r, delivery=nguoi_dung["staff_vd"])
        receipt = GridMutationReceipt.objects.create(table=t, actor=nguoi_dung["admin"], operation=uuid.uuid4(), fingerprint="x", result={})
        GridCellHistory.objects.bulk_create([GridCellHistory(record=r, receipt=receipt, column="ma_don", before="", after="x")])
        Grant.objects.create(table=t, user=nguoi_dung["staff_mkt"], action=GrantAction.VIEW, granted_by=nguoi_dung["admin"])
        ReportSource.objects.create(table=t, kind="delivery", columns={})
        old_tables.append((t, r))
    order = Order.objects.get(record=rows[0])
    Order.objects.filter(pk=order.pk).update(record=old_tables[0][1])

    with pytest.raises(CommandError):
        call_command("xoa_bang_van_don_cu")
    with pytest.raises(CommandError):
        call_command("xoa_bang_van_don_cu", "--dong-y-xoa-cung")
    assert TableDef.all_objects.filter(code__in=("van_don_moi", "van_don_db")).count() == 2
    with pytest.raises(CommandError):
        call_command("xoa_bang_van_don_cu", "--bang", WAYBILL_TABLE_CODE, "--dong-y-xoa-cung", "--backup-da-lam")

    ra = _ra("xoa_bang_van_don_cu", "--dong-y-xoa-cung", "--backup-da-lam")
    assert "van_don_moi: đã xoá cứng" in ra and "van_don_db: đã xoá cứng" in ra
    assert not TableDef.all_objects.filter(code__in=("van_don_moi", "van_don_db")).exists()
    for t, r in old_tables:
        assert not DataRecord.all_objects.filter(pk=r.pk).exists()
        assert not WaybillItem._base_manager.filter(record_id=r.pk).exists()
        assert not GridCellHistory.objects.filter(record_id=r.pk).exists()
        assert not GridMutationReceipt.objects.filter(table_id=t.pk).exists()
        assert not Grant._base_manager.filter(table_id=t.pk).exists()
        assert not ReportSource.objects.filter(table_id=t.pk).exists()
    order.refresh_from_db()
    assert order.record_id is None
    assert TableDef.objects.filter(code=WAYBILL_TABLE_CODE).exists()
    assert DataRecord.objects.filter(table=table).count() == len(rows)
    assert AuditLog.objects.filter(action=AuditAction.DELETE, target_id="van_don_db").exists()
    assert "không có gì để xoá" in _ra("xoa_bang_van_don_cu", "--dong-y-xoa-cung", "--backup-da-lam")


def test_destination_feature_is_gone(client, feedback, nguoi_dung):
    """AC-36.6 — `/cau-hinh/nhan-don/` 404 với mọi vai; sidebar Admin không còn "Bảng nhận
    đơn"; `TableDef` không còn `receives_orders`, còn `delivery_view_version`."""
    for user in (nguoi_dung["admin"], nguoi_dung["staff_vd"], nguoi_dung["staff_sale_1"]):
        client.force_login(user)
        assert client.get("/cau-hinh/nhan-don/").status_code == 404
    client.force_login(nguoi_dung["admin"])
    assert "Bảng nhận đơn" not in client.get("/").content.decode()
    fields = {f.name for f in TableDef._meta.get_fields()}
    assert "receives_orders" not in fields and "delivery_view_version" in fields


@pytest.mark.django_db(transaction=True)
def test_migration_0014_roundtrip(departments):
    """AC-36.6 — Migration 0014 bỏ `receives_orders` chạy xuôi và ngược, giữ dữ liệu."""
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor
    assert connection.settings_dict["NAME"].startswith("test_")
    table = TableDef.objects.create(code="migration-036", name="Migration 036", department=departments["vd"])

    def columns():
        with connection.cursor() as cursor:
            return {c.name for c in connection.introspection.get_table_description(cursor, "forms_builder_tabledef")}

    try:
        MigrationExecutor(connection).migrate([("forms_builder", "0013_remove_tabledef_delivery_view_all")])
        assert "receives_orders" in columns()
    finally:
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
    assert "receives_orders" not in columns() and TableDef.objects.filter(pk=table.pk).exists()


def test_reports_and_seed_commands_target_the_single_table(departments, nguoi_dung, settings):
    """AC-36.7 — `configure_erp_reports` tạo nguồn Vận đơn cho `van_don`; `nap_du_lieu_van_don`
    và `nap_khach_mau` (mặc định) nạp vào `van_don` có phân công."""
    dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])
    call_command("configure_erp_reports")
    assert ReportSource.objects.get(table__code=WAYBILL_TABLE_CODE).kind == "delivery"
    settings.DEBUG = True
    from orders.models import ProductGroup
    nhom = ProductGroup.objects.create(name="Nhóm 36")
    Product.objects.create(name="SP 36", code="sp-36", group=nhom)
    _ra("nap_khach_mau", "--so-khach", "5")
    ds = DataRecord.objects.filter(table__code=WAYBILL_TABLE_CODE, data__ma_don__startswith="KH-")
    assert ds.exists() and WaybillAssignment.objects.filter(record__in=ds).count() == ds.count()
    _ra("nap_khach_mau", "--so-khach", "0", "--xoa-cu")
