"""Dữ liệu mẫu dùng chung cho mọi bài kiểm thử.

Dựng đủ chín vai trò của ma trận phân quyền: ba bộ phận nhân ba cấp bậc,
cộng một quản trị viên.
"""
import gc
import os
import threading
import traceback
import warnings

import pytest
from django.contrib.auth import get_user_model

from core.constants import Rank
from tests.live_server_requests import LIVE_SERVER_REQUESTS


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item, nextitem):
    """TL-71 — Bài đứng quá `faulthandler_timeout` (CI đặt cho hai bước e2e): ngoài ngăn xếp các luồng do
    faulthandler in, in thêm ngăn xếp các greenlet. Playwright đồng bộ chạy thân bài trong một greenlet, nên
    lúc treo faulthandler chỉ thấy luồng chính đứng trong vòng lặp asyncio của Playwright, không thấy bài đang
    chờ ở dòng nào. Không đặt `faulthandler_timeout` (chạy thường) thì không làm gì."""
    giay = float(item.config.getini("faulthandler_timeout") or 0)
    if giay <= 0:
        yield
        return
    # Chậm hơn faulthandler một giây cho hai bản in khỏi xen nhau
    canh = threading.Timer(giay + 1, _in_ngan_xep_greenlet, args=(item,))
    canh.daemon = True
    canh.start()
    try:
        yield
    finally:
        canh.cancel()


def _in_ngan_xep_greenlet(item):
    try:
        import greenlet
        from _pytest.faulthandler import fault_handler_stderr_fd_key
        fd = item.config.stash[fault_handler_stderr_fd_key]    # stderr thật; stderr thường đang bị pytest bắt
    except (ImportError, KeyError):
        return
    dong = [f"\n== TL-71: {item.nodeid} đứng quá faulthandler_timeout — ngăn xếp các greenlet ==\n"]
    for g in gc.get_objects():
        if isinstance(g, greenlet.greenlet) and g.gr_frame is not None:
            dong.append(f"-- {g!r}\n")
            dong.extend(traceback.format_stack(g.gr_frame))
    os.write(fd, "".join(dong).encode())


@pytest.fixture(autouse=True)
def _live_server_idle_before_flush(request):
    """TL-67 — Bài có máy chủ thử: trình duyệt đóng xong thì chờ máy chủ xử lý hết yêu cầu dở rồi mới
    để pytest-django dọn bảng, không thì TRUNCATE kẹt khoá với truy vấn đang chạy
    (`tests/live_server_requests.py`)."""
    if "live_server" not in request.fixturenames:
        yield
        return
    # CSDL dựng trước fixture này nên dọn sau nó; các fixture của bài (trang, trình duyệt) dựng sau
    # nên đóng trước — lúc chờ ở dưới, tab đã đóng và pytest chưa TRUNCATE
    request.getfixturevalue("transactional_db")
    yield
    if not LIVE_SERVER_REQUESTS.wait_idle():
        warnings.warn("Máy chủ thử còn yêu cầu dở sau 5 giây, dọn bảng có thể kẹt khoá (TL-67)", stacklevel=1)


@pytest.fixture
def User():
    return get_user_model()


@pytest.fixture
def departments(db):
    from org.models import Department

    return {
        "sale": Department.objects.create(name="Sale", code="sale"),
        "mkt": Department.objects.create(name="Marketing", code="marketing"),
        "vd": Department.objects.create(name="Vận đơn", code="van-don"),
        # Kế toán – Kiểm soát nội bộ (org/0004, ADR-038): xem và sửa mọi báo cáo
        # Migration org/0004 đã tạo sẵn Kế toán trong DB kiểm thử → lấy lại, không tạo trùng
        "kt": Department.objects.get_or_create(code="ke-toan", defaults={"name": "Kế toán"})[0],
    }


@pytest.fixture
def make_user(db, User):
    """Tạo một tài khoản kèm hồ sơ nhân sự."""
    from org.models import UserProfile

    def _tao(username, rank=Rank.STAFF, department=None, team=None,
             password="matkhau-kiem-thu-1", must_change_password=False):
        user = User.objects.create_user(
            username=username, email=f"{username}@kimngan.vn", password=password,
        )
        UserProfile.objects.create(
            user=user, full_name=username.replace("_", " ").title(), rank=rank,
            department=department, team=team,
            must_change_password=must_change_password,
        )
        return user

    return _tao


@pytest.fixture
def teams(db, departments, make_user):
    """Hai team trong bộ phận Sale, mỗi team một Leader."""
    from org.models import Team

    leader1 = make_user("leader_sale_1", Rank.LEADER, departments["sale"])
    leader2 = make_user("leader_sale_2", Rank.LEADER, departments["sale"])
    t1 = Team.objects.create(name="Sale 1", department=departments["sale"], leader=leader1)
    t2 = Team.objects.create(name="Sale 2", department=departments["sale"], leader=leader2)
    leader1.profile.team = t1
    leader1.profile.save(update_fields=["team"])
    leader2.profile.team = t2
    leader2.profile.save(update_fields=["team"])
    return {"sale1": t1, "sale2": t2, "leader1": leader1, "leader2": leader2}


@pytest.fixture
def nguoi_dung(db, departments, teams, make_user):
    """Chín vai trò cộng quản trị viên và một nhân viên Kế toán (ADR-038)."""
    return {
        "staff_sale_1": make_user("staff_sale_1", Rank.STAFF, departments["sale"], teams["sale1"]),
        "staff_sale_1b": make_user("staff_sale_1b", Rank.STAFF, departments["sale"], teams["sale1"]),
        "staff_sale_2": make_user("staff_sale_2", Rank.STAFF, departments["sale"], teams["sale2"]),
        "leader_sale_1": teams["leader1"],
        "leader_sale_2": teams["leader2"],
        "manager_sale": make_user("manager_sale", Rank.MANAGER, departments["sale"]),
        "staff_mkt": make_user("staff_mkt", Rank.STAFF, departments["mkt"]),
        "manager_mkt": make_user("manager_mkt", Rank.MANAGER, departments["mkt"]),
        "staff_vd": make_user("staff_vd", Rank.STAFF, departments["vd"]),
        "staff_kt": make_user("staff_kt", Rank.STAFF, departments["kt"]),
        "admin": make_user("quan_tri", Rank.ADMIN),
    }


@pytest.fixture
def probes(db, departments, teams, nguoi_dung):
    """Mỗi người một bản ghi, để kiểm ai thấy được của ai."""
    from core.tests.models import ScopeProbe

    def _tao(ten, nguoi, bo_phan, team=None):
        return ScopeProbe.objects.create(
            title=ten, created_by=nguoi, department=bo_phan, team=team,
        )

    return {
        "cua_staff_1": _tao("Của staff sale 1", nguoi_dung["staff_sale_1"],
                            departments["sale"], teams["sale1"]),
        "cua_staff_1b": _tao("Của staff sale 1b", nguoi_dung["staff_sale_1b"],
                             departments["sale"], teams["sale1"]),
        "cua_staff_2": _tao("Của staff sale 2", nguoi_dung["staff_sale_2"],
                            departments["sale"], teams["sale2"]),
        "cua_mkt": _tao("Của marketing", nguoi_dung["staff_mkt"], departments["mkt"]),
        "cua_vd": _tao("Của vận đơn", nguoi_dung["staff_vd"], departments["vd"]),
    }
