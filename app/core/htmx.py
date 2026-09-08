"""Nhận biết yêu cầu từ htmx — một chỗ, thay vì mỗi view tự đọc header."""


def is_htmx(request):
    """Yêu cầu do htmx gửi (header `HX-Request: true`): trả mảnh HTML hay
    header `HX-Redirect`, không trả cả trang."""
    return request.headers.get("HX-Request") == "true"
