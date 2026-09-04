"""Dựng dữ liệu mẫu cho một máy mới.

Cơ sở dữ liệu không theo kho mã. Không có lệnh này thì `docker compose up`
trên máy mới cho ra hệ thống trống trơn — **không có tài khoản nào để đăng
nhập**, kể cả quản trị viên.

Đây là việc số 1 trong danh sách kiểm thủ công ở `docs/04` mục 11:
*"Cài đặt từ đầu trên máy sạch, chạy tới màn hình đăng nhập"*.

    docker compose -f deploy/docker-compose.yml exec web python manage.py du_lieu_mau

**Chạy lại được nhiều lần**: đã có thì bỏ qua, không tạo trùng và không ghi đè
dữ liệu ai đã nhập.

**Chỉ chạy ở môi trường phát triển.** Lệnh này tạo tài khoản với mật khẩu ai
cũng biết; chạy trên máy chủ thật là mở toang cửa. Muốn chạy khi `DEBUG` tắt
thì phải ghi rõ `--dong-y-chay-that`.
"""
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from core.constants import Currency, Rank
from orders.constants import WAYBILL_DEPARTMENT_CODE, WAYBILL_DEPARTMENT_NAME

#: Mật khẩu chung cho mọi tài khoản mẫu. Chỉ dùng ở máy phát triển.
MAT_KHAU_MAU = "MatKhauTam-2026"

#: Ba bộ phận. Bộ phận Vận đơn lấy tên từ `orders.constants` để khớp với
#: lệnh `tao_bang_van_don`.
BO_PHAN = [
    ("Sale", "sale"),
    ("Marketing", "marketing"),
    (WAYBILL_DEPARTMENT_NAME, WAYBILL_DEPARTMENT_CODE),
]

#: Hai team, đều thuộc Sale — đủ để thử phạm vi quyền của Leader.
TEAM = [("Sale 1", "sale"), ("Sale 2", "sale")]

#: (tên đăng nhập, họ tên, cấp bậc, mã bộ phận, tên team, buộc đổi mật khẩu)
TAI_KHOAN = [
    ("quantri",     "Quản trị viên",  Rank.ADMIN,   None,        None,     False),
    ("sale.manager", "Lê Quốc Bảo",   Rank.MANAGER, "sale",      None,     False),
    ("sale.leader",  "Trần Văn Dũng", Rank.LEADER,  "sale",      "Sale 1", False),
    ("sale.leader2", "Phạm Quốc Anh", Rank.LEADER,  "sale",      "Sale 2", False),
    ("sale.staff",   "Nguyễn Thị Hà", Rank.STAFF,   "sale",      "Sale 1", False),
    ("sale.staff2",  "Lý Thu Hằng",   Rank.STAFF,   "sale",      "Sale 2", False),
    # Tài khoản mới, giữ nguyên cờ buộc đổi mật khẩu để thử luồng FR-1.4
    ("sale.moi",     "Nhân viên mới", Rank.STAFF,   "sale",      None,     True),
    ("mkt.manager",  "Đỗ Thu Trang",  Rank.MANAGER, "marketing", None,     False),
    ("mkt.leader",   "Vũ Hoài Nam",   Rank.LEADER,  "marketing", None,     False),
    ("mkt.staff",    "Phạm Minh Anh", Rank.STAFF,   "marketing", None,     False),
    ("vd.manager",   "Bùi Kim Chi",   Rank.MANAGER, "van-don",   None,     False),
    ("vd.staff",     "Hoàng Văn Tú",  Rank.STAFF,   "van-don",   None,     False),
]

#: Bảng Báo cáo Marketing, dựng đúng theo sheet BC MKT trong tệp thật.
#: (nhãn, tên kỹ thuật, kiểu, nhãn ý nghĩa)
COT_BC_MKT = [
    ("Ngày", "ngay", "date", "date"),
    ("Marketer", "marketer", "text", "seller"),
    ("Sản phẩm", "san_pham", "text", "product"),
    ("Số Mess", "so_mess", "integer", ""),
    ("CPQC", "cpqc", "money", ""),
    ("Số đơn", "so_don", "integer", ""),
    ("Doanh số", "doanh_so", "money", "revenue"),
]

#: Bốn cột tính sẵn — đúng bốn công thức trong tệp thật của khách hàng.
#: (nhãn, tên kỹ thuật, phép tính, toán hạng A, toán hạng B, số chữ số thập phân)
COT_TINH_BC_MKT = [
    ("CPO", "cpo", "divide", "cpqc", "so_don", 0),
    ("Giá Mess", "gia_mess", "divide", "cpqc", "so_mess", 0),
    ("AOV", "aov", "divide", "doanh_so", "so_don", 0),
    ("Tỉ lệ chốt", "ti_le_chot", "percent", "so_don", "so_mess", 2),
]

