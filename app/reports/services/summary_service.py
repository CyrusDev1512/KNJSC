"""Màn hình Báo cáo tổng hợp — chọn bảng nguồn, dựng bối cảnh, xuất Excel.

Tầng dịch vụ (điều cấm 2). Phép tính nằm ở `reports/aggregations.py`; tệp này
chỉ lo phần gắn với người dùng: bảng nào được chọn (Q35 — đúng MỘT bảng trong
phạm vi quyền, không cộng gộp nhiều bảng vì đếm trùng doanh thu), bộ lọc mặc
định, và ghi nhật ký khi xuất (nguyên tắc P5).

Phạm vi quyền đi qua Custom Manager (quy tắc 11): danh sách bảng qua
`TableDef.objects.in_scope`, số liệu qua `DataRecord.objects.in_scope`. Gọi
`?nguon=` ra ngoài danh sách đó là 403, không phải danh sách rỗng (quy tắc 8).
"""
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from core.audit import record, record_denied
from core.constants import AuditAction
from core.exceptions import BusinessError, OutOfScopeError
from forms_builder.models import DataRecord, TableDef

from .. import aggregations, layout, marketing

#: Cách nhóm hợp lệ trên URL. "thi-truong" có mặt ở thanh tab nhưng chưa có
#: số liệu — hoãn theo Q36, chờ chốt backlog N9.
TABS = (
    ("tong-hop", "Tổng hợp"),
    ("nhan-vien", "Theo nhân viên"),
    ("san-pham", "Theo sản phẩm"),
    ("thi-truong", "Theo thị trường"),
)

#: Tab trên URL sang khoá nhóm của tầng phép tính.
GROUP_OF_TAB = {"tong-hop": "ngay", "nhan-vien": "nhan-vien", "san-pham": "san-pham"}

#: Trần số dòng nhóm lấy về một lượt. Dòng nhóm ít hơn bản ghi rất nhiều
#: (một tháng nhóm theo ngày là ~31 dòng), nên lấy cả rồi cắt trang trong bộ
#: nhớ — đỡ hai lệnh đếm và lấy trang của Paginator, giữ màn hình dưới trần
#: 10 lệnh truy vấn (AC-10.2). Trần này chỉ để chặn bảng có cột nhóm gần như
#: mỗi dòng một giá trị.
MAX_GROUPS = 2_000


def source_tables(user):
    """Các bảng chọn được làm nguồn số liệu: trong phạm vi quyền, đang dùng,
    và có ít nhất một cột mang nhãn ý nghĩa — bảng không nhãn thì không có gì
    để thống kê (ADR-001)."""
    tables = list(
        TableDef.objects.in_scope(user)
        .filter(Q(columns__meaning__gt="") | Q(erp_report__isnull=False), is_active=True)
        .distinct()
        .select_related("erp_report", "department")
        .prefetch_related("columns")
        .order_by("name")
    )
    # Các bộ phận đã được JOIN cùng bảng. Tái sử dụng đúng đối tượng của
    # hồ sơ cho khung trang, tránh truy vấn lặp khi thêm bộ lọc nhân sự.
    profile = getattr(user, "profile", None)
    if profile is not None and profile.department_id:
        for table in tables:
            if table.department_id == profile.department_id:
                profile.department = table.department
                break
    return tables


def pick_table(user, code, tables, *, request=None):
    """Chọn bảng nguồn theo `?nguon=`.

    Không gửi gì thì lấy bảng đầu danh sách; danh sách rỗng thì trả None để
    màn hình hiện trạng thái rỗng (không phải lỗi). Gửi mã ngoài danh sách —
    kể cả mã không tồn tại — thì từ chối 403, không phân biệt hai trường hợp
    để khỏi lộ bảng nào có thật (quy tắc 8, AC-3.6).
    """
    if not code:
        return tables[0] if tables else None
    for bang in tables:
        if bang.code == code:
            return bang
    record_denied(user, f"bao-cao/tong-hop/?nguon={code}", request)
    raise OutOfScopeError()


def default_range():
    """Khoảng lọc mặc định: từ đầu tháng này tới hôm nay — chặn quét cả bảng,
    và hiện sẵn trên ô lọc để người dùng luôn biết phạm vi đang áp."""
    hom_nay = timezone.localdate()
    return hom_nay.replace(day=1), hom_nay


