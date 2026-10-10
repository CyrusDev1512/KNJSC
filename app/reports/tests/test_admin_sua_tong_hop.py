"""Admin sửa lần nộp ngay trên Báo cáo tổng hợp — ADR-050 (chủ dự án 10.10.2026, duyệt mockup tương tác).

"Tôi muốn quản trị có chức năng khi vào báo cáo tổng hợp có thể sửa dữ liệu": nút ✎ ở ô đầu mỗi dòng lần nộp, chỉ
Admin thấy; bấm mở hộp sửa chạy đúng luồng Sửa báo cáo có lịch sử (ADR-032) ở chế độ hộp `khung=1`; lưu xong bảng đổi
tại chỗ. Dòng Toàn kỳ, TỔNG CỘNG, nguồn Vận đơn và Bảng dữ liệu (ADR-014) không có ✎. Quyền máy chủ không đổi:
`daily_service.can_amend` như cũ.
"""
import re
from datetime import date, timedelta

import pytest

from core.constants import AuditAction, Rank
from core.identity import employee_code
from core.models import AuditLog
from reports.services import daily_service
from reports.tests.test_activity import delivery_source  # noqa: F401
from reports.tests.test_aggregations import bang_mkt  # noqa: F401
from reports.tests.test_mkt_derived_revenue import mkt_source  # noqa: F401
from reports.tests.test_mkt_excel import marketing_scope  # noqa: F401

pytestmark = pytest.mark.django_db

NGAY = date(2026, 8, 28)
KY = {"tu": "2026-08-27", "den": "2026-08-28"}
NUT = 'class="report-sua"'


def _nop_mkt(bm, nguoi, ngay=NGAY, **so):
    """Nộp một báo cáo Marketing qua đúng đường của form (có DailyReport), số theo mã cột."""
    gia_tri = {"ngay": ngay.isoformat(), "so_mess": "100", "cpqc": "2000000", "so_don": "10",
               "doanh_so": "5000000", **so}
    du_lieu = {f.field.code: gia_tri[f.link.column.code] for f in bm.ordered_fields()
               if getattr(f, "link", None) and f.link.column.code in gia_tri}
    return daily_service.submit(bm, du_lieu, report_date=ngay, actor=nguoi)


def _ma_truong(bm, cot):
    """Tên ô trên form (mã trường) của một cột bảng."""
    return next(f.field.code for f in bm.ordered_fields() if getattr(f, "link", None) and f.link.column.code == cot)


@pytest.fixture
def mkt(bang_mkt, mkt_source, nguoi_dung):  # noqa: F811
    """Nguồn Báo cáo Marketing cấu hình thật (`configure_erp_reports`), ba lần nộp qua form: staff_mkt nộp hai lần
    ngày 28, một lần ngày 27."""
    bm = mkt_source.table.forms.get()
    nhan_vien = nguoi_dung["staff_mkt"]
    lan = [_nop_mkt(bm, nhan_vien, so_mess="120"), _nop_mkt(bm, nhan_vien, so_mess="80"),
           _nop_mkt(bm, nhan_vien, ngay=NGAY - timedelta(days=1), so_mess="60")]
    return {"bm": bm, "nguon": {"nguon": bang_mkt.code, **KY}, "lan": lan}


def _khoi(html, loai):
    return "".join(re.findall(rf'<section class="report-block report-block-{loai}".*?</section>', html, re.S))


