"""Bố cục khối của Báo cáo tổng hợp như ảnh mẫu (ADR-040, đợt 2) — thuần, không truy vấn.

Cách xem Tổng hợp: khối ``period`` (toàn kỳ theo nhân sự) đứng đầu, rồi mỗi ngày một
khối ``day`` có TỔNG CỘNG riêng đứng ngay dưới tiêu đề và STT đếm lại từ 1; **Gộp**
(`?gop=1`) thì thay các khối ngày bằng một khối ``days`` mỗi ngày một dòng — chính là
bố cục trước 19.09. Các cách xem khác là một khối ``single`` như cũ. Mọi khối mang sẵn
cột định danh (ghim trái, `left` tính bằng biến CSS), dòng đã định dạng và dòng tổng —
template `reports/_bang_khoi.html` chỉ in.

Khối toàn kỳ cộng **trong bộ nhớ** từ chính các dòng ngày × người đã lấy (SUM kết hợp
được, phần đối soát cộng theo khoá) nên không tốn truy vấn; chạm trần `MAX_GROUPS` thì
tầng dịch vụ đưa kết quả "Theo nhân viên" vào (`period_block_from_rows`).
"""
from reports import aggregations

#: Chiều rộng và lớp CSS của từng loại cột định danh (biến khai ở `.report-view`)
WIDTH = {"team": "--w-team", "ngay": "--w-ngay", "nhom": "--w-nhom", "stt": "--w-stt",
         "person": "--w-nhan-su", "leader": "--w-leader"}
CSS = {"team": "id-team", "ngay": "id-ngay", "nhom": "id-nhom", "stt": "id-stt",
       "person": "id-nhan-su", "leader": "id-leader"}
#: Cột định danh của khối theo nhân sự (toàn kỳ và từng ngày) — như ảnh: STT · Team · Nhân sự; Leader thêm từ ADR-035
PERSON_KINDS = (("stt", "STT", "stt"), ("team", "Team", "team"), ("person", "Nhân sự", "person"), ("leader", "Leader", "leader"))
DAY_KINDS = (("nhom", "Ngày", "ngay"),)
TOTAL_LABEL = {"period": "TỔNG CỘNG · toàn kỳ", "day": "TỔNG CỘNG", "days": "TỔNG CỘNG · toàn kỳ", "single": "Tổng trong bộ lọc"}


def identity(kinds):
    """Cột định danh ghim trái: `left` của cột thứ 2+ là tổng chiều rộng các cột trước (biến
    CSS đặt trên `<table>`). Trả `(columns, style)`; mỗi cột `{code, label, kind, pos, edge}`."""
    columns, style, widths = [], [], []
    for pos, (code, label, width) in enumerate(kinds, start=1):
        columns.append({"code": code, "label": label, "kind": CSS[width], "pos": pos, "edge": pos == len(kinds)})
        if pos >= 2:
            style.append(f"--id-left-{pos}:calc({' + '.join(f'var({w})' for w in widths)})")
        widths.append(WIDTH[width])
    return columns, ";".join(style)


def block(kind, title, kinds, rows, totals, **extra):
    columns, style = identity(kinds)
    for row in rows:
        # Cặp (cột, giá trị) để template in đúng thứ tự mà không cần chỉ mục
        row["identity"] = list(zip(columns, row["identity"]))
    return {"kind": kind, "title": title, "identity_columns": columns, "identity_style": style,
            "label_span": len(columns), "total_label": TOTAL_LABEL[kind], "rows": rows, "totals": totals, **extra}


def person_row(stt, item, cells, raw=None):
    """Một dòng người: giữ cả khoá phẳng (`stt`, `team`, `person`, `leader`, `nhom`) cho bài kiểm,
    ô thô `raw` cho Excel, và dãy `identity` cho template."""
    team = item.get("team_name") or "—"
    person = item.get("person_name") or "—"
    leader = item.get("leader_name") or "—"
    return {"kind": "row", "stt": stt, "team": team, "person": person, "leader": leader,
            "nhom": item.get("nhom"), "cells": cells, "raw": raw, "identity": [stt, team, person, leader]}


def _row_key(item):
    """Khoá một dòng người: (ngày, mã); Bảng dữ liệu chi tiết từng lần nộp (ADR-040 đợt 4) có thêm
    id dòng nên hai lần nộp cùng ngày cùng người vẫn là hai dòng riêng."""
    return (item.get("nhom"), item.get("person_name"), item.get("record_id"))


def stt_by_day(items):
    """STT đếm lại từ 1 trong từng ngày, trên toàn bộ dòng để không đứt khi sang trang."""
    stt, dem = {}, {}
    for item in items:
        ngay = item.get("nhom")
        dem[ngay] = dem.get(ngay, 0) + 1
        stt[_row_key(item)] = dem[ngay]
    return stt


