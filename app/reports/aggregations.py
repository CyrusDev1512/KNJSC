"""Phép tính của báo cáo tổng hợp, dựa trên nhãn ý nghĩa — FR-5.1 tới FR-5.4.

Tầng này dịch `meaning.AGGREGATIONS` sang ORM: nhóm theo cột mang nhãn, cộng
tổng các cột số, tính lại cột tính sẵn trên tổng. Nó không biết HTTP và không
biết phạm vi quyền — nhận queryset ĐÃ qua `.in_scope(user)` rồi mới tính
(quy tắc 11, noi theo `forms_builder/query.py`).

Ba điều cần biết khi đọc:

- Giá trị số trong JSON không đồng nhất: INTEGER là số JSON thật, còn
  MONEY/DECIMAL là **chuỗi** (`record_service.parse_value`). Vì vậy phải đi
  qua ``KeyTextTransform`` (toán tử ``->>`` ra text) rồi mới ``Cast`` sang
  Decimal — Cast thẳng trên jsonb nổ với giá trị chuỗi. Đường text-rồi-cast
  nhận được cả hai dạng; khoá thiếu ra NULL và ``Sum`` bỏ qua.
- Cột tính sẵn không cộng tổng được (tổng của tỉ lệ ≠ tỉ lệ của tổng). Chúng
  được tính lại từ tổng hai toán hạng bằng chính ``ColumnDef.compute`` — với
  chia và phần trăm, đó chính là trung bình có trọng số (CPO, AOV, tỉ lệ
  chốt). Riêng phép nhân thì bỏ hẳn: tổng các tích không bằng tích các tổng.
- `DataRecord.Meta.ordering` là ``["-created_at"]`` — không xoá đi trước khi
  ``values().annotate()`` thì `created_at` lọt vào GROUP BY và mỗi dòng thành
  một nhóm riêng. Mọi truy vấn ở đây đều `.order_by()` trắng trước.

Nhóm theo thị trường cố ý chưa có — người dùng hoãn ngày 03.09.2026 (Q36),
chờ chốt nguồn số liệu ở backlog N9.
"""
from dataclasses import dataclass, replace
from decimal import Decimal

from django.db.models import Count, DecimalField, F, Sum
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Cast

from core.money import MONEY_DECIMAL_PLACES, MONEY_MAX_DIGITS
from forms_builder.meaning import (
    COLUMN_OF, FieldType, Meaning, can_group, can_sum,
)
from forms_builder.models import ComputeOp

#: Cách nhóm trên URL sang nhãn ý nghĩa. Khai một chỗ duy nhất (quy tắc 7).
#: "thi-truong" cố ý vắng mặt — hoãn theo Q36, chờ chốt backlog N9.
GROUP_KEYS = {
    "ngay": Meaning.DATE,
    "nhan-vien": Meaning.SELLER,
    "san-pham": Meaning.PRODUCT,
}

#: Đơn vị đếm cho nhãn "Tổng cộng · N ..." ở chân bảng.
UNIT_OF = {
    "ngay": "ngày",
    "nhan-vien": "nhân viên",
    "san-pham": "sản phẩm",
}

#: Kiểu dữ liệu cộng tổng được. Các kiểu khác chỉ lưu và hiển thị (ADR-001).
SUMMABLE_TYPES = {FieldType.INTEGER, FieldType.DECIMAL, FieldType.MONEY}

#: Phép tính lại được trên tổng các toán hạng. MULTIPLY vắng mặt là cố ý.
RECOMPUTABLE_OPS = {ComputeOp.ADD, ComputeOp.SUBTRACT, ComputeOp.DIVIDE, ComputeOp.PERCENT}


@dataclass(frozen=True)
class ReportColumn:
    """Một cột số trên báo cáo, sau cột nhóm."""

    code: str
    label: str
    kind: str          # "sum" | "computed" | "share"
    decimals: int = 0
    suffix: str = ""   # "%" cho phần trăm và tỉ trọng