def test_nut_sua_chi_o_dong_lan_nop(client, mkt, nguoi_dung):
    """AC-50.1 — Admin mở Báo cáo tổng hợp nguồn Marketing: mỗi dòng lần nộp (khối ngày) có đúng một nút ✎ ở ô đầu,
    trỏ hộp sửa `/bao-cao/<id>/sua/?khung=1` của đúng lần nộp đó, dòng mang `data-lan-nop`; khối Toàn kỳ và mọi dòng
    TỔNG CỘNG không có ✎. Chế độ Gộp (một bảng mọi lần nộp) cũng vậy"""
    client.force_login(nguoi_dung["admin"])
    mong = {str(r.pk) for r in mkt["lan"]}
    for them in ({}, {"gop": "1"}):
        html = client.get("/bao-cao/tong-hop/", {**mkt["nguon"], **them}).content.decode()
        assert html.count(NUT) == 3, them
        assert set(re.findall(r'data-sua-url="/bao-cao/(\d+)/sua/\?khung=1"', html)) == mong
        assert set(re.findall(r'data-lan-nop="(\d+)"', html)) == mong
        assert NUT not in _khoi(html, "period")
        for tong in re.findall(r'<tr class="report-total".*?</tr>', html, re.S):
            assert NUT not in tong
    html = client.get("/bao-cao/tong-hop/", mkt["nguon"]).content.decode()
    assert _khoi(html, "day").count(NUT) == 3 and 'id="report-sua-hop"' in html


def test_vai_khac_khong_thay_nut_sua(client, mkt, nguoi_dung, make_user):
    """AC-50.2 — Chỉ Admin thấy ✎: Manager, Staff, Kế toán, CEO mở cùng trang vẫn 200 nhưng không có nút, không có
    hộp sửa; quyền sửa ở máy chủ không đổi (Manager vẫn sửa được qua Lịch sử báo cáo)"""
    ceo = make_user("ceo_bc", Rank.CEO)
    for nguoi in (nguoi_dung["manager_mkt"], nguoi_dung["staff_mkt"], nguoi_dung["staff_kt"], ceo):
        client.force_login(nguoi)
        r = client.get("/bao-cao/tong-hop/", mkt["nguon"])
        html = r.content.decode()
        assert r.status_code == 200 and NUT not in html and 'id="report-sua-hop"' not in html, nguoi.username
    assert daily_service.can_amend(nguoi_dung["manager_mkt"], mkt["lan"][0])


def test_bang_du_lieu_khong_co_nut_sua(client, mkt, nguoi_dung):
    """AC-50.3 — Bảng dữ liệu dạng báo cáo dùng chung bảng khối với Báo cáo tổng hợp nhưng chỉ để xem (ADR-014):
    Admin mở cũng không có ✎, không có hộp sửa"""
    client.force_login(nguoi_dung["admin"])
    html = client.get(f"/bang/{mkt['bm'].table.code}/", KY).content.decode()
    assert "report-block" in html and NUT not in html and 'id="report-sua-hop"' not in html


def test_nguon_van_don_khong_co_nut_sua(client, delivery_source, nguoi_dung):  # noqa: F811
    """AC-50.3 — Nguồn Vận đơn: mỗi dòng là số gộp theo ngày × người, không phải một lần nộp, nên Admin không thấy ✎
    dù bảng nguồn có báo cáo đã nộp"""
    client.force_login(nguoi_dung["admin"])
    r = client.get("/bao-cao/tong-hop/", {"nguon": delivery_source.table.code, "tu": "2026-08-01", "den": "2026-08-01"})
    html = r.content.decode()
    assert r.status_code == 200 and "report-block" in html
    assert NUT not in html and 'id="report-sua-hop"' not in html


def test_hop_sua_tra_phan_form(client, mkt, nguoi_dung, make_user):
    """AC-50.4 — `GET /bao-cao/<id>/sua/?khung=1` trả phần form cho hộp, không có khung trang: ô nhập của lần nộp,
    phiên bản, xem trước chỉ số, nút Lịch sử sửa (0). Quyền như trang Sửa báo cáo: Admin và Manager bộ phận 200;
    người nộp (Staff), CEO, Manager bộ phận khác 404"""
    bao_cao = mkt["lan"][0]
    url = f"/bao-cao/{bao_cao.pk}/sua/?khung=1"
    client.force_login(nguoi_dung["admin"])
    r = client.get(url)
    html = r.content.decode()
    assert r.status_code == 200
    assert 'class="topbar"' not in html and "<html" not in html
    assert f'name="version" value="{bao_cao.record.updated_at.isoformat()}"' in html
    assert f'name="{_ma_truong(mkt["bm"], "so_mess")}"' in html and 'id="xem-truoc-chi-so"' in html
    assert "Lịch sử sửa (0)" in html and employee_code(nguoi_dung["staff_mkt"]) in html
    client.force_login(nguoi_dung["manager_mkt"])
    assert client.get(url).status_code == 200
    for nguoi in (nguoi_dung["staff_mkt"], make_user("ceo_hop", Rank.CEO), nguoi_dung["manager_sale"]):
        client.force_login(nguoi)
        assert client.get(url).status_code == 404, nguoi.username
        assert client.post(url, {"version": "x"}).status_code == 404, nguoi.username


