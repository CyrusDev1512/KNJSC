"""Thư mục chứa bảng — `docs/04` mục 11, ADR-010 (Giai đoạn C).

Thư mục phẳng, thuộc bộ phận, chỉ để sắp xếp thanh bên Bảng tính. Mỗi bài
phân quyền kiểm cả hai chiều.
"""
import pytest

from core.constants import AuditAction
from core.exceptions import BusinessError
from core.models import AuditLog
from forms_builder.models import Folder, TableDef
from forms_builder.services import folder_service

pytestmark = pytest.mark.django_db


@pytest.fixture
def cac_bang(departments, nguoi_dung):
    return {
        "sale": TableDef.objects.create(
            name="Đơn hàng Sale", code="don_sale",
            department=departments["sale"], created_by=nguoi_dung["manager_sale"]),
        "sale2": TableDef.objects.create(
            name="Khách Sale", code="khach_sale",
            department=departments["sale"], created_by=nguoi_dung["manager_sale"]),
        "mkt": TableDef.objects.create(
            name="Báo cáo Marketing", code="bc_mkt",
            department=departments["mkt"], created_by=nguoi_dung["manager_mkt"]),
    }


def _so(action):
    return AuditLog.objects.filter(action=action).count()


def test_manager_tao_doi_ten_xoa_thu_muc_va_chuyen_bang(client, cac_bang, departments, nguoi_dung):
    """AC-11.17 — Manager của bộ phận tạo, đổi tên, xếp bảng vào, rồi xoá thư mục: bảng về không thư mục, thư mục xoá mềm, mỗi bước một dòng nhật ký; trùng tên bị từ chối"""
    ql = nguoi_dung["manager_sale"]
    client.force_login(ql)
    truoc = _so(AuditAction.CREATE), _so(AuditAction.UPDATE), _so(AuditAction.DELETE)

    kq = client.post("/bang-tinh/thu-muc/moi/", {"name": " Sale 2026 ", "ve": "don_sale"})
    assert kq.status_code == 302 and kq["Location"] == "/bang-tinh/don_sale/"
    thu_muc = Folder.objects.get(department=departments["sale"], name="Sale 2026")
    assert thu_muc.created_by == ql
    assert _so(AuditAction.CREATE) == truoc[0] + 1

    # Thanh bên: có thư mục (trống) và mục không thư mục chứa hai bảng
    kq = client.get("/bang-tinh/don_sale/")
    cay = {(t.name if t else None): [b.code for b in bs] for t, bs in kq.context["cay"]}
    assert cay["Sale 2026"] == [] and set(cay[None]) == {"don_sale", "khach_sale"}
    html = kq.content.decode()
    assert "Sale 2026" in html and "Thư mục mới" in html and 'id="bt-form-thu-muc"' in html

    # Trùng tên → báo lỗi, không tạo thêm
    kq = client.post("/bang-tinh/thu-muc/moi/", {"name": "Sale 2026", "ve": "don_sale"}, follow=True)
    assert "đã có thư mục" in kq.content.decode()
    assert Folder.objects.filter(department=departments["sale"]).count() == 1
    # Tên trống → báo lỗi
    client.post("/bang-tinh/thu-muc/moi/", {"name": "  ", "ve": "don_sale"})
    assert Folder.objects.filter(department=departments["sale"]).count() == 1

    # Xếp bảng vào thư mục
    kq = client.post("/bang-tinh/don_sale/chuyen-thu-muc/", {"folder": thu_muc.pk})
    assert kq.status_code == 302
    cac_bang["sale"].refresh_from_db()
    assert cac_bang["sale"].folder == thu_muc
    cay = {(t.name if t else None): [b.code for b in bs] for t, bs in client.get("/bang-tinh/don_sale/").context["cay"]}
    assert cay["Sale 2026"] == ["don_sale"] and cay[None] == ["khach_sale"]
    # Bỏ ra ngoài rồi xếp lại
    client.post("/bang-tinh/don_sale/chuyen-thu-muc/", {"folder": ""})
    cac_bang["sale"].refresh_from_db()
    assert cac_bang["sale"].folder is None
    client.post("/bang-tinh/don_sale/chuyen-thu-muc/", {"folder": thu_muc.pk})

    # Đổi tên
    kq = client.post(f"/bang-tinh/thu-muc/{thu_muc.pk}/sua/", {"name": "Sale năm nay", "ve": "don_sale"})
    assert kq.status_code == 302
    thu_muc.refresh_from_db()
    assert thu_muc.name == "Sale năm nay"

    # Xoá: xoá mềm, bảng về không thư mục
    kq = client.post(f"/bang-tinh/thu-muc/{thu_muc.pk}/xoa/", {"ve": "don_sale"})
    assert kq.status_code == 302
    cac_bang["sale"].refresh_from_db()
    assert cac_bang["sale"].folder is None
    assert not Folder.objects.filter(pk=thu_muc.pk).exists()
    assert Folder.all_objects.get(pk=thu_muc.pk).is_deleted
    assert _so(AuditAction.DELETE) == truoc[2] + 1
    assert _so(AuditAction.UPDATE) >= truoc[1] + 4          # chuyển ×3, đổi tên ×1
    # Tên cũ dùng lại được sau khi xoá
    folder_service.create_folder(name="Sale 2026", department=departments["sale"], actor=ql)

    # Thư mục khác bộ phận không nhận bảng
    tm_mkt = folder_service.create_folder(name="MKT", department=departments["mkt"], actor=nguoi_dung["manager_mkt"])
    with pytest.raises(BusinessError):
        folder_service.move_table(cac_bang["sale"], tm_mkt, actor=ql)


