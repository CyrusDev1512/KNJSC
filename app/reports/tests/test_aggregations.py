"""Kiểm thử tầng phép tính của báo cáo tổng hợp — `reports/aggregations.py`.

Kiểm ở mức dữ liệu, chưa qua HTTP: cộng đúng cột JSON lẫn cột tách, tính lại
cột tính sẵn trên tổng, ba cách nhóm, và bộ lọc. Phần phạm vi quyền qua màn
hình nằm ở `test_summary_scope.py`.

Mọi phép so tiền dùng `Decimal`, tuyệt đối không float (BR-8).
"""
from datetime import date
from decimal import Decimal

import pytest

from forms_builder.meaning import FieldType, Meaning
from forms_builder.models import ColumnDef, ComputeOp, DataRecord, TableDef
from forms_builder.services import record_service
from reports import aggregations

pytestmark = pytest.mark.django_db


@pytest.fixture
def bang_mkt(departments, nguoi_dung):
    """Bảng giống hệt Báo cáo Marketing của dữ liệu mẫu: bốn cột mang nhãn,
    ba cột số không nhãn nằm trong JSON, ba cột tính sẵn."""
    bang = TableDef.objects.create(
        name="Báo cáo Marketing", code="bc_mkt_test",
        department=departments["mkt"], created_by=nguoi_dung["manager_mkt"],
    )
    cot = [
        ("Ngày", "ngay", FieldType.DATE, Meaning.DATE),
        ("Marketer", "marketer", FieldType.TEXT, Meaning.SELLER),
        ("Sản phẩm", "san_pham", FieldType.TEXT, Meaning.PRODUCT),
        ("Số Mess", "so_mess", FieldType.INTEGER, ""),
        ("CPQC", "cpqc", FieldType.MONEY, ""),
        ("Số đơn", "so_don", FieldType.INTEGER, ""),
        ("Doanh số", "doanh_so", FieldType.MONEY, Meaning.REVENUE),
    ]
    for i, (ten, ma, kieu, nhan) in enumerate(cot):
        ColumnDef.objects.create(
            table=bang, name=ten, code=ma, field_type=kieu, meaning=nhan, order=i,
        )
    ColumnDef.objects.create(
        table=bang, name="CPO", code="cpo", field_type=FieldType.MONEY, order=7,
        is_computed=True, compute_op=ComputeOp.DIVIDE,
        compute_left="cpqc", compute_right="so_don", compute_decimals=0,
    )
    ColumnDef.objects.create(
        table=bang, name="Tỉ lệ chốt", code="ti_le_chot", field_type=FieldType.DECIMAL,
        order=8, is_computed=True, compute_op=ComputeOp.PERCENT,
        compute_left="so_don", compute_right="so_mess", compute_decimals=2,
    )
    # Phép nhân — để chứng minh nó KHÔNG được tính lại trên tổng
    ColumnDef.objects.create(
        table=bang, name="Tích thử", code="tich_thu", field_type=FieldType.DECIMAL,
        order=9, is_computed=True, compute_op=ComputeOp.MULTIPLY,
        compute_left="so_don", compute_right="so_mess", compute_decimals=0,
    )
    return bang


#: (ngày, marketer, sản phẩm, so_mess, cpqc, so_don, doanh_so)
DONG = [
    ("2026-08-01", "Minh", "Máy massage", "100", "200000", "10", "1500000"),
    ("2026-08-01", "Hà", "Đèn ngủ", "50", "80000", "4", "400000"),
    ("2026-08-02", "Minh", "Máy massage", "80", "150000", "8", "1200000"),
    ("2026-08-03", "Hà", "Đèn ngủ", "40", "70000", "2", "180000"),
]


@pytest.fixture
def dong_mau(bang_mkt, nguoi_dung):
    """Bốn dòng số nhỏ, đối chiếu tay được."""
    ket_qua = []
    for ngay, nguoi, sp, mess, cpqc, don, ds in DONG:
        ket_qua.append(record_service.create_record(
            bang_mkt,
            {"ngay": ngay, "marketer": nguoi, "san_pham": sp,
             "so_mess": mess, "cpqc": cpqc, "so_don": don, "doanh_so": ds},
            actor=nguoi_dung["staff_mkt"],
        ))
    return ket_qua


