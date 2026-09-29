"""Tạo bảng, sửa cột kèm cấp quyền, nhập tệp chạy **ngay trong KN CRM** — ADR-015, AC-11.34.

Ba màn hình này là view của `forms_builder` gắn thêm vào URLconf 8021, template
kế thừa khung KN CRM có sidebar qua biến `khung`. Tên `bang` và `bang_xem`
ở KN CRM dẫn về trang thư mục và lưới; Bảng dữ liệu (`/bang/`) vẫn không có.
"""
import pytest
from django.test import override_settings

from core.constants import AuditAction, Rank
from core.models import AuditLog
from forms_builder.meaning import FieldType
from forms_builder.models import ColumnDef, TableDef

pytestmark = pytest.mark.django_db

ERP = override_settings(ROOT_URLCONF="knjsc.urls")
KHUNG_CRM = "KN CRM<small>Bảng tính</small>"
KHUNG_ERP = 'class="sp-erp"'  # Khung Solarpunk ERP, ADR-028.


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


def test_tao_bang_sua_cot_nhap_tep_trong_kn_crm(client, bang_sale, nguoi_dung, leader_mkt, departments):
    """AC-11.34 — Ở KN CRM, Leader trở lên tạo bảng, sửa cột và nhập tệp ngay trong khung có sidebar (mục Nhập tệp liệt kê bảng được nhập); Manager có mục Cấp quyền, Leader vào mục đó bị 403 có nhật ký; Staff bị 403 ở mục Nhập tệp; `bang`/`bang_xem` dẫn về thư mục và lưới; Bảng dữ liệu `/bang/` vẫn 404; ở KN ERP các màn này vẫn dùng khung ERP"""
    ld = nguoi_dung["leader_sale_1"]
    client.force_login(ld)
    # Sidebar có Nhập tệp, không có Cấp quyền (Manager mới có)
    ben = client.get("/").content.decode().split('id="thanh-ben"')[1].split('<div class="chinh">')[0]
    assert 'href="/nhap-tep/"' in ben and 'href="/cap-quyen/"' not in ben
    # Tạo bảng: nút đã ẩn nhưng đường dẫn còn sống (ADR-040) — bảng thường tạo
    # xong quản lý tiếp bên KN ERP, màn Cột của nó ở KN CRM trả 404
    kq = client.get("/bang/moi/")
    assert kq.status_code == 200 and KHUNG_CRM in kq.content.decode()
    kq = client.post("/bang/moi/", {"name": "Bảng Leader", "code": "bang_leader", "description": ""})
    assert kq.status_code == 302 and kq["Location"] == "/bang/bang_leader/cot/"
    assert TableDef.objects.get(code="bang_leader").department == departments["sale"]
    assert client.get("/bang/bang_leader/cot/").status_code == 404
    assert client.get("/danh-sach-bang/")["Location"] == "/thu-muc/"
    # Nhập tệp: chỉ còn bảng vận đơn (ADR-040) — bảng thường không được liệt kê,
    # gõ thẳng đường nhập cũng 404
    kq = client.get("/nhap-tep/")
    html = kq.content.decode()
    assert kq.status_code == 200 and KHUNG_CRM in html
    assert "don_sale" not in html and "bang_leader" not in html
    assert [b.code for b in kq.context["cac_bang"]] == []
    assert client.get("/bang/don_sale/nhap/").status_code == 404
    # Cấp quyền: Leader bị từ chối có nhật ký
    truoc = _tu_choi()
    assert client.get("/cap-quyen/").status_code == 403 and _tu_choi() == truoc + 1
    # Bảng dữ liệu vẫn không có ở KN CRM
    assert client.get("/bang/").status_code == 404
    assert client.get("/bang/don_sale/").status_code == 404

    # Manager: mục Cấp quyền chỉ liệt kê bảng vận đơn — bảng thường không hiện,
    # gõ thẳng đường cấp quyền 404 (quản lý tiếp bên KN ERP)
    client.force_login(nguoi_dung["manager_sale"])
    ben = client.get("/").content.decode().split('id="thanh-ben"')[1].split('<div class="chinh">')[0]
    assert 'href="/cap-quyen/"' in ben
    kq = client.get("/cap-quyen/")
    assert kq.status_code == 200 and 'href="/bang/don_sale/cot/"' not in kq.content.decode()
    assert client.post("/bang/don_sale/cap-quyen/", {}).status_code == 404
    # Leader bộ phận khác: bảng Sale không có trong danh sách nhập, gõ thẳng 404
    client.force_login(leader_mkt)
    kq = client.get("/nhap-tep/")
    assert kq.status_code == 200 and "Đơn hàng Sale" not in kq.content.decode()
    assert client.get("/bang/don_sale/nhap/").status_code == 404
    # Staff: 403 có nhật ký ở mục Nhập tệp và Tạo bảng
    client.force_login(nguoi_dung["staff_sale_1"])
    truoc = _tu_choi()
    assert client.get("/nhap-tep/").status_code == 403
    assert client.get("/bang/moi/").status_code == 403
    assert _tu_choi() == truoc + 2

    # ADR-045: Leader vẫn dùng CRM nhưng không mở các màn bảng ở ERP.
    client.force_login(ld)
    with ERP:
        assert client.get("/bang/moi/").status_code == 403
        client.force_login(nguoi_dung["manager_sale"])
        kq = client.get("/bang/moi/")
        html = kq.content.decode()
        assert kq.status_code == 200 and KHUNG_ERP in html and KHUNG_CRM not in html
        assert client.get("/nhap-tep/").status_code == 404
