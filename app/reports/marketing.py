"""Cách trình bày BC MKT của CRM_ Tân.xlsx, chỉ dùng trong báo cáo ERP.

Cột M giữ nguyên tên Hóa đơn/Doanh thu và công thức K/J theo xác nhận
chủ dự án 09.09.2026. Không suy ra phép chia Hóa đơn cho Doanh thu.
"""
from dataclasses import dataclass, replace
from decimal import Decimal
import unicodedata

from . import aggregations


def normalized(name):
    return " ".join(unicodedata.normalize("NFC", name).casefold().split())


def is_marketing(columns):
    names = {normalized(c.name) for c in columns}
    return {"marketer", "số mess", "cpqc", "số đơn", "doanh số"} <= names


def divide(a, b):
    return None if a is None or b in (None, 0) else Decimal(a) / Decimal(b)


@dataclass(frozen=True)
class Metric:
    code: str
    sources: tuple
    kind: str

    def compute(self, values):
        if self.kind == "missing":
            return None
        args = [values.get(k) for k in self.sources]
        if self.kind == "k_over_j":
            cpqc, mess, orders = args
            return divide(divide(cpqc, mess), divide(cpqc, orders))
        return divide(*args)


def adapt(result, columns):
    if not result.ok or not is_marketing(columns):
        return result
    by_name = {normalized(c.name): c for c in columns if not c.is_computed}
    summed = {c.code: c for c in result.columns if c.kind == "sum"}
    display, metrics = [], []
    codes = {}
    for i, label in enumerate(("Số Mess", "CPQC", "Số đơn", "Doanh số", "Doanh thu", "Hóa đơn")):
        source = by_name.get(normalized(label))
        code = source.code if source is not None and source.code in summed else f"__mkt_missing_{i}"
        codes[label] = code
        if code in summed:
            display.append(replace(summed[code], label=label))
        else:
            display.append(aggregations.ReportColumn(code, label, "computed", 2))
            metrics.append(Metric(code, (), "missing"))
    formulas = (
        ("CPO", ("CPQC", "Số đơn"), "divide"),
        ("Giá Mess", ("CPQC", "Số Mess"), "divide"),
        ("CPQC/Doanh số", ("CPQC", "Doanh số"), "divide"),
        ("Hóa đơn/Doanh thu", ("CPQC", "Số Mess", "Số đơn"), "k_over_j"),
        ("AOV", ("Doanh số", "Số đơn"), "divide"),
    )
    for i, (label, inputs, kind) in enumerate(formulas):
        code = f"__mkt_metric_{i}"
        metrics.append(Metric(code, tuple(codes[n] for n in inputs), kind))
        # Excel ghi công thức chia; giữ giá trị tỷ số, không tự nhân 100.
        display.append(aggregations.ReportColumn(code, label, "computed", 4 if "/" in label else 2))
    result = replace(result, columns=tuple(display), computed_columns=tuple(metrics),
                     group_label="Marketer" if result.unit == "nhân viên" else result.group_label)
    return with_totals(result, result.totals) if result.totals is not None else result


def with_totals(result, totals):
    totals = dict(totals)
    values = {k.removeprefix("c_"): v for k, v in totals.items() if k.startswith("c_")}
    totals.update(aggregations._recompute(result.computed_columns, values))
    return replace(result, totals=totals)
