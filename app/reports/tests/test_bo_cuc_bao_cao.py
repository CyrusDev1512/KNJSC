"""Bố cục Báo cáo tổng hợp theo bản vẽ 18.09: chip bộ lọc, cột định danh ghim, ba trạng thái bộ lọc; đầu trang gọn
trên thanh trên cùng với menu ⋯ (07.10.2026)."""
import re

import pytest

from reports.models import ReportSource
from reports.services import summary_service
from reports.tests.test_activity import delivery_source  # noqa: F401 — fixture
from reports.tests.test_aggregations import bang_mkt, dong_mau  # noqa: F401 — fixture
from reports.tests.test_che_do_so_lieu import _nop
from reports.tests.test_mkt_derived_revenue import _bao_cao, mkt_source, van_don  # noqa: F401 — fixture
from reports.tests.test_mkt_excel import marketing_scope  # noqa: F401 — fixture

pytestmark = pytest.mark.django_db


@pytest.fixture
def nguon(marketing_scope):
    return ReportSource.objects.create(table=marketing_scope.table, kind="sale",
                                       columns={"mess": "so_mess", "orders": "so_don", "sales": "doanh_so", "market": "thi_truong"})


def _get(client, nguon, **extra):
    return client.get("/bao-cao/tong-hop/", {"nguon": nguon.table.code, "tu": "2026-08-01", "den": "2026-08-31", **extra})


def test_chips_theo_bo_loc_va_link_bo_dung_tham_so(client, nguon, nguoi_dung):
    """AC-22.13 — Hàng chip render từ bộ lọc đang áp: Kỳ, Team, Nhân sự, Sản phẩm, Thị trường (không còn chip
    Cách xem, Chế độ — 01.10.2026); × của mỗi chip là link cùng URL bỏ đúng tham số đó (bỏ Team thì bỏ luôn
    Nhân sự); Xóa lọc chỉ giữ nguồn; số bộ lọc bỏ được là huy hiệu của thanh dọc. Từ 07.10.2026 chip nằm trên thanh
    trên cùng và chip Kỳ là chữ kỳ ngay bên cạnh (AC-42.18), nên trang in bốn chip"""
    client.force_login(nguoi_dung["manager_sale"])
    team = nguoi_dung["staff_sale_1"].profile.team_id
    person = nguoi_dung["staff_sale_1"].pk
    r = _get(client, nguon, team=team, nhan_su=person, sp="SP1", thi_truong="__missing__")
    assert r.status_code == 200
    chips = {c["label"]: c for c in r.context["chips"]}
    assert list(chips) == ["Kỳ", "Sản phẩm", "Thị trường", "Team", "Nhân sự"]
    assert chips["Kỳ"]["value"] == "01/08 – 31/08/2026" and "tu=" not in chips["Kỳ"]["url"] and "den=" not in chips["Kỳ"]["url"]
    assert chips["Thị trường"]["value"] == "Chưa xác định" and "thi_truong" not in chips["Thị trường"]["url"]
    assert chips["Team"]["value"] == "Sale 1" and "team=" not in chips["Team"]["url"] and "nhan_su=" not in chips["Team"]["url"]
    assert "Staff Sale 1" in chips["Nhân sự"]["value"] and "nhan_su=" not in chips["Nhân sự"]["url"] and f"team={team}" in chips["Nhân sự"]["url"]
    assert r.context["filters_active"] == 5
    assert r.context["clear_url"] == f"?nguon={nguon.table.code}"
    html = r.content.decode()
    assert f'data-active="5"' in html and 'data-filters="open"' in html and 'class="huy-hieu" aria-hidden="true" >5</span>' in html
    assert html.count('class="report-chip"') == 4 and 'class="chip-xoa"' in html and 'class="chip-clear"' in html
    # Không lọc gì: Kỳ mặc định không bỏ được, không huy hiệu, không Xóa lọc
    r0 = client.get("/bao-cao/tong-hop/", {"nguon": nguon.table.code})
    assert r0.context["filters_active"] == 0 and r0.context["chips"][0]["url"] == "" and 'class="chip-clear"' not in r0.content.decode()
    assert 'class="huy-hieu" aria-hidden="true" hidden' in r0.content.decode()


