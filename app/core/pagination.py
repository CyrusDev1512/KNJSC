"""Phân trang.

Quy tắc 1: mọi màn hình danh sách phải có phân trang, mặc định 25 dòng.
Quy tắc Q4: không bao giờ lấy toàn bộ bảng trong màn hình danh sách.
"""
from urllib.parse import urlencode

from django.conf import settings
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator

PAGE_SIZES = (25, 50, 100)


def page_size(request, param="moi_trang", default=None):
    """Số dòng mỗi trang, chỉ nhận các giá trị đã cho phép. `default` cho màn
    hình có cỡ riêng (Bảng tính 100 dòng) — vẫn phải nằm trong PAGE_SIZES."""
    mac_dinh = default if default in PAGE_SIZES else getattr(settings, "PAGE_SIZE_DEFAULT", 25)
    try:
        chon = int(request.GET.get(param, mac_dinh))
    except (TypeError, ValueError):
        return mac_dinh
    return chon if chon in PAGE_SIZES else mac_dinh


def paginate(request, queryset, param="trang", size_param="moi_trang", default_size=None):
    """Cắt trang một queryset. Trả về đối tượng trang của Django.

    `param` cho phép một màn hình có hai bảng cùng phân trang độc lập —
    ví dụ màn hình Bộ phận và team.
    """
    paginator = Paginator(queryset, page_size(request, size_param, default_size))
    so_trang = request.GET.get(param, 1)
    try:
        return paginator.page(so_trang)
    except PageNotAnInteger:
        return paginator.page(1)
    except EmptyPage:
        return paginator.page(paginator.num_pages)


def pagination_context(request, queryset, ten_don_vi="dòng", param="trang",
                       size_param="moi_trang", default_size=None):
    """Bối cảnh cho `components/phan_trang.html`: trang, cỡ trang, các cỡ cho
    chọn, tên đơn vị ("25 việc"), tên tham số. Một hàm cho mọi màn hình danh
    sách; `param`/`size_param` cho màn hình có hai bảng phân trang độc lập."""
    trang = paginate(request, queryset, param=param, size_param=size_param, default_size=default_size)
    return {
        "page_obj": trang, "trang": trang,
        "moi_trang": page_size(request, size_param, default_size), "cac_co_trang": PAGE_SIZES,
        "ten_don_vi": ten_don_vi, "tham_so": param, "tham_so_co": size_param,
    }


def filter_query(**tham_so):
    """Chuỗi truy vấn của bộ lọc để nối vào liên kết phân trang (`qs_loc` của
    `components/phan_trang.html`): bắt đầu bằng "&", đã mã hoá URL, bỏ giá trị
    trống. Ghép tay `f"&tim={tim}"` thì "Sale & Marketing" hay "#" làm hỏng bộ lọc."""
    giu = {k: v for k, v in tham_so.items() if v not in (None, "")}
    return "&" + urlencode(giu) if giu else ""


class PaginatedListMixin:
    """Mixin đặt sẵn số dòng mỗi trang cho ListView."""

    paginate_by = getattr(settings, "PAGE_SIZE_DEFAULT", 25)
    page_kwarg = "trang"

    def get_paginate_by(self, queryset):
        return page_size(self.request)
