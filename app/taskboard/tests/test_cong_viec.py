"""Công việc — FR-11.1 tới FR-11.5, ADR-015.

Mỗi bài phân quyền kiểm **cả hai chiều**: được phép và bị từ chối.
"""
from datetime import date, timedelta

import pytest

from core.constants import AuditAction
from core.exceptions import BusinessError, OutOfScopeError
from core.models import AuditLog
from taskboard.constants import TaskPriority, TaskStatus
from taskboard.models import Task
from taskboard.services import task_service

pytestmark = pytest.mark.django_db


def _so(action):
    return AuditLog.objects.filter(action=action).count()


def _viec(actor, title, **k):
    return task_service.create_task(title=title, actor=actor, **k)


@pytest.fixture
def cac_viec(nguoi_dung):
    n = nguoi_dung
    return {
        "a": _viec(n["manager_sale"], "Gọi lại khách Canada", assignee=n["staff_sale_1"],
                   due_date=date.today() - timedelta(days=1)),
        "b": _viec(n["staff_sale_2"], "Chốt đơn tồn team 2"),
        "c": _viec(n["staff_mkt"], "Chạy quảng cáo tháng 10"),
    }


# ══ AC-14.1 · Giao việc theo phạm vi ═══════════════════════════════

def test_giao_viec_theo_pham_vi(client, nguoi_dung):
    """AC-14.1 — Staff tự giao cho mình, giao người khác bị từ chối; Leader giao trong team, người team khác bị từ chối; Manager giao cả bộ phận, không giao sang bộ phận khác; Admin giao được mọi người"""
    n = nguoi_dung
    client.force_login(n["staff_sale_1"])
    assert client.get("/cong-viec/moi/").status_code == 200
    truoc = _so(AuditAction.CREATE)
    kq = client.post("/cong-viec/moi/", {"title": "Tự nhận", "priority": "vua"})
    assert kq.status_code == 302
    viec = Task.objects.get(title="Tự nhận")
    assert viec.assignee == n["staff_sale_1"] and viec.created_by == n["staff_sale_1"]
    assert viec.department_id == n["staff_sale_1"].profile.department_id
    assert _so(AuditAction.CREATE) == truoc + 1

    # Staff giao cho người khác: người đó không nằm trong danh sách chọn → form từ chối
    kq = client.post("/cong-viec/moi/", {"title": "Đùn việc", "priority": "vua", "assignee": n["staff_sale_1b"].pk})
    assert kq.status_code == 200 and not Task.objects.filter(title="Đùn việc").exists()
    with pytest.raises(BusinessError):
        _viec(n["staff_sale_1"], "Đùn việc", assignee=n["staff_sale_1b"])

    # Leader giao trong team mình, không giao sang team khác
    v = _viec(n["leader_sale_1"], "Cho team 1", assignee=n["staff_sale_1"])
    assert v.assignee == n["staff_sale_1"]
    with pytest.raises(BusinessError):
        _viec(n["leader_sale_1"], "Cho team 2", assignee=n["staff_sale_2"])

    # Manager giao cả bộ phận, không giao sang bộ phận khác
    assert _viec(n["manager_sale"], "Cho team 2", assignee=n["staff_sale_2"]).assignee == n["staff_sale_2"]
    with pytest.raises(BusinessError):
        _viec(n["manager_mkt"], "Lấn sân", assignee=n["staff_sale_1"])

    # Admin không thuộc bộ phận nào: việc lấy bộ phận của người làm
    v = _viec(n["admin"], "Từ quản trị", assignee=n["staff_mkt"])
    assert v.department_id == n["staff_mkt"].profile.department_id
    with pytest.raises(BusinessError):
        _viec(n["admin"], "Không ai làm")            # admin tự nhận mà không có bộ phận


# ══ AC-14.2 · Phạm vi xem ═══════════════════════════════════════════