def test_hop_sua_luu_204_ghi_lich_su(client, mkt, nguoi_dung):
    """AC-50.5 — Lưu trong hộp: trả 204 (không chuyển trang, không flash), `X-Bao-Cao-Doi: 1`, số mới vào DB, một
    ReportRevision của Admin và một dòng nhật ký Sửa; lưu lại đúng số cũ thì 204, `X-Bao-Cao-Doi: 0`, không thêm lịch
    sử; ngày, người nộp giữ nguyên"""
    bao_cao, admin = mkt["lan"][0], nguoi_dung["admin"]
    o = _ma_truong(mkt["bm"], "so_mess")
    url = f"/bao-cao/{bao_cao.pk}/sua/?khung=1"
    client.force_login(admin)
    r = client.post(url, {"version": bao_cao.record.updated_at.isoformat(), o: "150"})
    assert r.status_code == 204 and r["X-Bao-Cao-Doi"] == "1"
    bao_cao.record.refresh_from_db()
    assert bao_cao.record.data["so_mess"] == 150 and bao_cao.record.data["ngay"] == NGAY.isoformat()
    assert bao_cao.revisions.count() == 1 and bao_cao.revisions.get().actor == admin
    assert AuditLog.objects.filter(action=AuditAction.UPDATE, actor=admin, target_id=str(bao_cao.pk)).count() == 1
    r = client.post(url, {"version": bao_cao.record.updated_at.isoformat(), o: "150"})
    assert r.status_code == 204 and r["X-Bao-Cao-Doi"] == "0"
    assert bao_cao.revisions.count() == 1
    assert "Lịch sử sửa (1)" in client.get(url).content.decode()


def test_hop_sua_thieu_o_bat_buoc_400(client, mkt, nguoi_dung):
    """AC-50.6 — Để trống ô bắt buộc rồi Lưu trong hộp: 400, phần form báo đúng lời máy chủ "Chưa điền các trường
    bắt buộc: …", không ghi gì"""
    bao_cao = mkt["lan"][0]
    client.force_login(nguoi_dung["admin"])
    r = client.post(f"/bao-cao/{bao_cao.pk}/sua/?khung=1",
                    {"version": bao_cao.record.updated_at.isoformat(), _ma_truong(mkt["bm"], "so_mess"): ""})
    assert r.status_code == 400
    assert "Chưa điền các trường bắt buộc" in r.content.decode() and "<html" not in r.content.decode()
    assert bao_cao.revisions.count() == 0


