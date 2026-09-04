"""Thanh lọc bên trái của Bảng tính — ADR-010.

Ba khối, giống công cụ vận hành mà bộ phận đang quen dùng: **Chọn nhanh** một
khoảng thời gian, **Từ ngày / Đến ngày**, và danh sách **Sản phẩm** đánh dấu
chọn. Không có tham số mới trên URL: chọn nhanh và khoảng ngày viết thẳng vào
`f_<cột ngày>__lon_bang` và `f_<cột ngày>__nho_bang`, nên bộ đọc chung
(`query.read_filters`), chip "đang lọc" và nút Xuất Excel hiểu ngay.

Cột ngày là cột mang nhãn ý nghĩa **Ngày**, cột sản phẩm là cột mang nhãn
**Sản phẩm** (ADR-007). Bảng vận đơn không có cột Sản phẩm mà có mỗi sản phẩm
một cột số lượng (Q39), nên khối Sản phẩm của nó lọc bằng `sp=<mã cột>`.
"""
from datetime import date, timedelta

from forms_builder.meaning import Meaning

from . import grid_service

#: (mã, nhãn) — thứ tự hiện trên thanh bên
DATE_PRESETS = (
    ("hom_nay", "Hôm nay"),
    ("hom_qua", "Hôm qua"),
    ("7_ngay", "7 ngày qua"),
    ("thang_nay", "Tháng này"),
    ("thang_truoc", "Tháng trước"),
)


def date_column(columns):
    return next((c for c in columns if c.meaning == Meaning.DATE), None)


def product_column(columns):
    return next((c for c in columns if c.meaning == Meaning.PRODUCT), None)


def preset_range(key, today=None):
    """`(từ, đến)` của một mốc chọn nhanh, hoặc `(None, None)` nếu mã lạ."""
    hom_nay = today or date.today()
    if key == "hom_nay":
        return hom_nay, hom_nay
    if key == "hom_qua":
        qua = hom_nay - timedelta(days=1)
        return qua, qua
    if key == "7_ngay":
        return hom_nay - timedelta(days=6), hom_nay
    if key == "thang_nay":
        return hom_nay.replace(day=1), hom_nay
    if key == "thang_truoc":
        dau_thang = hom_nay.replace(day=1)
        cuoi_truoc = dau_thang - timedelta(days=1)
        return cuoi_truoc.replace(day=1), cuoi_truoc
    return None, None


def _khoa_ngay(cot):
    return f"f_{cot.code}__lon_bang", f"f_{cot.code}__nho_bang"


def preset_links(date_col, params, today=None):
    """Mỗi mốc chọn nhanh thành `(mã, nhãn, chuỗi truy vấn, đang bật, lớp CSS)`.
    Lớp tính ở đây vì bài quét lớp CSS không đọc được điều kiện trong template."""
    k_tu, k_den = _khoa_ngay(date_col)
    tu_hien, den_hien = params.get(k_tu, ""), params.get(k_den, "")
    giu = grid_service.params_without(params, exclude=(k_tu, k_den))
    ket_qua = []
    for ma, nhan in DATE_PRESETS:
        tu, den = preset_range(ma, today)
        cap = giu + [(k_tu, tu.isoformat()), (k_den, den.isoformat())]
        qs = "&".join(f"{k}={v}" for k, v in _ma_hoa(cap))
        bat = tu_hien == tu.isoformat() and den_hien == den.isoformat()
        ket_qua.append((ma, nhan, qs, bat, "chip chip-nhan" if bat else "chip"))
    return ket_qua


def _ma_hoa(cap):
    from urllib.parse import quote

    return [(quote(k, safe=""), quote(str(v), safe="")) for k, v in cap]


def product_options(user, table, columns, params):
    """Danh sách sản phẩm để đánh dấu chọn.

    Trả `{"kind": ..., "param": tên tham số, "items": [(giá trị, nhãn, số dòng, đang chọn)]}`;
    `kind` là `"cot_sl"` (bảng vận đơn), `"gia_tri"` (bảng có cột Sản phẩm)
    hoặc None (không có khối này).
    """
    if grid_service.is_waybill(table):
        dang_chon = set(grid_service.read_products(params, columns))
        return {
            "kind": "cot_sl", "param": grid_service.PRODUCT_PARAM,
            "items": [(c.code, c.name, None, c.code in dang_chon)
                      for c in grid_service.product_columns_of(columns)],
        }
    cot = product_column(columns)
    if cot is None:
        return {"kind": None, "param": "", "items": []}
    ten_tham_so = f"f_{cot.code}__trong"
    dang_chon = set(params.getlist(ten_tham_so)) if hasattr(params, "getlist") else set()
    return {
        "kind": "gia_tri", "param": ten_tham_so,
        "items": [(gt, gt or "(trống)", so, gt in dang_chon)
                  for gt, so in grid_service.filter_options(user, table, cot)],
    }


def context(user, table, columns, params, today=None):
    """Toàn bộ dữ liệu của thanh bên cho template."""
    cot_ngay = date_column(columns)
    san_pham = product_options(user, table, columns, params)
    ben = {"cot_ngay": cot_ngay, "san_pham": san_pham}
    if cot_ngay is not None:
        k_tu, k_den = _khoa_ngay(cot_ngay)
        ben.update({
            "chon_nhanh": preset_links(cot_ngay, params, today),
            "k_tu": k_tu, "k_den": k_den,
            "tu": params.get(k_tu, ""), "den": params.get(k_den, ""),
            "giu_ngay": grid_service.params_without(params, exclude=(k_tu, k_den)),
        })
    if san_pham["kind"]:
        ben["giu_san_pham"] = grid_service.params_without(params, exclude=(san_pham["param"],))
    ben["co_gi"] = cot_ngay is not None or bool(san_pham["kind"])
    return ben
