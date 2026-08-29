"""Kiểm thử màn hình bảng dữ liệu — phần người dùng thật sự chạm vào.

`test_bang_dong.py` kiểm mô hình dữ liệu. Tệp này kiểm đường đi qua HTTP: ai
vào được màn hình nào, ai sửa được ô nào, và gọi thẳng đường dẫn có bị chặn
không (FR-3.6).

Mỗi bài phân quyền kiểm **cả hai chiều** — chỉ kiểm chiều được phép thì không
phát hiện được rò rỉ dữ liệu.
"""
from decimal import Decimal

import pytest

from core.constants import AuditAction
from core.models import AuditLog
from forms_builder.meaning import FieldType, Meaning
from forms_builder.models import ColumnDef, ComputeOp, DataRecord, TableDef
from forms_builder.services import record_service, table_service

pytestmark = pytest.mark.django_db


@pytest.fixture
def bang_sale(departments, nguoi_dung):
    """Bảng của bộ phận Sale, có cột mang nhãn và một cột tính sẵn."""
    bang = TableDef.objects.create(
        name="Đơn hàng Sale", code="don_sale",
        department=departments["sale"], created_by=nguoi_dung["manager_sale"],
    )
    cot = [
        ("Ngày", "ngay", FieldType.DATE, Meaning.DATE),
        ("Khách hàng", "khach", FieldType.TEXT, Meaning.CUSTOMER),
        ("Người bán", "nguoi_ban", FieldType.TEXT, Meaning.SELLER),
        ("Doanh thu", "doanh_thu", FieldType.MONEY, Meaning.REVENUE),
        ("Số lượng", "so_luong", FieldType.INTEGER, ""),
    ]
    for i, (ten, ma, kieu, nhan) in enumerate(cot):
        ColumnDef.objects.create(
            table=bang, name=ten, code=ma, field_type=kieu, meaning=nhan, order=i,
        )
    ColumnDef.objects.create(
        table=bang, name="Giá đơn vị", code="gia_dv", field_type=FieldType.MONEY,
        order=5, is_computed=True, compute_op=ComputeOp.DIVIDE,
        compute_left="doanh_thu", compute_right="so_luong", compute_decimals=2,
    )
    return bang


@pytest.fixture
def bang_mkt_khac(departments, nguoi_dung):
    """Bảng của bộ phận Marketing — dùng để kiểm chiều bị từ chối."""
    return TableDef.objects.create(
        name="Báo cáo Marketing", code="bc_mkt",
        department=departments["mkt"], created_by=nguoi_dung["manager_mkt"],
    )


def _dong(bang, nguoi, **gia_tri):
    return record_service.create_record(bang, gia_tri, actor=nguoi)


# ══ Phạm vi quyền trên định nghĩa bảng ═════════════════════════════

def test_moi_cap_bac_thay_bang_cua_bo_phan_minh(bang_sale, bang_mkt_khac, nguoi_dung):
    """AC-3.5 — Người bộ phận này không thấy bảng của bộ phận khác"""
    for ma in ("staff_sale_1", "leader_sale_1", "manager_sale"):
        thay = set(TableDef.objects.in_scope(nguoi_dung[ma]).values_list("code", flat=True))
        assert "don_sale" in thay, f"{ma} phải thấy bảng bộ phận mình"
        assert "bc_mkt" not in thay, f"{ma} không được thấy bảng bộ phận khác"


def test_leader_thay_bang_du_khong_phai_nguoi_tao(bang_sale, nguoi_dung):
    """AC-3.2 — Leader thấy bảng của bộ phận mình, dù bảng do Manager tạo

    Bài này đỏ nếu `TableDef` quay lại dùng phạm vi theo người tạo: Leader
    không được tạo bảng nên sẽ thấy danh sách rỗng và không vào được đâu.
    """
    assert bang_sale.created_by_id != nguoi_dung["leader_sale_1"].pk
    thay = TableDef.objects.in_scope(nguoi_dung["leader_sale_1"])
    assert list(thay.values_list("code", flat=True)) == ["don_sale"]