def _tong_hop(bang, user, **tham_so):
    return aggregations.summarize(
        bang, DataRecord.objects.in_scope(user), **tham_so)


def test_cong_dung_cot_json_va_cot_tach(bang_mkt, dong_mau, nguoi_dung):
    """FR-5.4 — Cộng đúng cả cột tách (Doanh thu) lẫn cột JSON

    Cột INTEGER nằm trong JSON dạng số thật, cột MONEY dạng chuỗi — cả hai
    phải cộng ra đúng một kết quả Decimal.
    """
    kq = _tong_hop(bang_mkt, nguoi_dung["manager_mkt"], group_key="ngay")
    assert kq.ok
    assert kq.totals["so_dong"] == 4
    assert kq.totals["c_so_mess"] == Decimal("270")
    assert kq.totals["c_cpqc"] == Decimal("500000")
    assert kq.totals["c_so_don"] == Decimal("24")
    assert kq.totals["c_doanh_so"] == Decimal("3280000")


def test_cot_tinh_san_tinh_lai_tren_tong(bang_mkt, dong_mau, nguoi_dung):
    """BR-8 — Cột tính sẵn tính lại từ tổng toán hạng, không cộng tổng

    CPO tổng = tổng CPQC ÷ tổng số đơn (trung bình có trọng số), không phải
    tổng các CPO từng dòng.
    """
    kq = _tong_hop(bang_mkt, nguoi_dung["manager_mkt"], group_key="ngay")
    assert kq.totals["cpo"] == (Decimal("500000") / Decimal("24")).quantize(Decimal("1"))
    assert kq.totals["ti_le_chot"] == (
        Decimal("24") / Decimal("270") * 100).quantize(Decimal("0.01"))


def test_phep_nhan_khong_tinh_lai(bang_mkt, dong_mau, nguoi_dung):
    """ADR-006 — Cột tính phép nhân không hiện trên báo cáo tổng hợp

    Tổng các tích không bằng tích các tổng, nên tính lại là ra số sai.
    """
    kq = _tong_hop(bang_mkt, nguoi_dung["manager_mkt"], group_key="ngay")
    assert "tich_thu" not in kq.totals
    assert all(c.code != "tich_thu" for c in kq.columns)


def test_nhom_theo_ngay(bang_mkt, dong_mau, nguoi_dung):
    """FR-5.1 — Nhóm theo ngày: mỗi ngày một dòng, cộng đúng trong ngày"""
    kq = _tong_hop(bang_mkt, nguoi_dung["manager_mkt"], group_key="ngay")
    dong = list(kq.rows)
    assert [d["nhom"] for d in dong] == [
        date(2026, 8, 3), date(2026, 8, 2), date(2026, 8, 1)]
    ngay_1 = dong[2]
    assert ngay_1["so_dong"] == 2
    assert ngay_1["c_doanh_so"] == Decimal("1900000")
    assert ngay_1["c_so_mess"] == Decimal("150")


def test_nhom_theo_nhan_vien(bang_mkt, dong_mau, nguoi_dung):
    """FR-5.1 — Nhóm theo người bán, xếp theo doanh thu giảm dần"""
    kq = _tong_hop(bang_mkt, nguoi_dung["manager_mkt"], group_key="nhan-vien")
    dong = list(kq.rows)
    assert [d["nhom"] for d in dong] == ["Minh", "Hà"]
    assert dong[0]["c_doanh_so"] == Decimal("2700000")
    assert dong[1]["c_doanh_so"] == Decimal("580000")


def test_nhom_theo_san_pham_co_ti_trong(bang_mkt, dong_mau, nguoi_dung):
    """FR-5.1 — Nhóm theo sản phẩm có thêm cột Tỉ trọng, cộng thành 100%"""
    kq = _tong_hop(bang_mkt, nguoi_dung["manager_mkt"], group_key="san-pham")
    assert kq.columns[-1].kind == "share"
    dong = aggregations.finish_rows(list(kq.rows), kq)
    ti_trong = [d["cells"][-1] for d in dong]
    assert ti_trong == ["82,3%", "17,7%"]
    assert aggregations.total_cells(kq)[-1] == "100%"


