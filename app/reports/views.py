"""Màn hình báo cáo hằng ngày.

View chỉ nhận yêu cầu, kiểm quyền, gọi tầng dịch vụ (điều cấm 2). Phạm vi
quyền do `DailyReport.objects.in_scope` lo, không viết điều kiện lọc ở đây
(quy tắc 11).

Quyền sửa nội dung theo quyết định 16/09/2026; phạm vi và phiên bản
được kiểm lại trong transaction tại daily_service.amend.
"""
from datetime import date
from io import BytesIO
from urllib.parse import urlencode

from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.exceptions import BusinessError, OutOfScopeError
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
    from core.permissions import assert_business_write
    assert_business_write(request.user)
    request.nav_current = "bao_cao_ngay"

    cac_bieu_mau = list(daily_service.forms_for(request.user))
    ma_chon = request.POST.get("bieu_mau") or request.GET.get("bieu_mau")
    bm = next((f for f in cac_bieu_mau if f.code == ma_chon), None)
    if ma_chon and bm is None:
        raise OutOfScopeError("Biểu mẫu không thuộc phạm vi của bạn.")
    if bm is None and cac_bieu_mau:
        bm = cac_bieu_mau[0]

    ngay = timezone.localdate()
    cac_truong = list(bm.ordered_fields()) if bm else []
    du_lieu, loi = {}, []
    from core.permissions import is_admin
    duoc_chon_team = is_admin(request.user)
    team_ho_so = getattr(getattr(request.user, 'profile', None), 'team', None)
    cac_team = daily_service.team_choices(bm) if bm and duoc_chon_team else []
    team_chon = request.POST.get("team") if request.method == "POST" else None
    if team_chon is None:
        team_chon = daily_service.default_team_id(request.user)

    if request.method == "POST" and bm is not None:
        du_lieu = {t.field.code: request.POST.get(t.field.code, "").strip()
                   for t in cac_truong}
        try:
            team = daily_service.resolve_team(bm, request.POST.get("team")) if duoc_chon_team and cac_team else team_ho_so
            daily_service.submit_current(
                bm, du_lieu, actor=request.user,
                request=request, fields=cac_truong, team=team,
            )
            messages.success(
                request, f"Đã nộp báo cáo cho ngày {ngay:%d.%m.%Y}. Nhân viên không tự sửa; "
                         "cần sửa số thì nhờ quản lý hoặc Kế toán trong Lịch sử báo cáo.")
            return redirect("bao_cao_lich_su")
        except BusinessError as e:
            loi.append(str(e))

    so_lan_da_nop = daily_service.submissions_today(bm, request.user, ngay) if bm else 0
    return render(request, "reports/bao_cao_ngay.html", {
        "cac_bieu_mau": cac_bieu_mau, "bm": bm, "ngay": ngay, "so_lan_da_nop": so_lan_da_nop,
        "cac_team": cac_team, "team_chon": str(team_chon or ""),
        "team_tu_dong": team_ho_so.name if team_ho_so else 'Chưa được gán Team',
        # Ô nhập, ô chọn, ô danh tính — cùng bộ với màn hình điền biểu mẫu
        "cac_o": daily_service.report_widgets(
            bm, cac_truong, du_lieu, user=request.user, day=ngay,
        ) if bm else [],
        "loi": loi,
        "cac_cot_tinh": bm.table.computed_columns() if bm else [],
    })


def _history_query(request, *, include_page=False):
    keys = ["tim", "tu", "den", "bieu_mau", "bo_phan"]
    if include_page:
        keys += ["trang", "moi_trang"]
    return urlencode({key: request.GET[key] for key in keys if request.GET.get(key)})


