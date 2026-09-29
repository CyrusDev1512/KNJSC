"""ADR-037 — mã nhân sự theo quy ước THUANLT: gợi ý, duy nhất, cố định, đăng nhập, hiển thị,
lệnh gán mã cũ. Mỗi bài kiểm cả chiều được phép lẫn chiều bị từ chối."""
from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from core.constants import Rank
from core.exceptions import BusinessError
from core.identity import employee_code, identity_label
from core.models import AuditLog
from forms_builder.meaning import FieldType, Meaning
from forms_builder.models import ColumnDef, DataRecord, TableDef
from org.models import UserProfile
from org.services import account_service, staff_code_service

pytestmark = pytest.mark.django_db


def test_quy_tac_ma_nhan_su(make_user, departments, nguoi_dung):
    """AC-37.1 — Mã = TÊN + chữ đầu họ + chữ đầu tên đệm, viết hoa không dấu (Lê Thưởng Thuận → THUANLT);
    họ tên không cho mã hợp lệ thì lấy chữ số của tên đăng nhập; hồ sơ lưu mà rỗng thì tự gán, nên
    mọi hồ sơ đều có mã hợp lệ và `employee_code` trả mã, không còn trả tên đăng nhập"""
    assert staff_code_service.base_code("Lê Thưởng Thuận") == "THUANLT"
    assert staff_code_service.base_code("Nguyễn Thị Hà") == "HANT"
    assert staff_code_service.base_code("Đỗ Thu Trang") == "TRANGDT"
    assert staff_code_service.base_code("Hà") == "HA"
    assert staff_code_service.base_code("Staff Sale 1") == ""          # từ cuối là số → không hợp lệ
    assert staff_code_service.suggest("Nhan Vien 9", "nhan_vien_9") == "NHANVIEN9"
    assert staff_code_service.suggest("", "123") == "NV123"
    assert staff_code_service.normalise(" thuận lt ") == "THUANLT"
    with pytest.raises(BusinessError):
        staff_code_service.validate("1ABC")
    for user in nguoi_dung.values():
        assert staff_code_service.CODE_PATTERN.match(user.profile.staff_code), user.username
        assert employee_code(user) == user.profile.staff_code != user.username
    thuan = make_user("thuan.le", Rank.STAFF, departments["sale"])
    UserProfile.objects.filter(pk=thuan.profile.pk).update(staff_code="")   # như hồ sơ trước ADR-037
    thuan.profile.refresh_from_db()
    thuan.profile.full_name = "Lê Thưởng Thuận"
    thuan.profile.save()
    assert thuan.profile.staff_code == "THUANLT"
    assert identity_label(thuan) == "THUANLT · Lê Thưởng Thuận"
    assert identity_label(nguoi_dung["admin"]).startswith(employee_code(nguoi_dung["admin"]) + " · ")


def test_trung_ma_thi_them_so(departments, nguoi_dung):
    """AC-37.2 — Hai người cùng họ tên: THUANLT rồi THUANLT2; mã trùng tên đăng nhập của người khác
    cũng phải nhảy số (tài khoản mới dùng mã làm tên đăng nhập); gán tay mã đã có người dùng bị từ chối"""
    admin = nguoi_dung["admin"]
    a = account_service.create_account(username="thuan1", email="a@x.vn", full_name="Lê Thưởng Thuận",
                                       department=departments["sale"], actor=admin)
    b = account_service.create_account(username="thuan2", email="b@x.vn", full_name="Lê Thưởng Thuận",
                                       department=departments["sale"], actor=admin)
    assert (a.staff_code, b.staff_code) == ("THUANLT", "THUANLT2")
    get_user_model().objects.create_user(username="ThuanLT3", email="c@x.vn", password="x-mat-khau-dai-1")
    assert staff_code_service.suggest("Lê Thưởng Thuận") == "THUANLT4"
    c = account_service.create_account(username="thuan4", email="d@x.vn", full_name="Lê Thưởng Thuận",
                                       department=departments["sale"], actor=admin)
    assert c.staff_code == "THUANLT4"
    UserProfile.objects.filter(pk=c.pk).update(staff_code="")
    c.refresh_from_db()
    with pytest.raises(BusinessError):
        staff_code_service.assign(c, "THUANLT", actor=admin)
    c.refresh_from_db()
    assert c.staff_code == ""


