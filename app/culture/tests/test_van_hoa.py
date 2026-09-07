"""Ghi nhận văn hoá, sao và bảng xếp hạng doanh số — FR-12.1 tới FR-12.5, ADR-015.

Trang Văn hoá là của toàn công ty, nên "bị từ chối" ở đây là: tự ghi nhận,
lời nhắn trống, người đã khoá, thành viên không có, gọi sai phương thức, và
chưa đăng nhập. Bảng xếp hạng là ngoại lệ phạm vi có chủ ý (ADR-015 mục 5):
bài AC-15.2 kiểm đúng điều nó hứa — chỉ hạng, số đơn, tổng; không lộ mã đơn.
"""
from datetime import date, timedelta
from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from core.constants import AuditAction, Currency
from core.exceptions import BusinessError
from core.models import AuditLog
from culture.constants import MONTHLY_RANK_STARS, CoreValue, StarSource
from culture.models import Recognition, StarAward
from culture.services import leaderboard_service, recognition_service
from orders.constants import Market
from orders.models import Order, Product, ProductGroup
from orders.services import dispatch_service, order_service

pytestmark = pytest.mark.django_db

#: Tỉ giá tròn để đọc số bằng mắt: 100 USD = 2.500.000, 500 CAD = 9.000.000
TI_GIA = {"VND": Decimal("1"), "USD": Decimal("25000"), "CAD": Decimal("18000")}


def _so(action):
    return AuditLog.objects.filter(action=action).count()


@pytest.fixture
def san_pham(db, departments, nguoi_dung):
    """Lên đơn cần bảng vận đơn và một sản phẩm."""
    dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])
    nhom = ProductGroup.objects.create(name="Đồ gia dụng")
    return Product.objects.create(name="Máy massage cầm tay HM-200", code="hm200", group=nhom)


def _don(nguoi, san_pham, gia, currency=Currency.USD, market=Market.US):
    return order_service.create_order(
        phone=f"09{Order.all_objects.count():08d}", customer_name="Khách thử",
        currency=currency, market=market,
        lines=[{"product": san_pham, "quantity": 1, "unit_price": gia}], actor=nguoi,
    )


def _lui_ve_thang_truoc(*cac_don):
    """Đẩy ngày lên đơn về giữa tháng trước — đúng luật là không sửa đơn, nên
    làm thẳng ở tầng dữ liệu, chỉ trong bài kiểm."""
    dau_thang, _ = leaderboard_service.month_range()
    Order.all_objects.filter(pk__in=[d.pk for d in cac_don]).update(
        created_at=dau_thang - timedelta(days=10))


def _ghi_nhan(giver, receiver, value=CoreValue.HOP_TAC, message="Làm tốt lắm"):
    return recognition_service.give_recognition(
        receiver=receiver, value=value, message=message, actor=giver)


# ══ AC-15.1 · Ghi nhận và sao ══════════════════════════════════════

