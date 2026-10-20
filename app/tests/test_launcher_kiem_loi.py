"""Launcher dừng khi cập nhật cấu trúc dữ liệu lỗi — TL-99 · P0-17.

Sự cố 06.09.2026: `migrate` trên máy Windows hỏng nhưng launcher vẫn ghi dấu vết
`storage/.kn-jsc-lan-truoc` bằng commit hiện tại; lần sau `KN JSC.bat` thấy "mã
không đổi", không migrate nữa, KN CRM báo lỗi cột chưa có mà không ai hiểu vì sao.
Bài học đã ghi ở backlog: tệp .bat phải kiểm errorlevel sau mỗi lệnh cấu trúc.

Kiểm tĩnh bằng đọc chữ (docs/08 mục 9: launcher kiểm tĩnh và kiểm tay, không có AC
riêng; VH-15, PLAT-07). Không cần Docker hay cơ sở dữ liệu. Lỗi cú pháp cmd thì bài
này không bắt được — phần đó là kiểm tay trên Windows.
"""
import re
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[2]

#: Hai launcher Windows ghi dấu vết sau khi cập nhật cấu trúc
LAUNCHER_WINDOWS = ["KN JSC.bat", "scripts/cap-nhat-local.bat"]
#: Hai tệp shell chạy cùng lệnh, dừng nhờ `set -e`
TEP_SHELL = ["scripts/cap-nhat-local.sh", "deploy/entrypoint.sh"]

LENH_CAU_TRUC = re.compile(r"manage\.py\s+(migrate|tao_bang_van_don)\b", re.I)
GHI_DAU_VET = re.compile(r">\s*\"?[^\"\s]*(kn-jsc-lan-truoc|%DAU_VET%)", re.I)
KIEM_LOI_GOTO = re.compile(r"^if\s+errorlevel\s+1\s+goto\s+:?(\S+)\s*$", re.I)
KIEM_LOI_KHOI = re.compile(r"^if\s+errorlevel\s+1\s*\($", re.I)
CUNG_DONG = re.compile(r"\|\|\s*(?:goto\s+:?(\S+)|exit\s+/b\s+([1-9]\d*))", re.I)
GOTO = re.compile(r"^goto\s+:?(\S+)", re.I)
THOAT = re.compile(r"^exit\s+/b\s*(\d*)", re.I)


def _tep(ten):
    """Đường dẫn tệp ở gốc kho. Trong container dev gốc là `/` và chỉ vài thư mục được gắn
    (deploy/docker-compose.yml): thiếu tệp ở đó thì bỏ qua; ở nơi khác (CI lấy cả kho) thiếu là đỏ,
    để đổi tên tệp không âm thầm thoát kiểm."""
    for duong in (GOC / ten, Path("/") / Path(ten).name):
        if duong.is_file():
            return duong
    if GOC == Path("/"):
        pytest.skip(f"Container không gắn {ten} — CI chạy bài này trên cả kho")
    pytest.fail(f"Không thấy {ten} ở gốc kho")


def _dong_lenh(noi_dung):
    """(số dòng gốc, lệnh) — bỏ dòng trống và chú thích `rem`, `::`; đọc được cả CRLF."""
    ket_qua = []
    for so, dong in enumerate(noi_dung.splitlines(), start=1):
        lenh = dong.strip()
        if not lenh or lenh.startswith("::") or re.match(r"^rem(\s|$)", lenh, re.I):
            continue
        ket_qua.append((so, lenh))
    return ket_qua


def _nhan(dong):
    return {lenh[1:].split()[0].lower(): i for i, (_, lenh) in enumerate(dong)
            if lenh.startswith(":") and not lenh.startswith("::") and len(lenh) > 1}