def test_pham_vi_xem_viec(client, cac_viec, nguoi_dung):
    """AC-14.2 — Staff thấy việc mình nhận hoặc tạo; Leader thấy việc của team; Manager cả bộ phận; Admin tất cả; gọi thẳng việc ngoài phạm vi trả 404"""
    n, v = nguoi_dung, cac_viec

    def thay(ai, tab="pham_vi"):
        client.force_login(n[ai])
        html = client.get(f"/cong-viec/?tab={tab}").content.decode()
        return {k for k, t in v.items() if t.title in html}

    assert thay("staff_sale_1") == {"a"}
    assert thay("staff_sale_1b") == set()
    assert thay("leader_sale_1") == {"a"}                 # người làm thuộc team 1
    assert thay("leader_sale_2") == {"b"}
    assert thay("manager_sale") == {"a", "b"}
    assert thay("manager_mkt") == {"c"}
    assert thay("admin") == {"a", "b", "c"}
    assert thay("manager_sale", tab="cua_toi") == {"a"}    # tab Của tôi: mình nhận hoặc tạo

    client.force_login(n["staff_sale_1"])
    assert client.get(f"/cong-viec/{v['a'].pk}/").status_code == 200
    assert client.get(f"/cong-viec/{v['b'].pk}/").status_code == 404
    assert client.post(f"/cong-viec/{v['b'].pk}/trang-thai/", {"trang_thai": "dang_lam"}).status_code == 404


# ══ AC-14.3 · Đổi trạng thái qua HTMX ═══════════════════════════════

def test_doi_trang_thai_htmx(client, cac_viec, nguoi_dung):
    """AC-14.3 — Người làm đổi trạng thái qua HTMX nhận về đúng một dòng bảng; chuyển sai bước trả 400; người cùng team không phải người làm bị 404 còn Leader đổi được; mỗi lần một dòng nhật ký"""
    n, a = nguoi_dung, cac_viec["a"]
    duong = f"/cong-viec/{a.pk}/trang-thai/"
    client.force_login(n["staff_sale_1"])
    truoc = _so(AuditAction.UPDATE)
    kq = client.post(duong, {"trang_thai": "dang_lam"}, HTTP_HX_REQUEST="true")
    assert kq.status_code == 200
    html = kq.content.decode()
    assert html.strip().startswith(f'<tr id="viec-{a.pk}"') and "Đang làm" in html and "<table" not in html
    a.refresh_from_db()
    assert a.status == TaskStatus.DANG_LAM and _so(AuditAction.UPDATE) == truoc + 1

    # Chuyển sai bước: Đang làm → Đang làm không có trong bảng
    kq = client.post(duong, {"trang_thai": "dang_lam"}, HTTP_HX_REQUEST="true")
    assert kq.status_code == 400 and "Không chuyển được" in kq.content.decode()
    assert _so(AuditAction.UPDATE) == truoc + 1

    # Xong thì ghi giờ xong; mở lại thì xoá giờ xong
    client.post(duong, {"trang_thai": "xong"}, HTTP_HX_REQUEST="true")
    a.refresh_from_db()
    assert a.status == TaskStatus.XONG and a.done_at is not None
    client.post(duong, {"trang_thai": "dang_lam"}, HTTP_HX_REQUEST="true")
    a.refresh_from_db()
    assert a.done_at is None

    # Cùng team nhưng không phải người làm hay người tạo → không thấy việc
    client.force_login(n["staff_sale_1b"])
    assert client.post(duong, {"trang_thai": "xong"}, HTTP_HX_REQUEST="true").status_code == 404
    # Leader của team đổi được
    client.force_login(n["leader_sale_1"])
    assert client.post(duong, {"trang_thai": "xong"}, HTTP_HX_REQUEST="true").status_code == 200
    # Không HTMX thì quay về trang chi tiết
    client.force_login(n["manager_sale"])
    kq = client.post(duong, {"trang_thai": "dang_lam", "ve": f"/cong-viec/{a.pk}/"})
    assert kq.status_code == 302 and kq["Location"] == f"/cong-viec/{a.pk}/"


# ══ AC-14.4 · Tab, lọc, phân trang ══════════════════════════════════

