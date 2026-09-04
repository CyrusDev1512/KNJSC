"""Quyền cấp thêm cho từng người hoặc từng team — FR-8.4, FR-3.4.

`docs/03` mục 3.4: phạm vi = phần theo cấp bậc + phần được cấp thêm. Tệp này
là phần thứ hai.

**Vì sao không dùng `core.scope._granted_scope`.** Hàm đó trả về
`(bộ_phận, team)` — chở được "cấp thêm cả một bộ phận", nhưng không chở được
"người X xem được bảng Y". `core.managers.apply_scope` cũng chỉ biết ba đường
dẫn người sở hữu, team, bộ phận; không có chỗ cho danh tính của thứ được cấp.
Nên đây là cơ chế **thứ hai**, chạy song song, theo đúng tiền lệ
`TableDefQuerySet.in_scope` đã tự viết phạm vi riêng cho model không vừa khuôn.

Hai loại câu hỏi, hai cách trả lời khác nhau:

- *Ai xem bảng nào* — lọc queryset, dùng `granted_table_ids`
- *Ai điền biểu mẫu nào* — phép kiểm ở view, dùng `can_fill`. Không phải chuyện
  queryset, và phải chạy **trước** khi đọc dữ liệu (P1, FR-3.6)
"""
from django.conf import settings
from django.db import transaction
from django.db.models import Q

from core.audit import record
from core.constants import AuditAction, Rank
from core.permissions import is_admin

from ..models import Grant, GrantAction

#: Tên thuộc tính giữ bộ nhớ đệm trên đối tượng người dùng của một lượt yêu cầu
CACHE_ATTR = "_knjsc_grants"


def _grants_of(user):
    """Mọi quyền cấp thêm đang có hiệu lực của một người, dạng tập hợp.

    Lấy **một lần cho mỗi lượt yêu cầu** rồi giữ trên chính đối tượng `user`.
    Không đệm thì mỗi queryset có phạm vi là thêm một lệnh truy vấn, và bài
    AC-10.2 sẽ đỏ — đó là bài duy nhất bắt được lỗi này.

    Trả về tập các bộ ba `(loại, khoá chính, việc)`, ví dụ `("table", 3, "view")`.
    """
    da_co = getattr(user, CACHE_ATTR, None)
    if da_co is not None:
        return da_co

    ho_so = getattr(user, "profile", None)
    dieu_kien = Q(user=user)
    team_id = getattr(ho_so, "team_id", None)
    if team_id:
        dieu_kien |= Q(team_id=team_id)

    ds = (Grant.objects.filter(dieu_kien, deleted_at__isnull=True)
          .values_list("table_id", "form_id", "action"))
    tap = frozenset(
        ("table", ma_bang, viec) if ma_bang else ("form", ma_bieu_mau, viec)
        for ma_bang, ma_bieu_mau, viec in ds
    )
    try:
        setattr(user, CACHE_ATTR, tap)
    except AttributeError:      # đối tượng người dùng ẩn danh không gán được
        pass
    return tap


def clear_cache(user):
    """Bỏ bộ nhớ đệm. Gọi sau khi cấp hoặc thu quyền trong cùng một lượt."""
    if hasattr(user, CACHE_ATTR):
        delattr(user, CACHE_ATTR)


def granted_table_ids(user, action=GrantAction.VIEW):
    """Khoá chính các bảng người này được cấp quyền, ngoài phạm vi cấp bậc."""
    if not getattr(user, "is_authenticated", False):
        return frozenset()
    return frozenset(
        ma for loai, ma, viec in _grants_of(user)
        if loai == "table" and viec == action
    )


def granted_form_ids(user, action=GrantAction.FILL):
    """Khoá chính các biểu mẫu người này được cấp quyền."""
    if not getattr(user, "is_authenticated", False):
        return frozenset()
    return frozenset(
        ma for loai, ma, viec in _grants_of(user)
        if loai == "form" and viec == action
    )


# ══ CÁC PHÉP KIỂM Ở TẦNG VIEW ═════════════════════════════════════

def can_fill(user, form):
    """Người này điền được biểu mẫu kia không — FR-8.4.

    Trong bộ phận của biểu mẫu thì điền được; ngoài bộ phận thì phải có cấp
    quyền riêng.
    """
    if is_admin(user):
        return True
    ho_so = getattr(user, "profile", None)
    if ho_so is not None and ho_so.department_id == form.department_id:
        return True
    return form.pk in granted_form_ids(user, GrantAction.FILL)


