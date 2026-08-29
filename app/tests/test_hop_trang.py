"""Kiểm thử hộp trắng — những nhánh mã chưa ai chạy vào.

Bản đo bao phủ chỉ ra chỗ hổng, tệp này lấp những chỗ **đáng** lấp. Không chạy
theo con số: mục tiêu là các nhánh mà nếu hỏng thì hỏng lặng lẽ.

Ba nhóm được chọn:

1. `link_service` — kiểm khớp kiểu giữa trường biểu mẫu và cột bảng. Hỏng ở
   đây là dữ liệu người dùng gõ vào rơi vào cột không nhận được nó (AC-8.6)
2. `core.tasks` — tác vụ nền, trước nay 0% và chỉ chạy trên máy chủ thật
3. Đường **huỷ** trong tầng dịch vụ — chỗ chỉ chạy khi có lỗi, nên không bao
   giờ chạy trong lối đi thuận
"""
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from core.exceptions import BusinessError
from core.money import format_money
from core.constants import AuditAction, Currency
from core.models import AuditLog
from forms_builder.meaning import FieldType, Meaning, type_fits
from forms_builder.models import ColumnDef, FieldDef, TableDef
from forms_builder.services import form_service, link_service, record_service, table_service

pytestmark = pytest.mark.django_db


@pytest.fixture
def bang(departments, nguoi_dung):
    b = TableDef.objects.create(
        name="Bảng thử", code="bang_thu",
        department=departments["sale"], created_by=nguoi_dung["manager_sale"],
    )
    ColumnDef.objects.create(
        table=b, name="Doanh thu", code="doanh_thu",
        field_type=FieldType.MONEY, meaning=Meaning.REVENUE, order=0,
    )
    ColumnDef.objects.create(
        table=b, name="Số lượng", code="so_luong", field_type=FieldType.INTEGER, order=1,
    )
    return b


# ══ link_service — kiểm khớp kiểu, AC-8.6 ══════════════════════════

def test_go_lien_ket_bang_cach_truyen_none(bang, departments, nguoi_dung):
    """FR-8.3 — Truyền cột đích là None thì gỡ liên kết, không nổ"""
    bm = form_service.create_form(
        name="Biểu mẫu thử", code="bm_thu", department=departments["sale"],
        table=bang, actor=nguoi_dung["manager_sale"],
    )
    truong = FieldDef.objects.create(
        name="Doanh thu", code="doanh_thu", field_type=FieldType.MONEY,
        meaning=Meaning.REVENUE, department=departments["sale"],
    )
    tf = form_service.add_field(
        bm, truong, column=bang.columns.get(code="doanh_thu"),
        actor=nguoi_dung["manager_sale"],
    )
    assert getattr(tf, "link", None) is not None

    link_service.link_column(tf, None)
    tf.refresh_from_db()
    assert not hasattr(tf, "link") or tf.link is None


def test_doi_kieu_truong_lam_hong_lien_ket_thi_bi_chan(bang, departments, nguoi_dung):
    """FR-8.6 — Đổi kiểu trường làm liên kết đang có thành lệch thì chặn

    Thà không cho đổi kiểu, còn hơn để biểu mẫu nhận dữ liệu rồi ghi vào cột
    sai kiểu. Nhánh này chỉ chạy khi thật sự có liên kết hỏng.
    """
    bm = form_service.create_form(
        name="Biểu mẫu thử", code="bm_thu", department=departments["sale"],
        table=bang, actor=nguoi_dung["manager_sale"],
    )
    truong = FieldDef.objects.create(
        name="Doanh thu", code="doanh_thu", field_type=FieldType.MONEY,
        meaning=Meaning.REVENUE, department=departments["sale"],
    )
    form_service.add_field(
        bm, truong, column=bang.columns.get(code="doanh_thu"),
        actor=nguoi_dung["manager_sale"],
    )

    with pytest.raises(BusinessError) as loi:
        form_service.update_field_def(
            truong, {"field_type": FieldType.TEXT, "meaning": ""},
            actor=nguoi_dung["manager_sale"],
        )
    assert "Biểu mẫu thử" in str(loi.value)


def test_tom_tat_lien_ket_dem_dung(bang, departments, nguoi_dung):
    """FR-8.6 — Tóm tắt cho biết bao nhiêu trường đã nối trên tổng số"""
    bm = form_service.create_form(
        name="Biểu mẫu thử", code="bm_thu", department=departments["sale"],
        table=bang, actor=nguoi_dung["manager_sale"],
    )
    for ma, kieu in (("doanh_thu", FieldType.MONEY), ("ghi_chu", FieldType.TEXT)):
        truong = FieldDef.objects.create(
            name=ma, code=ma, field_type=kieu, department=departments["sale"],
        )
        cot = bang.columns.filter(code=ma).first()
        form_service.add_field(bm, truong, column=cot, actor=nguoi_dung["manager_sale"])

    da_noi, tong, loi = link_service.summary(bm)
    assert (da_noi, tong, loi) == (1, 2, [])      # ghi_chu chưa có cột đích


