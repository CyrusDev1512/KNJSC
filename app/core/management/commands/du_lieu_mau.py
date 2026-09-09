"""Dựng dữ liệu mẫu cho một máy mới.

Cơ sở dữ liệu không theo kho mã. Không có lệnh này thì `docker compose up`
trên máy mới cho ra hệ thống trống trơn — **không có tài khoản nào để đăng
nhập**, kể cả quản trị viên.

Đây là việc số 1 trong danh sách kiểm thủ công ở `docs/04` mục 17:
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

from core.constants import Rank
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
    # Chọn một mang nhãn Sản phẩm: ô chọn lấy từ danh mục sản phẩm (FR-8.7)
    ("Sản phẩm", "san_pham", "choice", "product"),
    ("Số Mess", "so_mess", "integer", ""),
    ("CPQC", "cpqc", "money", ""),
    ("Số đơn", "so_don", "integer", ""),
    ("Doanh số", "doanh_so", "money", "revenue"),
]

#: Tài liệu mẫu — chỉ liên kết (tiêu đề, mục, người tải, mô tả) — ADR-017
TAI_LIEU_MAU = [
    ("Nội quy công ty 2026", "chung", "quantri", "Giờ làm, nghỉ phép, kỷ luật"),
    ("Sổ tay nhân viên mới", "chung", "quantri", "Đọc trong tuần đầu"),
    ("Quy trình chốt đơn và lên đơn", "sale", "sale.manager", "Kịch bản tư vấn, cách lên đơn"),
    ("Kế hoạch quảng cáo quý 4", "mkt", "mkt.manager", "Ngân sách và mục tiêu từng kênh"),
]

#: Việc mẫu — (tiêu đề, người tạo, người làm, ưu tiên, hạn lệch so với hôm nay, trạng thái)
CONG_VIEC_MAU = [
    ("Gọi lại 5 khách Canada chưa chốt", "sale.leader", "sale.staff", "cao", -1, "dang_lam"),
    ("Cập nhật giá sản phẩm mới lên bảng", "sale.manager", "sale.leader", "vua", 3, "moi"),
    ("Chốt đơn tồn của team 2", "sale.leader2", "sale.staff2", "vua", 2, "moi"),
    ("Lên kế hoạch quảng cáo tháng sau", "mkt.manager", "mkt.leader", "cao", 7, "moi"),
    ("Chụp ảnh sản phẩm đèn ngủ", "mkt.manager", "mkt.staff", "thap", -3, "xong"),
    ("Đối soát vận đơn tuần này", "vd.manager", "vd.staff", "vua", 1, "dang_lam"),
]

#: Ghi nhận mẫu, từ trên xuống (Q75) — (người ghi nhận, người được ghi nhận, giá trị, lời nhắn)
GHI_NHAN_MAU = [
    ("sale.leader", "sale.staff", "hop_tac",
     "Chốt đơn xong là gửi đủ địa chỉ và ghi chú giao hàng ngay, bên vận đơn không phải hỏi lại."),
    ("mkt.manager", "mkt.staff", "sang_tao", "Bộ ảnh đèn ngủ mới làm tỉ lệ chốt tăng rõ."),
    ("vd.manager", "vd.staff", "trach_nhiem", "Đối soát vận đơn tuần này xong trước hạn."),
    ("sale.leader2", "sale.staff2", "tan_tam", "Ở lại gọi thêm khách Canada tới tối để kịp đơn."),
]

#: Ngày sinh mẫu — `sale.staff` đúng hôm nay để Bảng tin có thiệp ngay khi dựng (FR-10.4)
NGAY_SINH_MAU = {
    "sale.staff": "hom-nay",
    "sale.staff2": (1998, 11, 20),
    "sale.leader": (1990, 3, 8),
    "mkt.staff": (1999, 7, 14),
    "mkt.manager": (1987, 12, 25),
    "vd.staff": (1996, 5, 2),
}

#: Bài mẫu trên Bảng tin — (tác giả, nội dung, ghim)
BAI_MAU = [
    ("quantri", "Chào mừng cả nhà đến với Bảng tin nội bộ KN JSC! Đây là nơi đăng thông báo, "
                "chia sẻ tin vui và chúc mừng nhau. Ai cũng đăng được; quản lý ghim bài quan trọng lên đầu.", True),
    ("sale.manager", "Tháng này team Sale chốt vượt mục tiêu 12%. Cảm ơn cả team đã gọi khách tới tối. "
                     "Thứ Hai tuần sau họp tổng kết lúc 9h sáng.", False),
    ("mkt.manager", "Bộ ảnh sản phẩm đèn ngủ mới đã lên. Team Sale lấy ảnh ở mục Tài liệu Marketing để gửi khách.", False),
    ("vd.manager", "Nhắc cả nhà: đơn Canada chốt sau 16h sẽ đi chuyến hôm sau. "
                   "Ghi rõ ghi chú giao hàng trên bảng vận đơn giúp bên mình.", False),
    ("sale.staff", "Hôm nay mình chốt được khách đầu tiên ở Philippines. Cảm ơn anh Dũng đã hướng dẫn kịch bản!", False),
]

#: Bình luận mẫu — (số thứ tự bài, người viết, nội dung)
BINH_LUAN_MAU = [
    (5, "sale.leader", "Giỏi lắm, giữ phong độ nhé!"),
    (5, "mkt.staff", "Chúc mừng Hà!"),
    (2, "sale.leader2", "Team 2 cũng đã sẵn sàng cho tháng sau."),
]

#: Lượt thích mẫu — (số thứ tự bài, người thích)
THICH_MAU = [
    (1, "sale.staff"), (1, "mkt.staff"), (1, "vd.staff"),
    (5, "sale.leader"), (5, "sale.manager"), (5, "mkt.staff"),
    (3, "sale.staff"),
]

#: Tài nguyên mẫu — (mục, tên, trạng thái, người giữ, mã bộ phận, ghi chú). Năm mục
#: mặc định lấy từ `resources.constants.DEFAULT_CATEGORIES`.
TAI_NGUYEN_MAU = [
    ("BM", "BM Kim Ngân 01", "dang_dung", "mkt.staff", "marketing", "Đang chạy 3 tài khoản QC"),
    ("BM", "BM Kim Ngân 02", "khoa", "mkt.leader", "marketing", "Bị khoá 03.09, đang kháng"),
    ("Via", "Via US 2019", "trong", None, None, "Via cổ, chưa gán ai"),
    ("Page", "Page KN Beauty CA", "dang_dung", "sale.staff", "sale", "Page bán hàng thị trường Canada"),
    ("Tài khoản QC", "TKQC 1023-55", "dang_dung", "mkt.staff", "marketing", "Ngưỡng 5.000.000"),
    ("SIM", "SIM Viettel 0987", "hong", "vd.staff", "van-don", "Đã báo nhà mạng"),
]

#: Bốn cột tính sẵn — đúng bốn công thức trong tệp thật của khách hàng.
#: (nhãn, tên kỹ thuật, phép tính, toán hạng A, toán hạng B, số chữ số thập phân)
COT_TINH_BC_MKT = [
    ("CPO", "cpo", "divide", "cpqc", "so_don", 0),
    ("Giá Mess", "gia_mess", "divide", "cpqc", "so_mess", 0),
    ("AOV", "aov", "divide", "doanh_so", "so_don", 0),
    ("Tỉ lệ chốt", "ti_le_chot", "percent", "so_don", "so_mess", 2),
]

#: Màu cột và ngưỡng cảnh báo mẫu — như bảng "Dữ liệu chi phí Ads" của người
#: dùng: tỉ lệ chốt tô vàng cả cột, CPO đỏ khi vượt 1.500.000 (FR-8.8)
MAU_COT_BC_MKT = {
    "ti_le_chot": {"highlight": "vang"},
    "cpo": {"highlight": "do", "alert_op": "gt", "alert_value": Decimal("1500000")},
}

#: Số liệu thật lấy từ sheet BC MKT. Dòng đầu cho CPO 1.506.687 và tỉ lệ chốt
#: 6,76% — đúng bằng con số trong bản của khách hàng. Tên sản phẩm phải khớp
#: danh mục `SAN_PHAM`, vì cột Sản phẩm là ô chọn chặt.
DONG_BC_MKT = [
    ("Nguyễn Quang Minh", "Máy massage cầm tay HM-200", 4303, "438446060", 291, "1425942850"),
    ("Trần Thu Hà", "Đèn ngủ cảm ứng", 2180, "196300000", 148, "612400000"),
    ("Nguyễn Quang Minh", "Máy massage cầm tay HM-200", 3907, "402118000", 264, "1288900000"),
    ("Lê Hoàng Nam", "Nồi chiên không dầu 5L", 1640, "151200000", 96, "441600000"),
    ("Trần Thu Hà", "Đèn ngủ cảm ứng", 2455, "221000000", 171, "708300000"),
]

SAN_PHAM = [
    ("Máy massage cầm tay HM-200", "hm200"),
    ("Đèn ngủ cảm ứng", "den_ngu"),
    ("Nồi chiên không dầu 5L", "noi_chien"),
    # Bảy sản phẩm của tệp vận đơn Canada thật — mỗi sản phẩm một cột số lượng
    # trên bảng vận đơn (Q39). Tên phải khớp tiêu đề cột trong tệp để nhập
    # `docs/tham-khao/vandon-mau.xlsx` không cần chỉnh sửa.
    ("Retinol Cream", "retinol-cream"),
    ("Retinol Serum", "retinol-serum"),
    ("Vitamin C Cream", "vitamin-c-cream"),
    ("Vitamin C Serum", "vitamin-c-serum"),
    ("Kem Chống Nắng", "kem-chong-nang"),
    ("Sữa Rửa Mặt", "sua-rua-mat"),
    ("Retinol Eye Serum", "retinol-eye-serum"),
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
                       "bảng": 0, "biểu mẫu": 0, "sản phẩm": 0, "dòng dữ liệu": 0,
                       "tài liệu": 0, "việc": 0, "đơn hàng": 0, "ghi nhận": 0,
                       "ngày sinh": 0, "bài": 0, "bình luận": 0, "lượt thích": 0,
                       "thiệp sinh nhật": 0, "mục tài nguyên": 0, "tài nguyên": 0}
        self.dat_lai_mat_khau = 0

        bo_phan = self._bo_phan()
        team = self._team(bo_phan)
        nguoi = self._tai_khoan(bo_phan, team)
        self._san_pham()                     # trước bảng vận đơn: cột sl_* theo sản phẩm
        self._bang_van_don(nguoi["quantri"])
        self._bao_cao_marketing(bo_phan, nguoi)
        self._thu_muc(nguoi)
        self._tai_lieu(bo_phan, nguoi)
        self._cong_viec(nguoi)
        # ADR-018: Vận đơn mới bắt đầu trống, không tạo đơn demo khi nạp mẫu.
        self._ghi_nhan(nguoi)
        self._ngay_sinh(nguoi)
        self._bang_tin(nguoi)
        self._tai_nguyen(bo_phan, nguoi)

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
            co_san = User.objects.filter(username=ten_dn).select_related("profile").first()
            if co_san is not None:
                # Tài khoản mẫu đã có từ lần chạy trước: đặt lại đúng mật khẩu
                # in ra cuối lệnh và mở khoá — không thì màn hình in một mật
                # khẩu mà cơ sở dữ liệu giữ một mật khẩu khác, đăng nhập hỏng
                # mà không ai hiểu vì sao (03.09.2026, máy Windows của người dùng)
                ho_so = getattr(co_san, "profile", None)
                if ho_so is not None:
                    account_service.reset_password(ho_so, self.mat_khau)
                    account_service.unlock_account(ho_so)
                    ho_so.must_change_password = doi_mk
                    ho_so.save(update_fields=["must_change_password"])
                    self.dat_lai_mat_khau += 1
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
    def _thu_muc(self, nguoi):
        """Mỗi bộ phận một thư mục chứa bảng của mình — để thanh bên Bảng tính
        có cây mà xem (ADR-010). Chạy lại được: đã có thì thôi."""
        from forms_builder.models import Folder, TableDef
        from forms_builder.services import folder_service
        from orders.constants import WAYBILL_TABLE_CODE

        for ten, ma_bang, ten_dn in (("Vận đơn 2026", WAYBILL_TABLE_CODE, "vd.manager"),
                                     ("Báo cáo 2026", "bao_cao_mkt", "mkt.manager")):
            bang = TableDef.objects.filter(code=ma_bang).select_related("department").first()
            if bang is None:
                continue
            thu_muc = Folder.objects.filter(department=bang.department, name=ten).first()
            if thu_muc is None:
                thu_muc = folder_service.create_folder(
                    name=ten, department=bang.department, actor=nguoi[ten_dn])
                self.da_tao.setdefault("thư mục", 0)
                self.da_tao["thư mục"] += 1
            if bang.folder_id is None:
                folder_service.move_table(bang, thu_muc, actor=nguoi[ten_dn])

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
                compute_left=a, compute_right=b, compute_decimals=so_le,
                **MAU_COT_BC_MKT.get(ma, {}))

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

    # ── Nhóm Nội bộ — ADR-017 ──

    def _tai_lieu(self, bo_phan, nguoi):
        """Ba mục và bốn tài liệu dạng liên kết. Không đưa tệp nhị phân vào kho mã."""
        from documents.models import DocumentCategory
        from documents.services import document_service

        if DocumentCategory.all_objects.exists():
            return
        chung = document_service.create_category(
            name="Quy định chung", department=None, actor=nguoi["quantri"])
        sale = document_service.create_category(
            name="Quy trình Sale", department=bo_phan["sale"], actor=nguoi["sale.manager"])
        mkt = document_service.create_category(
            name="Tài liệu Marketing", department=bo_phan["marketing"], actor=nguoi["mkt.manager"])
        for tieu_de, muc, ai, mo_ta in TAI_LIEU_MAU:
            document_service.upload_document(
                title=tieu_de, category={"chung": chung, "sale": sale, "mkt": mkt}[muc],
                link="https://docs.google.com/document/d/mau-" + muc, description=mo_ta,
                actor=nguoi[ai],
            )
            self.da_tao["tài liệu"] += 1

    def _cong_viec(self, nguoi):
        """Sáu việc mẫu: một quá hạn, một đã xong — FR-11."""
        from taskboard.constants import TaskStatus
        from taskboard.models import Task
        from taskboard.services import task_service

        if Task.all_objects.exists():
            return
        hom_nay = timezone.localdate()
        for tieu_de, ai_tao, ai_lam, uu_tien, lech, trang_thai in CONG_VIEC_MAU:
            viec = task_service.create_task(
                title=tieu_de, assignee=nguoi[ai_lam], priority=uu_tien,
                due_date=hom_nay + timedelta(days=lech) if lech is not None else None,
                actor=nguoi[ai_tao],
            )
            if trang_thai == TaskStatus.DANG_LAM:
                task_service.change_status(viec, TaskStatus.DANG_LAM, actor=nguoi[ai_lam])
            elif trang_thai == TaskStatus.XONG:
                task_service.change_status(viec, TaskStatus.DANG_LAM, actor=nguoi[ai_lam])
                task_service.change_status(viec, TaskStatus.XONG, actor=nguoi[ai_lam])
            self.da_tao["việc"] += 1

    def _ghi_nhan(self, nguoi):
        """Bốn ghi nhận chéo bộ phận, mỗi ghi nhận một sao — FR-12.1, FR-12.2."""
        from culture.models import Recognition
        from culture.services import recognition_service

        if Recognition.objects.exists():
            return
        for ai, nguoi_nhan, gia_tri, loi_nhan in GHI_NHAN_MAU:
            recognition_service.give_recognition(
                receiver=nguoi[nguoi_nhan], value=gia_tri, message=loi_nhan, actor=nguoi[ai])
            self.da_tao["ghi nhận"] += 1

    def _ngay_sinh(self, nguoi):
        """Ngày sinh cho vài hồ sơ mẫu — chỉ điền chỗ còn trống, không ghi đè."""
        hom_nay = timezone.localdate()
        for ten_dn, ngay in NGAY_SINH_MAU.items():
            ho_so = nguoi[ten_dn].profile
            if ho_so.birthday is not None:
                continue
            # 1996 nhuận, nên hôm nay là 29.02 vẫn đổi năm được
            ho_so.birthday = hom_nay.replace(year=1996) if ngay == "hom-nay" else date(*ngay)
            ho_so.save(update_fields=["birthday"])
            self.da_tao["ngày sinh"] += 1

    def _bang_tin(self, nguoi):
        """Năm bài (bài chào mừng ghim), bình luận, lượt thích, và thiệp sinh nhật
        hôm nay — cùng hàm với tác vụ nền 06:00 (FR-10.4)."""
        from feed.constants import PostKind
        from feed.models import Post
        from feed.services import post_service

        if not Post.all_objects.filter(kind=PostKind.BAI_VIET).exists():
            cac_bai = []
            for ai, noi_dung, ghim in BAI_MAU:
                bai = post_service.create_post(body=noi_dung, actor=nguoi[ai])
                if ghim:
                    post_service.pin_post(bai, actor=nguoi[ai])
                cac_bai.append(bai)
                self.da_tao["bài"] += 1
            for so, ai, noi_dung in BINH_LUAN_MAU:
                post_service.add_comment(cac_bai[so - 1], body=noi_dung, actor=nguoi[ai])
                self.da_tao["bình luận"] += 1
            for so, ai in THICH_MAU:
                post_service.toggle_like(cac_bai[so - 1], actor=nguoi[ai])
                self.da_tao["lượt thích"] += 1
        self.da_tao["thiệp sinh nhật"] += post_service.create_birthday_posts(timezone.localdate())

    def _tai_nguyen(self, bo_phan, nguoi):
        """Năm mục mặc định và sáu tài nguyên mẫu — FR-13. Ghi chú không có mật khẩu."""
        from resources.models import Resource, ResourceCategory
        from resources.services import resource_service

        self.da_tao["mục tài nguyên"] += resource_service.ensure_default_categories(actor=nguoi["quantri"])
        if Resource.all_objects.exists():
            return
        muc = {m.name: m for m in ResourceCategory.objects.all()}
        for ten_muc, ten, trang_thai, ai_giu, ma_bp, ghi_chu in TAI_NGUYEN_MAU:
            resource_service.create_resource(
                category=muc[ten_muc], name=ten, status=trang_thai, note=ghi_chu,
                holder=nguoi[ai_giu] if ai_giu else None,
                department=bo_phan[ma_bp] if ma_bp else None,
                actor=nguoi["quantri"],
            )
            self.da_tao["tài nguyên"] += 1

    # ── Báo cáo kết quả ──

    def _bao_cao_ket_qua(self, nguoi):
        from forms_builder.models import DataRecord, TableDef

        da = ", ".join(f"{v} {k}" for k, v in self.da_tao.items() if v)
        self.stdout.write(self.style.SUCCESS(
            "Da tao: " + (da if da else "khong co gi moi, du lieu da day du")))
        if self.dat_lai_mat_khau:
            self.stdout.write(
                f"Da dat lai mat khau va mo khoa {self.dat_lai_mat_khau} tai khoan mau co san")
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