@dataclass(frozen=True)
class SummaryResult:
    """Kết quả một lượt tổng hợp. `rows` chưa cắt trang — tầng trên tự cắt."""

    ok: bool
    group_label: str = ""
    group_is_date: bool = False
    unit: str = "dòng"
    columns: tuple = ()
    rows: object = None        # queryset .values() — mỗi phần tử một dict
    totals: dict = None        # tổng cộng trên TOÀN BỘ kết quả, không theo trang
    computed_columns: tuple = ()
    revenue_alias: str = ""    # khoá của cột doanh thu trong dict dòng, nếu có


def labeled_columns(columns):
    """Ánh xạ nhãn ý nghĩa sang cột của bảng: `{Meaning: ColumnDef}`."""
    return {c.meaning: c for c in columns if c.meaning}


def _alias(code):
    """Tên khoá trong dict kết quả. Thêm tiền tố để không đụng tên cột model
    (`data`, `team`…) hay hai khoá cố định `nhom`, `so_dong`."""
    return f"c_{code}"


def _sum_columns(columns):
    """Các cột nhập tay cộng tổng được, theo đúng thứ tự cột của bảng.

    Nhờ `ALLOWED_TYPES`, cột số duy nhất có thể mang nhãn là Doanh thu — mọi
    cột số khác đều nằm trong JSON.
    """
    ket_qua = []
    for c in columns:
        if c.is_computed or c.field_type not in SUMMABLE_TYPES:
            continue
        if c.meaning and c.meaning != Meaning.REVENUE:
            continue        # không xảy ra theo ALLOWED_TYPES, chặn cho chắc
        ket_qua.append(c)
    return ket_qua


def _sum_exprs(sum_cols):
    """Biểu thức Sum cho từng cột — cột tách cộng thẳng, cột JSON phải qua
    text rồi mới cast (xem docstring đầu tệp)."""
    exprs = {}
    for c in sum_cols:
        if c.meaning == Meaning.REVENUE and can_sum(Meaning.REVENUE):
            exprs[_alias(c.code)] = Sum("val_revenue")
        else:
            exprs[_alias(c.code)] = Sum(Cast(
                KeyTextTransform(c.code, "data"),
                output_field=DecimalField(
                    max_digits=MONEY_MAX_DIGITS, decimal_places=MONEY_DECIMAL_PLACES,
                ),
            ))
    return exprs


def _recomputable(columns, sum_cols):
    """Cột tính sẵn tính lại được trên tổng: phép hợp lệ và đủ hai toán hạng
    đều là cột đã cộng."""
    co_tong = {c.code for c in sum_cols}
    return [
        c for c in columns
        if c.is_computed and c.compute_op in RECOMPUTABLE_OPS
        and c.compute_left in co_tong and c.compute_right in co_tong
    ]


def apply_filters(qs, by_meaning, *, date_from=None, date_to=None, product=""):
    """Bộ lọc chung của màn hình — FR-5.2, FR-5.3, trên cột tách có chỉ mục.

    Bảng không có cột mang nhãn tương ứng thì bộ lọc đó không áp — tầng trên
    đã biết mà ẩn ô lọc đi.
    """
    if Meaning.DATE in by_meaning:
        if date_from is not None:
            qs = qs.filter(val_date__gte=date_from)
        if date_to is not None:
            qs = qs.filter(val_date__lte=date_to)
    if product and Meaning.PRODUCT in by_meaning:
        qs = qs.filter(val_product=product)
    return qs


def _recompute(computed_cols, values_by_code):
    """Tính lại các cột tính sẵn từ một dict `{mã cột: tổng}`."""
    return {
        c.code: c.compute(values_by_code)
        for c in computed_cols
    }