def test_ma_co_dinh_va_ai_duoc_gan(client, departments, nguoi_dung):
    """AC-37.3 — Mã đã gán thì không đổi được (lưu model hay form sửa hồ sơ đều giữ nguyên); hồ sơ cũ
    còn rỗng thì Admin gán một lần qua form và ghi nhật ký; gợi ý mã chỉ Admin gọi được, Staff và
    Manager bị từ chối"""
    admin, staff = nguoi_dung["admin"], nguoi_dung["staff_sale_1"]
    ma_cu = staff.profile.staff_code
    staff.profile.staff_code = "KHACHAN"
    with pytest.raises(BusinessError):
        staff.profile.save()
    staff.profile.refresh_from_db()
    assert staff.profile.staff_code == ma_cu
    client.force_login(admin)
    du_lieu = {"full_name": staff.profile.full_name, "staff_code": "KHACHAN", "rank": Rank.STAFF,
               "department": departments["sale"].pk, "team": staff.profile.team_id}
    assert client.post(f"/nhan-su/{staff.profile.pk}/sua/", du_lieu).status_code == 302
    staff.profile.refresh_from_db()
    assert staff.profile.staff_code == ma_cu            # ô bị khoá, giá trị gửi lên bị bỏ qua
    # Hồ sơ cũ chưa có mã (như dữ liệu trước ADR-037): Admin gán được đúng một lần
    UserProfile.objects.filter(pk=staff.profile.pk).update(staff_code="")
    assert client.post(f"/nhan-su/{staff.profile.pk}/sua/", {**du_lieu, "staff_code": "hant"}).status_code == 302
    staff.profile.refresh_from_db()
    assert staff.profile.staff_code == "HANT"
    assert AuditLog.objects.filter(target_type="UserProfile", detail__contains="Mã nhân sự").exists()
    assert client.get("/nhan-su/goi-y-ma/", {"ho_ten": "Lê Thưởng Thuận"}).json() == {"ma": "THUANLT"}
    for role in ("staff_sale_1", "manager_sale"):
        client.force_login(nguoi_dung[role])
        assert client.get("/nhan-su/goi-y-ma/", {"ho_ten": "Lê Thưởng Thuận"}).status_code == 403


def test_tai_khoan_moi_dang_nhap_bang_ma(client, departments, nguoi_dung):
    """AC-37.4 — Tạo tài khoản để trống tên đăng nhập và mã: mã gợi ý từ họ tên và tên đăng nhập = mã;
    đăng nhập bằng mã gõ hoa hay thường đều vào, sai mật khẩu vẫn bị chặn; tài khoản cũ giữ tên đăng
    nhập của mình"""
    client.force_login(nguoi_dung["admin"])
    response = client.post("/nhan-su/moi/", {
        "full_name": "Lê Thưởng Thuận", "staff_code": "", "username": "",
        "rank": Rank.STAFF, "department": departments["mkt"].pk, "password": "MatKhauTam-2026!",
    })
    assert response.status_code == 200 and response.context["created_profile"].staff_code == "THUANLT"
    user = get_user_model().objects.get(username="THUANLT")
    assert "THUANLT" in response.content.decode()
    client.logout()
    assert client.login(username="thuanlt", password="MatKhauTam-2026!")
    client.logout()
    assert client.login(username="THUANLT", password="MatKhauTam-2026!")
    client.logout()
    assert not client.login(username="thuanlt", password="sai-mat-khau-999")
    # Tài khoản mới có thể tự đặt tên đăng nhập khác mã; trùng tên đăng nhập bị từ chối
    client.force_login(nguoi_dung["admin"])
    response = client.post("/nhan-su/moi/", {
        "full_name": "Lê Thưởng Thuận", "staff_code": "", "username": "thuan.le",
        "rank": Rank.STAFF, "department": departments["mkt"].pk, "password": "MatKhauTam-2026!",
    })
    assert response.status_code == 200 and response.context["created_profile"].staff_code == "THUANLT2"
    assert response.context["created_profile"].user.username == "thuan.le"
    response = client.post("/nhan-su/moi/", {
        "full_name": "Ai Đó", "staff_code": "", "username": "thuanlt",
        "rank": Rank.STAFF, "department": departments["mkt"].pk, "password": "MatKhauTam-2026!",
    })
    assert response.status_code == 200 and response.context["form"].errors
    assert nguoi_dung["staff_sale_1"].username == "staff_sale_1"   # người cũ giữ tên đăng nhập


