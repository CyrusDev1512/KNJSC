"""Màn hình báo cáo hằng ngày.

View chỉ nhận yêu cầu, kiểm quyền, gọi tầng dịch vụ (điều cấm 2). Phạm vi
quyền do `DailyReport.objects.in_scope` lo, không viết điều kiện lọc ở đây
(quy tắc 11).

**Không có view sửa báo cáo** — BR-2 và FR-4.4. Thiếu đường dẫn là cách chặn
chắc nhất; gọi thẳng cũng không có gì để gọi.
"""
from datetime import date
from io import BytesIO
from urllib.parse import urlencode

from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.exceptions import BusinessError
from core.pagination import pagination_context

from forms_builder.services import form_service

from . import aggregations, excel, marketing
from .services import daily_service, summary_service


def _ngay_bao_cao(chuoi):
    """Đọc ngày báo cáo trên biểu mẫu. Không hợp lệ thì lấy hôm nay."""
    try:
        return date.fromisoformat(chuoi)
    except (TypeError, ValueError):
        return timezone.localdate()


@login_required
def bao_cao_ngay(request):
    """Nộp báo cáo cho một ngày — FR-4.1, FR-4.2.

    Biểu mẫu đổi theo bộ phận: danh sách lấy qua `FormDef.objects.in_scope`
    nên mỗi bộ phận chỉ thấy biểu mẫu của mình (AC-4.1).
    """
    request.nav_current = "bao_cao_ngay"

    cac_bieu_mau = list(daily_service.forms_for(request.user))
    ma_chon = request.POST.get("bieu_mau") or request.GET.get("bieu_mau")
    bm = next((f for f in cac_bieu_mau if f.code == ma_chon), None)
    if bm is None and cac_bieu_mau:
        bm = cac_bieu_mau[0]

    ngay = _ngay_bao_cao(request.POST.get("ngay_bao_cao") or request.GET.get("ngay"))
    cac_truong = list(bm.ordered_fields()) if bm else []
    du_lieu, loi = {}, []

    if request.method == "POST" and bm is not None:
        du_lieu = {t.field.code: request.POST.get(t.field.code, "").strip()
                   for t in cac_truong}
        try:
            daily_service.submit(
                bm, du_lieu, report_date=ngay, actor=request.user,
                request=request, fields=cac_truong,
            )
            messages.success(
                request, f"Đã nộp báo cáo cho ngày {ngay:%d.%m.%Y}. Báo cáo đã khoá.")
            return redirect("bao_cao_lich_su")
        except BusinessError as e:
            loi.append(str(e))

    da_nop = bool(bm) and daily_service.already_submitted(bm, request.user, ngay)
    return render(request, "reports/bao_cao_ngay.html", {
        "cac_bieu_mau": cac_bieu_mau, "bm": bm, "ngay": ngay,
        # Ô nhập, ô chọn, ô danh tính — cùng bộ với màn hình điền biểu mẫu
        "cac_o": form_service.widgets(bm, cac_truong, du_lieu, user=request.user) if bm else [],
        "loi": loi, "da_nop": da_nop,
        "cac_cot_tinh": bm.table.computed_columns() if bm else [],
    })


@login_required
def bao_cao_lich_su(request):
    """Xem lại báo cáo cũ trong phạm vi quyền — FR-4.3, FR-4.5."""
    request.nav_current = "bao_cao_lich_su"

    ds = daily_service.history(request.user)

    tim = request.GET.get("tim", "").strip()
    if tim:
        ds = ds.filter(created_by__profile__full_name__icontains=tim)
    tu = request.GET.get("tu", "").strip()
    if tu:
        ds = ds.filter(report_date__gte=_ngay_bao_cao(tu))
    den = request.GET.get("den", "").strip()
    if den:
        ds = ds.filter(report_date__lte=_ngay_bao_cao(den))

    forms, departments = daily_service.history_choices(request.user)
    form_code = request.GET.get("bieu_mau", "").strip()
    dept_code = request.GET.get("bo_phan", "").strip()
    selected_form = get_object_or_404(forms, code=form_code) if form_code else None
    selected_dept = get_object_or_404(departments, code=dept_code) if dept_code else None
    if selected_form:
        ds = ds.filter(form=selected_form)
    if selected_dept:
        ds = ds.filter(department=selected_dept)
    boi_canh = {"tim": tim, "tu": tu, "den": den, "cac_bieu_mau": forms,
               "cac_bo_phan": departments, "bieu_mau": form_code, "bo_phan": dept_code}
    boi_canh.update(pagination_context(request, ds, "báo cáo"))
    daily_service.attach_marketing_links(boi_canh["trang"], forms, tu, den)
    return render(request, "reports/bao_cao_lich_su.html", boi_canh)


