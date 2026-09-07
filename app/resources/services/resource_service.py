"""Quy tắc của Tài nguyên — FR-13.1 tới FR-13.4, ADR-015.

Tầng dịch vụ, không biết gì về HTTP (điều cấm 2). Mọi thao tác ghi đều ghi
nhật ký (BR-5) và nằm trong một giao dịch. Nhật ký không bao giờ chép nội
dung ghi chú — chỉ ghi "đã đổi".
"""
import re
import unicodedata

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Max, Q

from core.audit import record
from core.constants import LINK_SCHEMES, AuditAction, Rank
from core.exceptions import BusinessError, OutOfScopeError
from core.identity import display_name
from core.permissions import has_rank

from ..constants import (
    DEFAULT_CATEGORIES, LINK_MAX, NAME_MAX, NOTE_MAX, RESOURCE_FIELD_LABELS, SECRET_STRONG,
    SECRET_WEAK, ResourceStatus,
)
from ..models import Resource, ResourceCategory


# ══ QUYỀN ═════════════════════════════════════════════════════════

def can_manage(user):
    """Manager trở lên thêm, sửa, gỡ tài nguyên và thêm mục — FR-13.1, FR-13.3."""
    return has_rank(user, Rank.MANAGER)


def _phai_la_quan_ly(actor):
    if not can_manage(actor):
        raise OutOfScopeError("Chỉ quản lý trở lên sửa được danh mục tài nguyên.")


# ══ ĐỌC ═══════════════════════════════════════════════════════════

def categories():
    """Mục kèm số tài nguyên còn sống — một truy vấn."""
    return ResourceCategory.objects.annotate(
        so_tai_nguyen=Count("resources", filter=Q(resources__deleted_at__isnull=True)),
    )


def resources_qs():
    return Resource.objects.select_related("category", "holder", "holder__profile", "department")


def holders():
    """Ai giữ được tài nguyên: mọi tài khoản đang hoạt động có hồ sơ."""
    return (
        get_user_model().objects.filter(is_active=True, profile__isnull=False)
        .select_related("profile").order_by("profile__full_name", "username")
    )


# ══ KIỂM ══════════════════════════════════════════════════════════

def _mau(cac_tu):
    return "|".join(re.escape(unicodedata.normalize("NFC", t)) for t in cac_tu)


#: Từ mạnh đứng một mình là chặn; từ yếu phải kèm một giá trị có chữ số ngay sau
_MAU_MANH = re.compile(r"(?<!\w)(?:" + _mau(SECRET_STRONG) + r")(?!\w)")
_MAU_YEU = re.compile(
    r"(?<!\w)(?:" + _mau(SECRET_WEAK) + r")(?!\w)\s*(?:[:=\-]|là)?\s*\S*\d\S*"
)


def check_text(text, nhan="Ghi chú"):
    """Chuỗi không được chứa mật khẩu hay mã bí mật — FR-13.4. Là bộ lọc tốt
    nhất có thể, không phải bảo đảm: kho này không phải két sắt."""
    chuan = unicodedata.normalize("NFC", text or "").casefold()
    if _MAU_MANH.search(chuan) or _MAU_YEU.search(chuan):
        raise BusinessError(
            f"{nhan} không được chứa mật khẩu hay mã bí mật. "
            "Kho tài nguyên chỉ ghi có gì, ai giữ, tình trạng ra sao."
        )
    return (text or "").strip()


def check_note(note):
    """Ghi chú — giữ tên cũ cho chỗ gọi sẵn có."""
    note = check_text(note, "Ghi chú")
    if len(note) > NOTE_MAX:
        raise BusinessError(f"Ghi chú dài quá {NOTE_MAX} ký tự.")
    return note


def _lien_ket(link):
    """Liên kết chỉ nhận http(s) — kiểm ở dịch vụ, không trông vào form (XSS lưu trữ)."""
    link = check_text(link, "Liên kết")
    if link and not link.startswith(LINK_SCHEMES):
        raise BusinessError("Liên kết phải bắt đầu bằng http:// hoặc https://.")
    if len(link) > LINK_MAX:
        raise BusinessError(f"Liên kết dài quá {LINK_MAX} ký tự.")
    return link


def _ten(name):
    name = check_text(name, "Tên")
    if not name:
        raise BusinessError("Tên không được để trống.")
    if len(name) > NAME_MAX:
        raise BusinessError(f"Tên dài quá {NAME_MAX} ký tự.")
    return name


# ══ GHI — MỤC ═════════════════════════════════════════════════════