def _nhan_dan_toi_thoat_loi(dong, nhan, dich, ten, so_dong):
    """Đi từ nhãn `dich` theo luật cmd (nhãn không chặn luồng, `goto` thì nhảy) phải tới `exit /b` khác 0,
    không ghi dấu vết trên đường đi. Trả lỗi hoặc None."""
    i = nhan.get(dich.lower().lstrip(":"))
    if i is None:
        return f"{ten}:{so_dong} — nhãn :{dich} không có"
    for _ in range(200):
        i += 1
        if i >= len(dong):
            return f"{ten}:{so_dong} — nhãn :{dich} chạy hết tệp mà không exit /b khác 0"
        so, lenh = dong[i]
        if GHI_DAU_VET.search(lenh):
            return f"{ten}:{so_dong} — đường lỗi qua :{dich} vẫn ghi dấu vết ở dòng {so}"
        if m := GOTO.match(lenh):
            i = nhan.get(m.group(1).lower())
            if i is None:
                return f"{ten}:{so_dong} — nhãn :{m.group(1)} không có"
            continue
        if m := THOAT.match(lenh):
            return None if m.group(1) and int(m.group(1)) != 0 else (
                f"{ten}:{so_dong} — đường lỗi qua :{dich} thoát mã 0 ở dòng {so}")
    return f"{ten}:{so_dong} — đường lỗi qua :{dich} lặp vòng"


def _loi_cau_truc(noi_dung, ten="tep.bat"):
    """Danh sách lỗi 'tệp:dòng — …': lệnh migrate/tao_bang_van_don không kiểm errorlevel ngay sau, hoặc
    đường lỗi không thoát mã khác 0, hoặc dấu vết ghi trước lệnh cấu trúc cuối cùng."""
    dong = _dong_lenh(noi_dung)
    nhan = _nhan(dong)
    loi = []
    cuoi = 0
    for i, (so, lenh) in enumerate(dong):
        if not LENH_CAU_TRUC.search(lenh):
            continue
        cuoi = so
        if m := CUNG_DONG.search(lenh):
            if m.group(1) and (sai := _nhan_dan_toi_thoat_loi(dong, nhan, m.group(1), ten, so)):
                loi.append(sai)
            continue
        if i + 1 >= len(dong):
            loi.append(f"{ten}:{so} — {lenh} không kiểm errorlevel")
            continue
        sau = dong[i + 1][1]
        if m := KIEM_LOI_GOTO.match(sau):
            if sai := _nhan_dan_toi_thoat_loi(dong, nhan, m.group(1), ten, so):
                loi.append(sai)
        elif KIEM_LOI_KHOI.match(sau):
            ra = None
            for _, trong in dong[i + 2:]:
                if trong.startswith(")"):
                    break
                if GHI_DAU_VET.search(trong):
                    ra = "ghi"
                    break
                if m := GOTO.match(trong):
                    ra = _nhan_dan_toi_thoat_loi(dong, nhan, m.group(1), ten, so) or "ok"
                    break
                if (m := THOAT.match(trong)) and m.group(1) and int(m.group(1)) != 0:
                    ra = "ok"
                    break
            if ra != "ok":
                loi.append(ra if ra not in (None, "ghi") else f"{ten}:{so} — khối kiểm lỗi không dừng sau {lenh}")
        else:
            loi.append(f"{ten}:{so} — {lenh} không kiểm errorlevel (dòng sau: {sau})")
    for so, lenh in dong:
        if GHI_DAU_VET.search(lenh) and so < cuoi:
            loi.append(f"{ten}:{so} — ghi dấu vết trước lệnh cấu trúc cuối cùng (dòng {cuoi})")
    return loi


@pytest.mark.parametrize("ten", LAUNCHER_WINDOWS)
def test_launcher_windows_kiem_errorlevel_sau_migrate_va_tao_bang_van_don(ten):
    """TL-99 · P0-17 — migrate hay tao_bang_van_don hỏng thì launcher Windows dừng, thoát mã khác 0 và
    KHÔNG ghi dấu vết `storage/.kn-jsc-lan-truoc` — lần sau còn chạy lại bước đó (sự cố 06.09.2026)"""
    noi_dung = _tep(ten).read_text(encoding="utf-8", errors="replace")
    assert LENH_CAU_TRUC.search(noi_dung), f"{ten} không còn gọi migrate — bài cần xem lại"
    assert _loi_cau_truc(noi_dung, ten) == []


BAT_DUNG = """@echo off
rem manage.py migrate trong chú thích không tính
%COMPOSE% exec -T web python manage.py migrate --noinput
if errorlevel 1 goto :loi
%COMPOSE% exec -T web python manage.py tao_bang_van_don
if errorlevel 1 (
  echo hong
  goto :loi_cau_truc
)
>"storage\\.kn-jsc-lan-truoc" echo abc
exit /b 0

:loi_cau_truc
echo CAP NHAT CAU TRUC KHONG XONG
goto :loi

:loi
pause
exit /b 1
"""