def test_cau_giai_thich_khop_kieu(bang):
    """FR-8.6 — `check` trả câu giải thích khi lệch, trả None khi khớp"""
    cot_tien = bang.columns.get(code="doanh_thu")
    truong_chu = FieldDef(name="Ghi chú", code="ghi_chu", field_type=FieldType.TEXT)
    truong_tien = FieldDef(name="Doanh thu", code="dt", field_type=FieldType.MONEY)

    assert link_service.check(truong_tien, cot_tien) is None
    cau = link_service.check(truong_chu, cot_tien)
    assert "Ghi chú" in cau and "Doanh thu" in cau


def test_rut_cau_loi_ra_khoi_validation_error():
    """NFR-6 — Rút được câu tiếng Việt ra khỏi lỗi của Django để hiện lên"""
    loi_dict = ValidationError({"column": ValidationError("Lệch kiểu rồi")})
    loi_list = ValidationError(["Câu một", "Câu hai"])

    assert "Lệch kiểu rồi" in link_service.validation_message(loi_dict)
    assert "Câu một" in link_service.validation_message(loi_list)
    assert link_service.validation_message("chuỗi thường") == "chuỗi thường"


# ══ Bảng tương thích kiểu — mọi cặp ════════════════════════════════

@pytest.mark.parametrize("truong,cot,khop", [
    (FieldType.INTEGER, FieldType.MONEY, True),        # nới rộng an toàn
    (FieldType.INTEGER, FieldType.DECIMAL, True),
    (FieldType.DECIMAL, FieldType.INTEGER, False),     # mất phần lẻ
    (FieldType.TEXT, FieldType.LONG_TEXT, True),
    (FieldType.LONG_TEXT, FieldType.TEXT, False),      # có thể tràn độ dài
    (FieldType.DATE, FieldType.DATETIME, True),
    (FieldType.DATETIME, FieldType.DATE, False),       # mất giờ
    (FieldType.TEXT, FieldType.MONEY, False),          # đây là AC-8.6
    (FieldType.BOOLEAN, FieldType.TEXT, False),
    (FieldType.CHOICE, FieldType.TEXT, True),
])
def test_bang_tuong_thich_kieu(truong, cot, khop):
    """FR-8.6 — Bảng tương thích kiểu chỉ cho nới rộng an toàn, một chiều"""
    assert type_fits(truong, cot) is khop


# ══ Ép kiểu giá trị người dùng gõ ══════════════════════════════════

@pytest.mark.parametrize("kieu,gia_tri,mong_doi", [
    (FieldType.INTEGER, "1.234", 1234),                # dấu chấm ngăn nghìn
    (FieldType.INTEGER, " 42 ", 42),
    (FieldType.MONEY, "1234,56", "1234.56"),           # dấu phẩy thập phân
    (FieldType.DATE, "2026-08-28", "2026-08-28"),
    (FieldType.BOOLEAN, "có", True),
    (FieldType.BOOLEAN, "không", False),
    (FieldType.TEXT, "  chữ  ", "chữ"),
])
def test_ep_kieu_gia_tri_hop_le(bang, kieu, gia_tri, mong_doi):
    """BR-8 — Ép giá trị người dùng gõ về đúng kiểu, tiền qua số thập phân"""
    cot = ColumnDef(table=bang, name="thử", code="thu", field_type=kieu)
    assert record_service.parse_value(cot, gia_tri) == mong_doi


@pytest.mark.parametrize("kieu,gia_tri", [
    (FieldType.INTEGER, "không phải số"),
    (FieldType.MONEY, "abc"),
    (FieldType.DATE, "28/08/2026"),                    # sai định dạng
    (FieldType.DATETIME, "hôm qua"),
])
def test_ep_kieu_gia_tri_hong_thi_bao_loi_tieng_viet(bang, kieu, gia_tri):
    """NFR-6 — Gõ sai kiểu thì báo lỗi tiếng Việt, không nổ trang trắng"""
    cot = ColumnDef(table=bang, name="Ô thử", code="thu", field_type=kieu)
    with pytest.raises(BusinessError) as loi:
        record_service.parse_value(cot, gia_tri)
    assert "Ô thử" in str(loi.value)


def test_o_trong_thi_tra_none(bang):
    """BR-8 — Ô để trống trả None, không phải chuỗi rỗng hay số không"""
    cot = ColumnDef(table=bang, name="thử", code="thu", field_type=FieldType.MONEY)
    assert record_service.parse_value(cot, "") is None
    assert record_service.parse_value(cot, "   ") is None
    assert record_service.parse_value(cot, None) is None


# ══ Hiển thị và đọc lại tiền ═══════════════════════════════════════