def date_presets(today=None, *, start=None, end=None, key=None):
    """Chọn nhanh kỳ (ADR-038, sheet MKT): Hôm nay, Hôm qua, 7 ngày, Tuần này (thứ Hai → hôm nay,
    ADR-042), Tháng này, Tháng trước. Mỗi mục `{key, label, start, end, active}`. Chỉ **một** mục
    `active` (chủ dự án 01.10.2026: ngày 01 "Hôm nay" và "Tháng này" cùng khoảng nên từng sáng cả hai):
    mục `key` — nút vừa bấm, ô ẩn `ky` — nếu khoảng của nó khớp kỳ đang lọc, không thì mục khớp đầu tiên."""
    from datetime import timedelta

    hom_nay = today or timezone.localdate()
    dau_thang = hom_nay.replace(day=1)
    cuoi_thang_truoc = dau_thang - timedelta(days=1)
    muc = (
        ("hom-nay", "Hôm nay", hom_nay, hom_nay),
        ("hom-qua", "Hôm qua", hom_nay - timedelta(days=1), hom_nay - timedelta(days=1)),
        ("7-ngay", "7 ngày", hom_nay - timedelta(days=6), hom_nay),
        ("tuan-nay", "Tuần này", hom_nay - timedelta(days=hom_nay.weekday()), hom_nay),
        ("thang-nay", "Tháng này", dau_thang, hom_nay),
        ("thang-truoc", "Tháng trước", cuoi_thang_truoc.replace(day=1), cuoi_thang_truoc),
    )
    khop = [ma for ma, _, tu, den in muc if (start, end) == (tu, den)]
    sang = key if key in khop else (khop[0] if khop else None)
    return [{"key": ma, "label": label, "start": tu, "end": den, "active": ma == sang} for ma, label, tu, den in muc]


def parse_day(text, fallback):
    """Đọc một ô ngày trên thanh lọc. Chuỗi hỏng thì rơi về mặc định."""
    try:
        return date.fromisoformat(text)
    except (TypeError, ValueError):
        return fallback


def product_choices(scoped_qs, table):
    """Giá trị cho ô chọn sản phẩm: các sản phẩm có thật trong phạm vi quyền
    của người xem — Leader không thấy tên hàng của team khác.

    `scoped_qs` là queryset đã `in_scope`, dùng chung với phần tính toán để
    khỏi dựng lại phạm vi.
    """
    if table is None:
        return []
    return list(
        scoped_qs
        .filter(table=table)
        .exclude(val_product="")
        .order_by()
        .values_list("val_product", flat=True)
        .distinct()
        .order_by("val_product")
    )


def _money_by_currency(result, i, cot):
    """Ô tiền theo từng loại tiền của dòng TỔNG CỘNG: "4.321 USD · 2.234 CAD" — không bao giờ cộng hai loại
    tiền (ADR-046, TL-92)."""
    phan = [f"{aggregations.format_number(raw[i], cot.decimals)} {layout.currency_label(tien)}"
            for tien, raw in aggregations.total_rows(result) if raw[i] is not None]
    return " · ".join(phan) or "—"


def _headline(result):
    """Bốn ô số đầu trang, lấy từ chính dòng tổng cộng — không truy vấn thêm.

    Ưu tiên các cột theo thứ tự cột của bảng; bảng không có cột số nào thì
    hiện mỗi ô Số dòng. Nguồn tách loại tiền thì ô tiền ghi theo từng loại tiền.
    """
    o = []
    for i, cot in enumerate(result.columns):
        if cot.kind == "share":
            continue
        if result.currency_key and cot.money and cot.kind == "sum":
            text = _money_by_currency(result, i, cot)
        else:
            gia_tri = result.totals.get(
                f"c_{cot.code}" if cot.kind == "sum" else cot.code)
            text = aggregations.format_number(gia_tri, cot.decimals)
            text = text + cot.suffix if text != "—" else text
        o.append({
            "nhan": cot.label, "gia_tri": text,
            "code": cot.code, "kind": cot.kind, "money": cot.money,
        })
        if len(o) == 4:
            break
    if not o:
        o = [{"nhan": "Số dòng",
              "gia_tri": aggregations.format_number(result.totals.get("so_dong", 0)),
              "code": "so_dong", "kind": "sum", "money": False}]
    return o


def currency_note(result):
    """Chú thích đơn vị khi nguồn tách loại tiền (AC-46.1, 46.2): số giữ đúng như đã nhập, không quy đổi;
    cảnh báo khi có dòng chưa có loại tiền. Đọc từ tổng theo loại tiền đã có — không tốn truy vấn."""
    if not result.currency_key:
        return {"label": "", "warning": ""}
    thieu = sum(s.get("so_dong") or 0 for s in result.currency_sums if not s.get(result.currency_key))
    return {
        "label": ("Số tiền giữ đúng như đã nhập, không quy đổi tỉ giá; mỗi dòng một loại tiền, "
                  "TỔNG CỘNG tách theo loại tiền."),
        "warning": (f"{thieu} dòng chưa có loại tiền: cộng riêng ở nhóm “{layout.UNKNOWN_CURRENCY}”, "
                    "không vào loại tiền nào. Điền Loại tiền cho các dòng đó ở bảng nguồn.") if thieu else "",
    }


