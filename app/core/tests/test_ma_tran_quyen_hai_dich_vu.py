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
# Đường dẫn chung chỉ nhận POST mà ghi quyền → vai được làm ở (ERP, CRM): chỉ Manager bộ phận sở hữu và Admin (ADR-015
# mục 5). Thấy được bảng (quyền Xem, Kế toán, Sale có dòng vận đơn) không có nghĩa là cấp, thu quyền được (TL-01)
CHUNG_POST = {
    "bang/<slug:code>/cap-quyen/": ({"manager_vd", "admin"}, {"manager_vd", "admin"}),
    "bang/<slug:code>/thu-quyen/<int:pk>/": ({"manager_vd", "admin"}, {"manager_vd", "admin"}),
}
# Chỉ nhận POST, hoặc cần id có sẵn: không gọi GET được, nhưng vẫn là đường dẫn chung đã rà
CHUNG_KHONG_GET = {
    "", "dang-nhap/", "dang-xuat/",
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
    assert chung == set(CHUNG) | set(CHUNG_POST) | CHUNG_KHONG_GET


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


#: Ba kiểu "thấy bảng vận đơn mà không sở hữu": Manager được cấp Xem, Manager Kế toán, Manager Sale có dòng vận đơn
KE_NGOAI = ("manager_mkt", "manager_kt", "manager_sale")


@pytest.fixture
def vai_cap_quyen(vai, nguoi_dung, departments, make_user):
    """Bảng vận đơn cùng ba Manager thấy được nó mà không sở hữu nó (TL-01)."""
    from forms_builder.models import DataRecord, GrantAction, TableDef
    from forms_builder.services import grant_service

    bang = TableDef.objects.get(code=ACTIVE_WAYBILL_TABLE_CODE)
    ds = dict(vai)
    grant_service.grant(table=bang, user=ds["manager_mkt"], action=GrantAction.VIEW, actor=ds["manager_vd"])
    ds["manager_kt"] = make_user("manager_kt", Rank.MANAGER, departments["kt"])
    DataRecord.objects.create(table=bang, department=departments["sale"], created_by=ds["manager_sale"],
                              data={"ma_don": "TL01-1"})
    grant_service.clear_cache(ds["manager_mkt"])
    return bang, ds


@pytest.mark.parametrize("mau", sorted(CHUNG_POST))
def test_cap_thu_quyen_tung_vai_o_hai_dich_vu(settings, vai_cap_quyen, mau):
    """AC-1.12 — Cấp và thu quyền bảng vận đơn ở cả ERP lẫn CRM: chỉ Manager bộ phận sở hữu và Admin làm được; mọi
    vai khác, kể cả Manager thấy được bảng (quyền Xem, Kế toán, Sale có dòng vận đơn), bị 403/404 và không quyền nào
    đổi (TL-01)"""
    from forms_builder.models import Grant, GrantAction
    from forms_builder.services import grant_service

    settings.GRID_ONLY_TABLES = set()
    bang, ds = vai_cap_quyen
    for conf, duoc in zip((ERP, CRM), CHUNG_POST[mau]):
        settings.ROOT_URLCONF = conf
        for ten in VAI + ("manager_mkt", "manager_kt"):
            c = Client()
            c.force_login(ds[ten])
            if "cap-quyen" in mau:
                truoc = Grant.objects.count()
                ma = c.post(f"/bang/{bang.code}/cap-quyen/", {"user": ds["staff_mkt"].pk, "action": "view"}).status_code
                sau = Grant.objects.count()
                if ten in duoc:
                    assert ma == 302 and sau == truoc + 1, (conf, ten, ma)
                    assert Grant.objects.latest("pk").granted_by == ds[ten]
                else:
                    assert ma in (403, 404) and sau == truoc, (conf, ten, ma)
            else:
                q = grant_service.grant(table=bang, user=ds["staff_mkt"], action=GrantAction.EDIT, actor=ds["manager_vd"])
                ma = c.post(f"/bang/{bang.code}/thu-quyen/{q.pk}/").status_code
                q.refresh_from_db()
                if ten in duoc:
                    assert ma == 302 and q.deleted_at is not None, (conf, ten, ma)
                else:
                    assert ma in (403, 404) and q.deleted_at is None, (conf, ten, ma)


@pytest.mark.parametrize("ten", KE_NGOAI)
@pytest.mark.parametrize("conf", (ERP, CRM))
def test_quan_ly_bo_phan_khac_khong_tu_cap_hay_thu_quyen(settings, vai_cap_quyen, conf, ten):
    """AC-3.7 — Gọi thẳng cấp, thu quyền bảng vận đơn: Manager thấy được bảng mà không sở hữu (quyền Xem, Kế toán
    ADR-025, Sale có dòng vận đơn ADR-033) không tự cấp Sửa cho mình hay team mình, không thu quyền của chủ; 403 kèm
    nhật ký Từ chối (TL-01)"""
    from core.constants import AuditAction
    from core.models import AuditLog
    from forms_builder.models import Grant, GrantAction, TableDef
    from forms_builder.services import grant_service
    from org.models import Team

    settings.GRID_ONLY_TABLES = set()
    settings.ROOT_URLCONF = conf
    bang, ds = vai_cap_quyen
    ke = ds[ten]
    quyen_chu = grant_service.grant(table=bang, user=ds["staff_sale_1"], action=GrantAction.EDIT, actor=ds["manager_vd"])
    team = Team.objects.create(name=f"Team {ten}", department=ke.profile.department)
    ke.profile.team = team
    ke.profile.save(update_fields=["team"])
    assert TableDef.objects.in_scope(ke).filter(pk=bang.pk).exists()      # tiền đề: kẻ này thấy được bảng
    c = Client()
    c.force_login(ke)
    so_quyen, tu_choi = Grant.objects.count(), AuditLog.objects.filter(action=AuditAction.DENIED).count()

    assert c.post(f"/bang/{bang.code}/cap-quyen/", {"user": ke.pk, "action": "edit"}).status_code == 403
    assert c.post(f"/bang/{bang.code}/cap-quyen/", {"team": team.pk, "action": "edit"}).status_code == 403
    assert c.post(f"/bang/{bang.code}/thu-quyen/{quyen_chu.pk}/").status_code == 403

    quyen_chu.refresh_from_db()
    assert quyen_chu.deleted_at is None and Grant.objects.count() == so_quyen
    assert AuditLog.objects.filter(action=AuditAction.DENIED).count() == tu_choi + 3
    grant_service.clear_cache(ke)
    assert bang.pk not in grant_service.granted_table_ids(ke, GrantAction.EDIT)
