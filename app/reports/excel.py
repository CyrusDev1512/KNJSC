"""Dựng tệp Excel cho báo cáo tổng hợp — FR-5.6.

Chỉ chứa cơ khí openpyxl, không truy vấn gì: nhận `SummaryResult` đã tính
xong và ghi ra Workbook. Số ghi dạng `Decimal` nguyên trạng, không đổi sang
float (BR-8) — Excel đọc được và số khớp tuyệt đối với màn hình.

Giai đoạn 7 sẽ có `core/excel.py` cho nhập và xuất bảng thô; tệp này chỉ
phục vụ báo cáo tổng hợp và có thể được gộp về đó sau.
"""
from openpyxl import Workbook
from openpyxl.styles import Font

from core.excel import neutralise_formulas

from . import aggregations


def build_workbook(title, result, subtitle="", blocks=None):
    """Một sheet: tiêu đề, dòng phụ, bảng số liệu, dòng cuối là tổng cộng. Có `blocks` (Báo cáo tổng
    hợp, ADR-042/046) thì xuất theo khối như màn hình — mọi cách xem, chế độ và loại tiền; không có
    `blocks` là đường cũ của báo cáo theo bảng (`summary_service`)."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Bao cao tong hop"

    dam = Font(bold=True)
    ws.append([title])
    ws["A1"].font = dam
    unit_note = getattr(result, 'currency_warning', '') or getattr(result, 'currency_label', '')
    ws.append([' · '.join(part for part in (subtitle, unit_note) if part)])
    ws.append([])
    if blocks:
        return _khoi(wb, ws, result, blocks, dam)

    show_team = getattr(result, 'show_team', False)
    show_person = getattr(result, 'show_person', False)
    show_leader = show_person or getattr(result, 'show_leader', False)
    # Cột danh tính đi kèm cột nhóm, cùng thứ tự với màn hình (ADR-035)
    after = (['STT', 'Nhân sự'] if show_person else []) + (['Leader'] if show_leader else [])
    ws.append((['Team'] if show_team else []) + [result.group_label] + after + [c.label for c in result.columns])
    for o in ws[ws.max_row]:
        o.font = dam

    # Tổng hợp xuất theo khối ngày như màn hình (AC-22.15): dòng Tổng ngày trước các dòng
    # của ngày, STT đếm lại từ 1. Các cách xem khác vẫn đi từng dòng.
    # Dòng đã ở bộ nhớ (≤ MAX_GROUPS) thì dùng luôn; queryset lớn thì đi từng dòng
    items = result.rows if isinstance(result.rows, list) else (list(result.rows) if show_person else result.rows.iterator())
    tong_ngay = aggregations.subtotals(items, result) if show_person else {}
    so_nhom, ngay_truoc, stt = 0, object(), 0
    for item in items:
        nhom, cells = aggregations.row_values(item, result)
        if show_person and nhom != ngay_truoc:
            ngay_truoc, stt = nhom, 0
            ws.append(([''] if show_team else []) + [f"Tổng ngày {aggregations.format_group(nhom, result)}"]
                      + [''] * len(after) + tong_ngay[nhom])
            for o in ws[ws.max_row]:
                o.font = dam
        stt += 1
        identity = ([stt, item['person_name']] if show_person else []) + ([item['leader_name'] or '—'] if show_leader else [])
        ws.append(([item['team_name']] if show_team else []) + [aggregations.format_group(nhom, result)] + identity + cells)
        so_nhom += 1

    ws.append(([''] if show_team else []) + [f"Tổng cộng · {so_nhom} {result.unit}"] + [''] * len(after) + aggregations.total_values(result))
    for o in ws[ws.max_row]:
        o.font = dam

    return neutralise_formulas(wb)


def _dam(ws, dam):
    for o in ws[ws.max_row]:
        o.font = dam


def _ghi_khoi(ws, result, b, dam):
    """Một khối: hàng tiêu đề cột, các dòng TỔNG CỘNG đứng đầu như màn hình (mỗi loại tiền một dòng,
    ô Loại tiền riêng — ADR-046), rồi các dòng (số thô, đúng như màn hình, không quy đổi)."""
    nhan = [c["label"] for c in b["identity_columns"]]
    ws.append(nhan + [c.label for c in result.columns]); _dam(ws, dam)
    for tong in b["total_rows"]:
        dinh_danh = [tong["label"]] + [''] * (b["total_span"] - 1)
        if b["tien_column"] is not None:
            dinh_danh.append(tong["currency"])
        ws.append(dinh_danh + list(tong["raw"])); _dam(ws, dam)
    for row in b["rows"]:
        ws.append([v for _, v in row["identity"]] + list(row["raw"]))


#: Tên sheet theo khối đứng đầu (tên sheet Excel không dấu, ≤ 31 ký tự)
SHEET = {"day": "Theo ngay", "days": "Theo ngay", "submissions": "Tung lan nop", "single": "Bao cao tong hop"}


def _khoi(wb, ws, result, blocks, dam):
    """Chế độ Cộng theo ngày: sheet 1 "Toan ky theo nhan su" = khối toàn kỳ; sheet 2 "Theo ngay" = từng
    ngày một khối (hoặc mỗi ngày một dòng khi Gộp). Chế độ Từng lần nộp và các cách xem một khối: một
    sheet gồm mọi khối. Cùng số với màn hình vì cùng `layout` dựng."""
    if blocks[0]["kind"] == "period":
        ws.title = "Toan ky theo nhan su"
        ky = blocks[0]
        ws.append([ky["title"]]); _dam(ws, dam)
        _ghi_khoi(ws, result, ky, dam)
        ngay, con_lai = wb.create_sheet("Theo ngay"), blocks[1:]
    else:
        ws.title = SHEET.get(blocks[0]["kind"], "Bao cao tong hop")
        ngay, con_lai = ws, blocks
    for b in con_lai:
        if b["kind"] == "day" and b["title"]:
            ngay.append([f"Ngày {b['title']}"]); _dam(ngay, dam)
        elif b["kind"] == "submissions":
            ngay.append([b["title"]]); _dam(ngay, dam)
        _ghi_khoi(ngay, result, b, dam)
        ngay.append([])
    return neutralise_formulas(wb)
