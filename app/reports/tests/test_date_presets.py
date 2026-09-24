"""ADR-038 — Chọn nhanh kỳ ở Báo cáo tổng hợp."""
from datetime import date

import pytest

from reports.models import ReportSource
from reports.services import summary_service
from reports.tests.test_aggregations import bang_mkt  # noqa: F401

pytestmark = pytest.mark.django_db


def test_chon_nhanh_ky(client, bang_mkt, nguoi_dung, monkeypatch):
    """AC-38.5 — Chọn nhanh: Hôm nay, Hôm qua, 7 ngày, Tuần này (thứ Hai → hôm nay, ADR-042), Tháng này,
    Tháng trước đúng ngày (kể cả qua đầu tháng, đầu năm và tuần vắt qua tháng); màn hình có nút với
    `data-tu`/`data-den` và JS áp ngay; nút khớp khoảng đang lọc được đánh dấu"""
    muc = {m["key"]: (m["start"], m["end"]) for m in summary_service.date_presets(date(2026, 9, 18))}
    assert muc == {
        "hom-nay": (date(2026, 9, 18), date(2026, 9, 18)),
        "hom-qua": (date(2026, 9, 17), date(2026, 9, 17)),
        "7-ngay": (date(2026, 9, 12), date(2026, 9, 18)),
        "tuan-nay": (date(2026, 9, 14), date(2026, 9, 18)),      # 18.09.2026 là thứ Sáu
        "thang-nay": (date(2026, 9, 1), date(2026, 9, 18)),
        "thang-truoc": (date(2026, 8, 1), date(2026, 8, 31)),
    }
    dau_nam = {m["key"]: (m["start"], m["end"]) for m in summary_service.date_presets(date(2027, 1, 1))}
    assert dau_nam["hom-qua"] == (date(2026, 12, 31), date(2026, 12, 31))
    assert dau_nam["7-ngay"] == (date(2026, 12, 26), date(2027, 1, 1))
    assert dau_nam["thang-truoc"] == (date(2026, 12, 1), date(2026, 12, 31))
    assert dau_nam["tuan-nay"] == (date(2026, 12, 28), date(2027, 1, 1))     # tuần vắt qua năm
    assert {m["key"]: m["start"] for m in summary_service.date_presets(date(2026, 9, 21))}["tuan-nay"] == date(2026, 9, 21)   # thứ Hai
    assert [m["label"] for m in summary_service.date_presets(date(2026, 9, 18))] == \
        ["Hôm nay", "Hôm qua", "7 ngày", "Tuần này", "Tháng này", "Tháng trước"]
    active = [m["key"] for m in summary_service.date_presets(date(2026, 9, 18), start=date(2026, 9, 1), end=date(2026, 9, 18)) if m["active"]]
    assert active == ["thang-nay"]

    ReportSource.objects.create(table=bang_mkt, kind="mkt", columns={
        "mess": "so_mess", "orders": "so_don", "sales": "doanh_so", "cost": "cpqc", "market": "thi_truong"})
    client.force_login(nguoi_dung["manager_mkt"])
    page = client.get("/bao-cao/tong-hop/", {"nguon": bang_mkt.code})   # mặc định = Tháng này
    assert page.status_code == 200
    html = page.content.decode()
    keys = [m["key"] for m in page.context["presets"] if m["active"]]
    assert keys == ["thang-nay"]
    for m in page.context["presets"]:
        assert f'data-tu="{m["start"]:%Y-%m-%d}" data-den="{m["end"]:%Y-%m-%d}"' in html
    assert 'class="nut report-preset is-active" data-key="thang-nay"' in html
    assert "report-filters.js" in html


def test_chon_nhanh_tuan_nay():
    """AC-42.12 — "Tuần này" là thứ Hai tuần này tới hôm nay, kể cả tuần vắt qua tháng; đứng ngay sau "7 ngày"
    trong dãy Chọn nhanh"""
    from datetime import date

    from reports.services.summary_service import date_presets

    presets = date_presets(date(2026, 10, 1))          # thứ Năm; tuần bắt đầu thứ Hai 28.09 — vắt qua tháng
    labels = [p["label"] for p in presets]
    assert labels.index("Tuần này") == labels.index("7 ngày") + 1
    tuan = next(p for p in presets if p["label"] == "Tuần này")
    assert (tuan["start"], tuan["end"]) == (date(2026, 9, 28), date(2026, 10, 1))
    thu_hai = next(p for p in date_presets(date(2026, 9, 28)) if p["label"] == "Tuần này")
    assert (thu_hai["start"], thu_hai["end"]) == (date(2026, 9, 28), date(2026, 9, 28))   # đúng thứ Hai: một ngày

