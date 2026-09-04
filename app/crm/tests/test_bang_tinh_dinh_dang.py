"""Định dạng ô trên Bảng tính — `docs/04` mục 11, ADR-010 (Giai đoạn B).

Định dạng lưu trong `DataRecord.style`, mọi người cùng thấy; quyền = quyền
sửa ô. Mỗi bài phân quyền kiểm cả hai chiều.
"""
import pytest
from django.test import override_settings

from core.constants import GRID_FORMAT_CELLS_MAX, AuditAction
from core.exceptions import BusinessError
from core.models import AuditLog
from forms_builder.meaning import FieldType, Meaning
from forms_builder.models import ColumnDef, DataRecord, TableDef
from forms_builder.services import record_service
from orders.services import dispatch_service

pytestmark = pytest.mark.django_db

SUA_DUOC = override_settings(GRID_ONLY_TABLES=set())


@pytest.fixture
def bang_sale(departments, nguoi_dung):
    bang = TableDef.objects.create(
        name="Đơn hàng Sale", code="don_sale",
        department=departments["sale"], created_by=nguoi_dung["manager_sale"],
    )
    for i, (ten, ma, kieu, nhan) in enumerate([
        ("Ngày", "ngay", FieldType.DATE, Meaning.DATE),
        ("Khách hàng", "khach", FieldType.TEXT, Meaning.CUSTOMER),
        ("Ghi chú", "ghi_chu", FieldType.LONG_TEXT, ""),
    ]):
        ColumnDef.objects.create(table=bang, name=ten, code=ma, field_type=kieu, meaning=nhan, order=i)
    return bang


@pytest.fixture
def bang_vd(departments, nguoi_dung):
    return dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])


def _dong(bang, nguoi, **gia_tri):
    return record_service.create_record(bang, gia_tri, actor=nguoi)


def _o(*cap):
    return [f"{ban_ghi.pk}:{ma}" for ban_ghi, ma in cap]


# ══ Sổ định dạng — quy tắc 7 ═══════════════════════════════════════

def test_normalise_style_chi_nhan_gia_tri_trong_so():
    """AC-11.15 — Sổ định dạng đóng: khoá hay giá trị lạ bị từ chối, giá trị rỗng nghĩa là bỏ, số được ép kiểu"""
    assert record_service.normalise_style({"b": "1", "bg": "vang", "fs": "14", "al": "c"}) == {"b": 1, "bg": "vang", "fs": 14, "al": "c"}
    assert record_service.normalise_style({"b": "", "bg": "", "fs": "0"}) == {}
    for xau in ({"bg": "#ff0000"}, {"fs": "13"}, {"al": "justify"}, {"color": "red"}, {"b": "x"}):
        with pytest.raises(BusinessError):
            record_service.normalise_style(xau)
    with pytest.raises(BusinessError):
        record_service.normalise_style("b=1")


# ══ Lưu và cùng thấy — AC-11.15 ════════════════════════════════════

def test_dinh_dang_o_luu_va_nguoi_khac_thay(client, bang_sale, nguoi_dung):
    """AC-11.15 — Định dạng ô (đậm, nền, cỡ, căn) lưu vào cơ sở dữ liệu, người khác mở cũng thấy; gộp từng thuộc tính, bỏ được từng cái hoặc gỡ hết; giá trị ngoài sổ bị từ chối; mỗi lần một dòng nhật ký"""
    st = nguoi_dung["staff_sale_1"]
    d1 = _dong(bang_sale, st, ngay="2026-08-01", khach="A", ghi_chu="x")
    d2 = _dong(bang_sale, st, ngay="2026-08-02", khach="B", ghi_chu="y")
    client.force_login(st)
    duong = "/bang-tinh/don_sale/dinh-dang/"

    truoc = AuditLog.objects.filter(action=AuditAction.UPDATE).count()
    kq = client.post(duong, {"o": _o((d1, "ghi_chu"), (d2, "ghi_chu")), "b": "1", "bg": "vang"})
    assert kq.status_code == 200
    html = kq.content.decode()
    assert html.count('hx-swap-oob="outerHTML"') == 2
    assert html.count("dd-dam dd-nen-vang") == 2
    assert f'id="o-{d1.pk}-ghi_chu"' in html and f'id="o-{d2.pk}-ghi_chu"' in html
    d1.refresh_from_db(); d2.refresh_from_db()
    assert d1.style == {"ghi_chu": {"b": 1, "bg": "vang"}} and d2.style == d1.style
    assert d1.data["ghi_chu"] == "x"                       # dữ liệu không bị đụng
    assert AuditLog.objects.filter(action=AuditAction.UPDATE).count() == truoc + 1
    assert "Định dạng 2 ô" in AuditLog.objects.filter(action=AuditAction.UPDATE).latest("created_at").detail

    # Gộp: thêm căn giữa và cỡ chữ, đậm và nền vẫn còn
    assert client.post(duong, {"o": _o((d1, "ghi_chu")), "al": "c", "fs": "14"}).status_code == 200
    d1.refresh_from_db()
    assert d1.style["ghi_chu"] == {"b": 1, "bg": "vang", "al": "c", "fs": 14}
    # Bỏ một thuộc tính: gửi rỗng
    assert client.post(duong, {"o": _o((d1, "ghi_chu")), "b": ""}).status_code == 200
    d1.refresh_from_db()
    assert d1.style["ghi_chu"] == {"bg": "vang", "al": "c", "fs": 14}
    # Không đổi gì thì không thêm nhật ký
    sau = AuditLog.objects.filter(action=AuditAction.UPDATE).count()
    assert client.post(duong, {"o": _o((d1, "ghi_chu")), "bg": "vang"}).status_code == 200
    assert AuditLog.objects.filter(action=AuditAction.UPDATE).count() == sau

    # Người khác cùng phạm vi mở lưới thì thấy lớp định dạng
    client.force_login(nguoi_dung["manager_sale"])
    html = client.get("/bang-tinh/don_sale/").content.decode()
    assert "dd-nen-vang dd-can-giua dd-co-14" in html or ("dd-nen-vang" in html and "dd-can-giua" in html and "dd-co-14" in html)
    # Ô trả về sau khi sửa giá trị vẫn giữ định dạng
    kq = client.post(f"/bang-tinh/don_sale/o/{d1.pk}/ghi_chu/", {"gia_tri": "đổi"})
    assert kq.status_code == 200 and "dd-nen-vang" in kq.content.decode()

    # Gỡ hết
    client.force_login(st)
    assert client.post(duong, {"o": _o((d1, "ghi_chu"), (d2, "ghi_chu")), "xoa": "1"}).status_code == 200
    d1.refresh_from_db(); d2.refresh_from_db()
    assert d1.style == {} and d2.style == {}

    # Giá trị ngoài sổ → 400 kèm lời báo, không lưu; không chọn ô → 400; quá nhiều ô → 400
    kq = client.post(duong, {"o": _o((d1, "ghi_chu")), "bg": "#ff0000"})
    assert kq.status_code == 400 and "không dùng được" in kq.content.decode()
    d1.refresh_from_db()
    assert d1.style == {}
    assert client.post(duong, {"b": "1"}).status_code == 400
    qua_nhieu = [f"{d1.pk}:ghi_chu"] * (GRID_FORMAT_CELLS_MAX + 1)
    assert client.post(duong, {"o": qua_nhieu, "b": "1"}).status_code == 400
    # Cột lạ bị bỏ qua, ô lạ (bảng khác) bị bỏ qua
    assert client.post(duong, {"o": [f"{d1.pk}:khong_co"], "b": "1"}).status_code == 400


