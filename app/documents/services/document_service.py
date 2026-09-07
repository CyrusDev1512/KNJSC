"""Quy tắc của Tài liệu — FR-9.1 tới FR-9.5, ADR-015.

Tầng dịch vụ, không biết gì về HTTP (điều cấm 2). Mọi thao tác ghi đều ghi
nhật ký (BR-5) và nằm trong một giao dịch.
"""
import uuid
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.db.models import Count, Q

from core.audit import record
from core.constants import AuditAction, Rank
from core.exceptions import BusinessError, OutOfScopeError
from core.excel import check_size, sniff_kind
from core.permissions import has_rank, in_department, is_admin

from ..constants import (
    DESCRIPTION_MAX, DOCUMENT_FILE_KINDS, DOCUMENT_SUBDIR, FILE_NAME_MAX, LINK_SCHEMES,
    TITLE_MAX,
)
from ..models import Document, DocumentCategory


# ══ QUYỀN ═════════════════════════════════════════════════════════

def can_manage_category(user, department):
    """Ai tạo được mục: Admin mọi mục; Manager chỉ mục của bộ phận mình."""
    if is_admin(user):
        return True
    if department is None or not has_rank(user, Rank.MANAGER):
        return False
    return in_department(user, department.pk)


def can_manage_document(user, doc):
    """Ai gỡ được tài liệu: người tải, Manager của bộ phận đó, Admin — FR-9.4."""
    if is_admin(user) or doc.created_by_id == getattr(user, "pk", None):
        return True
    return (
        doc.department_id is not None
        and has_rank(user, Rank.MANAGER)
        and in_department(user, doc.department_id)
    )


# ══ ĐỌC ═══════════════════════════════════════════════════════════

def categories_of(user):
    """Mục trong phạm vi kèm số tài liệu còn sống — một truy vấn."""
    return (
        DocumentCategory.objects.in_scope(user)
        .select_related("department")
        .annotate(so_tai_lieu=Count("documents", filter=Q(documents__deleted_at__isnull=True)))
    )


def documents_of(user):
    return (
        Document.objects.in_scope(user)
        .select_related("category", "department", "created_by", "created_by__profile")
    )


def absolute_path(doc):
    return Path(settings.STORAGE_DIR) / doc.file_path if doc.file_path else None


# ══ GHI ═══════════════════════════════════════════════════════════

@transaction.atomic
def create_category(*, name, department, actor, request=None, order=0):
    """Tạo mục. Manager chỉ cho bộ phận mình; mục toàn công ty chỉ Admin — FR-9.1."""
    name = (name or "").strip()
    if not name:
        raise BusinessError("Tên mục không được để trống.")
    if department is None and not is_admin(actor):
        raise BusinessError("Chỉ quản trị viên tạo được mục dùng chung toàn công ty.")
    if not can_manage_category(actor, department):
        raise BusinessError("Bạn chỉ tạo được mục cho bộ phận của mình.")
    if DocumentCategory.objects.filter(department=department, name__iexact=name).exists():
        raise BusinessError(f'Mục "{name}" đã có rồi.')

    muc = DocumentCategory.objects.create(
        name=name, department=department, order=order, created_by=actor,
    )
    record(
        AuditAction.CREATE, actor=actor, target=muc,
        detail=f"Tạo mục tài liệu #{muc.pk} — {muc.pham_vi}", request=request,
    )
    return muc


def _luu_tep(upload, kind):
    """Lưu tệp vào `STORAGE_DIR/tai-lieu/`; trả đường dẫn tương đối — FR-9.5."""
    thu_muc = Path(settings.STORAGE_DIR) / DOCUMENT_SUBDIR
    thu_muc.mkdir(parents=True, exist_ok=True)
    ten = f"{uuid.uuid4().hex}.{kind}"
    upload.seek(0)
    with open(thu_muc / ten, "wb") as f:
        for doan in upload.chunks():
            f.write(doan)
    return f"{DOCUMENT_SUBDIR}/{ten}"


@transaction.atomic
def upload_document(*, title, category, upload=None, link="", description="",
                    actor, request=None):
    """Tải lên một tệp hoặc thêm một liên kết vào mục trong phạm vi — FR-9.2.

    Tệp kiểm cỡ và kiểm nội dung (NFR-11, NFR-12) trước khi ghi ra đĩa.
    """
    title = (title or "").strip()
    if not title:
        raise BusinessError("Tiêu đề không được để trống.")
    if len(title) > TITLE_MAX:
        raise BusinessError(f"Tiêu đề dài quá {TITLE_MAX} ký tự.")
    link = (link or "").strip()
    if upload is None and not link:
        raise BusinessError("Cần chọn tệp hoặc dán liên kết.")
    if link and not link.startswith(LINK_SCHEMES):
        raise BusinessError("Liên kết phải bắt đầu bằng http:// hoặc https://.")
    if not DocumentCategory.objects.in_scope(actor).filter(pk=category.pk).exists():
        raise OutOfScopeError("Mục này không thuộc phạm vi của bạn.")

    doc = Document(
        title=title, category=category, department=category.department,
        description=(description or "").strip()[:DESCRIPTION_MAX], link=link,
        created_by=actor,
    )
    if upload is not None:
        check_size(upload.size)
        kind = sniff_kind(upload, declared_name=upload.name, allowed=DOCUMENT_FILE_KINDS)
        doc.file_path = _luu_tep(upload, kind)
        doc.file_name = str(upload.name)[:FILE_NAME_MAX]
        doc.file_kind = kind
        doc.file_size = upload.size
    doc.save()
    record(
        AuditAction.CREATE, actor=actor, target=doc,
        detail=f"Tải lên tài liệu #{doc.pk} vào mục {category.name}"
               + (" (liên kết)" if doc.la_lien_ket else f" ({doc.file_kind}, {doc.file_size} byte)"),
        request=request,
    )
    return doc


@transaction.atomic
def delete_document(doc, *, actor, request=None):
    """Gỡ tài liệu: xoá mềm, tệp vẫn nằm trên đĩa để khôi phục được — FR-9.4."""
    doc.delete(by=actor)
    record(
        AuditAction.DELETE, actor=actor, target=doc,
        detail=f"Gỡ tài liệu #{doc.pk} khỏi mục {doc.category.name}", request=request,
    )
    return doc
