"""Tài liệu chia theo mục — FR-9.1 tới FR-9.5, ADR-017.

Mỗi bài phân quyền kiểm **cả hai chiều**: được phép và bị từ chối.
"""
import io
import os
import time
import zipfile
from pathlib import Path

import pytest
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from core.constants import UPLOAD_MAX_BYTES, AuditAction, FileKind
from core.exceptions import BusinessError, OutOfScopeError
from core.models import AuditLog
from documents.constants import DOCUMENT_SUBDIR
from documents.models import Document, DocumentCategory
from documents.services import document_service

pytestmark = pytest.mark.django_db

PDF = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"


def _zip(ten_trong):
    """ZIP nhỏ nhất có đúng tệp đặc trưng của Word hay Excel — ZIP rác đổi đuôi không qua."""
    dem = io.BytesIO()
    with zipfile.ZipFile(dem, "w") as z:
        z.writestr(ten_trong, "<x/>")
    return dem.getvalue()


ZIP = _zip("word/document.xml")


def _tep(ten="quy-dinh.pdf", noi_dung=PDF):
    return SimpleUploadedFile(ten, noi_dung, content_type="application/octet-stream")


def _so(action):
    return AuditLog.objects.filter(action=action).count()


@pytest.fixture
def cac_muc(departments, nguoi_dung):
    return {
        "chung": document_service.create_category(
            name="Quy định chung", department=None, actor=nguoi_dung["admin"]),
        "sale": document_service.create_category(
            name="Quy trình Sale", department=departments["sale"], actor=nguoi_dung["manager_sale"]),
        "mkt": document_service.create_category(
            name="Tài liệu Marketing", department=departments["mkt"], actor=nguoi_dung["manager_mkt"]),
    }


@pytest.fixture
def cac_tai_lieu(cac_muc, nguoi_dung):
    lk = "https://docs.google.com/document/d/abc"
    return {
        "chung": document_service.upload_document(
            title="Nội quy công ty", category=cac_muc["chung"], link=lk, actor=nguoi_dung["admin"]),
        "sale": document_service.upload_document(
            title="Quy trình chốt đơn", category=cac_muc["sale"], link=lk, actor=nguoi_dung["manager_sale"]),
        "mkt": document_service.upload_document(
            title="Kế hoạch quảng cáo", category=cac_muc["mkt"], link=lk, actor=nguoi_dung["manager_mkt"]),
    }


# ══ AC-12.1 · Tạo mục và tải lên theo cấp bậc ═══════════════════════

def test_manager_tao_muc_va_tai_len_staff_bi_tu_choi(client, departments, cac_muc, nguoi_dung):
    """AC-12.1 — Manager tạo mục cho bộ phận mình và tải tệp lên mục trong phạm vi; Manager không tạo được mục toàn công ty, Admin tạo được; Staff và Leader gọi đường tải lên thì bị từ chối và có nhật ký"""
    ql = nguoi_dung["manager_sale"]
    client.force_login(ql)
    truoc = _so(AuditAction.CREATE)
    kq = client.post("/tai-lieu/muc-moi/", {"name": "Biểu mẫu Sale", "department": departments["sale"].pk})
    assert kq.status_code == 302
    assert DocumentCategory.objects.filter(name="Biểu mẫu Sale", department=departments["sale"]).exists()

    # Manager không tạo được mục toàn công ty, cũng không tạo cho bộ phận khác
    so_muc = DocumentCategory.objects.count()
    client.post("/tai-lieu/muc-moi/", {"name": "Mục chung của Sale", "department": ""})
    client.post("/tai-lieu/muc-moi/", {"name": "Lấn sân", "department": departments["mkt"].pk})
    assert DocumentCategory.objects.count() == so_muc
    with pytest.raises(BusinessError):
        document_service.create_category(name="Trùng tên", department=None, actor=ql)
    # Admin thì được
    client.force_login(nguoi_dung["admin"])
    assert client.post("/tai-lieu/muc-moi/", {"name": "Thông báo chung", "department": ""}).status_code == 302
    assert DocumentCategory.objects.filter(name="Thông báo chung", department__isnull=True).exists()

    # Manager tải tệp PDF thật lên mục của bộ phận mình
    client.force_login(ql)
    assert client.get("/tai-lieu/tai-len/").status_code == 200
    kq = client.post("/tai-lieu/tai-len/", {
        "category": cac_muc["sale"].pk, "title": "Quy định hoa hồng", "description": "Bản 2026",
        "file": _tep("hoa-hong.pdf"),
    })
    assert kq.status_code == 302, kq.content[:300]
    doc = Document.objects.get(title="Quy định hoa hồng")
    assert doc.file_kind == FileKind.PDF and doc.file_name == "hoa-hong.pdf"
    assert doc.department_id == departments["sale"].pk and doc.created_by == ql
    assert doc.file_path.startswith(f"{DOCUMENT_SUBDIR}/")
    assert (Path(settings.STORAGE_DIR) / doc.file_path).read_bytes() == PDF
    assert _so(AuditAction.CREATE) == truoc + 3          # hai mục + một tài liệu

    # Staff và Leader không tải lên được, cả GET lẫn POST, và có nhật ký từ chối
    for ma in ("staff_sale_1", "leader_sale_1"):
        client.force_login(nguoi_dung[ma])
        tu_choi = _so(AuditAction.DENIED)
        assert client.get("/tai-lieu/tai-len/").status_code == 403, ma
        assert client.post("/tai-lieu/tai-len/", {
            "category": cac_muc["sale"].pk, "title": "Lén", "file": _tep(),
        }).status_code == 403, ma
        assert client.post("/tai-lieu/muc-moi/", {"name": "Lén", "department": departments["sale"].pk}).status_code == 403
        assert _so(AuditAction.DENIED) == tu_choi + 3, ma
    assert not Document.objects.filter(title="Lén").exists()


