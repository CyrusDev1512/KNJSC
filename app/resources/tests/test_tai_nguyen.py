"""Tài nguyên dùng chung — FR-13.1 tới FR-13.4, ADR-015.

Danh mục là của toàn công ty (Q64): mọi cấp bậc xem được cả danh sách, nên
chiều "bị từ chối" là Staff và Leader thêm, sửa, gỡ, thêm mục — mỗi lần một
dòng nhật ký từ chối. Mỗi bài kiểm cả hai chiều.
"""
import pytest

from core.constants import AuditAction
from core.exceptions import BusinessError, OutOfScopeError
from core.models import AuditLog
from resources.constants import DEFAULT_CATEGORIES, ResourceStatus
from resources.models import Resource, ResourceCategory
from resources.services import resource_service

pytestmark = pytest.mark.django_db


def _so(action):
    return AuditLog.objects.filter(action=action).count()


@pytest.fixture
def cac_muc(nguoi_dung):
    resource_service.ensure_default_categories(actor=nguoi_dung["admin"])
    return {m.name: m for m in ResourceCategory.objects.all()}


@pytest.fixture
def cac_tai_nguyen(cac_muc, nguoi_dung, departments):
    n = nguoi_dung
    tao = resource_service.create_resource
    return {
        "bm": tao(category=cac_muc["BM"], name="BM Kim Ngân 01", status=ResourceStatus.DANG_DUNG,
                  holder=n["staff_mkt"], department=departments["mkt"], actor=n["manager_mkt"]),
        "via": tao(category=cac_muc["Via"], name="Via US 2019", status=ResourceStatus.TRONG,
                   actor=n["manager_mkt"]),
        "page": tao(category=cac_muc["Page"], name="Page KN Beauty CA", status=ResourceStatus.KHOA,
                    holder=n["staff_sale_1"], link="https://facebook.com/knbeauty", actor=n["admin"]),
    }


# ══ AC-16.1 · Mục và danh sách chung ═══════════════════════════════

def test_muc_va_danh_sach_chung(client, cac_tai_nguyen, cac_muc, nguoi_dung):
    """AC-16.1 — Tài nguyên chia theo mục BM, Via, Page…; mọi cấp bậc, mọi bộ phận xem được cả danh sách với trạng thái là chip; lọc theo mục, trạng thái, người giữ và tìm theo tên; mục không có trả 404; danh sách phân trang 25 dòng; Manager trở lên thêm mục, Staff bị từ chối có nhật ký, trùng tên bị chặn"""
    n = nguoi_dung
    assert set(cac_muc) == set(DEFAULT_CATEGORIES)

    for vai in ("staff_sale_1", "leader_sale_1", "manager_sale", "staff_vd", "admin"):
        client.force_login(n[vai])
        kq = client.get("/tai-nguyen/")
        assert kq.status_code == 200, vai
        assert kq.context["page_obj"].paginator.count == 3
    html = kq.content.decode()
    assert "BM Kim Ngân 01" in html and "Via US 2019" in html and "Page KN Beauty CA" in html
    assert 'class="chip chip-nhan">Đang dùng' in html and 'class="chip chip-cho">Khoá' in html
    assert "<button" not in html.split("<tbody>")[1].split("</tbody>")[0].replace(
        '<button class="nut nut-nho nut-nguy" type="submit">Gỡ</button>', "")   # trạng thái không phải nút

    # Lọc và tìm
    client.force_login(n["staff_vd"])
    ten = lambda kq: [tn.name for tn, _ in kq.context["cac_dong"]]     # noqa: E731
    assert ten(client.get("/tai-nguyen/", {"muc": cac_muc["BM"].pk})) == ["BM Kim Ngân 01"]
    assert ten(client.get("/tai-nguyen/", {"trang_thai": "khoa"})) == ["Page KN Beauty CA"]
    assert ten(client.get("/tai-nguyen/", {"nguoi": n["staff_mkt"].pk})) == ["BM Kim Ngân 01"]
    assert ten(client.get("/tai-nguyen/", {"tim": "us 20"})) == ["Via US 2019"]
    assert ten(client.get("/tai-nguyen/", {"tim": "kn", "trang_thai": "trong"})) == []
    assert client.get("/tai-nguyen/", {"muc": 999999}).status_code == 404
    assert "&trang_thai=khoa" in client.get("/tai-nguyen/", {"trang_thai": "khoa"}).context["qs_loc"]

    # Phân trang 25
    for i in range(24):
        resource_service.create_resource(category=cac_muc["SIM"], name=f"SIM {i:02d}", actor=n["admin"])
    assert len(client.get("/tai-nguyen/").context["trang"]) == 25
    assert len(client.get("/tai-nguyen/", {"trang": 2}).context["trang"]) == 2
    assert next(m for m in client.get("/tai-nguyen/").context["cac_muc"] if m.name == "SIM").so_tai_nguyen == 24

    # Thêm mục: Manager được, Staff bị từ chối có nhật ký, trùng tên bị chặn
    client.force_login(n["manager_sale"])
    truoc = _so(AuditAction.CREATE)
    assert client.post("/tai-nguyen/muc-moi/", {"name": "Tài khoản TikTok"}).status_code == 302
    assert ResourceCategory.objects.filter(name="Tài khoản TikTok").exists()
    assert _so(AuditAction.CREATE) == truoc + 1
    client.post("/tai-nguyen/muc-moi/", {"name": "tài khoản tiktok"})
    assert ResourceCategory.objects.filter(name__iexact="tài khoản tiktok").count() == 1
    with pytest.raises(BusinessError):
        resource_service.create_category(name="  ", actor=n["manager_sale"])
    client.force_login(n["staff_sale_1"])
    tu_choi = _so(AuditAction.DENIED)
    assert client.post("/tai-nguyen/muc-moi/", {"name": "Lậu"}).status_code == 403
    assert _so(AuditAction.DENIED) == tu_choi + 1
    assert not ResourceCategory.objects.filter(name="Lậu").exists()
    assert client.get("/tai-nguyen/muc-moi/").status_code == 405
    client.logout()
    assert "/dang-nhap/" in client.get("/tai-nguyen/")["Location"]