def test_thu_muc_theo_bo_phan_va_cap_bac(client, cac_bang, departments, nguoi_dung):
    """AC-11.17 — Staff và Leader bị 403 có nhật ký ở mọi thao tác thư mục; Manager bộ phận khác không thấy thư mục (404) và không chuyển được bảng của bộ phận khác; thanh bên của Sale không hiện thư mục Marketing"""
    tm_sale = folder_service.create_folder(name="Sale 2026", department=departments["sale"], actor=nguoi_dung["manager_sale"])
    tm_mkt = folder_service.create_folder(name="MKT 2026", department=departments["mkt"], actor=nguoi_dung["manager_mkt"])

    for ma in ("staff_sale_1", "leader_sale_1"):
        client.force_login(nguoi_dung[ma])
        truoc = _so(AuditAction.DENIED)
        assert client.post("/bang-tinh/thu-muc/moi/", {"name": "Lén", "ve": "don_sale"}).status_code == 403
        assert client.post(f"/bang-tinh/thu-muc/{tm_sale.pk}/sua/", {"name": "Lén", "ve": "don_sale"}).status_code == 403
        assert client.post(f"/bang-tinh/thu-muc/{tm_sale.pk}/xoa/", {"ve": "don_sale"}).status_code == 403
        assert client.post("/bang-tinh/don_sale/chuyen-thu-muc/", {"folder": tm_sale.pk}).status_code == 403
        assert _so(AuditAction.DENIED) == truoc + 4, ma
        # vẫn thấy cây, nhưng không có nút tạo thư mục
        kq = client.get("/bang-tinh/don_sale/")
        assert kq.status_code == 200 and kq.context["duoc_quan_ly_thu_muc"] is False
        html = kq.content.decode()
        assert "Sale 2026" in html and "MKT 2026" not in html and 'id="bt-form-thu-muc"' not in html
    tm_sale.refresh_from_db()
    assert tm_sale.name == "Sale 2026" and not tm_sale.is_deleted
    cac_bang["sale"].refresh_from_db()
    assert cac_bang["sale"].folder is None

    # Manager Marketing: thư mục Sale ngoài phạm vi → 404; bảng Sale ngoài phạm vi → 404
    client.force_login(nguoi_dung["manager_mkt"])
    assert client.post(f"/bang-tinh/thu-muc/{tm_sale.pk}/sua/", {"name": "x", "ve": "bc_mkt"}).status_code == 404
    assert client.post(f"/bang-tinh/thu-muc/{tm_sale.pk}/xoa/", {"ve": "bc_mkt"}).status_code == 404
    assert client.post("/bang-tinh/don_sale/chuyen-thu-muc/", {"folder": tm_mkt.pk}).status_code == 404
    # nhưng làm được với thư mục và bảng của mình
    assert client.post("/bang-tinh/bc_mkt/chuyen-thu-muc/", {"folder": tm_mkt.pk}).status_code == 302
    cac_bang["mkt"].refresh_from_db()
    assert cac_bang["mkt"].folder == tm_mkt
    # thư mục Sale không có trong cây của Marketing
    cay = {(t.name if t else None) for t, _ in client.get("/bang-tinh/bc_mkt/").context["cay"]}
    assert "MKT 2026" in cay and "Sale 2026" not in cay

    # Admin làm được với mọi bộ phận
    client.force_login(nguoi_dung["admin"])
    assert client.post(f"/bang-tinh/thu-muc/{tm_sale.pk}/sua/", {"name": "Sale (admin)", "ve": "don_sale"}).status_code == 302
    tm_sale.refresh_from_db()
    assert tm_sale.name == "Sale (admin)"

    # Chưa đăng nhập → chuyển đăng nhập
    client.logout()
    kq = client.post("/bang-tinh/thu-muc/moi/", {"name": "x", "ve": "don_sale"})
    assert kq.status_code == 302 and "/dang-nhap/" in kq["Location"]
