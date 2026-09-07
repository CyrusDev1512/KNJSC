"""Kiểm thử lệnh dựng dữ liệu mẫu.

Lệnh này là thứ duy nhất biến một máy trống thành một hệ thống dùng được —
`docs/04` mục 17 việc số 1: *"Cài đặt từ đầu trên máy sạch, chạy tới màn hình
đăng nhập"*. Hỏng lặng lẽ thì người mở máy mới không đăng nhập được, và cũng
không biết vì sao.

Bốn điều phải đúng:

1. Chạy trên cơ sở dữ liệu trống thì ra hệ thống đăng nhập được
2. Chạy lại nhiều lần không tạo trùng
3. Số liệu mẫu đúng bằng số trong tệp thật của khách hàng
4. Không chạy được ở môi trường thật nếu chưa ghi rõ là cố ý
"""
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from core.constants import Rank
from forms_builder.models import DataRecord, FormDef, TableDef
from orders.constants import WAYBILL_TABLE_CODE
from orders.models import Product
from org.models import Department, Team, UserProfile

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _nhu_may_phat_trien(settings):
    """Django tự tắt `DEBUG` khi chạy kiểm thử, còn lệnh này chỉ chạy khi bật.

    Bật lại để mô phỏng đúng máy phát triển. Hai bài kiểm hàng rào ở cuối tệp
    tự tắt lại bằng `override_settings`.
    """
    settings.DEBUG = True


def _chay(**tuy_chon):
    ra = StringIO()
    call_command("du_lieu_mau", stdout=ra, **tuy_chon)
    return ra.getvalue()


def test_may_trong_chay_xong_thi_dang_nhap_duoc(client):
    """docs/04 mục 17.1 — Cài từ đầu trên máy sạch, chạy tới màn hình đăng nhập

    Đây là bài quan trọng nhất của tệp: không có nó thì người mở máy mới nhận
    một hệ thống không có tài khoản nào.
    """
    from django.contrib.auth import get_user_model

    assert not get_user_model().objects.exists()
    _chay()

    assert get_user_model().objects.count() == 12
    kq = client.post("/dang-nhap/", {
        "username": "quantri", "password": "MatKhauTam-2026",
    })
    assert kq.status_code == 302, "Tài khoản quản trị không đăng nhập được"


def test_dung_du_co_cau_to_chuc():
    """FR-2.1, FR-2.2 — Ba bộ phận, hai team, mỗi team một trưởng nhóm"""
    _chay()

    assert set(Department.objects.values_list("code", flat=True)) == {
        "sale", "marketing", "van-don"}
    assert Team.objects.count() == 2
    assert all(t.leader_id is not None for t in Team.objects.all()), (
        "Team chưa có trưởng nhóm thì không thử được phạm vi quyền của Leader"
    )


def test_du_bon_cap_bac_de_thu_pham_vi_quyen():
    """AC-3.1 tới AC-3.8 — Có đủ bốn cấp bậc ở cả ba bộ phận để thử phân quyền"""
    from org.models import UserProfile

    _chay()
    cap_bac = set(UserProfile.objects.values_list("rank", flat=True))
    assert cap_bac == {Rank.STAFF, Rank.LEADER, Rank.MANAGER, Rank.ADMIN}

    for ma in ("sale", "marketing", "van-don"):
        assert UserProfile.objects.filter(department__code=ma).count() >= 2, (
            f"Bộ phận {ma} cần ít nhất hai người để thử phạm vi quyền"
        )


def test_so_lieu_mau_dung_bang_tep_that_cua_khach_hang():
    """AC-7.10 — Cột tính sẵn cho đúng số liệu trong tệp thật

    Dòng đầu sheet BC MKT: CPQC 438.446.060 · Số đơn 291 · Số Mess 4.303.
    Bản của khách hàng ra CPO 1.506.687 và tỉ lệ chốt 6,76%.
    """
    _chay()
    bg = DataRecord.objects.filter(table__code="bao_cao_mkt").order_by("created_at").first()

    assert bg is not None, "Chưa dựng dòng dữ liệu nào cho bảng Báo cáo Marketing"
    assert bg.data["cpo"] == "1506687"
    assert bg.data["ti_le_chot"] == "6.76"


