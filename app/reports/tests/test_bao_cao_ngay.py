"""Kiểm thử báo cáo hằng ngày — Giai đoạn 4.

Thứ dễ sai nhất ở đây là **khoá sau khi nộp**. BR-2 và FR-4.4 nói báo cáo đã
nộp không sửa và không xoá được, nên phải chặn ở ba tầng và kiểm cả ba:

1. Không có view sửa — gọi thẳng đường dẫn cũng không có gì để gọi
2. `DailyReport.save()` nổ nếu ai đó sửa bằng mã
3. Ràng buộc duy nhất trong cơ sở dữ liệu chặn nộp đè

Mỗi bài phân quyền kiểm **cả hai chiều**.
"""
from datetime import date

import pytest
from django.utils import timezone

from core.constants import AuditAction
from core.exceptions import BusinessError
from core.models import AuditLog
from forms_builder.meaning import FieldType, Meaning
from forms_builder.models import ColumnDef, ComputeOp, FieldDef, TableDef
from forms_builder.services import form_service
from reports.models import DailyReport
from reports.services import daily_service

pytestmark = pytest.mark.django_db

NGAY = date(2026, 8, 28)


def _dung_bieu_mau(bo_phan, nguoi, ma):
    """Dựng một bảng và một biểu mẫu nối vào nó, cho một bộ phận."""
    bang = TableDef.objects.create(
        name=f"Bảng {ma}", code=f"bang_{ma}", department=bo_phan, created_by=nguoi,
    )
    cot = [
        ("Ngày", "ngay", FieldType.DATE, Meaning.DATE),
        ("Số Mess", "so_mess", FieldType.INTEGER, ""),
        ("Số đơn", "so_don", FieldType.INTEGER, ""),
        ("Doanh số", "doanh_so", FieldType.MONEY, Meaning.REVENUE),
    ]
    for i, (ten, ma_cot, kieu, nhan) in enumerate(cot):
        ColumnDef.objects.create(
            table=bang, name=ten, code=ma_cot, field_type=kieu, meaning=nhan, order=i,
        )
    ColumnDef.objects.create(
        table=bang, name="Tỉ lệ chốt", code="ti_le_chot", field_type=FieldType.DECIMAL,
        order=4, is_computed=True, compute_op=ComputeOp.PERCENT,
        compute_left="so_don", compute_right="so_mess", compute_decimals=2,
    )

    bm = form_service.create_form(
        name=f"Báo cáo {ma}", code=f"bc_{ma}", department=bo_phan,
        table=bang, actor=nguoi,
    )
    for ten, ma_cot, kieu, nhan in cot:
        truong = FieldDef.objects.create(
            name=ten, code=ma_cot, field_type=kieu, meaning=nhan, department=bo_phan,
        )
        form_service.add_field(
            bm, truong, column=bang.columns.get(code=ma_cot),
            required=(ma_cot == "ngay"), actor=nguoi,
        )
    return bm


@pytest.fixture
def bm_mkt(departments, nguoi_dung):
    return _dung_bieu_mau(departments["mkt"], nguoi_dung["manager_mkt"], "mkt")


@pytest.fixture
def bm_sale(departments, nguoi_dung):
    return _dung_bieu_mau(departments["sale"], nguoi_dung["manager_sale"], "sale")


def _nop(bm, nguoi, ngay=NGAY, **gia_tri):
    du_lieu = {"ngay": ngay.isoformat(), "so_mess": "1000", "so_don": "50",
               "doanh_so": "5000000"}
    du_lieu.update(gia_tri)
    return daily_service.submit(bm, du_lieu, report_date=ngay, actor=nguoi)


# ══ Mỗi bộ phận một biểu mẫu riêng — FR-4.1 ════════════════════════

def test_moi_bo_phan_thay_bieu_mau_rieng(bm_mkt, bm_sale, nguoi_dung):
    """AC-4.1 — Mỗi bộ phận thấy biểu mẫu riêng, không thấy của bộ phận khác"""
    cua_mkt = set(daily_service.forms_for(nguoi_dung["staff_mkt"])
                  .values_list("code", flat=True))
    assert "bc_mkt" in cua_mkt
    assert "bc_sale" not in cua_mkt

    cua_sale = set(daily_service.forms_for(nguoi_dung["staff_sale_1"])
                   .values_list("code", flat=True))
    assert "bc_sale" in cua_sale
    assert "bc_mkt" not in cua_sale


def test_man_hinh_nop_chi_hien_bieu_mau_cua_bo_phan(client, bm_mkt, bm_sale, nguoi_dung):
    """AC-4.1 — Màn hình nộp chỉ liệt kê biểu mẫu của bộ phận mình"""
    client.force_login(nguoi_dung["staff_mkt"])
    noi_dung = client.get("/bao-cao/").content.decode()
    assert "Báo cáo mkt" in noi_dung
    assert "Báo cáo sale" not in noi_dung


