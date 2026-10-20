"""Phản hồi lỗi bộ lọc trên các màn đọc HTML; đường JSON giữ hợp đồng lỗi hiện có."""
from functools import wraps

from django.shortcuts import render
from django.urls import reverse

from .query import InvalidFilter


def filter_errors(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        try:
            return view(request, *args, **kwargs)
        except InvalidFilter as error:
            # Các view được bọc đều lấy bảng qua quyền trước khi đọc bộ lọc.
            code = kwargs.get("code")
            if code is None and args:
                code = getattr(args[0], "code", args[0])
            return render(request, "forms_builder/loi_bo_loc.html", {
                "loi": str(error), "bo_loc_url": reverse("bang_xem", args=[code]),
            }, status=400)
    return wrapped