# ══ AC-12.2 · Phạm vi xem và tải về ═════════════════════════════════

def test_pham_vi_xem_theo_muc(client, cac_muc, cac_tai_lieu, nguoi_dung):
    """AC-12.2 — Staff thấy tài liệu toàn công ty và của bộ phận mình, không thấy của bộ phận khác; gọi thẳng đường tải về tài liệu bộ phận khác trả 404; Admin thấy tất cả"""
    client.force_login(nguoi_dung["staff_sale_1"])
    kq = client.get("/tai-lieu/")
    assert kq.status_code == 200
    html = kq.content.decode()
    assert "Nội quy công ty" in html and "Quy trình chốt đơn" in html
    assert "Kế hoạch quảng cáo" not in html and "Tài liệu Marketing" not in html

    # Tải về: tài liệu trong phạm vi chỉ có liên kết thì chuyển tới liên kết
    kq = client.get(f"/tai-lieu/{cac_tai_lieu['sale'].pk}/tai/")
    assert kq.status_code == 302 and kq["Location"].startswith("https://docs.google.com/")
    # Ngoài phạm vi: 404, không lộ là có tài liệu
    assert client.get(f"/tai-lieu/{cac_tai_lieu['mkt'].pk}/tai/").status_code == 404
    assert client.get(f"/tai-lieu/?muc={cac_muc['mkt'].pk}").status_code == 404
    assert client.get(f"/tai-lieu/?muc={cac_muc['sale'].pk}").status_code == 200

    # Vận đơn chỉ thấy mục toàn công ty
    client.force_login(nguoi_dung["staff_vd"])
    html = client.get("/tai-lieu/").content.decode()
    assert "Nội quy công ty" in html and "Quy trình chốt đơn" not in html

    # Admin thấy cả ba
    client.force_login(nguoi_dung["admin"])
    html = client.get("/tai-lieu/").content.decode()
    assert all(t in html for t in ("Nội quy công ty", "Quy trình chốt đơn", "Kế hoạch quảng cáo"))
    assert client.get(f"/tai-lieu/{cac_tai_lieu['mkt'].pk}/tai/").status_code == 302

    # Tìm theo tiêu đề
    html = client.get("/tai-lieu/?tim=chốt").content.decode()
    assert "Quy trình chốt đơn" in html and "Nội quy công ty" not in html


# ══ AC-12.3 · Kiểm tệp và liên kết ══════════════════════════════════

def test_tep_sai_bi_tu_choi_lien_ket_hop_le(cac_muc, nguoi_dung):
    """AC-12.3 — Tệp đổi đuôi, sai loại hoặc quá 10 MB bị từ chối; Word nhận theo đuôi khai báo; tài liệu chỉ có liên kết tạo được, thiếu cả hai hoặc liên kết sai giao thức thì từ chối"""
    ql, muc = nguoi_dung["manager_sale"], cac_muc["sale"]
    goi = lambda **k: document_service.upload_document(title="Thử", category=muc, actor=ql, **k)

    with pytest.raises(BusinessError):
        goi(upload=_tep("virus.pdf", b"MZ\x90\x00" + b"\x00" * 40))     # nội dung lạ
    with pytest.raises(BusinessError):
        goi(upload=_tep("doi-duoi.docx", PDF))                          # PDF khai là Word
    with pytest.raises(BusinessError):
        goi(upload=_tep("chay.exe", ZIP))                               # đuôi ngoài danh sách
    with pytest.raises(BusinessError) as loi:
        goi(upload=_tep("to.pdf", PDF + b"\x00" * UPLOAD_MAX_BYTES))
    assert "vượt giới hạn" in str(loi.value)
    assert Document.objects.count() == 0

    doc = goi(upload=_tep("quy-trinh.docx", ZIP))
    assert doc.file_kind == FileKind.DOCX and doc.file_size == len(ZIP)

    with pytest.raises(BusinessError):
        goi()                                                           # không tệp, không liên kết
    with pytest.raises(BusinessError):
        goi(link="ftp://noi-khac")
    lk = goi(link="https://drive.google.com/x")
    assert lk.la_lien_ket and lk.file_path == ""
    with pytest.raises(BusinessError):
        goi(link="https://drive.google.com/x", title="   ") if False else document_service.upload_document(
            title="   ", category=muc, link="https://a.b", actor=ql)
    # Mục ngoài phạm vi thì từ chối kể cả Manager
    with pytest.raises(OutOfScopeError):
        document_service.upload_document(
            title="Lấn", category=cac_muc["mkt"], link="https://a.b", actor=ql)


