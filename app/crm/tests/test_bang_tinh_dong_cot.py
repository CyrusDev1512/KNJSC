"""Menu chuột phải của Bảng tính: xoá và khôi phục dòng, chèn và bỏ cột,
mốc mới nhất để tự cập nhật (`docs/04` AC-11.21, AC-11.22, AC-11.26 — ADR-011).

Mỗi đường dẫn kiểm cả ba cấp bậc, cả chiều cho phép lẫn chiều từ chối.
"""
import itertools
import pytest
from django.test import override_settings

from core.constants import AuditAction
from core.models import AuditLog
from forms_builder.meaning import FieldType, Meaning
from forms_builder.models import ColumnDef, ComputeOp, DataRecord, TableDef
from forms_builder.services import record_service, table_service
from orders.services import dispatch_service

pytestmark = pytest.mark.django_db

SUA_DUOC = override_settings(GRID_ONLY_TABLES=set())


@pytest.fixture
def bang_sale(departments, nguoi_dung):
    bang = TableDef.objects.create(
        name="Đơn hàng Sale", code="don_sale",
        department=departments["sale"], created_by=nguoi_dung["manager_sale"],
        # KN CRM chỉ phục vụ bảng vận đơn (ADR-040) — bảng đạo cụ mang workflow
        # để lưới phục vụ; cột tuỳ ý nên profile vận đơn không đổi hành vi bài
        workflow="waybill",
    )
    cot = [
        ("Ngày", "ngay", FieldType.DATE, Meaning.DATE),
        ("Khách hàng", "khach", FieldType.TEXT, Meaning.CUSTOMER),
        ("Doanh thu", "doanh_thu", FieldType.MONEY, Meaning.REVENUE),
        ("Số lượng", "so_luong", FieldType.INTEGER, ""),
    ]
    for i, (ten, ma, kieu, nhan) in enumerate(cot, start=1):
        ColumnDef.objects.create(table=bang, name=ten, code=ma, field_type=kieu, meaning=nhan,
                                 order=i, is_key=(ma == "khach"))
    ColumnDef.objects.create(
        table=bang, name="Giá đơn vị", code="gia_dv", field_type=FieldType.MONEY,
        order=5, is_computed=True, compute_op=ComputeOp.DIVIDE,
        compute_left="doanh_thu", compute_right="so_luong", compute_decimals=2,
    )
    return bang


@pytest.fixture
def bang_vd(departments, nguoi_dung):
    return dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])


#: Mã đơn mỗi dòng một số: bảng vận đơn không nhận hai dòng sống cùng mã (ràng buộc 06.10.2026)
_MA = itertools.count(1)


def _dong(bang, nguoi, **gia_tri):
    # Bảng vận đơn duy nhất mang profile (ADR-036): đủ cột bắt buộc, tiền theo quốc gia.
    mac_dinh = {"ma_don": f"DH-{next(_MA)}-{gia_tri.get('ten_khach', 'x')}", "ngay": "2026-08-01",
                "ten_khach": "Khách", "so_dien_thoai": "0900", "quoc_gia": "Hoa Kỳ", "loai_tien": "USD"}
    return record_service.create_record(bang, {**mac_dinh, **gia_tri}, actor=nguoi)


# ══ Xoá và khôi phục dòng — AC-11.21 ═══════════════════════════════

def test_xoa_dong_la_xoa_mem_va_khoi_phuc_duoc(client,bang_sale,nguoi_dung):
    d=_dong(bang_sale,nguoi_dung['staff_sale_1'],khach='A')
    client.force_login(nguoi_dung['manager_sale'])
    for action in ['xoa-dong','khoi-phuc-dong']:
        assert client.post(f'/bang-tinh/{bang_sale.code}/{action}/',{'dong':[d.pk]}).status_code==409
    d.refresh_from_db();assert d.deleted_at is None


def test_phan_quyen_xoa_dong_ba_cap_bac(client,bang_sale,nguoi_dung):
    d=_dong(bang_sale,nguoi_dung['staff_sale_1'],khach='A')
    client.force_login(nguoi_dung['manager_sale'])
    for action in ['xoa-dong','khoi-phuc-dong']:
        assert client.post(f'/bang-tinh/{bang_sale.code}/{action}/',{'dong':[d.pk]}).status_code==409
    d.refresh_from_db();assert d.deleted_at is None


