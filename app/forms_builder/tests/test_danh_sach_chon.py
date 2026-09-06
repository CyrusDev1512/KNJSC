"""Danh sách chọn của cột kiểu *Chọn một* — FR-8.7, Q58.

Bước 1 kiểm phần định nghĩa: Manager đặt danh sách trong Sửa cột, model chặn
danh sách sai. Phần điền, sửa ô và "Thêm mới…" kiểm ở các bài phía dưới cùng
tệp (thêm dần theo giai đoạn).
"""
import pytest
from django.core.exceptions import ValidationError

from forms_builder.forms import ColumnForm
from forms_builder.meaning import FieldType, Meaning
from forms_builder.models import CHOICE_OPTION_MAX_LENGTH, ColumnDef, TableDef
from forms_builder.services import table_service

pytestmark = pytest.mark.django_db


@pytest.fixture
def bang_sale(departments, nguoi_dung):
    """Bảng của bộ phận Sale, chưa có cột nào."""
    return TableDef.objects.create(
        name="Kênh bán Sale", code="kenh_sale",
        department=departments["sale"], created_by=nguoi_dung["manager_sale"],
    )


# ══ Định nghĩa danh sách — Sửa cột ═══════════════════════════════

def test_danh_sach_chi_cho_kieu_chon_mot(bang_sale):
    """AC-8.7 — Danh sách chọn chỉ đặt được cho cột kiểu Chọn một"""
    cot = ColumnDef(
        table=bang_sale, name="Kênh", code="kenh",
        field_type=FieldType.TEXT, options=["Facebook", "TikTok"],
    )
    with pytest.raises(ValidationError) as loi:
        cot.full_clean()
    assert "options" in loi.value.message_dict

    cot.field_type = FieldType.CHOICE
    cot.full_clean()          # kiểu Chọn một thì nhận
    cot.save()
    assert ColumnDef.objects.get(pk=cot.pk).options == ["Facebook", "TikTok"]


def test_danh_sach_bo_trung_va_dong_trong(bang_sale):
    """AC-8.7 — Sửa cột gõ mỗi dòng một giá trị: bỏ dòng trống, khoảng trắng thừa và giá trị trùng"""
    form = ColumnForm({
        "name": "Kênh", "code": "kenh", "field_type": FieldType.CHOICE,
        "meaning": "", "order": 1, "compute_decimals": 2,
        "options": "Facebook\n\n  TikTok  \nfacebook\nZalo\n",
    }, table=bang_sale)
    assert form.is_valid(), form.errors
    assert form.cleaned_data["options"] == ["Facebook", "TikTok", "Zalo"]

    cot = table_service.add_column(bang_sale, **form.cleaned_data)
    assert cot.options == ["Facebook", "TikTok", "Zalo"]

    # Mở lại để sửa thì thấy đúng từng dòng
    form_sua = ColumnForm(instance=cot, table=bang_sale)
    assert form_sua.initial["options"] == "Facebook\nTikTok\nZalo"


def test_model_chan_danh_sach_trung_va_qua_dai(bang_sale):
    """FR-8.7 — Danh sách đến từ dịch vụ hay JSON tay đều bị chặn nếu trùng, trống hoặc quá dài"""
    cot = ColumnDef(table=bang_sale, name="Kênh", code="kenh", field_type=FieldType.CHOICE)

    for sai in (["A", "a"], ["A", ""], ["A", "x" * (CHOICE_OPTION_MAX_LENGTH + 1)], " có dấu cách "):
        cot.options = sai if isinstance(sai, list) else [sai]
        with pytest.raises(ValidationError) as loi:
            cot.full_clean()
        assert "options" in loi.value.message_dict, sai


def test_cot_mang_nhan_san_pham_khong_nhap_danh_sach_tay(bang_sale):
    """FR-8.7 — Cột Chọn một mang nhãn có nguồn hệ thống thì không nhập danh sách tay"""
    from forms_builder import choice_registry

    cot = ColumnDef(
        table=bang_sale, name="Sản phẩm", code="san_pham",
        field_type=FieldType.CHOICE, meaning=Meaning.PRODUCT, options=["Kem"],
    )
    if choice_registry.has_meaning_source(Meaning.PRODUCT):
        with pytest.raises(ValidationError) as loi:
            cot.full_clean()
        assert "không nhập tay" in str(loi.value.message_dict["options"])
    else:
        # Chưa module nào đăng ký nguồn (giai đoạn sau) thì cột nhận danh sách tay
        cot.full_clean()


