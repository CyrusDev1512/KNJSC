"""Màn hình của module org.

View chỉ nhận yêu cầu, kiểm quyền, gọi tầng dịch vụ, trả kết quả. Quy tắc
nghiệp vụ nằm ở services/ (điều cấm 2).

Mọi danh sách lấy dữ liệu qua `objects.in_scope(user)` — không viết điều
kiện lọc quyền ở đây (quy tắc 11).
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from core.constants import Rank
from core.exceptions import BusinessError
from core.pagination import PAGE_SIZES, page_size, paginate
from core.permissions import assert_rank, is_admin

from .forms import BoPhanForm, SuaHoSoForm, TaoTaiKhoanForm, TeamForm
from .models import Department, Team, UserProfile
from .services import account_service, org_service


def _phan_trang(request, queryset, ten_don_vi="dòng", param="trang", size_param="moi_trang"):
    """Bối cảnh dùng chung cho khối phân trang.

    `param` cho phép một màn hình có hai bảng phân trang độc lập.
    """
    trang = paginate(request, queryset, param=param, size_param=size_param)
    return {
        "page_obj": trang, "trang": trang,
        "moi_trang": page_size(request, size_param), "cac_co_trang": PAGE_SIZES,
        "ten_don_vi": ten_don_vi, "tham_so": param, "tham_so_co": size_param,
    }


# ══ NHÂN SỰ ═══════════════════════════════════════════════════════

@login_required
def nhan_su(request):
    """Danh sách nhân sự trong phạm vi quyền.

    Leader thấy team mình phụ trách, Manager thấy cả bộ phận, Admin thấy
    tất cả. Staff không vào được màn hình này.
    """
    request.nav_current = "nhan_su"
    assert_rank(request.user, Rank.LEADER, request)

    ds = (UserProfile.objects.in_scope(request.user)
          .select_related("user", "department", "team"))

    tim = request.GET.get("tim", "").strip()
    if tim:
        ds = ds.filter(
            Q(full_name__icontains=tim)
            | Q(user__username__icontains=tim)
            | Q(user__email__icontains=tim)
        )
    cap_bac = request.GET.get("cap_bac", "")
    if cap_bac:
        ds = ds.filter(rank=cap_bac)
    trang_thai = request.GET.get("trang_thai", "")
    if trang_thai == "hoat-dong":
        ds = ds.filter(user__is_active=True)
    elif trang_thai == "bi-khoa":
        ds = ds.filter(user__is_active=False)

    boi_canh = {
        "tim": tim, "cap_bac": cap_bac, "trang_thai": trang_thai,
        "cac_cap_bac": Rank.choices,
        "duoc_sua": is_admin(request.user),
    }
    boi_canh.update(_phan_trang(request, ds, "người"))
    return render(request, "org/nhan_su.html", boi_canh)


@login_required
def nhan_su_moi(request):
    """Tạo tài khoản. Chỉ quản trị viên (kien-truc.md — ai sở hữu dữ liệu gì)."""
    request.nav_current = "nhan_su"
    assert_rank(request.user, Rank.ADMIN, request)

    form = TaoTaiKhoanForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        account_service.create_account(
            username=d["username"], email=d["email"], full_name=d["full_name"],
            rank=d["rank"], department=d["department"], team=d["team"],
            password=d["password"], actor=request.user, request=request,
        )
        messages.success(request, f"Đã tạo tài khoản {d['username']}.")
        return redirect("nhan_su")

    return render(request, "org/nhan_su_form.html", {
        "form": form, "tieu_de": "Tạo tài khoản", "la_tao_moi": True,
    })


@login_required
def nhan_su_sua(request, pk):
    """Sửa hồ sơ. Chỉ quản trị viên."""
    request.nav_current = "nhan_su"
    assert_rank(request.user, Rank.ADMIN, request)

    # Lấy bản ghi trong phạm vi quyền, không lấy thẳng theo khoá chính —
    # nếu không thì ngày nào nới quyền cho Manager là họ sửa được hồ sơ
    # người bộ phận khác
    ho_so = get_object_or_404(
        UserProfile.objects.in_scope(request.user)
        .select_related("user", "department", "team"),
        pk=pk,
    )
    # Chụp giá trị cũ trước khi form kiểm tra — form gắn instance sẽ ghi đè
    # giá trị mới lên chính đối tượng ngay trong lúc kiểm tra
    goc = account_service.snapshot_profile(ho_so)
    form = SuaHoSoForm(request.POST or None, instance=ho_so)
    if request.method == "POST" and form.is_valid():
        # Đi qua tầng dịch vụ để thay đổi được ghi vào nhật ký — BR-5
        account_service.update_profile(
            ho_so, form.cleaned_data, before=goc,
            actor=request.user, request=request,
        )
        messages.success(request, f"Đã cập nhật hồ sơ {ho_so}.")
        return redirect("nhan_su")

    return render(request, "org/nhan_su_form.html", {
        "form": form, "ho_so": ho_so,
        "tieu_de": f"Sửa hồ sơ · {ho_so}", "la_tao_moi": False,
    })


@login_required
def nhan_su_doi_trang_thai(request, pk):
    """Khoá hoặc mở khoá tài khoản. Chỉ quản trị viên."""
    assert_rank(request.user, Rank.ADMIN, request)
    if request.method != "POST":
        return redirect("nhan_su")

    ho_so = get_object_or_404(
        UserProfile.objects.in_scope(request.user).select_related("user"), pk=pk,
    )
    if ho_so.user_id == request.user.pk:
        messages.error(request, "Không tự khoá tài khoản của chính mình được.")
        return redirect("nhan_su")

    if ho_so.user.is_active:
        account_service.lock_account(ho_so, actor=request.user, request=request)
        messages.success(request, f"Đã khoá {ho_so}. Phiên đang mở của họ bị huỷ ngay.")
    else:
        account_service.unlock_account(ho_so, actor=request.user, request=request)
        messages.success(request, f"Đã mở khoá {ho_so}.")
    return redirect("nhan_su")


# ══ BỘ PHẬN VÀ TEAM ═══════════════════════════════════════════════

@login_required
def bo_phan(request):
    """Bộ phận và team. Chỉ quản trị viên."""
    request.nav_current = "bo_phan"
    assert_rank(request.user, Rank.ADMIN, request)

    ds_bo_phan = (Department.objects.in_scope(request.user)
                  .annotate(so_nguoi=Count("members", distinct=True),
                            so_team=Count("teams", distinct=True))
                  .order_by("name"))
    ds_team = (Team.objects.in_scope(request.user)
               .select_related("department", "leader", "leader__profile")
               .annotate(so_nguoi=Count("members"))
               .order_by("department__name", "name"))

    form_bo_phan = BoPhanForm(prefix="bp")
    form_team = TeamForm(prefix="tm")

    if request.method == "POST":
        if "tao_bo_phan" in request.POST:
            form_bo_phan = BoPhanForm(request.POST, prefix="bp")
            if form_bo_phan.is_valid():
                org_service.create_department(
                    name=form_bo_phan.cleaned_data["name"],
                    code=form_bo_phan.cleaned_data["code"],
                    actor=request.user, request=request,
                )
                messages.success(request, "Đã tạo bộ phận.")
                return redirect("bo_phan")
        elif "tao_team" in request.POST:
            form_team = TeamForm(request.POST, prefix="tm")
            if form_team.is_valid():
                org_service.create_team(
                    name=form_team.cleaned_data["name"],
                    department=form_team.cleaned_data["department"],
                    leader=form_team.cleaned_data["leader"],
                    actor=request.user, request=request,
                )
                messages.success(request, "Đã tạo team.")
                return redirect("bo_phan")

    # Hai bảng phân trang độc lập nhau (quy tắc 1, Q4) — mỗi bảng một tham số
    return render(request, "org/bo_phan.html", {
        "form_bo_phan": form_bo_phan, "form_team": form_team,
        "pt_bo_phan": _phan_trang(request, ds_bo_phan, "bộ phận", "trang_bp", "moi_trang_bp"),
        "pt_team": _phan_trang(request, ds_team, "team", "trang_tm", "moi_trang_tm"),
    })