def test_ghi_nhan_dong_nghiep_cong_mot_sao(client, nguoi_dung):
    """AC-15.1 — Ai đăng nhập cũng ghi nhận được đồng nghiệp theo một giá trị văn hoá, người nhận được cộng đúng một sao cùng giao dịch và có nhật ký; tự ghi nhận, lời nhắn trống, giá trị lạ hay người đã khoá đều bị từ chối; GET vào đường gửi trả 405"""
    n = nguoi_dung
    ky = recognition_service.current_period()

    # Bốn cấp bậc, ba bộ phận đều mở được trang
    for vai in ("staff_sale_1", "leader_sale_1", "manager_mkt", "staff_vd", "admin"):
        client.force_login(n[vai])
        assert client.get("/van-hoa/").status_code == 200, vai

    # Staff Sale ghi nhận nhân viên Marketing — chéo bộ phận vẫn được
    client.force_login(n["staff_sale_1"])
    truoc = _so(AuditAction.CREATE)
    kq = client.post("/van-hoa/ghi-nhan/", {
        "receiver": n["staff_mkt"].pk, "value": CoreValue.SANG_TAO,
        "message": "Bộ ảnh mới làm tỉ lệ chốt tăng rõ",
    })
    assert kq.status_code == 302 and kq["Location"] == "/van-hoa/"
    gn = Recognition.objects.get()
    assert (gn.giver, gn.receiver, gn.value) == (n["staff_sale_1"], n["staff_mkt"], CoreValue.SANG_TAO)
    sao = StarAward.objects.get(recognition=gn)
    assert (sao.receiver, sao.source, sao.stars, sao.period) == (
        n["staff_mkt"], StarSource.GHI_NHAN, 1, ky)
    assert recognition_service.stars_of(n["staff_mkt"]) == 1
    assert _so(AuditAction.CREATE) == truoc + 1
    assert "Ghi nhận #" in AuditLog.objects.filter(action=AuditAction.CREATE).first().detail

    # Trang hiện ghi nhận cho người bộ phận khác xem
    client.force_login(n["staff_vd"])
    noi_dung = client.get("/van-hoa/").content.decode()
    assert "Bộ ảnh mới làm tỉ lệ chốt tăng rõ" in noi_dung and "Sáng tạo" in noi_dung

    # Danh sách chọn không có chính mình
    assert n["staff_vd"] not in recognition_service.recipients(n["staff_vd"])
    assert n["staff_mkt"] in recognition_service.recipients(n["staff_vd"])
    assert f'<option value="{n["staff_vd"].pk}">' not in noi_dung

    # Bị từ chối: tự ghi nhận, lời nhắn trống, giá trị lạ, người đã khoá
    with pytest.raises(BusinessError):
        _ghi_nhan(n["staff_vd"], n["staff_vd"])
    with pytest.raises(BusinessError):
        _ghi_nhan(n["staff_vd"], n["staff_mkt"], message="   ")
    with pytest.raises(BusinessError):
        _ghi_nhan(n["staff_vd"], n["staff_mkt"], value="lam_bua")
    n["staff_sale_2"].is_active = False
    n["staff_sale_2"].save(update_fields=["is_active"])
    with pytest.raises(BusinessError):
        _ghi_nhan(n["staff_vd"], n["staff_sale_2"])
    kq = client.post("/van-hoa/ghi-nhan/", {
        "receiver": n["staff_vd"].pk, "value": CoreValue.TAN_TAM, "message": "Tự khen",
    })
    assert kq.status_code == 302
    assert Recognition.objects.count() == 1 and StarAward.objects.count() == 1

    # Sai phương thức và chưa đăng nhập
    assert client.get("/van-hoa/ghi-nhan/").status_code == 405
    client.logout()
    kq = client.post("/van-hoa/ghi-nhan/", {"receiver": n["staff_mkt"].pk})
    assert kq.status_code == 302 and "/dang-nhap/" in kq["Location"]
    assert "/dang-nhap/" in client.get("/van-hoa/")["Location"]


# ══ AC-15.2 · Bảng xếp hạng doanh số ═══════════════════════════════