def test_tab_loc_va_phan_trang(client, nguoi_dung):
    """AC-14.4 — Tab Của tôi và Trong phạm vi, lọc theo trạng thái, người làm, ưu tiên; danh sách phân trang 25 dòng"""
    n = nguoi_dung
    for i in range(30):
        _viec(n["staff_sale_1"], f"Việc số {i:02d}", priority=TaskPriority.CAO if i < 3 else TaskPriority.VUA)
    xong = Task.objects.filter(title="Việc số 00").get()
    task_service.change_status(xong, TaskStatus.DANG_LAM, actor=n["staff_sale_1"])
    task_service.change_status(xong, TaskStatus.XONG, actor=n["staff_sale_1"])

    client.force_login(n["staff_sale_1"])
    html = client.get("/cong-viec/").content.decode()
    assert html.count('<tr id="viec-') == 25 and "phan-trang" in html
    html = client.get("/cong-viec/?trang=2").content.decode()
    assert html.count('<tr id="viec-') == 5
    html = client.get("/cong-viec/?trang_thai=xong").content.decode()
    assert html.count('<tr id="viec-') == 1 and "Việc số 00" in html
    html = client.get("/cong-viec/?uu_tien=cao").content.decode()
    assert html.count('<tr id="viec-') == 3
    html = client.get(f"/cong-viec/?nguoi={n['staff_sale_1'].pk}&trang_thai=moi").content.decode()
    assert html.count('<tr id="viec-') == 25
    # Manager xem tab Trong phạm vi thấy việc của Staff, tab Của tôi thì không
    client.force_login(n["manager_sale"])
    assert client.get("/cong-viec/?tab=pham_vi").content.decode().count('<tr id="viec-') == 25
    assert client.get("/cong-viec/?tab=cua_toi").content.decode().count('<tr id="viec-') == 0


# ══ AC-14.5 · Sửa và gỡ ═════════════════════════════════════════════

def test_sua_va_go_viec_theo_quyen(client, cac_viec, nguoi_dung):
    """AC-14.5 — Người tạo hoặc Leader trở lên sửa được việc (nhật ký ghi trường đổi); gỡ là xoá mềm bởi người tạo hoặc Manager; người làm không phải người tạo bị từ chối có nhật ký"""
    n, a = nguoi_dung, cac_viec["a"]
    # Người làm (không phải người tạo) không sửa, không gỡ được
    client.force_login(n["staff_sale_1"])
    tu_choi = _so(AuditAction.DENIED)
    assert client.post(f"/cong-viec/{a.pk}/sua/", {"title": "Đổi tên", "priority": "cao"}).status_code == 403
    assert client.post(f"/cong-viec/{a.pk}/go/").status_code == 403
    assert _so(AuditAction.DENIED) == tu_choi + 2
    assert client.get(f"/cong-viec/{a.pk}/go/").status_code == 405

    # Người tạo sửa được, nhật ký ghi trường đổi
    client.force_login(n["manager_sale"])
    truoc = _so(AuditAction.UPDATE)
    kq = client.post(f"/cong-viec/{a.pk}/sua/", {
        "title": "Gọi lại khách Canada (gấp)", "priority": "cao", "assignee": n["staff_sale_2"].pk,
        "due_date": "2026-12-31",
    })
    assert kq.status_code == 302
    a.refresh_from_db()
    assert a.priority == TaskPriority.CAO and a.assignee == n["staff_sale_2"]
    chi_tiet = AuditLog.objects.filter(action=AuditAction.UPDATE).latest("created_at").detail
    assert "Ưu tiên: Vừa → Cao" in chi_tiet and "Người làm:" in chi_tiet
    assert _so(AuditAction.UPDATE) == truoc + 1

    # Gỡ: xoá mềm, có nhật ký; gỡ rồi thì 404
    xoa = _so(AuditAction.DELETE)
    assert client.post(f"/cong-viec/{a.pk}/go/").status_code == 302
    assert not Task.objects.filter(pk=a.pk).exists()
    assert Task.all_objects.get(pk=a.pk).deleted_by == n["manager_sale"]
    assert _so(AuditAction.DELETE) == xoa + 1
    assert client.post(f"/cong-viec/{a.pk}/go/").status_code == 404
    # Admin gỡ được việc của bộ phận khác
    client.force_login(n["admin"])
    assert client.post(f"/cong-viec/{cac_viec['c'].pk}/go/").status_code == 302


