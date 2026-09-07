"""Bảng tin — FR-10.1 tới FR-10.6, ADR-015.

Bảng tin là của toàn công ty (FR-10.1), nên chiều "bị từ chối" ở đây là: ghim
hay gỡ bài người khác khi không phải Manager, bài trống, bài đã gỡ, sai
phương thức, chưa đăng nhập. Mỗi bài kiểm cả hai chiều.
"""
from datetime import date, timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

from core.constants import AuditAction
from core.exceptions import BusinessError, OutOfScopeError
from core.models import AuditLog
from culture.constants import CoreValue
from culture.services import recognition_service
from feed.constants import PostKind
from feed.models import Comment, Like, Post
from feed.services import post_service
from org.models import UserProfile

pytestmark = pytest.mark.django_db

#: Yêu cầu do HTMX gửi — view trả mảnh thay vì chuyển hướng
HX = {"HTTP_HX_REQUEST": "true"}


def _so(action):
    return AuditLog.objects.filter(action=action).count()


def _bai(actor, body="Tin vui hôm nay"):
    return post_service.create_post(body=body, actor=actor)


def _dat_sinh_nhat(user, ngay):
    ho_so = user.profile
    ho_so.birthday = ngay
    ho_so.save(update_fields=["birthday"])


# ══ AC-13.1 · Đăng và xem ═══════════════════════════════════════════

def test_dang_bai_va_xem_toan_cong_ty(client, nguoi_dung):
    """AC-13.1 — Ai đăng nhập cũng đăng được bài dạng chữ và thấy mọi bài, không phân theo bộ phận; bài ghim đứng đầu; bài trống hay quá dài bị từ chối; danh sách phân trang 25 dòng; GET vào đường đăng trả 405; chưa đăng nhập bị chuyển về đăng nhập"""
    n = nguoi_dung
    for vai in ("staff_sale_1", "leader_sale_1", "manager_mkt", "staff_vd", "admin"):
        client.force_login(n[vai])
        assert client.get("/bang-tin/").status_code == 200, vai

    client.force_login(n["staff_sale_1"])
    truoc = _so(AuditAction.CREATE)
    kq = client.post("/bang-tin/dang/", {"body": "Chốt được khách Philippines đầu tiên!"})
    assert kq.status_code == 302 and kq["Location"] == "/bang-tin/"
    bai = Post.objects.get()
    assert bai.author == n["staff_sale_1"] and bai.kind == PostKind.BAI_VIET and not bai.is_pinned
    assert _so(AuditAction.CREATE) == truoc + 1

    # Người bộ phận khác thấy bài, thấy tên tác giả
    client.force_login(n["staff_vd"])
    noi_dung = client.get("/bang-tin/").content.decode()
    assert "Chốt được khách Philippines đầu tiên!" in noi_dung and "Staff Sale 1" in noi_dung

    # Bài trống, bài quá dài: hiện lại trang với bài đang gõ, không tạo bài
    kq = client.post("/bang-tin/dang/", {"body": "   "})
    assert kq.status_code == 200 and Post.objects.count() == 1
    kq = client.post("/bang-tin/dang/", {"body": "x" * 2001})
    assert kq.status_code == 200 and Post.objects.count() == 1
    assert "x" * 2001 in kq.content.decode() and "Bài dài quá" in kq.content.decode()
    with pytest.raises(BusinessError):
        _bai(n["staff_vd"], "x" * 2001)

    # Bài ghim đứng đầu dù cũ nhất; 27 bài chia hai trang
    for i in range(26):
        _bai(n["staff_vd"], f"Bài số {i}")
    post_service.pin_post(bai, actor=n["admin"])
    trang = list(client.get("/bang-tin/").context["trang"])
    assert len(trang) == 25 and trang[0] == bai and trang[0].is_pinned
    assert len(client.get("/bang-tin/", {"trang": 2}).context["trang"]) == 2

    assert client.get("/bang-tin/dang/").status_code == 405
    client.logout()
    assert "/dang-nhap/" in client.get("/bang-tin/")["Location"]
    assert "/dang-nhap/" in client.post("/bang-tin/dang/", {"body": "x"})["Location"]