def summarize(table, scoped_qs, *, group_key, date_from=None, date_to=None,
              product="", columns=None, with_totals=True):
    """Một lượt tổng hợp: nhóm + cộng + dòng tổng cộng — FR-5.1 và FR-5.4.

    `scoped_qs` phải là `DataRecord.objects.in_scope(user)` (quy tắc 11).
    `columns` cho phép truyền danh sách cột đã lấy sẵn để khỏi truy vấn lại.

    `with_totals=False` bỏ lệnh aggregate dòng tổng cộng — cho màn hình đã
    lấy về toàn bộ dòng nhóm và sẽ tự cộng bằng `totals_from_rows` (SUM kết
    hợp được nên hai đường cho cùng một số); gắn lại bằng `attach_totals`.
    """
    meaning = GROUP_KEYS[group_key]
    cols = list(columns) if columns is not None else list(table.columns.all())
    by_meaning = labeled_columns(cols)

    group_col = by_meaning.get(meaning)
    if group_col is None or not can_group(meaning):
        # Bảng nguồn không có cột mang nhãn này — báo về để màn hình hiện
        # ghi chú, không nổ lỗi
        return SummaryResult(ok=False, unit=UNIT_OF[group_key])

    qs = apply_filters(
        scoped_qs.filter(table=table), by_meaning,
        date_from=date_from, date_to=date_to, product=product,
    )

    sum_cols = _sum_columns(cols)
    exprs = _sum_exprs(sum_cols)
    computed_cols = _recomputable(cols, sum_cols)
    revenue_col = by_meaning.get(Meaning.REVENUE)

    group_path = COLUMN_OF[meaning]
    # `.order_by()` trắng để xoá Meta.ordering trước khi GROUP BY — xem
    # docstring đầu tệp
    rows = (
        qs.order_by()
        .values(nhom=F(group_path))
        .annotate(so_dong=Count("id"), **exprs)
    )
    if meaning == Meaning.DATE:
        rows = rows.order_by("-nhom")
    elif revenue_col is not None and revenue_col in sum_cols:
        rows = rows.order_by(f"-{_alias(revenue_col.code)}", "nhom")
    else:
        rows = rows.order_by("nhom")

    # Dòng tổng cộng: MỘT lệnh riêng trên cùng queryset đã lọc, không cắt
    # trang — nhờ vậy AC-5.4 so nó với tổng các dòng chi tiết mới có nghĩa
    totals = None
    if with_totals:
        totals = qs.order_by().aggregate(so_dong=Count("id"), **exprs)
        totals.update(_recompute(
            computed_cols, {c.code: totals[_alias(c.code)] for c in sum_cols},
        ))

    # Danh sách cột hiển thị, sau cột nhóm: cột cộng và cột tính theo đúng
    # thứ tự cột của bảng, rồi Tỉ trọng nếu là tab sản phẩm có doanh thu
    hien = []
    tinh_duoc = {c.code for c in computed_cols}
    for c in cols:
        if c in sum_cols:
            hien.append(ReportColumn(
                code=c.code, label=c.name, kind="sum",
                decimals=0 if c.field_type == FieldType.INTEGER else 2,
            ))
        elif c.is_computed and c.code in tinh_duoc:
            hien.append(ReportColumn(
                code=c.code, label=c.name, kind="computed",
                decimals=c.compute_decimals,
                suffix="%" if c.compute_op == ComputeOp.PERCENT else "",
            ))
    if meaning == Meaning.PRODUCT and revenue_col is not None:
        hien.append(ReportColumn(
            code="__share__", label="Tỉ trọng", kind="share", decimals=1, suffix="%",
        ))

    return SummaryResult(
        ok=True,
        group_label=group_col.name,
        group_is_date=(meaning == Meaning.DATE),
        unit=UNIT_OF[group_key],
        columns=tuple(hien),
        rows=rows,
        totals=totals,
        computed_columns=tuple(computed_cols),
        revenue_alias=_alias(revenue_col.code) if revenue_col else "",
    )


def totals_only(table, scoped_qs, *, date_from=None, date_to=None, product="",
                columns=None):
    """Chỉ dòng tổng cộng, kèm cột tính lại — một lệnh truy vấn."""
    cols = list(columns) if columns is not None else list(table.columns.all())
    by_meaning = labeled_columns(cols)
    qs = apply_filters(
        scoped_qs.filter(table=table), by_meaning,
        date_from=date_from, date_to=date_to, product=product,
    )
    sum_cols = _sum_columns(cols)
    totals = qs.order_by().aggregate(so_dong=Count("id"), **_sum_exprs(sum_cols))
    totals.update(_recompute(
        _recomputable(cols, sum_cols),
        {c.code: totals[_alias(c.code)] for c in sum_cols},
    ))
    return totals