# ══ AC-16.2 · Thêm, sửa, gỡ ════════════════════════════════════════

def test_them_sua_go_tai_nguyen(client, cac_tai_nguyen, cac_muc, nguoi_dung, departments):
    """AC-16.2 — Manager trở lên thêm, sửa, gỡ tài nguyên; sửa ghi nhật ký từng trường đổi nhưng không chép ghi chú; gỡ là xoá mềm; Staff và Leader bị từ chối có nhật ký và không thấy nút; tài nguyên đã gỡ trả 404"""
    n = nguoi_dung
    via = cac_tai_nguyen["via"]

    # Staff, Leader: từ chối ở cả ba đường, có nhật ký, không thấy nút
    for vai in ("staff_mkt", "leader_sale_1"):
        client.force_login(n[vai])
        tu_choi = _so(AuditAction.DENIED)
        assert client.get("/tai-nguyen/moi/").status_code == 403
        assert client.get(f"/tai-nguyen/{via.pk}/sua/").status_code == 403
        assert client.post(f"/tai-nguyen/{via.pk}/go/").status_code == 403
        assert _so(AuditAction.DENIED) == tu_choi + 3, vai
        html = client.get("/tai-nguyen/").content.decode()
        assert f"/tai-nguyen/{via.pk}/sua/" not in html and "Thêm tài nguyên" not in html
    assert Resource.objects.filter(pk=via.pk).exists()
    with pytest.raises(OutOfScopeError):
        resource_service.update_resource(via, actor=n["staff_mkt"], name="Đổi trộm")
    with pytest.raises(OutOfScopeError):
        resource_service.delete_resource(via, actor=n["leader_sale_1"])

    # Manager thêm qua màn hình
    client.force_login(n["manager_mkt"])
    assert client.get("/tai-nguyen/moi/").status_code == 200
    truoc = _so(AuditAction.CREATE)
    kq = client.post("/tai-nguyen/moi/", {
        "category": cac_muc["SIM"].pk, "name": "SIM Viettel 0987", "status": "dang_dung",
        "holder": n["staff_mkt"].pk, "department": departments["mkt"].pk,
        "link": "", "note": "Nhận OTP quảng cáo, để ở bàn Marketing",
    })
    assert kq.status_code == 200 and not Resource.objects.filter(name="SIM Viettel 0987").exists()   # "OTP" trong ghi chú
    kq = client.post("/tai-nguyen/moi/", {
        "category": cac_muc["SIM"].pk, "name": "SIM Viettel 0987", "status": "dang_dung",
        "holder": n["staff_mkt"].pk, "department": departments["mkt"].pk,
        "link": "", "note": "Để ở bàn Marketing",
    })
    assert kq.status_code == 302
    sim = Resource.objects.get(name="SIM Viettel 0987")
    assert (sim.category, sim.status, sim.holder, sim.department, sim.created_by) == (
        cac_muc["SIM"], ResourceStatus.DANG_DUNG, n["staff_mkt"], departments["mkt"], n["manager_mkt"])
    assert _so(AuditAction.CREATE) == truoc + 1

    # Sửa: nhật ký ghi trường đổi, không chép ghi chú
    kq = client.get(f"/tai-nguyen/{sim.pk}/sua/")
    assert kq.status_code == 200 and 'value="SIM Viettel 0987"' in kq.content.decode()
    truoc = _so(AuditAction.UPDATE)
    kq = client.post(f"/tai-nguyen/{sim.pk}/sua/", {
        "category": cac_muc["SIM"].pk, "name": "SIM Viettel 0987", "status": "hong",
        "holder": "", "department": departments["mkt"].pk, "link": "", "note": "Đã báo nhà mạng",
    })
    assert kq.status_code == 302
    sim.refresh_from_db()
    assert (sim.status, sim.holder, sim.note) == (ResourceStatus.HONG, None, "Đã báo nhà mạng")
    assert _so(AuditAction.UPDATE) == truoc + 1
    chi_tiet = AuditLog.objects.filter(action=AuditAction.UPDATE).first().detail
    assert "Trạng thái: Đang dùng → Hỏng" in chi_tiet and "Người giữ: Staff Mkt → —" in chi_tiet
    assert "Ghi chú" in chi_tiet and "nhà mạng" not in chi_tiet and "Marketing" not in chi_tiet
    assert resource_service.update_resource(sim, actor=n["manager_mkt"], status="hong") is sim
    assert _so(AuditAction.UPDATE) == truoc + 1                            # không đổi gì: không thêm dòng
    with pytest.raises(BusinessError):
        resource_service.update_resource(sim, actor=n["manager_mkt"], name="")
    with pytest.raises(BusinessError):
        resource_service.update_resource(sim, actor=n["manager_mkt"], status="mat")

    # Gỡ: xoá mềm, có nhật ký; đã gỡ thì 404
    tx = _so(AuditAction.DELETE)
    assert client.post(f"/tai-nguyen/{sim.pk}/go/").status_code == 302
    assert not Resource.objects.filter(pk=sim.pk).exists()
    assert Resource.all_objects.get(pk=sim.pk).deleted_by == n["manager_mkt"]
    assert _so(AuditAction.DELETE) == tx + 1
    assert client.get(f"/tai-nguyen/{sim.pk}/sua/").status_code == 404
    assert client.post(f"/tai-nguyen/{sim.pk}/go/").status_code == 404
    assert client.get(f"/tai-nguyen/{via.pk}/go/").status_code == 405
    # Admin không thuộc bộ phận nào vẫn sửa được (danh mục chung)
    client.force_login(n["admin"])
    assert client.post(f"/tai-nguyen/{via.pk}/sua/", {
        "category": cac_muc["Via"].pk, "name": "Via US 2019", "status": "khoa",
        "holder": "", "department": "", "link": "", "note": "",
    }).status_code == 302
    via.refresh_from_db()
    assert via.status == ResourceStatus.KHOA


