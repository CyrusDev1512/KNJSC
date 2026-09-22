"""Khoá so trùng số điện thoại — TL-36, chốt 22.09.2026.

Cột Trùng trước nay so `val_phone` **đúng như gõ**: `+1 (416) 555-0123`,
`416 555 0123` và `4165550123` bị coi là ba khách khác nhau, nhân viên không biết
đây là khách cũ. Khoá `val_phone_key` = 9 chữ số cuối sau khi bỏ ký tự không phải
số; ô hiển thị vẫn giữ nguyên chữ nhân viên gõ.

Backfill một lệnh UPDATE cho dòng cũ (120 nghìn dòng đi trong một lượt trên máy đo).
Chạy ngược: bỏ cột — dữ liệu khoá suy ra được từ `val_phone` nên không mất gì.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("forms_builder", "0015_columndef_is_hidden"),
    ]

    operations = [
        migrations.AddField(
            model_name="datarecord",
            name="val_phone_key",
            field=models.CharField(
                "Khoá so trùng số điện thoại", max_length=9, blank=True, default=""),
        ),
        migrations.AddIndex(
            model_name="datarecord",
            index=models.Index(
                fields=["table", "val_phone_key"], name="record_table_phonekey_idx"),
        ),
        migrations.RunSQL(
            sql=(
                "UPDATE forms_builder_datarecord "
                "SET val_phone_key = right(regexp_replace(val_phone, '\\D', '', 'g'), 9) "
                "WHERE val_phone <> ''"
            ),
            # Chạy ngược không cần trả dữ liệu: AddField đảo sẽ bỏ luôn cột
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
