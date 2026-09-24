"""Bối cảnh màn hình dùng chung của Báo cáo tổng hợp và Bảng dữ liệu dạng báo cáo (ADR-042).

`activity_views.report` và `forms_builder.views.bang_xem` (bảng có nguồn báo cáo Sale/MKT, đợt 4)
cùng đọc tham số, dựng khối bảng, chip bộ lọc và tệp Excel ở đây — forms_builder không import
view của reports. Không có điều kiện quyền ở đây: phạm vi nằm trong `activity_service`.
"""
from io import BytesIO

from django.conf import settings
from django.http import HttpResponse

from core.audit import record
from core.constants import AuditAction
from core.exceptions import BusinessError
from core.pagination import pagination_context
from orders.models import WaybillItem
from reports import aggregations, excel, layout
from reports.services import activity_service as service, summary_service


def parameters(request):
    start, end = summary_service.default_range()
    group = request.GET.get("nhom", "day")
    aliases = {"tong-hop": "day", "nhan-vien": "person", "san-pham": "product", "thi-truong": "market"}
    return {
        "group": aliases.get(group, group),
        "start": summary_service.parse_day(request.GET.get("tu"), start),
        "end": summary_service.parse_day(request.GET.get("den"), end),
        # Nhiều sản phẩm (ADR-042 đợt 3): `sp` lặp lại; URL cũ `sp=A` vẫn là danh sách một mục
        "product": [p for p in request.GET.getlist("sp") if p],
        "market": request.GET.get("thi_truong", ""),
        "person": request.GET.get("nhan_su", ""),
        "team": request.GET.get("team", ""),
        "segment": request.GET.get("tep", ""),
    }


def with_query(request, **doi):
    """URL hiện tại với vài tham số đổi/bỏ (giá trị None là bỏ), về trang 1."""
    query = request.GET.copy()
    for key in ("trang",):
        query.pop(key, None)
    for key, value in doi.items():
        query.pop(key, None)
        if value is not None:
            query[key] = value
    return "?" + query.urlencode()