# ══ Phân giải danh sách và kiểm khi ghi — tầng dịch vụ ═══════════════

@pytest.fixture
def bang_kenh(bang_sale):
    """Bảng Sale có cột Chọn một với danh sách trên cột, và cột Sản phẩm mang nhãn."""
    ColumnDef.objects.create(
        table=bang_sale, name="Kênh", code="kenh", field_type=FieldType.CHOICE,
        options=["Facebook", "TikTok"], order=0,
    )
    ColumnDef.objects.create(
        table=bang_sale, name="Sản phẩm", code="san_pham", field_type=FieldType.CHOICE,
        meaning=Meaning.PRODUCT, order=1,
    )
    ColumnDef.objects.create(
        table=bang_sale, name="Ghi chú", code="ghi_chu", field_type=FieldType.TEXT, order=2,
    )
    return bang_sale


@pytest.fixture
def san_pham(db):
    from orders.models import Product, ProductGroup

    nhom = ProductGroup.objects.create(name="Mỹ phẩm")
    return {
        "cream": Product.objects.create(name="Retinol Cream", code="retinol-cream", group=nhom),
        "serum": Product.objects.create(name="Retinol Serum", code="retinol-serum", group=nhom),
    }


def test_cot_chon_tu_choi_gia_tri_ngoai_danh_sach(bang_kenh, nguoi_dung):
    """AC-8.7 — Cột Chọn một chỉ nhận giá trị trong danh sách, không phân biệt hoa thường, giá trị lạ bị từ chối kèm gợi ý"""
    from core.exceptions import BusinessError
    from forms_builder.services import record_service

    dong = record_service.create_record(
        bang_kenh, {"kenh": "facebook"}, actor=nguoi_dung["staff_sale_1"])
    assert dong.data["kenh"] == "Facebook"        # đưa về đúng nhãn

    with pytest.raises(BusinessError) as loi:
        record_service.create_record(bang_kenh, {"kenh": "Zalo"}, actor=nguoi_dung["staff_sale_1"])
    assert "không có trong danh sách" in str(loi.value)
    assert "Facebook, TikTok" in str(loi.value)


def test_cot_chon_chua_co_danh_sach_khong_nhan_gia_tri(bang_sale, nguoi_dung):
    """AC-8.7 — Cột Chọn một chưa có danh sách thì không nhận giá trị nào, lỗi chỉ Manager tới Sửa cột (Q58)"""
    from core.exceptions import BusinessError
    from forms_builder.services import record_service

    ColumnDef.objects.create(
        table=bang_sale, name="Nguồn", code="nguon", field_type=FieldType.CHOICE, order=0)
    with pytest.raises(BusinessError) as loi:
        record_service.create_record(bang_sale, {"nguon": "Bất kỳ"}, actor=nguoi_dung["staff_sale_1"])
    assert "chưa có danh sách" in str(loi.value)
    # Để trống thì vẫn được — cột không bắt buộc
    dong = record_service.create_record(bang_sale, {"nguon": ""}, actor=nguoi_dung["staff_sale_1"])
    assert dong.data.get("nguon") is None


def test_cot_san_pham_lay_danh_sach_tu_danh_muc(bang_kenh, san_pham, nguoi_dung):
    """AC-8.8 — Cột Chọn một mang nhãn Sản phẩm lấy danh sách từ danh mục sản phẩm đang bán"""
    from core.exceptions import BusinessError
    from forms_builder import choice_registry
    from forms_builder.services import record_service

    cot = bang_kenh.columns.get(code="san_pham")
    ds = choice_registry.for_column(cot)
    assert ds.source == choice_registry.SOURCE_MEANING and ds.strict and ds.can_add
    assert list(ds.options()) == ["Retinol Cream", "Retinol Serum"]

    dong = record_service.create_record(
        bang_kenh, {"kenh": "TikTok", "san_pham": "retinol serum"}, actor=nguoi_dung["staff_sale_1"])
    assert dong.data["san_pham"] == "Retinol Serum"
    assert dong.val_product == "Retinol Serum"
    with pytest.raises(BusinessError):
        record_service.create_record(
            bang_kenh, {"kenh": "TikTok", "san_pham": "Kem lạ"}, actor=nguoi_dung["staff_sale_1"])

    # Sản phẩm ngừng bán thì rời khỏi danh sách
    san_pham["cream"].is_active = False
    san_pham["cream"].save(update_fields=["is_active"])
    assert list(ds.options()) == ["Retinol Serum"]


