"""Lệnh nâng cấp cấu trúc tính lại dòng cũ — AC-36.13 (06.10.2026).

`tao_bang_van_don` (`ensure_waybill_table` → `upgrade_schema`) và `configure_erp_reports` tạo, sửa cột thẳng trong DB
mỗi lần bật máy. Trước đây không lệnh nào tính lại dòng đã có: gắn lại nhãn Khách hàng cho cột thì `val_customer` của
dòng cũ vẫn trống, lọc và Báo cáo tổng hợp thiếu dòng mà không báo gì. Nay cấu trúc đổi thì tính lại; không đổi thì
không đụng tới dòng nào (lệnh chạy mỗi lần bật máy).
"""
import pytest

from forms_builder.models import DataRecord
from forms_builder.services import record_service, table_service
from orders.services import dispatch_service

pytestmark = pytest.mark.django_db


def test_nang_cap_cau_truc_tinh_lai_cot_tach_cua_dong_cu(nguoi_dung):
    """AC-36.13 — Bảng vận đơn cũ thiếu nhãn Khách hàng ở cột Tên khách: chạy lại `ensure_waybill_table` gắn nhãn và
    tính lại `val_customer` cho dòng đã có"""
    bang = dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])
    dong = record_service.create_record(bang, {"ma_don": "DH-NC-1", "ngay": "2026-10-06", "ten_khach": "An",
                                               "so_dien_thoai": "0900", "loai_tien": "USD"}, actor=nguoi_dung["admin"])
    nhan = bang.columns.get(code="ten_khach").meaning
    assert nhan and DataRecord.objects.get(pk=dong.pk).val_customer == "An"
    # Giả lập dữ liệu từ bản cũ: cột chưa mang nhãn, cột tách trống
    bang.columns.filter(code="ten_khach").update(meaning="")
    DataRecord.objects.filter(pk=dong.pk).update(val_customer="")

    dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])
    assert bang.columns.get(code="ten_khach").meaning == nhan
    assert DataRecord.objects.get(pk=dong.pk).val_customer == "An"


def test_cau_truc_khong_doi_thi_khong_tinh_lai(nguoi_dung, monkeypatch):
    """AC-36.13 — Chạy lại lệnh khi cấu trúc không đổi: không tính lại, không tạo tác vụ nền"""
    bang = dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])
    record_service.create_record(bang, {"ma_don": "DH-NC-2", "ngay": "2026-10-06", "ten_khach": "B",
                                        "so_dien_thoai": "0900", "loai_tien": "USD"}, actor=nguoi_dung["admin"])
    goi = []
    monkeypatch.setattr(table_service, "schedule_resync", lambda *a, **k: goi.append(a))
    dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])
    assert goi == []
