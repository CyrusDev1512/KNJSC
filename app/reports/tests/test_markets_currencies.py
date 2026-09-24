"""ADR-031 bổ sung 18.09.2026 — bảy thị trường, tám loại tiền, tỉ giá theo sheet Quy ước."""
from decimal import Decimal

import pytest
from django.core.management.base import CommandError

from core.constants import CURRENCY_DECIMALS, Currency
from core.exceptions import BusinessError
from core.money import format_money
from forms_builder.choice_registry import options_for
from forms_builder.meaning import FieldType
from forms_builder.models import ColumnDef, DataRecord, FormDef
from forms_builder.services import record_service
from orders.constants import Market
from orders.services.currency_service import MARKET_CURRENCIES, for_label, for_market
from reports.management.commands.configure_erp_reports import configure_source
from reports.models import ReportSource
from reports.services import activity_service
from reports.tests.test_aggregations import bang_mkt  # noqa: F401

pytestmark = pytest.mark.django_db


def test_bay_thi_truong_tam_loai_tien(bang_mkt, nguoi_dung, settings):
    """AC-38.1 — Bảy thị trường (US, CA, PH, EU, KR, JP, AU) ↔ tám loại tiền; cột Thị trường và Loại
    tiền của bảng cấu hình trước 18.09 được bổ sung giá trị mới, giữ giá trị cũ, chạy lại không đổi;
    nộp Hàn Quốc → KRW, Úc → AUD; báo cáo quy tiền về ₫ nên EUR lẫn JPY vẫn công bố tổng (ADR-042);
    JPY/KRW không phần lẻ; KRW chưa có tỉ giá thì báo cáo cảnh báo và không cộng tiền dòng đó, bảng
    xếp hạng báo rõ, không âm thầm ra số"""
    from culture.services.leaderboard_service import to_vnd

    assert [m.label for m in Market] == ["Hoa Kỳ", "Canada", "Philippines", "Châu Âu", "Hàn Quốc", "Nhật Bản", "Úc"]
    assert {str(MARKET_CURRENCIES[m]) for m in Market} == {"USD", "CAD", "PHP", "EUR", "KRW", "JPY", "AUD"}
    assert for_market(Market.AU) == Currency.AUD and for_label("Hàn Quốc") == Currency.KRW
    assert CURRENCY_DECIMALS[Currency.JPY] == 0 and CURRENCY_DECIMALS[Currency.KRW] == 0
    assert format_money(Decimal("1550"), Currency.JPY) == "1.550 ¥"
    assert format_money(Decimal("12.5"), Currency.AUD) == "12,50 "

    # Bảng đã cấu hình trước 18.09: Thị trường ba nước, Loại tiền bốn mã
    ColumnDef.objects.create(table=bang_mkt, name="Thị trường", code="thi_truong", field_type=FieldType.CHOICE,
                             options=["Hoa Kỳ", "Canada", "Philippines"], order=90)
    ColumnDef.objects.create(table=bang_mkt, name="Loại tiền", code="loai_tien", field_type=FieldType.CHOICE,
                             options=["VND", "USD", "CAD", "PHP"], order=91)
    FormDef.objects.create(table=bang_mkt, department=bang_mkt.department, code="bc_mkt_tt", name="BC MKT")
    configure_source(bang_mkt, "mkt")
    thi_truong = ColumnDef.objects.get(table=bang_mkt, code="thi_truong")
    assert thi_truong.options == ["Hoa Kỳ", "Canada", "Philippines", "Châu Âu", "Hàn Quốc", "Nhật Bản", "Úc"]
    assert ColumnDef.objects.get(table=bang_mkt, code="loai_tien").options == ["VND", "USD", "CAD", "PHP", "EUR", "KRW", "JPY", "AUD"]
    configure_source(bang_mkt, "mkt")
    assert ColumnDef.objects.get(pk=thi_truong.pk).options[-1] == "Úc"
    assert "Úc" in options_for("bao_cao_mkt", "thi_truong")
    thi_truong.field_type = FieldType.TEXT
    thi_truong.save(update_fields=["field_type"])
    with pytest.raises(CommandError):
        configure_source(bang_mkt, "mkt")
    thi_truong.field_type = FieldType.CHOICE
    thi_truong.save(update_fields=["field_type"])

    han = record_service.create_record(bang_mkt, {"ngay": "2026-09-18", "marketer": "x", "san_pham": "SP",
        "so_mess": 2, "cpqc": "10", "so_don": 1, "doanh_so": "20", "thi_truong": "Hàn Quốc"},
        actor=nguoi_dung["staff_mkt"])
    uc = record_service.create_record(bang_mkt, {"ngay": "2026-09-18", "marketer": "x", "san_pham": "SP",
        "so_mess": 2, "cpqc": "10", "so_don": 1, "doanh_so": "20", "thi_truong": "Úc"},
        actor=nguoi_dung["staff_mkt"])
    assert han.data["loai_tien"] == "KRW" and uc.data["loai_tien"] == "AUD"
    with pytest.raises(BusinessError):
        record_service.create_record(bang_mkt, {"ngay": "2026-09-18", "marketer": "x", "san_pham": "SP",
            "so_mess": 2, "cpqc": "10", "so_don": 1, "doanh_so": "20", "thi_truong": "Sao Hoả"},
            actor=nguoi_dung["staff_mkt"])

    # Báo cáo tổng hợp quy ₫ (ADR-042): EUR một mình hay lẫn JPY đều công bố tổng bằng ₫;
    # thêm dòng KRW (chưa có tỉ giá) thì cảnh báo nêu KRW, tiền dòng đó không vào tổng, Số Mess vẫn đếm
    from reports import aggregations
    DataRecord.objects.filter(pk__in=[han.pk, uc.pk]).delete()
    source = ReportSource.objects.get(table=bang_mkt)
    record_service.create_record(bang_mkt, {"ngay": "2026-09-18", "marketer": "x", "san_pham": "SP",
        "so_mess": 2, "cpqc": "10", "so_don": 1, "doanh_so": "20", "thi_truong": "Châu Âu"},
        actor=nguoi_dung["staff_mkt"])
    result = activity_service.build(nguoi_dung["manager_mkt"], source, start=None, end=None)
    assert result.currency_label.startswith("VND") and not result.currency_warning

    def tong(result):
        return dict(zip([c.label for c in result.columns], aggregations.total_values(result)))
    assert tong(result)["CPQC"] == Decimal("285000")
    record_service.create_record(bang_mkt, {"ngay": "2026-09-18", "marketer": "x", "san_pham": "SP",
        "so_mess": 2, "cpqc": "10", "so_don": 1, "doanh_so": "20", "thi_truong": "Nhật Bản"},
        actor=nguoi_dung["staff_mkt"])
    result = activity_service.build(nguoi_dung["manager_mkt"], source, start=None, end=None)
    assert not result.currency_warning and tong(result)["CPQC"] == Decimal("286550")
    record_service.create_record(bang_mkt, {"ngay": "2026-09-18", "marketer": "x", "san_pham": "SP",
        "so_mess": 2, "cpqc": "10", "so_don": 1, "doanh_so": "20", "thi_truong": "Hàn Quốc"},
        actor=nguoi_dung["staff_mkt"])
    result = activity_service.build(nguoi_dung["manager_mkt"], source, start=None, end=None)
    assert "1 dòng" in result.currency_warning and "KRW" in result.currency_warning
    assert result.currency_label.startswith("VND")
    assert tong(result)["CPQC"] == Decimal("286550") and tong(result)["Số Mess"] == 6

    assert to_vnd(Decimal("10"), "EUR") == Decimal("285000")
    assert to_vnd(Decimal("1"), "AUD") == Decimal("17000")
    assert "KRW" not in settings.EXCHANGE_RATES_VND
    with pytest.raises(BusinessError, match="KRW"):
        to_vnd(Decimal("1000"), "KRW")
