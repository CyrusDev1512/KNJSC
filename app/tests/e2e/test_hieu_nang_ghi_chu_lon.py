"""Ghi chú tự giãn dòng ở quy mô lớn: trần khung vẽ và hiệu năng hình học — `docs/04` AC-11.44.

Dòng cao lên thì **tổng chiều cao khung vẽ** cao lên theo. Trình duyệt có trần cho chiều cao
một phần tử; vượt trần là nó cắt cụt, dòng nằm dưới điểm cắt không cuộn tới được — vỡ view mà
không báo lỗi gì. Trước AC-11.44 mọi dòng đều 28 px nên chuyện này không thể xảy ra; sau
AC-11.44 thì có thể. Bộ bài này đo đúng chỗ đó.

Mốc dự án (`core/constants.py`): khoảng 100.000 đơn một năm, kiểm dự phòng **300.000 dòng**,
tối đa 10 người cùng lúc; p95 đọc 1 s, ghi 0,5 s, hỏi mốc 0,3 s.

Ba bài, hai bài đầu chạy luôn vì chỉ tính toán trong trình duyệt, không cần dữ liệu:

    1. Trần chiều cao khung vẽ  — đo trần thật của trình duyệt rồi đối chiếu với các mốc
    2. Hiệu năng hình học hàng — 300.000 dòng, 150.000 dòng cao: đặt, tra, dựng lại mất bao lâu
    3. 300.000 dòng thật        — cần `KN_GHI_CHU_300K=1` và cơ sở dữ liệu kiểm riêng

Bài 3 dựng 300.000 dòng bằng SQL nhân bản (như `crm/tests/test_master_capacity.py`) nên nặng;
nó **tự bỏ qua** khi thiếu biến môi trường. Bỏ qua không phải là đã kiểm.
"""
import os
import time

import pytest
from django.db import connection

from crm.tests.test_waybill_feedback import feedback  # noqa: F401  (fixture dùng lại)
from forms_builder.models import DataRecord

from .conftest import chup

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.trinh_duyet, pytest.mark.cham]

ROW = 28
#: Mốc dự án: đơn một năm, và mức kiểm dự phòng
DON_MOT_NAM = 100_000
DU_PHONG = 300_000
#: Ghi chú 427 ký tự ở cột 400 px đo được 160 px (biên bản 23.09)
CAO_GHI_CHU_DAI = 160
#: Hỏi mốc mỗi 8 giây; tải lại mềm phải xong trong một nhịp, lấy 1 giây làm ngưỡng đỏ
NGUONG_DUNG_LAI_MS = 1000
#: Tra vị trí dòng chạy mỗi khung hình khi cuộn — phải dưới một phần nhỏ của 16,7 ms
NGUONG_TRA_MOT_LAN_MS = 0.5


@pytest.fixture
def kn_crm(settings):
    settings.ROOT_URLCONF = "knjsc.urls_bangtinh"
    settings.BANGTINH_URL = ""
    return settings


def _mo_luoi(trang, live_server, dang_nhap, nguoi_dung, bang):
    loi_js = []
    trang.on("pageerror", lambda e: loi_js.append(str(e)))
    dang_nhap(trang, nguoi_dung["admin"])
    trang.goto(f"{live_server.url}/bang-tinh/{bang.code}/")
    trang.wait_for_selector(".mg-cell[data-id]", timeout=30_000)
    trang.evaluate("() => document.fonts.ready")
    trang.wait_for_timeout(500)
    return loi_js


# ══ 1. Trần chiều cao khung vẽ ══════════════════════════════════════

