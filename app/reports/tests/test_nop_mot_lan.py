"""Một lần nộp chỉ ghi một báo cáo — AC-4.12 (săn lỗi 06.10.2026).

Lỗi tìm được: gửi lại cùng một lần nộp (mạng chập chờn làm trình duyệt gửi lại, bấm Back rồi Nộp lại, hai yêu cầu
tới cùng lúc) thì mỗi lần thành một báo cáo — Doanh số, CPQC trong Báo cáo tổng hợp bị cộng gấp đôi, gấp ba. Nay mỗi
lần mở form có một mã lần nộp dùng một lần (`ma_lan_nop`); gửi lại đúng mã đó thì không tạo bản mới. Nộp nhiều lần
trong ngày vẫn được (AC-4.7) — mỗi lần mở form là một mã mới.
"""
import re
import threading
import uuid

import pytest
from django.db import connection

from reports.models import DailyReport
from reports.tests.test_bao_cao_ngay import bm_mkt  # noqa: F401

pytestmark = pytest.mark.django_db


def _ma_lan_nop(html):
    return re.search(r'name="ma_lan_nop" value="([0-9a-f-]{36})"', html).group(1)


def _du_lieu(bm, ma, **them):
    return {"bieu_mau": bm.code, "ma_lan_nop": ma, "ngay": "2026-08-28", "so_mess": "1000", "so_don": "50",
            "doanh_so": "5000000", **them}


def test_gui_lai_cung_lan_nop_chi_ghi_mot_bao_cao(client, bm_mkt, nguoi_dung):  # noqa: F811
    """AC-4.12 — Form nộp có mã lần nộp; gửi lại đúng lần nộp đó (mạng gửi lại, Back rồi Nộp) chỉ ghi một báo cáo, lần sau báo "đã ghi, không tạo thêm"; mở form lần nữa là mã mới và nộp tiếp được (AC-4.7); form cũ không có mã vẫn nộp được"""
    client.force_login(nguoi_dung["staff_mkt"])
    ma = _ma_lan_nop(client.get("/bao-cao/").content.decode())
    for _ in range(3):
        kq = client.post("/bao-cao/", _du_lieu(bm_mkt, ma), follow=True)
        assert kq.status_code == 200
    assert DailyReport.objects.filter(created_by=nguoi_dung["staff_mkt"]).count() == 1
    assert "không tạo thêm" in kq.content.decode()

    ma_moi = _ma_lan_nop(client.get("/bao-cao/").content.decode())
    assert ma_moi != ma
    client.post("/bao-cao/", _du_lieu(bm_mkt, ma_moi))
    du_lieu_cu = _du_lieu(bm_mkt, "")
    du_lieu_cu.pop("ma_lan_nop")
    client.post("/bao-cao/", du_lieu_cu)                          # tab mở từ trước bản sửa
    assert DailyReport.objects.filter(created_by=nguoi_dung["staff_mkt"]).count() == 3


def test_nop_loi_roi_sua_lai_cung_ma_van_ghi_duoc(client, bm_mkt, nguoi_dung):  # noqa: F811
    """AC-4.12 — Lần nộp bị từ chối (ô số gõ chữ) không giữ chỗ mã: sửa lại rồi nộp với cùng mã thì ghi được đúng một báo cáo; form hiện lại giữ nguyên mã"""
    client.force_login(nguoi_dung["staff_mkt"])
    ma = _ma_lan_nop(client.get("/bao-cao/").content.decode())
    kq = client.post("/bao-cao/", _du_lieu(bm_mkt, ma, so_mess="abc"))
    assert kq.status_code == 200 and _ma_lan_nop(kq.content.decode()) == ma
    assert not DailyReport.objects.exists()
    client.post("/bao-cao/", _du_lieu(bm_mkt, ma))
    client.post("/bao-cao/", _du_lieu(bm_mkt, ma))
    assert DailyReport.objects.count() == 1


def test_ma_cua_nguoi_khac_khong_chan_nguoi_nay(client, bm_mkt, nguoi_dung):  # noqa: F811
    """AC-4.12 — Mã lần nộp tính riêng từng người: hai người trùng mã (giả mạo hay ngẫu nhiên) vẫn mỗi người một báo cáo, không ai thấy báo cáo của người kia"""
    ma = str(uuid.uuid4())
    for ai in ("staff_mkt", "manager_mkt"):
        client.force_login(nguoi_dung[ai])
        client.post("/bao-cao/", _du_lieu(bm_mkt, ma))
    assert DailyReport.objects.count() == 2


@pytest.mark.django_db(transaction=True)
def test_hai_yeu_cau_cung_luc_chi_ghi_mot(bm_mkt, nguoi_dung):  # noqa: F811
    """AC-4.12 — Hai yêu cầu cùng một lần nộp tới cùng lúc (hai luồng thật, hai kết nối DB) chỉ ghi một báo cáo, không lỗi"""
    from django.test import Client

    ma = str(uuid.uuid4())
    rao, ket = threading.Barrier(2), []

    def gui():
        c = Client()
        c.force_login(nguoi_dung["staff_mkt"])
        rao.wait()
        try:
            ket.append(c.post("/bao-cao/", _du_lieu(bm_mkt, ma)).status_code)
        finally:
            connection.close()

    luong = [threading.Thread(target=gui) for _ in range(2)]
    [t.start() for t in luong]
    [t.join() for t in luong]
    assert ket == [302, 302]
    assert DailyReport.objects.count() == 1
