"""Bảng tính — lưới làm việc kiểu Excel trên mọi bảng động (ADR-009, ADR-010).

Bảng lấy qua `TableDef.objects.in_scope` (quy tắc 11): ngoài phạm vi → 404,
đúng như màn hình Bảng dữ liệu. Bảng vận đơn ở dịch vụ chính chỉ xem
(`GRID_ONLY_TABLES` có `van_don`), ở dịch vụ `bangtinh` sửa được — cùng mã,
chỉ khác cấu hình. Quyền sửa ô và thêm dòng kiểm ở máy chủ, không phải chỉ ẩn nút.
"""
from io import BytesIO
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, QueryDict
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST, require_http_methods

from core.audit import record_denied
from core.constants import GRID_PAGE_SIZE, Rank
from core.exceptions import BusinessError, OutOfScopeError
from core.pagination import PAGE_SIZES, page_size, paginate
from core.permissions import has_rank
from forms_builder.models import DataRecord, TableDef
from forms_builder.services import export_service, grant_service, record_service
from orders.constants import WAYBILL_TABLE_CODE

from .services import grid_service, sidebar_service


def _cac_bang(user):
    """Mọi bảng người này thấy được — thanh bên liệt kê, bảng mặc định chọn từ đây."""
    return TableDef.objects.in_scope(user).select_related("department").order_by("name")


def _bang(request, code):
    """Bảng trong phạm vi quyền; ngoài phạm vi → 404, như `bang_xem`."""
    request.nav_current = "bang_tinh"
    return get_object_or_404(_cac_bang(request.user), code=code)


def _ma_bang_mac_dinh(user):
    """`/bang-tinh/` mở bảng vận đơn nếu người này thấy nó, không thì bảng đầu
    tiên trong phạm vi; không có bảng nào thì 404 kèm lời giải thích."""
    cac = _cac_bang(user)
    if cac.filter(code=WAYBILL_TABLE_CODE).exists():
        return WAYBILL_TABLE_CODE
    dau = cac.first()
    if dau is None:
        raise Http404("Chưa có bảng nào trong phạm vi của bạn.")
    return dau.code


def _qs_khac(params, bo_khoa=()):
    return grid_service.qs_without(params, bo_khoa)


def _ngoai(duong_dan):
    """Địa chỉ ở dịch vụ chính — Bảng tính có thể chạy ở dịch vụ riêng (ADR-009)."""
    return settings.MAIN_APP_URL.rstrip("/") + duong_dan


def _qs_hien_tai(request):
    """Chuỗi lọc của trang đang mở, đọc từ URL mà HTMX gửi kèm — để ô trả về
    sau khi sửa vẫn mang liên kết lọc đúng bộ lọc hiện tại."""
    hien_tai = request.headers.get("HX-Current-URL", "")
    return _qs_khac(QueryDict(urlsplit(hien_tai).query))


@login_required
def bang_tinh(request):
    """Bảng tính mặc định — bảng vận đơn, hoặc bảng đầu tiên trong phạm vi."""
    return bang_tinh_xem(request, _ma_bang_mac_dinh(request.user))


@login_required
def bang_tinh_xem(request, code):
    """Lưới một bảng: lọc theo cột, sắp xếp, phân trang 100 dòng, sửa ô tại chỗ,
    dòng trống để thêm, thanh lọc bên trái, thanh công cụ."""
    bang = _bang(request, code)
    luoi = grid_service.build_grid(request.user, request.GET, table=bang)
    trang = paginate(request, luoi.queryset, default_size=GRID_PAGE_SIZE)
    qs_loc = _qs_khac(request.GET)
    chips = [
        (nhan, "?" + _qs_khac(request.GET, bo_khoa=(khoa,)))
        for khoa, nhan in luoi.chips
    ]
    vd = luoi.is_waybill
    duoc_them = grant_service.can_create_record(request.user, bang)
    return render(request, "crm/bang_tinh.html", {
        "bang": bang, "luoi": luoi, "cac_cot": luoi.columns, "la_van_don": vd,
        "cac_tieu_de": grid_service.header_columns(luoi.columns, luoi.filters, waybill=vd),
        "cac_dong": grid_service.rows(trang.object_list, luoi.columns, request.user, waybill=vd),
        "cac_dong_trong": grid_service.spare_rows(luoi.columns, waybill=vd) if duoc_them else [],
        "page_obj": trang, "moi_trang": page_size(request, default=GRID_PAGE_SIZE),
        "cac_co_trang": PAGE_SIZES, "ten_don_vi": "vận đơn" if vd else "dòng",
        "qs_loc": ("&" + qs_loc) if qs_loc else "",
        "qs_giu": qs_loc,
        "chips": chips,
        "chi_xem": grant_service.is_grid_only(bang),
        "duoc_them_dong": duoc_them,
        "duoc_sua_cot": has_rank(request.user, Rank.MANAGER),
        "duoc_nhap": grant_service.can_import(request.user, bang),
        "bang_du_lieu_url": _ngoai(f"/bang/{bang.code}/"),
        "nhap_url": _ngoai(f"/bang/{bang.code}/nhap/"),
        "sua_cot_url": _ngoai(f"/bang/{bang.code}/cot/"),
        "so_cot_co_dinh": len(grid_service.frozen_columns(luoi.columns, waybill=vd)),
        "cot_khoa": luoi.key_column,
        "ben": sidebar_service.context(request.user, bang, luoi.columns, request.GET),
        "cac_bang": _cac_bang(request.user),
    })


