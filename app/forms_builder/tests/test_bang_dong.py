"""Kiểm thử mô hình bảng động — phần rủi ro nhất của dự án.

Ba thứ phải đúng, nếu sai thì mọi giai đoạn sau phải làm lại:

1. Cột mang nhãn ý nghĩa phải được chép sang cột tách có chỉ mục (ADR-001)
2. Cột tính sẵn phải tính đúng và lưu lại được (ADR-006)
3. Lọc và sắp xếp phải chạy đúng trên cả cột tách lẫn khoá JSON
"""
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from forms_builder import query
from forms_builder.meaning import FieldType, Meaning, aggregations_for, can_group, can_sum
from forms_builder.models import ColumnDef, ComputeOp, DataRecord, TableDef

pytestmark = pytest.mark.django_db


@pytest.fixture
def bang_mkt(departments, nguoi_dung):
    """Bảng báo cáo Marketing, dựng đúng theo sheet BC MKT của khách hàng."""
    bang = TableDef.objects.create(
        name="Báo cáo Marketing", code="bao_cao_mkt",
        department=departments["mkt"], created_by=nguoi_dung["admin"],
    )
    cot = [
        ("Ngày", "ngay", FieldType.DATE, Meaning.DATE),
        ("Marketer", "marketer", FieldType.TEXT, Meaning.SELLER),
        ("Số Mess", "so_mess", FieldType.INTEGER, ""),
        ("CPQC", "cpqc", FieldType.MONEY, ""),
        ("Số đơn", "so_don", FieldType.INTEGER, ""),
        ("Doanh số", "doanh_so", FieldType.MONEY, Meaning.REVENUE),
    ]
    for i, (ten, ma, kieu, nhan) in enumerate(cot):
        ColumnDef.objects.create(
            table=bang, name=ten, code=ma, field_type=kieu, meaning=nhan, order=i,
        )
    # Hai cột tính sẵn, đúng công thức trong tệp thật
    ColumnDef.objects.create(
        table=bang, name="CPO", code="cpo", field_type=FieldType.MONEY, order=6,
        is_computed=True, compute_op=ComputeOp.DIVIDE,
        compute_left="cpqc", compute_right="so_don", compute_decimals=0,
    )
    ColumnDef.objects.create(
        table=bang, name="Tỉ lệ chốt", code="ti_le_chot", field_type=FieldType.DECIMAL,
        order=7, is_computed=True, compute_op=ComputeOp.PERCENT,
        compute_left="so_don", compute_right="so_mess", compute_decimals=2,
    )
    return bang


def tao_ban_ghi(bang, nguoi, **gia_tri):
    return DataRecord.objects.create(
        table=bang, created_by=nguoi, department=bang.department, data=gia_tri,
    )


# ══ Cột tách có chỉ mục — ADR-001 ══════════════════════════════════

def test_cot_mang_nhan_duoc_chep_sang_cot_tach(bang_mkt, nguoi_dung):
    """AC-7.2 — Cột mang nhãn ý nghĩa được tách ra cột riêng có chỉ mục"""
    bg = tao_ban_ghi(
        bang_mkt, nguoi_dung["staff_mkt"],
        ngay="2026-08-28", marketer="Nguyễn Quang Minh",
        so_mess=4303, cpqc="438446060", so_don=291, doanh_so="1425942850",
    )
    bg.refresh_from_db()
    assert str(bg.val_date) == "2026-08-28"
    assert bg.val_seller == "Nguyễn Quang Minh"
    assert bg.val_revenue == Decimal("1425942850.00")


def test_cot_khong_co_nhan_chi_nam_trong_json(bang_mkt, nguoi_dung):
    """AC-7.2 — Cột không có nhãn chỉ lưu trong JSON, không chiếm cột tách"""
    bg = tao_ban_ghi(bang_mkt, nguoi_dung["staff_mkt"], so_mess=4303, cpqc="438446060")
    bg.refresh_from_db()
    assert bg.data["so_mess"] == 4303
    assert bg.val_customer == ""
    assert bg.val_phone == ""