# ══ Thời điểm nộp — FR-4.2 ═════════════════════════════════════════

def test_ghi_nhan_thoi_diem_nop(bm_mkt, nguoi_dung):
    """AC-4.2 — Nộp báo cáo thì thời điểm nộp được ghi lại chính xác"""
    truoc = timezone.now()
    bc = _nop(bm_mkt, nguoi_dung["staff_mkt"])
    sau = timezone.now()

    assert truoc <= bc.submitted_at <= sau
    assert bc.report_date == NGAY          # ngày báo cáo khác thời điểm nộp


def test_thoi_diem_nop_luu_gio_quoc_te(bm_mkt, nguoi_dung):
    """AC-9.4 — Lưu theo giờ quốc tế, hiển thị theo giờ Việt Nam — BR-7"""
    bc = _nop(bm_mkt, nguoi_dung["staff_mkt"])
    assert timezone.is_aware(bc.submitted_at)
    assert bc.submitted_at.utcoffset().total_seconds() == 0


def test_noi_dung_ghi_vao_bang_dich(bm_mkt, nguoi_dung):
    """AC-8.3 — Nội dung báo cáo ghi vào đúng bảng đích, cột tính sẵn tự tính"""
    bc = _nop(bm_mkt, nguoi_dung["staff_mkt"], so_mess="4303", so_don="291")

    assert bc.record.table == bm_mkt.table
    assert bc.record.data["so_mess"] == 4303
    assert bc.record.data["ti_le_chot"] == "6.76"


def test_thieu_truong_bat_buoc_thi_khong_nop_duoc(bm_mkt, nguoi_dung):
    """AC-8.2 — Trường bắt buộc bỏ trống thì không nộp được"""
    with pytest.raises(BusinessError) as loi:
        daily_service.submit(
            bm_mkt, {"ngay": "", "so_mess": "10"},
            report_date=NGAY, actor=nguoi_dung["staff_mkt"],
        )
    assert "Ngày" in str(loi.value)
    assert not DailyReport.objects.exists()


# ══ Khoá sau khi nộp — FR-4.4, BR-2 ════════════════════════════════

def test_khong_nop_de_len_ban_da_co(bm_mkt, nguoi_dung):
    """AC-4.4 — Không nộp đè lên báo cáo đã có của cùng ngày"""
    _nop(bm_mkt, nguoi_dung["staff_mkt"])

    with pytest.raises(BusinessError) as loi:
        _nop(bm_mkt, nguoi_dung["staff_mkt"])
    assert "đã nộp" in str(loi.value)
    assert DailyReport.objects.count() == 1


def test_sua_bao_cao_bang_ma_thi_no_ngay(bm_mkt, nguoi_dung):
    """AC-4.4 — Sửa báo cáo đã nộp bằng mã cũng bị chặn, không chỉ trên giao diện"""
    bc = _nop(bm_mkt, nguoi_dung["staff_mkt"])
    bc.report_date = date(2026, 8, 1)

    with pytest.raises(RuntimeError):
        bc.save()


def test_khong_co_duong_dan_sua_bao_cao(client, bm_mkt, nguoi_dung):
    """AC-4.4 — Không có đường dẫn sửa báo cáo, gọi thẳng cũng không có gì"""
    bc = _nop(bm_mkt, nguoi_dung["staff_mkt"])
    client.force_login(nguoi_dung["staff_mkt"])

    for duong_dan in (f"/bao-cao/{bc.pk}/sua/", f"/bao-cao/{bc.pk}/cap-nhat/"):
        assert client.get(duong_dan).status_code == 404


def test_nop_lai_ngay_khac_thi_duoc(bm_mkt, nguoi_dung):
    """FR-4.2 — Chiều được phép: nộp cho ngày khác thì bình thường"""
    _nop(bm_mkt, nguoi_dung["staff_mkt"], ngay=date(2026, 8, 28))
    _nop(bm_mkt, nguoi_dung["staff_mkt"], ngay=date(2026, 8, 29))
    assert DailyReport.objects.count() == 2


def test_bo_bao_cao_la_danh_dau_khong_xoa_cung(bm_mkt, nguoi_dung):
    """AC-9.1 — Bỏ báo cáo là đánh dấu xoá, bản ghi vẫn còn trong cơ sở dữ liệu"""
    bc = _nop(bm_mkt, nguoi_dung["staff_mkt"])
    daily_service.withdraw(bc, actor=nguoi_dung["staff_mkt"])

    assert not DailyReport.objects.filter(pk=bc.pk).exists()
    con = DailyReport.all_objects.get(pk=bc.pk)
    assert con.deleted_at is not None
    assert con.record.data["so_mess"] == 1000      # nội dung cũ vẫn nguyên