def test_admin_thay_bang_cua_moi_bo_phan(bang_sale, bang_mkt_khac, nguoi_dung):
    """AC-3.8 — Quản trị viên thấy bảng của mọi bộ phận"""
    thay = set(TableDef.objects.in_scope(nguoi_dung["admin"]).values_list("code", flat=True))
    assert {"don_sale", "bc_mkt"} <= thay


# ══ Màn hình danh sách bảng ════════════════════════════════════════

def test_staff_vao_duoc_danh_sach_bang(client, bang_sale, nguoi_dung):
    """AC-7.1 — Màn hình danh sách bảng có phân trang, mặc định 25 dòng"""
    client.force_login(nguoi_dung["staff_sale_1"])
    kq = client.get("/bang/")
    assert kq.status_code == 200
    assert kq.context["page_obj"].paginator.per_page == 25
    assert "Đơn hàng Sale" in kq.content.decode()


def test_bang_bo_phan_khac_khong_hien_trong_danh_sach(client, bang_sale, bang_mkt_khac, nguoi_dung):
    """AC-3.5 — Bảng của bộ phận khác không xuất hiện trên màn hình danh sách"""
    client.force_login(nguoi_dung["staff_sale_1"])
    noi_dung = client.get("/bang/").content.decode()
    assert "Đơn hàng Sale" in noi_dung
    assert "Báo cáo Marketing" not in noi_dung


def test_staff_khong_tao_duoc_bang(client, nguoi_dung):
    """AC-3.7 — Staff gọi thẳng đường dẫn tạo bảng vẫn bị từ chối"""
    client.force_login(nguoi_dung["staff_sale_1"])
    assert client.get("/bang/moi/").status_code == 403


def test_manager_tao_duoc_bang(client, nguoi_dung):
    """AC-8.1 — Manager tạo được bảng mới mà không cần sửa mã nguồn"""
    client.force_login(nguoi_dung["manager_sale"])
    kq = client.post("/bang/moi/", {
        "name": "Bảng thử", "code": "bang_thu", "description": "",
    })
    assert kq.status_code == 302
    bang = TableDef.objects.get(code="bang_thu")
    assert bang.department == nguoi_dung["manager_sale"].profile.department


def test_gọi_thang_bang_bo_phan_khac_bi_chan(client, bang_mkt_khac, nguoi_dung):
    """AC-3.7 — Gọi thẳng đường dẫn của bảng bộ phận khác vẫn bị chặn"""
    client.force_login(nguoi_dung["staff_sale_1"])
    assert client.get("/bang/bc_mkt/").status_code == 404


# ══ Màn hình bảng dữ liệu ══════════════════════════════════════════

def test_staff_chi_thay_dong_cua_minh(client, bang_sale, nguoi_dung):
    """AC-3.1 — Staff chỉ thấy bản ghi do chính mình tạo"""
    _dong(bang_sale, nguoi_dung["staff_sale_1"], khach="Khách của tôi", so_luong=1)
    _dong(bang_sale, nguoi_dung["staff_sale_2"], khach="Khách người khác", so_luong=1)

    client.force_login(nguoi_dung["staff_sale_1"])
    noi_dung = client.get("/bang/don_sale/").content.decode()
    assert "Khách của tôi" in noi_dung
    assert "Khách người khác" not in noi_dung


def test_manager_thay_moi_dong_trong_bo_phan(client, bang_sale, nguoi_dung):
    """AC-3.4 — Manager thấy toàn bộ bản ghi của bộ phận mình"""
    _dong(bang_sale, nguoi_dung["staff_sale_1"], khach="Khách một", so_luong=1)
    _dong(bang_sale, nguoi_dung["staff_sale_2"], khach="Khách hai", so_luong=1)

    client.force_login(nguoi_dung["manager_sale"])
    noi_dung = client.get("/bang/don_sale/").content.decode()
    assert "Khách một" in noi_dung and "Khách hai" in noi_dung