#: Số liệu thật lấy từ sheet BC MKT. Dòng đầu cho CPO 1.506.687 và tỉ lệ chốt
#: 6,76% — đúng bằng con số trong bản của khách hàng.
DONG_BC_MKT = [
    ("Nguyễn Quang Minh", "Máy massage HM-200", 4303, "438446060", 291, "1425942850"),
    ("Trần Thu Hà", "Đèn ngủ cảm ứng", 2180, "196300000", 148, "612400000"),
    ("Nguyễn Quang Minh", "Máy massage HM-200", 3907, "402118000", 264, "1288900000"),
    ("Lê Hoàng Nam", "Bộ nồi chống dính", 1640, "151200000", 96, "441600000"),
    ("Trần Thu Hà", "Đèn ngủ cảm ứng", 2455, "221000000", 171, "708300000"),
]

SAN_PHAM = [
    ("Máy massage cầm tay HM-200", "hm200"),
    ("Đèn ngủ cảm ứng", "den_ngu"),
    ("Nồi chiên không dầu 5L", "noi_chien"),
]


class Command(BaseCommand):
    help = "Dựng dữ liệu mẫu để dùng thử trên máy mới. Chạy lại nhiều lần được."

    def add_arguments(self, parser):
        parser.add_argument(
            "--mat-khau", default=MAT_KHAU_MAU,
            help=f"Mật khẩu cho mọi tài khoản mẫu. Mặc định {MAT_KHAU_MAU}",
        )
        parser.add_argument(
            "--dong-y-chay-that", action="store_true",
            help="Cho phép chạy khi DEBUG tắt. Chỉ dùng khi biết chắc mình làm gì.",
        )

    def handle(self, *args, **o):
        if not settings.DEBUG and not o["dong_y_chay_that"]:
            raise CommandError(
                "DEBUG đang tắt. Lệnh này tạo tài khoản với mật khẩu ai cũng biết, "
                "chạy trên máy chủ thật là mở toang cửa.\n"
                "Chắc chắn muốn chạy thì thêm --dong-y-chay-that."
            )

        self.mat_khau = o["mat_khau"]
        self.da_tao = {"bộ phận": 0, "team": 0, "tài khoản": 0,
                       "bảng": 0, "biểu mẫu": 0, "sản phẩm": 0, "dòng dữ liệu": 0}

        bo_phan = self._bo_phan()
        team = self._team(bo_phan)
        nguoi = self._tai_khoan(bo_phan, team)
        self._bang_van_don(nguoi["quantri"])
        self._bao_cao_marketing(bo_phan, nguoi)
        self._san_pham()

        self._bao_cao_ket_qua(nguoi)

    # ── Cơ cấu tổ chức ──

    def _bo_phan(self):
        from org.models import Department

        ket_qua = {}
        for ten, ma in BO_PHAN:
            bp, moi = Department.objects.get_or_create(code=ma, defaults={"name": ten})
            ket_qua[ma] = bp
            self.da_tao["bộ phận"] += int(moi)
        return ket_qua

    def _team(self, bo_phan):
        from org.models import Team

        ket_qua = {}
        for ten, ma_bo_phan in TEAM:
            t, moi = Team.objects.get_or_create(
                name=ten, department=bo_phan[ma_bo_phan])
            ket_qua[ten] = t
            self.da_tao["team"] += int(moi)
        return ket_qua

    @transaction.atomic
    def _tai_khoan(self, bo_phan, team):
        """Tạo tài khoản qua tầng dịch vụ để nhật ký hoạt động có dấu vết."""
        from django.contrib.auth import get_user_model

        from org.services import account_service

        User = get_user_model()
        ket_qua = {}
        for ten_dn, ho_ten, cap_bac, ma_bp, ten_team, doi_mk in TAI_KHOAN:
            co_san = User.objects.filter(username=ten_dn).first()
            if co_san is not None:
                ket_qua[ten_dn] = co_san
                continue

            ho_so = account_service.create_account(
                username=ten_dn, email=f"{ten_dn}@kimngan.vn", full_name=ho_ten,
                rank=cap_bac,
                department=bo_phan.get(ma_bp) if ma_bp else None,
                team=team.get(ten_team) if ten_team else None,
                password=self.mat_khau,
            )
            # `create_account` luôn bật cờ buộc đổi mật khẩu (FR-1.4). Với dữ
            # liệu mẫu thì tắt đi cho đỡ vướng, trừ tài khoản `sale.moi` cố ý
            # giữ lại để thử đúng luồng đó.
            if ho_so.must_change_password != doi_mk:
                ho_so.must_change_password = doi_mk
                ho_so.save(update_fields=["must_change_password"])
            ket_qua[ten_dn] = ho_so.user
            self.da_tao["tài khoản"] += 1

        # Gán trưởng nhóm cho hai team Sale
        for ten_team, ten_dn in (("Sale 1", "sale.leader"), ("Sale 2", "sale.leader2")):
            t = team[ten_team]
            if t.leader_id is None:
                t.leader = ket_qua[ten_dn]
                t.save(update_fields=["leader"])
        return ket_qua

    # ── Bảng và biểu mẫu ──

    def _bang_van_don(self, quan_tri):
        from forms_builder.models import TableDef
        from orders.constants import WAYBILL_TABLE_CODE
        from orders.services import dispatch_service

        da_co = TableDef.all_objects.filter(code=WAYBILL_TABLE_CODE).exists()
        bang = dispatch_service.ensure_waybill_table(actor=quan_tri)
        self.da_tao["bảng"] += int(not da_co)
        return bang

    @transaction.atomic
    def _bao_cao_marketing(self, bo_phan, nguoi):
        """Bảng Báo cáo Marketing, biểu mẫu nộp báo cáo, và số liệu thật."""
        from forms_builder.models import FieldDef, TableDef
        from forms_builder.services import form_service, record_service, table_service

        if TableDef.all_objects.filter(code="bao_cao_mkt").exists():
            return

        ql, nv = nguoi["mkt.manager"], nguoi["mkt.staff"]
        bp = bo_phan["marketing"]

        bang = table_service.create_table(
            name="Báo cáo Marketing", code="bao_cao_mkt",
            description="Dựng theo sheet BC MKT trong tệp thật của công ty.",
            department=bp, actor=ql,
        )
        self.da_tao["bảng"] += 1

        for i, (ten, ma, kieu, nhan) in enumerate(COT_BC_MKT):
            table_service.add_column(
                bang, actor=ql, name=ten, code=ma,
                field_type=kieu, meaning=nhan, order=i)
        for j, (ten, ma, phep, a, b, so_le) in enumerate(
                COT_TINH_BC_MKT, start=len(COT_BC_MKT)):
            table_service.add_column(
                bang, actor=ql, name=ten, code=ma, field_type="money", order=j,
                is_computed=True, compute_op=phep,
                compute_left=a, compute_right=b, compute_decimals=so_le)

        # Thư viện định nghĩa trường, rồi biểu mẫu nộp báo cáo ngày
        bieu_mau = form_service.create_form(
            name="Báo cáo Marketing ngày", code="bc_mkt_ngay",
            description="Điền cuối ngày. CPO và tỉ lệ chốt hệ thống tự tính.",
            department=bp, table=bang, actor=ql,
        )
        self.da_tao["biểu mẫu"] += 1
        for ten, ma, kieu, nhan in COT_BC_MKT:
            truong = FieldDef.objects.create(
                name=ten, code=ma, field_type=kieu, meaning=nhan, department=bp)
            form_service.add_field(
                bieu_mau, truong, column=bang.columns.get(code=ma),
                required=(ma in ("ngay", "marketer", "so_mess")), actor=ql)

        # Năm dòng số liệu thật, lùi dần từ hôm nay
        cac_cot = list(bang.columns.all())
        hom_nay = timezone.localdate()
        for i, (ai, sp, mess, cp, don, ds) in enumerate(DONG_BC_MKT):
            record_service.create_record(bang, {
                "ngay": (hom_nay - timedelta(days=i)).isoformat(),
                "marketer": ai, "san_pham": sp, "so_mess": mess,
                "cpqc": cp, "so_don": don, "doanh_so": ds,
            }, actor=nv, columns=cac_cot)
            self.da_tao["dòng dữ liệu"] += 1

    def _san_pham(self):
        from orders.models import Product, ProductGroup

        nhom, _ = ProductGroup.objects.get_or_create(name="Đồ gia dụng")
        for ten, ma in SAN_PHAM:
            _, moi = Product.objects.get_or_create(
                code=ma, defaults={"name": ten, "group": nhom, "unit": "cái"})
            self.da_tao["sản phẩm"] += int(moi)

    # ── Báo cáo kết quả ──

    def _bao_cao_ket_qua(self, nguoi):
        from forms_builder.models import DataRecord, TableDef

        da = ", ".join(f"{v} {k}" for k, v in self.da_tao.items() if v)
        self.stdout.write(self.style.SUCCESS(
            "Da tao: " + (da if da else "khong co gi moi, du lieu da day du")))
        self.stdout.write(
            f"Hien co: {TableDef.objects.count()} bang, "
            f"{DataRecord.objects.count()} dong, {len(nguoi)} tai khoan")
        self.stdout.write("")
        self.stdout.write("Dang nhap tai http://127.0.0.1:8020/ voi mat khau: "
                          + self.mat_khau)
        self.stdout.write("")
        for ten_dn, ho_ten, cap_bac, ma_bp, _, _ in TAI_KHOAN:
            self.stdout.write(
                f"  {ten_dn:14} {cap_bac:8} {ma_bp or 'moi bo phan':12} {ho_ten}")
