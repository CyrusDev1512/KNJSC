"""Kiểm thử biểu mẫu và cấp quyền riêng — Giai đoạn 3 phần B.

Ba thứ phải đúng:

1. Nối trường vào cột lệch kiểu thì bị chặn, và nói rõ trường nào — AC-8.6
2. Dữ liệu điền vào biểu mẫu ghi đúng bảng đích — AC-8.3
3. Cấp quyền riêng thì thấy thêm, thu quyền thì hết thấy, và phiên đang mở
   của người bị đổi quyền mất hiệu lực ngay — AC-1.6

Mỗi bài phân quyền kiểm **cả hai chiều**.
"""
from decimal import Decimal

import pytest

from core.constants import AuditAction
from core.exceptions import BusinessError
from core.models import AuditLog
from forms_builder.meaning import FieldType, Meaning, type_fits
from forms_builder.models import (
    ColumnDef, ComputeOp, DataRecord, FieldDef, FormDef, FormField,
    FormTableLink, Grant, GrantAction, TableDef,
)
from forms_builder.services import form_service, grant_service, link_service

pytestmark = pytest.mark.django_db


@pytest.fixture
def bang_mkt(departments, nguoi_dung):
    """Bảng đích của bộ phận Marketing, có một cột tính sẵn."""
    bang = TableDef.objects.create(
        name="Báo cáo Marketing", code="bc_mkt",
        department=departments["mkt"], created_by=nguoi_dung["manager_mkt"],
    )
    cot = [
        ("Ngày", "ngay", FieldType.DATE, Meaning.DATE),
        ("Marketer", "marketer", FieldType.TEXT, Meaning.SELLER),
        ("Số Mess", "so_mess", FieldType.INTEGER, ""),
        ("Số đơn", "so_don", FieldType.INTEGER, ""),
        ("Doanh số", "doanh_so", FieldType.MONEY, Meaning.REVENUE),
    ]
    for i, (ten, ma, kieu, nhan) in enumerate(cot):
        ColumnDef.objects.create(
            table=bang, name=ten, code=ma, field_type=kieu, meaning=nhan, order=i,
        )
    ColumnDef.objects.create(
        table=bang, name="Tỉ lệ chốt", code="ti_le_chot",
        field_type=FieldType.DECIMAL, order=5, is_computed=True,
        compute_op=ComputeOp.PERCENT, compute_left="so_don",
        compute_right="so_mess", compute_decimals=2,
    )
    return bang


@pytest.fixture
def truong_mkt(departments):
    """Thư viện định nghĩa trường của bộ phận Marketing."""
    ds = {}
    for ten, ma, kieu, nhan in [
        ("Ngày", "ngay", FieldType.DATE, Meaning.DATE),
        ("Marketer", "marketer", FieldType.TEXT, Meaning.SELLER),
        ("Số Mess", "so_mess", FieldType.INTEGER, ""),
        ("Số đơn", "so_don", FieldType.INTEGER, ""),
        ("Doanh số", "doanh_so", FieldType.MONEY, Meaning.REVENUE),
        ("Ghi chú", "ghi_chu", FieldType.TEXT, ""),
    ]:
        ds[ma] = FieldDef.objects.create(
            name=ten, code=ma, field_type=kieu, meaning=nhan,
            department=departments["mkt"],
        )
    return ds


@pytest.fixture
def bieu_mau(bang_mkt, truong_mkt, departments, nguoi_dung):
    """Biểu mẫu Marketing đã nối đủ năm trường vào năm cột."""
    bm = form_service.create_form(
        name="Báo cáo Marketing ngày", code="bc_mkt_ngay",
        department=departments["mkt"], table=bang_mkt,
        actor=nguoi_dung["manager_mkt"],
    )
    for ma in ("ngay", "marketer", "so_mess", "so_don", "doanh_so"):
        form_service.add_field(
            bm, truong_mkt[ma], column=bang_mkt.columns.get(code=ma),
            required=(ma in ("ngay", "so_mess")),
            actor=nguoi_dung["manager_mkt"],
        )
    return bm