# ══ AC-16.3 · Không lưu mật khẩu ═══════════════════════════════════

def test_ghi_chu_khong_chua_mat_khau(cac_muc, nguoi_dung):
    """AC-16.3 — Ghi chú chứa mật khẩu, OTP, 2FA, token hay mã bí mật bị từ chối ở cả thêm lẫn sửa; không có cột mật khẩu trong bảng; nhật ký không chứa ghi chú"""
    n = nguoi_dung
    for xau in ("Mật khẩu: Abc123", "password abc", "pass: 1234", "mã OTP gửi về SIM này", "2FA qua app", "token dán ở đây"):
        with pytest.raises(BusinessError):
            resource_service.create_resource(category=cac_muc["BM"], name="BM 02", note=xau, actor=n["admin"])
    assert not Resource.objects.filter(name="BM 02").exists()
    bm = resource_service.create_resource(category=cac_muc["BM"], name="BM 02", note="Đang chạy 3 tài khoản", actor=n["admin"])
    with pytest.raises(BusinessError):
        resource_service.update_resource(bm, actor=n["admin"], note="pwd: 123456")
    bm.refresh_from_db()
    assert bm.note == "Đang chạy 3 tài khoản"
    assert not any("password" in f.name or "secret" in f.name for f in Resource._meta.get_fields())
    assert all("Đang chạy 3 tài khoản" not in a.detail for a in AuditLog.objects.all())


# ══ Ngân sách truy vấn — AC-10.2 ═══════════════════════════════════

def test_danh_sach_tai_nguyen_khong_qua_muoi_lenh_truy_van(client, cac_tai_nguyen, nguoi_dung, django_assert_max_num_queries):
    """AC-10.2 — Danh sách tài nguyên có dữ liệu chạy không quá 10 lệnh truy vấn"""
    client.force_login(nguoi_dung["manager_sale"])
    client.get("/tai-nguyen/")
    with django_assert_max_num_queries(10):
        assert client.get("/tai-nguyen/").status_code == 200