def totals_from_rows(items, result):
    """Dòng tổng cộng tính từ chính các dòng nhóm đã lấy về.

    Chỉ dùng khi `items` là TOÀN BỘ dòng nhóm — chưa cắt trang, chưa chạm
    trần. SUM kết hợp được nên tổng của tổng từng nhóm bằng đúng lệnh
    aggregate trên cả bảng; tầng trên chạm trần thì phải quay về `totals_only`.
    """
    totals = {"so_dong": sum(i["so_dong"] for i in items)}
    for cot in result.columns:
        if cot.kind != "sum":
            continue
        khoa = _alias(cot.code)
        gia_tri = [i[khoa] for i in items if i[khoa] is not None]
        totals[khoa] = sum(gia_tri, Decimal("0")) if gia_tri else None
    totals.update(_recompute(
        result.computed_columns,
        {k.removeprefix("c_"): v for k, v in totals.items() if k.startswith("c_")},
    ))
    return totals


def attach_totals(result, totals):
    """Gắn dòng tổng cộng tính ngoài vào một kết quả `with_totals=False`."""
    return replace(result, totals=totals)


# ══ HIỂN THỊ ══════════════════════════════════════════════════════

def format_number(value, decimals=0):
    """Định dạng số kiểu Việt Nam: nghìn dấu chấm, thập phân dấu phẩy.

    Không kèm ký hiệu tiền — bảng động chưa lưu loại tiền theo dòng (N10).
    Số nguyên chẵn thì bỏ phần lẻ cho gọn, kể cả khi cột khai hai chữ số.
    """
    if value is None:
        return "—"
    so = Decimal(value)
    if decimals and so == so.to_integral_value():
        decimals = 0
    text = f"{so:,.{decimals}f}"
    return text.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def _cell_values(result, values_by_code):
    """Giá trị thô (Decimal hoặc None) cho một dòng, theo đúng `result.columns`.

    Tỉ trọng tính tại đây: doanh thu của nhóm chia tổng doanh thu — dòng tổng
    cộng tự ra 100 vì tử và mẫu bằng nhau.
    """
    cells = []
    tong_doanh_thu = result.totals.get(result.revenue_alias) if result.revenue_alias else None
    for cot in result.columns:
        if cot.kind == "share":
            phan = values_by_code.get(result.revenue_alias.removeprefix("c_"))
            if phan is None or not tong_doanh_thu:
                cells.append(None)
            else:
                cells.append((Decimal(phan) / Decimal(tong_doanh_thu) * 100)
                             .quantize(Decimal(1).scaleb(-cot.decimals)))
        else:
            cells.append(values_by_code.get(cot.code))
    return cells


def _format_cells(result, raw_cells):
    """Chuỗi hiển thị cho một dãy ô thô."""
    out = []
    for cot, gia_tri in zip(result.columns, raw_cells):
        text = format_number(gia_tri, cot.decimals)
        out.append(text + cot.suffix if text != "—" else text)
    return out


def row_values(item, result):
    """`(giá trị nhóm, dãy ô thô)` của một dòng nhóm — cột tính sẵn đã tính
    lại theo dòng. Dùng cho cả màn hình lẫn tệp xuất."""
    by_code = {k.removeprefix("c_"): v for k, v in item.items() if k.startswith("c_")}
    by_code.update(_recompute(result.computed_columns, by_code))
    return item.get("nhom"), _cell_values(result, by_code)


def total_values(result):
    """Dãy ô thô của dòng tổng cộng, cùng thứ tự cột với dòng chi tiết."""
    by_code = {k.removeprefix("c_"): v for k, v in result.totals.items() if k.startswith("c_")}
    by_code.update({c.code: result.totals.get(c.code) for c in result.computed_columns})
    return _cell_values(result, by_code)


def format_group(value, result):
    """Chuỗi hiển thị của giá trị nhóm. Nhóm rỗng hiện "—"."""
    if value in (None, ""):
        return "—"
    if result.group_is_date:
        return value.strftime("%d.%m.%Y")
    return str(value)


def finish_rows(page_items, result):
    """Hoàn thiện các dòng của MỘT trang thành chuỗi hiển thị. Chạy sau khi
    cắt trang để không tính thừa."""
    rows = []
    for item in page_items:
        nhom, raw = row_values(item, result)
        rows.append({
            "nhom": format_group(nhom, result),
            "cells": _format_cells(result, raw),
        })
    return rows


def total_cells(result):
    """Dãy ô hiển thị cho dòng tổng cộng."""
    return _format_cells(result, total_values(result))
