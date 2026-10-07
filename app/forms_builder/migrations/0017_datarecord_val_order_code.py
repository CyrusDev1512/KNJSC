"""Mỗi mã đơn một dòng sống ở bảng vận đơn — chốt 06.10.2026.

Thêm cột `val_order_code` (mã đơn đã cắt khoảng trắng, chỉ bảng vận đơn), điền cho dòng cũ, rồi tạo ràng buộc duy
nhất một phần `record_ma_don_unique` trên `(table, val_order_code)` cho dòng chưa xoá có mã.

Dữ liệu đang có hai dòng sống cùng mã thì **dừng**, liệt kê mã trùng, không tạo ràng buộc nửa vời; cả migration
quay lui (Postgres chạy trong một giao dịch). Dọn trùng trên lưới (xoá hoặc sửa mã) rồi chạy lại. Rà trước khi
phát hành: `manage.py kiem_tra_du_lieu`.

Chạy ngược: bỏ ràng buộc và cột — khoá suy ra lại được từ `data`, không mất gì.
"""
from django.db import migrations, models

# Cùng điều kiện với `orders.constants.is_waybill_table`
DIEN_KHOA = """
UPDATE forms_builder_datarecord AS r
SET val_order_code = left(btrim(coalesce(r.data->>'ma_don', '')), 200)
FROM forms_builder_tabledef AS t
WHERE r.table_id = t.id AND (t.code = 'van_don' OR t.workflow = 'waybill')
  AND btrim(coalesce(r.data->>'ma_don', '')) <> ''
"""


def dung_neu_con_trung(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            SELECT val_order_code, count(*) FROM forms_builder_datarecord
            WHERE deleted_at IS NULL AND val_order_code <> ''
            GROUP BY table_id, val_order_code HAVING count(*) > 1
            ORDER BY val_order_code LIMIT 20
        """)
        trung = cursor.fetchall()
    if trung:
        ds = ", ".join(f"{ma} ({so} dòng)" for ma, so in trung)
        raise RuntimeError(
            "Bảng vận đơn đang có mã đơn trùng giữa các dòng chưa xoá: " + ds
            + ". Sửa mã hoặc xoá dòng thừa trên lưới rồi chạy lại migrate; danh sách đủ: manage.py kiem_tra_du_lieu.")


class Migration(migrations.Migration):

    dependencies = [
        ("forms_builder", "0016_datarecord_val_phone_key"),
    ]

    operations = [
        migrations.AddField(
            model_name="datarecord",
            name="val_order_code",
            field=models.CharField(
                "Mã đơn (khoá chống trùng)", max_length=200, blank=True, default="", db_default=""),
        ),
        # Chạy ngược không cần trả dữ liệu: AddField đảo sẽ bỏ luôn cột
        migrations.RunSQL(sql=DIEN_KHOA, reverse_sql=migrations.RunSQL.noop),
        migrations.RunPython(dung_neu_con_trung, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="datarecord",
            constraint=models.UniqueConstraint(
                fields=["table", "val_order_code"], name="record_ma_don_unique",
                condition=models.Q(deleted_at__isnull=True) & ~models.Q(val_order_code=""),
            ),
        ),
    ]