def test_bang_thieu_cot_nhom_khong_no(bang_mkt, departments, nguoi_dung):
    """NFR-6 — Bảng không có cột mang nhãn thì báo về, không nổ lỗi"""
    bang_trong = TableDef.objects.create(
        name="Bảng trống", code="bang_trong",
        department=departments["mkt"], created_by=nguoi_dung["manager_mkt"],
    )
    kq = _tong_hop(bang_trong, nguoi_dung["manager_mkt"], group_key="nhan-vien")
    assert kq.ok is False


def test_loc_theo_khoang_ngay(bang_mkt, dong_mau, nguoi_dung):
    """FR-5.2 — Lọc từ ngày đến ngày trên cột tách có chỉ mục"""
    kq = _tong_hop(
        bang_mkt, nguoi_dung["manager_mkt"], group_key="ngay",
        date_from=date(2026, 8, 2), date_to=date(2026, 8, 3),
    )
    assert kq.totals["so_dong"] == 2
    assert kq.totals["c_doanh_so"] == Decimal("1380000")


def test_loc_theo_san_pham(bang_mkt, dong_mau, nguoi_dung):
    """FR-5.3 — Lọc theo sản phẩm trả về đúng phần của sản phẩm đó"""
    kq = _tong_hop(
        bang_mkt, nguoi_dung["manager_mkt"], group_key="ngay", product="Đèn ngủ",
    )
    assert kq.totals["so_dong"] == 2
    assert kq.totals["c_doanh_so"] == Decimal("580000")


def test_dong_xoa_mem_khong_vao_tong(bang_mkt, dong_mau, nguoi_dung):
    """BR-4 — Dòng đã đánh dấu xoá không được tính vào tổng

    ADR-008 cảnh báo dòng mồ côi: quên lọc xoá mềm là báo cáo phình số.
    """
    dong_mau[0].delete(by=nguoi_dung["manager_mkt"])
    kq = _tong_hop(bang_mkt, nguoi_dung["manager_mkt"], group_key="ngay")
    assert kq.totals["so_dong"] == 3
    assert kq.totals["c_doanh_so"] == Decimal("1780000")


def test_tong_cong_bang_tong_cac_dong_nhom(bang_mkt, dong_mau, nguoi_dung):
    """FR-5.4 — Dòng tổng cộng khớp tổng các dòng nhóm, so bằng Decimal"""
    kq = _tong_hop(bang_mkt, nguoi_dung["manager_mkt"], group_key="nhan-vien")
    dong = list(kq.rows)
    for khoa in ("c_doanh_so", "c_so_mess", "c_cpqc", "c_so_don"):
        assert kq.totals[khoa] == sum((d[khoa] for d in dong), Decimal("0"))
    assert kq.totals["so_dong"] == sum(d["so_dong"] for d in dong)


def test_dinh_dang_so_kieu_viet_nam():
    """NFR-6 — Số hiện theo tập quán Việt Nam: nghìn chấm, thập phân phẩy"""
    assert aggregations.format_number(Decimal("1425942850.00"), 2) == "1.425.942.850"
    assert aggregations.format_number(Decimal("74.90"), 2) == "74,90"
    assert aggregations.format_number(Decimal("4303"), 0) == "4.303"
    assert aggregations.format_number(None) == "—"


def test_tong_chi_mot_lenh(bang_mkt, dong_mau, nguoi_dung, django_assert_num_queries):
    """Quy tắc Q2 — totals_only gộp về đúng một lệnh truy vấn"""
    cot = list(bang_mkt.columns.all())
    qs = DataRecord.objects.in_scope(nguoi_dung["manager_mkt"])
    with django_assert_num_queries(1):
        tong = aggregations.totals_only(bang_mkt, qs, columns=cot)
    assert tong["c_doanh_so"] == Decimal("3280000")