def test_cot_nguoi_ban_goi_y_nhan_su_bo_phan(bang_sale, nguoi_dung, departments):
    """FR-8.7 — Cột Chọn một mang nhãn Người bán gợi ý nhân sự đang làm ở bộ phận sở hữu bảng, vẫn nhận tên khác"""
    from forms_builder import choice_registry
    from forms_builder.services import record_service

    cot = ColumnDef.objects.create(
        table=bang_sale, name="Người bán", code="nguoi_ban", field_type=FieldType.CHOICE,
        meaning=Meaning.SELLER, order=0)
    ds = choice_registry.for_column(cot)
    assert not ds.strict and not ds.can_add
    ten = ds.options()
    assert "Staff Sale 1" in ten and "Manager Sale" in ten      # họ tên trong hồ sơ
    assert "Staff Mkt" not in ten                               # bộ phận khác

    dong = record_service.create_record(
        bang_sale, {"nguoi_ban": "Người đã nghỉ"}, actor=nguoi_dung["staff_sale_1"])
    assert dong.val_seller == "Người đã nghỉ"


def test_nhap_hang_loat_cot_chon_mot_lan_truy_van_danh_sach(
        bang_kenh, san_pham, nguoi_dung, django_assert_max_num_queries):
    """AC-8.7 — Nhập hàng loạt kiểm danh sách chọn bằng một bản chụp, dòng lỗi được liệt kê, dòng hợp lệ vẫn vào"""
    from forms_builder.services import record_service

    dong = [{"kenh": "facebook", "san_pham": "Retinol Cream"} for _ in range(40)]
    dong.insert(5, {"kenh": "Zalo", "san_pham": "Retinol Cream"})
    dong.insert(9, {"kenh": "TikTok", "san_pham": "Không có"})
    cac_cot = list(bang_kenh.columns.all())
    # Danh mục sản phẩm đọc đúng một lần; mỗi lô 500 dòng ghi một lệnh; một dòng nhật ký
    with django_assert_max_num_queries(6):
        kq = record_service.create_records_bulk(
            bang_kenh, dong, actor=nguoi_dung["manager_sale"], columns=cac_cot)
    assert kq.created == 40
    assert [so for so, _ in kq.errors] == [6, 10]
    assert "không có trong danh sách" in kq.errors[0][1]


def test_bang_van_don_giu_so_crm(departments, nguoi_dung):
    """AC-11.3 — Bảng vận đơn vẫn dùng sổ danh sách của Bảng tính, danh sách trên cột không chen vào"""
    from forms_builder import choice_registry
    from orders.services import dispatch_service

    bang = dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])
    cot = bang.columns.get(code="trang_thai_vc")
    ds = choice_registry.for_column(cot)
    assert ds.source == choice_registry.SOURCE_REGISTRY
    assert "Đã lên đơn" in ds.options()
    assert choice_registry.match(ds, "đã lên đơn") == ("Đã lên đơn", True)


# ══ Thêm giá trị mới — tầng dịch vụ ═════════════════════════════════

def test_them_gia_tri_vao_cot_ghi_nhat_ky(bang_kenh, nguoi_dung):
    """AC-8.8 — Thêm giá trị mới vào danh sách trên cột: ghi vào cột, có một dòng nhật ký, trùng thì trả nhãn cũ không ghi gì"""
    from core.constants import AuditAction
    from core.models import AuditLog
    from forms_builder.services import choice_service

    cot = bang_kenh.columns.get(code="kenh")
    truoc = AuditLog.objects.filter(action=AuditAction.UPDATE).count()
    assert choice_service.add_option(cot, "  Zalo ", actor=nguoi_dung["manager_sale"]) == "Zalo"
    cot.refresh_from_db()
    assert cot.options == ["Facebook", "TikTok", "Zalo"]
    assert AuditLog.objects.filter(action=AuditAction.UPDATE).count() == truoc + 1

    # Đã có rồi (khác hoa thường) thì trả nhãn có sẵn, không ghi thêm gì
    assert choice_service.add_option(cot, "tiktok", actor=nguoi_dung["manager_sale"]) == "TikTok"
    cot.refresh_from_db()
    assert cot.options == ["Facebook", "TikTok", "Zalo"]
    assert AuditLog.objects.filter(action=AuditAction.UPDATE).count() == truoc + 1