# ══ AC-13.2 · Thích và bình luận ═══════════════════════════════════

def test_thich_va_binh_luan(client, nguoi_dung):
    """AC-13.2 — Bấm thích qua HTMX nhận về đúng nút mới với số lượt; bấm lại là bỏ thích, thích lại không sinh dòng mới; bình luận hiện dưới bài kèm số bình luận, gửi qua HTMX nhận về mảnh bình luận; bình luận trống bị từ chối; bài đã gỡ hay không có trả 404; mỗi tương tác một dòng nhật ký"""
    n = nguoi_dung
    bai = _bai(n["staff_sale_1"])
    client.force_login(n["staff_mkt"])

    truoc = _so(AuditAction.CREATE)
    kq = client.post(f"/bang-tin/{bai.pk}/thich/", **HX)
    assert kq.status_code == 200
    html = kq.content.decode()
    assert "Đã thích" in html and 'aria-pressed="true"' in html and '<span class="so">1</span>' in html
    assert "<html" not in html
    assert Like.objects.filter(post=bai, user=n["staff_mkt"]).exists()
    assert _so(AuditAction.CREATE) == truoc + 1

    tx = _so(AuditAction.DELETE)
    html = client.post(f"/bang-tin/{bai.pk}/thich/", **HX).content.decode()
    assert "Đã thích" not in html and 'aria-pressed="false"' in html and '<span class="so">0</span>' in html
    assert not Like.objects.filter(post=bai).exists() and Like.all_objects.filter(post=bai).count() == 1
    assert _so(AuditAction.DELETE) == tx + 1

    client.post(f"/bang-tin/{bai.pk}/thich/", **HX)                      # thích lại: dùng lại dòng cũ
    assert Like.all_objects.filter(post=bai).count() == 1 and Like.objects.filter(post=bai).count() == 1
    kq = client.post(f"/bang-tin/{bai.pk}/thich/")                       # không HTMX: quay về bài
    assert kq.status_code == 302 and kq["Location"] == f"/bang-tin/{bai.pk}/"
    assert Like.objects.filter(post=bai).count() == 0

    # Bình luận: gửi thường quay về bài, gửi HTMX nhận mảnh
    truoc = _so(AuditAction.CREATE)
    kq = client.post(f"/bang-tin/{bai.pk}/binh-luan/", {"body": "Chúc mừng!"})
    assert kq.status_code == 302 and kq["Location"] == f"/bang-tin/{bai.pk}/"
    assert Comment.objects.filter(post=bai, author=n["staff_mkt"], body="Chúc mừng!").exists()
    assert _so(AuditAction.CREATE) == truoc + 1
    html = client.get(f"/bang-tin/{bai.pk}/").content.decode()
    assert "Chúc mừng!" in html and "1 bình luận" in html and "Staff Mkt" in html
    html = client.post(f"/bang-tin/{bai.pk}/binh-luan/", {"body": "Lần hai"}, **HX).content.decode()
    assert f'id="binh-luan-{bai.pk}"' in html and "Lần hai" in html and "<html" not in html
    assert f'id="binh-luan-{bai.pk}"' in client.get(f"/bang-tin/{bai.pk}/binh-luan/").content.decode()
    kq = client.post(f"/bang-tin/{bai.pk}/binh-luan/", {"body": " "})
    assert kq.status_code == 302 and Comment.objects.filter(post=bai).count() == 2
    assert "Viết nội dung bình luận" in client.post(f"/bang-tin/{bai.pk}/binh-luan/", {"body": ""}, **HX).content.decode()
    with pytest.raises(BusinessError):
        post_service.add_comment(bai, body="y" * 501, actor=n["staff_mkt"])
    assert "2 bình luận" in client.get("/bang-tin/").content.decode()

    # Bài đã gỡ, bài không có
    post_service.delete_post(bai, actor=n["staff_sale_1"])
    for duong_dan in (f"/bang-tin/{bai.pk}/", "/bang-tin/999999/", f"/bang-tin/{bai.pk}/binh-luan/"):
        assert client.get(duong_dan).status_code == 404, duong_dan
    assert client.post(f"/bang-tin/{bai.pk}/thich/", **HX).status_code == 404
    assert client.get(f"/bang-tin/{bai.pk}/thich/").status_code == 405


