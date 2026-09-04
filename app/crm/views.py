"""Bảng tính vận đơn — màn hình làm việc của bộ phận Vận đơn (ADR-009).

Mọi view kiểm bộ phận ở máy chủ trước khi đọc gì (quy tắc 8, AC-11.4): chỉ
bộ phận Vận đơn và Admin. Ở dịch vụ chính (`GRID_ONLY_TABLES` có `van_don`)
lưới chỉ xem; ở dịch vụ `bangtinh` thì sửa được — cùng mã, chỉ khác cấu hình.
"""
from io import BytesIO

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, QueryDict
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from core.constants import GRID_PAGE_SIZE
from core.exceptions import BusinessError, OutOfScopeError
from core.pagination import PAGE_SIZES, page_size, paginate
from core.permissions import assert_departments
from forms_builder.models import DataRecord
from forms_builder.services import export_service, grant_service, record_service
from orders.constants import WAYBILL_DEPARTMENT_CODE

from .services import grid_service

#: Tham số không phải bộ lọc — không chép vào biểu mẫu lọc, không thành chip
THAM_SO_HE_THONG = {"trang", "moi_trang"}


def _bang_cua_van_don(request):
    """Bảng vận đơn, sau khi chắc người này thuộc bộ phận Vận đơn hoặc Admin."""
    assert_departments(request.user, (WAYBILL_DEPARTMENT_CODE,), request)
    try:
        return grid_service.waybill_table()
    except BusinessError as loi:
        raise Http404(str(loi)) from loi


def _qs_khac(params, bo_khoa=()):
    """Chuỗi truy vấn của mọi tham số **trừ** các khoá cho trước — để một bộ
    lọc mới cộng dồn với bộ lọc cũ, và để chip "bỏ lọc" bỏ đúng một cái."""
    q = QueryDict("", mutable=True)
    for k in params.keys():
        if k in THAM_SO_HE_THONG or k in bo_khoa:
            continue
        q.setlist(k, params.getlist(k))
    return q.urlencode()


@login_required
def bang_tinh(request):
    """Lưới vận đơn: lọc theo cột, sắp xếp, phân trang 100 dòng, sửa ô tại chỗ."""
    request.nav_current = "bang_tinh"
    bang = _bang_cua_van_don(request)
    luoi = grid_service.build_grid(request.user, request.GET, table=bang)
    trang = paginate(request, luoi.queryset, default_size=GRID_PAGE_SIZE)
    qs_loc = _qs_khac(request.GET)
    chips = [
        (nhan, "?" + _qs_khac(request.GET, bo_khoa=(khoa,)))
        for khoa, nhan in luoi.chips
    ]
    return render(request, "crm/bang_tinh.html", {
        "bang": bang, "luoi": luoi, "cac_cot": luoi.columns,
        "cac_tieu_de": grid_service.header_columns(luoi.columns, luoi.filters),
        "cac_dong": grid_service.rows(trang.object_list, luoi.columns, request.user),
        "page_obj": trang, "moi_trang": page_size(request, default=GRID_PAGE_SIZE),
        "cac_co_trang": PAGE_SIZES, "ten_don_vi": "vận đơn",
        "qs_loc": ("&" + qs_loc) if qs_loc else "",
        "qs_giu": qs_loc,
        "chips": chips,
        "chi_xem": grant_service.is_grid_only(bang),
        "bang_du_lieu_url": settings.MAIN_APP_URL.rstrip("/") + f"/bang/{bang.code}/",
        "nhap_url": settings.MAIN_APP_URL.rstrip("/") + f"/bang/{bang.code}/nhap/",
        "so_cot_co_dinh": len(grid_service.frozen_columns(luoi.columns)),
    })


@login_required
def bang_tinh_loc_cot(request, ma_cot):
    """Mảnh HTMX: hộp lọc của một cột — danh sách giá trị kèm số đếm, hoặc
    khoảng, hoặc chứa chữ; luôn có Trống / Có giá trị."""
    bang = _bang_cua_van_don(request)
    cot = get_object_or_404(bang.columns, code=ma_cot)
    loai = grid_service.filter_kind(cot)
    q = (request.GET.get("q") or "").strip()
    bo_loc = {k: request.GET.getlist(k) for k in request.GET.keys() if k.startswith(f"f_{ma_cot}")}
    dang_chon = set(bo_loc.get(f"f_{ma_cot}__trong", []))
    return render(request, "crm/_loc_cot.html", {
        "bang": bang, "cot": cot, "loai": loai, "q": q,
        "tuy_chon": grid_service.filter_options(request.user, bang, cot, q) if loai == "danh_sach" else [],
        "dang_chon": dang_chon,
        "tu": request.GET.get(f"f_{ma_cot}__lon_bang", ""),
        "den": request.GET.get(f"f_{ma_cot}__nho_bang", ""),
        "chua": request.GET.get(f"f_{ma_cot}__chua", ""),
        "rong": f"f_{ma_cot}__rong" in request.GET,
        "co": f"f_{ma_cot}__co" in request.GET,
        # Giữ mọi tham số khác để bộ lọc cộng dồn
        "giu": [(k, v) for k in request.GET.keys() if not k.startswith(f"f_{ma_cot}")
                and k not in THAM_SO_HE_THONG and k != "q" for v in request.GET.getlist(k)],
    })


