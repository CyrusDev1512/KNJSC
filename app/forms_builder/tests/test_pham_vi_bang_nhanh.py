"""Phạm vi bảng (`TableDef.objects.in_scope`) hỏi nhẹ mà kết quả y nguyên — AC-10.23 (07.10.2026).

Menu khung KN CRM gọi phạm vi bảng ở mọi trang, trang chủ gọi bốn lần. Cách cũ luôn kèm một `EXISTS` trên mọi dòng vận
đơn (OR qua JOIN đơn hàng và phân công): 0,4 s mỗi lần ở 385.000 dòng — kể cả với người mà điều kiện đó chắc chắn rỗng
(nó đòi phòng của chính người dùng là Sale hay CSKH). Nay chỉ thêm nhánh đó cho Sale/CSKH, và tách OR thành ba `EXISTS`
theo chỉ mục. Bài so tập bảng với cách tính cũ (chép nguyên vào đây làm mốc) cho mọi vai.
"""
import pytest
from django.db.models import Exists, OuterRef, Q

from core.constants import ACCOUNTING_DEPARTMENT_CODE, Rank
from core.scope import get_user_scope
from core.managers import apply_department_scope
from forms_builder.models import DataRecord, GrantAction, TableDef
from forms_builder.services import grant_service
from orders.constants import waybill_condition
from orders.models import Product, ProductGroup, WaybillAssignment
from orders.services import dispatch_service
from orders.tests.test_len_don import _len_don
from org.models import Department

pytestmark = pytest.mark.django_db


def _cu(user):
    """Cách tính trước 07.10.2026, chép nguyên — mốc để so."""
    qs = TableDef.objects.all()
    trong_bo_phan = apply_department_scope(qs, user, field="department_id")
    if get_user_scope(user).all_departments:
        return set(trong_bo_phan.values_list("pk", flat=True))
    duoc_cap = grant_service.granted_table_ids(user, GrantAction.VIEW)
    accounting = Department.objects.filter(pk=getattr(getattr(user, 'profile', None), 'department_id', None),
        code=ACCOUNTING_DEPARTMENT_CODE, is_active=True, deleted_at__isnull=True)
    visible = DataRecord.objects.filter(waybill_condition()).filter(
        Q(created_by_id=user.pk, created_by__profile__department__code='sale')
        | Q(order__created_by_id=user.pk, order__created_by__profile__department__code='sale')
        | Q(order__seller_id=user.pk, order__seller__profile__department__code='sale')
        | Q(assignment__care_id=user.pk, assignment__care__profile__department__code__in=['sale', 'cskh']))
    return set(qs.filter(
        Q(pk__in=trong_bo_phan.values("pk")) | Q(pk__in=duoc_cap)
        | Q(Exists(visible.filter(table_id=OuterRef('pk'))))
        | ((waybill_condition("") | Q(erp_report__isnull=False)) & Q(Exists(accounting)))
    ).values_list("pk", flat=True))


@pytest.fixture
def the_gioi(nguoi_dung, departments, make_user, settings):
    """Hai bảng vận đơn (bộ phận Vận đơn và một bảng workflow vận đơn của Marketing), bảng thường từng bộ phận;
    dòng do Sale tạo, đơn Sale bán hộ, phân công CSKH và Sale; một quyền xem riêng; người Kế toán, CSKH, CEO."""
    settings.GRID_ONLY_TABLES = set()
    admin = nguoi_dung["admin"]
    dispatch_service.ensure_waybill_table(actor=admin)
    vd2 = TableDef.objects.create(name="Vận đơn MKT", code="vd_mkt", department=departments["mkt"],
                                  created_by=admin, workflow="waybill")
    thuong = {k: TableDef.objects.create(name=f"Thường {k}", code=f"thuong_{k}", department=departments[k], created_by=admin)
              for k in ("sale", "mkt", "vd")}
    nhom = ProductGroup.objects.create(name="Nhóm")
    sp = {"massage": Product.objects.create(name="Máy", code="may", group=nhom)}
    _len_don(nguoi_dung["staff_sale_1"], sp)                                     # dòng + đơn do Sale tạo
    don2 = _len_don(admin, sp, phone="0911", seller=nguoi_dung["staff_sale_2"])       # Admin lên đơn, Sale đứng đơn
    cskh = make_user("cskh_x", Rank.STAFF, Department.objects.create(code="cskh", name="CSKH"))
    WaybillAssignment.objects.create(record=don2.record, care=cskh)
    dong = DataRecord.objects.create(table=vd2, department=vd2.department, data={"ma_don": "X"},
                                     created_by=nguoi_dung["staff_mkt"])
    WaybillAssignment.objects.create(record=dong, care=nguoi_dung["leader_sale_2"])
    grant_service.grant(table=thuong["sale"], user=nguoi_dung["staff_mkt"], action=GrantAction.VIEW, actor=admin)
    return {**dict(nguoi_dung), "cskh": cskh, "ceo": make_user("ceo_x", Rank.CEO),
            "leader_vd": make_user("leader_vd_x", Rank.LEADER, departments["vd"])}