# ══ AC-13.3 · Ghim và gỡ ═══════════════════════════════════════════

def test_ghim_va_go_bai(client, nguoi_dung):
    """AC-13.3 — Manager và Admin ghim, gỡ ghim và gỡ được bài bất kỳ; tác giả gỡ được bài của mình; Staff hay Leader ghim hoặc gỡ bài người khác bị từ chối có nhật ký và không thấy nút; gỡ là xoá mềm; bình luận gỡ bởi người viết hoặc Manager trở lên"""
    n = nguoi_dung
    bai = _bai(n["staff_sale_1"], "Bài của staff Sale")
    bai_khac = _bai(n["staff_mkt"], "Bài của Marketing")

    client.force_login(n["staff_sale_1"])
    tu_choi = _so(AuditAction.DENIED)
    assert client.post(f"/bang-tin/{bai.pk}/ghim/").status_code == 403
    assert client.post(f"/bang-tin/{bai_khac.pk}/go/").status_code == 403
    client.force_login(n["leader_sale_1"])
    assert client.post(f"/bang-tin/{bai.pk}/ghim/").status_code == 403
    assert client.post(f"/bang-tin/{bai.pk}/go/").status_code == 403
    assert _so(AuditAction.DENIED) == tu_choi + 4
    assert not Post.objects.get(pk=bai.pk).is_pinned and Post.objects.filter(pk=bai_khac.pk).exists()
    with pytest.raises(OutOfScopeError):
        post_service.pin_post(bai, actor=n["staff_sale_1"])
    with pytest.raises(OutOfScopeError):
        post_service.delete_post(bai_khac, actor=n["staff_sale_1"])

    client.force_login(n["staff_sale_1"])
    html = client.get("/bang-tin/").content.decode()
    assert f'action="/bang-tin/{bai.pk}/go/"' in html                 # bài mình: có nút gỡ
    assert f'action="/bang-tin/{bai_khac.pk}/go/"' not in html        # bài người khác: không
    assert f'action="/bang-tin/{bai.pk}/ghim/"' not in html           # Staff không ghim

    # Manager Sale ghim bài của Marketing (bài bất kỳ), bài lên đầu; Admin gỡ ghim
    client.force_login(n["manager_sale"])
    truoc = _so(AuditAction.UPDATE)
    assert client.post(f"/bang-tin/{bai_khac.pk}/ghim/").status_code == 302
    bai_khac.refresh_from_db()
    assert bai_khac.is_pinned and bai_khac.pinned_by == n["manager_sale"] and bai_khac.pinned_at
    assert _so(AuditAction.UPDATE) == truoc + 1
    assert list(client.get("/bang-tin/").context["trang"])[0] == bai_khac
    client.force_login(n["admin"])
    client.post(f"/bang-tin/{bai_khac.pk}/ghim/")
    bai_khac.refresh_from_db()
    assert not bai_khac.is_pinned and bai_khac.pinned_by is None

    # Tác giả gỡ bài mình: xoá mềm, có nhật ký
    client.force_login(n["staff_sale_1"])
    tx = _so(AuditAction.DELETE)
    assert client.post(f"/bang-tin/{bai.pk}/go/").status_code == 302
    assert not Post.objects.filter(pk=bai.pk).exists()
    assert Post.all_objects.get(pk=bai.pk).deleted_by == n["staff_sale_1"]
    assert _so(AuditAction.DELETE) == tx + 1
    # Manager gỡ bài người bộ phận khác
    client.force_login(n["manager_sale"])
    assert client.post(f"/bang-tin/{bai_khac.pk}/go/").status_code == 302
    assert not Post.objects.filter(pk=bai_khac.pk).exists()

    # Bình luận: người viết gỡ được, người khác không, Manager gỡ được
    bai3 = _bai(n["staff_vd"], "Bài ba")
    bl = post_service.add_comment(bai3, body="Hay", actor=n["staff_mkt"])
    client.force_login(n["staff_sale_2"])
    assert client.post(f"/bang-tin/binh-luan/{bl.pk}/go/").status_code == 403
    client.force_login(n["staff_mkt"])
    kq = client.post(f"/bang-tin/binh-luan/{bl.pk}/go/")
    assert kq.status_code == 302 and kq["Location"] == f"/bang-tin/{bai3.pk}/"
    assert not Comment.objects.filter(pk=bl.pk).exists() and Comment.all_objects.filter(pk=bl.pk).exists()
    bl2 = post_service.add_comment(bai3, body="Nữa", actor=n["staff_mkt"])
    client.force_login(n["manager_sale"])
    assert client.post(f"/bang-tin/binh-luan/{bl2.pk}/go/").status_code == 302
    assert not Comment.objects.filter(pk=bl2.pk).exists()
    assert client.post(f"/bang-tin/binh-luan/{bl2.pk}/go/").status_code == 404
    assert client.get(f"/bang-tin/{bai3.pk}/ghim/").status_code == 405


