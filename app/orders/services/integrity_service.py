"""Rà toàn vẹn dữ liệu — lệnh `kiem_tra_du_lieu` (06.10.2026).

Chỉ đọc. Chạy được trên VPS trước và sau mỗi lần phát hành để biết dữ liệu có lệch không, thay vì đợi người dùng
thấy số sai. Năm phép rà, mỗi phép trả `(số chỗ lệch, vài ví dụ)`:

1. **Cột tách lệch `data`** (`val_*`, khoá số điện thoại, khoá mã đơn) và cột tính sẵn chưa tính lại — tính lại
   trong bộ nhớ rồi so, đúng như `resync_table` sẽ làm. Sửa được bằng `--sua` (gọi `resync_table`).
2. **Mã đơn trùng** giữa các dòng chưa xoá của bảng vận đơn (đọc từ `data`, bắt được cả dữ liệu trước migration
   `forms_builder/0017`).
3. **Đơn mồ côi**: đơn còn sống mà dòng vận đơn đã xoá hay không có; dòng còn sống mà đơn đã bỏ.
4. **Cột `sl_*` lệch Chi tiết sản phẩm** (`WaybillItem` còn sống) — chỉ để biết, **không** tính vào mã thoát: cột ẩn
   mặc định và chưa có đường nào giữ nó theo Chi tiết (sửa Chi tiết trên lưới, `nap_du_lieu_van_don` đều không ghi).
5. **Giá trị ngoài danh sách chọn** của cột Chọn một (danh sách bị sửa sau khi đã nhập).

**Trước migration `forms_builder/0017`** (mã mới vừa cập nhật, DB chưa có cột khoá mã đơn) chỉ phép rà mã đơn trùng
chạy được — các phép khác nạp cả dòng `DataRecord`, gồm cột chưa có. Lúc đó lệnh rà đúng như migration sẽ rà, và
`--sua` đổi mã các dòng thừa để migrate chạy được (TL-76). `migrate` cũng dừng sớm với lời chỉ cách gỡ này
(`chan_migrate_khi_trung_ma`, nối ở `orders/apps.py`), thay vì dừng giữa chừng ở `0017`.
"""
from collections import defaultdict

from django.core.management.base import CommandError
from django.db import connections, transaction
from django.db.models import Count, Q
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Trim

from forms_builder import choice_registry
from forms_builder.meaning import FieldType
from forms_builder.models import DERIVED_FIELDS, DataRecord, TableDef
from forms_builder.services.table_service import _giong, resync_table

from ..constants import waybill_condition
from ..models import Order, WaybillItem
from .dispatch_service import PRODUCT_COLUMN_PREFIX, product_column_code_of

LO = 2000
VI_DU = 5


def _ket_qua():
    return {"so": 0, "vi_du": []}


def _ghi(kq, vi_du):
    kq["so"] += 1
    if len(kq["vi_du"]) < VI_DU:
        kq["vi_du"].append(vi_du)


def lech_cot_tach(table):
    """Số dòng (kể cả đã xoá) mà cột tách hay cột tính sẵn khác với kết quả tính lại từ `data`."""
    kq = _ket_qua()
    cot = list(table.columns.all())
    pks = list(DataRecord.all_objects.filter(table=table).order_by("pk").values_list("pk", flat=True))
    for i in range(0, len(pks), LO):
        for ban_ghi in DataRecord.all_objects.filter(pk__in=pks[i:i + LO]).select_related("table").order_by("pk"):
            truoc = (dict(ban_ghi.data), *(getattr(ban_ghi, c) for c in DERIVED_FIELDS))
            ban_ghi.apply_computed_columns(cot)
            ban_ghi.sync_indexed_columns(cot)
            sau = (ban_ghi.data, *(getattr(ban_ghi, c) for c in DERIVED_FIELDS))
            khac = [c for c, a, b in zip(("data", *DERIVED_FIELDS), truoc, sau) if not _giong(a, b)]
            if khac:
                _ghi(kq, f"dòng #{ban_ghi.pk}: {', '.join(khac)}")
    return kq