def test_hop_sua_xung_dot_409_nap_so_moi(client, mkt, nguoi_dung):
    """AC-50.7 — Admin mở hộp, Manager lưu trước (đổi Số đơn): Admin bấm Lưu với phiên bản cũ thì 409, không ghi đè;
    hộp nạp số mới nhất và phiên bản mới, ô Manager vừa đổi tô vàng (`vua-doi`), câu báo nêu mã người vừa sửa; Admin
    bấm Lưu lại với phiên bản mới thì được"""
    bao_cao, bm = mkt["lan"][0], mkt["bm"]
    o_mess, o_don = _ma_truong(bm, "so_mess"), _ma_truong(bm, "so_don")
    cu = bao_cao.record.updated_at.isoformat()
    client.force_login(nguoi_dung["admin"])
    # Hộp mở: số lúc mở nằm ở các ô ẩn `goc-…`, gửi kèm khi Lưu
    goc = dict(re.findall(r'name="(goc-[^"]+)" value="([^"]*)"', client.get(f"/bao-cao/{bao_cao.pk}/sua/?khung=1")
                          .content.decode()))
    assert goc[f"goc-{o_don}"] == "10"
    client.force_login(nguoi_dung["manager_mkt"])
    assert client.post(f"/bao-cao/{bao_cao.pk}/sua/", {"version": cu, o_don: "99"}).status_code == 302
    client.force_login(nguoi_dung["admin"])
    r = client.post(f"/bao-cao/{bao_cao.pk}/sua/?khung=1", {"version": cu, **goc, o_mess: "777"})
    html = r.content.decode()
    bao_cao.record.refresh_from_db()
    assert r.status_code == 409 and bao_cao.record.data["so_mess"] == 120 and bao_cao.record.data["so_don"] == 99
    moi = bao_cao.record.updated_at.isoformat()
    assert f'name="version" value="{moi}"' in html
    assert re.search(rf'name="{o_don}"[^>]*value="99"', html)
    assert re.search(rf'<div class="truong vua-doi"[^>]*>\s*<label for="o-{o_don}"', html)
    assert not re.search(rf'<div class="truong vua-doi"[^>]*>\s*<label for="o-{o_mess}"', html)
    assert employee_code(nguoi_dung["manager_mkt"]) in html
    r = client.post(f"/bao-cao/{bao_cao.pk}/sua/?khung=1", {"version": moi, o_mess: "777"})
    bao_cao.record.refresh_from_db()
    assert r.status_code == 204 and bao_cao.record.data["so_mess"] == 777 and bao_cao.record.data["so_don"] == 99


def test_xung_dot_khong_do_lan_sua_thi_khong_neu_ten(client, mkt, nguoi_dung):
    """AC-50.7 — Câu báo 409 chỉ nêu mã người sửa khi lần sửa của họ có sau lúc Admin mở hộp: Manager sửa từ trước,
    Admin mở hộp, rồi dòng đổi theo đường khác (không có lần sửa) — câu báo không đổ cho Manager, và không nhắc ô tô
    vàng khi không ô nào khác số lúc mở hộp"""
    bao_cao, bm = mkt["lan"][0], mkt["bm"]
    o_don = _ma_truong(bm, "so_don")
    client.force_login(nguoi_dung["manager_mkt"])
    cu = bao_cao.record.updated_at.isoformat()
    assert client.post(f"/bao-cao/{bao_cao.pk}/sua/", {"version": cu, o_don: "11"}).status_code == 302
    client.force_login(nguoi_dung["admin"])
    trang = client.get(f"/bao-cao/{bao_cao.pk}/sua/?khung=1").content.decode()
    luc_mo = re.search(r'name="version" value="([^"]+)"', trang).group(1)
    bao_cao.record.refresh_from_db()
    bao_cao.record.save(skip_sync=True)   # đổi `updated_at` mà không qua `amend`
    r = client.post(f"/bao-cao/{bao_cao.pk}/sua/?khung=1", {"version": luc_mo, o_don: "12"})
    html = r.content.decode()
    assert r.status_code == 409 and "Báo cáo vừa được người khác sửa." in html
    assert employee_code(nguoi_dung["manager_mkt"]) + " vừa sửa" not in html
    assert "ô tô vàng" not in html and "truong vua-doi" not in html


def test_ngan_sach_truy_van_khi_co_nut_sua(client, mkt, nguoi_dung, django_assert_max_num_queries):
    """AC-50.8 — Gắn mã lần nộp cho nút ✎ đi chung câu truy vấn dòng (LEFT JOIN 1-1): trang của Admin vẫn ≤ 10 truy
    vấn như AC-46.9"""
    client.force_login(nguoi_dung["admin"])
    client.get("/bao-cao/tong-hop/", mkt["nguon"])
    with django_assert_max_num_queries(10):
        assert client.get("/bao-cao/tong-hop/", mkt["nguon"]).status_code == 200
