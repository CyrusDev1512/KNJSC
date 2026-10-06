"""Một lần bấm Lưu đơn chỉ ra một đơn — AC-6.11 (săn lỗi 06.10.2026).

Nút Lưu đơn đã chặn bấm đúp ở trình duyệt, nhưng cùng một lần gửi đi hai lần ở tầng mạng (trình duyệt gửi lại khi
mạng chập chờn, Back rồi Lưu lại) vẫn ra hai đơn hai mã. Nay form mang mã lần nộp dùng một lần như form báo cáo
(AC-4.12): gửi lại thì báo lại đúng đơn đã lưu, không tạo đơn mới.
"""
import re
import threading
import uuid

import pytest
from django.db import connection

from orders.models import Order

from .test_waybill_new import form_data, setup  # noqa: F401 — fixture `setup` dùng chung

pytestmark = pytest.mark.django_db


def _ma(html):
    return re.search(r'name="ma_lan_nop" value="([0-9a-f-]{36})"', html).group(1)


def test_gui_lai_lan_luu_don_chi_ra_mot_don(client, setup, nguoi_dung):  # noqa: F811
    """AC-6.11 — Form Lên đơn có mã lần nộp; gửi lại đúng lần đó thì chỉ một đơn, lần sau báo lại mã đơn đã lưu; lưu xong form mới có mã mới nên lên đơn tiếp được; form cũ không có mã vẫn lưu được"""
    client.force_login(nguoi_dung["staff_sale_1"])
    ma = _ma(client.get("/van-don/len-don/").content.decode())
    lan_dau = client.post("/van-don/len-don/", {**form_data(setup[2]), "ma_lan_nop": ma})
    don = Order.objects.get()
    assert don.code in lan_dau.content.decode()
    ma_moi = _ma(lan_dau.content.decode())
    assert ma_moi != ma
    lan_hai = client.post("/van-don/len-don/", {**form_data(setup[2]), "ma_lan_nop": ma})
    assert Order.objects.count() == 1
    assert don.code in lan_hai.content.decode() and "không tạo đơn mới" in lan_hai.content.decode()
    client.post("/van-don/len-don/", {**form_data(setup[2]), "ma_lan_nop": ma_moi})
    client.post("/van-don/len-don/", form_data(setup[2]))            # tab mở từ trước bản sửa
    assert Order.objects.count() == 3


@pytest.mark.django_db(transaction=True)
def test_hai_lan_luu_don_cung_luc_chi_ra_mot(setup, nguoi_dung):  # noqa: F811
    """AC-6.11 — Hai yêu cầu cùng một lần Lưu đơn tới cùng lúc (hai luồng, hai kết nối DB) chỉ ra một đơn, cả hai đều trả về đơn đó"""
    from django.test import Client

    ma = str(uuid.uuid4())
    rao, ket = threading.Barrier(2), []

    def gui():
        c = Client()
        c.force_login(nguoi_dung["staff_sale_1"])
        rao.wait()
        try:
            ket.append(re.findall(r"DH-\d{4}-\d{4}", c.post("/van-don/len-don/",
                                                         {**form_data(setup[2]), "ma_lan_nop": ma}).content.decode()))
        finally:
            connection.close()

    luong = [threading.Thread(target=gui) for _ in range(2)]
    [t.start() for t in luong]
    [t.join() for t in luong]
    assert Order.objects.count() == 1
    ma_don = Order.objects.get().code
    assert all(ma_don in k for k in ket)
