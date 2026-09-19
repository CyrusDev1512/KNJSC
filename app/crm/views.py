"""Bảng tính — lưới làm việc kiểu Excel trên mọi bảng động (ADR-009, ADR-010).

Bảng lấy qua `TableDef.objects.in_scope` (quy tắc 11): ngoài phạm vi → 404,
đúng như màn hình Bảng dữ liệu. Bảng vận đơn ở dịch vụ chính chỉ xem
(`GRID_ONLY_TABLES` có `van_don`), ở dịch vụ `bangtinh` sửa được — cùng mã,
chỉ khác cấu hình. Quyền sửa ô và thêm dòng kiểm ở máy chủ, không phải chỉ ẩn nút.
"""
from io import BytesIO

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Count, Max
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from core.audit import record_denied
from core.constants import GRID_FILTER_OPTIONS_MAX, GRID_INSERT_COLUMNS_MAX, Rank
from core.exceptions import BusinessError, OutOfScopeError
from core.permissions import assert_rank, has_rank, in_departments
from core.navigation import SALES_ONLY
from forms_builder.models import DataRecord, Folder, TableDef
from forms_builder.services import export_service, folder_service, grant_service, table_service
from orders.constants import WAYBILL_TABLE_CODE, is_waybill_table
from orders.services import dispatch_service
from org.models import Department

from .services import grid_service, master_grid_service, tong_quan_service, tree_service


def _cac_bang(user):
    """Mọi bảng người này thấy được — thanh bên liệt kê, bảng mặc định chọn từ đây."""
    return TableDef.objects.in_scope(user).filter(is_active=True).select_related("department").order_by("name")


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






@login_required
def tong_quan(request):
    """Trang chủ KN CRM — tổng quan theo phạm vi quyền, có sidebar (ADR-015).

    Không có nút ←: về ERP bằng mục KN ERP. Từ đây bấm Bảng tính mới sang
    trang thư mục, rồi mới mở lưới.
    """
    request.nav_current = "tong_quan"
    boi_canh = tong_quan_service.tong_quan(request.user)
    boi_canh.update({
        "erp_url": _ngoai("/"),
        "duoc_tao_bang": has_rank(request.user, Rank.LEADER),
        "tao_bang_url": reverse("bang_moi"),
    })
    return render(request, "crm/tong_quan.html", boi_canh)


@login_required
def thu_muc(request):
    """Mục Bảng tính của KN CRM — trang thư mục: cây Bộ phận ▸ Quý ▸ Tháng ▸ bảng
    (ADR-012, ADR-015), có sidebar; bấm một bảng mới mở lưới toàn màn hình.

    Cây chỉ dựng từ phạm vi quyền; `bp` ngoài phạm vi trả 404 có nhật ký
    (quy tắc 8), không phải trang rỗng. Không có bảng nào thì cũng 404 kèm lời.
    """
    request.nav_current = "thu_muc"
    try:
        du_lieu = tree_service.build(
            request.user,
            bp_code=request.GET.get("bp", ""), quy_raw=request.GET.get("quy", ""),
            thang_raw=request.GET.get("thang", ""), tat_ca=request.GET.get("tat-ca") == "1",
        )
    except LookupError:
        record_denied(request.user, request.get_full_path(), request)
        raise Http404("Bộ phận này không có bảng nào trong phạm vi của bạn.")
    if du_lieu is None:
        raise Http404("Chưa có bảng nào trong phạm vi của bạn.")
    bp = du_lieu["bp"]
    request.nav_current = f"bp:{bp.code}"
    boi_canh = dict(du_lieu)
    boi_canh.update({
        "erp_url": _ngoai("/"),
        "duoc_quan_ly_thu_muc": has_rank(request.user, Rank.LEADER)
                                and grant_service.can_manage_folders(request.user, bp),
        "duoc_cap_quyen": has_rank(request.user, Rank.MANAGER),
        "cap_quyen_url": reverse("cap_quyen"),
        "tao_bang_url": reverse("bang_moi"),
    })
    return render(request, "crm/thu_muc.html", boi_canh)


