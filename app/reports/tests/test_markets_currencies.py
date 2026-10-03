"""ADR-031 bổ sung 18.09.2026 — bảy thị trường, tám loại tiền, tỉ giá theo sheet Quy ước."""
from datetime import date
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
    nộp Hàn Quốc → KRW, Úc → AUD; báo cáo không quy đổi (ADR-046 thay ADR-042): EUR lẫn JPY thì mỗi loại
    tiền một dòng tổng với đúng số đã nhập, tổng chung chỉ còn số đếm; KRW chưa có tỉ giá vẫn hiện như
    mọi loại tiền khác; JPY/KRW không phần lẻ; bảng xếp hạng (còn quy đổi, Q71) báo rõ KRW chưa có tỉ
    giá, không âm thầm ra số"""
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
    # Báo cáo MKT nộp bằng tiền Việt (ADR-047): thị trường nào cũng VND; Thị trường lạ vẫn bị chặn
    assert han.data["loai_tien"] == "VND" and uc.data["loai_tien"] == "VND"
    with pytest.raises(BusinessError):
        record_service.create_record(bang_mkt, {"ngay": "2026-09-18", "marketer": "x", "san_pham": "SP",
            "so_mess": 2, "cpqc": "10", "so_don": 1, "doanh_so": "20", "thi_truong": "Sao Hoả"},
            actor=nguoi_dung["staff_mkt"])

    # Báo cáo tổng hợp không quy đổi (ADR-046): mỗi loại tiền một dòng tổng, số đúng như nhập;
    # KRW (chưa có tỉ giá) không còn là ngoại lệ — hiện như mọi loại tiền, không cảnh báo.
    # Báo cáo MKT nay luôn VND (ADR-047); cơ chế nhiều loại tiền vẫn dùng cho Sale, nên ghi nhãn theo thị trường
    # thẳng vào dòng để kiểm cơ chế đó

    def nop_theo_thi_truong(thi_truong):
        dong = record_service.create_record(bang_mkt, {"ngay": "2026-09-18", "marketer": "x", "san_pham": "SP",
            "so_mess": 2, "cpqc": "10", "so_don": 1, "doanh_so": "20", "thi_truong": thi_truong},
            actor=nguoi_dung["staff_mkt"])
        DataRecord.objects.filter(pk=dong.pk).update(data={**dong.data, "loai_tien": for_label(thi_truong)})

    from reports import aggregations
    DataRecord.objects.filter(pk__in=[han.pk, uc.pk]).delete()
    source = ReportSource.objects.get(table=bang_mkt)
    nop_theo_thi_truong("Châu Âu")
    result = activity_service.build(nguoi_dung["manager_mkt"], source, start=None, end=None)
    assert "không quy đổi" in result.currency_label and not result.currency_warning

    def tong(result):
        return dict(zip([c.label for c in result.columns], aggregations.total_values(result)))

    def theo_tien(result):
        return {tien: dict(zip([c.label for c in result.columns], raw)) for tien, raw in aggregations.total_rows(result)}
    assert list(theo_tien(result)) == ["EUR"] and theo_tien(result)["EUR"]["CPQC"] == Decimal("10")
    assert tong(result)["CPQC"] == Decimal("10")          # một loại tiền: tổng chung chính là tổng EUR
    nop_theo_thi_truong("Nhật Bản")
    result = activity_service.build(nguoi_dung["manager_mkt"], source, start=None, end=None)
    assert not result.currency_warning and list(theo_tien(result)) == ["EUR", "JPY"]
    assert theo_tien(result)["EUR"]["CPQC"] == Decimal("10") and theo_tien(result)["JPY"]["CPQC"] == Decimal("10")
    # Hai loại tiền: tổng chung không cộng tiền (None), vẫn đếm đủ
    assert tong(result)["CPQC"] is None and tong(result)["CPO"] is None and tong(result)["Số Mess"] == 4
    nop_theo_thi_truong("Hàn Quốc")
    result = activity_service.build(nguoi_dung["manager_mkt"], source, start=None, end=None)
    assert not result.currency_warning and list(theo_tien(result)) == ["EUR", "KRW", "JPY"]
    assert theo_tien(result)["KRW"]["CPQC"] == Decimal("10") and tong(result)["Số Mess"] == 6

    assert to_vnd(Decimal("10"), "EUR") == Decimal("285000")
    assert to_vnd(Decimal("1"), "AUD") == Decimal("17000")
    assert "KRW" not in settings.EXCHANGE_RATES_VND
    with pytest.raises(BusinessError, match="KRW"):
        to_vnd(Decimal("1000"), "KRW")


def test_the_tong_quan_khong_hien_o_don_vi_va_canh_bao_quy_doi(client, bang_mkt, nguoi_dung):
    """AC-22.18 — Thẻ Báo cáo tổng hợp trên Tổng quan không còn ô đơn vị/tỉ giá hay ô cảnh báo
    "… dòng chưa quy đổi được" (chủ dự án 26.09.2026); từ ADR-046 không còn quy đổi nên cả màn chi
    tiết cũng không có cảnh báo đó — dòng KRW hiện với loại tiền của nó, thẻ có cột KRW"""
    ColumnDef.objects.create(table=bang_mkt, name="Loại tiền", code="loai_tien", field_type=FieldType.CHOICE,
                             options=["VND", "USD"], order=91)
    FormDef.objects.create(table=bang_mkt, department=bang_mkt.department, code="bc_mkt_tq", name="BC MKT")
    configure_source(bang_mkt, "mkt")
    # Ngày của nguồn báo cáo do hệ thống đặt (ADR-032): truyền ngày hệ thống, không thì báo cáo mang ngày chạy
    # bài và rơi khỏi kỳ tháng 9 khi bài chạy từ tháng 10 (TL-70)
    record_service.create_record(bang_mkt, {"ngay": "2026-09-18", "marketer": "x", "san_pham": "SP",
        "so_mess": 2, "cpqc": "10", "so_don": 1, "doanh_so": "20", "thi_truong": "Hàn Quốc"},
        actor=nguoi_dung["staff_mkt"], system_day=date(2026, 9, 18))
    client.force_login(nguoi_dung["manager_mkt"])
    ky = {"tu": "2026-09-01", "den": "2026-09-30"}

    tong_quan = client.get("/", {"mkt_nguon": bang_mkt.code, **ky})
    khoi = next(b for b in tong_quan.context["activity"]["blocks"] if b["kind"] == "mkt")
    assert khoi["ok"] and khoi["data"]["state"] == "ready", khoi
    html = tong_quan.content.decode()
    assert "chưa quy đổi được" not in html and "quy đổi theo tỉ giá cố định" not in html
    assert "dashboard-note" not in html and "currency_note" not in khoi["data"]
    assert khoi["data"]["currencies"] == ["VND"]          # báo cáo MKT luôn VND (ADR-047)

    chi_tiet = client.get("/bao-cao/tong-hop/", {"nguon": bang_mkt.code, **ky}).content.decode()
    assert "chưa quy đổi được" not in chi_tiet and ">VND</td>" in chi_tiet
