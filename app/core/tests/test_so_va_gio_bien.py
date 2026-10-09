"""Số và giờ ở biên — AC-9.7, AC-9.8 (săn lỗi 06.10.2026).

Đo trên hệ thống thật: gõ "NaN", "Infinity", "1e400" hay một số 24 chữ số vào ô Doanh số của form nộp báo cáo là trang
lỗi 500 — `parse_money` nhận cả các chữ Python hiểu là số, rồi cơ sở dữ liệu từ chối. Và chip "Hôm nay" của lưới lấy
ngày theo đồng hồ máy chủ (container chạy giờ quốc tế), nên từ 0 giờ tới 7 giờ sáng giờ Việt Nam "Hôm nay" là hôm qua.
"""
from datetime import date, datetime, timezone as dt_timezone
from decimal import Decimal, InvalidOperation
from unittest.mock import patch

import pytest

from core.exceptions import BusinessError
from core.money import parse_money
from reports.models import DailyReport
from reports.tests.test_bao_cao_ngay import bm_mkt  # noqa: F401
from reports.tests.test_nop_mot_lan import _du_lieu, _ma_lan_nop


@pytest.mark.parametrize("chu", ["NaN", "nan", "sNaN", "Infinity", "-inf", "1e5", "1E400", "+-5", "--5", "0x10"])
def test_o_so_tu_choi_chu_khong_phai_so_viet(chu):
    """AC-9.7 — Ô tiền và số thập phân chỉ nhận chữ số với dấu chấm, phẩy, một dấu trừ: "NaN", "Infinity", "1e400", "+-5" bị từ chối, không lọt xuống cơ sở dữ liệu"""
    with pytest.raises((InvalidOperation, BusinessError)):
        parse_money(chu)


def test_o_so_qua_dai_bao_loi_tieng_viet():
    """AC-9.7 — Số vượt 16 chữ số phần nguyên (trần của cột tiền 18 chữ số, 2 số lẻ) báo lỗi tiếng Việt nói rõ trần, không thành trang lỗi 500"""
    assert parse_money("9.999.999.999.999.999,99") == Decimal("9999999999999999.99")
    with pytest.raises(BusinessError, match="16 chữ số"):
        parse_money("123456789012345678901234")


@pytest.mark.parametrize("chu, so", [
    ("1.234,5", Decimal("1234.5")), ("1,234.5", Decimal("1234.5")), ("1.234", Decimal("1234")),
    ("150.00", Decimal("150.00")), ("-5.000", Decimal("-5000")), ("0", Decimal("0")), ("1 234 ₫", Decimal("1234")),
])
def test_o_so_van_doc_dung_cach_viet_viet_nam(chu, so):
    """AC-9.7 — Siết lại không làm hỏng cách viết đang nhận: chấm ngăn nghìn, phẩy thập phân, dán số kiểu Mỹ, số âm, ký hiệu tiền"""
    assert parse_money(chu) == so


@pytest.mark.django_db
def test_nop_bao_cao_doanh_so_nan_bao_loi_khong_500(client, bm_mkt, nguoi_dung):  # noqa: F811
    """AC-9.7 — Nộp báo cáo Marketing với Doanh số "NaN", "Infinity" hay số 24 chữ số: form hiện lỗi tiếng Việt ở lại trang, không trang lỗi 500, không thêm báo cáo"""
    client.force_login(nguoi_dung["staff_mkt"])
    for chu in ("NaN", "Infinity", "123456789012345678901234"):
        ma = _ma_lan_nop(client.get("/bao-cao/").content.decode())
        r = client.post("/bao-cao/", _du_lieu(bm_mkt, ma, doanh_so=chu))
        assert r.status_code == 200, chu
        assert not DailyReport.objects.exists(), chu


def test_chip_hom_nay_theo_gio_viet_nam():
    """AC-9.8 — Chip "Hôm nay", "Tháng này" của lưới tính theo giờ Việt Nam: 00:30 ngày 01/04 giờ Việt Nam (17:30 ngày 31/03 giờ quốc tế) là ngày 01/04, tháng 4"""
    from crm.services.sidebar_service import preset_range

    luc = datetime(2026, 3, 31, 17, 30, tzinfo=dt_timezone.utc)
    with patch("django.utils.timezone.now", return_value=luc):
        assert preset_range("hom_nay") == (date(2026, 4, 1), date(2026, 4, 1))
        assert preset_range("thang_nay") == (date(2026, 4, 1), date(2026, 4, 1))
        assert preset_range("thang_truoc") == (date(2026, 3, 1), date(2026, 3, 31))


def test_ten_tep_xuat_theo_gio_viet_nam():
    """AC-9.8 — Tên tệp Excel xuất từ lưới mang ngày giờ Việt Nam, không phải giờ máy chủ"""
    from types import SimpleNamespace

    from forms_builder.services.export_service import file_name

    luc = datetime(2026, 3, 31, 17, 30, tzinfo=dt_timezone.utc)
    with patch("django.utils.timezone.now", return_value=luc):
        assert file_name(SimpleNamespace(code="van_don")) == "van_don-20260401-0030.xlsx"