def test_bo_kiem_tinh_nhan_dung_cach_viet_dung_va_sai():
    """TL-99 · P0-17 — Bộ đọc chữ của bài launcher: nhận các cách viết đúng, bắt từng cách viết sai đúng dòng
    (để bài launcher đỏ vì lỗi thật, không vì regex hỏng)"""
    assert _loi_cau_truc(BAT_DUNG) == []
    assert _loi_cau_truc(BAT_DUNG.replace("\n", "\r\n")) == []
    assert _loi_cau_truc("manage.py migrate || goto :loi\n:loi\nexit /b 1\n") == []

    thieu = BAT_DUNG.replace("if errorlevel 1 (\n  echo hong\n  goto :loi_cau_truc\n)\n", "")
    assert _loi_cau_truc(thieu) == ["tep.bat:5 — %COMPOSE% exec -T web python manage.py tao_bang_van_don "
                                    "không kiểm errorlevel (dòng sau: >\"storage\\.kn-jsc-lan-truoc\" echo abc)"]
    chen = BAT_DUNG.replace("--noinput\nif errorlevel", "--noinput\necho xong\nif errorlevel")
    assert [l.split(" — ")[0] for l in _loi_cau_truc(chen)] == ["tep.bat:3"]
    ghi_truoc = '>"storage\\.kn-jsc-lan-truoc" echo abc\n' + BAT_DUNG
    assert any("ghi dấu vết trước" in l for l in _loi_cau_truc(ghi_truoc))
    ghi_tren_duong_loi = BAT_DUNG.replace("echo CAP NHAT CAU TRUC KHONG XONG",
                                          '>"%DAU_VET%" echo abc')
    assert any("vẫn ghi dấu vết" in l for l in _loi_cau_truc(ghi_tren_duong_loi))
    thoat_0 = BAT_DUNG.replace("pause\nexit /b 1", "pause\nexit /b 0")
    assert any("thoát mã 0" in l for l in _loi_cau_truc(thoat_0))


@pytest.mark.parametrize("ten", TEP_SHELL)
def test_ban_sh_va_entrypoint_dung_ngay_khi_lenh_cau_truc_loi(ten):
    """TL-99 · P0-17 — Bản shell và entrypoint dừng ngay khi migrate hay tao_bang_van_don hỏng: có `set -e`
    trước lệnh đầu, không `|| …` nuốt lỗi — không thì web lên với lược đồ cũ"""
    dong = _tep(ten).read_text(encoding="utf-8").splitlines()
    cau_truc = [i for i, d in enumerate(dong) if LENH_CAU_TRUC.search(d) and not d.lstrip().startswith("#")]
    assert cau_truc, f"{ten} không còn gọi migrate — bài cần xem lại"
    set_e = [i for i, d in enumerate(dong) if re.match(r"^\s*set\s+-[a-z]*e", d)]
    assert set_e and set_e[0] < cau_truc[0], f"{ten} thiếu set -e trước migrate"
    assert not any(re.match(r"^\s*set\s+\+[a-z]*e", d) for d in dong[:cau_truc[-1]]), f"{ten} tắt set -e"
    for i in cau_truc:
        assert "||" not in dong[i] and "; true" not in dong[i], f"{ten}:{i + 1} nuốt lỗi: {dong[i]}"
    ghi = [i for i, d in enumerate(dong) if "kn-jsc-lan-truoc" in d and ">" in d]
    assert all(i > cau_truc[-1] for i in ghi), f"{ten} ghi dấu vết trước lệnh cấu trúc"


@pytest.mark.parametrize("ten", LAUNCHER_WINDOWS)
def test_launcher_windows_chi_dung_ky_tu_ascii(ten):
    """TL-99 · P0-17 — Lời báo trong launcher Windows là ASCII không dấu: cap-nhat-local.bat không đổi trang
    mã nên chữ có dấu hiện thành rác trên cmd"""
    assert _tep(ten).read_bytes().isascii()