# ══ Chèn và bỏ cột — AC-11.22 ══════════════════════════════════════

def test_manager_chen_cot_canh_cot_dang_chon(client, bang_sale, nguoi_dung):
    """AC-11.22 — Manager của bộ phận sở hữu chèn N cột chữ ngắn bên trái hoặc bên phải cột đang chọn; thứ tự cột đánh lại theo vị trí mới; tên và mã cột mới không trùng; có nhật ký"""
    client.force_login(nguoi_dung["manager_sale"])
    kq = client.post(f"/bang-tinh/{bang_sale.code}/them-cot/", {"canh": "khach", "ben": "phai", "so": 2})
    assert kq.status_code == 200 and kq.json()["da_them"] == ["cot_moi_1", "cot_moi_2"]
    thu_tu = list(bang_sale.columns.order_by("order", "id").values_list("code", flat=True))
    assert thu_tu == ["ngay", "khach", "cot_moi_1", "cot_moi_2", "doanh_thu", "so_luong", "gia_dv"]
    assert bang_sale.columns.get(code="cot_moi_1").name == "Cột mới 1"
    kq = client.post(f"/bang-tinh/{bang_sale.code}/them-cot/", {"canh": "ngay", "ben": "trai", "so": 1})
    assert kq.status_code == 200 and kq.json()["da_them"] == ["cot_moi_3"]
    assert list(bang_sale.columns.order_by("order", "id").values_list("code", flat=True))[0] == "cot_moi_3"
    kq = client.post(f"/bang-tinh/{bang_sale.code}/them-cot/", {"so": 1})           # không cột cạnh: chèn cuối
    assert kq.status_code == 200
    assert list(bang_sale.columns.order_by("order", "id").values_list("code", flat=True))[-1] == "cot_moi_4"
    assert client.post(f"/bang-tinh/{bang_sale.code}/them-cot/", {"canh": "khong_co", "so": 1}).status_code == 400
    assert AuditLog.objects.filter(detail__startswith="Chèn cột").count() == 4
    kq = client.get(f"/bang-tinh/{bang_sale.code}/")
    assert kq.status_code == 200
    assert 'cot_moi_1' in [c['code'] for c in client.get(f'/bang-tinh/{bang_sale.code}/du-lieu/').json()['columns']]


def test_bo_cot_giu_gia_tri_va_tu_choi_cot_khoa_cot_tinh(client, bang_sale, bang_vd, nguoi_dung):
    """AC-11.22 — Bỏ cột xoá định nghĩa cột nhưng giữ giá trị trong bản ghi (BR-4); cột khoá, cột là vế của cột tính sẵn và cột hệ thống của bảng vận đơn bị từ chối"""
    nv = nguoi_dung["manager_sale"]
    # Cột xoá thử phải KHÔNG trùng mã chuẩn vận đơn: bảng đạo cụ mang workflow
    # (ADR-040) nên "ngay"/"so_luong" được profile giữ lại như bảng thật
    ColumnDef.objects.create(table=bang_sale, name="Ghi chú thêm", code="ghi_chu_them",
                             field_type=FieldType.TEXT, order=9)
    d = _dong(bang_sale, nv, khach="A", doanh_thu="10", so_luong="2",
              ngay="2026-01-01", ghi_chu_them="giữ lại")
    client.force_login(nv)
    kq = client.post(f"/bang-tinh/{bang_sale.code}/xoa-cot/", {"cot": ["ghi_chu_them"]})
    assert kq.status_code == 200 and kq.json()["da_bo"] == ["ghi_chu_them"]
    assert not bang_sale.columns.filter(code="ghi_chu_them").exists()
    d.refresh_from_db()
    assert d.data["ghi_chu_them"] == "giữ lại"                               # giá trị vẫn còn
    kq = client.post(f"/bang-tinh/{bang_sale.code}/xoa-cot/", {"cot": ["ngay"]})
    assert kq.status_code == 400 and "ận đơn" in kq.content.decode()         # mã chuẩn bị giữ
    assert client.post(f"/bang-tinh/{bang_sale.code}/xoa-cot/", {"cot": ["khach"]}).status_code == 400
    kq = client.post(f"/bang-tinh/{bang_sale.code}/xoa-cot/", {"cot": ["doanh_thu"]})
    assert kq.status_code == 400 and "cột tính sẵn" in kq.content.decode()
    assert client.post(f"/bang-tinh/{bang_sale.code}/xoa-cot/", {"cot": ["khong_co"]}).status_code == 400
    assert client.post(f"/bang-tinh/{bang_sale.code}/xoa-cot/", {}).status_code == 400
    assert bang_sale.columns.count() == 5
    client.force_login(nguoi_dung["admin"])
    kq = client.post(f"/bang-tinh/{bang_vd.code}/xoa-cot/", {"cot": ["ten_khach"]})
    assert kq.status_code == 400 and "ận đơn" in kq.content.decode()