def test_sua_ban_ghi_thi_cot_tach_cap_nhat_theo(bang_mkt, nguoi_dung):
    """AC-7.2 — Sửa giá trị thì cột tách phải đổi theo, không lệch với JSON"""
    bg = tao_ban_ghi(bang_mkt, nguoi_dung["staff_mkt"], doanh_so="1000000")
    bg.data["doanh_so"] = "2000000"
    bg.save()
    bg.refresh_from_db()
    assert bg.val_revenue == Decimal("2000000.00")


# ══ Cột tính sẵn — ADR-006 ═════════════════════════════════════════

def test_cot_tinh_san_tinh_dung_theo_so_lieu_that(bang_mkt, nguoi_dung):
    """AC-7.8 — Cột tính sẵn cho ra đúng số liệu trong tệp thật của khách hàng

    Dòng đầu sheet BC MKT: CPQC 438.446.060, Số đơn 291, Số Mess 4.303.
    Bản của khách hàng ra CPO = 1.506.687 và tỉ lệ chốt = 6,76%.
    """
    bg = tao_ban_ghi(
        bang_mkt, nguoi_dung["staff_mkt"],
        so_mess=4303, cpqc="438446060", so_don=291,
    )
    bg.refresh_from_db()
    assert bg.data["cpo"] == "1506687"
    assert bg.data["ti_le_chot"] == "6.76"


def test_chia_cho_khong_thi_de_trong_khong_no(bang_mkt, nguoi_dung):
    """AC-7.8 — Chia cho không thì để trống, không làm hỏng cả dòng"""
    bg = tao_ban_ghi(bang_mkt, nguoi_dung["staff_mkt"], cpqc="1000", so_don=0)
    bg.refresh_from_db()
    assert bg.data["cpo"] is None


def test_thieu_toan_hang_thi_de_trong(bang_mkt, nguoi_dung):
    """AC-7.8 — Thiếu một toán hạng thì để trống chứ không hiện số sai"""
    bg = tao_ban_ghi(bang_mkt, nguoi_dung["staff_mkt"], cpqc="1000")
    bg.refresh_from_db()
    assert bg.data["cpo"] is None


def test_cot_tinh_san_luu_lai_nen_sap_xep_duoc(bang_mkt, nguoi_dung):
    """AC-7.3 — Cột tính sẵn lưu vào JSON nên sắp xếp theo nó được

    Tính lúc hiển thị thì chỉ sắp xếp được trong một trang, sai ngay khi có
    trang thứ hai.
    """
    for cpqc, don in (("300", 3), ("100", 1), ("200", 1)):
        tao_ban_ghi(bang_mkt, nguoi_dung["staff_mkt"], cpqc=cpqc, so_don=don)
    cm = query.ColumnMap(bang_mkt)
    qs = query.apply_sort(DataRecord.objects.filter(table=bang_mkt), cm, "cpo")
    assert [r.data["cpo"] for r in qs] == ["100", "100", "200"]


# ══ Chặn cấu hình sai ngay lúc lưu định nghĩa ══════════════════════

def test_chan_gan_nhan_cho_truong_sai_kieu(bang_mkt):
    """AC-8.6 — Gán nhãn Doanh thu cho trường kiểu chữ thì bị chặn"""
    cot = ColumnDef(
        table=bang_mkt, name="Ghi chú", code="ghi_chu",
        field_type=FieldType.TEXT, meaning=Meaning.REVENUE,
    )
    with pytest.raises(ValidationError) as loi:
        cot.full_clean()
    assert "meaning" in loi.value.error_dict