def export_response(request, source, result, params, gop=False, *, detail="Xuất báo cáo hoạt động ERP"):
    """Tệp Excel đúng thứ đang hiện: theo khối khi có cách xem theo nhân sự, trên toàn bộ dòng."""
    if aggregations.row_count(result) > getattr(settings, "EXPORT_MAX_ROWS", 50000):
        raise BusinessError("Thu hẹp bộ lọc để xuất báo cáo.")
    record(AuditAction.EXPORT, actor=request.user, target=source.table, detail=detail, request=request)
    subtitle = f"{params['start']} đến {params['end']}"
    if params.get("product"):
        subtitle += " · Sản phẩm: " + ", ".join(params["product"])
    if params.get("segment"):
        subtitle += " · Tệp khách hàng: " + ("chưa có" if params["segment"] == "__missing__" else params["segment"])
    blocks = None
    if getattr(result, "show_person", False):
        # Xuất theo khối như màn hình (ADR-042), trên toàn bộ dòng — không cắt trang
        items = list(result.rows)
        tieu_de = f"Toàn kỳ {params['start']:%d/%m} – {params['end']:%d/%m/%Y} · theo nhân sự"
        khoi_ky = period_block(request, source, result, items if len(items) <= summary_service.MAX_GROUPS else None, items, params, tieu_de)
        if gop:
            blocks = [khoi_ky, layout.days_block(items, layout.days_of(items), result)]
        else:
            blocks = [khoi_ky, *layout.day_blocks(aggregations.finish_rows(items, result), items, items, result)]
    book = excel.build_workbook(source.table.name, result, subtitle=subtitle, blocks=blocks)
    if source.kind == "delivery":
        sheet = book.create_sheet("Trạng thái giao hàng")
        sheet.append(["Trạng thái", "Số đơn"])
        for item in result.shipping:
            sheet.append([item["label"], item["count"]])
    data = BytesIO()
    book.save(data)
    response = HttpResponse(data.getvalue(),
                            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="bao-cao-tong-hop.xlsx"'
    return response


def product_options(user, source):
    """Danh sách tick Sản phẩm: chỉ sản phẩm có thật trong phạm vi quyền (Leader không thấy hàng
    team khác). Nguồn báo cáo: tên sản phẩm (`val_product`); vận đơn: mã kèm tên từ chi tiết đơn."""
    records = service.records(user, source)
    if source.kind == "delivery":
        cap = (WaybillItem.objects.for_records(records).order_by("product__code")
               .values_list("product__code", "product__name").distinct())
        return [{"value": code, "label": f"{code} — {name}"} for code, name in cap]
    return [{"value": name, "label": name} for name in summary_service.product_choices(records, source.table)]


def blocks_context(request, source, result, params, gop, *, page_size=100):
    """Bố cục khối như ảnh mẫu (ADR-042 đợt 2). Cách xem Tổng hợp: khối toàn kỳ theo nhân sự
    (cộng trong bộ nhớ, không truy vấn thêm) rồi mỗi ngày một khối có TỔNG CỘNG riêng và STT;
    Gộp thì một khối mỗi ngày một dòng. Cách xem khác: một khối như cũ. `rows` phẳng, `label_span`,
    `identity_columns` giữ cho Tổng quan và bài kiểm. `page_size`: Báo cáo tổng hợp 100 nhóm
    (ADR-035), Bảng dữ liệu chi tiết 25 dòng (quy tắc 1)."""
    show_team, show_person, show_leader = (getattr(result, flag, False) for flag in ("show_team", "show_person", "show_leader"))
    # Giới hạn nhóm như báo cáo hiện có; dòng đã ở bộ nhớ khi ≤ MAX_GROUPS (`summarize_in_memory`).
    items = list(result.rows[:summary_service.MAX_GROUPS + 1])
    ca_bo = items if len(items) <= summary_service.MAX_GROUPS else None
    ctx = {"result": result, "totals": aggregations.total_cells(result), "empty": not result.totals["so_dong"]}
    tieu_de_ky = f"Toàn kỳ {params['start']:%d/%m} – {params['end']:%d/%m/%Y} · theo nhân sự"
    if show_person and gop:
        # Gộp: mỗi ngày một dòng — phân trang trên danh sách ngày
        nguon = ca_bo if ca_bo is not None else items
        ngay = layout.days_of(nguon)
        ctx.update(pagination_context(request, ngay, "ngày", default_size=page_size))
        blocks = [period_block(request, source, result, ca_bo, items, params, tieu_de_ky),
                  layout.days_block(nguon, list(ctx["trang"]), result)]
    else:
        page_source = items if ca_bo is not None else result.rows
        ctx.update(pagination_context(request, page_source, "nhóm", default_size=page_size))
        page_items = list(ctx["trang"])
        rows = aggregations.finish_rows(page_items, result)
        if show_person:
            all_items = ca_bo if ca_bo is not None else page_items
            blocks = [period_block(request, source, result, ca_bo, items, params, tieu_de_ky),
                      *layout.day_blocks(rows, page_items, all_items, result)]
        else:
            for row, raw in zip(rows, page_items):
                row["kind"] = "row"
                if show_team:
                    row["team"] = raw["team_name"]
                if show_leader:
                    row["leader"] = raw["leader_name"] or "—"
            blocks = [layout.single_block(single_kinds(result, show_team, show_leader), rows, ctx["totals"])]
    ctx["blocks"] = blocks
    ctx["rows"] = layout.flat_rows(blocks) if show_person else blocks[0]["rows"]
    # Khối cuối là khối đang phân trang; cột danh tính của nó là thứ template cũ và bài kiểm đọc
    dai_dien = blocks[-1]
    ctx.update(label_span=dai_dien["label_span"], identity_columns=dai_dien["identity_columns"],
               identity_style=dai_dien["identity_style"])
    return ctx


def period_block(request, source, result, ca_bo, items, params, title):
    """Khối toàn kỳ theo nhân sự: từ dòng trong bộ nhớ khi ≤ MAX_GROUPS; chạm trần thì dùng kết
    quả cách xem Theo nhân viên (thêm truy vấn, hiếm)."""
    if ca_bo is not None:
        return layout.period_block(ca_bo, result, title)
    ky = {k: v for k, v in params.items() if k != "group"}
    nguoi = service.build(request.user, source, group="person", **ky)
    dong = list(nguoi.rows)
    return layout.period_block_from_rows(aggregations.finish_rows(dong, nguoi), dong, nguoi, title)


def single_kinds(result, show_team, show_leader):
    """Cột định danh của cách xem không theo ngày (bản vẽ 18.09): Team · nhóm · Leader."""
    kinds = []
    if show_team:
        kinds.append(("team", "Team", "team"))
    kinds.append(("nhom", result.group_label, "ngay" if result.group_is_date else "nhom"))
    if show_leader:
        kinds.append(("leader", "Leader", "leader"))
    return kinds


def filter_chips(request, params, ctx, *, show_group=True):
    """Hàng chip bộ lọc đang áp, render từ `params`; × của mỗi chip là link cùng URL bỏ đúng tham số
    (Kỳ bỏ cả `tu` và `den` để về mặc định; bỏ Team thì bỏ luôn Nhân sự). Không có chip Nguồn;
    Cách xem không bỏ được (Bảng dữ liệu chỉ có một cách xem nên không có chip này)."""
    def without(*keys):
        query = request.GET.copy()
        for key in keys:
            query.pop(key, None)
        return "?" + query.urlencode()
    # Form luôn gửi `tu`/`den`, nên "đang lọc kỳ" là kỳ KHÁC mặc định — không phải "có tham số"
    # (trước đây chip Kỳ có × ngay sau lần Áp dụng đầu tiên, TL-46)
    dang_loc_ky = (params["start"], params["end"]) != summary_service.default_range()
    chips = [{"label": "Kỳ", "value": f"{params['start']:%d/%m} – {params['end']:%d/%m/%Y}",
              "url": without("tu", "den") if dang_loc_ky else ""}]
    if show_group:
        chips.append({"label": "Cách xem", "value": dict(service.GROUPS).get(params["group"], params["group"]), "url": ""})
    if request.GET.get("gop") == "1":
        chips.append({"label": "Gộp", "value": "mỗi ngày một dòng", "url": without("gop")})
    if params["product"]:
        sp = params["product"]
        chips.append({"label": "Sản phẩm", "value": ", ".join(sp) if len(sp) <= 2 else f"{len(sp)} sản phẩm", "url": without("sp")})
    if params["market"]:
        chips.append({"label": "Thị trường", "value": "Chưa xác định" if params["market"] == "__missing__" else params["market"], "url": without("thi_truong")})
    if params.get("segment"):
        chips.append({"label": "Tệp", "value": "Chưa có" if params["segment"] == "__missing__" else params["segment"], "url": without("tep")})
    for key, param, query_key, label in (("teams", "team", "team", "Team"), ("people", "person", "nhan_su", "Nhân sự")):
        value = params[param]
        if value:
            name = next((item["label"] for item in ctx.get(key, ()) if str(item["id"]) == str(value)), value)
            chips.append({"label": label, "value": name, "url": without(query_key, *(("nhan_su",) if param == "team" else ()))})
    keep = request.GET.copy()
    for key in list(keep.keys()):
        if key not in ("nguon", "dang"):
            keep.pop(key)
    return {"chips": chips, "filters_active": sum(1 for chip in chips if chip["url"]), "clear_url": "?" + keep.urlencode()}
