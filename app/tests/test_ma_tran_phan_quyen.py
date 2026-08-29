"""Ma trận kiểm chéo phân quyền — `docs/04` mục 3.

Tài liệu có một bảng 7 đường dẫn × 5 vai trò, mỗi ô ghi rõ *Vào được* hay
*Từ chối*. Mục 12 điều 2 bắt kiểm đủ cả 35 ô, và ghi thêm:

> **Không bỏ qua** các tiêu chí thuộc mục 3 và mục 9 với lý do sẽ sửa sau.
> Lỗi phân quyền dẫn tới rò rỉ dữ liệu, và dữ liệu đã lộ thì không thu hồi được.

Trước tệp này chưa ô nào được kiểm, vì chúng không có mã tiêu chí riêng nên
không bài nào truy ngược tới được.

**Bảng dưới đây chép đúng bảng trong tài liệu.** Sửa bảng trong tài liệu thì
phải sửa cả đây — hai chỗ lệch nhau là một trong hai chỗ sai.
"""
from datetime import date

import pytest

from forms_builder.meaning import FieldType, Meaning
from forms_builder.models import ColumnDef, FieldDef, TableDef
from forms_builder.services import form_service
from orders.services import dispatch_service
from reports.services import daily_service

pytestmark = pytest.mark.django_db

VAO_DUOC = "vao_duoc"
TU_CHOI = "tu_choi"
CHUYEN_DANG_NHAP = "chuyen_dang_nhap"

#: Năm cột của bảng trong tài liệu. `None` là chưa đăng nhập.
CAC_VAI_TRO = [
    ("Staff Sale", "staff_sale_1"),
    ("Leader Sale", "leader_sale_1"),
    ("Manager Sale", "manager_sale"),
    ("Staff Vận đơn", "staff_vd"),
    ("Chưa đăng nhập", None),
]

#: Bảy dòng của bảng, chép đúng `docs/04` mục 3.
MA_TRAN = {
    "Báo cáo của chính mình": {
        "staff_sale_1": VAO_DUOC, "leader_sale_1": VAO_DUOC,
        "manager_sale": VAO_DUOC, "staff_vd": VAO_DUOC, None: CHUYEN_DANG_NHAP,
    },
    "Báo cáo người cùng team": {
        "staff_sale_1": TU_CHOI, "leader_sale_1": VAO_DUOC,
        "manager_sale": VAO_DUOC, "staff_vd": TU_CHOI, None: CHUYEN_DANG_NHAP,
    },
    "Báo cáo team khác cùng bộ phận": {
        "staff_sale_1": TU_CHOI, "leader_sale_1": TU_CHOI,
        "manager_sale": VAO_DUOC, "staff_vd": TU_CHOI, None: CHUYEN_DANG_NHAP,
    },
    "Báo cáo bộ phận khác": {
        "staff_sale_1": TU_CHOI, "leader_sale_1": TU_CHOI,
        "manager_sale": TU_CHOI, "staff_vd": TU_CHOI, None: CHUYEN_DANG_NHAP,
    },
    "Màn hình lên đơn": {
        "staff_sale_1": VAO_DUOC, "leader_sale_1": VAO_DUOC,
        "manager_sale": VAO_DUOC, "staff_vd": TU_CHOI, None: CHUYEN_DANG_NHAP,
    },
    "Bảng vận đơn": {
        "staff_sale_1": TU_CHOI, "leader_sale_1": TU_CHOI,
        "manager_sale": TU_CHOI, "staff_vd": VAO_DUOC, None: CHUYEN_DANG_NHAP,
    },
    "Quản lý biểu mẫu": {
        "staff_sale_1": TU_CHOI, "leader_sale_1": TU_CHOI,
        "manager_sale": VAO_DUOC, "staff_vd": TU_CHOI, None: CHUYEN_DANG_NHAP,
    },
}

CAC_O = [
    (dong, ten_vai_tro, ma_vai_tro, MA_TRAN[dong][ma_vai_tro])
    for dong in MA_TRAN
    for ten_vai_tro, ma_vai_tro in CAC_VAI_TRO
]


