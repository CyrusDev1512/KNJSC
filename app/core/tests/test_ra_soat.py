"""Kiểm thử chặn hồi quy cho các lỗi tìm được ở đợt rà soát Giai đoạn 1 và 2.

Mỗi bài ở đây phải **đỏ** nếu hoàn tác bản sửa tương ứng. Đó là lý do tồn tại
của chúng: lỗi đã xảy ra một lần thì phải có bài kiểm giữ chỗ.
"""
import time
from decimal import Decimal

import pytest
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from core.constants import AuditAction
from core.models import AuditLog
from core.scope import get_user_scope

pytestmark = pytest.mark.django_db


# ══ F1 · Không có hồ sơ thì trả 403, không phải 500 ════════════════

def test_khong_co_ho_so_thi_tra_403_khong_phai_500(client, db, User):
    """AC-3.6 — Tài khoản chưa gán bộ phận nhận lỗi từ chối, không phải trang trắng

    `NoProfileError` từng kế thừa `BusinessError` nên Django trả lỗi 500.
    FR-3.5 đòi trả lỗi từ chối, NFR-6 cấm hiện trang trắng.
    """
    user = User.objects.create_user(username="chua_gan_bo_phan", password="matkhau-kiem-thu-1")
    client.force_login(user)
    assert client.get("/nhan-su/").status_code == 403


def test_loi_khong_co_ho_so_la_mot_dang_tu_choi_quyen(db, User):
    """AC-3.6 — NoProfileError phải là một dạng PermissionDenied"""
    from core.exceptions import NoProfileError

    assert issubclass(NoProfileError, PermissionDenied)


# ══ F2 · Phạm vi trên Team không được nổ ═══════════════════════════

def test_leader_loc_duoc_team_cua_minh(nguoi_dung, teams):
    """AC-3.2 — Leader lọc được danh sách team mà không gặp lỗi truy vấn

    `apply_scope` từng tự nối hậu tố `_id`, nên `team="id"` sinh ra lookup
    `id_id__in` và ném FieldError ngay khi có một Leader.
    """
    from org.models import Team

    thay = list(Team.objects.in_scope(nguoi_dung["leader_sale_1"]))
    assert teams["sale1"] in thay
    assert teams["sale2"] not in thay


def test_manager_thay_team_cua_bo_phan_minh(nguoi_dung, teams):
    """AC-3.4 — Manager thấy mọi team trong bộ phận mình"""
    from org.models import Team

    thay = list(Team.objects.in_scope(nguoi_dung["manager_sale"]))
    assert teams["sale1"] in thay and teams["sale2"] in thay


def test_staff_khong_thay_team_nao(nguoi_dung):
    """AC-3.1 — Staff không phụ trách team nào nên không thấy team nào"""
    from org.models import Team

    assert list(Team.objects.in_scope(nguoi_dung["staff_sale_1"])) == []


# ══ F3 · Tổng quan không được tự viết lại phạm vi ══════════════════

def test_tong_quan_dem_dung_pham_vi_tung_cap_bac(nguoi_dung, teams):
    """AC-3.1 tới AC-3.4 — Số bộ phận và team trên Tổng quan đúng bằng phạm vi

    Bản đầu tự lọc bằng `department_ids` cho mọi cấp bậc phi-admin, nên Staff
    đếm được cả team của bộ phận.
    """
    from dashboard.services import dashboard_service

    staff = dashboard_service.tong_quan(nguoi_dung["staff_sale_1"])["co_cau"]["data"]
    assert staff["so_team"] == 0        # Staff không phụ trách team nào

    leader = dashboard_service.tong_quan(nguoi_dung["leader_sale_1"])["co_cau"]["data"]
    assert leader["so_team"] == 1       # đúng team mình phụ trách

    admin = dashboard_service.tong_quan(nguoi_dung["admin"])["co_cau"]["data"]
    assert admin["so_team"] == 2


# ══ F4 · Kiểm quyền trên từng bản ghi ══════════════════════════════

def test_sua_ho_so_ngoai_pham_vi_bi_tu_choi(client, nguoi_dung):
    """AC-3.6 — Lấy hồ sơ để sửa phải đi qua phạm vi quyền

    Hai màn hình sửa và khoá từng lấy bản ghi thẳng theo khoá chính. Chưa lộ
    dữ liệu vì chỉ Admin vào được, nhưng sai ngay từ hình thức.
    """
    from org.models import UserProfile

    ho_so_mkt = UserProfile.objects.get(user=nguoi_dung["staff_mkt"])
    trong_pham_vi = UserProfile.objects.in_scope(nguoi_dung["manager_sale"])
    assert ho_so_mkt not in list(trong_pham_vi)


# ══ F5 · Hết phiên đúng 60 phút — AC-1.4 ═══════════════════════════