def test_cot_dinh_danh_ghim_theo_cach_xem(client, nguon, nguoi_dung):
    """AC-22.13 — Cột định danh theo lớp tổng quát `.report-identity`, vị trí 1–4: khối ngày của nguồn Sale = STT ·
    Team · Nhân sự · Leader (luôn từng lần nộp, 01.10.2026; cột Lần nộp ẩn từ 04.10.2026, AC-47.7); chỉ STT và Nhân sự
    (nguồn không có Loại tiền) đứng yên, `left` bằng biến CSS đặt trên bảng, cột đứng yên cuối mang lớp mép; Team,
    Leader trôi theo (`report-troi`, 02.10.2026); dòng Tổng mỗi cột định danh một ô, nhãn ở ô Nhân sự"""
    client.force_login(nguoi_dung["admin"])
    r = _get(client, nguon)
    cols = r.context["identity_columns"]
    # Khối theo ngày như ảnh mẫu (ADR-042): STT · Team · Nhân sự · Leader, không có cột Ngày, không còn Lần nộp
    assert [(c["code"], c["kind"], c["pos"], c["sticky"], c["edge"]) for c in cols] == [
        ("stt", "id-stt", 1, True, False), ("team", "id-team", 2, False, False),
        ("person", "id-nhan-su", 3, True, True), ("leader", "id-leader", 4, False, False)]
    kieu = "--id-left-3:calc(var(--w-stt))"
    assert r.context["identity_style"] == kieu
    html = r.content.decode()
    assert f'<table class="bang report-table" style="{kieu}">' in html
    assert '<th scope="row" class="report-identity id-nhan-su report-identity-edge" data-pos="3">TỔNG CỘNG</th>' in html
    assert 'class="report-identity report-troi id-leader" data-pos="4">Leader</th>' in html
    assert "id-lan" not in html and ">Lần nộp</th>" not in html
    # Khối ngày: cột đầu là STT, ngày thành tiêu đề đặt trên bảng (ADR-042)
    assert 'class="report-identity id-stt" data-pos="1">1</th>' in html and '<h3>01.08.2026</h3>' in html


def test_staff_khong_thay_chip_team_nguoi_khac(client, nguon, nguoi_dung):
    """AC-22.13 — Chip Nhân sự/Team chỉ đặt tên khi lọc trong phạm vi; Staff lọc người khác vẫn bị 403 như trước"""
    client.force_login(nguoi_dung["staff_sale_1"])
    r = _get(client, nguon, nhan_su=nguoi_dung["staff_sale_2"].pk)
    assert r.status_code == 403
    r = _get(client, nguon, nhan_su=nguoi_dung["staff_sale_1"].pk)
    assert r.status_code == 200 and r.context["chips"][-1]["label"] == "Nhân sự" and r.context["filters_active"] == 2   # Kỳ tự chọn + Nhân sự


def _doan(html, mo, dong="</div>"):
    """Đoạn HTML từ chỗ có `mo` tới thẻ đóng `dong` đầu tiên sau đó."""
    dau = html.index(mo)
    return html[dau:html.index(dong, dau)]