def ma_don_trung(table):
    kq = _ket_qua()
    nhom = (DataRecord.objects.filter(table=table)
            .annotate(ma=Trim(KeyTextTransform("ma_don", "data"))).exclude(ma__isnull=True).exclude(ma="")
            .values("ma").annotate(n=Count("id")).filter(n__gt=1).order_by("ma"))
    for dong in nhom:
        _ghi(kq, f"{dong['ma']} ({dong['n']} dòng)")
    return kq


def don_mo_coi():
    kq = _ket_qua()
    for don in (Order.all_objects.filter(deleted_at__isnull=True)
                .filter(Q(record__isnull=True) | Q(record__deleted_at__isnull=False))
                .only("code", "record_id").order_by("pk")):
        _ghi(kq, f"đơn {don.code} còn sống, dòng vận đơn đã xoá hoặc không có")
    for don in (Order.all_objects.filter(deleted_at__isnull=False, record__deleted_at__isnull=True)
                .only("code").order_by("pk")):
        _ghi(kq, f"đơn {don.code} đã bỏ, dòng vận đơn còn sống")
    return kq


def so_luong_lech(table):
    kq = _ket_qua()
    # Chỉ so sản phẩm đã có cột: sản phẩm thêm sau lần chạy `sync_product_columns` gần nhất chưa có ô để ghi
    co_cot = set(table.columns.filter(code__startswith=PRODUCT_COLUMN_PREFIX).values_list("code", flat=True))
    tong = defaultdict(dict)
    for record_id, product_code, qty in (WaybillItem.objects.filter(record__table=table, deleted_at__isnull=True)
                                         .values_list("record_id", "product__code", "quantity")):
        ma = product_column_code_of(product_code)
        if ma not in co_cot:
            continue
        tong[record_id][ma] = tong[record_id].get(ma, 0) + qty
    for pk, data in DataRecord.objects.filter(table=table).values_list("pk", "data").order_by("pk"):
        co = {k: _so(v) for k, v in data.items()
              if k in co_cot and v not in (None, "", 0, "0")}
        if co != tong.get(pk, {}):
            _ghi(kq, f"dòng #{pk}")
    return kq


def _so(v):
    try:
        return int(str(v))
    except ValueError:
        return v


def ngoai_danh_sach(table):
    kq = _ket_qua()
    for cot in table.columns.filter(field_type=FieldType.CHOICE, is_computed=False):
        ds = choice_registry.snapshot(choice_registry.for_column(cot))
        if ds is None:
            continue
        gia_tri = (DataRecord.objects.filter(table=table, data__has_key=cot.code)
                   .values_list(f"data__{cot.code}", flat=True).distinct())
        for v in gia_tri:
            if v in (None, ""):
                continue
            if not choice_registry.match(ds, str(v))[1]:
                n = DataRecord.objects.filter(table=table, **{f"data__{cot.code}": v}).count()
                _ghi(kq, f'cột {cot.code}: "{v}" ({n} dòng)')
                kq["so"] += n - 1
    return kq


#: Migration tạo cột khoá mã đơn và ràng buộc mỗi mã một dòng sống
MIGRATION_KHOA_MA_DON = ("forms_builder", "0017_datarecord_val_order_code")
TIEN_TO_DOI_MA = "TRUNG"

# Cùng điều kiện, cùng khoá với `forms_builder/0017` (điền khoá rồi rà trùng), đọc thẳng `data` nên chạy được trên DB
# chưa có cột khoá: rà trước đúng như migration sẽ rà. Kể cả bảng vận đơn đã xoá mềm, như migration.
_SQL_MA_TRUNG = """
SELECT r.table_id, left(btrim(coalesce(r.data->>'ma_don', '')), 200) AS ma, array_agg(r.id ORDER BY r.id)
FROM forms_builder_datarecord r JOIN forms_builder_tabledef t ON t.id = r.table_id
WHERE (t.code = 'van_don' OR t.workflow = 'waybill') AND r.deleted_at IS NULL
  AND btrim(coalesce(r.data->>'ma_don', '')) <> ''
GROUP BY r.table_id, left(btrim(coalesce(r.data->>'ma_don', '')), 200)
HAVING count(*) > 1
ORDER BY 2
"""