# ══ AC-12.4 · Gỡ tài liệu ════════════════════════════════════════════

def test_go_tai_lieu_theo_quyen(client, cac_muc, cac_tai_lieu, nguoi_dung):
    """AC-12.4 — Người tải, Manager của bộ phận và Admin gỡ được tài liệu (xoá mềm, có nhật ký); người khác bị từ chối có nhật ký; ngoài phạm vi là 404"""
    doc = cac_tai_lieu["sale"]
    duong = f"/tai-lieu/{doc.pk}/go/"

    client.force_login(nguoi_dung["staff_sale_1"])
    tu_choi = _so(AuditAction.DENIED)
    assert client.post(duong).status_code == 403
    assert _so(AuditAction.DENIED) == tu_choi + 1
    assert client.get(duong).status_code == 405

    client.force_login(nguoi_dung["manager_mkt"])
    assert client.post(duong).status_code == 404               # ngoài phạm vi

    client.force_login(nguoi_dung["manager_sale"])
    xoa = _so(AuditAction.DELETE)
    assert client.post(duong).status_code == 302
    assert not Document.objects.filter(pk=doc.pk).exists()
    assert Document.all_objects.get(pk=doc.pk).deleted_by == nguoi_dung["manager_sale"]
    assert _so(AuditAction.DELETE) == xoa + 1
    assert client.post(duong).status_code == 404               # đã gỡ thì không thấy nữa

    # Admin gỡ được tài liệu của bộ phận khác; người tải gỡ được của mình
    client.force_login(nguoi_dung["admin"])
    assert client.post(f"/tai-lieu/{cac_tai_lieu['mkt'].pk}/go/").status_code == 302
    client.force_login(nguoi_dung["manager_mkt"])
    moi = document_service.upload_document(
        title="Của tôi", category=cac_muc["chung"], link="https://a.b", actor=nguoi_dung["manager_mkt"])
    assert client.post(f"/tai-lieu/{moi.pk}/go/").status_code == 302


# ══ AC-12.5 · Tệp không bị dọn ═══════════════════════════════════════

def test_tep_tai_lieu_khong_bi_don_sau_24_gio(cac_muc, nguoi_dung):
    """AC-12.5 — Tệp tài liệu nằm ở storage/tai-lieu/ và không bị tác vụ dọn tệp 24 giờ xoá"""
    from core.tasks import don_tep_xuat_qua_han

    doc = document_service.upload_document(
        title="Cũ", category=cac_muc["sale"], upload=_tep(), actor=nguoi_dung["manager_sale"])
    tep = Path(settings.STORAGE_DIR) / doc.file_path
    assert tep.parent == Path(settings.STORAGE_DIR) / DOCUMENT_SUBDIR
    cu = time.time() - 3 * 24 * 3600
    os.utime(tep, (cu, cu))
    don_tep_xuat_qua_han()
    assert tep.exists()


def test_man_hinh_tai_lieu_khong_qua_muoi_lenh_truy_van(client, cac_tai_lieu, nguoi_dung, django_assert_max_num_queries):
    """AC-10.2 — Màn hình Tài liệu chạy không quá 10 lệnh truy vấn, với Admin lẫn Leader phải lọc theo bộ phận"""
    for vai in ("admin", "leader_sale_1", "staff_vd"):
        client.force_login(nguoi_dung[vai])
        client.get("/tai-lieu/")
        with django_assert_max_num_queries(10):
            assert client.get("/tai-lieu/").status_code == 200, vai


# ══ Dịch vụ tự kiểm quyền; mục mới không nổ — rà soát 07.09 ═════════