def test_dau_bang_gon_mot_hang_va_giai_thich_so_lieu(client, bang_mkt, mkt_source, van_don, nguoi_dung):
    """AC-22.24 — Vừa mở Báo cáo tổng hợp đã thấy số (chủ dự án duyệt mockup 02.10.2026): tên bảng, khoảng ngày,
    Ngưỡng màu (chỉ người đặt được ngưỡng) và Giải thích số liệu không chiếm hàng nào trên bảng — từ 07.10.2026 tên và
    kỳ ở thanh trên cùng, hai nút là mục của menu ⋯ (AC-42.18); câu loại tiền và đoạn "Tổng trên toàn bộ kết quả khớp
    bộ lọc · (TT) = …" (kèm biến thể nộp nhiều lần) thu vào panel Giải thích số liệu ẩn sẵn, giữ nguyên từng chữ; cảnh
    báo dòng chưa có loại tiền còn một dòng gọn, toàn văn ở `title` và trong panel; `?nguong=1` mở sẵn panel ngưỡng;
    Bảng dữ liệu giữ ô Ngưỡng màu dạng mở rộng như cũ. Nguồn Marketing không còn lọc theo Tệp khách hàng (ADR-048) nên
    biến thể "để trống khi lọc theo Tệp khách hàng" bỏ"""
    A, B = van_don["A"], van_don["B"]
    _nop(bang_mkt, A, 9, 0, cpqc="8000")
    _nop(bang_mkt, A, 10, 0, cpqc="500")      # A nộp hai lần cùng ngày cùng loại tiền: (TT) chỉ ở dòng TỔNG CỘNG
    _nop(bang_mkt, B, 11, 0, cpqc="3000", thi_truong="", tien="")   # chưa có loại tiền → cảnh báo
    ky = {"nguon": bang_mkt.code, "tu": "2026-08-01", "den": "2026-08-01"}
    client.force_login(B)                    # manager_mkt: đặt được ngưỡng
    r = client.get("/bao-cao/tong-hop/", ky)
    assert r.status_code == 200
    ket_qua = r.context["result"]
    nhan_tien, canh_bao = ket_qua.currency_label, ket_qua.currency_warning
    assert nhan_tien and canh_bao.startswith("1 dòng chưa có loại tiền")
    html = r.content.decode()
    # Thanh trên cùng: tên bảng, khoảng ngày; menu ⋯ có hai mục đóng sẵn — không còn đoạn giải thích dài trên bảng
    tren = _thanh_tren(html)
    assert f"<b>{bang_mkt.name}</b>" in tren and '<span class="bc-dau-ky">01/08 – 01/08/2026</span>' in tren
    assert ('<button type="button" class="report-them-muc" data-mo-ra aria-controls="report-nguong" '
            'aria-expanded="false">') in tren
    assert ('<button type="button" class="report-them-muc" data-mo-ra aria-controls="report-giai-thich" '
            'aria-expanded="false">') in tren
    assert "(TT) =" not in tren and nhan_tien not in tren
    # Panel ẩn sẵn, đủ chữ như trước: câu loại tiền, khoảng tổng và (TT) kèm biến thể nộp nhiều lần, toàn văn cảnh báo
    panel = _doan(html, '<div class="report-giai-thich" id="report-giai-thich" hidden>')
    assert nhan_tien in panel and canh_bao in panel
    assert ("Tổng trên toàn bộ kết quả khớp bộ lọc · (TT) = đối soát từ vận đơn do marketer phụ trách theo ngày lên "
            "đơn: Số đơn (TT) là số đơn; DS Chốt (TT) để trống vì báo cáo nộp bằng tiền Việt còn vận đơn thu bằng "
            "ngoại tệ, không quy đổi; ngày nào một người nộp nhiều lần thì (TT) chỉ hiện ở dòng TỔNG CỘNG của ngày") in panel
    assert html.count(nhan_tien) == 1, "câu loại tiền chỉ còn trong panel"
    # Cảnh báo một dòng gọn: toàn văn ở title
    assert (f'<p class="bao bao-cho report-canh-gon" role="status" title="{canh_bao}"><span>{canh_bao}</span></p>'
            in html)
    # Panel ngưỡng: ẩn sẵn; `?nguong=1` (sau khi lưu lỗi) thì mở sẵn, nút báo đang mở
    assert '<div class="report-nguong" id="report-nguong" hidden>' in html
    mo = client.get("/bao-cao/tong-hop/", {**ky, "nguong": "1"}).content.decode()
    assert '<div class="report-nguong" id="report-nguong">' in mo and 'aria-controls="report-nguong" aria-expanded="true"' in mo
    # Tham số `tep` cũ bị bỏ qua (ADR-048): không còn biến thể "để trống khi lọc theo Tệp khách hàng"
    tep = client.get("/bao-cao/tong-hop/", {**ky, "tep": "__missing__"}).content.decode()
    assert "Tệp khách hàng" not in _doan(tep, 'id="report-giai-thich"')
    # Staff: có Giải thích số liệu, không có nút và panel ngưỡng
    client.force_login(A)
    nv = client.get("/bao-cao/tong-hop/", ky).content.decode()
    assert 'aria-controls="report-giai-thich"' in nv and 'id="report-nguong"' not in nv and "Ngưỡng màu" not in nv
    # Bảng dữ liệu dạng báo cáo giữ ô Ngưỡng màu mở rộng như cũ
    client.force_login(B)
    bang = client.get(f"/bang/{bang_mkt.code}/", {"tu": "2026-08-01", "den": "2026-08-01"}).content.decode()
    assert '<details class="report-nguong" id="report-nguong">' in bang


# ── Đầu trang gọn: tên, kỳ, chip và menu ⋯ trên thanh trên cùng (chủ dự án duyệt mockup 07.10.2026) ─────────────