@login_required
@require_http_methods(["GET", "POST"])
def bang_tinh_o(request, pk, ma_cot):
    """Một ô: GET trả trình sửa (hoặc ô hiển thị khi `?hien=1`), POST lưu.

    Quyền kiểm ở máy chủ: ngoài bộ phận → 403; bảng chỉ xem ở dịch vụ này →
    403 (AC-11.7); giá trị ngoài danh sách → 400 kèm lý do (AC-11.3).
    """
    bang = _bang_cua_van_don(request)
    ban_ghi = get_object_or_404(
        DataRecord.objects.in_scope(request.user).select_related("table"), pk=pk, table=bang,
    )
    cac_cot = grid_service.display_columns(bang)
    cot = next((c for c in cac_cot if c.code == ma_cot), None)
    if cot is None:
        raise Http404
    co_dinh = dict((ma, (trai, rong)) for ma, trai, rong in grid_service.frozen_columns(cac_cot))
    cd = co_dinh.get(ma_cot)
    boi_canh = {
        "bang": bang, "ban_ghi": ban_ghi, "cot": cot,
        "gia_tri": ban_ghi.data.get(ma_cot), "duoc_sua": True,
        "lop": grid_service.cell_class(cot, cd, True), "style": grid_service.frozen_style(cd),
        "lop_sua": grid_service.cell_class(cot, cd, True, editing=True),
    }
    if request.GET.get("hien"):
        sua = grant_service.can_edit_record(request.user, ban_ghi)
        boi_canh.update(duoc_sua=sua, lop=grid_service.cell_class(cot, cd, sua))
        return render(request, "crm/_o.html", boi_canh)
    if not grant_service.can_edit_record(request.user, ban_ghi):
        raise OutOfScopeError("Bảng vận đơn chỉ sửa được ở Bảng tính.")

    if request.method == "POST":
        try:
            record_service.update_cell(
                ban_ghi, ma_cot, request.POST.get("gia_tri", ""),
                actor=request.user, request=request, columns=cac_cot,
            )
        except BusinessError as loi:
            boi_canh["loi"] = str(loi)
            boi_canh["lop_sua"] = grid_service.cell_class(cot, cd, True, editing=True, error=True)
            return render(request, "crm/_o_sua.html", _boi_canh_sua(bang, cot, boi_canh), status=400)
        boi_canh["gia_tri"] = ban_ghi.data.get(ma_cot)
        return render(request, "crm/_o.html", boi_canh)

    return render(request, "crm/_o_sua.html", _boi_canh_sua(bang, cot, boi_canh))


def _boi_canh_sua(bang, cot, boi_canh):
    danh_sach, chat = grid_service.choice_list(bang, cot)
    return {**boi_canh, "danh_sach": danh_sach, "chat": chat}


@login_required
def bang_tinh_xuat(request):
    """Xuất đúng lưới đang lọc ra Excel — cùng đường với Bảng dữ liệu (ADR-002)."""
    bang = _bang_cua_van_don(request)
    try:
        loai, ket_qua = export_service.export(request.user, bang, request.GET, request=request)
    except BusinessError as loi:
        messages.error(request, str(loi))
        return redirect("bang_tinh")
    if loai == "job":
        messages.info(
            request,
            f"Lưới có {ket_qua.total} dòng nên đang xuất ở tác vụ nền. Tệp sẵn sàng thì tải "
            "ở trang Tác vụ nền, giữ trong 24 giờ.",
        )
        return redirect("tac_vu_xem", pk=ket_qua.pk)
    dem = BytesIO()
    ket_qua.save(dem)
    phan_hoi = HttpResponse(dem.getvalue(), content_type=export_service.XLSX_MIME)
    phan_hoi["Content-Disposition"] = f'attachment; filename="{export_service.file_name(bang)}"'
    return phan_hoi