# ══ Kiểm khớp kiểu — FR-8.6 ════════════════════════════════════════

def test_noi_truong_kieu_chu_vao_cot_kieu_so_bi_chan(bieu_mau, bang_mkt, truong_mkt, nguoi_dung):
    """AC-8.6 — Nối trường kiểu chữ vào cột kiểu số thì bị chặn, thông báo rõ"""
    from django.core.exceptions import ValidationError

    with pytest.raises(ValidationError) as loi:
        form_service.add_field(
            bieu_mau, truong_mkt["ghi_chu"],
            column=bang_mkt.columns.get(code="doanh_so"),
            actor=nguoi_dung["manager_mkt"],
        )
    cau = link_service.validation_message(loi.value)
    assert "Ghi chú" in cau          # phải chỉ đúng tên trường bị lệch
    assert "Doanh số" in cau


def test_noi_dung_kieu_thi_luu_duoc(bieu_mau, bang_mkt):
    """AC-8.6 — Chiều được phép: kiểu khớp thì nối được"""
    assert bieu_mau.fields.count() == 5
    assert FormTableLink.objects.filter(form_field__form=bieu_mau).count() == 5


def test_so_nguyen_ghi_duoc_vao_cot_tien(bieu_mau, bang_mkt, truong_mkt, nguoi_dung):
    """AC-8.6 — Nới rộng an toàn: số nguyên ghi được vào cột tiền"""
    assert type_fits(FieldType.INTEGER, FieldType.MONEY)
    assert not type_fits(FieldType.TEXT, FieldType.MONEY)
    assert not type_fits(FieldType.DECIMAL, FieldType.INTEGER)   # mất phần lẻ


def test_khong_noi_duoc_vao_cot_tinh_san(bieu_mau, bang_mkt, truong_mkt, nguoi_dung):
    """ADR-006 — Cột tính sẵn không nhận dữ liệu nhập tay"""
    from django.core.exceptions import ValidationError

    with pytest.raises(ValidationError) as loi:
        form_service.add_field(
            bieu_mau, truong_mkt["ghi_chu"],
            column=bang_mkt.columns.get(code="ti_le_chot"),
            actor=nguoi_dung["manager_mkt"],
        )
    assert "tính sẵn" in link_service.validation_message(loi.value)


def test_khong_noi_duoc_sang_cot_cua_bang_khac(bieu_mau, truong_mkt, departments, nguoi_dung):
    """FR-8.3 — Chỉ nối được vào cột của bảng đích, không phải bảng bất kỳ"""
    from django.core.exceptions import ValidationError

    bang_khac = TableDef.objects.create(
        name="Bảng khác", code="bang_khac", department=departments["mkt"],
        created_by=nguoi_dung["manager_mkt"],
    )
    cot_la = ColumnDef.objects.create(
        table=bang_khac, name="Lạ", code="la", field_type=FieldType.TEXT,
    )
    with pytest.raises(ValidationError):
        form_service.add_field(
            bieu_mau, truong_mkt["ghi_chu"], column=cot_la,
            actor=nguoi_dung["manager_mkt"],
        )


def test_bang_dich_phai_cung_bo_phan(bang_mkt, departments, nguoi_dung):
    """FR-3.4 — Biểu mẫu không ghi được sang bảng của bộ phận khác"""
    from django.core.exceptions import ValidationError

    with pytest.raises(ValidationError):
        form_service.create_form(
            name="Ghi chéo", code="ghi_cheo",
            department=departments["sale"], table=bang_mkt,
            actor=nguoi_dung["manager_sale"],
        )


# ══ Điền biểu mẫu — FR-8.2, FR-8.3 ═════════════════════════════════

