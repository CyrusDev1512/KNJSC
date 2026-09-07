"""Màn hình Văn hoá — FR-12.1 tới FR-12.5, ADR-015.

View chỉ nhận yêu cầu, gọi tầng dịch vụ, trả kết quả (điều cấm 2). Trang này
là của toàn công ty: ai đăng nhập cũng xem được; ghi nhận thì đi từ trên
xuống (Q70) nên form chỉ hiện với Leader trở lên.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from core.audit import record_denied
from core.exceptions import BusinessError, OutOfScopeError
from core.identity import display_name
from core.pagination import pagination_context

from .constants import MESSAGE_MAX, MONTHLY_RANK_STARS, STARS_PER_RECOGNITION, CoreValue
from .forms import GhiNhanForm
from .services import leaderboard_service, recognition_service


def _hang_so():
    return {
        "sao_moi_ghi_nhan": STARS_PER_RECOGNITION,
        "sao_top": ", ".join(str(s) for s in MONTHLY_RANK_STARS),
        "message_max": MESSAGE_MAX,
    }


@login_required
def van_hoa(request):
    """Ghi nhận, bảng xếp hạng doanh số tháng này, nhiều sao nhất, ghi nhận mới nhất."""
    request.nav_current = "van_hoa"
    nguoi = recognition_service.active_users()      # một truy vấn dùng chung cho cả trang
    ky = recognition_service.current_period()
    boi_canh = pagination_context(request, recognition_service.recognitions_qs(), "ghi nhận")
    loi_ti_gia = ""
    try:
        bang_xep_hang = leaderboard_service.sales_leaderboard(users=nguoi)
    except BusinessError as loi:          # thiếu tỉ giá: báo rõ, không hiện số sai
        bang_xep_hang, loi_ti_gia = [], str(loi)
        messages.error(request, loi_ti_gia)
    tom_tat_sao = recognition_service.star_summary(period=ky, users=nguoi)
    duoc_ghi_nhan = recognition_service.can_recognize(request.user)
    boi_canh.update({
        "form": GhiNhanForm(),
        "duoc_ghi_nhan": duoc_ghi_nhan,
        "cac_nguoi": recognition_service.recipients(request.user, users=nguoi) if duoc_ghi_nhan else [],
        "cac_gia_tri": CoreValue.choices,
        "ky": ky, "ky_hien": recognition_service.period_label(ky),
        "bang_xep_hang": bang_xep_hang, "loi_ti_gia": loi_ti_gia,
        "nhieu_sao": recognition_service.star_totals(period=ky, users=nguoi, summary=tom_tat_sao),
        "sao_cua_toi": tom_tat_sao.get(request.user.pk, {}).get("sao", 0),
        **_hang_so(),
    })
    return render(request, "culture/van_hoa.html", boi_canh)


@login_required
@require_POST
def van_hoa_ghi_nhan(request):
    """Gửi một ghi nhận — FR-12.1. Nhân viên gọi thẳng đường này bị từ chối (Q70)."""
    if not recognition_service.can_recognize(request.user):
        record_denied(request.user, request.path, request)
        raise OutOfScopeError("Chỉ trưởng nhóm trở lên mới ghi nhận được cấp dưới.")
    form = GhiNhanForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Chưa gửi được: " + "; ".join(
            f"{form.fields[ten].label if ten in form.fields else 'Biểu mẫu'}: {' '.join(loi)}"
            for ten, loi in form.errors.items()))
        return redirect("van_hoa")
    d = form.cleaned_data
    try:
        ghi_nhan = recognition_service.give_recognition(
            receiver=recognition_service.active_user(d["receiver"]),
            value=d["value"], message=d["message"], actor=request.user, request=request,
        )
        messages.success(request, f"Đã ghi nhận {display_name(ghi_nhan.receiver)}, cộng một sao.")
    except BusinessError as loi:
        messages.error(request, str(loi))
    return redirect("van_hoa")


@login_required
def van_hoa_thanh_vien(request, pk):
    """Sao và ghi nhận của một thành viên — FR-12.5."""
    request.nav_current = "van_hoa"
    nguoi = recognition_service.active_user(pk)
    if nguoi is None:
        raise Http404
    boi_canh = pagination_context(request, recognition_service.received_by(nguoi), "ghi nhận")
    ky = recognition_service.current_period()
    boi_canh.update({
        "nguoi": nguoi,
        "tong_sao": recognition_service.stars_of(nguoi),
        "sao_ky": recognition_service.stars_of(nguoi, ky),
        "theo_ky": recognition_service.stars_by_period(nguoi),
        "ky_hien": recognition_service.period_label(ky),
        **_hang_so(),
    })
    return render(request, "culture/thanh_vien.html", boi_canh)