def _dung_bao_cao(bo_phan, nguoi):
    """Một biểu mẫu và một báo cáo đã nộp, cho một người."""
    bang = TableDef.objects.create(
        name=f"Bảng {nguoi.username}", code=f"bang_{nguoi.username}",
        department=bo_phan, created_by=nguoi,
    )
    ColumnDef.objects.create(
        table=bang, name="Ngày", code="ngay", field_type=FieldType.DATE,
        meaning=Meaning.DATE, order=0,
    )
    bm = form_service.create_form(
        name=f"Báo cáo {nguoi.username}", code=f"bc_{nguoi.username}",
        department=bo_phan, table=bang, actor=nguoi,
    )
    truong = FieldDef.objects.create(
        name="Ngày", code=f"ngay_{nguoi.username}", field_type=FieldType.DATE,
        meaning=Meaning.DATE, department=bo_phan,
    )
    form_service.add_field(bm, truong, column=bang.columns.get(code="ngay"), actor=nguoi)
    return daily_service.submit(
        bm, {f"ngay_{nguoi.username}": "2026-08-28"},
        report_date=date(2026, 8, 28), actor=nguoi,
    )


@pytest.fixture
def duong_dan(departments, teams, nguoi_dung):
    """Dựng dữ liệu rồi trả về đường dẫn thật cho từng dòng của bảng.

    Bốn dòng đầu cần báo cáo của bốn người khác nhau, nên phải dựng thật —
    không đoán khoá chính được.
    """
    dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])

    cua_minh = {}
    for ma in ("staff_sale_1", "leader_sale_1", "manager_sale", "staff_vd"):
        nguoi = nguoi_dung[ma]
        bp = departments["vd"] if ma == "staff_vd" else departments["sale"]
        cua_minh[ma] = _dung_bao_cao(bp, nguoi).pk

    cung_team = _dung_bao_cao(departments["sale"], nguoi_dung["staff_sale_1b"]).pk
    team_khac = _dung_bao_cao(departments["sale"], nguoi_dung["staff_sale_2"]).pk
    bo_phan_khac = _dung_bao_cao(departments["mkt"], nguoi_dung["staff_mkt"]).pk

    return {
        "Báo cáo của chính mình": cua_minh,          # đường dẫn khác nhau theo người
        "Báo cáo người cùng team": f"/bao-cao/{cung_team}/",
        "Báo cáo team khác cùng bộ phận": f"/bao-cao/{team_khac}/",
        "Báo cáo bộ phận khác": f"/bao-cao/{bo_phan_khac}/",
        "Màn hình lên đơn": "/len-don/",
        "Bảng vận đơn": "/bang/van_don/",
        "Quản lý biểu mẫu": "/bieu-mau/",
    }


def _ket_qua(ma_http, vi_tri):
    """Đổi mã HTTP sang chữ trong bảng của tài liệu."""
    if ma_http == 200:
        return VAO_DUOC
    if ma_http in (403, 404):
        return TU_CHOI
    if ma_http == 302 and "/dang-nhap/" in vi_tri:
        return CHUYEN_DANG_NHAP
    return f"khác ({ma_http})"


@pytest.mark.parametrize(
    "dong,ten_vai_tro,ma_vai_tro,mong_doi", CAC_O,
    ids=[f"{d} · {t}" for d, t, _, _ in CAC_O],
)
def test_ma_tran_kiem_cheo(client, nguoi_dung, duong_dan,
                           dong, ten_vai_tro, ma_vai_tro, mong_doi):
    """AC-3.1 tới AC-3.8 — Một ô trong ma trận kiểm chéo, `docs/04` mục 3

    Mục 12 điều 2 đòi kiểm đủ 35 ô, cả chiều cho phép lẫn chiều từ chối.
    """
    if ma_vai_tro is not None:
        client.force_login(nguoi_dung[ma_vai_tro])

    dd = duong_dan[dong]
    if isinstance(dd, dict):                 # dòng "của chính mình"
        if ma_vai_tro is None:
            dd = f"/bao-cao/{dd['staff_sale_1']}/"
        else:
            dd = f"/bao-cao/{dd[ma_vai_tro]}/"

    kq = client.get(dd)
    thuc_te = _ket_qua(kq.status_code, kq.get("Location", ""))

    assert thuc_te == mong_doi, (
        f"Ô [{dong} × {ten_vai_tro}]: tài liệu ghi {mong_doi}, "
        f"thực tế {thuc_te} khi gọi {dd}"
    )


def test_ma_tran_du_ba_muoi_lam_o():
    """Mục 12 điều 2 — Bảng phải đủ 7 đường dẫn × 5 vai trò"""
    assert len(CAC_O) == 35, f"Ma trận có {len(CAC_O)} ô, tài liệu ghi 35"