def test_dung_du_bang_bieu_mau_va_san_pham():
    """Máy mới phải có đủ thứ để đi trọn luồng ba bộ phận"""
    _chay()

    assert TableDef.objects.filter(code=WAYBILL_TABLE_CODE).exists(), "Thiếu bảng vận đơn"
    assert TableDef.objects.filter(code="bao_cao_mkt").exists(), "Thiếu bảng báo cáo"
    assert FormDef.objects.filter(code="bc_mkt_ngay").exists(), "Thiếu biểu mẫu nộp báo cáo"
    assert Product.objects.count() >= 3, "Thiếu sản phẩm để lên đơn"


def test_chay_lai_khong_tao_trung():
    """Lệnh chạy lại nhiều lần được, không sinh bản ghi trùng"""
    _chay()
    dem = (Department.objects.count(), Team.objects.count(),
           TableDef.objects.count(), DataRecord.objects.count(),
           Product.objects.count(), FormDef.objects.count())

    ra = _chay()

    assert (Department.objects.count(), Team.objects.count(),
            TableDef.objects.count(), DataRecord.objects.count(),
            Product.objects.count(), FormDef.objects.count()) == dem
    assert "khong co gi moi" in ra, (
        "Chạy lần hai vẫn báo có tạo thứ gì đó — bản báo cáo nói sai"
    )


def test_tai_khoan_moi_van_giu_co_buoc_doi_mat_khau():
    """AC-1.5 — Giữ một tài khoản chưa đổi mật khẩu để thử đúng luồng FR-1.4"""
    from org.models import UserProfile

    _chay()
    assert UserProfile.objects.get(user__username="sale.moi").must_change_password
    assert not UserProfile.objects.get(user__username="quantri").must_change_password


@override_settings(DEBUG=False)
def test_khong_chay_duoc_o_moi_truong_that():
    """NFR-4 — Lệnh tạo tài khoản mật khẩu ai cũng biết thì phải chặn ở máy thật"""
    with pytest.raises(CommandError) as loi:
        _chay()
    assert "DEBUG" in str(loi.value)

    from django.contrib.auth import get_user_model
    assert not get_user_model().objects.exists(), "Đã chặn mà vẫn tạo tài khoản"


@override_settings(DEBUG=False)
def test_van_chay_duoc_khi_ghi_ro_la_co_y():
    """Chặn được nhưng không khoá chết — người biết mình làm gì thì vẫn chạy được"""
    _chay(dong_y_chay_that=True)

    from django.contrib.auth import get_user_model
    assert get_user_model().objects.count() == 12


def test_san_pham_mau_khop_danh_muc_va_co_mau():
    """AC-8.8 — Cột Sản phẩm mẫu là ô chọn lấy từ danh mục, mọi dòng mẫu khớp tên sản phẩm; cột mẫu có màu và ngưỡng để thấy ngay"""
    from decimal import Decimal

    from forms_builder.models import ColumnDef

    _chay()
    bang_cot = {c.code: c for c in ColumnDef.objects.filter(table__code="bao_cao_mkt")}
    assert bang_cot["san_pham"].field_type == "choice" and bang_cot["san_pham"].meaning == "product"
    ten_san_pham = set(Product.objects.values_list("name", flat=True))
    for dong in DataRecord.objects.filter(table__code="bao_cao_mkt"):
        assert dong.data["san_pham"] in ten_san_pham, dong.data["san_pham"]
    assert bang_cot["ti_le_chot"].highlight == "vang"
    assert (bang_cot["cpo"].highlight, bang_cot["cpo"].alert_op, bang_cot["cpo"].alert_value) == (
        "do", "gt", Decimal("1500000"))