def _chon_bang(request, *, tieu_de, mo_ta, duoc, url_name, nhan_nut, rong_mo_ta):
    """Trang chọn bảng dùng chung cho Nhập tệp và Cấp quyền: bảng trong phạm vi
    mà `duoc(user, bang)` đúng, kèm số dòng, mỗi hàng một nút hành động."""
    cac_bang = []
    for b in (TableDef.objects.in_scope(request.user).select_related("department")
              .with_visible_record_count(request.user).order_by("department__name", "name")):
        if duoc(request.user, b):
            b.url_hanh_dong = reverse(url_name, args=[b.code])
            cac_bang.append(b)
    return render(request, "crm/chon_bang.html", {
        "tieu_de": tieu_de, "mo_ta": mo_ta, "cac_bang": cac_bang, "nhan_nut": nhan_nut,
        "rong_tieu_de": "Không có bảng nào", "rong_mo_ta": rong_mo_ta,
        "duoc_tao_bang": has_rank(request.user, Rank.LEADER), "erp_url": _ngoai("/"),
    })


@login_required
def nhap_tep(request):
    """Mục Nhập tệp trên sidebar — Leader trở lên (ADR-015): chọn bảng rồi vào
    luồng nhập 4 bước của forms_builder chạy ngay trong KN CRM."""
    request.nav_current = "nhap_tep"
    assert_rank(request.user, Rank.LEADER, request)
    return _chon_bang(
        request, tieu_de="Nhập tệp", url_name="bang_nhap", nhan_nut="Nhập tệp",
        mo_ta="Chọn bảng để nhập Excel hay CSV. Chỉ hiện bảng bạn được nhập: bảng của bộ phận mình, hoặc bảng được cấp quyền sửa.",
        duoc=grant_service.can_import, rong_mo_ta="Bạn chưa được nhập vào bảng nào.",
    )


@login_required
def cap_quyen(request):
    """Mục Cấp quyền trên sidebar — Manager (ADR-015): chọn bảng của bộ phận
    mình rồi vào màn Cột kèm cấp quyền của forms_builder, ngay trong KN CRM."""
    request.nav_current = "cap_quyen"
    assert_rank(request.user, Rank.MANAGER, request)
    return _chon_bang(
        request, tieu_de="Cấp quyền", url_name="bang_cot", nhan_nut="Cột & cấp quyền",
        mo_ta="Chọn bảng của bộ phận mình để cấp quyền xem hay sửa cho người ngoài bộ phận, và sửa cột.",
        duoc=grant_service.can_manage_columns, rong_mo_ta="Bộ phận bạn chưa có bảng nào.",
    )


@login_required
def bang_tinh(request):
    """Bảng tính mặc định — bảng vận đơn, hoặc bảng đầu tiên trong phạm vi."""
    return bang_tinh_xem(request, _ma_bang_mac_dinh(request.user))


