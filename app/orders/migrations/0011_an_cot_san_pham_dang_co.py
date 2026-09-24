"""Ẩn với cả công ty toàn bộ cột số lượng theo sản phẩm đang có — ADR-039 bổ sung 22.09.

Từ nay `dispatch_service.sync_product_columns` sinh cột sản phẩm ở trạng thái ẩn luôn.
Tệp này lo phần còn lại: các cột `sl_*` đã mọc trước đó trên bảng vận đơn, gồm cả cột
của sản phẩm gõ thử. Chỉ đổi cờ hiển thị — không xoá cột, không đụng một ô dữ liệu nào,
nên `mua_lai` và số lượng của 221 dòng nhập từ tệp thật vẫn còn nguyên và hiện lại đủ.

Chạy ngược là **không làm gì**: cột vẫn còn cùng dữ liệu, quản lý bảng bật lại bất cứ
lúc nào bằng mục "Đang ẩn với cả công ty" trong hộp "Cột". Nếu chạy ngược mà tự hiện
lại cả nhóm thì sẽ xoá luôn lựa chọn người dùng đã bấm tay trước đó.
"""
from django.db import migrations

#: Tiền tố mã cột sản phẩm. Viết thẳng ở đây thay vì import
#: `dispatch_service.PRODUCT_COLUMN_PREFIX`: tệp chuyển đổi phải chạy được y nguyên trong
#: tương lai, kể cả khi mã nguồn đổi hằng số đó.
TIEN_TO = "sl_"


def an_cot_san_pham(apps, schema_editor):
    ColumnDef = apps.get_model("forms_builder", "ColumnDef")
    ColumnDef.objects.filter(
        code__startswith=TIEN_TO, is_hidden=False,
        table__workflow="waybill",
    ).update(is_hidden=True)


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0010_payment_methods_seven"),
        ("forms_builder", "0015_columndef_is_hidden"),
    ]

    operations = [
        migrations.RunPython(an_cot_san_pham, migrations.RunPython.noop),
    ]
