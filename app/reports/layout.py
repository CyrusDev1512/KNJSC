"""Bố cục khối của Báo cáo tổng hợp như ảnh mẫu (ADR-042, đợt 2) — thuần, không truy vấn.

Cách xem Tổng hợp: khối ``period`` (toàn kỳ theo nhân sự) đứng đầu, rồi mỗi ngày một
khối ``day`` có TỔNG CỘNG riêng đứng ngay dưới tiêu đề và STT đếm lại từ 1; **Gộp**
(`?gop=1`) thì thay các khối ngày bằng một khối ``days`` mỗi ngày một dòng — chính là
bố cục trước 19.09. Các cách xem khác là một khối ``single`` như cũ. Mọi khối mang sẵn
cột định danh (cột đứng yên khi kéo ngang có `left` tính bằng biến CSS, cột còn lại trôi theo),
dòng đã định dạng và các dòng tổng — template `reports/_bang_khoi.html` chỉ in.

**Không quy đổi tiền (ADR-046).** Nguồn có cột Loại tiền thì mỗi dòng một loại tiền: khối có thêm
cột định danh **Loại tiền** (cuối cùng, sát cột số) và **mỗi loại tiền một dòng TỔNG CỘNG**
(`total_rows`), không bao giờ cộng hai loại tiền. **Chế độ Từng lần nộp** (cách xem Tổng hợp):
khối toàn kỳ vẫn đứng đầu, rồi mỗi ngày một khối, mỗi lần nộp một dòng có cột **Lần nộp**
("Lần 2 · 16:40"); Gộp thì một khối ``submissions`` gồm mọi lần nộp trong kỳ.

Khối toàn kỳ cộng **trong bộ nhớ** từ chính các dòng ngày × người đã lấy (SUM kết hợp
được, phần đối soát cộng theo khoá) nên không tốn truy vấn; chạm trần `MAX_GROUPS` thì
tầng dịch vụ đưa kết quả "Theo nhân viên" vào (`period_block_from_rows`).
"""
from django.utils import timezone

from core.money import currency_rank
from reports import aggregations

#: Chiều rộng và lớp CSS của từng loại cột định danh (biến khai ở `.report-view`)
WIDTH = {"team": "--w-team", "ngay": "--w-ngay", "nhom": "--w-nhom", "stt": "--w-stt",
         "person": "--w-nhan-su", "leader": "--w-leader", "lan": "--w-lan", "tien": "--w-tien"}
CSS = {"team": "id-team", "ngay": "id-ngay", "nhom": "id-nhom", "stt": "id-stt",
       "person": "id-nhan-su", "leader": "id-leader", "lan": "id-lan", "tien": "id-tien"}
#: Cột định danh của khối theo nhân sự (toàn kỳ và từng ngày) — như ảnh: STT · Team · Nhân sự; Leader thêm từ ADR-035
PERSON_KINDS = (("stt", "STT", "stt"), ("team", "Team", "team"), ("person", "Nhân sự", "person"), ("leader", "Leader", "leader"))
DAY_KINDS = (("nhom", "Ngày", "ngay"),)
#: Khối Gộp của chế độ Từng lần nộp: mọi lần nộp trong kỳ, như mockup 28.09 (ADR-046)
SUBMISSION_KINDS = (("nhom", "Ngày", "ngay"), ("person", "Nhân sự", "person"))
LAN_KIND = ("lan", "Lần nộp", "lan")
TIEN_KIND = ("tien", "Loại tiền", "tien")
TOTAL_LABEL = {"period": "TỔNG CỘNG · toàn kỳ", "day": "TỔNG CỘNG", "days": "TỔNG CỘNG · toàn kỳ",
               "submissions": "TỔNG CỘNG · toàn kỳ", "single": "Tổng trong bộ lọc"}
