"""Bố cục Báo cáo tổng hợp theo bản vẽ 18.09: chip bộ lọc, cột định danh ghim, ba trạng thái bộ lọc."""
import pytest

from reports.models import ReportSource
from reports.tests.test_aggregations import bang_mkt, dong_mau  # noqa: F401 — fixture
from reports.tests.test_che_do_so_lieu import _nop
from reports.tests.test_mkt_derived_revenue import mkt_source, van_don  # noqa: F401 — fixture
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
    Nhân sự); Xóa lọc chỉ giữ nguồn; số bộ lọc bỏ được là huy hiệu của thanh dọc"""
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
    assert html.count('class="report-chip"') == 5 and 'class="chip-xoa"' in html and 'class="chip-clear"' in html
    # Không lọc gì: Kỳ mặc định không bỏ được, không huy hiệu, không Xóa lọc
    r0 = client.get("/bao-cao/tong-hop/", {"nguon": nguon.table.code})
    assert r0.context["filters_active"] == 0 and r0.context["chips"][0]["url"] == "" and 'class="chip-clear"' not in r0.content.decode()
    assert 'class="huy-hieu" aria-hidden="true" hidden' in r0.content.decode()


def test_cot_dinh_danh_ghim_theo_cach_xem(client, nguon, nguoi_dung):
    """AC-22.13 — Cột định danh theo lớp tổng quát `.report-identity`, vị trí 1–5: khối ngày = STT · Team · Nhân sự ·
    Leader · Lần nộp (luôn từng lần nộp, 01.10.2026); chỉ STT và Nhân sự (nguồn không có Loại tiền) đứng yên, `left`
    bằng biến CSS đặt trên bảng, cột đứng yên cuối mang lớp mép; Team, Leader, Lần nộp trôi theo (`report-troi`,
    02.10.2026); dòng Tổng mỗi cột định danh một ô, nhãn ở ô Nhân sự"""
    client.force_login(nguoi_dung["admin"])
    r = _get(client, nguon)
    cols = r.context["identity_columns"]
    # Khối theo ngày như ảnh mẫu (ADR-042): STT · Team · Nhân sự · Leader · Lần nộp, không có cột Ngày
    assert [(c["code"], c["kind"], c["pos"], c["sticky"], c["edge"]) for c in cols] == [
        ("stt", "id-stt", 1, True, False), ("team", "id-team", 2, False, False),
        ("person", "id-nhan-su", 3, True, True), ("leader", "id-leader", 4, False, False), ("lan", "id-lan", 5, False, False)]
    kieu = "--id-left-3:calc(var(--w-stt))"
    assert r.context["identity_style"] == kieu
    html = r.content.decode()
    assert f'<table class="bang report-table" style="{kieu}">' in html
    assert '<th scope="row" class="report-identity id-nhan-su report-identity-edge" data-pos="3">TỔNG CỘNG</th>' in html
    assert 'class="report-identity report-troi id-lan" data-pos="5">Lần nộp</th>' in html
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
    nút Ngưỡng màu (chỉ người đặt được ngưỡng) và nút Giải thích số liệu nằm một hàng; câu loại tiền và đoạn
    "Tổng trên toàn bộ kết quả khớp bộ lọc · (TT) = …" (cả hai biến thể) thu vào panel Giải thích số liệu ẩn sẵn,
    giữ nguyên từng chữ; cảnh báo dòng chưa có loại tiền còn một dòng gọn, toàn văn ở `title` và trong panel;
    `?nguong=1` mở sẵn panel ngưỡng; Bảng dữ liệu giữ ô Ngưỡng màu dạng mở rộng như cũ"""
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
    # Một hàng: tên bảng, khoảng ngày, hai nút đóng sẵn — không còn đoạn giải thích dài trên bảng
    hang = _doan(html, 'class="report-results-heading"')
    assert f"<h2>{bang_mkt.name}</h2>" in hang and '<span class="report-ky">01/08/2026 – 01/08/2026</span>' in hang
    assert ('<button type="button" class="nut nut-nho" data-mo-ra aria-controls="report-nguong" '
            'aria-expanded="false">Ngưỡng màu</button>') in hang
    assert ('<button type="button" class="nut nut-nho" data-mo-ra aria-controls="report-giai-thich" '
            'aria-expanded="false">Giải thích số liệu</button>') in hang
    assert "(TT) =" not in hang and nhan_tien not in hang
    # Panel ẩn sẵn, đủ chữ như trước: câu loại tiền, khoảng tổng và (TT) kèm biến thể nộp nhiều lần, toàn văn cảnh báo
    panel = _doan(html, '<div class="report-giai-thich" id="report-giai-thich" hidden>')
    assert nhan_tien in panel and canh_bao in panel
    assert ("Tổng trên toàn bộ kết quả khớp bộ lọc · (TT) = đối soát từ vận đơn do marketer phụ trách theo ngày lên "
            "đơn: Số đơn (TT) là số đơn, DS Chốt (TT) là tiền đã thu theo loại tiền của đơn; ngày nào một người nộp "
            "nhiều lần (cùng loại tiền) thì (TT) chỉ hiện ở dòng TỔNG CỘNG của ngày") in panel
    assert html.count(nhan_tien) == 1, "câu loại tiền chỉ còn trong panel"
    # Cảnh báo một dòng gọn: toàn văn ở title
    assert (f'<p class="bao bao-cho report-canh-gon" role="status" title="{canh_bao}"><span>{canh_bao}</span></p>'
            in html)
    # Panel ngưỡng: ẩn sẵn; `?nguong=1` (sau khi lưu lỗi) thì mở sẵn, nút báo đang mở
    assert '<div class="report-nguong" id="report-nguong" hidden>' in html
    mo = client.get("/bao-cao/tong-hop/", {**ky, "nguong": "1"}).content.decode()
    assert '<div class="report-nguong" id="report-nguong">' in mo and 'aria-controls="report-nguong" aria-expanded="true"' in mo
    # Lọc theo Tệp khách hàng: biến thể "để trống" vẫn còn trong panel
    tep = client.get("/bao-cao/tong-hop/", {**ky, "tep": "__missing__"}).content.decode()
    assert "— để trống khi lọc theo Tệp khách hàng" in _doan(tep, 'id="report-giai-thich"')
    # Staff: có Giải thích số liệu, không có nút và panel ngưỡng
    client.force_login(A)
    nv = client.get("/bao-cao/tong-hop/", ky).content.decode()
    assert 'aria-controls="report-giai-thich"' in nv and 'id="report-nguong"' not in nv and "Ngưỡng màu" not in nv
    # Bảng dữ liệu dạng báo cáo giữ ô Ngưỡng màu mở rộng như cũ
    client.force_login(B)
    bang = client.get(f"/bang/{bang_mkt.code}/", {"tu": "2026-08-01", "den": "2026-08-01"}).content.decode()
    assert '<details class="report-nguong" id="report-nguong">' in bang