@login_required
def bao_cao_lich_su(request):
    """Xem lại báo cáo cũ trong phạm vi quyền — FR-4.3, FR-4.5."""
    request.nav_current = "bao_cao_lich_su"

    ds = daily_service.history(request.user)

    tim = request.GET.get("tim", "").strip()
    if tim:
        ds = ds.filter(Q(created_by__username__icontains=tim)
                       | Q(created_by__profile__staff_code__icontains=tim)
                       | Q(created_by__profile__full_name__icontains=tim))
    tu = request.GET.get("tu", "").strip()
    if tu:
        ds = ds.filter(report_date__gte=_ngay_bao_cao(tu))
    den = request.GET.get("den", "").strip()
    if den:
        ds = ds.filter(report_date__lte=_ngay_bao_cao(den))

    forms, departments = daily_service.history_choices(request.user)
    forms, departments = list(forms), list(departments)
    form_code = request.GET.get("bieu_mau", "").strip()
    dept_code = request.GET.get("bo_phan", "").strip()
    selected_form = next((form for form in forms if form.code == form_code), None)
    selected_dept = next((dept for dept in departments if dept.code == dept_code), None)
    if (form_code and selected_form is None) or (dept_code and selected_dept is None):
        raise Http404("Bộ lọc không thuộc phạm vi báo cáo của bạn.")
    if selected_form:
        ds = ds.filter(form=selected_form)
    if selected_dept:
        ds = ds.filter(department=selected_dept)
    boi_canh = {"tim": tim, "tu": tu, "den": den, "cac_bieu_mau": forms,
               "cac_bo_phan": departments, "bieu_mau": form_code, "bo_phan": dept_code}
    boi_canh.update(pagination_context(request, ds, "báo cáo"))
    boi_canh["qs_loc"] = "&" + _history_query(request)
    boi_canh["history_query"] = _history_query(request, include_page=True)
    # Manager/Admin có mục "Đã bỏ" để khôi phục báo cáo bỏ nhầm — ADR-041
    boi_canh["duoc_khoi_phuc"] = daily_service.can_restore(request.user)
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


def _configured_report(request, table, tables, *, export=False):
    """Nguồn đã cấu hình hiển thị ngay tại URL tổng hợp, dùng cùng bộ tính."""
    from . import activity_views
    choices = [t.erp_report for t in tables if getattr(t, "erp_report", None) is not None]
    if table is not None and getattr(table, "erp_report", None) is not None:
        return activity_views.report(request, export=export, choices=choices)
    return None


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

    configured = _configured_report(request, bang, cac_bang, export=False)
    if configured is not None:
        return configured

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

    configured = _configured_report(request, bang, cac_bang, export=True)
    if configured is not None:
        return configured

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
    revisions = list(bao_cao.revisions.select_related('actor', 'actor__profile')[:50])
    columns = {c.code: c for c in bao_cao.form.table.columns.all()}
    for revision in revisions:
        revision.display_changes = [{'name':columns[code].name,
            'before':daily_service.display_report_value(columns[code], revision.before.get(code)),
            'after':daily_service.display_report_value(columns[code], revision.after.get(code))}
            for code in columns if revision.before.get(code) != revision.after.get(code)]
    return render(request, "reports/bao_cao_xem.html", {
        "bao_cao": bao_cao,
        "cac_dong": daily_service.read_report_cells(bao_cao),
        "duoc_bo": daily_service.can_withdraw(request.user, bao_cao),
        "duoc_sua": daily_service.can_amend(request.user, bao_cao),
        "revisions": revisions,
        "history_query": _history_query(request, include_page=True),
    })


@login_required
@require_POST
def bao_cao_bo(request, pk):
    """Bỏ một báo cáo đã nộp — người nộp, Leader trong team, Manager trong bộ
    phận, Admin (ADR-041). Không phải sửa — nội dung cũ giữ nguyên (BR-4)."""
    from core.audit import record_denied
    bao_cao = get_object_or_404(daily_service.history(request.user), pk=pk)
    if not daily_service.can_withdraw(request.user, bao_cao):
        record_denied(request.user, request.get_full_path(), request)
        return HttpResponse("Bạn không có quyền bỏ báo cáo này.", status=403)

    daily_service.withdraw(bao_cao, actor=request.user, request=request)
    messages.success(request, "Đã bỏ báo cáo. Nộp lại sẽ là một bản ghi mới; quản lý khôi phục được ở mục Đã bỏ.")
    return redirect("bao_cao_lich_su")