def test_phan_quyen_chen_bo_cot_ba_cap_bac(client, bang_sale, nguoi_dung):
    """AC-11.22 — Staff không chèn hay bỏ cột (403 có nhật ký); Manager bộ phận khác 404; Leader, Manager của bộ phận sở hữu và Admin thì được (ADR-015)"""
    truoc = AuditLog.objects.filter(action=AuditAction.DENIED).count()
    for ai in ("staff_sale_1",):
        client.force_login(nguoi_dung[ai])
        assert client.post(f"/bang-tinh/{bang_sale.code}/them-cot/", {"canh": "khach", "so": 1}).status_code == 403
        assert client.post(f"/bang-tinh/{bang_sale.code}/xoa-cot/", {"cot": ["so_luong"]}).status_code == 403
    assert AuditLog.objects.filter(action=AuditAction.DENIED).count() == truoc + 2
    client.force_login(nguoi_dung["leader_sale_1"])
    assert client.post(f"/bang-tinh/{bang_sale.code}/them-cot/", {"canh": "khach", "so": 1}).status_code == 200
    assert bang_sale.columns.filter(code="cot_moi_1").exists()
    assert client.post(f"/bang-tinh/{bang_sale.code}/xoa-cot/", {"cot": ["cot_moi_1"]}).status_code == 200
    assert not bang_sale.columns.filter(code="cot_moi_1").exists()
    client.force_login(nguoi_dung["manager_mkt"])
    assert client.post(f"/bang-tinh/{bang_sale.code}/them-cot/", {"so": 1}).status_code == 404
    client.force_login(nguoi_dung["admin"])
    assert client.post(f"/bang-tinh/{bang_sale.code}/them-cot/", {"canh": "khach", "so": 1}).status_code == 200
    assert bang_sale.columns.filter(code="cot_moi_1").exists()
    assert client.post(f"/bang-tinh/{bang_sale.code}/xoa-cot/", {"cot": ["cot_moi_1"]}).status_code == 200
    assert not bang_sale.columns.filter(code="cot_moi_1").exists()


def test_insert_columns_dich_vu(bang_sale, nguoi_dung):
    """AC-11.22 — Dịch vụ `insert_columns` đánh lại `order` liên tục và không đụng cột đã có; `removable_reason` nêu lý do giữ cột"""
    moi = table_service.insert_columns(bang_sale, count=2, anchor="doanh_thu", after=False, actor=nguoi_dung["manager_sale"])
    assert [c.code for c in moi] == ["cot_moi_1", "cot_moi_2"]
    assert list(bang_sale.columns.order_by("order").values_list("order", flat=True)) == [1, 2, 3, 4, 5, 6, 7]
    assert list(bang_sale.columns.order_by("order").values_list("code", flat=True))[2:4] == ["cot_moi_1", "cot_moi_2"]
    assert table_service.removable_reason(bang_sale.columns.get(code="khach"))
    assert "cột tính sẵn" in table_service.removable_reason(bang_sale.columns.get(code="doanh_thu"))
    assert table_service.removable_reason(bang_sale.columns.get(code="cot_moi_1")) == ""


# ══ Mốc mới nhất để tự cập nhật — AC-11.26 ════════════════════════