# ══ AC-13.4 · Thiệp sinh nhật ══════════════════════════════════════

def test_thiep_sinh_nhat_tu_dong(client, nguoi_dung):
    """AC-13.4 — Mỗi sáng hệ thống đăng thiệp cho người có sinh nhật hôm đó theo hồ sơ, mỗi người mỗi năm một thiệp; dịch vụ, lệnh và tác vụ nền chạy lại không nhân đôi, thiệp đã gỡ không đăng lại; tài khoản đã khoá không có thiệp; sinh 29.02 được chúc ngày 28.02 năm không nhuận; thiệp hiện trên Bảng tin với kiểu riêng"""
    from feed.tasks import thiep_sinh_nhat

    n = nguoi_dung
    hom_nay = timezone.localdate()
    _dat_sinh_nhat(n["staff_sale_1"], hom_nay.replace(year=1996))
    _dat_sinh_nhat(n["staff_mkt"], hom_nay.replace(year=1992))
    _dat_sinh_nhat(n["leader_sale_1"], hom_nay.replace(year=1988))
    n["leader_sale_1"].is_active = False
    n["leader_sale_1"].save(update_fields=["is_active"])
    _dat_sinh_nhat(n["staff_vd"], (hom_nay - timedelta(days=40)).replace(year=1992))

    truoc = _so(AuditAction.CREATE)
    assert post_service.create_birthday_posts() == 2
    assert _so(AuditAction.CREATE) == truoc + 1
    thiep = Post.objects.filter(kind=PostKind.SINH_NHAT)
    assert {t.subject for t in thiep} == {n["staff_sale_1"], n["staff_mkt"]}
    t = thiep.get(subject=n["staff_sale_1"])
    assert t.author is None and t.birthday_on == hom_nay and t.la_sinh_nhat
    assert "Staff Sale 1" in t.body and "sinh nhật" in t.body

    assert post_service.create_birthday_posts() == 0
    assert thiep_sinh_nhat() == 0
    ra = StringIO()
    call_command("thiep_sinh_nhat", "--ngay", hom_nay.isoformat(), stdout=ra)
    assert "0 thiep moi" in ra.getvalue()
    with pytest.raises(CommandError):
        call_command("thiep_sinh_nhat", "--ngay", "hom-qua", stdout=StringIO())
    assert Post.objects.filter(kind=PostKind.SINH_NHAT).count() == 2
    assert _so(AuditAction.CREATE) == truoc + 1                  # không có thiệp mới thì không thêm dòng

    post_service.delete_post(t, actor=n["admin"])               # gỡ rồi chạy lại: không đăng lại
    assert post_service.create_birthday_posts() == 0

    # Trên trang: thiệp có kiểu riêng, không có tác giả, hiện tên người được chúc
    _bai(n["staff_vd"], "Bài thường")
    client.force_login(n["staff_vd"])
    kq = client.get("/bang-tin/")
    html = kq.content.decode()
    assert "bai-sinh-nhat" in html and "Staff Mkt" in html and "Thiệp tự động" in html
    assert [b.la_sinh_nhat for b in kq.context["trang"]] == [False, True]

    # 29.02: năm không nhuận chúc ngày 28.02, năm nhuận chờ đúng ngày
    UserProfile.objects.update(birthday=None)
    _dat_sinh_nhat(n["staff_sale_2"], date(2000, 2, 29))
    assert post_service.create_birthday_posts(date(2027, 2, 28)) == 1
    assert post_service.create_birthday_posts(date(2028, 2, 28)) == 0
    assert post_service.create_birthday_posts(date(2028, 2, 29)) == 1