def _thanh_tren(html):
    """Thanh trên cùng của trang: từ `<header class="topbar">` tới `</header>`."""
    dau = html.index('<header class="topbar">')
    return html[dau:html.index("</header>", dau)]


def _muc_menu(html):
    """Nhãn các mục của menu ⋯ theo thứ tự."""
    return re.findall(r"<b>([^<]+)</b>", _doan(html, 'id="report-them-menu"'))


def test_thanh_tren_cung_co_ten_ky_chip_va_menu(client, nguon, nguoi_dung):
    """AC-42.18 — Báo cáo tổng hợp không còn hàng nút, hàng chip, hàng tên bảng trên bảng (chủ dự án duyệt mockup
    07.10.2026): thanh trên cùng ghi tên báo cáo thay "Báo cáo tổng hợp", kỳ gọn, chip lọc trừ Kỳ (chip Gộp chỉ còn
    nhãn và ×, mỗi chip có `title` đủ chữ), "Xóa lọc", và nút ⋯ với Không gộp / Gộp (`aria-current` ở cách đang xem),
    Ngưỡng màu, Giải thích số liệu, Toàn màn hình, Xuất Excel theo đúng bộ lọc đang xem; hai panel có nút Đóng"""
    client.force_login(nguoi_dung["manager_sale"])
    team = nguoi_dung["staff_sale_1"].profile.team_id
    r = _get(client, nguon, team=team, nhan_su=nguoi_dung["staff_sale_1"].pk, gop="1")
    assert r.status_code == 200
    html = r.content.decode()
    tren = _thanh_tren(html)
    assert f"<b>{nguon.table.name}</b>" in tren and "<b>Báo cáo tổng hợp</b>" not in tren
    assert '<span class="bc-dau-ky">01/08 – 31/08/2026</span>' in tren
    # Chip trừ Kỳ (kỳ đã là chữ ngay bên cạnh): Gộp chỉ còn nhãn và ×, giá trị ở title; × bỏ đúng tham số như cũ
    chips = _doan(tren, 'id="report-chips"')
    assert chips.count('class="report-chip"') == 3 and "<b>Kỳ</b>" not in chips
    assert '<span class="report-chip" title="Gộp: mọi lần nộp một bảng"><b>Gộp</b> <a class="chip-xoa"' in chips
    assert 'title="Team: Sale 1"' in chips and "<b>Nhân sự</b>" in chips
    assert '<a class="chip-clear" href="?nguon=' in chips          # bốn bộ lọc bỏ được (Kỳ, Gộp, Team, Nhân sự)
    # Menu ⋯: đúng thứ tự, đánh dấu cách đang xem, câu mô tả Gộp của nguồn có lần nộp
    assert _muc_menu(tren) == ["Không gộp", "Gộp", "Ngưỡng màu", "Giải thích số liệu", "Toàn màn hình", "Xuất Excel"]
    menu = _doan(tren, 'id="report-them-menu"')
    assert 'data-che-do="gop" aria-current="true"' in menu and 'data-che-do="khong-gop" aria-current="false"' in menu
    assert "Một bảng mọi lần nộp trong kỳ" in menu
    xuat = re.search(r'<a class="report-them-muc" id="report-xuat" href="([^"]+)"', menu).group(1)
    assert xuat.startswith("/bao-cao/tong-hop/xuat/?") and "gop=1" in xuat and f"team={team}" in xuat
    # Panel giữ chỗ ở đầu hộp bảng, có nút Đóng; không còn ba hàng trên bảng
    assert 'data-dong="report-giai-thich"' in html and 'data-dong="report-nguong"' in html
    assert "report-controls" not in html and "report-results-heading" not in html and "report-seg" not in html
    assert html.count('id="report-chips"') == 1 and html.count('id="report-xuat"') == 1
    # Cú pháp template không lọt ra trang (chú thích `{# #}` viết hai dòng in thành chữ, đẩy bảng xuống 60 px)
    assert "{#" not in html and "#}" not in html and "{%" not in html


