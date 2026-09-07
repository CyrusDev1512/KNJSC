"""Leader như Manager trong bộ phận mình — ADR-015, AC-11.33.

Người dùng chốt 06.09.2026: trong KN CRM, Leader được thêm, sửa, xoá, tạo,
nhập tệp, xuất Excel như Manager, giới hạn trong bộ phận mình. Riêng cấp
quyền cho người khác vẫn là việc của Manager. Bài này kiểm **cả hai chiều**:
Leader đúng bộ phận làm được; Staff, Leader bộ phận khác (kể cả khi được cấp
quyền Xem) bị từ chối có nhật ký hoặc 404 ngoài phạm vi.
"""
import pytest
from django.test import override_settings

from core.constants import AuditAction, Rank
from core.models import AuditLog
from forms_builder.meaning import FieldType
from forms_builder.models import ColumnDef, GrantAction, TableDef
from forms_builder.services import grant_service

pytestmark = pytest.mark.django_db

ERP = override_settings(ROOT_URLCONF="knjsc.urls")


@pytest.fixture
def bang_sale(departments, nguoi_dung):
    bang = TableDef.objects.create(
        name="Đơn hàng Sale", code="don_sale",
        department=departments["sale"], created_by=nguoi_dung["manager_sale"],
    )
    ColumnDef.objects.create(table=bang, name="Khách", code="khach", field_type=FieldType.TEXT, order=0)
    return bang


@pytest.fixture
def leader_mkt(departments, make_user):
    return make_user("leader_mkt", Rank.LEADER, departments["mkt"])


def _tu_choi():
    return AuditLog.objects.filter(action=AuditAction.DENIED).count()


def test_leader_quan_ly_trong_bo_phan_minh(client, bang_sale, nguoi_dung, leader_mkt, departments):
    """AC-11.33 — Leader của bộ phận sở hữu bảng tạo bảng, sửa cột, chèn/bỏ cột trên lưới, tạo thư mục, nhập tệp, xuất Excel như Manager; Staff bị 403 có nhật ký; Leader bộ phận khác không thấy bảng (404), được cấp quyền Xem thì xem nhưng không đổi cấu trúc (403 có nhật ký); cấp quyền cho người khác vẫn chỉ Manager"""
    ld = nguoi_dung["leader_sale_1"]
    client.force_login(ld)
    # Trong KN CRM: thư mục, chèn/bỏ cột, xuất
    assert client.post("/bang-tinh/thu-muc/moi/", {"name": "Q3", "ve": "don_sale"}).status_code == 302
    assert client.post("/bang-tinh/don_sale/them-cot/", {"canh": "khach", "so": 1}).status_code == 200
    assert bang_sale.columns.filter(code="cot_moi_1").exists()
    assert client.post("/bang-tinh/don_sale/xoa-cot/", {"cot": ["cot_moi_1"]}).status_code == 200
    assert client.get("/bang-tinh/don_sale/").context["duoc_quan_ly_cot"] is True
    assert client.post("/bang-tinh/don_sale/xuat/").status_code in (200, 302)
    # Ở KN ERP: tạo bảng vào đúng bộ phận mình, Sửa cột, Nhập tệp
    with ERP:
        assert client.get("/bang/moi/").status_code == 200
        kq = client.post("/bang/moi/", {"name": "Bảng của Leader", "code": "bang_leader", "description": ""})
        assert kq.status_code == 302
        assert TableDef.objects.get(code="bang_leader").department == departments["sale"]
        assert client.get("/bang/don_sale/cot/").status_code == 200
        assert client.get("/bang/don_sale/nhap/").status_code == 200
        # Cấp quyền cho người khác: vẫn chỉ Manager
        truoc = _tu_choi()
        assert client.post("/bang/don_sale/cap-quyen/", {}).status_code == 403
        assert _tu_choi() == truoc + 1
        client.force_login(nguoi_dung["manager_sale"])
        assert client.post("/bang/don_sale/cap-quyen/", {}).status_code in (200, 302)

    # Staff: từ chối có nhật ký ở tạo bảng và Sửa cột
    client.force_login(nguoi_dung["staff_sale_1"])
    truoc = _tu_choi()
    with ERP:
        assert client.get("/bang/moi/").status_code == 403
        assert client.get("/bang/don_sale/cot/").status_code == 403
        assert client.get("/bang/don_sale/nhap/").status_code == 403
    assert _tu_choi() == truoc + 3

    # Leader bộ phận khác: không thấy bảng Sale → 404
    client.force_login(leader_mkt)
    with ERP:
        assert client.get("/bang/don_sale/cot/").status_code == 404
        assert client.get("/bang/don_sale/nhap/").status_code == 404
    assert client.post("/bang-tinh/don_sale/them-cot/", {"canh": "khach", "so": 1}).status_code == 404
    # Được cấp quyền Xem: thấy bảng, nhưng cấu trúc và nhập vẫn 403 có nhật ký
    grant_service.grant(table=bang_sale, user=leader_mkt, action=GrantAction.VIEW, actor=nguoi_dung["manager_sale"])
    grant_service.clear_cache(leader_mkt)
    assert client.get("/bang-tinh/don_sale/").status_code == 200
    truoc = _tu_choi()
    with ERP:
        assert client.get("/bang/don_sale/cot/").status_code == 403
        assert client.get("/bang/don_sale/nhap/").status_code == 403
    assert client.post("/bang-tinh/don_sale/them-cot/", {"canh": "khach", "so": 1}).status_code == 403
    assert client.post("/bang-tinh/thu-muc/moi/", {"name": "Lén", "ve": "don_sale"}).status_code == 403
    assert _tu_choi() == truoc + 4
    assert grant_service.can_manage_columns(leader_mkt, bang_sale) is False
    assert grant_service.can_import(leader_mkt, bang_sale) is False