def can_import(user, table):
    """Người này nhập được tệp vào bảng kia không — FR-7.5, backlog Q38.

    Nhập là tạo hàng nghìn dòng một lúc nên nghiêm hơn sửa ô: quản lý trở
    lên trong bộ phận sở hữu bảng, hoặc người/team được cấp quyền **sửa**
    trên bảng đó. Admin luôn được.
    """
    if is_admin(user):
        return True
    ho_so = getattr(user, "profile", None)
    if ho_so is None:
        return False
    if ho_so.department_id == table.department_id and ho_so.rank in (Rank.MANAGER, Rank.ADMIN):
        return True
    return table.pk in granted_table_ids(user, GrantAction.EDIT)


def is_grid_only(table):
    """Bảng chỉ xem ở màn hình Bảng dữ liệu, sửa ở Bảng tính — ADR-009.

    Đọc từ settings để dịch vụ `bangtinh` (danh sách rỗng) vẫn sửa được
    cùng một bảng; kiểm ở máy chủ, không phải chỉ ẩn nút.
    """
    return table.code in getattr(settings, "GRID_ONLY_TABLES", ())


def can_edit_record(user, record_obj):
    """Người này sửa được dòng dữ liệu kia không — FR-7.4.

    Ba đường: quản lý trở lên trong bộ phận sở hữu bảng, hoặc chính người tạo
    dòng, hoặc có cấp quyền sửa trên bảng đó. Bảng chỉ xem (ADR-009) thì
    không ai sửa được ở đây, kể cả Admin — chỗ sửa là Bảng tính.
    """
    if is_grid_only(record_obj.table):
        return False
    if is_admin(user):
        return True
    if record_obj.created_by_id == getattr(user, "pk", None):
        return True

    ho_so = getattr(user, "profile", None)
    if ho_so is None:
        return False

    cung_bo_phan = ho_so.department_id == record_obj.table.department_id
    if cung_bo_phan and ho_so.rank in (Rank.MANAGER, Rank.ADMIN):
        return True
    # Bảng dùng chung là hàng đợi việc của cả bộ phận: ai trong bộ phận đó
    # cũng sửa được. Bảng vận đơn là ví dụ — nhân viên Vận đơn không tạo dòng
    # nào nhưng chính họ là người cập nhật trạng thái giao hàng
    if cung_bo_phan and record_obj.table.is_shared:
        return True
    return record_obj.table_id in granted_table_ids(user, GrantAction.EDIT)


# ══ CẤP VÀ THU QUYỀN ══════════════════════════════════════════════

def _nguoi_bi_anh_huong(grant):
    """Hồ sơ của những người mà quyền này chạm tới."""
    from org.models import UserProfile

    if grant.user_id:
        return list(UserProfile.objects.filter(user_id=grant.user_id))
    return list(UserProfile.objects.filter(team_id=grant.team_id))


def _mat_hieu_luc_phien(grant):
    """Đổi quyền thì phiên đang mở phải mất hiệu lực ngay — P4, FR-1.5.

    Cơ chế `session_epoch` chỉ tự tăng khi đổi cột trên chính `UserProfile`
    (xem `org/models.py SESSION_SENSITIVE_FIELDS`). Quyền cấp thêm nằm ở bảng
    khác nên **không tự kích hoạt** — phải gọi tay ở đây.
    """
    for ho_so in _nguoi_bi_anh_huong(grant):
        ho_so.invalidate_sessions()
        ho_so.save(update_fields=["session_epoch"])


@transaction.atomic
def grant(*, table=None, form=None, user=None, team=None, action,
          actor=None, request=None):
    """Cấp quyền riêng cho một người hoặc một team."""
    quyen = Grant(
        table=table, form=form, user=user, team=team,
        action=action, granted_by=actor,
    )
    quyen.full_clean(exclude=["granted_by"])
    quyen.save()

    _mat_hieu_luc_phien(quyen)
    if user is not None:
        clear_cache(user)

    record(
        AuditAction.PERMISSION, actor=actor, target=quyen,
        detail=f"Cấp quyền — {quyen}", request=request,
    )
    return quyen


@transaction.atomic
def revoke(quyen, *, actor=None, request=None):
    """Thu hồi một quyền đã cấp. Đánh dấu xoá, không xoá cứng (BR-4)."""
    mo_ta = str(quyen)
    quyen.delete(by=actor)

    _mat_hieu_luc_phien(quyen)
    if quyen.user_id is not None:
        clear_cache(quyen.user)

    record(
        AuditAction.PERMISSION, actor=actor, target=quyen,
        detail=f"Thu quyền — {mo_ta}", request=request,
    )
    return quyen


def grants_of_table(table):
    """Các quyền đang có hiệu lực trên một bảng, để hiện lên màn hình."""
    return (Grant.objects.filter(table=table)
            .select_related("user", "team", "granted_by").order_by("-created_at"))


def grants_of_form(form):
    """Các quyền đang có hiệu lực trên một biểu mẫu."""
    return (Grant.objects.filter(form=form)
            .select_related("user", "team", "granted_by").order_by("-created_at"))
