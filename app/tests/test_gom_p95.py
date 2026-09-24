"""Bộ gom p95 từ log VPS — `scripts/gom-p95-vps.py`.

Kiểm bằng dòng log **đúng dạng thật** mà `core/request_metrics.py` phát ra, nên
đổi khuôn log mà quên sửa bộ gom thì bài này đỏ. Không cần Docker, không cần
cơ sở dữ liệu: bộ gom chỉ đọc chữ.
"""
import importlib.util
import json
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def gom():
    spec = importlib.util.spec_from_file_location("gom_p95_vps", GOC / "scripts" / "gom-p95-vps.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def dong_log(route, ms, method="GET", status=200, db_ms=None, queries=3):
    """Một dòng y như container `crm` in ra: tiền tố Django rồi tới JSON."""
    ban_ghi = {"request_id": "abc123", "route": route, "method": method, "status": status,
               "ms": ms, "pid": 7, "db_ms": ms / 2 if db_ms is None else db_ms,
               "connect_ms": 0.0, "queries": queries, "db_pid": 42,
               "sqlstate": None, "connection": "keep-alive"}
    return f"2026-09-22 03:14:15,926 INFO knjsc.request {json.dumps(ban_ghi)}"


# ══ Phân vị ═══════════════════════════════════════════════════════

def test_p95_lay_gia_tri_da_that_su_xay_ra(gom):
    """Phân vị theo thứ hạng gần nhất, không nội suy — số trả về phải là một
    giá trị có thật trong dãy, để truy nguyên được về đúng một dòng log."""
    gia_tri = [float(x) for x in range(1, 101)]
    assert gom.percentile(gia_tri, 95) == 95.0
    assert gom.percentile(gia_tri, 50) == 50.0
    assert gom.percentile(gia_tri, 100) == 100.0


def test_p95_khong_no_voi_day_rong_hoac_mot_phan_tu(gom):
    """Khoảng thời gian không có yêu cầu nào là chuyện bình thường ban đêm."""
    assert gom.percentile([], 95) == 0.0
    assert gom.percentile([7.5], 95) == 7.5


# ══ Xếp nhóm ══════════════════════════════════════════════════════

def test_hoi_tham_tach_khoi_doc_du_cung_la_GET(gom):
    """`moi-nhat/` là GET nhưng ngưỡng 300 ms chứ không phải 1000 ms — xếp
    nhầm vào Đọc là che mất một nhóm đang vượt ngưỡng."""
    assert gom.classify({"route": "bang-tinh/<slug:code>/moi-nhat/", "method": "GET"}) == "hoi_tham"
    assert gom.classify({"route": "bang-tinh/<slug:code>/du-lieu/", "method": "GET"}) == "doc"


def test_moi_phuong_thuc_ghi_deu_vao_nhom_ghi(gom):
    """Xếp theo phương thức chứ không theo danh sách tuyến: thêm tuyến ghi mới
    thì không phải sửa script, và không tuyến nào rơi ra ngoài mọi nhóm."""
    for method in ("POST", "PUT", "PATCH", "DELETE"):
        assert gom.classify({"route": "bang-tinh/<slug:code>/gi-do/", "method": method}) == "ghi"


# ══ Đọc log ═══════════════════════════════════════════════════════

def test_chi_nhat_dong_so_do_bo_qua_dong_khac(gom):
    """Log thật lẫn dòng khởi động, cảnh báo, traceback. Chúng không phải lỗi
    của bộ gom nên không được đếm vào `dong_bo_qua`."""
    lines = [
        dong_log("thu-muc/", 120.0),
        "2026-09-22 03:14:16,000 INFO django.server khoi dong xong",
        'Traceback (most recent call last):',
        dong_log("bang-tinh/<slug:code>/du-lieu/", 340.0),
    ]
    entries, bo_qua = gom.parse(lines)
    assert [e["ms"] for e in entries] == [120.0, 340.0]
    assert bo_qua == 0


def test_dong_json_hong_duoc_dem_chu_khong_lam_hong_ca_luot(gom):
    """Log bị cắt giữa chừng khi xoay vòng là chuyện có thật."""
    entries, bo_qua = gom.parse([dong_log("thu-muc/", 10.0), "INFO knjsc.request {cut off...}"])
    assert len(entries) == 1 and bo_qua == 1


# ══ Phán quyết ════════════════════════════════════════════════════

def test_vuot_nguong_thi_bao_khong_dat_va_ma_thoat_bang_1(gom, tmp_path, capsys):
    """Ghi p95 vượt 500 ms phải ra KHÔNG ĐẠT, và mã thoát 1 để cron bắt được."""
    lines = [dong_log("bang-tinh/<slug:code>/luu-json/", 900.0, method="POST") for _ in range(30)]
    tep = tmp_path / "log.txt"
    tep.write_text("\n".join(lines), encoding="utf-8")

    ma_thoat = gom.main(["--tep", str(tep)])
    assert ma_thoat == 1
    assert "KHÔNG ĐẠT" in capsys.readouterr().out


def test_trong_nguong_thi_dat_va_ma_thoat_bang_0(gom, tmp_path):
    lines = [dong_log("bang-tinh/<slug:code>/luu-json/", 120.0, method="POST") for _ in range(30)]
    tep = tmp_path / "log.txt"
    tep.write_text("\n".join(lines), encoding="utf-8")
    assert gom.main(["--tep", str(tep)]) == 0


def test_it_mau_thi_noi_ro_chu_khong_phan_quyet_lang_le(gom, tmp_path, capsys):
    """p95 trên ba mẫu chỉ là số lớn nhất. Im lặng đưa ra ĐẠT ở đây là tự lừa —
    đúng thứ `docs/06` cấm: không tuyên bố đạt những kiểm tra chưa chạy."""
    tep = tmp_path / "log.txt"
    tep.write_text("\n".join(dong_log("thu-muc/", 50.0) for _ in range(3)), encoding="utf-8")

    assert gom.main(["--tep", str(tep)]) == 2
    ra = capsys.readouterr().out
    assert "thiếu mẫu" in ra and "chưa nói lên điều gì" in ra


def test_tuyen_cham_theo_ban_chat_khong_keo_phan_quyet_xuong(gom, tmp_path):
    """Nhập tệp 20 giây là đúng thiết kế. Tính nó vào nhóm Ghi thì nhóm nào
    cũng đỏ và con số mất hết ý nghĩa."""
    lines = [dong_log("bang-tinh/<slug:code>/luu-json/", 100.0, method="POST") for _ in range(30)]
    lines += [dong_log("bang/<slug:code>/nhap/", 20000.0, method="POST") for _ in range(5)]
    tep = tmp_path / "log.txt"
    tep.write_text("\n".join(lines), encoding="utf-8")

    assert gom.main(["--tep", str(tep)]) == 0


def test_khong_co_so_do_thi_chi_ra_ba_nguyen_nhan(gom, tmp_path, capsys):
    """Người vận hành gặp bảng rỗng cần biết đi tìm ở đâu, không phải đoán."""
    tep = tmp_path / "log.txt"
    tep.write_text("khong co gi o day\n", encoding="utf-8")
    gom.main(["--tep", str(tep)])
    ra = capsys.readouterr().out
    assert "CRM_REQUEST_METRICS" in ra and "--since" in ra


# ══ Biên bản JSON ═════════════════════════════════════════════════

def test_ghi_duoc_json_cho_bien_ban(gom, tmp_path):
    """Mỗi tác vụ có đo để lại biên bản (CLAUDE.md). Số phải máy đọc được."""
    tep = tmp_path / "log.txt"
    tep.write_text("\n".join(dong_log("thu-muc/", 200.0) for _ in range(25)), encoding="utf-8")
    ra = tmp_path / "bien-ban.json"

    gom.main(["--tep", str(tep), "--json", str(ra)])
    bao_cao = json.loads(ra.read_text(encoding="utf-8"))
    assert bao_cao["tong_yeu_cau"] == 25
    assert bao_cao["nhom"]["doc"]["p95"] == 200.0
    assert bao_cao["nhom"]["doc"]["ket_luan"] == "ĐẠT"
    assert bao_cao["tuyen"][0]["tuyen"] == "thu-muc/"


# ══ Ngưỡng không được trôi khỏi mã nguồn ══════════════════════════

def test_nguong_trong_script_khop_core_constants(gom):
    """Script chạy ngoài container nên phải chép ngưỡng. Chép thì sẽ trôi —
    bài này là chỗ chặn: đổi `core/constants.py` mà quên script thì đỏ."""
    from core import constants

    assert gom.READ_P95_MS == constants.PERF_READ_P95_MS
    assert gom.WRITE_P95_MS == constants.PERF_WRITE_P95_MS
    assert gom.POLL_P95_MS == constants.PERF_POLL_P95_MS