# ══ BÁO CÁO TỔNG HỢP — FR-5.1 tới FR-5.6 ═════════════════════════

def _tham_so_tong_hop(request):
    """Đọc bộ tham số chung của màn hình tổng hợp và đường xuất Excel.

    Trả về dict đã chuẩn hoá: tab lạ rơi về "tong-hop", ngày hỏng rơi về
    khoảng mặc định (đầu tháng tới hôm nay).
    """
    tab = request.GET.get("nhom", "").strip()
    if tab not in {ma for ma, _ in summary_service.TABS}:
        tab = "tong-hop"
    mac_tu, mac_den = summary_service.default_range()
    tu_tho = request.GET.get("tu", "").strip()
    den_tho = request.GET.get("den", "").strip()
    return {
        "tab": tab,
        "tu": summary_service.parse_day(tu_tho, mac_tu),
        "den": summary_service.parse_day(den_tho, mac_den),
        # Phụ chú "so với kỳ trước" chỉ tính khi người dùng chủ động lọc
        "loc_tay": bool(tu_tho and den_tho),
        "sp": request.GET.get("sp", "").strip(),
        "nguon": request.GET.get("nguon", "").strip(),
    }


def _query_loc(tham_so, bang, **doi):
    """Chuỗi truy vấn giữ trạng thái lọc, cho các thẻ tab và phân trang."""
    gia_tri = {
        "nguon": bang.code if bang else tham_so["nguon"],
        "nhom": tham_so["tab"],
        "tu": tham_so["tu"].isoformat(),
        "den": tham_so["den"].isoformat(),
        "sp": tham_so["sp"],
    }
    gia_tri.update(doi)
    return urlencode({k: v for k, v in gia_tri.items() if v})


@login_required
def bao_cao_tong_hop(request):
    """Thống kê theo nhãn ý nghĩa của bảng nguồn — FR-5.1 tới FR-5.5.

    Nguồn số liệu là đúng MỘT bảng trong phạm vi quyền (Q35). Tab đổi bằng
    tham số GET, không JavaScript — kiểm được ở mức HTML (Q31). Tab "Theo
    thị trường" đang hoãn chờ chốt nguồn (Q36, backlog N9).
    """
    request.nav_current = "bao_cao_tong_hop"

    cac_bang = summary_service.source_tables(request.user)
    tham_so = _tham_so_tong_hop(request)
    # Ngoài phạm vi là 403 ngay tại đây (quy tắc 8), trước mọi truy vấn khác
    bang = summary_service.pick_table(
        request.user, tham_so["nguon"], cac_bang, request=request)

    tabs = summary_service.TABS
    if bang is not None and marketing.is_marketing(list(bang.columns.all())):
        tabs = (("tong-hop", "Thống kê tổng hợp"), ("nhan-vien", "Thống kê theo MKT"),
                ("san-pham", "Thống kê theo sản phẩm"), ("thi-truong", "Thống kê theo thị trường"))
    boi_canh = {
        "cac_bang": cac_bang, "bang": bang,
        "tab": tham_so["tab"], "tu": tham_so["tu"], "den": tham_so["den"],
        "sp": tham_so["sp"], "hoan_thi_truong": tham_so["tab"] == "thi-truong",
        "cac_tab": [
            {"ma": ma, "nhan": nhan,
             "url": "?" + _query_loc(tham_so, bang, nhom=ma)}
            for ma, nhan in tabs
        ],
        "qs": _query_loc(tham_so, bang),
        # Đuôi nối vào liên kết phân trang để không mất trạng thái lọc
        "qs_loc": "&" + _query_loc(tham_so, bang),
        "crm_dashboard_url": (
            settings.BANGTINH_URL.rstrip("/") + "/thong-ke/"
            if settings.BANGTINH_URL else ""
        ),
    }

    if bang is not None and not boi_canh["hoan_thi_truong"]:
        boi_canh.update(summary_service.build_context(
            request.user, bang, tab=tham_so["tab"],
            date_from=tham_so["tu"], date_to=tham_so["den"],
            product=tham_so["sp"], with_compare=tham_so["loc_tay"],
        ))
        kq = boi_canh["kq"]
        if kq.ok:
            # Cắt trang trên danh sách nhóm đã lấy về — xem MAX_GROUPS
            boi_canh.update(pagination_context(
                request, boi_canh.pop("cac_nhom"), ten_don_vi=kq.unit))
            boi_canh["cac_dong"] = aggregations.finish_rows(
                list(boi_canh["trang"].object_list), kq)
            boi_canh["dong_tong"] = aggregations.total_cells(kq)

    return render(request, "reports/bao_cao_tong_hop.html", boi_canh)