def test_moi_nhat_tra_moc_trong_pham_vi(client, bang_sale, nguoi_dung):
    """AC-11.26 — `moi-nhat/` trả mốc sửa gần nhất và số cột **trong phạm vi người xem**, không có dữ liệu, không đếm dòng; đổi ô, xoá mềm, thêm dòng đều đổi mốc; bộ phận khác 404; chưa đăng nhập thì chuyển về đăng nhập"""
    nv, nv_b = nguoi_dung["staff_sale_1"], nguoi_dung["staff_sale_1b"]
    d1 = _dong(bang_sale, nv, khach="A", doanh_thu="10", so_luong="1")
    _dong(bang_sale, nv_b, khach="B", doanh_thu="10", so_luong="1")
    client.force_login(nv)
    kq = client.get(f"/bang-tinh/{bang_sale.code}/moi-nhat/")
    assert kq.status_code == 200
    d = kq.json()
    assert "so" not in d and d["cot"] == 5 and d["moc"] and d["tinh_lai"] is None and "A" not in kq.content.decode()
    record_service.update_cell(d1, "khach", "A2", actor=nv)
    moc2 = client.get(f"/bang-tinh/{bang_sale.code}/moi-nhat/").json()["moc"]
    assert moc2 > d["moc"]
    client.force_login(nguoi_dung["manager_sale"])         # Manager thấy cả hai dòng
    moc_ql = client.get(f"/bang-tinh/{bang_sale.code}/moi-nhat/").json()["moc"]
    record_service.delete_record(d1, actor=nv)              # xoá mềm cũng đổi mốc (không cần đếm dòng)
    assert client.get(f"/bang-tinh/{bang_sale.code}/moi-nhat/").json()["moc"] > moc_ql
    client.force_login(nguoi_dung["staff_mkt"])
    assert client.get(f"/bang-tinh/{bang_sale.code}/moi-nhat/").status_code == 404
    client.logout()
    assert client.get(f"/bang-tinh/{bang_sale.code}/moi-nhat/").status_code == 302


# ══ Một luật bỏ cột ở mọi cửa — AC-11.22, TL-13 ═══════════════════

#: Ba cửa bỏ cột: (URLconf, kiểu) — lưới 8021 và màn Cột ở 8021 và 8020
CUA_BO_COT = [("knjsc.urls_bangtinh", "luoi"), ("knjsc.urls_bangtinh", "man_cot"), ("knjsc.urls", "man_cot")]
#: (bảng, mã cột, chữ phải có trong lời báo)
COT_KHONG_BO_DUOC = [
    ("bang_vd", "so_dien_thoai", "Cột chuẩn của Vận đơn"),
    ("bang_vd", "email", "tệp vận đơn thật"),
    ("bang_vd", "sl_thu", "tệp vận đơn thật"),
    ("bang_sale", "khach", "cột khoá"),
    ("bang_sale", "doanh_thu", "cột tính sẵn"),
    ("bang_sale", "ghi_chu_noi", "Biểu mẫu thử"),
]


@pytest.fixture
def cot_bo_thu(request, nguoi_dung, departments):
    """Bảng theo tham số, kèm cột `sl_thu` (bảng vận đơn) hoặc cột `ghi_chu_noi` đang nhận dữ liệu từ
    một biểu mẫu (bảng Sale) — chỉ dựng bảng cần cho ca đó."""
    from forms_builder.models import FieldDef
    from forms_builder.services import form_service

    def _dung(ten_bang):
        bang = request.getfixturevalue(ten_bang)
        if ten_bang == "bang_vd":
            ColumnDef.objects.create(table=bang, name="SL Thử", code="sl_thu", field_type=FieldType.INTEGER, order=99)
            return bang, nguoi_dung["admin"]
        ql = nguoi_dung["manager_sale"]
        cot = ColumnDef.objects.create(table=bang, name="Ghi chú nội bộ", code="ghi_chu_noi",
                                       field_type=FieldType.TEXT, order=9)
        bm = form_service.create_form(name="Biểu mẫu thử", code="bm_thu", department=departments["sale"],
                                      table=bang, actor=ql)
        truong = FieldDef.objects.create(name="Ghi chú", code="ghi_chu", field_type=FieldType.TEXT,
                                         department=departments["sale"])
        form_service.add_field(bm, truong, column=cot, actor=ql)
        return bang, ql
    return _dung


def _bo_cot(client, cua, bang, ma):
    if cua == "luoi":
        return client.post(f"/bang-tinh/{bang.code}/xoa-cot/", {"cot": [ma]})
    return client.post(f"/bang/{bang.code}/cot/{bang.columns.get(code=ma).pk}/bo/")