def test_ma_truoc_ten_sau_o_danh_sach_va_o_chon(client, departments, nguoi_dung):
    """AC-37.5 — Danh sách nhân sự hiện cột Mã và tìm được theo mã; ô Người bán gợi ý mã (không phải
    họ tên); nhãn danh tính là `MÃ · Họ tên`; Staff vẫn không vào được danh sách nhân sự"""
    from forms_builder.services import choice_service

    manager = nguoi_dung["manager_sale"]
    manager.profile.full_name = "Lê Quốc Bảo"
    manager.profile.save(update_fields=["full_name"])
    assert identity_label(manager) == employee_code(manager) + " · Lê Quốc Bảo"
    client.force_login(nguoi_dung["admin"])
    html = client.get("/nhan-su/", {"tim": employee_code(manager).lower()}).content.decode()
    assert "<th>Mã nhân sự</th>" in html and employee_code(manager) in html and "staff_sale_2" not in html
    bang = TableDef.objects.create(name="Bảng Sale", code="bang_sale_ma", department=departments["sale"],
                                   created_by=manager)
    # Ô chọn mang nhãn Người bán (sổ theo nhãn chỉ áp cho cột Chọn một) gợi ý mã, không gợi ý họ tên
    cot = ColumnDef.objects.create(table=bang, name="Người bán", code="nguoi_ban",
                                   field_type=FieldType.CHOICE, meaning=Meaning.SELLER)
    goi_y = choice_service.options_for(cot).options()
    assert employee_code(manager) in goi_y and "Lê Quốc Bảo" not in goi_y
    client.force_login(nguoi_dung["staff_sale_1"])
    assert client.get("/nhan-su/", {"tim": employee_code(manager)}).status_code == 403


def test_lenh_gan_ma_nhan_su_cu(departments, nguoi_dung):
    """AC-37.6 — `gan_ma_nhan_su_cu`: xem trước không ghi gì; chạy thật gán mã cho hồ sơ rỗng, đổi ô
    danh tính khớp đúng tên đăng nhập (cả `val_seller`) và giữ giá trị lạ; chạy lần hai không đổi thêm"""
    staff, other = nguoi_dung["staff_sale_1"], nguoi_dung["staff_sale_2"]
    UserProfile.objects.filter(pk=staff.profile.pk).update(staff_code="")
    bang = TableDef.objects.create(name="Bảng cũ", code="bang_cu", department=departments["sale"],
                                   created_by=nguoi_dung["manager_sale"])
    ColumnDef.objects.create(table=bang, name="Người bán", code="nguoi_ban",
                             field_type=FieldType.TEXT, meaning=Meaning.SELLER)
    cua_staff = DataRecord.objects.create(table=bang, department=bang.department, created_by=staff,
                                          data={"nguoi_ban": "staff_sale_1"}, val_seller="staff_sale_1")
    cua_other = DataRecord.objects.create(table=bang, department=bang.department, created_by=other,
                                          data={"nguoi_ban": "staff_sale_2"}, val_seller="staff_sale_2")
    la = DataRecord.objects.create(table=bang, department=bang.department, created_by=other,
                                   data={"nguoi_ban": "Ai đó"}, val_seller="Ai đó")
    out = StringIO()
    call_command("gan_ma_nhan_su_cu", stdout=out)
    assert "XEM TRUOC" in out.getvalue() and "STAFFSALE1" in out.getvalue()
    assert UserProfile.objects.get(pk=staff.profile.pk).staff_code == ""
    assert DataRecord.objects.get(pk=cua_staff.pk).data["nguoi_ban"] == "staff_sale_1"

    out = StringIO()
    call_command("gan_ma_nhan_su_cu", "--xac-nhan", stdout=out)
    assert UserProfile.objects.get(pk=staff.profile.pk).staff_code == "STAFFSALE1"
    cua_staff.refresh_from_db(); cua_other.refresh_from_db(); la.refresh_from_db()
    assert cua_staff.data["nguoi_ban"] == "STAFFSALE1" and cua_staff.val_seller == "STAFFSALE1"
    assert cua_other.data["nguoi_ban"] == employee_code(other) and cua_other.val_seller == employee_code(other)
    assert la.data["nguoi_ban"] == "Ai đó" and la.val_seller == "Ai đó"
    assert "Tong dong doi o danh tinh: 2" in out.getvalue()
    assert AuditLog.objects.filter(actor_label="gan_ma_nhan_su_cu", target_type="TableDef").count() == 1

    out = StringIO()
    call_command("gan_ma_nhan_su_cu", "--xac-nhan", stdout=out)
    assert "Tong dong doi o danh tinh: 0" in out.getvalue() or "Khong co ten dang nhap" in out.getvalue()
    assert AuditLog.objects.filter(actor_label="gan_ma_nhan_su_cu", target_type="TableDef").count() == 1