def test_loc_theo_cot_tra_ve_dung_so_ban_ghi(client, bang_sale, nguoi_dung):
    """AC-7.2 — Lọc theo cột trả về đúng số bản ghi"""
    _dong(bang_sale, nguoi_dung["manager_sale"], khach="Anh Minh", so_luong=1)
    _dong(bang_sale, nguoi_dung["manager_sale"], khach="Chị Lan", so_luong=1)

    client.force_login(nguoi_dung["manager_sale"])
    kq = client.get("/bang/don_sale/", {"f_khach": "Anh Minh"})
    assert kq.context["page_obj"].paginator.count == 1


def test_sap_xep_theo_cot_ca_hai_chieu(client, bang_sale, nguoi_dung):
    """AC-7.3 — Sắp xếp theo cột cho ra thứ tự đúng, cả tăng và giảm"""
    for tien in ("300", "100", "200"):
        _dong(bang_sale, nguoi_dung["manager_sale"], doanh_thu=tien, so_luong=1)

    client.force_login(nguoi_dung["manager_sale"])
    tang = client.get("/bang/don_sale/", {"sap": "doanh_thu"})
    assert [bg.val_revenue for bg in tang.context["page_obj"]] == [
        Decimal("100.00"), Decimal("200.00"), Decimal("300.00")]

    giam = client.get("/bang/don_sale/", {"sap": "doanh_thu", "chieu": "giam"})
    assert [bg.val_revenue for bg in giam.context["page_obj"]] == [
        Decimal("300.00"), Decimal("200.00"), Decimal("100.00")]


def test_chi_cot_co_chi_muc_moi_duoc_loc(client, bang_sale, nguoi_dung):
    """Quy tắc 9 — Thanh lọc chỉ hiện cột có chỉ mục"""
    client.force_login(nguoi_dung["manager_sale"])
    kq = client.get("/bang/don_sale/")
    ma_loc = {o["cot"].code for o in kq.context["cac_cot_loc"]}
    assert "khach" in ma_loc          # mang nhãn Khách hàng, có cột tách
    assert "so_luong" not in ma_loc   # không mang nhãn, nằm trong JSON


def test_man_hinh_bang_khong_qua_muoi_lenh_truy_van(
        client, bang_sale, nguoi_dung, django_assert_max_num_queries):
    """AC-10.2 — Màn hình danh sách chạy không quá 10 lệnh truy vấn"""
    for i in range(30):
        _dong(bang_sale, nguoi_dung["manager_sale"], khach=f"Khách {i}", so_luong=1)

    client.force_login(nguoi_dung["manager_sale"])
    client.get("/bang/don_sale/")          # lượt đầu ghi mốc phiên
    with django_assert_max_num_queries(10):
        assert client.get("/bang/don_sale/").status_code == 200


# ══ Sửa từng ô — FR-7.4 ════════════════════════════════════════════

def _duong_dan_o(ban_ghi, ma_cot):
    return f"/bang/{ban_ghi.table.code}/o/{ban_ghi.pk}/{ma_cot}/"


def test_manager_sua_duoc_o(client, bang_sale, nguoi_dung):
    """AC-7.4 — Người có quyền sửa được ô ngay trên bảng"""
    bg = _dong(bang_sale, nguoi_dung["manager_sale"], khach="Tên cũ", so_luong=1)

    client.force_login(nguoi_dung["manager_sale"])
    kq = client.post(_duong_dan_o(bg, "khach"), {"gia_tri": "Tên mới"})
    assert kq.status_code == 200

    bg.refresh_from_db()
    assert bg.data["khach"] == "Tên mới"
    assert bg.val_customer == "Tên mới"      # cột tách phải đổi theo