@SUA_DUOC
@pytest.mark.parametrize("bang_ten,ma,loi", COT_KHONG_BO_DUOC)
@pytest.mark.parametrize("urlconf,cua", CUA_BO_COT)
def test_bo_cot_cung_mot_luat_o_moi_cua(client, settings, cot_bo_thu, nguoi_dung, urlconf, cua, bang_ten, ma, loi):
    """AC-11.22 — Cùng một luật bỏ cột ở mọi cửa (lưới, màn Cột ở 8020 và 8021): cột chuẩn và cột theo tệp
    vận đơn thật, cột khoá, vế của cột tính sẵn, cột đang nhận dữ liệu từ biểu mẫu bị từ chối 400 kèm lời
    báo; cột còn nguyên, cột tách của dòng cũ không mất, không có nhật ký bỏ cột (TL-13)"""
    settings.ROOT_URLCONF = urlconf
    client.raise_request_exception = False
    bang, nguoi = cot_bo_thu(bang_ten)
    d = _dong(bang, nguoi, khach="A", doanh_thu="10", so_luong="2") if bang_ten == "bang_sale" else None
    truoc = d.val_revenue if d is not None else None
    client.force_login(nguoi)

    kq = _bo_cot(client, cua, bang, ma)

    assert kq.status_code == 400, kq.status_code
    assert loi in kq.content.decode()
    assert bang.columns.filter(code=ma).exists()
    if d is not None:
        d.refresh_from_db()
        assert d.val_revenue == truoc
    assert not AuditLog.objects.filter(detail__startswith=f"Bỏ cột {ma} ").exists()


@SUA_DUOC
def test_remove_column_tu_choi_cot_khong_bo_duoc(cot_bo_thu, nguoi_dung):
    """AC-11.22 — Tầng dịch vụ `remove_column` tự áp luật bỏ cột (mọi cửa sau này cũng qua luật):
    cột khoá, vế công thức, cột nối biểu mẫu, cột theo tệp vận đơn thật ném BusinessError, cột còn nguyên;
    `removable_reason` của cột thường vẫn trống (TL-13)"""
    from core.exceptions import BusinessError

    sale, ql = cot_bo_thu("bang_sale")
    vd, admin = cot_bo_thu("bang_vd")
    for bang, ma, nguoi, loi in ((sale, "khach", ql, "cột khoá"), (sale, "doanh_thu", ql, "cột tính sẵn"),
                                 (sale, "ghi_chu_noi", ql, "Biểu mẫu thử"), (vd, "email", admin, "tệp vận đơn thật"),
                                 (vd, "sl_thu", admin, "tệp vận đơn thật")):
        cot = bang.columns.get(code=ma)
        assert loi in table_service.removable_reason(cot), ma
        with pytest.raises(BusinessError, match=loi):
            table_service.remove_column(cot, actor=nguoi)
        assert bang.columns.filter(code=ma).exists(), ma
    thuong = ColumnDef.objects.create(table=sale, name="Ghi chú thêm", code="ghi_chu_them",
                                      field_type=FieldType.TEXT, order=10)
    assert table_service.removable_reason(thuong) == ""


@SUA_DUOC
@pytest.mark.parametrize("urlconf,cua", CUA_BO_COT)
def test_bo_cot_thuong_duoc_o_moi_cua_giu_gia_tri(client, settings, bang_sale, nguoi_dung, urlconf, cua):
    """AC-11.22 — Chiều cho phép: cột thường bỏ được ở mọi cửa, giá trị đã nhập vẫn nằm trong bản ghi (BR-4),
    có nhật ký (bài khoá, TL-13)"""
    settings.ROOT_URLCONF = urlconf
    ql = nguoi_dung["manager_sale"]
    ColumnDef.objects.create(table=bang_sale, name="Ghi chú thêm", code="ghi_chu_them",
                             field_type=FieldType.TEXT, order=9)
    d = _dong(bang_sale, ql, khach="A", ghi_chu_them="giữ lại")
    client.force_login(ql)

    kq = _bo_cot(client, cua, bang_sale, "ghi_chu_them")

    if cua == "luoi":
        assert kq.status_code == 200 and kq.json()["da_bo"] == ["ghi_chu_them"]
    else:
        assert kq.status_code == 302 and kq.url.endswith(f"/bang/{bang_sale.code}/cot/")
    assert not bang_sale.columns.filter(code="ghi_chu_them").exists()
    d.refresh_from_db()
    assert d.data["ghi_chu_them"] == "giữ lại"
    assert AuditLog.objects.filter(detail__startswith="Bỏ cột ghi_chu_them").exists()
