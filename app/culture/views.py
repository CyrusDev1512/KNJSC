"""Màn hình Văn hoá — FR-12.1 tới FR-12.5, ADR-015.

View chỉ nhận yêu cầu, gọi tầng dịch vụ, trả kết quả (điều cấm 2). Trang này
là của toàn công ty: ai đăng nhập cũng xem được và ghi nhận được.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from core.exceptions import BusinessError
from core.identity import display_name
from core.pagination import PAGE_SIZES, page_size, paginate

from .constants import CoreValue
from .forms import GhiNhanForm
from .services import leaderboard_service, recognition_service


def _phan_trang(request, queryset, ten_don_vi="ghi nhận"):
    trang = paginate(request, queryset)
    return {
        "page_obj": trang, "trang": trang,
        "moi_trang": page_size(request), "cac_co_trang": PAGE_SIZES,
        "ten_don_vi": ten_don_vi, "tham_so": "trang", "tham_so_co": "moi_trang",
    }


@login_required
def van_hoa(request):
    """Ghi nhận, bảng xếp hạng doanh số tháng này, nhiều sao nhất, ghi nhận mới nhất."""
    request.nav_current = "van_hoa"
    nguoi = recognition_service.active_users()      # một truy vấn dùng chung cho cả trang
    ky = recognition_service.current_period()
    boi_canh = _phan_trang(request, recognition_service.recognitions_qs())
    try:
        bang_xep_hang = leaderboard_service.sales_leaderboard(users=nguoi)
    except BusinessError as loi:          # thiếu tỉ giá: báo rõ, không hiện số sai
        bang_xep_hang = []
        messages.error(request, str(loi))
    boi_canh.update({
        "form": GhiNhanForm(),
        "cac_nguoi": recognition_service.recipients(request.user, users=nguoi),
        "cac_gia_tri": CoreValue.choices,
        "ky": ky, "ky_hien": f"{ky[5:]}/{ky[:4]}",
        "bang_xep_hang": bang_xep_hang,
        "nhieu_sao": recognition_service.star_totals(period=ky, users=nguoi),
        "sao_cua_toi": recognition_service.stars_of(request.user),
    })
    return render(request, "culture/van_hoa.html", boi_canh)


@login_required
@require_POST
def van_hoa_ghi_nhan(request):
    """Gửi một ghi nhận — FR-12.1."""
    form = GhiNhanForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Chọn đồng nghiệp, giá trị và viết lời nhắn.")
        return redirect("van_hoa")
    d = form.cleaned_data
    nguoi = recognition_service.active_users().get(d["receiver"])
    try:
        ghi_nhan = recognition_service.give_recognition(
            receiver=nguoi, value=d["value"], message=d["message"],
            actor=request.user, request=request,
        )
        messages.success(request, f"Đã ghi nhận {display_name(ghi_nhan.receiver)}, cộng một sao.")
    except BusinessError as loi:
        messages.error(request, str(loi))
    return redirect("van_hoa")


@login_required
def van_hoa_thanh_vien(request, pk):
    """Sao và ghi nhận của một thành viên — FR-12.5."""
    request.nav_current = "van_hoa"
    nguoi = recognition_service.active_users().get(pk)
    if nguoi is None:
        raise Http404
    boi_canh = _phan_trang(request, recognition_service.received_by(nguoi))
    ky = recognition_service.current_period()
    boi_canh.update({
        "nguoi": nguoi,
        "tong_sao": recognition_service.stars_of(nguoi),
        "sao_ky": recognition_service.stars_of(nguoi, ky),
        "theo_ky": recognition_service.stars_by_period(nguoi),
        "ky_hien": f"{ky[5:]}/{ky[:4]}",
    })
    return render(request, "culture/thanh_vien.html", boi_canh)