@override_settings(EXCHANGE_RATES_VND=TI_GIA)
def test_bang_xep_hang_doanh_so_thang_nay(client, nguoi_dung, san_pham):
    """AC-15.2 — Bảng xếp hạng gộp đơn tháng này theo người bán, quy về VND bằng tỉ giá cố định trong cấu hình, xếp theo tổng rồi số đơn; đơn đã bỏ và đơn tháng trước không tính; mọi bộ phận xem được nhưng không thấy mã đơn; thiếu tỉ giá thì báo lỗi, không trả số sai"""
    n = nguoi_dung
    _don(n["staff_sale_1b"], san_pham, "15000000", Currency.VND)             # 15.000.000
    _don(n["staff_sale_2"], san_pham, "500.00", Currency.CAD, Market.CA)      # 9.000.000
    _don(n["staff_sale_1"], san_pham, "100.00")                              # 2 đơn = 5.000.000
    _don(n["staff_sale_1"], san_pham, "100.00")
    _don(n["manager_sale"], san_pham, "200.00")                              # 1 đơn = 5.000.000
    # Hai đơn to hơn tất cả nhưng không được tính: một đã bỏ, một của tháng trước
    order_service.cancel_order(_don(n["staff_sale_1"], san_pham, "9999.00"), actor=n["staff_sale_1"])
    _lui_ve_thang_truoc(_don(n["staff_sale_1"], san_pham, "9999.00"))

    bang = leaderboard_service.sales_leaderboard()
    assert [(d["hang"], d["user"], d["so_don"], d["tong_vnd"]) for d in bang] == [
        (1, n["staff_sale_1b"], 1, Decimal("15000000")),
        (2, n["staff_sale_2"], 1, Decimal("9000000")),
        (3, n["staff_sale_1"], 2, Decimal("5000000")),     # bằng tổng, nhiều đơn hơn thì đứng trên
        (4, n["manager_sale"], 1, Decimal("5000000")),
    ]
    assert [d["sao_thuong"] for d in bang] == [5, 3, 1, 0]
    assert bang[0]["tong_hien"] == "15.000.000"
    assert leaderboard_service.to_vnd(Decimal("0.10"), "USD") == Decimal("2500")

    # Bộ phận Vận đơn xem được hạng, tên, số đơn, tổng — không thấy mã đơn nào
    client.force_login(n["staff_vd"])
    kq = client.get("/van-hoa/")
    assert kq.status_code == 200
    noi_dung = kq.content.decode()
    assert "15.000.000" in noi_dung and "Staff Sale 1B" in noi_dung
    assert "DH-" not in noi_dung
    assert kq.context["bang_xep_hang"][0]["user"] == n["staff_sale_1b"]

    # Thiếu tỉ giá: không quy đổi bừa
    with override_settings(EXCHANGE_RATES_VND={"VND": Decimal("1")}):
        with pytest.raises(BusinessError):
            leaderboard_service.sales_leaderboard()
        kq = client.get("/van-hoa/")
        assert kq.status_code == 200 and kq.context["bang_xep_hang"] == []
        assert "Chưa có tỉ giá cho" in kq.content.decode()


# ══ AC-15.3 · Thưởng sao tháng ═════════════════════════════════════

@override_settings(EXCHANGE_RATES_VND=TI_GIA)
def test_thuong_sao_top_ba_thang_truoc_khong_nhan_doi(nguoi_dung, san_pham):
    """AC-15.3 — Ngày 1 hằng tháng ba người dẫn đầu kỳ trước nhận 5, 3, 1 sao; lệnh và tác vụ nền chạy lại không nhân đôi; kỳ sai định dạng bị từ chối; mỗi lần chạy một dòng nhật ký"""
    from culture.tasks import thuong_sao_thang

    n = nguoi_dung
    ky_truoc = leaderboard_service.previous_period()
    ky_nay = recognition_service.current_period()
    assert leaderboard_service.previous_period(date(2026, 1, 15)) == "2025-12"
    dau, cuoi = leaderboard_service.month_range("2026-02")
    assert (dau.date(), cuoi.date()) == (date(2026, 2, 1), date(2026, 3, 1))
    assert dau.utcoffset().total_seconds() == 7 * 3600          # theo giờ Việt Nam

    _lui_ve_thang_truoc(
        _don(n["staff_sale_1"], san_pham, "400.00"),
        _don(n["staff_sale_2"], san_pham, "300.00"),
        _don(n["staff_sale_1b"], san_pham, "200.00"),
        _don(n["leader_sale_1"], san_pham, "100.00"),            # hạng 4: không có sao
    )
    _don(n["manager_sale"], san_pham, "9999.00")                # tháng này: chưa tới lượt

    truoc = _so(AuditAction.CREATE)
    assert leaderboard_service.award_monthly_stars(ky_truoc) == 3
    assert _so(AuditAction.CREATE) == truoc + 1
    thuong = {s.receiver: (s.stars, s.rank) for s in StarAward.objects.filter(source=StarSource.XEP_HANG)}
    assert thuong == {
        n["staff_sale_1"]: (5, 1), n["staff_sale_2"]: (3, 2), n["staff_sale_1b"]: (1, 3),
    }
    assert MONTHLY_RANK_STARS == (5, 3, 1)
    assert recognition_service.stars_of(n["staff_sale_1"], ky_truoc) == 5
    assert recognition_service.stars_of(n["staff_sale_1"], ky_nay) == 0
    assert recognition_service.stars_of(n["leader_sale_1"]) == 0

    # Chạy lại bằng dịch vụ, bằng lệnh, bằng tác vụ nền: không thêm sao nào
    assert leaderboard_service.award_monthly_stars(ky_truoc) == 0
    ra = StringIO()
    call_command("thuong_sao_thang", "--thang", ky_truoc, stdout=ra)
    assert "0 dong sao moi" in ra.getvalue()
    assert thuong_sao_thang() == 0                              # mặc định: tháng trước
    assert StarAward.objects.filter(source=StarSource.XEP_HANG).count() == 3
    assert recognition_service.stars_of(n["staff_sale_1"]) == 5
    assert _so(AuditAction.CREATE) == truoc + 4                 # mỗi lần chạy một dòng

    # Kỳ sai định dạng
    with pytest.raises(BusinessError):
        leaderboard_service.award_monthly_stars("2026-13")
    with pytest.raises(CommandError):
        call_command("thuong_sao_thang", "--thang", "thang-nay", stdout=StringIO())


