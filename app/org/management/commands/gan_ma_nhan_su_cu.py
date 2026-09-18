"""Gán mã nhân sự cho hồ sơ cũ và đổi tên đăng nhập → mã trong ô danh tính — ADR-037.

Chạy một lần khi phát hành (sau `migrate` org/0005). Mặc định chỉ **in ra** việc sẽ làm;
có `--xac-nhan` mới ghi. Chạy lại không đổi thêm gì.

    manage.py gan_ma_nhan_su_cu            # xem trước (như --thu)
    manage.py gan_ma_nhan_su_cu --xac-nhan # ghi thật

Việc 1: hồ sơ chưa có mã → gợi ý theo quy tắc THUANLT (`staff_code_service.suggest`).
Việc 2: mọi cột mang nhãn Người bán (`nguoi_ban`, `marketer`, `sale`…) của mọi bảng: giá trị
**khớp đúng** một tên đăng nhập thì đổi thành mã người đó, kể cả cột gương `val_seller`;
giá trị khác để nguyên và liệt kê. Cột phụ trách `phu_trach_*` đọc từ phân công nên không
cần đổi. Dữ liệu thật, nên lệnh chạy được cả khi DEBUG tắt.
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from core.audit import record
from core.constants import AuditAction
from forms_builder.meaning import Meaning
from forms_builder.models import DataRecord, TableDef
from org.models import UserProfile
from org.services import staff_code_service

CHUNK = 2000


class Command(BaseCommand):
    help = "Gan ma nhan su cho ho so cu va doi ten dang nhap -> ma trong o danh tinh (ADR-037)"

    def add_arguments(self, parser):
        parser.add_argument("--thu", action="store_true", help="Chi in ra, khong ghi (mac dinh)")
        parser.add_argument("--xac-nhan", action="store_true", help="Ghi that")

    def handle(self, *args, **options):
        ghi = bool(options["xac_nhan"]) and not options["thu"]
        self.stdout.write("CHE DO: " + ("GHI THAT" if ghi else "XEM TRUOC (them --xac-nhan de ghi)"))
        with transaction.atomic():
            self.gan_ma(ghi)
            self.doi_o_danh_tinh(ghi)
            if not ghi:
                transaction.set_rollback(True)

    # ── Việc 1 ──────────────────────────────────────────────────────
    def gan_ma(self, ghi):
        thieu = list(UserProfile.objects.filter(staff_code="")
                     .select_related("user").order_by("pk"))
        self.stdout.write(f"Ho so chua co ma: {len(thieu)}")
        for ho_so in thieu:
            ma = staff_code_service.suggest(
                ho_so.full_name, ho_so.user.get_username(),
                exclude_pk=ho_so.pk, exclude_user_pk=ho_so.user_id,
            )
            self.stdout.write(f"  {ho_so.user.get_username():20} {ho_so.full_name:30} -> {ma}")
            if ghi:
                staff_code_service.assign(ho_so, ma)

    # ── Việc 2 ──────────────────────────────────────────────────────
    def doi_o_danh_tinh(self, ghi):
        User = get_user_model()
        # tên đăng nhập → mã; hồ sơ chưa có mã (chế độ xem trước) lấy mã gợi ý nên bảng in ra đúng
        anh_xa = {}
        for user in User.objects.select_related("profile").order_by("pk"):
            ho_so = getattr(user, "profile", None)
            if ho_so is None:
                continue
            ma = ho_so.staff_code or staff_code_service.suggest(
                ho_so.full_name, user.get_username(), exclude_pk=ho_so.pk, exclude_user_pk=user.pk)
            if ma != user.get_username():
                anh_xa[user.get_username()] = ma
        if not anh_xa:
            self.stdout.write("Khong co ten dang nhap nao can doi thanh ma.")
            return
        tong = 0
        for table in TableDef.objects.order_by("pk"):
            cot = [c.code for c in table.columns.filter(meaning=Meaning.SELLER)]
            if not cot:
                continue
            dieu_kien = Q(val_seller__in=list(anh_xa))
            for code in cot:
                dieu_kien |= Q(**{f"data__{code}__in": list(anh_xa)})
            qs = (DataRecord.all_objects.filter(table=table).filter(dieu_kien)
                  .only("id", "data", "val_seller").order_by("pk"))
            doi, la = 0, set()
            batch = []
            for row in qs.iterator(chunk_size=CHUNK):
                thay = False
                for code in cot:
                    gia_tri = row.data.get(code)
                    if isinstance(gia_tri, str) and gia_tri in anh_xa:
                        row.data[code] = anh_xa[gia_tri]
                        thay = True
                    elif isinstance(gia_tri, str) and gia_tri and gia_tri not in anh_xa.values():
                        la.add(gia_tri)
                if row.val_seller in anh_xa:
                    row.val_seller = anh_xa[row.val_seller]
                    thay = True
                if thay:
                    doi += 1
                    batch.append(row)
                if len(batch) >= CHUNK:
                    self._ghi(batch, ghi)
                    batch = []
            self._ghi(batch, ghi)
            tong += doi
            if doi or la:
                self.stdout.write(f"  {table.code:20} doi {doi} dong" + (f"; gia tri la giu nguyen: {sorted(la)[:10]}" if la else ""))
            if ghi and doi:
                record(AuditAction.UPDATE, target=table, actor_label="gan_ma_nhan_su_cu",
                       detail=f"Doi ten dang nhap thanh ma nhan su o {doi} dong ({', '.join(cot)})")
        self.stdout.write(f"Tong dong doi o danh tinh: {tong}")

    def _ghi(self, batch, ghi):
        if ghi and batch:
            # bulk_update không qua save(): không đổi updated_at, không tính lại cột — chỉ đổi định danh
            DataRecord.all_objects.bulk_update(batch, ["data", "val_seller"], batch_size=CHUNK)
