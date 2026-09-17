"""Dữ liệu trình bày tab Tài liệu; tái sử dụng service và phạm vi hiện có."""
from django.http import Http404
from core.constants import Rank
from core.permissions import has_rank, is_admin
from core.pagination import filter_query, pagination_context
from org.models import Department
from .services import document_service

def _bo_phan_tao_muc(user):
    """Bộ phận mà người này được tạo mục: Admin mọi bộ phận, Manager bộ phận mình."""
    if is_admin(user):
        return Department.objects.all()
    ho_so = getattr(user, "profile", None)
    if ho_so is None or ho_so.department_id is None:
        return Department.objects.none()
    return Department.objects.filter(pk=ho_so.department_id)


def document_list_context(request):
    """Danh sách tài liệu trong phạm vi, lọc theo mục và tiêu đề — FR-9.1, FR-9.3."""
    cac_muc = list(document_service.categories_of(request.user))
    ds = document_service.documents_of(request.user)

    muc_chon = request.GET.get("muc", "").strip()
    tim = request.GET.get("tim", "").strip()
    muc_hien = None
    if muc_chon:
        # Mục ngoài phạm vi thì 404, không phải danh sách rỗng (quy tắc 8)
        muc_hien = next((m for m in cac_muc if str(m.pk) == muc_chon), None)
        if muc_hien is None:
            raise Http404
        ds = ds.filter(category=muc_hien)
    if tim:
        ds = ds.filter(title__icontains=tim)

    qs_loc = filter_query(tab="documents", muc=muc_hien.pk if muc_hien else "", tim=tim)

    boi_canh = pagination_context(request, ds, "tài liệu")
    boi_canh.update({
        "cac_muc": cac_muc, "muc_hien": muc_hien, "tim": tim, "qs_loc": qs_loc,
        "tong_tai_lieu": sum(m.so_tai_lieu for m in cac_muc),
        "duoc_tai_len": has_rank(request.user, Rank.MANAGER),
        "cac_bo_phan_muc": _bo_phan_tao_muc(request.user) if has_rank(request.user, Rank.MANAGER) else [],
        "la_admin": is_admin(request.user),
        "cac_dong": [
            (doc, document_service.can_manage_document(request.user, doc))
            for doc in boi_canh["page_obj"]
        ],
    })
    return boi_canh