def test_man_hinh_cong_viec_khong_qua_muoi_lenh_truy_van(client, cac_viec, nguoi_dung, django_assert_max_num_queries):
    """AC-10.2 — Màn hình Công việc chạy không quá 10 lệnh truy vấn"""
    client.force_login(nguoi_dung["admin"])
    client.get("/cong-viec/?tab=pham_vi")
    with django_assert_max_num_queries(10):
        assert client.get("/cong-viec/?tab=pham_vi").status_code == 200


# ══ Dịch vụ tự kiểm quyền, sửa giữ người làm, `ve` an toàn — rà soát 07.09 ═

def test_dich_vu_tu_kiem_quyen_va_sua_giu_nguoi_lam(nguoi_dung):
    """AC-14.5 — Gọi thẳng tầng dịch vụ bằng người không có quyền vẫn bị từ chối, không trông vào view; sửa việc để trống người làm thì giữ nguyên người cũ; đổi người làm thì việc chuyển sang bộ phận của người đó"""
    n = nguoi_dung
    v = task_service.create_task(title="Việc A", assignee=n["staff_sale_1"], actor=n["manager_sale"])
    with pytest.raises(OutOfScopeError):
        task_service.update_task(v, {"title": "Đổi trộm"}, actor=n["staff_sale_1b"])      # ngoài phạm vi Staff
    with pytest.raises(OutOfScopeError):
        task_service.change_status(v, TaskStatus.DANG_LAM, actor=n["staff_mkt"])          # bộ phận khác
    with pytest.raises(OutOfScopeError):
        task_service.delete_task(v, actor=n["leader_sale_1"])                             # Leader không gỡ
    task_service.update_task(v, {"assignee": None, "title": "Việc A sửa"}, actor=n["manager_sale"])
    v.refresh_from_db()
    assert v.assignee == n["staff_sale_1"] and v.title == "Việc A sửa"
    v2 = task_service.create_task(title="Việc B", assignee=n["staff_mkt"], actor=n["admin"])
    task_service.update_task(v2, {"assignee": n["staff_sale_2"]}, actor=n["admin"])
    v2.refresh_from_db()
    assert v2.assignee == n["staff_sale_2"] and v2.department_id == n["staff_sale_2"].profile.department_id
    with pytest.raises(BusinessError):
        task_service.update_task(v2, {"description": "x" * 2001}, actor=n["admin"])


def test_ve_chi_quay_ve_trong_he_thong(client, nguoi_dung):
    """AC-14.3 — Tham số `ve` sau khi đổi trạng thái chỉ chuyển về đường dẫn trong hệ thống, đường ngoài bị thay bằng danh sách việc; sai bước qua HTMX trả 400 dạng chữ thường để trình duyệt hiện lý do"""
    n = nguoi_dung
    v = task_service.create_task(title="Việc V", actor=n["staff_sale_1"])
    client.force_login(n["staff_sale_1"])
    kq = client.post(f"/cong-viec/{v.pk}/trang-thai/", {"trang_thai": "dang_lam", "ve": "https://evil.example/"})
    assert kq.status_code == 302 and kq["Location"] == "/cong-viec/"
    kq = client.post(f"/cong-viec/{v.pk}/trang-thai/", {"trang_thai": "xong", "ve": "/cong-viec/?tab=pham_vi"})
    assert kq.status_code == 302 and kq["Location"] == "/cong-viec/?tab=pham_vi"
    kq = client.post(f"/cong-viec/{v.pk}/trang-thai/", {"trang_thai": "huy"}, HTTP_HX_REQUEST="true")
    assert kq.status_code == 400 and kq["Content-Type"].startswith("text/plain")
    assert "Không chuyển được" in kq.content.decode()