@login_required
def bang_tinh_xem(request, code):
    """Lưới một bảng: lọc theo cột, sắp xếp, phân trang 100 dòng, sửa ô tại chỗ,
    dòng trống để thêm, thanh lọc bên trái, thanh công cụ."""
    if code == WAYBILL_TABLE_CODE and not _cac_bang(request.user).filter(code=code).exists():
        if in_departments(request.user, SALES_ONLY):
            return redirect("waybill_create")
        raise OutOfScopeError("Bạn không có quyền xem bảng Vận đơn.")
    bang = _bang(request, code)
    from .master_views import shell
    return shell(request, bang)


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
    tuy_chon = grid_service.filter_options(request.user, bang, cot, q)
    return render(request, "crm/_loc_cot.html", {
        "bang": bang, "cot": cot, "loai": loai, "q": q,
        "tuy_chon": [(gt, so) for gt, so in tuy_chon if gt != ""],
        "so_trong": next((so for gt, so in tuy_chon if gt == ""), 0),
        "tran": GRID_FILTER_OPTIONS_MAX,
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
def bang_tinh_o(request, code, **kwargs):
    _bang(request, code)
    return _master_upgrade_required(request)


def _master_upgrade_required(request):
    return render(request, 'crm/_bao_loi.html', {'loi':
        'Bộ lưới đã cập nhật. Giữ lại nội dung chưa lưu rồi tải lại trang để lưu an toàn.'}, status=409)






@login_required
def bang_tinh_dong_moi(request, code, **kwargs):
    _bang(request, code)
    return _master_upgrade_required(request)


@login_required
def bang_tinh_dinh_dang(request, code, **kwargs):
    _bang(request, code)
    return _master_upgrade_required(request)


@login_required
def bang_tinh_luu_o(request, code, **kwargs):
    _bang(request, code)
    return _master_upgrade_required(request)




def _bao_loi(request, loi, status=400):
    return render(request, "crm/_bao_loi.html", {"loi": loi}, status=status)


@login_required
def bang_tinh_xoa_dong(request, code, **kwargs):
    _bang(request, code)
    return _master_upgrade_required(request)


@login_required
def bang_tinh_khoi_phuc_dong(request, code, **kwargs):
    _bang(request, code)
    return _master_upgrade_required(request)


def _kiem_quan_ly_cot(request, bang):
    assert_rank(request.user, Rank.LEADER, request)
    if not grant_service.can_manage_columns(request.user, bang):
        record_denied(request.user, request.path, request)
        raise OutOfScopeError("Chỉ quản lý của bộ phận sở hữu bảng mới thêm hay bỏ cột.")


@login_required
@require_POST
def bang_tinh_them_cot(request, code):
    """Chèn N cột chữ ngắn cạnh cột đang chọn — menu chuột phải, Manager của
    bộ phận sở hữu hoặc Admin (ADR-011). Trả JSON mã cột mới; lưới tải lại."""
    bang = _bang(request, code)
    _kiem_quan_ly_cot(request, bang)
    try:
        so = max(1, min(int(request.POST.get("so") or 1), GRID_INSERT_COLUMNS_MAX))
    except ValueError:
        so = 1
    canh = request.POST.get("canh") or None
    if canh and not bang.columns.filter(code=canh).exists():
        return _bao_loi(request, "Cột đứng cạnh không còn trong bảng — tải lại trang.")
    try:
        moi = table_service.insert_columns(
            bang, count=so, anchor=canh, after=request.POST.get("ben") != "trai",
            actor=request.user, request=request,
        )
    except (BusinessError, ValidationError) as e:
        return _bao_loi(request, str(e))
    return JsonResponse({"da_them": [c.code for c in moi]})


@login_required
@require_POST
def bang_tinh_xoa_cot(request, code):
    """Bỏ các cột đã chọn — menu chuột phải, Manager của bộ phận sở hữu hoặc
    Admin. Giá trị đã nhập vẫn nằm trong bản ghi (BR-4); cột khoá, cột là vế
    của cột tính sẵn và cột hệ thống của bảng vận đơn thì từ chối."""
    bang = _bang(request, code)
    _kiem_quan_ly_cot(request, bang)
    ma = [m for m in dict.fromkeys(request.POST.getlist("cot")) if m]
    if not ma:
        return _bao_loi(request, "Chưa chọn cột nào để bỏ.")
    cac = list(bang.columns.filter(code__in=ma))
    if len(cac) != len(ma):
        return _bao_loi(request, "Có cột không còn trong bảng — tải lại trang.")
    for c in cac:
        ly_do = table_service.removable_reason(c)
        if not ly_do and grid_service.is_waybill(bang) and (
            c.code in {cot[1] for cot in dispatch_service.WAYBILL_COLUMNS} or c.code.startswith(dispatch_service.PRODUCT_COLUMN_PREFIX)
        ):
            ly_do = f'"{c.name}" là cột theo tệp vận đơn thật, hệ thống quản lý.'
        if ly_do:
            return _bao_loi(request, ly_do)
    with transaction.atomic():
        for c in cac:
            table_service.remove_column(c, actor=request.user, request=request)
    return JsonResponse({"da_bo": ma})


@login_required
def bang_tinh_moi_nhat(request, code):
    """Mốc mới nhất của bảng trong phạm vi người xem — lưới hỏi mỗi
    `GRID_POLL_SECONDS` giây để tự cập nhật khi người khác sửa (ADR-011).
    Chỉ có thời điểm sửa gần nhất, số cột và tiến độ tác vụ tính lại cột (nếu
    có, ADR-016) — không có dữ liệu. Không đếm dòng: thêm, xoá mềm, khôi phục
    đều đổi `updated_at` (kể cả dòng đã xoá, nên lấy trên `all_objects`), mà
    COUNT(*) là quét cả bảng 100 tab × mỗi 8 giây (K27).
    """
    bang = _bang(request, code)                     # bảng ngoài phạm vi → 404 ở đây
    return JsonResponse(master_grid_service.latest_stamp(request.user, bang))




# ── Thư mục chứa bảng — ADR-010 ───────────────────────────────────

@login_required
@require_POST
def bang_tinh_an_cot(request, code):
    """Ẩn hoặc hiện cột với cả công ty — ADR-039, quản lý bảng hoặc Admin.

    Khác nút "Cột" của lưới vốn chỉ nhớ trong trình duyệt từng người. Không
    xoá gì: hiện lại là thấy đủ dữ liệu cũ. Trả JSON mã cột đã đổi; lưới tải lại.
    """
    bang = _bang(request, code)
    _kiem_quan_ly_cot(request, bang)
    ma = [m for m in dict.fromkeys(request.POST.getlist("cot")) if m]
    an = request.POST.get("an") != "0"
    try:
        da_doi = table_service.set_columns_hidden(bang, ma, an, actor=request.user, request=request)
    except BusinessError as loi:
        return _bao_loi(request, str(loi))
    return JsonResponse({"da_doi": da_doi, "an": an})


def _kiem_quan_ly_thu_muc(request, department):
    """Quản lý (Leader, Manager) của bộ phận đó hoặc Admin — ADR-015; không thì 403 có ghi nhật ký."""
    assert_rank(request.user, Rank.LEADER, request)
    if not grant_service.can_manage_folders(request.user, department):
        record_denied(request.user, request.path, request)
        raise OutOfScopeError("Chỉ quản lý của bộ phận này mới sắp xếp được thư mục.")


def _thu_muc(request, pk):
    return get_object_or_404(Folder.objects.in_scope(request.user).select_related("department"), pk=pk)


def _ve(request):
    """Quay về bảng đang mở (tham số `ve`), hoặc bảng mặc định."""
    ma = request.POST.get("ve", "")
    if ma and _cac_bang(request.user).filter(code=ma).exists():
        return redirect("bang_tinh_xem", code=ma)
    return redirect("bang_tinh")


@login_required
@require_POST
def thu_muc_moi(request):
    """Tạo thư mục: từ lưới (`ve` = bảng đang mở, thư mục thuộc bộ phận của
    bảng) hoặc từ trang chủ KN CRM (`bo_phan` = khoá bộ phận đang chọn)."""
    ma_bp = request.POST.get("bo_phan", "")
    if ma_bp:
        bo_phan = get_object_or_404(Department, pk=ma_bp)
        ve_trang_chu = tree_service.home_url(bo_phan, all_tables=True)
    else:
        bo_phan = _bang(request, request.POST.get("ve", "")).department
        ve_trang_chu = None
    _kiem_quan_ly_thu_muc(request, bo_phan)
    try:
        thu_muc = folder_service.create_folder(
            name=request.POST.get("name", ""), department=bo_phan,
            actor=request.user, request=request,
        )
    except BusinessError as loi:
        messages.error(request, str(loi))
    else:
        messages.success(request, f"Đã tạo thư mục {thu_muc.name}.")
    return redirect(ve_trang_chu) if ve_trang_chu else _ve(request)


@login_required
@require_POST
def thu_muc_sua(request, pk):
    thu_muc = _thu_muc(request, pk)
    _kiem_quan_ly_thu_muc(request, thu_muc.department)
    try:
        folder_service.rename_folder(thu_muc, request.POST.get("name", ""), actor=request.user, request=request)
    except BusinessError as loi:
        messages.error(request, str(loi))
    else:
        messages.success(request, f"Đã đổi tên thư mục thành {thu_muc.name}.")
    return _ve(request)


@login_required
@require_POST
def thu_muc_xoa(request, pk):
    thu_muc = _thu_muc(request, pk)
    _kiem_quan_ly_thu_muc(request, thu_muc.department)
    ten = thu_muc.name
    so_bang = folder_service.delete_folder(thu_muc, actor=request.user, request=request)
    messages.success(request, f"Đã xoá thư mục {ten}; {so_bang} bảng về không thư mục.")
    return _ve(request)


@login_required
@require_POST
def bang_tinh_chuyen_thu_muc(request, code):
    """Xếp bảng đang mở vào một thư mục cùng bộ phận (rỗng = bỏ ra ngoài)."""
    bang = _bang(request, code)
    _kiem_quan_ly_thu_muc(request, bang.department)
    ma_thu_muc = request.POST.get("folder", "")
    thu_muc = _thu_muc(request, ma_thu_muc) if ma_thu_muc else None
    try:
        folder_service.move_table(bang, thu_muc, actor=request.user, request=request)
    except BusinessError as loi:
        messages.error(request, str(loi))
    else:
        messages.success(request, f"Bảng {bang.name} giờ ở {thu_muc.name if thu_muc else 'không thư mục'}.")
    return redirect("bang_tinh_xem", code=bang.code)


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