@login_required
def bao_cao_tong_hop_xuat(request):
    """Tải tệp Excel đúng số liệu đang xem — FR-5.6. Mọi lần xuất đều ghi
    nhật ký (nguyên tắc P5); phần ghi nằm trong tầng dịch vụ."""
    cac_bang = summary_service.source_tables(request.user)
    tham_so = _tham_so_tong_hop(request)
    bang = summary_service.pick_table(
        request.user, tham_so["nguon"], cac_bang, request=request)

    if bang is None or tham_so["tab"] == "thi-truong":
        messages.error(request, "Chưa có số liệu để xuất ở màn hình này.")
        return redirect("bao_cao_tong_hop")

    try:
        kq = summary_service.build_export(
            request.user, bang, tab=tham_so["tab"],
            date_from=tham_so["tu"], date_to=tham_so["den"],
            product=tham_so["sp"], request=request,
        )
    except BusinessError as e:
        messages.error(request, str(e))
        return redirect("bao_cao_tong_hop")

    nhan_tab = dict(summary_service.TABS)[tham_so["tab"]]
    wb = excel.build_workbook(
        f"{bang.name} — {nhan_tab}", kq,
        subtitle=f"Từ {tham_so['tu']:%d.%m.%Y} đến {tham_so['den']:%d.%m.%Y}",
    )
    dem = BytesIO()
    wb.save(dem)

    phan_hoi = HttpResponse(
        dem.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    ten_tep = f"bao-cao-tong-hop-{tham_so['tab']}-{timezone.localdate():%Y%m%d}.xlsx"
    phan_hoi["Content-Disposition"] = f'attachment; filename="{ten_tep}"'
    return phan_hoi


@login_required
def bao_cao_xem(request, pk):
    """Xem lại nội dung một báo cáo đã nộp. Chỉ đọc — BR-2."""
    request.nav_current = "bao_cao_lich_su"

    # Lấy trong phạm vi quyền, không lấy thẳng theo khoá chính
    bao_cao = get_object_or_404(
        daily_service.history(request.user), pk=pk,
    )
    return render(request, "reports/bao_cao_xem.html", {
        "bao_cao": bao_cao,
        "cac_dong": daily_service.read_report_cells(bao_cao),
        "duoc_bo": bao_cao.created_by_id == request.user.pk,
    })


@login_required
@require_POST
def bao_cao_bo(request, pk):
    """Bỏ một báo cáo đã nộp. Không phải sửa — nội dung cũ giữ nguyên (BR-4)."""
    bao_cao = get_object_or_404(daily_service.history(request.user), pk=pk)
    if bao_cao.created_by_id != request.user.pk:
        messages.error(request, "Chỉ người nộp mới bỏ được báo cáo của mình.")
        return redirect("bao_cao_lich_su")

    daily_service.withdraw(bao_cao, actor=request.user, request=request)
    messages.success(request, "Đã bỏ báo cáo. Nộp lại sẽ là một bản ghi mới.")
    return redirect("bao_cao_lich_su")