def test_pham_vi_bang_moi_trung_cach_cu_moi_vai(the_gioi):
    """AC-10.23 — Mọi vai (Staff/Leader/Manager Sale, Marketing, Vận đơn, Kế toán, CSKH, CEO, Admin): tập bảng của
    `TableDef.objects.in_scope` trùng đúng cách tính cũ; Sale thấy bảng vận đơn qua dòng mình tạo, đơn mình bán, phân
    công chăm sóc; CSKH qua phân công"""
    for ten, user in the_gioi.items():
        assert set(TableDef.objects.in_scope(user).values_list("pk", flat=True)) == _cu(user), ten
    assert TableDef.objects.get(code="vd_mkt").pk in _cu(the_gioi["leader_sale_2"])
    assert TableDef.objects.get(code="van_don").pk in _cu(the_gioi["cskh"])


def test_khong_hoi_dong_voi_nguoi_khong_phai_sale_cskh(the_gioi):
    """AC-10.23 — Người không thuộc Sale/CSKH: phạm vi bảng không còn truy vấn con trên bảng dòng; Sale vẫn có `EXISTS`"""
    for ten in ("staff_vd", "manager_mkt", "staff_kt", "leader_vd"):
        sql = str(TableDef.objects.in_scope(the_gioi[ten]).query)
        assert "forms_builder_datarecord" not in sql, ten
    assert "EXISTS" in str(TableDef.objects.in_scope(the_gioi["staff_sale_1"]).query)


def _dong_cu(user, table=None, tat_ca=False):
    """Tập dòng theo điều kiện phạm vi Sale/CSKH cũ (OR qua JOIN đơn hàng, phân công) — mốc để so."""
    from unittest import mock
    from orders.services import assignment_service as a

    def cu(user, original, *, only_new=False):
        scope = get_user_scope(user)
        dept = a.department(user)
        new = waybill_condition()
        if a.can_assign(user) or a.is_accountant(user) or dept == 'van-don':
            allowed = Q()
        elif dept == 'cskh':
            allowed = Q(assignment__care_id=user.pk)
        elif dept == 'sale':
            allowed = (Q(created_by_id=user.pk) | Q(order__created_by_id=user.pk) | Q(order__seller_id=user.pk)
                       | Q(assignment__care_id=user.pk))
            if scope.rank != Rank.STAFF:
                allowed |= original
        else:
            allowed = original
        return allowed if only_new else (~new & original) | (new & allowed)
    with mock.patch.object(a, "scope_condition", cu):
        ql = DataRecord.all_objects if tat_ca else DataRecord.objects
        return set(ql.in_scope(user, **({"table": table} if table else {})).values_list("pk", flat=True))


def test_pham_vi_dong_sale_cskh_trung_cach_cu(the_gioi):
    """AC-10.25 — Phạm vi dòng (chung, theo từng bảng, gồm cả dòng đã xoá) của mọi vai trùng điều kiện cũ: Sale qua
    dòng mình tạo, đơn mình lên hay đứng đơn, dòng được chăm sóc; CSKH qua chăm sóc"""
    cac_bang = list(TableDef.objects.all())
    for ten, user in the_gioi.items():
        for tat_ca in (False, True):
            ql = DataRecord.all_objects if tat_ca else DataRecord.objects
            assert set(ql.in_scope(user).values_list("pk", flat=True)) == _dong_cu(user, tat_ca=tat_ca), ten
            for b in cac_bang:
                assert set(ql.in_scope(user, table=b).values_list("pk", flat=True)) == _dong_cu(user, b, tat_ca), (ten, b.code)
    assert _dong_cu(the_gioi["staff_sale_2"]) and _dong_cu(the_gioi["cskh"])     # thế giới có đủ các nhánh