@login_required
def bao_cao_da_bo(request):
    """Danh sách báo cáo đã bỏ — Manager bộ phận mình và Admin khôi phục được
    (ADR-041). Người khác gọi thẳng bị 403 có nhật ký (quy tắc 8)."""
    from core.audit import record_denied
    from .models import DailyReport
    if not daily_service.can_restore(request.user):
        record_denied(request.user, request.get_full_path(), request)
        return HttpResponse("Bạn không có quyền xem báo cáo đã bỏ.", status=403)
    request.nav_current = "bao_cao_lich_su"
    ds = (DailyReport.all_objects.in_scope(request.user)
          .filter(deleted_at__isnull=False)
          .select_related("form", "record", "created_by", "created_by__profile",
                          "department", "team", "deleted_by", "deleted_by__profile")
          .order_by("-updated_at"))
    boi_canh = pagination_context(request, ds, "báo cáo")
    return render(request, "reports/bao_cao_da_bo.html", boi_canh)


@login_required
@require_POST
def bao_cao_khoi_phuc(request, pk):
    """Khôi phục một báo cáo đã bỏ — Manager bộ phận mình hoặc Admin (ADR-041)."""
    from core.audit import record_denied
    from .models import DailyReport
    bao_cao = get_object_or_404(
        DailyReport.all_objects.in_scope(request.user).filter(deleted_at__isnull=False), pk=pk)
    try:
        daily_service.restore(bao_cao, actor=request.user, request=request)
    except OutOfScopeError:
        record_denied(request.user, request.get_full_path(), request)
        return HttpResponse("Bạn không có quyền khôi phục báo cáo này.", status=403)
    messages.success(request, "Đã khôi phục báo cáo; số liệu về lại Báo cáo tổng hợp.")
    return redirect("bao_cao_da_bo")


@login_required
def bao_cao_sua(request, pk):
    """Sửa nội dung trong phạm vi quản lý, giữ báo cáo gốc và lịch sử."""
    report = get_object_or_404(daily_service.history(request.user), pk=pk)
    if not daily_service.can_amend(request.user, report):
        raise Http404('Báo cáo không thuộc phạm vi được sửa.')
    request.nav_current = 'bao_cao_lich_su'
    fields = list(report.form.ordered_fields())
    values = {f.field.code: report.record.data.get(f.link.column.code, '')
              for f in fields if getattr(f, 'link', None)}
    # Giá trị lưu Decimal dùng dấu chấm, ô nhập tiền dùng dấu phẩy thập phân.
    for f in fields:
        if f.field.field_type in ('money', 'decimal') and f.field.code in values:
            values[f.field.code] = str(values[f.field.code] if values[f.field.code] is not None else '').replace('.', ',')
    version, errors, status = report.record.updated_at.isoformat(), [], 200
    if request.method == 'POST':
        values.update({f.field.code: request.POST[f.field.code] for f in fields if f.field.code in request.POST})
        version = request.POST.get('version', '')
        try:
            daily_service.amend(report, values, version=version, actor=request.user, request=request)
            messages.success(request, 'Đã cập nhật báo cáo và ghi lịch sử chỉnh sửa.')
            return redirect('bao_cao_xem', pk=pk)
        except daily_service.ReportConflict as error:
            errors, status = [str(error)], 409
        except BusinessError as error:
            errors, status = [str(error)], 400
    return render(request, 'reports/bao_cao_sua.html', {
        'bao_cao': report, 'bm': report.form, 'version': version, 'loi': errors,
        'cac_o': daily_service.report_widgets(report.form, fields, values,
            user=request.user, day=report.report_date, owner=report.created_by),
    }, status=status)
