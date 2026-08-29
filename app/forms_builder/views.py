"""Màn hình bảng động.

View chỉ nhận yêu cầu, kiểm quyền, gọi tầng dịch vụ, trả kết quả (điều cấm 2).
Mọi truy vấn đi qua `objects.in_scope(user)` — không viết điều kiện lọc quyền
ở đây (quy tắc 11).

Hai tầng phạm vi khác nhau, đừng lẫn:

- `TableDef.objects.in_scope()` — ai thấy *định nghĩa* bảng nào
- `DataRecord.objects.in_scope()` — ai thấy *bản ghi* nào trong bảng đó
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.constants import Rank
from core.exceptions import BusinessError, OutOfScopeError
from core.pagination import PAGE_SIZES, page_size, paginate
from core.permissions import assert_rank, has_rank

from . import query
from .forms import ColumnForm, TableForm
from .models import ColumnDef, DataRecord, TableDef
from .services import record_service, table_service


def _phan_trang(request, queryset, ten_don_vi="dòng", param="trang", size_param="moi_trang"):
    """Bối cảnh dùng chung cho khối phân trang (quy tắc 1)."""
    trang = paginate(request, queryset, param=param, size_param=size_param)
    return {
        "page_obj": trang, "trang": trang,
        "moi_trang": page_size(request, size_param), "cac_co_trang": PAGE_SIZES,
        "ten_don_vi": ten_don_vi, "tham_so": param, "tham_so_co": size_param,
    }


def _lay_bang(request, code):
    """Lấy bảng trong phạm vi quyền. Ngoài phạm vi thì 404, không phải rỗng."""
    return get_object_or_404(
        TableDef.objects.in_scope(request.user).select_related("department"),
        code=code,
    )


def _duoc_sua_bang(user):
    """Ai được tạo và sửa cấu trúc bảng — FR-8.1 giao cho Manager trở lên."""
    return has_rank(user, Rank.MANAGER)


# ══ QUẢN LÝ BẢNG ══════════════════════════════════════════════════

@login_required
def bang(request):
    """Danh sách bảng dữ liệu trong phạm vi quyền."""
    request.nav_current = "bang"

    # distinct=True vì đếm hai quan hệ trong cùng một lệnh, không thì hai bảng
    # nhân chéo nhau và cả hai con số đều sai
    ds = (TableDef.objects.in_scope(request.user)
          .select_related("department", "created_by")
          .annotate(so_cot=Count("columns", distinct=True),
                    so_dong=Count("records", distinct=True))
          .order_by("name"))

    tim = request.GET.get("tim", "").strip()
    if tim:
        ds = ds.filter(name__icontains=tim)

    boi_canh = {
        "tim": tim,
        "duoc_sua": _duoc_sua_bang(request.user),
    }
    boi_canh.update(_phan_trang(request, ds, "bảng"))
    return render(request, "forms_builder/bang.html", boi_canh)


@login_required
def bang_moi(request):
    """Tạo bảng mới — FR-8.1."""
    request.nav_current = "bang"
    assert_rank(request.user, Rank.MANAGER, request)

    ho_so = getattr(request.user, "profile", None)
    form = TableForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        bang_moi_tao = table_service.create_table(
            name=d["name"], code=d["code"], description=d["description"],
            department=ho_so.department, actor=request.user, request=request,
        )
        messages.success(request, f"Đã tạo bảng {bang_moi_tao.name}. Giờ thêm cột cho nó.")
        return redirect("bang_cot", code=bang_moi_tao.code)

    return render(request, "forms_builder/bang_form.html", {
        "form": form, "tieu_de": "Tạo bảng dữ liệu", "la_tao_moi": True,
    })


@login_required
def bang_cot(request, code):
    """Thêm và sửa cột của một bảng."""
    request.nav_current = "bang"
    assert_rank(request.user, Rank.MANAGER, request)
    bang_hien = _lay_bang(request, code)

    sua_pk = request.GET.get("cot")
    dang_sua = None
    if sua_pk:
        dang_sua = get_object_or_404(ColumnDef, pk=sua_pk, table=bang_hien)

    form = ColumnForm(request.POST or None, instance=dang_sua, table=bang_hien)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        if dang_sua:
            table_service.update_column(
                dang_sua, d, actor=request.user, request=request)
            messages.success(request, f"Đã sửa cột {dang_sua.name}.")
        else:
            cot = table_service.add_column(
                bang_hien, actor=request.user, request=request, **d)
            messages.success(request, f"Đã thêm cột {cot.name}.")
        return redirect("bang_cot", code=bang_hien.code)

    return render(request, "forms_builder/bang_cot.html", {
        "bang": bang_hien, "form": form, "dang_sua": dang_sua,
        "cac_cot": bang_hien.columns.order_by("order", "id"),
    })


@login_required
@require_POST
def bang_xoa_cot(request, code, pk):
    """Bỏ một cột khỏi bảng."""
    assert_rank(request.user, Rank.MANAGER, request)
    bang_hien = _lay_bang(request, code)
    cot = get_object_or_404(ColumnDef, pk=pk, table=bang_hien)
    ten = cot.name
    table_service.remove_column(cot, actor=request.user, request=request)
    messages.success(request, f"Đã bỏ cột {ten}.")
    return redirect("bang_cot", code=code)


# ══ MÀN HÌNH BẢNG DỮ LIỆU ═════════════════════════════════════════

def _doc_bo_loc(request, cac_cot):
    """Đọc tham số lọc trên đường dẫn, chỉ nhận cột có thật."""
    ma_cot = {c.code for c in cac_cot}
    bo_loc = {}
    for khoa, gia_tri in request.GET.items():
        if not khoa.startswith("f_") or not gia_tri.strip():
            continue
        ten = khoa[2:]
        if ten.partition("__")[0] in ma_cot:
            bo_loc[ten] = gia_tri.strip()
    return bo_loc


@login_required
def bang_xem(request, code):
    """Xem, lọc, sắp xếp và phân trang một bảng — FR-7.1 tới FR-7.3."""
    request.nav_current = "bang"
    bang_hien = _lay_bang(request, code)
    cac_cot = list(bang_hien.columns.order_by("order", "id"))

    bo_loc = _doc_bo_loc(request, cac_cot)
    tim = request.GET.get("tim", "").strip()
    sap_xep = request.GET.get("sap", "")
    giam_dan = request.GET.get("chieu", "") == "giam"

    ds, ban_do_cot = query.build(
        DataRecord.objects.in_scope(request.user)
                          .select_related("table", "created_by"),
        bang_hien, filters=bo_loc, search=tim, sort=sap_xep,
        descending=giam_dan, columns=cac_cot,
    )

    boi_canh = _phan_trang(request, ds, "dòng")
    boi_canh.update({
        "bang": bang_hien, "cac_cot": cac_cot,
        # Ghép sẵn giá trị đang lọc vào từng cột — template không tra được
        # dict theo biến
        "cac_cot_loc": [
            {"cot": c, "gia_tri": bo_loc.get(c.code, "")}
            for c in cac_cot if ban_do_cot.is_indexed(c.code)
        ],
        "tim": tim, "sap_xep": sap_xep, "giam_dan": giam_dan,
        "duoc_sua": _duoc_sua_bang(request.user),
        "cac_dong": [
            (bg, query.read_row(bg, cac_cot)) for bg in boi_canh["page_obj"]
        ],
    })
    return render(request, "forms_builder/bang_xem.html", boi_canh)


@login_required
@require_POST
def bang_sua_o(request, code, pk, ma_cot):
    """Sửa đúng một ô, trả về mảnh HTML của ô đó — FR-7.4.

    Quyền kiểm ở máy chủ trước khi đọc dữ liệu, không phải ẩn nút trên giao
    diện (FR-3.6, nguyên tắc P1). Gọi thẳng đường dẫn này vẫn bị chặn.
    """
    bang_hien = _lay_bang(request, code)
    # Bản ghi phải nằm trong phạm vi quyền — lấy thẳng theo khoá chính là lộ
    # dữ liệu của người khác
    ban_ghi = get_object_or_404(
        DataRecord.objects.in_scope(request.user).select_related("table"),
        pk=pk, table=bang_hien,
    )
    if not _duoc_sua_bang(request.user) and ban_ghi.created_by_id != request.user.pk:
        raise OutOfScopeError("Bạn không có quyền sửa dòng này.")

    cac_cot = list(bang_hien.columns.order_by("order", "id"))
    try:
        record_service.update_cell(
            ban_ghi, ma_cot, request.POST.get("gia_tri", ""),
            actor=request.user, request=request, columns=cac_cot,
        )
    except BusinessError as loi:
        return HttpResponse(
            f'<td class="o-sua o-loi" title="{loi}">{loi}</td>', status=400,
        )

    cot = next(c for c in cac_cot if c.code == ma_cot)
    return render(request, "forms_builder/_o.html", {
        "bang": bang_hien, "ban_ghi": ban_ghi, "cot": cot,
        "gia_tri": ban_ghi.data.get(ma_cot),
        "duoc_sua": True,
    })