# ══ AC-15.4 · Trang thành viên và nhiều sao nhất ═══════════════════

def test_trang_thanh_vien_tong_sao_va_ghi_nhan(client, nguoi_dung):
    """AC-15.4 — Trang thành viên hiện tổng sao mọi kỳ, sao kỳ này, sao theo tháng và ghi nhận nhận được phân trang 25 dòng; bảng Nhiều sao nhất xếp theo tổng sao; thành viên không có hoặc đã khoá trả 404"""
    n = nguoi_dung
    ky = recognition_service.current_period()
    ky_truoc = leaderboard_service.previous_period()
    for i in range(26):
        _ghi_nhan(n["staff_sale_1"], n["staff_mkt"], message=f"Lần {i + 1}")
    _ghi_nhan(n["staff_vd"], n["staff_sale_2"], value=CoreValue.TAN_TAM)
    StarAward.objects.create(                                   # thưởng xếp hạng tháng trước
        receiver=n["staff_mkt"], source=StarSource.XEP_HANG, stars=5, period=ky_truoc, rank=1)

    assert recognition_service.stars_of(n["staff_mkt"]) == 31
    assert recognition_service.stars_of(n["staff_mkt"], ky) == 26
    assert recognition_service.stars_by_period(n["staff_mkt"]) == [(ky, 26), (ky_truoc, 5)]
    top = recognition_service.star_totals()
    assert [(d["hang"], d["user"], d["sao"], d["sao_ky"]) for d in top] == [
        (1, n["staff_mkt"], 31, 26), (2, n["staff_sale_2"], 1, 1),
    ]

    client.force_login(n["staff_vd"])
    duong_dan = f"/van-hoa/thanh-vien/{n['staff_mkt'].pk}/"
    kq = client.get(duong_dan)
    assert kq.status_code == 200
    assert (kq.context["tong_sao"], kq.context["sao_ky"]) == (31, 26)
    assert kq.context["theo_ky"] == [(ky, 26), (ky_truoc, 5)]
    assert kq.context["page_obj"].paginator.count == 26
    assert len(kq.context["trang"]) == 25
    assert len(client.get(duong_dan, {"trang": 2}).context["trang"]) == 1
    assert "★ 31" in client.get("/van-hoa/").content.decode()

    # Không có, hoặc đã khoá: 404
    assert client.get("/van-hoa/thanh-vien/999999/").status_code == 404
    n["staff_sale_2"].is_active = False
    n["staff_sale_2"].save(update_fields=["is_active"])
    assert client.get(f"/van-hoa/thanh-vien/{n['staff_sale_2'].pk}/").status_code == 404
    assert [d["user"] for d in recognition_service.star_totals()] == [n["staff_mkt"]]
    client.logout()
    assert "/dang-nhap/" in client.get(duong_dan)["Location"]


# ══ Ngân sách truy vấn — AC-10.2 ═══════════════════════════════════

def test_trang_thanh_vien_khong_qua_muoi_lenh_truy_van(client, nguoi_dung, django_assert_max_num_queries):
    """AC-10.2 — Trang thành viên chạy không quá 10 lệnh truy vấn"""
    n = nguoi_dung
    for _ in range(3):
        _ghi_nhan(n["staff_sale_1"], n["staff_mkt"])
    client.force_login(n["admin"])
    duong_dan = f"/van-hoa/thanh-vien/{n['staff_mkt'].pk}/"
    client.get(duong_dan)
    with django_assert_max_num_queries(10):
        assert client.get(duong_dan).status_code == 200
