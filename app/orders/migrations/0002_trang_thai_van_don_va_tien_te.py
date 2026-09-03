"""Thị trường Canada, Philippines và trạng thái vận đơn theo tệp thật — Q40, Q41.

Hai việc:

1. `Order.currency` nhận thêm CAD và PHP.
2. Bảng vận đơn (`DataRecord` của bảng `van_don`) đang lưu **nhãn** trạng thái
   cũ ("Chờ xử lý", "Đã giao", "Hoàn hàng", "Chờ thanh toán", "Thất bại");
   đổi sang nhãn mới của tệp thật. Nhãn không có trong bảng ánh xạ giữ nguyên.
   Chạy ngược đổi lại đúng nhãn cũ.

Bảng ánh xạ chép cứng ở đây chứ không nhập từ `orders.constants` — tệp
chuyển đổi phải đứng yên khi hằng số đổi tiếp về sau (điều cấm 5).
"""
from django.db import migrations, models

WAYBILL_TABLE_CODE = "van_don"
VAN_CHUYEN = {"Chờ xử lý": "Đã lên đơn", "Đã giao": "Đã nhận hàng", "Hoàn hàng": "Hoàn đơn"}
THANH_TOAN = {"Chờ thanh toán": "Chưa thanh toán", "Thất bại": "Chưa thanh toán"}
# Chiều ngược: "Chưa thanh toán" về "Chờ thanh toán" (không phân biệt được
# "Thất bại" nữa — chấp nhận, vì nhãn cũ ấy không còn nghĩa trong nghiệp vụ)
VAN_CHUYEN_NGUOC = {moi: cu for cu, moi in VAN_CHUYEN.items()}
THANH_TOAN_NGUOC = {"Chưa thanh toán": "Chờ thanh toán"}


def _doi_nhan(apps, van_chuyen, thanh_toan):
    DataRecord = apps.get_model("forms_builder", "DataRecord")
    ds = DataRecord.objects.filter(table__code=WAYBILL_TABLE_CODE)
    for ban_ghi in ds.iterator(chunk_size=500):
        data = dict(ban_ghi.data or {})
        doi = False
        vc = data.get("trang_thai_vc")
        if vc in van_chuyen:
            data["trang_thai_vc"] = van_chuyen[vc]
            doi = True
        tt = data.get("trang_thai_tt")
        if tt in thanh_toan:
            data["trang_thai_tt"] = thanh_toan[tt]
            doi = True
        if not doi:
            continue
        ban_ghi.data = data
        # Cột tách của nhãn Trạng thái theo cột trang_thai_vc
        ban_ghi.val_status = (data.get("trang_thai_vc") or "")[:100]
        ban_ghi.save(update_fields=["data", "val_status"])


def xuoi(apps, schema_editor):
    _doi_nhan(apps, VAN_CHUYEN, THANH_TOAN)


def nguoc(apps, schema_editor):
    _doi_nhan(apps, VAN_CHUYEN_NGUOC, THANH_TOAN_NGUOC)


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0001_initial"),
        ("forms_builder", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="currency",
            field=models.CharField(
                choices=[
                    ("VND", "Việt Nam đồng"),
                    ("USD", "Đô la Mỹ"),
                    ("CAD", "Đô la Canada"),
                    ("PHP", "Peso Philippines"),
                ],
                default="USD",
                max_length=3,
                verbose_name="Loại tiền tệ",
            ),
        ),
        migrations.RunPython(xuoi, nguoc),
    ]