def test_chan_cot_tinh_san_thieu_toan_hang(bang_mkt):
    """AC-8.6 — Cột tính sẵn thiếu toán hạng thì bị chặn"""
    cot = ColumnDef(
        table=bang_mkt, name="Hỏng", code="hong", field_type=FieldType.DECIMAL,
        is_computed=True, compute_op=ComputeOp.DIVIDE, compute_left="cpqc",
    )
    with pytest.raises(ValidationError):
        cot.full_clean()


def test_chan_cot_tinh_tu_chinh_no(bang_mkt):
    """AC-8.6 — Cột không tính được từ chính nó"""
    cot = ColumnDef(
        table=bang_mkt, name="Vòng", code="vong", field_type=FieldType.DECIMAL,
        is_computed=True, compute_op=ComputeOp.DIVIDE,
        compute_left="vong", compute_right="cpqc",
    )
    with pytest.raises(ValidationError):
        cot.full_clean()


def test_chan_hai_cot_trung_ten_ky_thuat(bang_mkt):
    """AC-8.6 — Hai cột trong cùng bảng không được trùng tên kỹ thuật"""
    from django.db.utils import IntegrityError

    with pytest.raises(IntegrityError):
        ColumnDef.objects.create(
            table=bang_mkt, name="CPQC lần hai", code="cpqc",
            field_type=FieldType.MONEY,
        )


# ══ Truy vấn động ══════════════════════════════════════════════════

def test_loc_theo_cot_tach(bang_mkt, nguoi_dung):
    """AC-7.2 — Lọc theo cột mang nhãn dùng cột tách có chỉ mục"""
    tao_ban_ghi(bang_mkt, nguoi_dung["staff_mkt"], marketer="Minh", doanh_so="100")
    tao_ban_ghi(bang_mkt, nguoi_dung["staff_mkt"], marketer="Nam", doanh_so="200")
    cm = query.ColumnMap(bang_mkt)
    assert cm.path("marketer") == "val_seller"
    qs = query.apply_filters(DataRecord.objects.all(), cm, {"marketer": "Minh"})
    assert qs.count() == 1


def test_loc_theo_khoa_json(bang_mkt, nguoi_dung):
    """AC-7.2 — Lọc theo cột không có nhãn dùng khoá trong JSON"""
    tao_ban_ghi(bang_mkt, nguoi_dung["staff_mkt"], so_mess=100)
    tao_ban_ghi(bang_mkt, nguoi_dung["staff_mkt"], so_mess=200)
    cm = query.ColumnMap(bang_mkt)
    assert cm.path("so_mess") == "data__so_mess"
    qs = query.apply_filters(DataRecord.objects.all(), cm, {"so_mess": 200})
    assert qs.count() == 1


def test_cot_la_va_phep_so_sanh_la_bi_bo_qua(bang_mkt, nguoi_dung):
    """AC-7.2 — Tham số lạ trên đường dẫn bị bỏ qua, không ném lỗi

    Tham số do người dùng gõ nên không tin được. Bỏ qua an toàn hơn là nổ.
    """
    tao_ban_ghi(bang_mkt, nguoi_dung["staff_mkt"], so_mess=100)
    cm = query.ColumnMap(bang_mkt)
    qs = query.apply_filters(
        DataRecord.objects.all(), cm,
        {"cot_khong_ton_tai": "x", "so_mess__phep_la": "y"},
    )
    assert qs.count() == 1


def test_loc_theo_khoang_tren_cot_tach(bang_mkt, nguoi_dung):
    """AC-7.2 — So sánh lớn hơn nhỏ hơn chạy được trên cột tách"""
    for tien in ("100", "500", "900"):
        tao_ban_ghi(bang_mkt, nguoi_dung["staff_mkt"], doanh_so=tien)
    cm = query.ColumnMap(bang_mkt)
    qs = query.apply_filters(DataRecord.objects.all(), cm, {"doanh_so__lon_bang": "500"})
    assert qs.count() == 2