def chua_co_khoa_ma_don(using="default"):
    """DB chưa chạy `forms_builder/0017`: bảng dòng chưa có cột `val_order_code` (mã mới chạy trên lược đồ cũ)."""
    ket_noi = connections[using]
    with ket_noi.cursor() as cursor:
        if DataRecord._meta.db_table not in ket_noi.introspection.table_names(cursor):
            return False
        cot = ket_noi.introspection.get_table_description(cursor, DataRecord._meta.db_table)
    return "val_order_code" not in {c.name for c in cot}


def nhom_ma_trung(using="default"):
    """Các nhóm dòng sống cùng mã đơn trong một bảng vận đơn: `[{"table_id", "ma", "ids"}]`, id tăng dần."""
    with connections[using].cursor() as cursor:
        cursor.execute(_SQL_MA_TRUNG)
        return [{"table_id": bang, "ma": ma, "ids": list(ids)} for bang, ma, ids in cursor.fetchall()]


def doi_ma_trung(nhom, on_line=print, using="default"):
    """Mỗi nhóm trùng giữ một dòng, đổi mã các dòng thừa thành `TRUNG-<số dòng>-<mã cũ>` — không xoá, không mất dữ
    liệu; người dùng sửa lại mã đúng trên lưới sau khi cập nhật (lọc Mã đơn bắt đầu bằng `TRUNG-`).

    Giữ dòng gắn đơn gốc mang đúng mã đó (mã đơn hàng là duy nhất nên nhiều nhất một dòng như vậy), không có thì giữ
    dòng tạo trước. Ghi bằng SQL trên `data` để chạy được trước `0017`; mỗi dòng đổi một dòng nhật ký. Trả số dòng đã đổi.
    """
    from core.audit import record
    from core.constants import AuditAction

    so = 0
    with transaction.atomic(using=using), connections[using].cursor() as cursor:
        for g in nhom:
            giu = (Order.all_objects.using(using).filter(record_id__in=g["ids"], code=g["ma"])
                   .values_list("record_id", flat=True).first()) or g["ids"][0]
            for pk in g["ids"]:
                if pk == giu:
                    continue
                moi = f"{TIEN_TO_DOI_MA}-{pk}-{g['ma']}"[:200]
                cursor.execute(
                    f"UPDATE {DataRecord._meta.db_table} SET data = jsonb_set(data, '{{ma_don}}', to_jsonb(%s::text)), "
                    "updated_at = now() WHERE id = %s", [moi, pk])
                record(AuditAction.UPDATE, target=("DataRecord", pk), actor_label="kiem_tra_du_lieu",
                       detail=f"Đổi mã đơn trùng {g['ma']} → {moi}, giữ dòng #{giu} (trước migration 0017)")
                on_line(f"  Đổi mã dòng #{pk}: {g['ma']} → {moi} (giữ dòng #{giu})")
                so += 1
    return so


def _truoc_khoa_ma_don(*, fix, on_line):
    on_line("Cơ sở dữ liệu chưa chạy migration forms_builder 0017 (khoá mã đơn): chỉ rà mã đơn trùng.")
    nhom = nhom_ma_trung()
    if nhom and fix:
        so = doi_ma_trung(nhom, on_line)
        on_line(f"  Đã đổi mã {so} dòng thừa. Sau khi cập nhật, sửa lại mã đúng trên lưới: lọc Mã đơn bắt đầu bằng "
                f"{TIEN_TO_DOI_MA}-.")
        nhom = nhom_ma_trung()
    vi_du = "; ".join(f"{g['ma']} ({len(g['ids'])} dòng)" for g in nhom[:VI_DU])
    on_line(f"  {'LỆCH' if nhom else 'ĐẠT'} · mã đơn trùng (dòng chưa xoá): {len(nhom)}" + (f" — {vi_du}" if vi_du else ""))
    on_line("  Chạy `python manage.py kiem_tra_du_lieu --sua` để đổi mã các dòng thừa, rồi chạy migrate." if nhom
            else "  Không còn mã đơn trùng: chạy migrate được.")
    return len(nhom)