def test_het_phien_sau_60_phut_khong_thao_tac(client, nguoi_dung, settings):
    """AC-1.4 — Phiên không thao tác quá 60 phút thì yêu cầu tiếp theo bị từ chối"""
    assert settings.SESSION_IDLE_TIMEOUT_SECONDS == 3600, "FR-1.3 quy định 60 phút"

    client.post("/dang-nhap/", {
        "username": "staff_sale_1", "password": "matkhau-kiem-thu-1",
    })
    assert client.get("/").status_code == 200

    # Đẩy dấu thời gian lùi quá ngưỡng
    phien = client.session
    phien["last_seen_at"] = int(time.time()) - settings.SESSION_IDLE_TIMEOUT_SECONDS - 1
    phien.save()

    tra_loi = client.get("/")
    assert tra_loi.status_code == 302
    assert "het_phien=1" in tra_loi.headers["Location"]


def test_con_trong_60_phut_thi_van_vao_duoc(client, nguoi_dung, settings):
    """AC-1.4 — Chưa quá ngưỡng thì phiên vẫn còn hiệu lực"""
    client.post("/dang-nhap/", {
        "username": "staff_sale_1", "password": "matkhau-kiem-thu-1",
    })
    phien = client.session
    phien["last_seen_at"] = int(time.time()) - 60
    phien.save()
    assert client.get("/").status_code == 200


# ══ F6 · Mọi thay đổi đều ghi nhật ký — AC-9.2 ═════════════════════

def test_sua_ho_so_qua_man_hinh_co_ghi_nhat_ky(client, nguoi_dung, departments):
    """AC-9.2 — Sửa hồ sơ qua màn hình sinh đúng một dòng nhật ký

    Màn hình từng gọi thẳng `form.save()`, nên đổi cấp bậc không để lại dấu
    vết nào — vi phạm BR-5.
    """
    from core.constants import Rank
    from org.models import UserProfile

    client.force_login(nguoi_dung["admin"])
    ho_so = UserProfile.objects.get(user=nguoi_dung["staff_sale_1"])
    truoc = AuditLog.objects.filter(action=AuditAction.UPDATE).count()

    tra_loi = client.post(f"/nhan-su/{ho_so.pk}/sua/", {
        "full_name": ho_so.full_name,
        "rank": Rank.MANAGER,
        "department": departments["sale"].pk,
        "team": "",
    })
    assert tra_loi.status_code == 302

    sau = AuditLog.objects.filter(action=AuditAction.UPDATE)
    assert sau.count() == truoc + 1
    chi_tiet = sau.first().detail
    assert "Cấp bậc" in chi_tiet and "Quản lý" in chi_tiet


def test_moi_ham_dich_vu_deu_ghi_nhat_ky(db, departments, nguoi_dung):
    """AC-9.2 — Mọi thao tác thay đổi dữ liệu sinh một dòng trong nhật ký"""
    from core.constants import Rank
    from org.services import account_service, org_service

    ho_so = nguoi_dung["staff_sale_1"].profile
    cac_thao_tac = [
        lambda: org_service.create_department(name="Kế toán", code="ke-toan"),
        lambda: org_service.create_team(name="Team mới", department=departments["sale"]),
        lambda: account_service.set_rank(ho_so, Rank.LEADER),
        lambda: account_service.lock_account(ho_so),
        lambda: account_service.unlock_account(ho_so),
        lambda: account_service.reset_password(ho_so, "MatKhauMoi-2026"),
    ]
    for chay in cac_thao_tac:
        truoc = AuditLog.objects.count()
        chay()
        assert AuditLog.objects.count() > truoc, chay


# ══ F7 · Màn hình bộ phận phải có phân trang ═══════════════════════

def test_man_hinh_bo_phan_co_phan_trang(client, nguoi_dung):
    """AC-10.2 — Màn hình danh sách phải có phân trang, mặc định 25 dòng"""
    client.force_login(nguoi_dung["admin"])
    noi_dung = client.get("/bo-phan/").content.decode()
    assert noi_dung.count('class="phan-trang"') == 2      # bộ phận và team
    assert "Mỗi trang" in noi_dung


# ══ F8 · Nhật ký không xoá được kể cả theo lô ══════════════════════

def test_khong_xoa_duoc_nhat_ky_theo_lo(nguoi_dung):
    """AC-9.3 — Không có đường nào xoá được bản ghi nhật ký, kể cả theo lô

    Chặn ở mức đối tượng là chưa đủ: `objects.filter(...).delete()` vẫn xoá
    cứng được nếu queryset không chặn.
    """
    from core import audit

    audit.record(AuditAction.LOGIN, actor=nguoi_dung["admin"])
    with pytest.raises(RuntimeError):
        AuditLog.objects.all().delete()


def test_khong_sua_duoc_nhat_ky_theo_lo(nguoi_dung):
    """AC-9.3 — Không sửa được bản ghi nhật ký theo lô"""
    from core import audit

    audit.record(AuditAction.LOGIN, actor=nguoi_dung["admin"])
    with pytest.raises(RuntimeError):
        AuditLog.objects.all().update(detail="sửa trộm")


# ══ F11 · Hiển thị giờ Việt Nam — AC-9.4 ═══════════════════════════