@login_required
def bang_tinh_loc_cot(request, code, ma_cot):
    """Mảnh HTMX: hộp lọc của một cột — danh sách giá trị kèm số đếm, hoặc
    khoảng, hoặc chứa chữ; luôn có Trống / Có giá trị."""
    bang = _bang(request, code)
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
                and k not in grid_service.SYSTEM_PARAMS and k != "q" for v in request.GET.getlist(k)],
    })


@login_required
@require_http_methods(["GET", "POST"])
def bang_tinh_o(request, code, pk, ma_cot):
    """Một ô: GET trả trình sửa (hoặc ô hiển thị khi `?hien=1`), POST lưu.

    Quyền kiểm ở máy chủ: ngoài phạm vi → 404; bảng chỉ xem ở dịch vụ này →
    403 (AC-11.7); giá trị ngoài danh sách → 400 kèm lý do (AC-11.3).
    """
    bang = _bang(request, code)
    ban_ghi = get_object_or_404(
        DataRecord.objects.in_scope(request.user).select_related("table"), pk=pk, table=bang,
    )
    vd = grid_service.is_waybill(bang)
    cac_cot = grid_service.display_columns(bang)
    cot = next((c for c in cac_cot if c.code == ma_cot), None)
    if cot is None:
        raise Http404
    co_dinh = dict((ma, (trai, rong)) for ma, trai, rong in grid_service.frozen_columns(cac_cot, waybill=vd))
    cd = co_dinh.get(ma_cot)
    lech = grid_service.DUPLICATE_COLUMN_WIDTH if vd else 0
    kieu = (ban_ghi.style or {}).get(ma_cot)
    boi_canh = {
        "bang": bang, "ban_ghi": ban_ghi, "cot": cot, "qs_giu": _qs_hien_tai(request),
        "gia_tri": ban_ghi.data.get(ma_cot), "duoc_sua": True,
        "lop": grid_service.cell_class(cot, cd, True, style=kieu),
        "style": grid_service.frozen_style(cd, offset=lech),
        "lop_sua": grid_service.cell_class(cot, cd, True, editing=True),
    }
    if request.GET.get("hien"):
        sua = grant_service.can_edit_record(request.user, ban_ghi)
        boi_canh.update(duoc_sua=sua, lop=grid_service.cell_class(cot, cd, sua, style=kieu))
        return render(request, "crm/_o.html", boi_canh)
    if not grant_service.can_edit_record(request.user, ban_ghi):
        raise OutOfScopeError("Bảng này chỉ xem ở đây, sửa ở Bảng tính.")

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
@require_POST
def bang_tinh_dong_moi(request, code):
    """Dòng trống cuối lưới: gõ vào rồi rời đi là thành bản ghi thật — ADR-010.

    Trả về `<tr>` thật của dòng vừa tạo kèm một `<tr>` trống mới; sai thì trả
    lại dòng trống với giá trị đã gõ và lý do, mã 400. Không quyền → 403 có
    ghi nhật ký (AC-11.14).
    """
    bang = _bang(request, code)
    if not grant_service.can_create_record(request.user, bang):
        record_denied(request.user, request.path, request)
        raise OutOfScopeError("Bạn không thêm được dòng vào bảng này.")
    vd = grid_service.is_waybill(bang)
    cac_cot = grid_service.display_columns(bang)
    gia_tri = {
        c.code: (request.POST.get(c.code) or "").strip()
        for c in cac_cot if not c.is_computed
    }
    da_dien = {k: v for k, v in gia_tri.items() if v != ""}
    boi_canh = {"bang": bang, "la_van_don": vd, "cac_cot": cac_cot}

    loi = ""
    if not da_dien:
        loi = "Dòng trống, chưa có gì để lưu."
    else:
        try:
            ban_ghi = record_service.create_record(
                bang, da_dien, actor=request.user, request=request, columns=cac_cot,
            )
        except BusinessError as e:
            loi = str(e)
        else:
            ds = (DataRecord.objects.in_scope(request.user)
                  .select_related("table", "created_by").filter(pk=ban_ghi.pk))
            if vd:
                ds = ds.annotate(so_trung=grid_service.duplicate_count(bang))
            moi = ds.first() or ban_ghi
            html = render_to_string("crm/_dong.html", {
                **boi_canh, "qs_giu": _qs_hien_tai(request),
                "d": grid_service.row_context(moi, cac_cot, request.user, waybill=vd),
            }, request) + render_to_string("crm/_dong_moi.html", {
                **boi_canh, "dong": grid_service.spare_rows(cac_cot, 1, waybill=vd)[0],
                "lop_dong": "dong-moi",
            }, request)
            return HttpResponse(html)

    # Tô ô của cột được nhắc tên trong lời báo lỗi, nếu có
    cot_loi = next((c.code for c in cac_cot if c.name and c.name in loi), None)
    dong = grid_service.spare_rows(cac_cot, 1, waybill=vd, values=gia_tri, error_column=cot_loi)[0]
    return render(request, "crm/_dong_moi.html", {
        **boi_canh, "dong": dong, "loi": loi, "lop_dong": "dong-moi dong-moi-loi",
    }, status=400)


@login_required
def bang_tinh_xuat(request, code):
    """Xuất đúng lưới đang lọc ra Excel — cùng đường với Bảng dữ liệu (ADR-002),
    cộng hai bộ lọc riêng của lưới qua builder `grid`."""
    bang = _bang(request, code)
    try:
        loai, ket_qua = export_service.export(
            request.user, bang, request.GET, request=request, builder="grid",
        )
    except BusinessError as loi:
        messages.error(request, str(loi))
        return redirect("bang_tinh_xem", code=bang.code)
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