def currency_visible(result, columns):
    """Có hiện cột Loại tiền không: nguồn tách loại tiền, trừ bảng Marketing — chủ dự án chọn ẩn cột Loại
    tiền của báo cáo MKT (AC-47.6); dòng TỔNG CỘNG vẫn tách theo loại tiền."""
    return bool(result.currency_key) and not marketing.is_marketing(columns)


def display_rows(page_items, result):
    """Các dòng của một trang để hiện, kèm nhãn loại tiền của dòng khi nguồn tách loại tiền."""
    rows = aggregations.finish_rows(page_items, result)
    if result.currency_key:
        for row, item in zip(rows, page_items):
            row["tien"] = layout.currency_label(item.get(result.currency_key))
    return rows


def total_lines(result, so_nhom):
    """Các dòng TỔNG CỘNG ở chân bảng: một dòng như cũ, hoặc mỗi loại tiền một dòng "Tổng cộng · USD"."""
    if not result.currency_key:
        return [{"label": f"Tổng cộng · {so_nhom} {result.unit}", "currency": None,
                 "cells": aggregations.total_cells(result)}]
    return [layout.total_row("single", result, tien, raw, label="Tổng cộng")
            for tien, raw in aggregations.total_rows(result)]


def build_context(user, table, *, tab, date_from, date_to, product,
                  with_compare=False):
    """Bối cảnh phần số liệu của màn hình, cho một tab đã chọn.

    Một queryset phạm vi dùng chung cho mọi truy vấn của lượt này (quy tắc
    11); dòng nhóm lấy về dạng danh sách có trần `MAX_GROUPS` để cắt trang
    trong bộ nhớ. Bảng có cột Loại tiền thì loại tiền là một chiều nhóm và
    TỔNG CỘNG tách theo loại tiền như bản mới (ADR-046, TL-92).
    """
    scoped = DataRecord.objects.in_scope(user)
    columns = list(table.columns.all())
    tien = aggregations.currency_column_expression(columns)
    # Dòng tổng cộng tính từ chính các dòng nhóm đã lấy về (SUM kết hợp
    # được) — đỡ một lệnh aggregate; chỉ khi chạm trần MAX_GROUPS mới phải
    # cộng bằng lệnh riêng cho khỏi thiếu nhóm
    result = aggregations.summarize(
        table, scoped,
        group_key=GROUP_OF_TAB[tab], columns=columns,
        date_from=date_from, date_to=date_to, product=product,
        with_totals=False, currency_expression=tien,
    )
    result = marketing.adapt(result, columns)
    cac_nhom = []
    if result.ok:
        cac_nhom = list(result.rows[:MAX_GROUPS + 1])
        loc = {"columns": columns, "date_from": date_from, "date_to": date_to, "product": product}
        if len(cac_nhom) > MAX_GROUPS:
            cac_nhom = cac_nhom[:MAX_GROUPS]
            totals = aggregations.totals_only(table, scoped, **loc)
            currency_sums = (aggregations.currency_totals_only(table, scoped, currency_expression=tien, **loc)
                             if tien is not None else ())
        else:
            totals = aggregations.totals_from_rows(cac_nhom, result)
            currency_sums = aggregations.currency_sums_from_rows(cac_nhom, result)
        result = marketing.with_totals(replace(result, currency_sums=currency_sums), totals)
    boi_canh = {
        "kq": result,
        "o_so": _headline(result) if result.ok else [],
        "cac_nhom": cac_nhom,
        "cac_san_pham": product_choices(scoped, table),
        "cot_tien": result.ok and currency_visible(result, columns),
        "ghi_chu_tien": currency_note(result) if result.ok else {"label": "", "warning": ""},
    }
    if with_compare and result.ok:
        boi_canh["o_so"] = _compare(
            table, scoped, columns, boi_canh["o_so"], result,
            date_from=date_from, date_to=date_to, product=product, currency_expression=tien,
        )
    return boi_canh