@transaction.atomic
def create_category(*, name, actor, request=None, order=None):
    """Thêm mục — Manager trở lên (FR-13.1). Không chỉ thứ tự thì xếp cuối."""
    _phai_la_quan_ly(actor)
    name = (name or "").strip()
    if not name:
        raise BusinessError("Tên mục không được để trống.")
    if ResourceCategory.objects.filter(name__iexact=name).exists():
        raise BusinessError(f"Đã có mục tên {name}.")
    if order is None:
        cuoi = ResourceCategory.objects.aggregate(m=Max("order"))["m"]
        order = 0 if cuoi is None else cuoi + 1
    muc = ResourceCategory.objects.create(name=name, order=order, created_by=actor)
    record(AuditAction.CREATE, actor=actor, target=muc, detail=f"Thêm mục tài nguyên {muc.name}", request=request)
    return muc


@transaction.atomic
def ensure_default_categories(*, actor=None, request=None):
    """Năm mục mặc định cho máy mới; đã có thì thôi. Trả về số mục mới."""
    moi = 0
    for thu_tu, ten in enumerate(DEFAULT_CATEGORIES):
        if ResourceCategory.objects.filter(name__iexact=ten).exists():
            continue
        muc = ResourceCategory.objects.create(name=ten, order=thu_tu, created_by=actor)
        record(AuditAction.CREATE, actor=actor, target=muc, detail=f"Thêm mục tài nguyên {ten}", request=request)
        moi += 1
    return moi


# ══ GHI — TÀI NGUYÊN ══════════════════════════════════════════════

@transaction.atomic
def create_resource(*, category, name, actor, request=None, note="", link="",
                    status=ResourceStatus.TRONG, holder=None, department=None):
    """Thêm tài nguyên — Manager trở lên (FR-13.3)."""
    _phai_la_quan_ly(actor)
    if category is None or category.deleted_at is not None:
        raise BusinessError("Chọn một mục trong danh sách.")
    if status not in ResourceStatus.values:
        raise BusinessError("Trạng thái không hợp lệ.")
    tn = Resource(
        category=category, name=_ten(name), note=check_note(note), link=_lien_ket(link),
        status=status, holder=holder, department=department, created_by=actor,
    )
    tn.full_clean(exclude=["created_by"])
    tn.save()
    record(
        AuditAction.CREATE, actor=actor, target=tn,
        detail=f"Thêm tài nguyên #{tn.pk} {tn.name} — mục {category.name}", request=request,
    )
    return tn


def _hien(truong, gia_tri):
    if truong in ("note", "link"):
        return "…"                      # không chép ghi chú hay liên kết vào nhật ký
    if truong == "status":
        return ResourceStatus(gia_tri).label if gia_tri else "—"
    if truong == "holder":
        return display_name(gia_tri) if gia_tri else "—"
    if gia_tri is None or gia_tri == "":
        return "—"
    return str(gia_tri)


@transaction.atomic
def update_resource(tn, *, actor, request=None, **thay_doi):
    """Sửa tài nguyên — Manager trở lên; nhật ký ghi từng trường đổi, trừ nội dung ghi chú."""
    _phai_la_quan_ly(actor)
    doi = []
    for truong, moi in thay_doi.items():
        if truong not in RESOURCE_FIELD_LABELS:
            raise BusinessError(f"Không sửa được trường {truong}.")
        if truong == "name":
            moi = _ten(moi)
        elif truong == "note":
            moi = check_note(moi)
        elif truong == "link":
            moi = _lien_ket(moi)
        elif truong == "status" and moi not in ResourceStatus.values:
            raise BusinessError("Trạng thái không hợp lệ.")
        elif truong == "category" and (moi is None or moi.deleted_at is not None):
            raise BusinessError("Chọn một mục trong danh sách.")
        cu = getattr(tn, truong)
        if cu == moi:
            continue
        setattr(tn, truong, moi)
        doi.append(f"{RESOURCE_FIELD_LABELS[truong]}: {_hien(truong, cu)} → {_hien(truong, moi)}")
    if not doi:
        return tn
    tn.full_clean(exclude=["created_by"])
    tn.save()
    record(
        AuditAction.UPDATE, actor=actor, target=tn,
        detail=f"Sửa tài nguyên #{tn.pk} — " + "; ".join(doi), request=request,
    )
    return tn


@transaction.atomic
def delete_resource(tn, *, actor, request=None):
    """Gỡ tài nguyên — xoá mềm (BR-4), Manager trở lên."""
    _phai_la_quan_ly(actor)
    tn.delete(by=actor)
    record(AuditAction.DELETE, actor=actor, target=tn, detail=f"Gỡ tài nguyên #{tn.pk} {tn.name}", request=request)
    return tn