def test_xoa_loc_khi_can_va_ky_vat_qua_nam(client, nguon, nguoi_dung):
    """AC-42.18 — "Xóa lọc" chỉ hiện khi bỏ được nhiều hơn chip duy nhất đang có: không lọc gì thì không có; một chip
    có × thì × làm việc đó, không lặp "Xóa lọc"; chỉ kỳ khác mặc định (kỳ là chữ, không ×) thì còn "Xóa lọc" để về kỳ
    mặc định. Kỳ vắt qua năm ghi đủ năm cả hai đầu"""
    client.force_login(nguoi_dung["manager_sale"])
    tu, den = summary_service.default_range()

    def tren(**extra):
        query = {"nguon": nguon.table.code, "tu": tu.isoformat(), "den": den.isoformat(), **extra}
        return _thanh_tren(client.get("/bao-cao/tong-hop/", query).content.decode())
    khong = tren()
    assert 'class="report-chip"' not in khong and 'class="chip-clear"' not in khong
    mot = tren(gop="1")
    assert mot.count('class="report-chip"') == 1 and 'class="chip-clear"' not in mot
    ky = tren(tu="2026-08-01", den="2026-08-31")
    assert 'class="report-chip"' not in ky and f'<a class="chip-clear" href="?nguon={nguon.table.code}">Xóa lọc</a>' in ky
    assert '<span class="bc-dau-ky">15/12/2025 – 10/01/2026</span>' in tren(tu="2025-12-15", den="2026-01-10")


@pytest.mark.parametrize("vai, co_nguong", [("staff_sale_1", False), ("leader_sale_1", True), ("admin", True)])
def test_menu_theo_cap_bac(client, nguon, nguoi_dung, vai, co_nguong):
    """AC-42.18 — Ngưỡng màu trong menu ⋯ và panel của nó chỉ có với người đặt được ngưỡng (quản lý bộ phận sở hữu
    nguồn, Admin); Staff có đủ mục còn lại"""
    client.force_login(nguoi_dung[vai])
    html = _get(client, nguon).content.decode()
    muc = ["Không gộp", "Gộp", "Giải thích số liệu", "Toàn màn hình", "Xuất Excel"]
    assert _muc_menu(_thanh_tren(html)) == (muc[:2] + ["Ngưỡng màu"] + muc[2:] if co_nguong else muc)
    assert ('data-dong="report-nguong"' in html) is co_nguong and 'data-dong="report-giai-thich"' in html


def test_menu_nguon_van_don_mo_ta_gop(client, delivery_source, nguoi_dung):
    """AC-42.18 — Nguồn Vận đơn không có lần nộp: mục Gộp mô tả "Một bảng, mỗi ngày một dòng" (khớp chip "mỗi ngày
    một dòng")"""
    client.force_login(nguoi_dung["admin"])
    tren = _thanh_tren(client.get("/bao-cao/tong-hop/", {"nguon": delivery_source.table.code}).content.decode())
    menu = _doan(tren, 'id="report-them-menu"')
    assert "Một bảng, mỗi ngày một dòng" in menu and "Một bảng mọi lần nộp trong kỳ" not in menu


def test_tien_viet_canh_ky_tren_thanh_tren(client, bang_mkt, mkt_source, nguoi_dung):
    """AC-42.18 — Báo cáo Marketing toàn VND ghi "· Tiền: ₫" ngay sau kỳ trên thanh trên cùng (AC-48.4)"""
    _bao_cao(bang_mkt, nguoi_dung["staff_mkt"], "2026-08-01", "SP1")
    client.force_login(nguoi_dung["manager_mkt"])
    tren = _thanh_tren(client.get("/bao-cao/tong-hop/", {"nguon": bang_mkt.code, "tu": "2026-08-01",
                                                         "den": "2026-08-03"}).content.decode())
    assert '<span class="bc-dau-ky">01/08 – 03/08/2026 · Tiền: ₫</span>' in tren


def test_bang_du_lieu_va_trang_khac_khong_doi(client, nguon, nguoi_dung):
    """AC-42.18 — Chỉ Báo cáo tổng hợp đổi đầu trang: Bảng dữ liệu dạng báo cáo giữ hàng nút (Gộp / Không gộp),
    hàng chip và tên trang như cũ, thanh trên cùng không có menu ⋯; Tổng quan không có gì thêm trên thanh trên cùng"""
    client.force_login(nguoi_dung["manager_sale"])
    bang = client.get(f"/bang/{nguon.table.code}/", {"tu": "2026-08-01", "den": "2026-08-31"}).content.decode()
    assert 'class="report-controls"' in bang and 'class="report-seg"' in bang and 'id="report-chips"' in bang
    assert "bc-dau" not in bang and "report-them" not in bang
    tong_quan = client.get("/").content.decode()
    assert "bc-dau" not in tong_quan and "report-them" not in tong_quan