def test_tran_chieu_cao_khung_ve(live_server, trang, dang_nhap, kn_crm,
                                 feedback, nguoi_dung):  # noqa: F811
    """AC-11.44 — Đo trần chiều cao một phần tử của trình duyệt rồi đối chiếu với các mốc của
    dự án: ở 100.000 đơn một năm, kể cả khi **mọi** dòng đều có ghi chú dài, khung vẽ vẫn nằm
    trong trần; ở 300.000 dòng thì chiều cao trung bình tối đa là bao nhiêu"""
    loi_js = _mo_luoi(trang, live_server, dang_nhap, nguoi_dung, feedback[0])

    # Dò nhị phân trần thật: đặt chiều cao rồi đọc lại, trình duyệt cắt ở đâu thì biết ở đó
    tran = trang.evaluate(
        """() => {
            const d = document.createElement('div');
            d.style.cssText = 'position:absolute;left:-99999px;top:0;width:1px';
            document.body.append(d);
            let duoc = 1000, khong = 100000000;       // 1 nghìn chắc được, 100 triệu chắc không
            while (khong - duoc > 1024) {
                const giua = Math.floor((duoc + khong) / 2);
                d.style.height = giua + 'px';
                (d.offsetHeight === giua ? (duoc = giua) : (khong = giua));
            }
            d.remove();
            return duoc;
        }"""
    )
    moc = {
        "300k dòng × 28 px (như trước AC-11.44)": DU_PHONG * ROW,
        f"100k dòng × {CAO_GHI_CHU_DAI} px (một năm, mọi dòng ghi chú dài)": DON_MOT_NAM * CAO_GHI_CHU_DAI,
        f"300k dòng × {CAO_GHI_CHU_DAI} px (dự phòng, mọi dòng ghi chú dài)": DU_PHONG * CAO_GHI_CHU_DAI,
        "300k dòng × 2000 px (mọi dòng chạm trần)": DU_PHONG * 2000,
    }
    print(f"\nAC-11.44 trần chiều cao trình duyệt: {tran:,} px")
    for ten, can in moc.items():
        print(f"    {'vừa ' if can <= tran else 'VƯỢT'} {ten}: cần {can:,} px"
              f" ({can / tran:.1%} trần)")
    cao_tb_toi_da = tran // DU_PHONG
    so_dong_toi_da = tran // CAO_GHI_CHU_DAI
    print(f"    → ở {DU_PHONG:,} dòng, chiều cao trung bình tối đa: {cao_tb_toi_da} px")
    print(f"    → nếu mọi dòng cao {CAO_GHI_CHU_DAI} px, tối đa {so_dong_toi_da:,} dòng")

    assert tran > 10_000_000, f"trần đo được quá thấp, số đo không đáng tin: {tran}"
    assert DU_PHONG * ROW < tran, "ngay cả bảng toàn dòng 28 px cũng vượt trần — sai số đo"
    assert DON_MOT_NAM * CAO_GHI_CHU_DAI < tran, (
        f"ở mức thật {DON_MOT_NAM:,} đơn một năm, nếu mọi dòng đều có ghi chú dài thì khung vẽ "
        f"cần {DON_MOT_NAM * CAO_GHI_CHU_DAI:,} px, vượt trần {tran:,} px — lưới sẽ cắt cụt")
    assert cao_tb_toi_da > ROW, "chiều cao trung bình tối đa còn thấp hơn dòng mặc định"
    assert not loi_js, loi_js


# ══ 2. Hiệu năng hình học hàng ══════════════════════════════════════