def test_du_lieu_ghi_dung_bang_dich(client, bieu_mau, bang_mkt, nguoi_dung):
    """AC-8.3 — Dữ liệu từ biểu mẫu ghi đúng vào bảng đích đã chọn"""
    client.force_login(nguoi_dung["staff_mkt"])
    kq = client.post(f"/bieu-mau/{bieu_mau.code}/dien/", {
        "ngay": "2026-08-28", "marketer": "Nguyễn Quang Minh",
        "so_mess": "4303", "so_don": "291", "doanh_so": "1425942850",
    })
    assert kq.status_code == 302

    bg = DataRecord.objects.get(table=bang_mkt)
    assert bg.data["marketer"] == "Nguyễn Quang Minh"
    assert bg.val_revenue == Decimal("1425942850.00")
    assert bg.data["ti_le_chot"] == "6.76"      # cột tính sẵn tự tính


def test_truong_bat_buoc_bo_trong_thi_khong_gui_duoc(client, bieu_mau, bang_mkt, nguoi_dung):
    """AC-8.2 — Trường đánh dấu bắt buộc thì không gửi được nếu bỏ trống"""
    client.force_login(nguoi_dung["staff_mkt"])
    kq = client.post(f"/bieu-mau/{bieu_mau.code}/dien/", {
        "ngay": "", "marketer": "Ai đó", "so_mess": "10",
    })
    assert kq.status_code == 200                # ở lại trang, không chuyển hướng
    assert "Ngày" in kq.content.decode()
    assert not DataRecord.objects.filter(table=bang_mkt).exists()


def test_gia_tri_sai_kieu_bi_tu_choi(client, bieu_mau, bang_mkt, nguoi_dung):
    """NFR-6 — Gõ chữ vào ô số thì báo lỗi tiếng Việt, không hiện trang trắng"""
    client.force_login(nguoi_dung["staff_mkt"])
    kq = client.post(f"/bieu-mau/{bieu_mau.code}/dien/", {
        "ngay": "2026-08-28", "so_mess": "không phải số",
    })
    assert kq.status_code == 200
    assert "Số nguyên" in kq.content.decode()
    assert not DataRecord.objects.filter(table=bang_mkt).exists()


def test_dien_bieu_mau_sinh_mot_dong_nhat_ky(client, bieu_mau, nguoi_dung):
    """AC-9.2 — Mỗi lần nhập sinh một dòng nhật ký"""
    truoc = AuditLog.objects.filter(action=AuditAction.CREATE).count()
    client.force_login(nguoi_dung["staff_mkt"])
    client.post(f"/bieu-mau/{bieu_mau.code}/dien/", {
        "ngay": "2026-08-28", "so_mess": "10",
    })
    assert AuditLog.objects.filter(action=AuditAction.CREATE).count() == truoc + 1


# ══ Phạm vi quyền trên biểu mẫu ════════════════════════════════════

def test_nguoi_bo_phan_khac_khong_dien_duoc(client, bieu_mau, nguoi_dung):
    """AC-8.4 — Người không được phân quyền không điền được, gọi thẳng cũng chặn"""
    client.force_login(nguoi_dung["staff_sale_1"])
    assert client.get(f"/bieu-mau/{bieu_mau.code}/dien/").status_code == 404


def test_nguoi_trong_bo_phan_dien_duoc(client, bieu_mau, nguoi_dung):
    """AC-8.4 — Chiều được phép: người trong bộ phận điền được ngay"""
    client.force_login(nguoi_dung["staff_mkt"])
    assert client.get(f"/bieu-mau/{bieu_mau.code}/dien/").status_code == 200


def test_leader_thay_bieu_mau_du_khong_phai_nguoi_tao(bieu_mau, nguoi_dung):
    """AC-3.2 — Leader thấy biểu mẫu của bộ phận mình, dù do Manager tạo

    Bài này đỏ nếu `FormDef` quay lại dùng phạm vi theo người tạo.
    """
    thay = FormDef.objects.in_scope(nguoi_dung["staff_mkt"])
    assert list(thay.values_list("code", flat=True)) == ["bc_mkt_ngay"]


def test_staff_khong_sua_duoc_bieu_mau(client, bieu_mau, nguoi_dung):
    """AC-3.7 — Staff gọi thẳng đường dẫn sửa biểu mẫu vẫn bị từ chối"""
    client.force_login(nguoi_dung["staff_mkt"])
    assert client.get(f"/bieu-mau/{bieu_mau.code}/sua/").status_code == 403