def test_dinh_dang_theo_quyen_sua_o(client, bang_sale, bang_vd, nguoi_dung):
    """AC-11.15 — Định dạng ô theo đúng quyền sửa ô: dòng của mình được, dòng người khác team bị 403 có nhật ký, quản lý được; bảng vận đơn chỉ xem ở dịch vụ chính thì 403, ở dịch vụ Bảng tính thì được; ngoài phạm vi 404"""
    d_1 = _dong(bang_sale, nguoi_dung["staff_sale_1"], ngay="2026-08-01", khach="A")
    d_2 = _dong(bang_sale, nguoi_dung["staff_sale_2"], ngay="2026-08-01", khach="B")
    duong = "/bang-tinh/don_sale/dinh-dang/"

    client.force_login(nguoi_dung["staff_sale_1"])
    assert client.post(duong, {"o": _o((d_1, "khach")), "b": "1"}).status_code == 200
    truoc = AuditLog.objects.filter(action=AuditAction.DENIED).count()
    # dòng của team khác: không thấy (ngoài phạm vi) → bị bỏ qua, không ô nào đổi → vẫn 200 nhưng không lưu
    kq = client.post(duong, {"o": _o((d_2, "khach")), "b": "1"})
    d_2.refresh_from_db()
    assert d_2.style == {}
    # Leader cùng team thấy dòng nhưng không sửa được dòng người khác → 403 có nhật ký
    client.force_login(nguoi_dung["leader_sale_1"])
    d_1b = _dong(bang_sale, nguoi_dung["staff_sale_1b"], ngay="2026-08-01", khach="C")
    assert client.post(duong, {"o": _o((d_1b, "khach")), "b": "1"}).status_code == 403
    assert AuditLog.objects.filter(action=AuditAction.DENIED).count() == truoc + 1
    d_1b.refresh_from_db()
    assert d_1b.style == {}
    client.force_login(nguoi_dung["manager_sale"])
    assert client.post(duong, {"o": _o((d_1b, "khach"), (d_2, "khach")), "al": "r"}).status_code == 200
    d_1b.refresh_from_db(); d_2.refresh_from_db()
    assert d_1b.style["khach"]["al"] == "r" and d_2.style["khach"]["al"] == "r"

    # Ngoài phạm vi bảng → 404
    client.force_login(nguoi_dung["staff_mkt"])
    assert client.post(duong, {"o": _o((d_1, "khach")), "b": "1"}).status_code == 404

    # Bảng vận đơn: dịch vụ chính chỉ xem → 403; dịch vụ Bảng tính → 200
    vd = nguoi_dung["staff_vd"]
    dong = _dong(bang_vd, vd, ma_don="D1", ten_khach="X", so_dien_thoai="0911")
    client.force_login(vd)
    duong_vd = "/bang-tinh/van_don/dinh-dang/"
    assert client.post(duong_vd, {"o": _o((dong, "ten_khach")), "bg": "luc"}).status_code == 403
    with SUA_DUOC:
        assert client.post(duong_vd, {"o": _o((dong, "ten_khach")), "bg": "luc"}).status_code == 200
        html = client.get("/bang-tinh/van_don/").content.decode()
        assert "dd-nen-luc" in html
    dong.refresh_from_db()
    assert dong.style == {"ten_khach": {"bg": "luc"}}
    assert DataRecord.objects.get(pk=dong.pk).val_customer == "X"