def test_them_gia_tri_rong_hoac_sai_kieu_bi_tu_choi(bang_kenh, nguoi_dung):
    """FR-8.7 — Giá trị mới rỗng, hoặc thêm vào cột không phải Chọn một, đều bị từ chối"""
    from core.exceptions import BusinessError
    from forms_builder.services import choice_service

    with pytest.raises(BusinessError):
        choice_service.add_option(bang_kenh.columns.get(code="kenh"), "   ")
    with pytest.raises(BusinessError):
        choice_service.add_option(bang_kenh.columns.get(code="ghi_chu"), "Gì đó")


def test_them_gia_tri_cot_san_pham_la_them_san_pham(bang_kenh, san_pham, nguoi_dung):
    """AC-8.8 — "Thêm mới…" ở cột Sản phẩm là thêm sản phẩm vào danh mục, có mã tự sinh"""
    from forms_builder.services import choice_service
    from orders.models import Product

    cot = bang_kenh.columns.get(code="san_pham")
    assert choice_service.add_option(cot, "Sữa rửa mặt", actor=nguoi_dung["manager_sale"]) == "Sữa rửa mặt"
    sp = Product.objects.get(name="Sữa rửa mặt")
    assert sp.code == "sua-rua-mat" and sp.is_active
    # Đã có thì không tạo thêm
    assert choice_service.add_option(cot, "retinol cream", actor=nguoi_dung["manager_sale"]) == "Retinol Cream"
    assert Product.objects.count() == 3


def test_quyen_them_gia_tri(bang_kenh, nguoi_dung, departments):
    """AC-8.8 — Admin và Manager bộ phận sở hữu bảng thêm được; Staff, Leader, Manager bộ phận khác thì không"""
    from forms_builder.services import choice_service

    assert choice_service.can_manage_options(nguoi_dung["admin"], bang_kenh)
    assert choice_service.can_manage_options(nguoi_dung["manager_sale"], bang_kenh)
    for ma in ("staff_sale_1", "leader_sale_1", "manager_mkt", "staff_vd"):
        assert not choice_service.can_manage_options(nguoi_dung[ma], bang_kenh), ma


# ══ Màn hình — ô chọn và "Thêm mới…" ════════════════════════════════

@pytest.fixture
def bieu_mau_kenh(bang_kenh, departments, nguoi_dung):
    """Biểu mẫu Sale nối vào bảng kênh: Kênh (chọn), Sản phẩm (chọn, nhãn), Ghi chú."""
    from forms_builder.models import FieldDef
    from forms_builder.services import form_service

    ql = nguoi_dung["manager_sale"]
    bm = form_service.create_form(
        name="Kênh bán ngày", code="kenh_ngay", department=departments["sale"],
        table=bang_kenh, actor=ql,
    )
    for ten, ma, kieu, nhan in [
        ("Kênh", "kenh", FieldType.CHOICE, ""),
        ("Sản phẩm", "san_pham", FieldType.CHOICE, Meaning.PRODUCT),
        ("Ghi chú", "ghi_chu", FieldType.TEXT, ""),
    ]:
        truong = FieldDef.objects.create(
            name=ten, code=ma, field_type=kieu, meaning=nhan, department=departments["sale"])
        form_service.add_field(
            bm, truong, column=bang_kenh.columns.get(code=ma), required=(ma == "kenh"), actor=ql)
    return bm


def _dong_kenh(bang, nguoi, **gia_tri):
    from forms_builder.services import record_service

    return record_service.create_record(bang, gia_tri, actor=nguoi)


def test_o_chon_tren_bang_du_lieu_la_select(client, bang_kenh, san_pham, nguoi_dung):
    """AC-8.7 — Ô của cột Chọn một trên Bảng dữ liệu là ô chọn; Manager có mục Thêm mới, Staff thì không"""
    _dong_kenh(bang_kenh, nguoi_dung["staff_sale_1"], kenh="Facebook")

    client.force_login(nguoi_dung["manager_sale"])
    html = client.get("/bang/kenh_sale/").content.decode()
    assert '<select class="o-trong-bang" name="gia_tri"' in html
    assert '<option value="Facebook" selected>' in html
    assert '<option value="Retinol Cream">' in html          # cột Sản phẩm lấy từ danh mục
    assert '<option value="__them__">' in html

    client.force_login(nguoi_dung["staff_sale_1"])           # sửa được dòng của mình
    html = client.get("/bang/kenh_sale/").content.decode()
    assert '<select class="o-trong-bang" name="gia_tri"' in html
    assert '<option value="__them__">' not in html


