"""Màn hình báo cáo hằng ngày.

View chỉ nhận yêu cầu, kiểm quyền, gọi tầng dịch vụ (điều cấm 2). Phạm vi
quyền do `DailyReport.objects.in_scope` lo, không viết điều kiện lọc ở đây
(quy tắc 11).

**Không có view sửa báo cáo** — BR-2 và FR-4.4. Thiếu đường dẫn là cách chặn
chắc nhất; gọi thẳng cũng không có gì để gọi.
"""
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.exceptions import BusinessError
from core.pagination import PAGE_SIZES, page_size, paginate

from .services import daily_service


def _phan_trang(request, queryset, ten_don_vi="báo cáo"):
    """Bối cảnh khối phân trang (quy tắc 1)."""
    trang = paginate(request, queryset)
    return {
        "page_obj": trang, "trang": trang,
        "moi_trang": page_size(request), "cac_co_trang": PAGE_SIZES,
        "ten_don_vi": ten_don_vi, "tham_so": "trang", "tham_so_co": "moi_trang",
    }


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
        # Chưa nhập gì thì điền sẵn giá trị mặc định của định nghĩa trường
        "cac_o": [(t, du_lieu.get(t.field.code) or t.field.default_value)
                  for t in cac_truong],
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

    boi_canh = {"tim": tim, "tu": tu, "den": den}
    boi_canh.update(_phan_trang(request, ds))
    return render(request, "reports/bao_cao_lich_su.html", boi_canh)


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
        "cac_dong": daily_service.read_report(bao_cao),
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
