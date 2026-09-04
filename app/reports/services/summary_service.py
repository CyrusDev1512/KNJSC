"""Màn hình Báo cáo tổng hợp — chọn bảng nguồn, dựng bối cảnh, xuất Excel.

Tầng dịch vụ (điều cấm 2). Phép tính nằm ở `reports/aggregations.py`; tệp này
chỉ lo phần gắn với người dùng: bảng nào được chọn (Q35 — đúng MỘT bảng trong
phạm vi quyền, không cộng gộp nhiều bảng vì đếm trùng doanh thu), bộ lọc mặc
định, và ghi nhật ký khi xuất (nguyên tắc P5).

Phạm vi quyền đi qua Custom Manager (quy tắc 11): danh sách bảng qua
`TableDef.objects.in_scope`, số liệu qua `DataRecord.objects.in_scope`. Gọi
`?nguon=` ra ngoài danh sách đó là 403, không phải danh sách rỗng (quy tắc 8).
"""
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.utils import timezone

from core.audit import record, record_denied
from core.constants import AuditAction
from core.exceptions import BusinessError, OutOfScopeError
from forms_builder.models import DataRecord, TableDef

from .. import aggregations

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
    return list(
        TableDef.objects.in_scope(user)
        .filter(is_active=True, columns__meaning__gt="")
        .distinct()
        .order_by("name")
    )


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


def _headline(result):
    """Bốn ô số đầu trang, lấy từ chính dòng tổng cộng — không truy vấn thêm.

    Ưu tiên các cột theo thứ tự cột của bảng; bảng không có cột số nào thì
    hiện mỗi ô Số dòng.
    """
    o = []
    for cot in result.columns:
        if cot.kind == "share":
            continue
        gia_tri = result.totals.get(
            f"c_{cot.code}" if cot.kind == "sum" else cot.code)
        text = aggregations.format_number(gia_tri, cot.decimals)
        o.append({
            "nhan": cot.label,
            "gia_tri": text + cot.suffix if text != "—" else text,
            "code": cot.code, "kind": cot.kind,
        })
        if len(o) == 4:
            break
    if not o:
        o = [{"nhan": "Số dòng",
              "gia_tri": aggregations.format_number(result.totals.get("so_dong", 0)),
              "code": "so_dong", "kind": "sum"}]
    return o


def build_context(user, table, *, tab, date_from, date_to, product,
                  with_compare=False):
    """Bối cảnh phần số liệu của màn hình, cho một tab đã chọn.

    Một queryset phạm vi dùng chung cho mọi truy vấn của lượt này (quy tắc
    11); dòng nhóm lấy về dạng danh sách có trần `MAX_GROUPS` để cắt trang
    trong bộ nhớ.
    """
    scoped = DataRecord.objects.in_scope(user)
    columns = list(table.columns.all())
    # Dòng tổng cộng tính từ chính các dòng nhóm đã lấy về (SUM kết hợp
    # được) — đỡ một lệnh aggregate; chỉ khi chạm trần MAX_GROUPS mới phải
    # cộng bằng lệnh riêng cho khỏi thiếu nhóm
    result = aggregations.summarize(
        table, scoped,
        group_key=GROUP_OF_TAB[tab], columns=columns,
        date_from=date_from, date_to=date_to, product=product,
        with_totals=False,
    )
    cac_nhom = []
    if result.ok:
        cac_nhom = list(result.rows[:MAX_GROUPS + 1])
        if len(cac_nhom) > MAX_GROUPS:
            cac_nhom = cac_nhom[:MAX_GROUPS]
            totals = aggregations.totals_only(
                table, scoped, columns=columns,
                date_from=date_from, date_to=date_to, product=product,
            )
        else:
            totals = aggregations.totals_from_rows(cac_nhom, result)
        result = aggregations.attach_totals(result, totals)
    boi_canh = {
        "kq": result,
        "o_so": _headline(result) if result.ok else [],
        "cac_nhom": cac_nhom,
        "cac_san_pham": product_choices(scoped, table),
    }
    if with_compare and result.ok:
        boi_canh["o_so"] = _compare(
            table, scoped, columns, boi_canh["o_so"], result,
            date_from=date_from, date_to=date_to, product=product,
        )
    return boi_canh


def _compare(table, scoped_qs, columns, headline, result, *, date_from, date_to, product):
    """Gắn phụ chú "so với kỳ trước" vào các ô số: kỳ liền trước cùng độ dài.

    Chỉ chạy khi người dùng chủ động gửi khoảng lọc — tốn đúng một lệnh truy
    vấn; nếu màn hình chạm trần 10 lệnh (AC-10.2) thì đây là lệnh bỏ đầu tiên.
    """
    do_dai = (date_to - date_from).days + 1
    truoc_den = date_from - timedelta(days=1)
    truoc_tu = truoc_den - timedelta(days=do_dai - 1)
    tong_truoc = aggregations.totals_only(
        table, scoped_qs, columns=columns,
        date_from=truoc_tu, date_to=truoc_den, product=product,
    )
    for o in headline:
        if o["kind"] != "sum":
            continue
        khoa = "so_dong" if o["code"] == "so_dong" else f"c_{o['code']}"
        truoc = tong_truoc.get(khoa) or Decimal("0")
        hien = result.totals.get(khoa) or Decimal("0")
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
    return result