def test_gui_thang_gia_tri_la_vao_o_chon_bi_400(client, bang_kenh, nguoi_dung):
    """AC-8.7 — Gửi thẳng giá trị ngoài danh sách vào ô chọn thì bị từ chối, ô trả về vẫn là ô chọn kèm lý do"""
    dong = _dong_kenh(bang_kenh, nguoi_dung["manager_sale"], kenh="Facebook")
    client.force_login(nguoi_dung["manager_sale"])

    kq = client.post(f"/bang/kenh_sale/o/{dong.pk}/kenh/", {"gia_tri": "Zalo"})
    assert kq.status_code == 400
    html = kq.content.decode()
    assert "o-loi" in html and "<select" in html and "không có trong danh sách" in html
    dong.refresh_from_db()
    assert dong.data["kenh"] == "Facebook"

    kq = client.post(f"/bang/kenh_sale/o/{dong.pk}/kenh/", {"gia_tri": "tiktok"})
    assert kq.status_code == 200
    assert '<option value="TikTok" selected>' in kq.content.decode()
    dong.refresh_from_db()
    assert dong.data["kenh"] == "TikTok"


def test_bieu_mau_va_bao_cao_ngay_hien_o_chon(client, bieu_mau_kenh, san_pham, nguoi_dung):
    """AC-8.7 — Màn hình điền biểu mẫu và nộp báo cáo ngày vẽ cột Chọn một thành ô chọn; Manager thấy Thêm mới"""
    client.force_login(nguoi_dung["manager_sale"])
    for url in ("/bieu-mau/kenh_ngay/dien/", "/bao-cao/?bieu_mau=kenh_ngay"):
        html = client.get(url).content.decode()
        assert '<select class="o-nhap" name="kenh"' in html, url
        assert '<option value="TikTok">' in html and '<option value="Retinol Cream">' in html
        assert html.count('<option value="__them__">') == 2                     # Kênh và Sản phẩm

    client.force_login(nguoi_dung["staff_sale_1"])
    html = client.get("/bieu-mau/kenh_ngay/dien/").content.decode()
    assert '<select class="o-nhap" name="kenh"' in html and "__them__" not in html


def test_manager_them_gia_tri_qua_duong_dan(client, bang_kenh, nguoi_dung):
    """AC-8.8 — Manager bộ phận sở hữu thêm giá trị qua đường dẫn: danh sách trả về có mục mới được chọn, cột đổi, có nhật ký"""
    from core.constants import AuditAction
    from core.models import AuditLog

    client.force_login(nguoi_dung["manager_sale"])
    truoc = AuditLog.objects.filter(action=AuditAction.UPDATE).count()
    kq = client.post("/bang/kenh_sale/cot/kenh/lua-chon/", {"nhan_moi": "Zalo"})
    assert kq.status_code == 200
    html = kq.content.decode()
    assert '<option value="Zalo" selected>' in html and '<option value="__them__">' in html
    assert bang_kenh.columns.get(code="kenh").options == ["Facebook", "TikTok", "Zalo"]
    assert AuditLog.objects.filter(action=AuditAction.UPDATE).count() == truoc + 1


def test_staff_va_leader_them_gia_tri_bi_403_co_nhat_ky(client, bang_kenh, nguoi_dung):
    """AC-8.8 — Staff và Leader gửi thẳng đường dẫn thêm giá trị thì bị từ chối và có dòng nhật ký từ chối"""
    from core.constants import AuditAction
    from core.models import AuditLog

    for ma in ("staff_sale_1", "leader_sale_1"):
        truoc = AuditLog.objects.filter(action=AuditAction.DENIED).count()
        client.force_login(nguoi_dung[ma])
        kq = client.post("/bang/kenh_sale/cot/kenh/lua-chon/", {"nhan_moi": "Zalo"})
        assert kq.status_code == 403, ma
        assert AuditLog.objects.filter(action=AuditAction.DENIED).count() == truoc + 1
    assert bang_kenh.columns.get(code="kenh").options == ["Facebook", "TikTok"]