#: Nhãn ngắn của dòng TỔNG CỘNG trên màn hình: nằm gọn trong ô Nhân sự (tiêu đề khối đã nói toàn kỳ hay
#: ngày nào, mã tiền ở ô Loại tiền); Excel vẫn ghi nhãn dài `TOTAL_LABEL` kèm loại tiền
TOTAL_SHORT = {"single": "Tổng trong bộ lọc"}
#: Cột định danh đứng yên khi kéo ngang, ngoài cột đầu (STT, hay Ngày ở khối Gộp) — chủ dự án duyệt mockup
#: 02.10.2026: đủ biết dòng của ai, ngày nào, tiền gì; Team, Leader, Lần nộp giữ chỗ nhưng trôi theo, nhường
#: chỗ cho cột số
STICKY_CODES = ("person", "nhom", "tien")
#: Cột định danh ẩn theo loại nguồn (chủ dự án 03.10.2026, ADR-047): báo cáo MKT luôn VND nên cột Loại tiền thừa,
#: cột Lần nộp cũng bỏ — hai lần nộp cùng ngày vẫn là hai dòng. Chỉ đổi hiển thị (màn hình và Excel), không đổi
#: cách cộng tổng. Sale bỏ cột Lần nộp từ 04.10.2026 nhưng giữ Loại tiền: một người nộp được nhiều loại tiền (ADR-046).
HIDDEN_IDENTITY = {"mkt": ("lan", "tien"), "sale": ("lan",)}
#: Nhãn của loại tiền trống (báo cáo cũ chưa có Loại tiền) — cùng chữ với cảnh báo của dịch vụ
UNKNOWN_CURRENCY = "Chưa rõ"


def identity(kinds):
    """Cột định danh: cột đầu và các cột `STICKY_CODES` đứng yên khi kéo ngang, `left` của chúng là tổng
    chiều rộng các cột *đứng yên* đứng trước (biến CSS đặt trên `<table>`; mỗi cột rộng cố định nên cộng ra
    đúng); cột khác trôi theo. Bóng mép ở cột đứng yên cuối. Trả `(columns, style)`; mỗi cột
    `{code, label, kind, pos, sticky, edge}`."""
    columns, style, widths = [], [], []
    for pos, (code, label, width) in enumerate(kinds, start=1):
        sticky = pos == 1 or code in STICKY_CODES
        columns.append({"code": code, "label": label, "kind": CSS[width], "pos": pos, "sticky": sticky, "edge": False})
        if sticky:
            if widths:
                style.append(f"--id-left-{pos}:calc({' + '.join(f'var({w})' for w in widths)})")
            widths.append(WIDTH[width])
    dung_yen = [c for c in columns if c["sticky"]]
    if dung_yen:
        dung_yen[-1]["edge"] = True
    return columns, ";".join(style)


def currency_label(code):
    """Chữ hiện ở cột Loại tiền: mã tiền, trống thì "Chưa rõ"."""
    return code or UNKNOWN_CURRENCY


def visible(kinds, result):
    """Bỏ các cột định danh ẩn của loại nguồn (`HIDDEN_IDENTITY`)."""
    an = HIDDEN_IDENTITY.get(getattr(result, "source_kind", ""), ())
    return tuple(k for k in kinds if k[0] not in an)


def with_currency(kinds, result):
    """Thêm cột Loại tiền vào cuối cột định danh khi nguồn tách loại tiền (ADR-046), trừ cột ẩn của nguồn."""
    return visible(tuple(kinds) + ((TIEN_KIND,) if result.currency_key else ()), result)


def total_row(kind, result, tien, raw, *, label=None):
    """Một dòng TỔNG CỘNG: nhãn (kèm loại tiền khi tách), ô đã định dạng so màu với tổng cùng loại
    tiền, và ô thô cho Excel."""
    nhan = label or TOTAL_LABEL[kind]
    if result.currency_key:
        nhan = f"{nhan} · {currency_label(tien)}"
    return {"label": nhan, "currency": currency_label(tien) if result.currency_key else None,
            "cells": aggregations.format_cells(result, raw, tien), "raw": raw}


def overall_totals(kind, result):
    """Các dòng TỔNG CỘNG toàn bộ kết quả — mỗi loại tiền một dòng (hoặc một dòng khi không tách)."""
    return [total_row(kind, result, tien, raw) for tien, raw in aggregations.total_rows(result)]