def test_bo_roi_nop_lai_duoc(bm_mkt, nguoi_dung):
    """BR-2 — Bỏ bản cũ rồi nộp lại được, và là một bản ghi mới"""
    cu = _nop(bm_mkt, nguoi_dung["staff_mkt"])
    daily_service.withdraw(cu, actor=nguoi_dung["staff_mkt"])
    moi = _nop(bm_mkt, nguoi_dung["staff_mkt"])

    assert moi.pk != cu.pk
    assert moi.submitted_at >= cu.submitted_at


# ══ Xem lại và phạm vi quyền — FR-4.3, FR-4.5 ══════════════════════

def test_staff_chi_thay_bao_cao_cua_minh(bm_sale, nguoi_dung):
    """AC-4.3 — Nhân viên xem lại được báo cáo cũ của chính mình, và chỉ của mình"""
    _nop(bm_sale, nguoi_dung["staff_sale_1"])
    _nop(bm_sale, nguoi_dung["staff_sale_2"])

    thay = daily_service.history(nguoi_dung["staff_sale_1"])
    assert thay.count() == 1
    assert thay.first().created_by == nguoi_dung["staff_sale_1"]


def test_leader_thay_bao_cao_ca_team(bm_sale, teams, nguoi_dung):
    """AC-4.5 — Leader xem được báo cáo của người trong team mình"""
    _nop(bm_sale, nguoi_dung["staff_sale_1"])
    thay = daily_service.history(nguoi_dung["leader_sale_1"])
    assert thay.filter(created_by=nguoi_dung["staff_sale_1"]).exists()


def test_leader_khong_thay_bao_cao_team_khac(bm_sale, nguoi_dung):
    """AC-3.3 — Chiều bị từ chối: Leader không thấy báo cáo của team khác"""
    _nop(bm_sale, nguoi_dung["staff_sale_2"])
    thay = daily_service.history(nguoi_dung["leader_sale_1"])
    assert not thay.filter(created_by=nguoi_dung["staff_sale_2"]).exists()


def test_manager_thay_bao_cao_ca_bo_phan(bm_sale, nguoi_dung):
    """AC-3.4 — Manager thấy báo cáo của toàn bộ bộ phận mình"""
    _nop(bm_sale, nguoi_dung["staff_sale_1"])
    _nop(bm_sale, nguoi_dung["staff_sale_2"])
    assert daily_service.history(nguoi_dung["manager_sale"]).count() == 2


def test_manager_khong_thay_bao_cao_bo_phan_khac(bm_mkt, bm_sale, nguoi_dung):
    """AC-3.5 — Manager không thấy báo cáo của bộ phận khác"""
    _nop(bm_mkt, nguoi_dung["staff_mkt"])
    assert not daily_service.history(nguoi_dung["manager_sale"]).exists()


def test_goi_thang_bao_cao_ngoai_pham_vi_bi_chan(client, bm_mkt, nguoi_dung):
    """AC-3.7 — Gọi thẳng đường dẫn xem báo cáo ngoài phạm vi vẫn bị chặn"""
    bc = _nop(bm_mkt, nguoi_dung["staff_mkt"])
    client.force_login(nguoi_dung["staff_sale_1"])
    assert client.get(f"/bao-cao/{bc.pk}/").status_code == 404


def test_chi_nguoi_nop_moi_bo_duoc_bao_cao(client, bm_sale, nguoi_dung):
    """BR-2 — Người khác không bỏ được báo cáo của mình, kể cả Manager"""
    bc = _nop(bm_sale, nguoi_dung["staff_sale_1"])
    client.force_login(nguoi_dung["manager_sale"])

    client.post(f"/bao-cao/{bc.pk}/bo/")
    assert DailyReport.objects.filter(pk=bc.pk).exists()


# ══ Nhật ký và hiệu năng ═══════════════════════════════════════════

def test_nop_bao_cao_sinh_mot_dong_nhat_ky(bm_mkt, nguoi_dung):
    """AC-9.2 — Nộp báo cáo sinh một dòng nhật ký"""
    truoc = AuditLog.objects.filter(action=AuditAction.CREATE).count()
    _nop(bm_mkt, nguoi_dung["staff_mkt"])
    ds = AuditLog.objects.filter(action=AuditAction.CREATE)

    # Một dòng cho bản ghi dữ liệu, một dòng cho lần nộp
    assert ds.count() == truoc + 2
    assert "Nộp báo cáo" in ds.latest("created_at").detail


def test_man_hinh_lich_su_khong_qua_muoi_lenh_truy_van(
        client, bm_sale, nguoi_dung, django_assert_max_num_queries):
    """AC-10.2 — Màn hình lịch sử chạy không quá 10 lệnh truy vấn"""
    for i in range(28, 31):
        _nop(bm_sale, nguoi_dung["staff_sale_1"], ngay=date(2026, 8, i))

    client.force_login(nguoi_dung["manager_sale"])
    client.get("/bao-cao/lich-su/")          # lượt đầu ghi mốc phiên
    with django_assert_max_num_queries(10):
        assert client.get("/bao-cao/lich-su/").status_code == 200