def test_bieu_mau_ngung_dung_thi_khong_dien_duoc(client, bieu_mau, nguoi_dung):
    """FR-8.5 — Biểu mẫu đã ngừng dùng thì không nhận dữ liệu nữa"""
    form_service.update_form(bieu_mau, {"is_active": False},
                             actor=nguoi_dung["manager_mkt"])
    client.force_login(nguoi_dung["staff_mkt"])
    assert client.get(f"/bieu-mau/{bieu_mau.code}/dien/").status_code == 403


# ══ Sửa biểu mẫu không mất dữ liệu — FR-8.5 ════════════════════════

def test_sua_bieu_mau_khong_lam_mat_du_lieu(bieu_mau, bang_mkt, nguoi_dung):
    """AC-8.5 — Sửa biểu mẫu không làm mất dữ liệu đã nhập trước đó"""
    from forms_builder.services import record_service

    bg = record_service.create_record(
        bang_mkt, {"marketer": "Trước khi sửa", "so_mess": 100, "so_don": 5},
        actor=nguoi_dung["staff_mkt"],
    )

    # Bỏ hai trường, đổi tên biểu mẫu
    for ma in ("marketer", "so_mess"):
        form_service.remove_field(
            bieu_mau.fields.get(field__code=ma), actor=nguoi_dung["manager_mkt"])
    form_service.update_form(bieu_mau, {"name": "Tên mới"},
                             actor=nguoi_dung["manager_mkt"])

    bg.refresh_from_db()
    assert bg.data["marketer"] == "Trước khi sửa"
    assert bg.val_seller == "Trước khi sửa"
    assert bg.data["so_mess"] == 100


def test_bo_truong_khoi_bieu_mau_khong_xoa_dinh_nghia(bieu_mau, truong_mkt, nguoi_dung):
    """FR-8.5 — Bỏ trường khỏi biểu mẫu không xoá nó khỏi thư viện dùng chung"""
    form_service.remove_field(
        bieu_mau.fields.get(field__code="marketer"), actor=nguoi_dung["manager_mkt"])

    assert not bieu_mau.fields.filter(field__code="marketer").exists()
    assert FieldDef.objects.filter(code="marketer").exists()


# ══ Cấp quyền riêng — FR-8.4, FR-3.4 ═══════════════════════════════

def test_cap_quyen_thi_thay_bang_cua_bo_phan_khac(bang_mkt, nguoi_dung):
    """FR-3.4 — Không xem được bộ phận khác, trừ khi được cấp quyền riêng"""
    nguoi = nguoi_dung["staff_sale_1"]
    assert not TableDef.objects.in_scope(nguoi).filter(code="bc_mkt").exists()

    grant_service.grant(
        table=bang_mkt, user=nguoi, action=GrantAction.VIEW,
        actor=nguoi_dung["manager_mkt"],
    )
    grant_service.clear_cache(nguoi)
    assert TableDef.objects.in_scope(nguoi).filter(code="bc_mkt").exists()


def test_thu_quyen_thi_het_thay(bang_mkt, nguoi_dung):
    """FR-3.4 — Chiều ngược lại: thu quyền thì không thấy nữa"""
    nguoi = nguoi_dung["staff_sale_1"]
    quyen = grant_service.grant(
        table=bang_mkt, user=nguoi, action=GrantAction.VIEW,
        actor=nguoi_dung["manager_mkt"],
    )
    grant_service.clear_cache(nguoi)
    assert TableDef.objects.in_scope(nguoi).filter(code="bc_mkt").exists()

    grant_service.revoke(quyen, actor=nguoi_dung["manager_mkt"])
    grant_service.clear_cache(nguoi)
    assert not TableDef.objects.in_scope(nguoi).filter(code="bc_mkt").exists()


