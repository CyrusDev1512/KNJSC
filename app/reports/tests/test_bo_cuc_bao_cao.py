"""Bố cục Báo cáo tổng hợp theo bản vẽ 18.09: chip bộ lọc, cột định danh ghim, ba trạng thái bộ lọc."""
import pytest

from reports.models import ReportSource
from reports.tests.test_aggregations import bang_mkt, dong_mau  # noqa: F401 — fixture
from reports.tests.test_mkt_excel import marketing_scope  # noqa: F401 — fixture

pytestmark = pytest.mark.django_db


@pytest.fixture
def nguon(marketing_scope):
    return ReportSource.objects.create(table=marketing_scope.table, kind="sale",
                                       columns={"mess": "so_mess", "orders": "so_don", "sales": "doanh_so", "market": "thi_truong"})


def _get(client, nguon, **extra):
    return client.get("/bao-cao/tong-hop/", {"nguon": nguon.table.code, "tu": "2026-08-01", "den": "2026-08-31", **extra})


def test_chips_theo_bo_loc_va_link_bo_dung_tham_so(client, nguon, nguoi_dung):
    """AC-22.13 — Hàng chip render từ bộ lọc đang áp: Kỳ, Cách xem, Team, Nhân sự, Sản phẩm, Thị trường;
    × của mỗi chip là link cùng URL bỏ đúng tham số đó (bỏ Team thì bỏ luôn Nhân sự); Xóa lọc chỉ giữ nguồn;
    số bộ lọc bỏ được là huy hiệu của thanh dọc"""
    client.force_login(nguoi_dung["manager_sale"])
    team = nguoi_dung["staff_sale_1"].profile.team_id
    person = nguoi_dung["staff_sale_1"].pk
    r = _get(client, nguon, team=team, nhan_su=person, sp="SP1", thi_truong="__missing__")
    assert r.status_code == 200
    chips = {c["label"]: c for c in r.context["chips"]}
    assert list(chips) == ["Kỳ", "Cách xem", "Sản phẩm", "Thị trường", "Team", "Nhân sự"]
    assert chips["Kỳ"]["value"] == "01/08 – 31/08/2026" and "tu=" not in chips["Kỳ"]["url"] and "den=" not in chips["Kỳ"]["url"]
    assert chips["Cách xem"]["value"] == "Tổng hợp" and chips["Cách xem"]["url"] == ""
    assert chips["Thị trường"]["value"] == "Chưa xác định" and "thi_truong" not in chips["Thị trường"]["url"]
    assert chips["Team"]["value"] == "Sale 1" and "team=" not in chips["Team"]["url"] and "nhan_su=" not in chips["Team"]["url"]
    assert "Staff Sale 1" in chips["Nhân sự"]["value"] and "nhan_su=" not in chips["Nhân sự"]["url"] and f"team={team}" in chips["Nhân sự"]["url"]
    assert r.context["filters_active"] == 5
    assert r.context["clear_url"] == f"?nguon={nguon.table.code}"
    html = r.content.decode()
    assert f'data-active="5"' in html and 'data-filters="open"' in html and 'class="huy-hieu" aria-hidden="true" >5</span>' in html
    assert html.count('class="report-chip"') == 6 and 'class="chip-xoa"' in html and 'class="chip-clear"' in html
    # Không lọc gì: Kỳ mặc định không bỏ được, không huy hiệu, không Xóa lọc
    r0 = client.get("/bao-cao/tong-hop/", {"nguon": nguon.table.code})
    assert r0.context["filters_active"] == 0 and r0.context["chips"][0]["url"] == "" and 'class="chip-clear"' not in r0.content.decode()
    assert 'class="huy-hieu" aria-hidden="true" hidden' in r0.content.decode()


def test_cot_dinh_danh_ghim_theo_cach_xem(client, nguon, nguoi_dung):
    """AC-22.13 — Cột định danh ghim trái theo lớp tổng quát `.report-identity`, vị trí 1–4 và `left` bằng biến
    CSS đặt trên bảng: Tổng hợp = Ngày · Nhân sự · Leader; Theo nhân viên = Team · người · Leader; cột cuối mang
    lớp mép; dòng Tổng ôm đủ các cột định danh"""
    client.force_login(nguoi_dung["admin"])
    r = _get(client, nguon)
    cols = r.context["identity_columns"]
    assert [(c["code"], c["kind"], c["pos"], c["edge"]) for c in cols] == [
        ("nhom", "id-ngay", 1, False), ("person", "id-nhan-su", 2, False), ("leader", "id-leader", 3, True)]
    assert r.context["identity_style"] == "--id-left-2:calc(var(--w-ngay));--id-left-3:calc(var(--w-ngay) + var(--w-nhan-su))"
    html = r.content.decode()
    assert '<table class="bang report-table" style="--id-left-2:calc(var(--w-ngay));--id-left-3:calc(var(--w-ngay) + var(--w-nhan-su))">' in html
    assert 'class="report-identity report-identity-edge" data-pos="1" colspan="3">Tổng trong bộ lọc</th>' in html
    assert 'class="report-identity id-ngay" data-pos="1">01.08.2026</th>' in html
    r2 = _get(client, nguon, nhom="person")
    cols = r2.context["identity_columns"]
    assert [(c["code"], c["kind"], c["pos"]) for c in cols] == [("team", "id-team", 1), ("nhom", "id-nhom", 2), ("leader", "id-leader", 3)]
    assert r2.context["identity_style"] == "--id-left-2:calc(var(--w-team));--id-left-3:calc(var(--w-team) + var(--w-nhom))"
    assert cols[-1]["edge"] and r2.context["label_span"] == 3
    r3 = _get(client, nguon, nhom="product")
    assert [c["code"] for c in r3.context["identity_columns"]] == ["nhom"] and r3.context["identity_style"] == ""
    assert 'data-pos="1" >Tổng trong bộ lọc' in r3.content.decode()


def test_staff_khong_thay_chip_team_nguoi_khac(client, nguon, nguoi_dung):
    """AC-22.13 — Chip Nhân sự/Team chỉ đặt tên khi lọc trong phạm vi; Staff lọc người khác vẫn bị 403 như trước"""
    client.force_login(nguoi_dung["staff_sale_1"])
    r = _get(client, nguon, nhan_su=nguoi_dung["staff_sale_2"].pk)
    assert r.status_code == 403
    r = _get(client, nguon, nhan_su=nguoi_dung["staff_sale_1"].pk)
    assert r.status_code == 200 and r.context["chips"][-1]["label"] == "Nhân sự" and r.context["filters_active"] == 2   # Kỳ tự chọn + Nhân sự