@pytest.mark.django_db
def test_chay_lai_dat_lai_dung_mat_khau_da_in(client):
    """docs/04 mục 17.1 — Chạy lại lệnh thì mật khẩu in ra cuối lệnh là mật khẩu thật, kể cả khi tài khoản đã có

    Lỗi thật ngày 03.09.2026: máy của người dùng có sẵn `quantri` từ lần dựng
    trước với mật khẩu khác; lệnh bỏ qua tài khoản có sẵn nên màn hình in một
    mật khẩu, cơ sở dữ liệu giữ một mật khẩu khác — đăng nhập hỏng.
    """
    from django.core.management import call_command
    from django.utils import timezone

    call_command("du_lieu_mau", "--mat-khau", "mat-khau-lan-mot", verbosity=0)
    ho_so = UserProfile.objects.select_related("user").get(user__username="quantri")
    ho_so.locked_until = timezone.now() + timezone.timedelta(minutes=15)   # đang bị khoá
    ho_so.save(update_fields=["locked_until"])

    call_command("du_lieu_mau", "--mat-khau", "mat-khau-lan-hai", verbosity=0)
    assert client.login(username="quantri", password="mat-khau-lan-hai")
    assert not client.login(username="quantri", password="mat-khau-lan-mot")
    ho_so.refresh_from_db()
    assert ho_so.locked_until is None and ho_so.must_change_password is False
    assert UserProfile.objects.get(user__username="sale.moi").must_change_password is True


# ══ Nhóm Nội bộ và bảng xếp hạng mẫu — ADR-015, rà soát 07.09 ═══════

TI_GIA_MAC_DINH = {"VND": 1, "USD": 25400, "CAD": 18500, "PHP": 440}


@override_settings(EXCHANGE_RATES_VND={k: __import__("decimal").Decimal(v) for k, v in TI_GIA_MAC_DINH.items()})
def test_du_lieu_noi_bo_va_bang_xep_hang_mau():
    """AC-15.2 — Dữ liệu mẫu dựng đủ nhóm Nội bộ: ba mục và bốn tài liệu, sáu việc, bốn ghi nhận từ trên xuống kèm bốn sao, năm bài (một ghim) với ba bình luận và bảy lượt thích, thiệp sinh nhật hôm nay cho sale.staff, năm mục và sáu tài nguyên; bốn đơn mẫu cho bảng xếp hạng tháng này ra đúng số ghi ở docs/07 với tỉ giá mặc định: sale.staff hạng 1 với 9.880.600 VND"""
    from decimal import Decimal

    from core.constants import rank_level
    from culture.models import Recognition, StarAward
    from culture.services import leaderboard_service
    from documents.models import Document, DocumentCategory
    from feed.constants import PostKind
    from feed.models import Comment, Like, Post
    from resources.models import Resource, ResourceCategory
    from taskboard.models import Task

    _chay()
    assert (DocumentCategory.objects.count(), Document.objects.count()) == (3, 4)
    assert Task.objects.count() == 6
    assert Recognition.objects.count() == 4 and StarAward.objects.count() == 4
    for gn in Recognition.objects.select_related("giver__profile", "receiver__profile"):
        assert rank_level(gn.giver.profile.rank) > rank_level(gn.receiver.profile.rank), gn   # Q70
    assert Post.objects.filter(kind=PostKind.BAI_VIET).count() == 5
    assert Post.objects.filter(is_pinned=True).count() == 1
    assert (Comment.objects.count(), Like.objects.count()) == (3, 7)
    thiep = Post.objects.filter(kind=PostKind.SINH_NHAT)
    assert thiep.count() == 1 and thiep.get().subject.username == "sale.staff"
    assert (ResourceCategory.objects.count(), Resource.objects.count()) == (5, 6)

    bxh = leaderboard_service.sales_leaderboard()
    assert [(d["user"].username, d["hang"], d["so_don"], d["tong_vnd"]) for d in bxh] == [
        ("sale.staff", 1, 2, Decimal("9880600")),
        ("sale.staff2", 2, 1, Decimal("6660000")),
        ("sale.leader", 3, 1, Decimal("2590000")),
    ]
    assert bxh[0]["tong_hien"] == "9.880.600"


def test_khong_nhet_don_mau_khi_da_co_van_don_that():
    """AC-15.2 — Máy đã có dòng vận đơn (nhập tệp thật) mà chưa có đơn hàng nào thì lệnh không dựng bốn đơn mẫu, để bảng xếp hạng không lẫn số giả"""
    from orders.models import Order

    _chay()
    assert Order.all_objects.count() == 4
    assert DataRecord.all_objects.filter(table__code=WAYBILL_TABLE_CODE).exists()
    Order.all_objects.all().hard_delete()                       # chỉ còn dòng vận đơn
    ra = _chay()
    assert Order.all_objects.count() == 0 and "đơn hàng" not in ra