def test_cap_quyen_thi_thay_ban_ghi_trong_bang(bang_mkt, nguoi_dung):
    """FR-3.4 — Được cấp quyền xem bảng thì thấy cả bản ghi trong bảng đó"""
    from forms_builder.services import record_service

    record_service.create_record(
        bang_mkt, {"marketer": "Của Marketing"}, actor=nguoi_dung["staff_mkt"])
    nguoi = nguoi_dung["staff_sale_1"]
    assert not DataRecord.objects.in_scope(nguoi).exists()

    grant_service.grant(
        table=bang_mkt, user=nguoi, action=GrantAction.VIEW,
        actor=nguoi_dung["manager_mkt"],
    )
    grant_service.clear_cache(nguoi)
    assert DataRecord.objects.in_scope(nguoi).count() == 1


def test_cap_quyen_cho_ca_team(bang_mkt, teams, nguoi_dung):
    """FR-8.4 — Cấp quyền cho một team thì mọi người trong team đều thấy"""
    nguoi = nguoi_dung["staff_sale_1"]
    grant_service.grant(
        table=bang_mkt, team=teams["sale1"], action=GrantAction.VIEW,
        actor=nguoi_dung["manager_mkt"],
    )
    grant_service.clear_cache(nguoi)
    assert TableDef.objects.in_scope(nguoi).filter(code="bc_mkt").exists()

    # Người ở team khác thì không
    khac = nguoi_dung["staff_sale_2"]
    grant_service.clear_cache(khac)
    assert not TableDef.objects.in_scope(khac).filter(code="bc_mkt").exists()


def test_cap_quyen_dien_bieu_mau(client, bieu_mau, nguoi_dung):
    """AC-8.4 — Cấp quyền điền thì người ngoài bộ phận điền được"""
    nguoi = nguoi_dung["staff_sale_1"]
    grant_service.grant(
        form=bieu_mau, user=nguoi, action=GrantAction.FILL,
        actor=nguoi_dung["manager_mkt"],
    )
    client.force_login(nguoi)
    assert client.get(f"/bieu-mau/{bieu_mau.code}/dien/").status_code == 200


def test_cap_quyen_lam_mat_hieu_luc_phien_dang_mo(client, bang_mkt, nguoi_dung):
    """AC-1.6 — Đổi quyền thì phiên đang mở mất hiệu lực ngay — P4, FR-1.5

    Cơ chế `session_epoch` chỉ tự tăng khi đổi cột trên chính hồ sơ nhân sự.
    Quyền cấp thêm nằm ở bảng khác nên phải gọi tay; bài này chặn việc quên.
    """
    # Đăng nhập thật, không dùng force_login: mốc phiên do màn hình đăng nhập
    # ghi vào, force_login bỏ qua bước đó nên không kiểm được P4
    nguoi = nguoi_dung["staff_sale_1"]
    client.post("/dang-nhap/", {
        "username": "staff_sale_1", "password": "matkhau-kiem-thu-1",
    })
    assert client.get("/bang/").status_code == 200

    grant_service.grant(
        table=bang_mkt, user=nguoi, action=GrantAction.VIEW,
        actor=nguoi_dung["manager_mkt"],
    )
    kq = client.get("/bang/")
    assert kq.status_code == 302
    assert "doi_quyen=1" in kq["Location"]


def test_cap_va_thu_quyen_deu_ghi_nhat_ky(bang_mkt, nguoi_dung):
    """AC-9.2 — Cấp và thu quyền đều sinh một dòng nhật ký"""
    truoc = AuditLog.objects.filter(action=AuditAction.PERMISSION).count()
    quyen = grant_service.grant(
        table=bang_mkt, user=nguoi_dung["staff_sale_1"], action=GrantAction.VIEW,
        actor=nguoi_dung["manager_mkt"],
    )
    grant_service.revoke(quyen, actor=nguoi_dung["manager_mkt"])

    ds = AuditLog.objects.filter(action=AuditAction.PERMISSION)
    assert ds.count() == truoc + 2
    assert "Thu quyền" in ds.latest("created_at").detail


def test_khong_cap_quyen_dien_cho_mot_bang(bang_mkt, nguoi_dung):
    """Bảng chỉ cấp được quyền xem hoặc sửa, không có quyền điền"""
    from django.core.exceptions import ValidationError

    with pytest.raises(ValidationError):
        grant_service.grant(
            table=bang_mkt, user=nguoi_dung["staff_sale_1"],
            action=GrantAction.FILL, actor=nguoi_dung["manager_mkt"],
        )