def test_dich_vu_tu_kiem_quyen_va_muc_moi_khong_no(client, cac_muc, nguoi_dung):
    """AC-12.4 — Gọi thẳng tầng dịch vụ: nhân viên tải lên hay người không có quyền gỡ đều bị từ chối, không trông vào view; tệp và liên kết cùng lúc bị từ chối; thêm mục với mã bộ phận không phải số trả 404, không 500; ZIP rác đổi đuôi .docx bị từ chối"""
    n = nguoi_dung
    goi = document_service.upload_document
    with pytest.raises(OutOfScopeError):
        goi(title="Lậu", category=cac_muc["chung"], link="https://vi.du/a", actor=n["staff_sale_1"])
    with pytest.raises(BusinessError):
        goi(title="Hai thứ", category=cac_muc["chung"], upload=_tep(), link="https://vi.du/a", actor=n["admin"])
    with pytest.raises(BusinessError):
        goi(title="Rác", category=cac_muc["chung"], upload=_tep("rac.docx", _zip("x.txt")), actor=n["admin"])
    doc = goi(title="Thật", category=cac_muc["chung"], link="https://vi.du/a", actor=n["admin"])
    with pytest.raises(OutOfScopeError):
        document_service.delete_document(doc, actor=n["manager_sale"])      # mục toàn công ty: chỉ Admin
    assert Document.objects.filter(pk=doc.pk).exists()

    client.force_login(n["manager_sale"])
    assert client.post("/tai-lieu/muc-moi/", {"name": "Mục lạ", "department": "abc"}).status_code == 404
    assert not DocumentCategory.objects.filter(name="Mục lạ").exists()


# ══ Tải về qua view, tệp mất trên đĩa, tên mục hoa thường — rà soát 07.09 ═

def test_tai_ve_qua_view_va_tep_mat_tren_dia(client, cac_muc, cac_tai_lieu, nguoi_dung):
    """AC-12.2 — Tải về đi qua view có kiểm quyền: tệp trả về dạng đính kèm đúng tên gốc và ghi một dòng nhật ký; mở liên kết chuyển tới liên kết và cũng ghi nhật ký; tệp mất trên đĩa thì báo lỗi rồi về danh sách, không 500, không nhật ký; tài liệu đã gỡ trả 404"""
    n = nguoi_dung
    doc = document_service.upload_document(
        title="Quy định nghỉ phép", category=cac_muc["chung"], upload=_tep(), actor=n["admin"])
    client.force_login(n["staff_vd"])
    xuat = _so(AuditAction.EXPORT)
    kq = client.get(f"/tai-lieu/{doc.pk}/tai/")
    assert kq.status_code == 200
    assert kq["Content-Disposition"].startswith("attachment") and "quy-dinh.pdf" in kq["Content-Disposition"]
    assert b"".join(kq.streaming_content) == PDF
    assert _so(AuditAction.EXPORT) == xuat + 1
    assert f"#{doc.pk}" in AuditLog.objects.filter(action=AuditAction.EXPORT).latest("created_at").detail

    lk = cac_tai_lieu["chung"]
    kq = client.get(f"/tai-lieu/{lk.pk}/tai/")
    assert kq.status_code == 302 and kq["Location"] == lk.link
    assert _so(AuditAction.EXPORT) == xuat + 2

    document_service.absolute_path(doc).unlink()                  # người vận hành lỡ xoá tệp
    kq = client.get(f"/tai-lieu/{doc.pk}/tai/", follow=True)
    assert kq.redirect_chain[-1][0] == "/tai-lieu/" and "Tệp không còn trên máy chủ" in kq.content.decode()
    assert _so(AuditAction.EXPORT) == xuat + 2

    document_service.delete_document(lk, actor=n["admin"])
    assert client.get(f"/tai-lieu/{lk.pk}/tai/").status_code == 404


def test_ten_muc_khong_phan_biet_hoa_thuong_o_tang_du_lieu(cac_muc, nguoi_dung, departments):
    """AC-12.1 — Tên mục chỉ khác hoa thường bị chặn ngay ở cơ sở dữ liệu (cùng bộ phận, hoặc cùng toàn công ty), không chỉ ở tầng dịch vụ; cùng tên ở bộ phận khác thì được; mục đã gỡ không giữ chỗ tên"""
    from django.db import IntegrityError, transaction

    n = nguoi_dung
    with pytest.raises(BusinessError):
        document_service.create_category(name="quy định chung", department=None, actor=n["admin"])
    with pytest.raises(IntegrityError), transaction.atomic():
        DocumentCategory.objects.create(name="quy định chung", department=None, created_by=n["admin"])
    with pytest.raises(IntegrityError), transaction.atomic():
        DocumentCategory.objects.create(name="quy trình sale", department=departments["sale"], created_by=n["admin"])
    khac_bp = DocumentCategory.objects.create(name="Quy trình Sale", department=departments["mkt"], created_by=n["admin"])
    assert khac_bp.pk
    DocumentCategory.objects.filter(pk=cac_muc["sale"].pk).delete(by=n["admin"])
    assert document_service.create_category(
        name="quy trình sale", department=departments["sale"], actor=n["manager_sale"]).pk != cac_muc["sale"].pk
