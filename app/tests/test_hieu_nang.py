"""Hiệu năng trên dữ liệu cỡ thật — AC-7.1, NFR-1.

Trước tệp này hệ thống chỉ **đếm số lệnh truy vấn** (quy tắc Q2), chưa bao giờ
chạy trên 50.000 dòng. Bài ở đây sinh đúng cỡ đó (`seed_perf`) rồi bấm giờ.
Chậm — đánh dấu `cham`, bỏ qua khi cần vòng lặp nhanh.
"""
import time

import pytest
from django.test import override_settings

from core.constants import PERF_PAGE_SECONDS, PERF_TABLE_ROWS
from core.management.commands import seed_perf
from forms_builder.models import DataRecord

# K24 đóng 22.09.2026: hai bài từng `xfail` vì đếm 12 lệnh truy vấn, ngân sách 10.
# Cắt được ba lệnh thừa — `/bang-tinh/` hỏi phạm vi quyền **ba** lần cho cùng một
# bảng, và `user.profile` cùng bộ phận của nó nạp lười ở mọi yêu cầu. Nay cả hai
# màn hình dùng 9 lệnh. Ngân sách giữ nguyên 10, không nới.
pytestmark = [pytest.mark.django_db, pytest.mark.cham]


@pytest.fixture(scope="module")
def du_lieu_lon(django_db_setup, django_db_blocker):
    """50.000 dòng vận đơn giả — sinh một lần cho cả module, vì mất gần một phút."""
    with django_db_blocker.unblock():
        from core.constants import Rank
        from django.contrib.auth import get_user_model
        from org.models import Department, UserProfile
        from orders.models import Product, ProductGroup

        User = get_user_model()
        sale = Department.objects.create(name="Sale", code="sale")
        vd = Department.objects.create(name="Vận đơn", code="van-don")
        admin = User.objects.create_user("perf_admin", password="x")
        UserProfile.objects.create(user=admin, full_name="Perf Admin", rank=Rank.ADMIN, must_change_password=False)
        nv = User.objects.create_user("perf_vd", password="x")
        UserProfile.objects.create(user=nv, full_name="Perf VD", rank=Rank.STAFF, department=vd, must_change_password=False)
        sale_nv = User.objects.create_user("perf_sale", password="x")
        UserProfile.objects.create(user=sale_nv, full_name="Perf Sale", rank=Rank.STAFF, department=sale, must_change_password=False)
        nhom = ProductGroup.objects.create(name="Mỹ phẩm perf")
        for ten, ma in [("Retinol Cream", "retinol-cream"), ("Retinol Serum", "retinol-serum"),
                        ("Vitamin C Serum", "vitamin-c-serum")]:
            Product.objects.create(name=ten, code=ma, group=nhom)
        bat_dau = time.monotonic()
        tao = seed_perf.run(n=PERF_TABLE_ROWS, actor=admin)
        yield {"vd": nv, "admin": admin, "tao": tao, "giay_sinh": time.monotonic() - bat_dau}
        seed_perf.clear()
        Product.objects.all().delete()
        nhom.delete()
        for u in (admin, nv, sale_nv):
            u.delete()
        # Dọn thật (không xoá mềm) vì đây là dữ liệu dựng riêng cho bài đo, ghi
        # thẳng ngoài giao dịch của pytest: bảng vận đơn giả giữ bộ phận bằng
        # PROTECT, và bộ phận xoá mềm vẫn chiếm tên "Sale" (unique) làm mọi bài
        # chạy sau không tạo lại được bộ phận.
        from forms_builder.models import TableDef
        for bang in TableDef.all_objects.filter(department__in=[sale, vd]):
            bang.hard_delete()
        vd.hard_delete()
        sale.hard_delete()


def _vao_lam(client, nguoi, duong_dan):
    """Đăng nhập rồi mở một trang bỏ đi trước khi bấm giờ.

    Yêu cầu **đầu tiên** sau khi đăng nhập ghi `last_seen_at` vào phiên, tức thêm
    SAVEPOINT + UPDATE + RELEASE. Đó là giá của lần đăng nhập, không phải giá của
    màn hình: `SessionTimeoutMiddleware.GHI_LAI_SAU` chỉ ghi lại mỗi 60 giây nên
    người dùng thật không trả khoản đó ở từng trang. Đo lượt đầu là đo lẫn.
    """
    client.force_login(nguoi)
    client.get(duong_dan)


def _bam_gio(client, duong_dan, django_assert_max_num_queries):
    with django_assert_max_num_queries(10):
        bat_dau = time.monotonic()
        kq = client.get(duong_dan)
        mat = time.monotonic() - bat_dau
    assert kq.status_code == 200, duong_dan
    return mat


def test_bang_du_lieu_50000_dong_duoi_2_giay(client, du_lieu_lon, django_assert_max_num_queries):
    """AC-7.1 — Bảng 50.000 bản ghi hiện trang đầu dưới 2 giây, không quá 10 lệnh truy vấn"""
    assert du_lieu_lon["tao"] == PERF_TABLE_ROWS
    assert DataRecord.objects.filter(table__code="van_don").count() >= PERF_TABLE_ROWS
    _vao_lam(client, du_lieu_lon["vd"], "/bang/van_don/")
    mat = _bam_gio(client, "/bang/van_don/", django_assert_max_num_queries)
    assert mat < PERF_PAGE_SECONDS, f"trang đầu Bảng dữ liệu mất {mat:.2f}s"
    # Có tìm kiếm và sắp xếp trên cột tách vẫn phải dưới ngưỡng
    mat = _bam_gio(client, "/bang/van_don/?tim=Taylor&sap=ngay&chieu=giam", django_assert_max_num_queries)
    assert mat < PERF_PAGE_SECONDS, f"tìm + sắp xếp mất {mat:.2f}s"


def test_bang_tinh_50000_dong_co_loc_duoi_2_giay(client, du_lieu_lon, django_assert_max_num_queries):
    """AC-7.1 — Bảng tính trên 50.000 dòng, có hai bộ lọc và cột Lọc trùng, trang đầu dưới 2 giây"""
    with override_settings(ROOT_URLCONF="knjsc.urls_bangtinh", GRID_ONLY_TABLES=set()):
        _vao_lam(client, du_lieu_lon["vd"], "/bang-tinh/")
        mat = _bam_gio(client, "/bang-tinh/", django_assert_max_num_queries)
        assert mat < PERF_PAGE_SECONDS, f"lưới không lọc mất {mat:.2f}s"
        mat = _bam_gio(
            client,
            "/bang-tinh/?f_trang_thai_vc__trong=%C4%90ang%20giao&f_ten_khach__chua=Taylor&sap=ngay",
            django_assert_max_num_queries,
        )
        assert mat < PERF_PAGE_SECONDS, f"lưới có lọc mất {mat:.2f}s"
        mat = _bam_gio(client, "/bang-tinh/van_don/loc/trang_thai_vc/", django_assert_max_num_queries)
        assert mat < PERF_PAGE_SECONDS, f"hộp lọc cột mất {mat:.2f}s"
        mat = _bam_gio(client, "/bang-tinh/?trung=1", django_assert_max_num_queries)
        assert mat < PERF_PAGE_SECONDS, f"lọc chỉ số trùng mất {mat:.2f}s"