def block(kind, title, kinds, rows, total_rows, **extra):
    columns, style = identity(kinds)
    for row in rows:
        # Cặp (cột, giá trị) để template in đúng thứ tự mà không cần chỉ mục
        row["identity"] = list(zip(columns, row["identity"]))
    # Excel: nhãn TỔNG CỘNG trải qua các cột định danh, trừ cột Loại tiền khi có (ô riêng). Màn hình in mỗi
    # cột định danh một ô (cột trôi không được che cột số), nhãn ngắn ở ô `total_at`: Nhân sự, không có thì cột đầu
    span = len(columns) - (1 if columns and columns[-1]["code"] == "tien" else 0)
    codes = [c["code"] for c in columns]
    return {"kind": kind, "title": title, "identity_columns": columns, "identity_style": style,
            "label_span": len(columns), "total_span": span, "tien_column": columns[-1] if span < len(columns) else None,
            "total_label": TOTAL_LABEL[kind], "total_short": TOTAL_SHORT.get(kind, "TỔNG CỘNG"),
            "total_at": "person" if "person" in codes else (codes[0] if codes else None),
            "rows": rows, "total_rows": total_rows, **extra}


def submission_label(item):
    """"Lần 2 · 16:40" — số thứ tự lần nộp trong ngày của người đó và giờ nộp (giờ Việt Nam);
    nộp vào hôm khác ngày báo cáo thì kèm ngày nộp: "Lần 1 · 08:05 29/09"."""
    lan, gio = item.get("lan"), item.get("gio")
    if gio is None:
        return f"Lần {lan}" if lan else "—"
    gio = timezone.localtime(gio)
    nhan = f"Lần {lan} · {gio:%H:%M}" if lan else f"{gio:%H:%M}"
    ngay = item.get("nhom")
    if ngay is not None and hasattr(ngay, "day") and gio.date() != ngay:
        nhan += f" {gio:%d/%m}"
    return nhan


def person_row(stt, item, cells, raw=None, kinds=PERSON_KINDS, result=None):
    """Một dòng người: giữ cả khoá phẳng (`stt`, `team`, `person`, `leader`, `nhom`) cho bài kiểm,
    ô thô `raw` cho Excel, và dãy `identity` theo đúng `kinds` cho template."""
    team = item.get("team_name") or "—"
    person = item.get("person_name") or "—"
    leader = item.get("leader_name") or "—"
    khoa_tien = result.currency_key if result is not None else ""
    tien = currency_label(item.get(khoa_tien)) if khoa_tien else None
    gia_tri = {"stt": stt, "team": team, "person": person, "leader": leader, "tien": tien,
               "lan": submission_label(item), "nhom": item.get("nhom")}
    return {"kind": "row", "stt": stt, "team": team, "person": person, "leader": leader, "currency": tien,
            "nhom": item.get("nhom"), "cells": cells, "raw": raw,
            "identity": [gia_tri[code] for code, _, _ in kinds]}


def _row_key(item):
    """Khoá một dòng người: (ngày, mã, loại tiền); chế độ Từng lần nộp có thêm id dòng nên hai lần
    nộp cùng ngày cùng người vẫn là hai dòng riêng."""
    return (item.get("nhom"), item.get("person_name"), item.get(aggregations.CURRENCY_KEY), item.get("record_id"))


def stt_by_day(items):
    """STT đếm lại từ 1 trong từng ngày, trên toàn bộ dòng để không đứt khi sang trang."""
    stt, dem = {}, {}
    for item in items:
        ngay = item.get("nhom")
        dem[ngay] = dem.get(ngay, 0) + 1
        stt[_row_key(item)] = dem[ngay]
    return stt


def _by_currency(tong, result):
    """`{(nhóm, tiền): raw}` → `{nhóm: [(tiền, raw), …]}` xếp theo `currency_rank`; không tách loại
    tiền thì `{nhóm: [("", raw)]}`."""
    out = {}
    if not result.currency_key:
        return {nhom: [("", raw)] for nhom, raw in tong.items()}
    for (nhom, tien), raw in tong.items():
        out.setdefault(nhom, []).append((tien or "", raw))
    for danh_sach in out.values():
        danh_sach.sort(key=lambda cap: (currency_rank(cap[0]), cap[0]))
    return out