def chan_migrate_khi_trung_ma(sender, plan=None, using="default", **kwargs):
    """`pre_migrate` của forms_builder: kế hoạch có `0017` (chiều xuôi) mà dữ liệu còn mã đơn trùng thì dừng ngay, trước
    khi áp migration nào, kèm cách gỡ chạy được trên DB cũ (TL-76). Không có `0017` trong kế hoạch (DB đã nâng cấp)
    hay bảng chưa có (DB mới) thì không làm gì."""
    app, ten = MIGRATION_KHOA_MA_DON
    if not any(m.app_label == app and m.name == ten and not lui for m, lui in (plan or [])):
        return
    ket_noi = connections[using]
    with ket_noi.cursor() as cursor:
        if DataRecord._meta.db_table not in ket_noi.introspection.table_names(cursor):
            return
    nhom = nhom_ma_trung(using)
    if nhom:
        raise CommandError(
            "Bảng vận đơn đang có mã đơn trùng giữa các dòng chưa xoá: "
            + ", ".join(f"{g['ma']} ({len(g['ids'])} dòng)" for g in nhom[:20])
            + ". Chưa áp migration nào. Chạy `python manage.py kiem_tra_du_lieu --sua` để đổi mã các dòng thừa thành "
            f"{TIEN_TO_DOI_MA}-<số dòng>-<mã cũ> (giữ dòng gắn đơn gốc), rồi chạy lại migrate. Máy local: "
            "docker compose -f deploy/docker-compose.yml run --rm -e RUN_MIGRATIONS=0 web python manage.py "
            "kiem_tra_du_lieu --sua")


def run(*, tables=None, fix=False, on_line=print):
    """Chạy năm phép rà, in từng dòng qua `on_line`. Trả tổng số chỗ lệch **sau** khi sửa (`fix`).
    DB chưa có khoá mã đơn (trước `0017`): chỉ rà mã đơn trùng, `fix` thì đổi mã dòng thừa."""
    if chua_co_khoa_ma_don():
        return _truoc_khoa_ma_don(fix=fix, on_line=on_line)
    bang = list(tables if tables is not None else TableDef.all_objects.filter(deleted_at__isnull=True).order_by("code"))
    van_don = set(TableDef.all_objects.filter(waybill_condition("")).values_list("pk", flat=True))
    tong = 0

    def bao(ten, kq, *, tinh=True):
        nonlocal tong
        tong += kq["so"] if tinh else 0
        nhan = "ĐẠT" if not kq["so"] else ("LỆCH" if tinh else "BIẾT")
        on_line(f"  {nhan} · {ten}: {kq['so']}"
                + (" — " + "; ".join(kq["vi_du"]) if kq["vi_du"] else ""))

    for t in bang:
        on_line(f"Bảng {t.code} ({DataRecord.all_objects.filter(table=t).count()} dòng)")
        kq = lech_cot_tach(t)
        if kq["so"] and fix:
            resync_table(t)
            on_line(f"  Đã tính lại {kq['so']} dòng lệch.")
            kq = lech_cot_tach(t)
        bao("cột tách / cột tính sẵn lệch data", kq)
        bao("giá trị ngoài danh sách chọn", ngoai_danh_sach(t))
        if t.pk in van_don:
            bao("mã đơn trùng (dòng chưa xoá)", ma_don_trung(t))
            bao("sl_* lệch Chi tiết sản phẩm (không tính vào mã thoát)", so_luong_lech(t), tinh=False)
    on_line("Đơn hàng")
    bao("đơn mồ côi", don_mo_coi())
    return tong