# ══ AC-13.5 · Thanh bên ════════════════════════════════════════════

def test_thanh_ben_va_ngan_sach_truy_van(client, nguoi_dung, django_assert_max_num_queries):
    """AC-13.5 — Thanh bên hiện sinh nhật tháng này theo ngày, năm người nhiều sao nhất, ba ghi nhận mới nhất và thành viên có hồ sơ tạo trong 30 ngày; trang Bảng tin và trang bài có dữ liệu chạy không quá 10 lệnh truy vấn"""
    n = nguoi_dung
    hom_nay = timezone.localdate()
    _dat_sinh_nhat(n["staff_sale_1"], date(1995, hom_nay.month, 28))
    _dat_sinh_nhat(n["staff_sale_2"], date(1990, hom_nay.month, 1))
    _dat_sinh_nhat(n["staff_mkt"], date(1991, hom_nay.month % 12 + 1, 5))      # tháng sau: không hiện
    for i in range(3):
        recognition_service.give_recognition(
            receiver=n["staff_mkt"], value=CoreValue.HOP_TAC, message=f"Lần {i}", actor=n["manager_mkt"])
    for i in range(2):
        recognition_service.give_recognition(
            receiver=n["staff_vd"], value=CoreValue.TAN_TAM, message=f"Nữa {i}", actor=n["admin"])
    UserProfile.objects.filter(user=n["staff_sale_1b"]).update(created_at=timezone.now() - timedelta(days=40))
    bai = _bai(n["staff_sale_1"])
    post_service.add_comment(bai, body="Một", actor=n["staff_mkt"])
    post_service.toggle_like(bai, actor=n["staff_vd"])
    post_service.toggle_like(bai, actor=n["staff_mkt"])
    _bai(n["staff_vd"], "Bài hai")

    client.force_login(n["staff_sale_2"])
    client.get("/bang-tin/")
    with django_assert_max_num_queries(10):
        kq = client.get("/bang-tin/")
    assert kq.status_code == 200
    with django_assert_max_num_queries(10):
        assert client.get(f"/bang-tin/{bai.pk}/").status_code == 200

    ben = kq.context
    assert list(ben["sinh_nhat_thang"]) == [n["staff_sale_2"], n["staff_sale_1"]]
    assert ben["sinh_nhat_thang"][0].sinh_nhat_hom_nay == (hom_nay.day == 1)
    assert [(d["user"], d["sao"]) for d in ben["top_sao"]] == [(n["staff_mkt"], 3), (n["staff_vd"], 2)]
    assert len(ben["ghi_nhan_moi"]) == 3 and ben["ghi_nhan_moi"][0].receiver == n["staff_vd"]
    assert n["staff_sale_1b"] not in ben["thanh_vien_moi"]           # hồ sơ 40 ngày: không còn mới
    assert len(ben["thanh_vien_moi"]) == 5 and ben["thanh_vien_moi"][0] == n["admin"]   # tạo sau cùng đứng đầu
    html = kq.content.decode()
    assert "1 bình luận" in html and '<span class="so">2</span>' in html and "★ 3" in html
    assert "Sinh nhật tháng" in html and "Thành viên mới" in html