def _subtotal_key(key, result):
    return (key, result.currency_key) if result.currency_key else key


def period_block(items, result, title):
    """Khối toàn kỳ theo nhân sự, cộng trong bộ nhớ từ các dòng ngày × người; Team/Leader lấy ở
    dòng đầu gặp của người đó; sắp theo mã nhân sự, rồi loại tiền (mỗi người mỗi loại tiền một dòng)."""
    kinds = with_currency(PERSON_KINDS, result)
    tong = _by_currency(aggregations.subtotals(items, result, key=_subtotal_key("person_name", result)), result)
    dau_tien = {}
    for item in items:
        dau_tien.setdefault(item.get("person_name"), item)
    rows, stt = [], 0
    for person in sorted(tong, key=lambda p: p or ""):
        for tien, raw in tong[person]:
            stt += 1
            item = {**dau_tien[person], aggregations.CURRENCY_KEY: tien} if result.currency_key else dau_tien[person]
            rows.append(person_row(stt, item, aggregations.format_cells(result, raw, tien), raw, kinds, result))
    # Đếm người, không đếm dòng: một người hai loại tiền là hai dòng nhưng vẫn một nhân sự
    return block("period", title, kinds, rows, overall_totals("period", result), count=len(tong))


def period_block_from_rows(rows, page_items, result, title):
    """Khối toàn kỳ khi chạm trần: dùng kết quả cách xem Theo nhân viên đã tính bằng truy vấn."""
    kinds = with_currency(PERSON_KINDS, result)
    out = [person_row(stt, item, row["cells"], aggregations.row_values(item, result)[1], kinds, result)
           for stt, (row, item) in enumerate(zip(rows, page_items), start=1)]
    vi_tri = [code for code, _, _ in kinds].index("person")
    for row, item in zip(out, page_items):
        row["person"] = item.get("nhom") or "—"
        row["identity"][vi_tri] = row["person"]
    return block("period", title, kinds, out, overall_totals("period", result),
                 count=len({item.get("nhom") for item in page_items}))


def day_kinds(result):
    """Cột định danh của khối ngày: STT · Team · Nhân sự · Leader, thêm Lần nộp ở chế độ Từng lần nộp
    và Loại tiền khi tách loại tiền."""
    kinds = PERSON_KINDS + ((LAN_KIND,) if getattr(result, "mode", "") == "tung-lan" else ())
    return with_currency(kinds, result)


def day_blocks(rows, page_items, all_items, result):
    """Mỗi ngày trên trang một khối: tiêu đề ngày, TỔNG CỘNG của ngày (cộng trên TOÀN BỘ dòng của
    ngày, mỗi loại tiền một dòng), dòng người có STT. Ngày bị tách trang thì trang sau ghi "(tiếp)"
    và lặp lại TỔNG CỘNG."""
    kinds = day_kinds(result)
    tong = _by_currency(aggregations.subtotals(all_items, result, key=_subtotal_key("nhom", result)), result)
    stt = stt_by_day(all_items)
    tiep = bool(page_items) and any(
        item is not page_items[0] and item.get("nhom") == page_items[0].get("nhom")
        for item in all_items[: _index_of(all_items, page_items[0])])
    blocks, hien_tai = [], None
    for row, item in zip(rows, page_items):
        ngay = item.get("nhom")
        if hien_tai is None or hien_tai["nhom"] != ngay:
            tieu_de = aggregations.format_group(ngay, result) + (" (tiếp)" if tiep and not blocks else "")
            tong_ngay = [total_row("day", result, tien, raw) for tien, raw in tong.get(ngay, [])]
            hien_tai = block("day", tieu_de, kinds, [], tong_ngay, nhom=ngay)
            blocks.append(hien_tai)
        dong = person_row(stt.get(_row_key(item), ""), item, row["cells"], aggregations.row_values(item, result)[1],
                          kinds, result)
        dong["nhom"] = row["nhom"]   # chuỗi ngày đã định dạng, như `finish_rows`
        dong["identity"] = list(zip(hien_tai["identity_columns"], dong["identity"]))
        _gan_lan_nop(dong, item)
        hien_tai["rows"].append(dong)
    return blocks