@pytest.mark.parametrize("chuoi,mong_doi", [
    ("1.234,56", Decimal("1234.56")),      # đúng thứ format_money in ra
    ("1234,56", Decimal("1234.56")),
    ("1.234.567", Decimal("1234567")),     # chỉ chấm, nhiều nhóm → ngăn nghìn
    ("1.234", Decimal("1234")),            # chỉ chấm, ba chữ số → ngăn nghìn
    ("150.00", Decimal("150.00")),         # chỉ chấm, hai chữ số → thập phân
    ("438446060", Decimal("438446060")),
    ("-500", Decimal("-500")),
    ("1.234,56 ₫", Decimal("1234.56")),    # kèm ký hiệu tiền tệ
])
def test_doc_lai_duoc_so_tien_nguoi_dung_go(chuoi, mong_doi):
    """BR-8 — Đọc số tiền theo tập quán Việt Nam: chấm ngăn nghìn, phẩy thập phân"""
    from core.money import parse_money

    assert parse_money(chuoi) == mong_doi


@pytest.mark.parametrize("so", [
    Decimal("1234.56"), Decimal("438446060"), Decimal("0.01"),
    Decimal("1000000"), Decimal("-2500.75"),
])
@pytest.mark.parametrize("tien_te", [Currency.VND, Currency.USD])
def test_hien_ra_roi_doc_lai_van_dung_so(so, tien_te):
    """BR-8 — Số hiện trên màn hình phải đọc lại được đúng nó

    Đây là lỗi thật đã tìm ra: `format_money` in ra `1.234,56` nhưng bộ đọc
    bỏ hết dấu phẩy nên nhận thành 123456 — sai gấp trăm lần. Người dùng chép
    số trên màn hình dán vào ô nhập là hỏng ngay.
    """
    from core.money import CURRENCY_DECIMALS, parse_money

    so_le = CURRENCY_DECIMALS.get(tien_te, 2)
    lam_tron = so.quantize(Decimal(1) if so_le == 0 else Decimal("0.01"))
    assert parse_money(format_money(so, tien_te)) == lam_tron


# ══ Hiển thị tiền ══════════════════════════════════════════════════

@pytest.mark.parametrize("so,tien_te,co_trong", [
    (Decimal("1234567"), Currency.VND, "1.234.567"),
    (Decimal("1234.56"), Currency.USD, "1.234,56"),
    (Decimal("0"), Currency.VND, "0"),
    (Decimal("-500"), Currency.VND, "500"),
])
def test_hien_tien_theo_tung_loai(so, tien_te, co_trong):
    """AC-9.5 — Tiền hiện đúng tập quán từng loại, không dùng số thực"""
    assert co_trong in format_money(so, tien_te)


# ══ Tác vụ nền ═════════════════════════════════════════════════════

def test_tac_vu_hang_doi_chay_duoc():
    """kien-truc.md — Celery và Redis chạy được một tác vụ mẫu"""
    from core.tasks import kiem_tra_hang_doi

    assert kiem_tra_hang_doi.delay().get() == "hang doi hoat dong"


def test_tac_vu_don_tep_ghi_nhat_ky():
    """AC-9.2 — Tác vụ nền cũng ghi nhật ký, không chạy âm thầm"""
    from core.tasks import don_tep_xuat_qua_han

    truoc = AuditLog.objects.filter(action=AuditAction.DELETE).count()
    don_tep_xuat_qua_han.delay().get()
    assert AuditLog.objects.filter(action=AuditAction.DELETE).count() == truoc + 1


# ══ Đường huỷ trong tầng dịch vụ ═══════════════════════════════════

def test_sua_bang_khong_doi_gi_thi_khong_ghi_nhat_ky(bang, nguoi_dung):
    """BR-5 — Gọi hàm sửa mà không đổi gì thì không sinh nhật ký rác"""
    truoc = AuditLog.objects.filter(action=AuditAction.UPDATE).count()
    table_service.update_table(
        bang, {"name": bang.name}, actor=nguoi_dung["manager_sale"])
    assert AuditLog.objects.filter(action=AuditAction.UPDATE).count() == truoc


def test_bo_cot_thi_tinh_lai_ca_bang(bang, nguoi_dung):
    """ADR-006 — Bỏ cột thì bản ghi cũ được đồng bộ lại, không giữ số cũ"""
    bg = record_service.create_record(
        bang, {"doanh_thu": "500", "so_luong": 2}, actor=nguoi_dung["manager_sale"])
    assert bg.val_revenue == Decimal("500.00")

    table_service.remove_column(
        bang.columns.get(code="doanh_thu"), actor=nguoi_dung["manager_sale"])
    bg.refresh_from_db()
    assert bg.val_revenue is None


def test_lenh_tao_bang_van_don_chay_lai_duoc(departments, nguoi_dung):
    """FR-6.3 — Lệnh tạo bảng vận đơn gọi nhiều lần không sinh bảng trùng"""
    from django.core.management import call_command
    from io import StringIO

    from orders.constants import WAYBILL_TABLE_CODE

    ra = StringIO()
    call_command("tao_bang_van_don", stdout=ra)
    call_command("tao_bang_van_don", stdout=ra)

    assert TableDef.all_objects.filter(code=WAYBILL_TABLE_CODE).count() == 1
    assert WAYBILL_TABLE_CODE in ra.getvalue()
