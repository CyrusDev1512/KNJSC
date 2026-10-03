"""Báo cáo Marketing nộp bằng tiền Việt (ADR-047, chủ dự án 03.10.2026): dòng báo cáo MKT đã nộp đổi nhãn Loại tiền
sang VND, **số giữ nguyên**, không nhân tỉ giá — nhân viên vốn gõ số tiền Việt, nhãn CAD/USD là do hệ thống tự gắn
theo Thị trường. Bảng Sale không đụng. Chạy ngược: nhãn lấy lại theo Thị trường như trước (ADR-031)."""
from django.db import migrations

VND = "VND"
#: Ảnh chụp `currency_service.MARKET_CURRENCIES` theo nhãn lúc viết tệp — tệp chuyển đổi không đọc mã đang chạy
THEO_THI_TRUONG = {"hoa kỳ": "USD", "canada": "CAD", "philippines": "PHP", "châu âu": "EUR",
                   "hàn quốc": "KRW", "nhật bản": "JPY", "úc": "AUD"}


def _nguon_mkt(apps):
    ReportSource = apps.get_model("reports", "ReportSource")
    for nguon in ReportSource.objects.filter(kind="mkt").select_related("table"):
        cot = (nguon.columns or {}).get("currency")
        if cot:
            yield nguon, cot, (nguon.columns or {}).get("market")


def _doi(apps, gia_tri):
    DataRecord = apps.get_model("forms_builder", "DataRecord")
    for nguon, cot, cot_thi_truong in _nguon_mkt(apps):
        doi = []
        for dong in DataRecord._base_manager.filter(table_id=nguon.table_id).only("id", "data").iterator(chunk_size=500):
            moi = gia_tri(dong.data or {}, cot_thi_truong)
            if (dong.data or {}).get(cot) != moi:
                dong.data = {**(dong.data or {}), cot: moi}
                doi.append(dong)
            if len(doi) >= 500:
                DataRecord._base_manager.bulk_update(doi, ["data"])
                doi = []
        if doi:
            DataRecord._base_manager.bulk_update(doi, ["data"])


def doi_sang_vnd(apps, schema_editor):
    ColumnDef = apps.get_model("forms_builder", "ColumnDef")
    for nguon, cot, _ in _nguon_mkt(apps):
        # Cột Loại tiền là cột chọn: VND phải có trong lựa chọn (bổ sung, không bỏ lựa chọn cũ)
        for column in ColumnDef.objects.filter(table_id=nguon.table_id, code=cot):
            if VND not in (column.options or []):
                column.options = [VND, *(column.options or [])]
                column.save(update_fields=["options"])
    _doi(apps, lambda data, cot_thi_truong: VND)


def tra_lai(apps, schema_editor):
    _doi(apps, lambda data, cot_thi_truong: THEO_THI_TRUONG.get(
        str(data.get(cot_thi_truong) or "").strip().casefold(), "") if cot_thi_truong else "")


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0005_reportsource_thresholds"),
        ("forms_builder", "0016_datarecord_val_phone_key"),
    ]

    operations = [
        migrations.RunPython(doi_sang_vnd, tra_lai),
    ]
