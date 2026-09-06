#!/usr/bin/env python3
"""Sinh khối CSS 40 màu của Bảng tính từ `record_service.PALETTE` (ADR-011).

Chạy lại mỗi khi đổi bảng màu:

    python3 scripts/sinh-css-mau.py

Ghi đè phần giữa hai dòng đánh dấu trong `app/static/css/bang-tinh.css`:
ô mẫu trên bảng màu (`bt-mau-m01`), màu chữ (`dd-chu-m01`) và màu nền
(`dd-nen-m01`, viết đủ độ ưu tiên để thắng màu dòng và ô cố định). Không gõ
tay 120 dòng, và bài quét lớp CSS (`test_giao_dien`) vẫn thấy đủ lớp.
"""
import re
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "app"))

DAU = "/* ══ SINH TỰ ĐỘNG: bảng 40 màu — scripts/sinh-css-mau.py đọc record_service.PALETTE, đừng sửa tay ══ */"
CUOI = "/* ══ HẾT SINH ══ */"
TEP = GOC / "app" / "static" / "css" / "bang-tinh.css"


def _palette():
    """Đọc PALETTE mà không nạp Django: chỉ cần tuple hằng trong tệp."""
    nguon = (GOC / "app" / "forms_builder" / "services" / "record_service.py").read_text(encoding="utf-8")
    return re.findall(r'\("(m\d\d)", "(#[0-9a-f]{6})"\)', nguon)


def sinh():
    dong = []
    for ma, hex_ in _palette():
        dong.append(f".bt-mau-{ma} {{ background: {hex_}; }}")
    for ma, hex_ in _palette():
        dong.append(f".luoi-vd td.dd-chu-{ma} {{ color: {hex_}; }}")
    for ma, hex_ in _palette():
        dong.append(
            f".luoi-vd td.dd-nen-{ma}, .luoi-vd tr.dong-xau td.dd-nen-{ma}, "
            f".luoi-vd td.co-dinh.dd-nen-{ma} {{ background: {hex_}; }}"
        )
    return "\n".join(dong)


def main():
    noi_dung = TEP.read_text(encoding="utf-8")
    if DAU not in noi_dung or CUOI not in noi_dung:
        sys.exit("Không thấy hai dòng đánh dấu trong bang-tinh.css")
    truoc, _, phan_sau = noi_dung.partition(DAU)
    _, _, sau = phan_sau.partition(CUOI)
    moi = f"{truoc}{DAU}\n{sinh()}\n{CUOI}{sau}"
    if moi != noi_dung:
        TEP.write_text(moi, encoding="utf-8")
    print(f"Đã sinh {len(_palette())} màu × 3 lớp vào {TEP.relative_to(GOC)}")


if __name__ == "__main__":
    main()
