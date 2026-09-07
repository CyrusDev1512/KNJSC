"""Hai chỉ mục cho KN CRM ở cỡ 100 nghìn dòng (K27): `moi-nhat/` lấy Max(updated_at)
theo bảng, cột Trùng gộp theo số điện thoại trong bảng. Đảo ngược: bỏ chỉ mục."""
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("forms_builder", "0008_columndef_options_highlight_alert")]

    operations = [
        migrations.AddIndex(
            model_name="datarecord",
            index=models.Index(fields=["table", "updated_at"], name="record_table_updated_idx"),
        ),
        migrations.AddIndex(
            model_name="datarecord",
            index=models.Index(fields=["table", "val_phone"], name="record_table_phone_idx"),
        ),
    ]