def test_staff_khong_sua_duoc_o_cua_nguoi_khac(client, bang_sale, nguoi_dung):
    """AC-7.4 — Không có quyền thì không sửa được ô, kể cả gọi thẳng đường dẫn"""
    bg = _dong(bang_sale, nguoi_dung["staff_sale_2"], khach="Của người khác", so_luong=1)

    client.force_login(nguoi_dung["staff_sale_1"])
    kq = client.post(_duong_dan_o(bg, "khach"), {"gia_tri": "Đã đổi"})
    assert kq.status_code == 404             # ngoài phạm vi, không thấy bản ghi

    bg.refresh_from_db()
    assert bg.data["khach"] == "Của người khác"


def test_staff_sua_duoc_dong_cua_chinh_minh(client, bang_sale, nguoi_dung):
    """AC-7.4 — Chiều được phép: Staff sửa được dòng do chính mình tạo"""
    bg = _dong(bang_sale, nguoi_dung["staff_sale_1"], khach="Của tôi", so_luong=1)

    client.force_login(nguoi_dung["staff_sale_1"])
    assert client.post(_duong_dan_o(bg, "khach"), {"gia_tri": "Của tôi, đã sửa"}).status_code == 200
    bg.refresh_from_db()
    assert bg.data["khach"] == "Của tôi, đã sửa"


def test_khong_sua_duoc_cot_tinh_san(client, bang_sale, nguoi_dung):
    """ADR-006 — Cột tính sẵn không sửa tay được, kể cả gọi thẳng đường dẫn"""
    bg = _dong(bang_sale, nguoi_dung["manager_sale"], doanh_thu="1000", so_luong=4)
    assert bg.data["gia_dv"] == "250.00"

    client.force_login(nguoi_dung["manager_sale"])
    kq = client.post(_duong_dan_o(bg, "gia_dv"), {"gia_tri": "999"})
    assert kq.status_code == 400

    bg.refresh_from_db()
    assert bg.data["gia_dv"] == "250.00"


def test_sua_o_sinh_mot_dong_nhat_ky(client, bang_sale, nguoi_dung):
    """AC-9.2 — Mọi thao tác thay đổi dữ liệu sinh một dòng nhật ký"""
    bg = _dong(bang_sale, nguoi_dung["manager_sale"], khach="Trước", so_luong=1)
    truoc = AuditLog.objects.filter(action=AuditAction.UPDATE).count()

    client.force_login(nguoi_dung["manager_sale"])
    client.post(_duong_dan_o(bg, "khach"), {"gia_tri": "Sau"})

    ds = AuditLog.objects.filter(action=AuditAction.UPDATE)
    assert ds.count() == truoc + 1
    assert "Trước → Sau" in ds.latest("created_at").detail


def test_sua_o_gia_tri_khong_doi_thi_khong_ghi_nhat_ky(client, bang_sale, nguoi_dung):
    """BR-5 — Không đổi gì thì không ghi nhật ký, tránh nhật ký rác"""
    bg = _dong(bang_sale, nguoi_dung["manager_sale"], khach="Y nguyên", so_luong=1)
    truoc = AuditLog.objects.filter(action=AuditAction.UPDATE).count()

    client.force_login(nguoi_dung["manager_sale"])
    client.post(_duong_dan_o(bg, "khach"), {"gia_tri": "Y nguyên"})

    assert AuditLog.objects.filter(action=AuditAction.UPDATE).count() == truoc


def test_sua_o_cap_nhat_luon_cot_tinh_san(client, bang_sale, nguoi_dung):
    """AC-7.10 — Sửa cột nguồn thì cột tính sẵn đổi theo ngay"""
    bg = _dong(bang_sale, nguoi_dung["manager_sale"], doanh_thu="1000", so_luong=4)

    client.force_login(nguoi_dung["manager_sale"])
    client.post(_duong_dan_o(bg, "so_luong"), {"gia_tri": "5"})

    bg.refresh_from_db()
    assert bg.data["gia_dv"] == "200.00"


