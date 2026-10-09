"""Cùng một đường dẫn ở KN ERP và KN CRM: ai vào được, ai bị chặn — AC-1.12 (06.10.2026).

Hai dịch vụ dùng chung view cho các trang quản lý bảng (ADR-015) nhưng gắn quyền khác nhau có chủ ý:
- ERP: Bảng dữ liệu và mọi trang dưới `/bang/` chỉ Manager trong phạm vi, CEO xem, Admin (ADR-045);
- CRM: Leader làm được như Manager trong bộ phận mình (ADR-015, `grant_service._quan_ly_bo_phan`), CEO chỉ xem.

Bảng dưới đây khoá đúng các khác biệt đó. Đường dẫn chung mới mọc ra thì bài đầu báo, để người thêm phải điền
quyền cho cả hai dịch vụ, không để một bên lặng lẽ rộng hơn bên kia.
"""
import pytest
from django.test import Client
from django.urls import URLResolver, get_resolver

from core.constants import Rank
from orders.constants import ACTIVE_WAYBILL_TABLE_CODE
from orders.services import dispatch_service

pytestmark = pytest.mark.django_db

ERP, CRM = "knjsc.urls", "knjsc.urls_bangtinh"
VAI = ("staff_sale_1", "manager_sale", "staff_vd", "leader_vd", "manager_vd", "staff_kt", "ceo", "admin")

# Đường dẫn có ở cả hai dịch vụ → (vai vào được ở ERP, vai vào được ở CRM). Vai khác phải bị chặn (403/404)
CHUNG = {
    "bang/moi/": ({"manager_sale", "manager_vd", "admin"},
                  {"manager_sale", "leader_vd", "manager_vd", "admin"}),
    "bang/<slug:code>/cot/": ({"manager_vd", "admin"}, {"leader_vd", "manager_vd", "admin"}),
    "bang/<slug:code>/nhap/": ({"manager_vd", "admin"}, {"leader_vd", "manager_vd", "admin"}),
    "bang/<slug:code>/mau-nhap.xlsx": ({"manager_vd", "admin"}, {"leader_vd", "manager_vd", "admin"}),
    "doi-mat-khau/": (set(VAI), set(VAI)),
    "nhat-ky/": ({"admin"}, {"admin"}),
    "ma-tran-quyen/": ({"admin"}, {"admin"}),
    "tac-vu/": ({"admin"}, {"admin"}),
}
# Chỉ nhận POST, hoặc cần id có sẵn: không gọi GET được, nhưng vẫn là đường dẫn chung đã rà
CHUNG_KHONG_GET = {
    "", "dang-nhap/", "dang-xuat/", "bang/<slug:code>/cap-quyen/", "bang/<slug:code>/thu-quyen/<int:pk>/",
    "bang/<slug:code>/cot/<int:pk>/bo/", "bang/<slug:code>/nhap/<int:pk>/", "bang/<slug:code>/nhap/<int:pk>/xac-nhan/",
    "tac-vu/<int:pk>/", "tac-vu/<int:pk>/tien-do/", "tac-vu/<int:pk>/tai/",
}


def _duong_dan(conf):
    ra = set()

    def di(ds, truoc=""):
        for p in ds:
            if isinstance(p, URLResolver):
                di(p.url_patterns, truoc + str(p.pattern))
            else:
                ra.add(truoc + str(p.pattern))
    di(get_resolver(conf).url_patterns)
    return ra


def test_duong_dan_chung_deu_da_ra_quyen():
    """AC-1.12 — Mọi đường dẫn có ở cả ERP lẫn CRM đều nằm trong bảng quyền hai dịch vụ"""
    chung = _duong_dan(ERP) & _duong_dan(CRM)
    assert chung == set(CHUNG) | CHUNG_KHONG_GET


@pytest.fixture
def vai(nguoi_dung, departments, make_user):
    dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])
    ds = dict(nguoi_dung)
    ds["ceo"] = make_user("ceo_ma_tran", Rank.CEO)
    ds["leader_vd"] = make_user("leader_vd", Rank.LEADER, departments["vd"])
    ds["manager_vd"] = make_user("manager_vd", Rank.MANAGER, departments["vd"])
    return ds


@pytest.mark.parametrize("mau", sorted(CHUNG))
def test_quyen_tung_vai_o_hai_dich_vu(settings, vai, mau):
    """AC-1.12 — Cùng đường dẫn, từng vai: được vào hay bị chặn ở ERP và CRM đúng bảng đã chốt (cả hai chiều)"""
    settings.GRID_ONLY_TABLES = set()
    duong = "/" + mau.replace("<slug:code>", ACTIVE_WAYBILL_TABLE_CODE)
    for conf, duoc in zip((ERP, CRM), CHUNG[mau]):
        settings.ROOT_URLCONF = conf
        for ten in VAI:
            c = Client()
            c.force_login(vai[ten])
            ma = c.get(duong).status_code
            if ten in duoc:
                assert ma == 200, (conf, duong, ten, ma)
            else:
                assert ma in (403, 404), (conf, duong, ten, ma)