def _gan_lan_nop(dong, item):
    """Dòng là đúng một lần nộp (chế độ Từng lần nộp): mang id báo cáo ngày cho nút ✎ của Admin và nhãn "Lần N ·
    giờ" cho nhãn đọc màn hình của nút (ADR-050). Khối toàn kỳ, TỔNG CỘNG, Vận đơn không gọi hàm này."""
    dong["report_id"] = item.get("report_id")
    dong["lan_nhan"] = submission_label(item)


def _index_of(items, item):
    for i, x in enumerate(items):
        if x is item:
            return i
    return 0


def days_block(all_items, page_days, result):
    """Gộp: mỗi ngày một dòng cho mỗi loại tiền — là TỔNG CỘNG của ngày đó (bố cục trước 19.09)."""
    kinds = with_currency(DAY_KINDS, result)
    tong = _by_currency(aggregations.subtotals(all_items, result, key=_subtotal_key("nhom", result)), result)
    rows = []
    for ngay in page_days:
        for tien, raw in tong.get(ngay, []):
            nhan = aggregations.format_group(ngay, result)
            rows.append({"kind": "row", "nhom": nhan, "ngay": ngay, "raw": raw,
                         "currency": currency_label(tien) if result.currency_key else None,
                         "cells": aggregations.format_cells(result, raw, tien),
                         "identity": [nhan] + ([currency_label(tien)] if "tien" in [k[0] for k in kinds] else [])})
    return block("days", "Theo ngày", kinds, rows, overall_totals("days", result), count=len(page_days))


def submissions_block(rows, page_items, result, title="Mọi lần nộp trong kỳ"):
    """Chế độ Từng lần nộp, Gộp: một khối mọi lần nộp trong kỳ — Ngày · Nhân sự · Lần nộp · Loại tiền,
    số đúng như nhập, TỔNG CỘNG toàn kỳ theo loại tiền (mockup 28.09, ADR-046)."""
    kinds = with_currency(SUBMISSION_KINDS + (LAN_KIND,), result)
    out = []
    for row, item in zip(rows, page_items):
        dong = person_row("", item, row["cells"], aggregations.row_values(item, result)[1], kinds, result)
        dong["nhom"] = row["nhom"]
        dong["ngay"] = item.get("nhom")   # ngày gốc: mốc `data-ngay` để đổi Gộp / Không gộp vẫn ở đúng ngày
        vi_tri = [code for code, _, _ in kinds].index("nhom")
        dong["identity"][vi_tri] = row["nhom"]
        _gan_lan_nop(dong, item)
        out.append(dong)
    return block("submissions", title, kinds, out, overall_totals("submissions", result), count=len(out))


def days_of(all_items):
    """Danh sách ngày theo thứ tự xuất hiện (mới nhất trước) — để phân trang khi Gộp."""
    out = []
    for item in all_items:
        if not out or out[-1] != item.get("nhom"):
            out.append(item.get("nhom"))
    return out


def single_block(kinds, rows, result, page_items=()):
    """Cách xem khác: một khối, cột định danh như ADR-035 (Team · nhóm · Leader), thêm Loại tiền."""
    kinds = with_currency(kinds, result)
    for row, item in zip(rows, page_items or [None] * len(rows)):
        if result.currency_key and item is not None:
            row["currency"] = row["tien"] = currency_label(item.get(result.currency_key))
        row["identity"] = [row["nhom"] if code == "nhom" else row.get(code, "—") for code, _, _ in kinds]
    return block("single", "", kinds, rows, overall_totals("single", result))


def flat_rows(blocks):
    """Dãy phẳng như trước đợt 2 (dòng `subtotal` rồi các dòng người) — cho bài kiểm và Tổng quan.
    Mỗi dòng TỔNG CỘNG của ngày (mỗi loại tiền một dòng) là một dòng `subtotal`."""
    out = []
    for b in blocks:
        if b["kind"] == "day":
            for tong in b["total_rows"]:
                out.append({"kind": "subtotal", "nhom": b["title"], "currency": tong["currency"], "cells": tong["cells"]})
            out.extend(b["rows"])
        elif b["kind"] != "period":
            out.extend(b["rows"])
    return out