def _compare(table, scoped_qs, columns, headline, result, *, date_from, date_to, product,
             currency_expression=None):
    """Gắn phụ chú "so với kỳ trước" vào các ô số: kỳ liền trước cùng độ dài.

    Chỉ chạy khi người dùng chủ động gửi khoảng lọc — tốn đúng một lệnh truy
    vấn; nếu màn hình chạm trần 10 lệnh (AC-10.2) thì đây là lệnh bỏ đầu tiên.
    Nguồn tách loại tiền: cột đếm cộng qua các loại tiền rồi so; cột tiền chỉ so
    khi hai kỳ cùng đúng một loại tiền — không trừ USD cho CAD (ADR-046, TL-92).
    """
    do_dai = (date_to - date_from).days + 1
    truoc_den = date_from - timedelta(days=1)
    truoc_tu = truoc_den - timedelta(days=do_dai - 1)
    loc = {"columns": columns, "date_from": truoc_tu, "date_to": truoc_den, "product": product}
    if result.currency_key and currency_expression is not None:
        theo_tien = aggregations.currency_totals_only(
            table, scoped_qs, currency_expression=currency_expression, **loc)
        tong_truoc = {}
        for dong in theo_tien:
            for khoa, gia_tri in dong.items():
                if (khoa == "so_dong" or khoa.startswith("c_")) and gia_tri is not None:
                    tong_truoc[khoa] = (tong_truoc.get(khoa) or Decimal("0")) + gia_tri
        tien_truoc = {d[result.currency_key] or "" for d in theo_tien}
        tien_nay = [t for t, _ in result.currency_totals]
        mot_tien = tien_nay[0] if len(tien_nay) == 1 and tien_truoc <= set(tien_nay) else None
        hien_tien = dict(result.currency_totals).get(mot_tien, {}) if mot_tien is not None else {}
    else:
        tong_truoc = aggregations.totals_only(table, scoped_qs, **loc)
        mot_tien, hien_tien = None, None
    for o in headline:
        if o["kind"] != "sum":
            continue
        khoa = "so_dong" if o["code"] == "so_dong" else f"c_{o['code']}"
        if hien_tien is not None and o.get("money"):
            if mot_tien is None:
                o["phu"] = {"chieu": "", "text": "nhiều loại tiền, không so", "khong_so": True}
                continue
            hien = hien_tien.get(khoa) or Decimal("0")
        else:
            hien = result.totals.get(khoa) or Decimal("0")
        truoc = tong_truoc.get(khoa) or Decimal("0")
        lech = Decimal(hien) - Decimal(truoc)
        if lech > 0:
            o["phu"] = {"chieu": "len", "text": "+" + aggregations.format_number(lech, 2)}
        elif lech < 0:
            o["phu"] = {"chieu": "xuong", "text": "−" + aggregations.format_number(-lech, 2)}
        else:
            o["phu"] = {"chieu": "", "text": "không đổi"}
    return headline


# ══ XUẤT EXCEL — FR-5.6 ═══════════════════════════════════════════

def build_export(user, table, *, tab, date_from, date_to, product, request=None):
    """Chạy lại đúng phép tính đang hiển thị, không cắt trang, trả dữ liệu
    cho tệp Excel. Ghi nhật ký TRƯỚC khi trả — nguyên tắc P5, BR-6.

    Ném `BusinessError` khi kết quả vượt giới hạn xuất (NFR-14) hoặc bảng
    không thống kê được.
    """
    columns = list(table.columns.all())
    result = aggregations.summarize(
        table, DataRecord.objects.in_scope(user),
        group_key=GROUP_OF_TAB[tab], columns=columns,
        date_from=date_from, date_to=date_to, product=product,
        currency_expression=aggregations.currency_column_expression(columns),
    )
    if not result.ok:
        raise BusinessError("Bảng nguồn không có cột phù hợp để thống kê theo cách này.")

    so_nhom = result.rows.count()
    gioi_han = getattr(settings, "EXPORT_MAX_ROWS", 50_000)
    if so_nhom > gioi_han:
        raise BusinessError(
            f"Kết quả có {so_nhom} dòng, vượt giới hạn xuất {gioi_han:,} dòng. "
            "Thu hẹp khoảng lọc rồi xuất lại."
        )

    # Chi tiết chỉ ghi tham số lọc, không ghi số liệu (điều cấm 6)
    record(
        AuditAction.EXPORT, actor=user, target=table,
        detail=(f"Xuất Excel báo cáo tổng hợp — bảng {table.code}, tab {tab}, "
                f"{date_from or '…'} đến {date_to or '…'}, {so_nhom} dòng nhóm"),
        request=request,
    )
    adapted = marketing.adapt(result, columns)
    # Bảng không phải Marketing cũng phải qua bước dựng TỔNG CỘNG theo loại tiền (TL-92)
    return marketing.with_totals(adapted, adapted.totals)