def test_manager_bo_phan_khac_va_nguoi_duoc_cap_quyen_bi_chan(client, bang_kenh, nguoi_dung):
    """AC-8.8 — Manager bộ phận khác không thấy bảng (404); người được cấp quyền Sửa vẫn không thêm được (403)"""
    from forms_builder.models import GrantAction
    from forms_builder.services import grant_service

    client.force_login(nguoi_dung["manager_mkt"])
    assert client.post("/bang/kenh_sale/cot/kenh/lua-chon/", {"nhan_moi": "Zalo"}).status_code == 404

    # Cấp quyền xem lẫn sửa — như màn hình cấp quyền vẫn làm
    for viec in (GrantAction.VIEW, GrantAction.EDIT):
        grant_service.grant(
            table=bang_kenh, user=nguoi_dung["staff_mkt"], action=viec,
            actor=nguoi_dung["manager_sale"],
        )
    client.force_login(nguoi_dung["staff_mkt"])
    assert client.get("/bang/kenh_sale/").status_code == 200          # thấy bảng nhờ cấp quyền
    assert client.post("/bang/kenh_sale/cot/kenh/lua-chon/", {"nhan_moi": "Zalo"}).status_code == 403
    assert bang_kenh.columns.get(code="kenh").options == ["Facebook", "TikTok"]


def test_them_gia_tri_rong_400_va_get_405(client, bang_kenh, nguoi_dung):
    """AC-8.8 — Giá trị rỗng bị từ chối kèm thông báo; đường dẫn chỉ nhận POST; cột không có thì 404"""
    client.force_login(nguoi_dung["manager_sale"])
    kq = client.post("/bang/kenh_sale/cot/kenh/lua-chon/", {"nhan_moi": "   "})
    assert kq.status_code == 400 and "không được để trống" in kq.content.decode()
    assert client.get("/bang/kenh_sale/cot/kenh/lua-chon/").status_code == 405
    assert client.post("/bang/kenh_sale/cot/khong_co/lua-chon/", {"nhan_moi": "X"}).status_code == 404


def test_cot_san_pham_them_gia_tri_qua_duong_dan_la_tao_san_pham(client, bang_kenh, san_pham, nguoi_dung):
    """AC-8.8 — Thêm mới ở cột Sản phẩm qua đường dẫn tạo sản phẩm trong danh mục và cột số lượng trên bảng vận đơn"""
    from orders.models import Product
    from orders.services import dispatch_service

    bang_vd = dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])
    client.force_login(nguoi_dung["manager_sale"])
    kq = client.post("/bang/kenh_sale/cot/san_pham/lua-chon/", {"nhan_moi": "Kem chống nắng"})
    assert kq.status_code == 200
    assert '<option value="Kem chống nắng" selected>' in kq.content.decode()
    assert Product.objects.filter(name="Kem chống nắng", code="kem-chong-nang").exists()
    assert bang_vd.columns.filter(code="sl_kem_chong_nang").exists()


def test_bang_co_cot_chon_khong_qua_muoi_lenh_truy_van(
        client, bang_kenh, san_pham, nguoi_dung, django_assert_max_num_queries):
    """AC-10.2 — Bảng có cột chọn (danh sách trên cột và danh mục sản phẩm) vẫn không quá 10 lệnh truy vấn"""
    for _ in range(30):
        _dong_kenh(bang_kenh, nguoi_dung["manager_sale"], kenh="Facebook", san_pham="Retinol Cream")
    client.force_login(nguoi_dung["manager_sale"])
    client.get("/bang/kenh_sale/")                  # lượt đầu ghi mốc phiên
    with django_assert_max_num_queries(10):
        assert client.get("/bang/kenh_sale/").status_code == 200


def test_man_hinh_dien_va_bao_cao_ngay_it_truy_van(
        client, bieu_mau_kenh, san_pham, nguoi_dung, django_assert_max_num_queries):
    """Quy tắc Q2 — Màn hình điền biểu mẫu và nộp báo cáo ngày có ô chọn vẫn dưới 12 lệnh truy vấn"""
    client.force_login(nguoi_dung["manager_sale"])
    for url in ("/bieu-mau/kenh_ngay/dien/", "/bao-cao/?bieu_mau=kenh_ngay"):
        client.get(url)
        with django_assert_max_num_queries(12):
            assert client.get(url).status_code == 200, url