def period_block(items, result, title):
    """Khối toàn kỳ theo nhân sự, cộng trong bộ nhớ từ các dòng ngày × người; Team/Leader lấy ở
    dòng đầu gặp của người đó; sắp theo mã nhân sự."""
    tong = aggregations.subtotals(items, result, key="person_name")
    dau_tien = {}
    for item in items:
        dau_tien.setdefault(item.get("person_name"), item)
    rows = [person_row(stt, dau_tien[person], aggregations.format_cells(result, raw), raw)
            for stt, (person, raw) in enumerate(sorted(tong.items(), key=lambda kv: kv[0] or ""), start=1)]
    return block("period", title, PERSON_KINDS, rows, aggregations.total_cells(result), count=len(rows),
                 totals_raw=aggregations.total_values(result))


def period_block_from_rows(rows, page_items, result, title):
    """Khối toàn kỳ khi chạm trần: dùng kết quả cách xem Theo nhân viên đã tính bằng truy vấn."""
    out = [person_row(stt, item, row["cells"], aggregations.row_values(item, result)[1])
           for stt, (row, item) in enumerate(zip(rows, page_items), start=1)]
    for row, item in zip(out, page_items):
        row["person"] = item.get("nhom") or "—"
        row["identity"][2] = row["person"]
    return block("period", title, PERSON_KINDS, out, aggregations.total_cells(result), count=len(out),
                 totals_raw=aggregations.total_values(result))


def day_blocks(rows, page_items, all_items, result):
    """Mỗi ngày trên trang một khối: tiêu đề ngày, TỔNG CỘNG của ngày (cộng trên TOÀN BỘ dòng của
    ngày), dòng người có STT. Ngày bị tách trang thì trang sau ghi "(tiếp)" và lặp lại TỔNG CỘNG."""
    tong = aggregations.subtotals(all_items, result)
    stt = stt_by_day(all_items)
    tiep = bool(page_items) and any(
        item is not page_items[0] and item.get("nhom") == page_items[0].get("nhom")
        for item in all_items[: _index_of(all_items, page_items[0])])
    blocks, hien_tai = [], None
    for row, item in zip(rows, page_items):
        ngay = item.get("nhom")
        if hien_tai is None or hien_tai["nhom"] != ngay:
            tieu_de = aggregations.format_group(ngay, result) + (" (tiếp)" if tiep and not blocks else "")
            hien_tai = block("day", tieu_de, PERSON_KINDS, [], aggregations.format_cells(result, tong.get(ngay, [])),
                             nhom=ngay, totals_raw=tong.get(ngay, []))
            blocks.append(hien_tai)
        dong = person_row(stt.get(_row_key(item), ""), item, row["cells"], aggregations.row_values(item, result)[1])
        dong["nhom"] = row["nhom"]   # chuỗi ngày đã định dạng, như `finish_rows`
        dong["identity"] = list(zip(hien_tai["identity_columns"], dong["identity"]))
        hien_tai["rows"].append(dong)
    return blocks


def _index_of(items, item):
    for i, x in enumerate(items):
        if x is item:
            return i
    return 0


def days_block(all_items, page_days, result):
    """Gộp: mỗi ngày một dòng là TỔNG CỘNG của ngày đó (bố cục trước 19.09)."""
    tong = aggregations.subtotals(all_items, result)
    rows = [{"kind": "row", "nhom": aggregations.format_group(ngay, result), "raw": tong.get(ngay, []),
             "cells": aggregations.format_cells(result, tong.get(ngay, [])),
             "identity": [aggregations.format_group(ngay, result)]} for ngay in page_days]
    return block("days", "Theo ngày", DAY_KINDS, rows, aggregations.total_cells(result), count=len(rows),
                 totals_raw=aggregations.total_values(result))


def days_of(all_items):
    """Danh sách ngày theo thứ tự xuất hiện (mới nhất trước) — để phân trang khi Gộp."""
    out = []
    for item in all_items:
        if not out or out[-1] != item.get("nhom"):
            out.append(item.get("nhom"))
    return out


def single_block(kinds, rows, totals):
    """Cách xem khác: một khối, cột định danh như ADR-035 (Team · nhóm · Leader)."""
    for row in rows:
        row["identity"] = [row["nhom"] if code == "nhom" else row.get(code, "—") for code, _, _ in kinds]
    return block("single", "", kinds, rows, totals)


def flat_rows(blocks):
    """Dãy phẳng như trước đợt 2 (dòng `subtotal` rồi các dòng người) — cho bài kiểm và Tổng quan."""
    out = []
    for b in blocks:
        if b["kind"] == "day":
            out.append({"kind": "subtotal", "nhom": b["title"], "cells": b["totals"]})
            out.extend(b["rows"])
        elif b["kind"] != "period":
            out.extend(b["rows"])
    return out
