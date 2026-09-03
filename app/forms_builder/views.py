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
from django.core.exceptions import ValidationError
from django.http import Http404
from django.db.models import Count
from io import BytesIO

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.constants import IMPORT_MAX_ROWS, UPLOAD_MAX_BYTES, JobStatus, Rank
from core.exceptions import BusinessError, OutOfScopeError
from core.pagination import PAGE_SIZES, page_size, paginate
from core.audit import record_denied
from core.permissions import assert_rank, has_rank, is_admin

from . import query
from .forms import (
    ColumnForm, FieldDefForm, FormFieldForm, FormForm, GrantForm, TableForm,
)
from .models import (
    ColumnDef, DataRecord, FieldDef, FormDef, FormField, Grant, TableDef,
)
from .services import (
    export_service, form_service, grant_service, import_service, link_service,
    record_service, table_service,
)


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
        "form_quyen": GrantForm(cho_bang=True),
        "cac_quyen": grant_service.grants_of_table(bang_hien),
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
    """Đọc tham số lọc trên đường dẫn — bộ đọc chung với xuất tệp và Bảng tính."""
    return query.read_filters(request.GET, cac_cot)


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
        "duoc_nhap": grant_service.can_import(request.user, bang_hien),
        # Bảng chỉ xem ở đây, sửa ở Bảng tính — ADR-009
        "chi_xem": grant_service.is_grid_only(bang_hien),
        "bang_tinh_url": settings.BANGTINH_URL,
        # Quyền sửa tính theo **từng dòng**: người tạo dòng sửa được dòng của
        # mình, quản lý sửa cả bảng, và có thể có quyền cấp riêng
        "cac_dong": [
            (bg, query.read_row(bg, cac_cot),
             grant_service.can_edit_record(request.user, bg))
            for bg in boi_canh["page_obj"]
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
    if not grant_service.can_edit_record(request.user, ban_ghi):
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


# ══ NHẬP VÀ XUẤT TỆP — FR-7.5 tới FR-7.7 ═════════════════════════

def _bang_duoc_nhap(request, code):
    """Bảng trong phạm vi VÀ người này được nhập vào nó. Ngoài quyền → 403,
    ghi nhật ký từ chối (quy tắc 8, AC-3.6) — kể cả khi chỉ mở trang chọn tệp."""
    bang_hien = _lay_bang(request, code)
    if not grant_service.can_import(request.user, bang_hien):
        record_denied(request.user, request.path, request)
        raise OutOfScopeError("Bạn không có quyền nhập dữ liệu vào bảng này.")
    return bang_hien


@login_required
def bang_nhap(request, code):
    """Bước 1 của luồng nhập: chọn tệp. POST → kiểm tệp, ánh xạ cột, sang xem trước."""
    request.nav_current = "bang"
    bang_hien = _bang_duoc_nhap(request, code)
    if request.method == "POST":
        tep = request.FILES.get("tep")
        if tep is None:
            messages.error(request, "Chưa chọn tệp nào.")
        else:
            try:
                job = import_service.prepare(bang_hien, tep, actor=request.user, request=request)
                return redirect("bang_nhap_xem_truoc", code=code, pk=job.pk)
            except BusinessError as loi:
                messages.error(request, str(loi))
    return render(request, "forms_builder/bang_nhap.html", {
        "bang": bang_hien,
        "gioi_han_mb": UPLOAD_MAX_BYTES // (1024 * 1024), "gioi_han_dong": IMPORT_MAX_ROWS,
    })


@login_required
def bang_nhap_xem_truoc(request, code, pk):
    """Bước 2: xem cột nào khớp cột nào trước khi ghi. Tác vụ phải là của mình."""
    request.nav_current = "bang"
    bang_hien = _bang_duoc_nhap(request, code)
    job = import_service.job_for(request.user, pk, table=bang_hien)
    if job is None:
        raise Http404
    if job.status != JobStatus.DRAFT:
        return redirect("tac_vu_xem", pk=job.pk)
    tom_tat = job.summary
    return render(request, "forms_builder/bang_nhap_xem_truoc.html", {
        "bang": bang_hien, "job": job,
        "mapping": tom_tat.get("mapping", []), "ignored": tom_tat.get("ignored", []),
        "sample": tom_tat.get("sample", []),
        "so_dong_hien_co": import_service.record_count(bang_hien),
    })


@login_required
@require_POST
def bang_nhap_xac_nhan(request, code, pk):
    """Bước 3: xác nhận — từ đây mới bắt đầu ghi, và ghi ở tác vụ nền."""
    bang_hien = _bang_duoc_nhap(request, code)
    job = import_service.job_for(request.user, pk, table=bang_hien)
    if job is None:
        raise Http404
    try:
        import_service.confirm(job, actor=request.user, request=request)
    except BusinessError as loi:
        messages.error(request, str(loi))
    return redirect("tac_vu_xem", pk=job.pk)


@login_required
def bang_xuat(request, code):
    """Xuất bảng ra Excel đúng như đang hiện, kèm bộ lọc — FR-7.6, ADR-002.

    Ai xem được bảng thì xuất được; chỉ ra những dòng trong phạm vi của mình
    vì queryset đi qua `in_scope`.
    """
    bang_hien = _lay_bang(request, code)
    try:
        loai, ket_qua = export_service.export(request.user, bang_hien, request.GET, request=request)
    except BusinessError as loi:
        messages.error(request, str(loi))
        return redirect("bang_xem", code=code)
    if loai == "job":
        messages.info(
            request,
            f"Bảng có {ket_qua.total} dòng nên đang xuất ở tác vụ nền. "
            "Tệp sẵn sàng thì tải ở trang này, giữ trong 24 giờ.",
        )
        return redirect("tac_vu_xem", pk=ket_qua.pk)
    dem = BytesIO()
    ket_qua.save(dem)
    phan_hoi = HttpResponse(dem.getvalue(), content_type=export_service.XLSX_MIME)
    phan_hoi["Content-Disposition"] = (
        f'attachment; filename="{export_service.file_name(bang_hien)}"'
    )
    return phan_hoi


@login_required
@require_POST
def bang_cap_quyen(request, code):
    """Cấp quyền xem hoặc sửa một bảng cho người ngoài bộ phận — FR-8.4."""
    assert_rank(request.user, Rank.MANAGER, request)
    bang_hien = _lay_bang(request, code)

    form = GrantForm(request.POST, cho_bang=True)
    if form.is_valid():
        d = form.cleaned_data
        try:
            grant_service.grant(
                table=bang_hien, user=d["user"], team=d["team"],
                action=d["action"], actor=request.user, request=request,
            )
            messages.success(request, "Đã cấp quyền. Phiên đang mở của người đó đã bị đăng xuất.")
        except ValidationError as loi:
            messages.error(request, link_service.validation_message(loi))
    else:
        messages.error(request, _loi_dau_tien(form))
    return redirect("bang_cot", code=code)


@login_required
@require_POST
def bang_thu_quyen(request, code, pk):
    """Thu hồi một quyền đã cấp trên bảng."""
    assert_rank(request.user, Rank.MANAGER, request)
    bang_hien = _lay_bang(request, code)
    quyen = get_object_or_404(Grant, pk=pk, table=bang_hien)
    grant_service.revoke(quyen, actor=request.user, request=request)
    messages.success(request, "Đã thu quyền.")
    return redirect("bang_cot", code=code)


# ══ QUẢN LÝ BIỂU MẪU ══════════════════════════════════════════════

def _lay_bieu_mau(request, code):
    """Lấy biểu mẫu trong phạm vi quyền. Ngoài phạm vi thì 404."""
    return get_object_or_404(
        FormDef.objects.in_scope(request.user).select_related("department", "table"),
        code=code,
    )


def _loi_dau_tien(form):
    """Câu lỗi đầu tiên của một biểu mẫu, để đưa vào thanh thông báo."""
    for ds in form.errors.values():
        if ds:
            return ds[0]
    return "Dữ liệu chưa hợp lệ."


@login_required
def bieu_mau(request):
    """Danh sách biểu mẫu và thư viện định nghĩa trường.

    Đây là màn hình **quản lý**, không phải chỗ nhân viên vào điền. Ma trận
    kiểm chéo `docs/04` mục 3 ghi rõ chỉ Manager trở lên vào được.
    Nhân viên điền biểu mẫu qua màn hình Nộp báo cáo ngày.
    """
    request.nav_current = "bieu_mau"
    assert_rank(request.user, Rank.MANAGER, request)

    ds = (FormDef.objects.in_scope(request.user)
          .select_related("department", "table", "created_by", "created_by__profile")
          .annotate(so_truong=Count("fields", distinct=True))
          .order_by("name"))

    tim = request.GET.get("tim", "").strip()
    if tim:
        ds = ds.filter(name__icontains=tim)

    ho_so = getattr(request.user, "profile", None)
    thu_vien = FieldDef.objects.all()
    if not is_admin(request.user) and ho_so is not None:
        thu_vien = thu_vien.filter(department=ho_so.department)

    boi_canh = {
        "tim": tim,
        "duoc_sua": _duoc_sua_bang(request.user),
        "thu_vien": thu_vien.select_related("department").order_by("name"),
    }
    boi_canh.update(_phan_trang(request, ds, "biểu mẫu"))
    return render(request, "forms_builder/bieu_mau.html", boi_canh)


@login_required
def bieu_mau_moi(request):
    """Tạo biểu mẫu mới, chọn bảng đích — FR-8.1, FR-8.3."""
    request.nav_current = "bieu_mau"
    assert_rank(request.user, Rank.MANAGER, request)

    ho_so = getattr(request.user, "profile", None)
    form = FormForm(request.POST or None, department=getattr(ho_so, "department", None))
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        moi = form_service.create_form(
            name=d["name"], code=d["code"], description=d["description"],
            department=ho_so.department, table=d["table"],
            actor=request.user, request=request,
        )
        messages.success(request, f"Đã tạo biểu mẫu {moi.name}. Giờ thêm trường cho nó.")
        return redirect("bieu_mau_sua", code=moi.code)

    return render(request, "forms_builder/bieu_mau_form.html", {
        "form": form, "tieu_de": "Tạo biểu mẫu", "la_tao_moi": True,
    })


@login_required
def bieu_mau_sua(request, code):
    """Trình tạo biểu mẫu: thêm trường, nối cột đích, phân quyền."""
    request.nav_current = "bieu_mau"
    assert_rank(request.user, Rank.MANAGER, request)
    bm = _lay_bieu_mau(request, code)

    sua_pk = request.GET.get("truong")
    dang_sua = None
    if sua_pk:
        dang_sua = get_object_or_404(
            FormField.objects.select_related("field", "link"),
            pk=sua_pk, form=bm,
        )

    form = FormFieldForm(request.POST or None, form_def=bm, instance=dang_sua)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        try:
            if dang_sua:
                form_service.update_field(
                    dang_sua, {"required": d["required"], "column": d["column"]},
                    actor=request.user, request=request,
                )
                messages.success(request, f"Đã sửa trường {dang_sua.field.name}.")
            else:
                truong = form_service.add_field(
                    bm, d["field"], column=d["column"], required=d["required"],
                    actor=request.user, request=request,
                )
                messages.success(request, f"Đã thêm trường {truong.field.name}.")
            return redirect("bieu_mau_sua", code=bm.code)
        except ValidationError as loi:
            messages.error(request, link_service.validation_message(loi))

    cac_truong = list(bm.ordered_fields())
    da_noi, tong, loi_noi = link_service.summary(bm, cac_truong)
    return render(request, "forms_builder/bieu_mau_sua.html", {
        "bm": bm, "form": form, "dang_sua": dang_sua, "cac_truong": cac_truong,
        "da_noi": da_noi, "tong_truong": tong, "loi_noi": loi_noi,
        "form_quyen": GrantForm(cho_bang=False),
        "cac_quyen": grant_service.grants_of_form(bm),
    })


@login_required
@require_POST
def bieu_mau_bo_truong(request, code, pk):
    """Bỏ một trường khỏi biểu mẫu. Không đụng tới dữ liệu đã nhập — FR-8.5."""
    assert_rank(request.user, Rank.MANAGER, request)
    bm = _lay_bieu_mau(request, code)
    truong = get_object_or_404(FormField, pk=pk, form=bm)
    ten = truong.field.name
    form_service.remove_field(truong, actor=request.user, request=request)
    messages.success(request, f"Đã bỏ trường {ten}. Dữ liệu đã nhập vẫn còn nguyên.")
    return redirect("bieu_mau_sua", code=code)


@login_required
def truong_moi(request):
    """Thêm một định nghĩa trường vào thư viện dùng chung của bộ phận."""
    request.nav_current = "bieu_mau"
    assert_rank(request.user, Rank.MANAGER, request)

    ho_so = getattr(request.user, "profile", None)
    form = FieldDefForm(request.POST or None, department=getattr(ho_so, "department", None))
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        form_service.create_field_def(
            name=d["name"], code=d["code"], field_type=d["field_type"],
            meaning=d["meaning"], hint=d["hint"],
            default_value=d["default_value"], department=ho_so.department,
            actor=request.user, request=request,
        )
        messages.success(request, f"Đã thêm trường {d['name']} vào thư viện.")
        quay_ve = request.GET.get("ve")
        if quay_ve:
            return redirect("bieu_mau_sua", code=quay_ve)
        return redirect("bieu_mau")

    return render(request, "forms_builder/truong_form.html", {
        "form": form, "tieu_de": "Thêm định nghĩa trường",
        "quay_ve": request.GET.get("ve", ""),
    })


@login_required
@require_POST
def bieu_mau_cap_quyen(request, code):
    """Cấp quyền điền biểu mẫu cho người ngoài bộ phận — FR-8.4."""
    assert_rank(request.user, Rank.MANAGER, request)
    bm = _lay_bieu_mau(request, code)

    form = GrantForm(request.POST, cho_bang=False)
    if form.is_valid():
        d = form.cleaned_data
        try:
            grant_service.grant(
                form=bm, user=d["user"], team=d["team"], action=d["action"],
                actor=request.user, request=request,
            )
            messages.success(request, "Đã cấp quyền điền biểu mẫu.")
        except ValidationError as loi:
            messages.error(request, link_service.validation_message(loi))
    else:
        messages.error(request, _loi_dau_tien(form))
    return redirect("bieu_mau_sua", code=code)


@login_required
@require_POST
def bieu_mau_thu_quyen(request, code, pk):
    """Thu hồi quyền điền biểu mẫu."""
    assert_rank(request.user, Rank.MANAGER, request)
    bm = _lay_bieu_mau(request, code)
    quyen = get_object_or_404(Grant, pk=pk, form=bm)
    grant_service.revoke(quyen, actor=request.user, request=request)
    messages.success(request, "Đã thu quyền.")
    return redirect("bieu_mau_sua", code=code)


# ══ ĐIỀN BIỂU MẪU ═════════════════════════════════════════════════

@login_required
def bieu_mau_dien(request, code):
    """Nhập một dòng dữ liệu qua biểu mẫu — FR-8.2, FR-8.3.

    Đây là chỗ khiến bảng động dùng được thật. Quyền kiểm ở máy chủ **trước**
    khi đọc dữ liệu (P1, FR-3.6): gọi thẳng đường dẫn vẫn bị chặn.
    """
    request.nav_current = "bieu_mau"
    bm = _lay_bieu_mau(request, code)

    if not grant_service.can_fill(request.user, bm):
        raise OutOfScopeError("Bạn không được phân quyền điền biểu mẫu này.")
    if not bm.is_active:
        raise OutOfScopeError("Biểu mẫu này đã ngừng dùng.")

    cac_truong = list(bm.ordered_fields())
    du_lieu, loi = {}, []

    if request.method == "POST":
        du_lieu = {t.field.code: request.POST.get(t.field.code, "").strip()
                   for t in cac_truong}
        thieu = form_service.missing_required(bm, du_lieu, cac_truong)
        if thieu:
            loi.append("Chưa điền các trường bắt buộc: " + ", ".join(thieu))
        else:
            try:
                record_service.create_record(
                    bm.table, form_service.values_by_column(bm, du_lieu, cac_truong),
                    actor=request.user, request=request,
                )
                messages.success(request, "Đã lưu một dòng vào bảng " + bm.table.name)
                return redirect("bieu_mau_dien", code=bm.code)
            except BusinessError as e:
                loi.append(str(e))

    return render(request, "forms_builder/bieu_mau_dien.html", {
        "bm": bm, "cac_truong": cac_truong, "du_lieu": du_lieu, "loi": loi,
        # Chưa nhập gì thì điền sẵn giá trị mặc định của định nghĩa trường
        "cac_o": [(t, du_lieu.get(t.field.code) or t.field.default_value)
                  for t in cac_truong],
    })