# ══ Bình luận phân trang, chống bấm đúp, ghim rõ ý — rà soát 07.09 ═

def test_binh_luan_phan_trang_va_ghim_ro_y(client, nguoi_dung):
    """AC-13.2 — Bài chỉ tải 20 bình luận mới nhất, "Xem bình luận cũ hơn" tải tiếp qua HTMX; nút Thích và form bình luận có hx-sync chống bấm đúp; ghim gửi rõ ý muốn nên hai quản lý bấm trên trang cũ không làm ngược ý nhau"""
    n = nguoi_dung
    bai = _bai(n["staff_sale_1"])
    for i in range(23):
        post_service.add_comment(bai, body=f"BL {i:02d}", actor=n["staff_mkt"])
    client.force_login(n["staff_vd"])
    html = client.get(f"/bang-tin/{bai.pk}/").content.decode()
    assert "BL 22" in html and "BL 03" in html and "BL 02" not in html
    assert "Xem bình luận cũ hơn" in html and 'hx-sync="this:drop"' in html
    truoc = Comment.objects.get(body="BL 03").pk
    cu = client.get(f"/bang-tin/{bai.pk}/binh-luan/", {"truoc": truoc}).content.decode()
    assert "BL 02" in cu and "BL 00" in cu and "BL 03" not in cu
    assert "Xem bình luận cũ hơn" not in cu and "<html" not in cu

    client.force_login(n["manager_sale"])
    client.post(f"/bang-tin/{bai.pk}/ghim/", {"ghim": "1"})
    bai.refresh_from_db()
    assert bai.is_pinned
    client.post(f"/bang-tin/{bai.pk}/ghim/", {"ghim": "1"})           # trang cũ bấm Ghim lần nữa: không đảo
    bai.refresh_from_db()
    assert bai.is_pinned
    client.post(f"/bang-tin/{bai.pk}/ghim/", {"ghim": "0"})
    bai.refresh_from_db()
    assert not bai.is_pinned


def test_thiep_sinh_nhat_bu_ngay_may_tat(nguoi_dung):
    """AC-13.4 — Máy tắt vài ngày thì khi bật lại đăng bù thiệp cho những ngày đó (tối đa 14 ngày), không đăng lại thiệp đã có, không đăng cho ngày tương lai"""
    from feed.tasks import thiep_sinh_nhat

    n = nguoi_dung
    hom_nay = timezone.localdate()
    _dat_sinh_nhat(n["staff_sale_1"], (hom_nay - timedelta(days=2)).replace(year=1996))
    _dat_sinh_nhat(n["staff_mkt"], (hom_nay - timedelta(days=1)).replace(year=1992))
    _dat_sinh_nhat(n["staff_vd"], hom_nay.replace(year=1988))
    _dat_sinh_nhat(n["staff_sale_2"], (hom_nay - timedelta(days=20)).replace(year=1996))   # quá 14 ngày: không bù

    assert post_service.catch_up_birthday_posts() == 1              # lần đầu chưa có thiệp: chỉ hôm nay
    # Giả lập máy tắt: thiệp mới nhất là của ba ngày trước
    Post.all_objects.filter(kind=PostKind.SINH_NHAT).update(
        birthday_on=hom_nay - timedelta(days=3), subject=n["staff_sale_1b"])
    assert post_service.catch_up_birthday_posts() == 3              # hai ngày trước, hôm qua, hôm nay
    assert post_service.catch_up_birthday_posts() == 0
    assert thiep_sinh_nhat() == 0
    assert set(Post.objects.filter(kind=PostKind.SINH_NHAT).values_list("subject_id", flat=True)) == {
        n["staff_sale_1b"].pk, n["staff_sale_1"].pk, n["staff_mkt"].pk, n["staff_vd"].pk,
    }
    with pytest.raises(CommandError):
        call_command("thiep_sinh_nhat", "--ngay", (hom_nay + timedelta(days=1)).isoformat(), stdout=StringIO())