def test_tim_kiem_chung_chi_quet_cot_tach(bang_mkt, nguoi_dung):
    """AC-7.2 — Tìm kiếm chung chỉ quét cột tách, không quét JSON

    Quét JSON thì không dùng được chỉ mục, và với 50.000 bản ghi sẽ vượt
    ngưỡng hai giây của NFR-1.
    """
    tao_ban_ghi(bang_mkt, nguoi_dung["staff_mkt"], marketer="Nguyễn Quang Minh")
    tao_ban_ghi(bang_mkt, nguoi_dung["staff_mkt"], marketer="Hoàng Tuấn Cường")
    cm = query.ColumnMap(bang_mkt)
    assert "val_seller" in cm.searchable_paths()
    assert "data__so_mess" not in cm.searchable_paths()
    assert query.apply_search(DataRecord.objects.all(), cm, "Quang").count() == 1


def test_sap_xep_hai_chieu(bang_mkt, nguoi_dung):
    """AC-7.3 — Sắp xếp theo cột cho ra thứ tự đúng, cả tăng và giảm"""
    for tien in ("300", "100", "200"):
        tao_ban_ghi(bang_mkt, nguoi_dung["staff_mkt"], doanh_so=tien)
    cm = query.ColumnMap(bang_mkt)
    tang = query.apply_sort(DataRecord.objects.all(), cm, "doanh_so")
    giam = query.apply_sort(DataRecord.objects.all(), cm, "doanh_so", descending=True)
    assert [r.val_revenue for r in tang] == [Decimal("100.00"), Decimal("200.00"), Decimal("300.00")]
    assert [r.val_revenue for r in giam][0] == Decimal("300.00")


# ══ Phạm vi quyền trên bảng động ═══════════════════════════════════

def test_ban_ghi_van_theo_pham_vi_quyen(bang_mkt, departments, nguoi_dung):
    """AC-3.5 — Manager bộ phận khác không thấy bản ghi của bảng này"""
    tao_ban_ghi(bang_mkt, nguoi_dung["staff_mkt"], so_mess=1)
    thay_mkt = DataRecord.objects.in_scope(nguoi_dung["manager_mkt"])
    thay_sale = DataRecord.objects.in_scope(nguoi_dung["manager_sale"])
    assert thay_mkt.count() == 1
    assert thay_sale.count() == 0


def test_admin_thay_moi_ban_ghi(bang_mkt, nguoi_dung):
    """AC-3.4 — Admin thấy bản ghi của mọi bảng"""
    tao_ban_ghi(bang_mkt, nguoi_dung["staff_mkt"], so_mess=1)
    assert DataRecord.objects.in_scope(nguoi_dung["admin"]).count() == 1


def test_xoa_ban_ghi_la_danh_dau(bang_mkt, nguoi_dung):
    """AC-9.1 — Xoá bản ghi trong bảng động cũng là đánh dấu"""
    bg = tao_ban_ghi(bang_mkt, nguoi_dung["staff_mkt"], so_mess=1)
    bg.delete(by=nguoi_dung["admin"])
    assert not DataRecord.objects.filter(pk=bg.pk).exists()
    assert DataRecord.all_objects.filter(pk=bg.pk).exists()


# ══ Bảy nhãn ý nghĩa ═══════════════════════════════════════════════

def test_bay_nhan_dung_theo_adr_007():
    """AC-8.2 — Bảy nhãn ý nghĩa đúng danh sách đã chốt ở ADR-007"""
    assert [m.value for m in Meaning] == [
        "date", "customer", "phone", "revenue", "seller", "product", "status",
    ]


def test_nhan_biet_phep_tinh_nao_lam_duoc():
    """AC-5.1 — Nhãn quyết định báo cáo tổng hợp tính được gì trên cột"""
    assert can_sum(Meaning.REVENUE)
    assert not can_sum(Meaning.STATUS)
    assert can_group(Meaning.PRODUCT)
    assert can_group(Meaning.SELLER)
    assert aggregations_for(Meaning.PHONE)
