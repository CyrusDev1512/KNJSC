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

from . import query, styling
from .forms import (
    ColumnForm, FieldDefForm, FormFieldForm, FormForm, GrantForm, TableForm,
)
from .models import (
    ColumnDef, DataRecord, FieldDef, FormDef, FormField, Grant, TableDef,
)
from .services import (
    choice_service, export_service, form_service, grant_service, import_service,
    link_service, record_service, table_service,
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
    """Ai được tạo và sửa cấu trúc bảng — FR-8.1 giao cho Manager trở lên;
    ADR-015 mở cho Leader (quản lý của bộ phận)."""
    return has_rank(user, Rank.LEADER)


def _kiem_sua_cau_truc(request, bang_hien):
    """Sửa cột: quản lý của bộ phận sở hữu bảng hoặc Admin — ADR-015. Bảng
    chỉ được cấp quyền xem từ bộ phận khác thì không đổi cấu trúc được
    (403 có nhật ký), cùng luật với chèn/bỏ cột trên lưới (AC-11.22)."""
    if not grant_service.can_manage_columns(request.user, bang_hien):
        record_denied(request.user, request.path, request)
        raise OutOfScopeError("Chỉ quản lý của bộ phận sở hữu bảng mới sửa được cột.")


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
    """Tạo bảng mới — FR-8.1; Leader trở lên (ADR-015)."""
    request.nav_current = "bang"
    assert_rank(request.user, Rank.LEADER, request)

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
    """Thêm và sửa cột của một bảng — quản lý của bộ phận sở hữu (ADR-015)."""
    request.nav_current = "bang"
    assert_rank(request.user, Rank.LEADER, request)
    bang_hien = _lay_bang(request, code)
    _kiem_sua_cau_truc(request, bang_hien)

    sua_pk = request.GET.get("cot")
    dang_sua = None
    if sua_pk:
        dang_sua = get_object_or_404(ColumnDef, pk=sua_pk, table=bang_hien)

    form = ColumnForm(request.POST or None, instance=dang_sua, table=bang_hien)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        if dang_sua:
            # ModelForm đã ghi giá trị mới vào `dang_sua` lúc kiểm, nên đưa
            # bản gốc từ cơ sở dữ liệu vào dịch vụ — không thì dịch vụ so
            # "cũ với mới" thấy giống nhau và lặng lẽ không lưu gì
            goc = ColumnDef.objects.get(pk=dang_sua.pk)
            table_service.update_column(
                goc, d, actor=request.user, request=request)
            messages.success(request, f"Đã sửa cột {goc.name}." + _bao_tinh_lai(goc))
        else:
            cot = table_service.add_column(
                bang_hien, actor=request.user, request=request, **d)
            messages.success(request, f"Đã thêm cột {cot.name}." + _bao_tinh_lai(cot))
        return redirect("bang_cot", code=bang_hien.code)

    return render(request, "forms_builder/bang_cot.html", {
        "bang": bang_hien, "form": form, "dang_sua": dang_sua,
        "cac_cot": bang_hien.columns.order_by("order", "id"),
        "form_quyen": GrantForm(cho_bang=True),
        "cac_quyen": grant_service.grants_of_table(bang_hien),
    })


def _bao_tinh_lai(cot):
    """Bảng lớn thì cột tính lại ở tác vụ nền (ADR-016) — nói rõ để Manager không tưởng lỗi."""
    job = getattr(cot, "resync_job", None)
    if job is None:
        return ""
    return (f" Bảng có {job.total} dòng nên giá trị đang được tính lại ở tác vụ nền #{job.pk}; "
            "lưới báo tiến độ và tự cập nhật khi xong.")


@login_required
@require_POST
def bang_xoa_cot(request, code, pk):
    """Bỏ một cột khỏi bảng — quản lý của bộ phận sở hữu (ADR-015)."""
    assert_rank(request.user, Rank.LEADER, request)
    bang_hien = _lay_bang(request, code)
    _kiem_sua_cau_truc(request, bang_hien)
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
    """Xem, lọc, sắp xếp và phân trang một bảng — FR-7.1 tới FR-7.4. Chỉ xem, không sửa ô (ADR-014)."""
    request.nav_current = "bang"
    bang_hien = _lay_bang(request, code)
    cac_cot = styling.decorate_columns(list(bang_hien.columns.order_by("order", "id")))

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
    # Bảng dữ liệu chỉ để xem với mọi bảng — ADR-014: không tính quyền sửa
    # từng dòng, không vẽ ô nhập; sửa số liệu là việc của KN CRM. Lớp CSS của
    # ô (màu cột, ngưỡng) tính sẵn ở styling để template chỉ in ra.
    cac_dong = [(bg, styling.row_cells(bg, cac_cot)) for bg in boi_canh["page_obj"]]
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
        # Nơi sửa duy nhất: lưới KN CRM của đúng bảng này — ADR-012, ADR-014
        "bang_tinh_url": settings.BANGTINH_URL.rstrip("/") + f"/bang-tinh/{bang_hien.code}/",
        "cac_dong": cac_dong,
    })
    return render(request, "forms_builder/bang_xem.html", boi_canh)


@login_required
@require_POST
def bang_them_lua_chon(request, code, ma_cot):
    """Thêm một giá trị vào danh sách chọn của cột, ngay tại ô chọn — FR-8.7, Q58.

    Trả về các `<option>` mới (mục vừa thêm được chọn sẵn) để trình duyệt chép
    vào mọi ô chọn cùng cột. Quyền kiểm ở máy chủ: Admin hoặc Manager bộ phận
    sở hữu bảng; người khác gửi thẳng thì bị từ chối và có nhật ký (FR-3.6).
    """
    bang_hien = _lay_bang(request, code)
    if not choice_service.can_manage_options(request.user, bang_hien):
        record_denied(request.user, request.path, request)
        raise OutOfScopeError(
            "Chỉ quản lý của bộ phận sở hữu bảng mới thêm được giá trị vào danh sách."
        )
    cot = get_object_or_404(bang_hien.columns, code=ma_cot)
    try:
        chuan = choice_service.add_option(
            cot, request.POST.get("nhan_moi", ""), actor=request.user, request=request,
        )
    except BusinessError as loi:
        return HttpResponse(str(loi), status=400)
    return render(request, "components/o_chon_muc.html", {
        "cac_muc": choice_service.items(choice_service.options_for(cot)),
        "gia_tri": chuan, "co_them": True,
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
        try:
            # Một đường với nộp báo cáo ngày: ép danh tính người điền (FR-4.6),
            # kiểm bắt buộc, ghi vào bảng đích
            form_service.fill(
                bm, du_lieu, actor=request.user, request=request, fields=cac_truong,
            )
            messages.success(request, "Đã lưu một dòng vào bảng " + bm.table.name)
            return redirect("bieu_mau_dien", code=bm.code)
        except BusinessError as e:
            loi.append(str(e))

    return render(request, "forms_builder/bieu_mau_dien.html", {
        "bm": bm, "cac_truong": cac_truong, "du_lieu": du_lieu, "loi": loi,
        # Ô nhập, ô chọn, ô danh tính — giá trị đang gõ hoặc mặc định của trường
        "cac_o": form_service.widgets(bm, cac_truong, du_lieu, user=request.user),
    })
