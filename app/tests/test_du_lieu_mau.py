"""Kiểm thử lệnh dựng dữ liệu mẫu.

Lệnh này là thứ duy nhất biến một máy trống thành một hệ thống dùng được —
`docs/04` mục 12 việc số 1: *"Cài đặt từ đầu trên máy sạch, chạy tới màn hình
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
from org.models import Department, Team

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
    """docs/04 mục 12.1 — Cài từ đầu trên máy sạch, chạy tới màn hình đăng nhập

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