def test_gia_tri_sai_kieu_bi_tu_choi(client, bang_sale, nguoi_dung):
    """NFR-6 — Gõ sai kiểu thì báo lỗi tiếng Việt, không hiện trang trắng"""
    bg = _dong(bang_sale, nguoi_dung["manager_sale"], so_luong=1)

    client.force_login(nguoi_dung["manager_sale"])
    kq = client.post(_duong_dan_o(bg, "so_luong"), {"gia_tri": "không phải số"})
    assert kq.status_code == 400
    assert "Số nguyên" in kq.content.decode()


# ══ Đổi công thức thì tính lại dữ liệu cũ — ADR-006 ════════════════

def test_doi_cong_thuc_thi_tinh_lai_ban_ghi_cu(bang_sale, nguoi_dung):
    """AC-7.12 — Đổi công thức thì bản ghi cũ được tính lại, không giữ số cũ"""
    bg = _dong(bang_sale, nguoi_dung["manager_sale"], doanh_thu="1000", so_luong=4)
    assert bg.data["gia_dv"] == "250.00"

    cot = bang_sale.columns.get(code="gia_dv")
    table_service.update_column(
        cot, {"compute_op": ComputeOp.MULTIPLY}, actor=nguoi_dung["manager_sale"])

    bg.refresh_from_db()
    assert bg.data["gia_dv"] == "4000.00"


def test_bo_cot_mang_nhan_thi_cot_tach_duoc_don_sach(bang_sale, nguoi_dung):
    """ADR-001 — Bỏ cột mang nhãn thì cột tách phải trả về rỗng

    Không dọn thì báo cáo tổng hợp vẫn cộng số của cột đã bị gỡ.
    """
    bg = _dong(bang_sale, nguoi_dung["manager_sale"], doanh_thu="500", so_luong=1)
    assert bg.val_revenue == Decimal("500.00")

    table_service.remove_column(
        bang_sale.columns.get(code="doanh_thu"), actor=nguoi_dung["manager_sale"])

    bg.refresh_from_db()
    assert bg.val_revenue is None


# ══ Xoá bản ghi ════════════════════════════════════════════════════

def test_xoa_dong_la_danh_dau(bang_sale, nguoi_dung):
    """AC-9.1 — Xoá dòng thì bản ghi vẫn còn trong cơ sở dữ liệu"""
    bg = _dong(bang_sale, nguoi_dung["manager_sale"], khach="Sắp xoá", so_luong=1)
    record_service.delete_record(bg, actor=nguoi_dung["manager_sale"])

    assert not DataRecord.objects.filter(pk=bg.pk).exists()
    con = DataRecord.all_objects.get(pk=bg.pk)
    assert con.deleted_at is not None
    assert con.deleted_by == nguoi_dung["manager_sale"]


# ══ Ma trận phân quyền ═════════════════════════════════════════════

def test_manager_xem_duoc_ma_tran_quyen(client, nguoi_dung):
    """AC-3.6 — Manager vào được màn hình ma trận phân quyền"""
    client.force_login(nguoi_dung["manager_sale"])
    assert client.get("/ma-tran-quyen/").status_code == 200


def test_staff_khong_xem_duoc_ma_tran_quyen(client, nguoi_dung):
    """AC-3.7 — Staff gọi thẳng đường dẫn ma trận phân quyền vẫn bị từ chối"""
    client.force_login(nguoi_dung["staff_sale_1"])
    assert client.get("/ma-tran-quyen/").status_code == 403


def test_ma_tran_sinh_dung_theo_thanh_dieu_huong(client, nguoi_dung):
    """Ma trận sinh từ mã nguồn, không chép tay — sửa quyền là bảng đổi theo"""
    from core.navigation import NAVIGATION

    client.force_login(nguoi_dung["admin"])
    hang = client.get("/ma-tran-quyen/").context["cac_hang"]
    so_muc = sum(len(nhom.items) for nhom in NAVIGATION)
    assert len([h for h in hang if not h["la_nhom"]]) == so_muc