def test_phai_chon_dung_mot_ben_nhan_quyen(bang_mkt, teams, nguoi_dung):
    """Ràng buộc: cấp cho đúng một người hoặc một team, không cả hai"""
    from django.core.exceptions import ValidationError

    with pytest.raises(ValidationError):
        grant_service.grant(
            table=bang_mkt, user=nguoi_dung["staff_sale_1"], team=teams["sale1"],
            action=GrantAction.VIEW, actor=nguoi_dung["manager_mkt"],
        )


# ══ Sửa ô theo quyền cấp riêng — gỡ K12 ════════════════════════════

def test_cap_quyen_sua_thi_sua_duoc_o(client, bang_mkt, nguoi_dung):
    """AC-7.4 — Được cấp quyền sửa thì sửa được ô, dù ngoài bộ phận"""
    from forms_builder.services import record_service

    bg = record_service.create_record(
        bang_mkt, {"marketer": "Tên cũ"}, actor=nguoi_dung["staff_mkt"])
    nguoi = nguoi_dung["staff_sale_1"]

    grant_service.grant(table=bang_mkt, user=nguoi, action=GrantAction.VIEW,
                        actor=nguoi_dung["manager_mkt"])
    grant_service.grant(table=bang_mkt, user=nguoi, action=GrantAction.EDIT,
                        actor=nguoi_dung["manager_mkt"])

    client.force_login(nguoi)
    kq = client.post(f"/bang/bc_mkt/o/{bg.pk}/marketer/", {"gia_tri": "Tên mới"})
    assert kq.status_code == 200
    bg.refresh_from_db()
    assert bg.data["marketer"] == "Tên mới"


def test_chi_cap_quyen_xem_thi_khong_sua_duoc_o(client, bang_mkt, nguoi_dung):
    """AC-7.4 — Chiều bị từ chối: chỉ được xem thì không sửa được ô"""
    from forms_builder.services import record_service

    bg = record_service.create_record(
        bang_mkt, {"marketer": "Tên cũ"}, actor=nguoi_dung["staff_mkt"])
    nguoi = nguoi_dung["staff_sale_1"]
    grant_service.grant(table=bang_mkt, user=nguoi, action=GrantAction.VIEW,
                        actor=nguoi_dung["manager_mkt"])

    client.force_login(nguoi)
    kq = client.post(f"/bang/bc_mkt/o/{bg.pk}/marketer/", {"gia_tri": "Tên mới"})
    assert kq.status_code == 403

    bg.refresh_from_db()
    assert bg.data["marketer"] == "Tên cũ"


# ══ Hiệu năng ══════════════════════════════════════════════════════

def test_man_hinh_bieu_mau_khong_qua_muoi_lenh_truy_van(
        client, bieu_mau, nguoi_dung, django_assert_max_num_queries):
    """AC-10.2 — Màn hình biểu mẫu chạy không quá 10 lệnh truy vấn"""
    client.force_login(nguoi_dung["manager_mkt"])
    client.get("/bieu-mau/")               # lượt đầu ghi mốc phiên
    with django_assert_max_num_queries(10):
        assert client.get("/bieu-mau/").status_code == 200


def test_lay_cap_quyen_chi_mot_lenh_truy_van(bang_mkt, nguoi_dung,
                                             django_assert_max_num_queries):
    """Quy tắc Q2 — Tập cấp quyền lấy một lần rồi giữ lại, không lấy lại mỗi lần

    Không đệm thì mỗi queryset có phạm vi là thêm một lệnh, và AC-10.2 sẽ đỏ.
    """
    nguoi = nguoi_dung["staff_sale_1"]
    grant_service.grant(table=bang_mkt, user=nguoi, action=GrantAction.VIEW,
                        actor=nguoi_dung["manager_mkt"])
    grant_service.clear_cache(nguoi)

    with django_assert_max_num_queries(1):
        for _ in range(5):
            grant_service.granted_table_ids(nguoi)