def test_hieu_nang_hinh_hoc_300k_dong(live_server, trang, dang_nhap, kn_crm,
                                      feedback, nguoi_dung):  # noqa: F811
    """AC-11.44 — Cây hình học hàng với 300.000 dòng, một nửa cao 160 px: đặt chiều cao, tra vị
    trí khi cuộn, và **dựng lại cây** (việc mà mỗi lượt tải lại mềm đều làm) tốn bao lâu.

    Dựng lại cây là chỗ đáng ngờ nhất: trước AC-11.44 lượt tải lại mềm xoá sạch cây, giờ nó
    giữ lại và dựng lại từng chiều cao — hỏi mốc chạy mỗi 8 giây nên việc này phải dưới 1 giây,
    nếu không lưới đứng hình mỗi lần có người khác sửa."""
    loi_js = _mo_luoi(trang, live_server, dang_nhap, nguoi_dung, feedback[0])

    do = trang.evaluate(
        """([tong, cao]) => {
            const G = window.KNJSCRowGeometry;
            if (!G) return {loi: 'trang không nạp KNJSCRowGeometry'};
            const g = new G(tong);
            const t0 = performance.now();
            for (let i = 0; i < tong; i += 2) g.set(i, cao);      // một nửa số dòng cao lên
            const dat = performance.now() - t0;

            const t1 = performance.now();
            const tong_cao = g.top(tong);
            const doc_tong = performance.now() - t1;

            const t2 = performance.now();
            for (let i = 0; i < 2000; i++) g.at(Math.random() * tong_cao);
            const tra = (performance.now() - t2) / 2000;

            const t3 = performance.now();
            g.resize(tong + 1);                                   // đúng việc tải lại mềm làm
            const dung_lai = performance.now() - t3;

            return {dat: Math.round(dat), doc_tong: Math.round(doc_tong * 100) / 100,
                    tra: Math.round(tra * 1000) / 1000, dung_lai: Math.round(dung_lai),
                    tong_cao, so_cao: g.heights.size, so_nut: g.tree.size};
        }""", [DU_PHONG, CAO_GHI_CHU_DAI])
    assert "loi" not in do, do

    mong_doi = (DU_PHONG // 2) * CAO_GHI_CHU_DAI + (DU_PHONG - DU_PHONG // 2) * ROW
    print(f"\nAC-11.44 hình học {DU_PHONG:,} dòng, {do['so_cao']:,} dòng cao {CAO_GHI_CHU_DAI} px:")
    print(f"    đặt {do['so_cao']:,} chiều cao : {do['dat']:,} ms")
    print(f"    đọc tổng chiều cao      : {do['doc_tong']} ms → {do['tong_cao']:,} px")
    print(f"    tra vị trí một lần      : {do['tra']} ms  (chạy mỗi khung hình khi cuộn)")
    print(f"    DỰNG LẠI CẢ CÂY         : {do['dung_lai']:,} ms  (mỗi lượt tải lại mềm)")
    print(f"    số nút cây Fenwick      : {do['so_nut']:,}")

    assert do["tong_cao"] == mong_doi, f"tổng chiều cao sai: {do['tong_cao']:,} ≠ {mong_doi:,}"
    assert do["tra"] < NGUONG_TRA_MOT_LAN_MS, (
        f"tra vị trí dòng mất {do['tra']} ms mỗi lần — cuộn sẽ giật ở {DU_PHONG:,} dòng")
    assert do["dung_lai"] < NGUONG_DUNG_LAI_MS, (
        f"dựng lại cây hình học mất {do['dung_lai']:,} ms; hỏi mốc chạy mỗi 8 giây nên lưới sẽ "
        f"đứng hình mỗi lần người khác sửa dữ liệu")
    assert not loi_js, loi_js


# ══ 3. 300.000 dòng thật ════════════════════════════════════════════

@pytest.mark.skipif(os.environ.get("KN_GHI_CHU_300K") != "1",
                    reason="Kiểm tải riêng 300.000 dòng — đặt KN_GHI_CHU_300K=1 để chạy")
def test_300k_dong_ghi_chu_dai_khong_vo_view(live_server, trang, dang_nhap, kn_crm,
                                             feedback, nguoi_dung):  # noqa: F811
    """AC-11.44 — 300.000 dòng mà dòng nào cũng có ghi chú dài: khung vẽ có bị trình duyệt cắt
    cụt không, cuộn tới cuối bảng có tới được dòng cuối không, đo chiều cao mỗi khối mất bao lâu"""
    bang, _, nguon = feedback
    truong = [f for f in DataRecord._meta.concrete_fields if f.name != "id"]
    cot_sql = ", ".join('"' + f.column + '"' for f in truong)
    chon = []
    for f in truong:
        if f.name == "data":
            chon.append("s.data || jsonb_build_object('ma_don','LON-'||g, 'ten_khach','Khách '||g,"
                        " 'ghi_chu', repeat('Ghi chú dài để dòng giãn hết cỡ. ', 12))")
        elif f.name in ("created_at", "updated_at"):
            chon.append("s.created_at - g * interval '1 second'")
        elif f.name == "val_customer":
            chon.append("'Khách '||g")
        else:
            chon.append('s."' + f.column + '"')
    bat_dau = time.time()
    with connection.cursor() as con:
        con.execute(
            f"INSERT INTO forms_builder_datarecord ({cot_sql}) SELECT " + ", ".join(chon) +
            " FROM forms_builder_datarecord s CROSS JOIN generate_series(%s,%s) g WHERE s.id=%s",
            [1, DU_PHONG - 1, nguon[0].pk])
        con.execute("ANALYZE forms_builder_datarecord")
    print(f"\nAC-11.44 nạp {DU_PHONG:,} dòng trong {time.time() - bat_dau:.0f} giây")

    mo = time.time()
    loi_js = _mo_luoi(trang, live_server, dang_nhap, nguoi_dung, bang)
    print(f"    mở lưới lần đầu: {int((time.time() - mo) * 1000):,} ms")

    khung = trang.evaluate(
        """() => {
            const c = document.getElementById('mg-canvas');
            const dat = parseInt(c.style.height, 10);
            return {dat, that: c.offsetHeight, tong: window.KNJSC_MASTER.diagnostics().total};
        }"""
    )
    print(f"    khung vẽ: đặt {khung['dat']:,} px, trình duyệt nhận {khung['that']:,} px,"
          f" tổng {khung['tong']:,} dòng")
    assert khung["tong"] >= DU_PHONG, khung
    assert khung["that"] >= khung["dat"] - 1, (
        f"trình duyệt CẮT CỤT khung vẽ: đặt {khung['dat']:,} px nhưng chỉ nhận {khung['that']:,} px "
        f"— các dòng nằm dưới điểm cắt không cuộn tới được")

    # Cuộn xuống tận đáy rồi kiểm dòng cuối có thật sự vẽ ra không
    trang.click("#mg-viewport")
    trang.keyboard.press("Control+End")
    trang.wait_for_timeout(2500)
    cuoi = trang.evaluate(
        """t => { const o = document.querySelector(`.mg-cell[data-r='${t - 1}'][data-id]`);
                  const vp = document.getElementById('mg-viewport');
                  return {co: !!o, chu: o ? o.textContent.trim().slice(0, 20) : null,
                          day: vp.scrollTop + vp.clientHeight >= vp.scrollHeight - 2}; }""",
        khung["tong"])
    print(f"    sau Ctrl+End: chạm đáy {cuoi['day']}, dòng cuối vẽ ra {cuoi['co']} ({cuoi['chu']})")
    chup(trang, "hieu-nang-ghi-chu-300k-cuoi-bang")
    assert cuoi["co"], f"cuộn tới cuối mà dòng cuối cùng không vẽ ra — vỡ view: {cuoi}"

    lo = trang.evaluate(
        "() => performance.getEntriesByName('mg-auto-height').map(e => Math.round(e.duration))")
    if lo:
        lo_sx = sorted(lo)
        print(f"    đo chiều cao mỗi khối 100 dòng: {len(lo)} lượt, "
              f"p50 {lo_sx[len(lo_sx) // 2]} ms, max {max(lo)} ms")
        assert max(lo) < 200, f"một lượt đo chiều cao mất {max(lo)} ms — quá lâu cho một khối"
    assert not loi_js, loi_js