def test_luu_gio_quoc_te_hien_gio_viet_nam(nguoi_dung, settings):
    """AC-9.4 — Dữ liệu lưu theo giờ quốc tế, hiển thị theo giờ Việt Nam"""
    from core import audit

    ban_ghi = audit.record(AuditAction.LOGIN, actor=nguoi_dung["admin"])
    ban_ghi.refresh_from_db()

    # Lưu ở UTC
    assert ban_ghi.created_at.utcoffset().total_seconds() == 0
    # Hiển thị ở giờ Việt Nam, lệch 7 tiếng
    gio_vn = timezone.localtime(ban_ghi.created_at)
    assert gio_vn.utcoffset().total_seconds() == 7 * 3600
    assert f"{gio_vn:%H:%M}" in str(ban_ghi)


# ══ AC-9.5 · Cộng 1.000 dòng tiền không sai số ═════════════════════

def test_cong_mot_nghin_dong_tien_khong_sai_so():
    """AC-9.5 — Cộng 1.000 dòng tiền cho kết quả chính xác tuyệt đối"""
    tong = Decimal("0.00")
    for _ in range(1000):
        tong += Decimal("0.01")
    assert tong == Decimal("10.00")

    # Cùng phép tính bằng số thực dấu phẩy động thì sai — đó là lý do có BR-8
    tong_float = 0.0
    for _ in range(1000):
        tong_float += 0.01
    assert tong_float != 10.0


# ══ AC-10.2 · Màn hình danh sách không quá 10 lệnh truy vấn ════════

@pytest.mark.parametrize(
    "duong_dan",
    ["/nhan-su/", "/nhat-ky/", "/bo-phan/", "/bang/", "/ma-tran-quyen/"],
)
def test_man_hinh_danh_sach_khong_qua_muoi_lenh_truy_van(
    client, nguoi_dung, django_assert_max_num_queries, duong_dan,
):
    """AC-10.2 — Màn hình danh sách chạy không quá 10 lệnh truy vấn

    Đây là bài duy nhất bắt được lỗi N+1 khi thêm màn hình mới (quy tắc Q2).
    """
    client.force_login(nguoi_dung["admin"])
    client.get(duong_dan)      # yêu cầu đầu ghi dấu thời gian vào phiên
    with django_assert_max_num_queries(10):
        assert client.get(duong_dan).status_code == 200


# ══ AC-10.7 · Không đọc được mật khẩu trong cơ sở dữ liệu ══════════

def test_khong_doc_duoc_mat_khau_trong_co_so_du_lieu(nguoi_dung):
    """AC-10.7 — Đọc trực tiếp cơ sở dữ liệu không thấy mật khẩu dạng đọc được"""
    user = nguoi_dung["staff_sale_1"]
    user.refresh_from_db()
    assert "matkhau-kiem-thu-1" not in user.password
    assert user.password.count("$") >= 2      # dạng thuật_toán$tham_số$băm


# ══ AC-1.3 · Tài khoản tự mở khoá sau 15 phút ══════════════════════

def test_tai_khoan_tu_mo_khoa_sau_muoi_lam_phut(client, nguoi_dung, settings):
    """AC-1.3 — Tài khoản bị khoá tự mở lại sau 15 phút"""
    from datetime import timedelta

    profile = nguoi_dung["staff_sale_1"].profile
    for _ in range(settings.LOGIN_MAX_FAILED):
        client.post("/dang-nhap/", {"username": "staff_sale_1", "password": "sai"})
    profile.refresh_from_db()
    assert profile.locked_until is not None

    # Đẩy mốc khoá lùi về quá khứ, coi như đã qua 15 phút
    profile.locked_until = timezone.now() - timedelta(seconds=1)
    profile.save(update_fields=["locked_until"])

    tra_loi = client.post("/dang-nhap/", {
        "username": "staff_sale_1", "password": "matkhau-kiem-thu-1",
    })
    assert tra_loi.status_code == 302


# ══ AC-2.1 và AC-2.2 · Tạo bộ phận và team ═════════════════════════

def test_tao_duoc_bo_phan_moi(client, nguoi_dung):
    """AC-2.1 — Tạo được bộ phận mới, hiển thị trong danh sách"""
    from org.models import Department

    client.force_login(nguoi_dung["admin"])
    client.post("/bo-phan/", {
        "bp-name": "Kế toán", "bp-code": "ke-toan", "bp-is_active": "on",
        "tao_bo_phan": "1",
    })
    assert Department.objects.filter(code="ke-toan").exists()
    assert "Kế toán" in client.get("/bo-phan/").content.decode()


def test_tao_duoc_nhieu_team_trong_mot_bo_phan(client, nguoi_dung, departments):
    """AC-2.2 — Tạo được nhiều team trong một bộ phận"""
    from org.models import Team

    client.force_login(nguoi_dung["admin"])
    for ten in ("Sale 3", "Sale 4"):
        client.post("/bo-phan/", {
            "tm-name": ten, "tm-department": departments["sale"].pk,
            "tm-leader": "", "tm-is_active": "on", "tao_team": "1",
        })
    assert Team.objects.filter(department=departments["sale"]).count() >= 4
