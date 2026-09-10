"""Hoàn thiện nhóm vận đơn mẫu MAU-* mà không tạo đơn hoặc khách ERP."""
import random
import re
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from core.audit import record as audit
from core.constants import AuditAction, Currency, Rank
from core.identity import display_name
from forms_builder.models import DataRecord, TableDef
from forms_builder.services import record_service
from orders.constants import (
    ACTIVE_WAYBILL_TABLE_CODE,
    Market,
    PaymentMethod,
    ShippingStatus,
)
from orders.models import Product, WaybillAssignment, WaybillItem
from orders.services import assignment_service, waybill_service
from org.models import UserProfile


PREFIX = "MAU-20260910-"
CODE_RE = re.compile(rf"^{re.escape(PREFIX)}(\d{{4,6}})$")
DEFAULT_TOTAL = 10_000
DEFAULT_SEED = 20260911
START_DATE = date(2026, 1, 1)
END_DATE = date(2026, 9, 11)

PLACES = (
    ("Ontario", "Toronto", "M5V"),
    ("Ontario", "Ottawa", "K1P"),
    ("British Columbia", "Vancouver", "V6B"),
    ("Alberta", "Calgary", "T2P"),
    ("Alberta", "Edmonton", "T5J"),
    ("Quebec", "Montréal", "H2Y"),
    ("Quebec", "Québec", "G1R"),
    ("Manitoba", "Winnipeg", "R3C"),
    ("Nova Scotia", "Halifax", "B3J"),
    ("Saskatchewan", "Saskatoon", "S7K"),
)
STREETS = (
    "Yonge Street", "King Street West", "Queen Street East", "Main Street",
    "Maple Avenue", "Harbour Street", "Cedar Road", "Lakeview Drive",
)
FIRST_NAMES = (
    "Alyssa", "Bianca", "Camille", "Diana", "Elena", "Frances", "Grace", "Hannah",
    "Iris", "Julia", "Katrina", "Lianne", "Maya", "Nadine", "Olivia", "Patricia",
    "Rina", "Sofia", "Teresa", "Vivian", "Adrian", "Brandon", "Caleb", "Daniel",
    "Ethan", "Felix", "Gabriel", "Henry", "Isaac", "Julian", "Kevin", "Lucas",
    "Marco", "Nathan", "Oscar", "Paolo", "Rafael", "Simon", "Theo", "Vincent",
)
LAST_NAMES = (
    "Abad", "Bautista", "Castillo", "Domingo", "Evangelista", "Flores", "Garcia",
    "Hernandez", "Ignacio", "Jimenez", "King", "Lim", "Mendoza", "Navarro",
    "Ocampo", "Pascual", "Quezon", "Reyes", "Santos", "Tolentino", "Uy", "Valdez",
    "Williams", "Young", "Zamora", "Anderson", "Brown", "Campbell", "Davis",
    "Edwards", "Foster", "Grant", "Hall", "Irving", "Johnson", "Kelly", "Lewis",
    "Martin", "Nelson", "Parker",
)
NOTES = (
    "Dữ liệu mẫu phục vụ kiểm thử Vận đơn mới.",
    "Gọi khách trước khi giao hàng.",
    "Ưu tiên giao trong giờ hành chính.",
    "Khách đề nghị để hàng tại quầy lễ tân.",
    "Kiểm tra lại địa chỉ trước khi xuất kho.",
    "Có thể giao vào buổi tối.",
)
BASE_PRICES = (
    Decimal("39.90"), Decimal("48.50"), Decimal("57.75"), Decimal("64.20"),
    Decimal("72.95"), Decimal("86.40"), Decimal("94.80"), Decimal("109.50"),
)
POSTAL_LETTERS = "ABCEGHJKLMNPRSTVWXYZ"


def _active_people(field, *, department=None):
    users = assignment_service.candidates(field)
    if department:
        users = users.filter(profile__department__code=department)
    return list(users.select_related("profile__department", "profile__team"))


def _preflight(total):
    if not 1 <= total <= 100_000:
        raise CommandError("--tong-so phải từ 1 đến 100.000.")
    table = TableDef.objects.filter(
        code=ACTIVE_WAYBILL_TABLE_CODE, is_active=True, deleted_at__isnull=True,
    ).first()
    if table is None:
        raise CommandError("Chưa có bảng Vận đơn mới (van_don_moi).")
    products = list(Product.objects.filter(is_active=True).order_by("code", "pk"))
    if not products:
        raise CommandError("Chưa có sản phẩm đang hoạt động.")
    sellers = _active_people("care", department="sale")
    if not sellers:
        raise CommandError("Chưa có nhân sự Sale đang hoạt động.")
    delivery = _active_people("delivery", department="van-don")
    if not delivery:
        raise CommandError("Chưa có nhân sự Vận đơn đang hoạt động.")
    admin = UserProfile.objects.filter(
        rank=Rank.ADMIN, user__is_active=True,
    ).select_related("user").order_by("user__username").first()
    if admin is None:
        raise CommandError("Chưa có tài khoản quản trị đang hoạt động.")
    columns = list(table.columns.order_by("order", "pk"))
    required = {c[1] for c in waybill_service.COLUMNS}
    missing = required - {column.code for column in columns}
    if missing:
        raise CommandError("Bảng Vận đơn mới thiếu cột chuẩn: " + ", ".join(sorted(missing)))
    return table, products, sellers, delivery, admin.user, columns


def _sequence(row):
    match = CODE_RE.fullmatch(str(row.data.get("ma_don", "")))
    if not match:
        raise CommandError(f"Mã mẫu không đúng định dạng: {row.data.get('ma_don')}")
    return int(match.group(1))


def _postal_code(prefix, rng):
    return f"{prefix} {rng.randrange(10)}{rng.choice(POSTAL_LETTERS)}{rng.randrange(10)}"


def _payment_mode(sequence, shipping):
    if shipping == ShippingStatus.HUY_TRUOC_GIAO.label:
        return "unpaid"
    if shipping in (ShippingStatus.HUY_SAU_GIAO.label, ShippingStatus.HOAN_DON.label):
        return "partial"
    return ("unpaid", "partial", "paid")[sequence % 3]


def _paid_amounts(items, mode):
    if mode == "unpaid":
        return [Decimal("0.00")] * len(items)
    totals = [(item.unit_price * item.quantity).quantize(Decimal("0.01")) for item in items]
    if mode == "paid":
        return totals
    paid = [Decimal("0.00")] * len(items)
    if len(items) > 1:
        paid[0] = totals[0]
    elif items[0].quantity > 1:
        paid[0] = items[0].unit_price
    else:
        paid[0] = (items[0].unit_price / Decimal("2")).quantize(Decimal("0.01"))
    return paid


def _sample(sequence, seed, products, sellers, delivery, *, identity=None):
    rng = random.Random(seed + sequence * 7919)
    province, city, postal = PLACES[(sequence - 1) % len(PLACES)]
    order_date = START_DATE + timedelta(days=rng.randrange((END_DATE - START_DATE).days + 1))
    seller = sellers[(sequence - 1) % len(sellers)]
    courier = delivery[(sequence - 1) % len(delivery)]
    count = min(len(products), 1 + rng.randrange(3))
    chosen = rng.sample(products, count)
    items = []
    for position, product in enumerate(chosen):
        quantity = 1 + rng.randrange(4)
        unit_price = BASE_PRICES[(sequence + position) % len(BASE_PRICES)]
        unit_price += Decimal(rng.randrange(0, 80)) / Decimal("100")
        items.append(WaybillItem(product=product, quantity=quantity,
                                 unit_price=unit_price.quantize(Decimal("0.01"))))
    shipping = list(ShippingStatus.labels)[(sequence - 1) % len(ShippingStatus.labels)]
    mode = _payment_mode(sequence, shipping)
    for item, paid in zip(items, _paid_amounts(items, mode)):
        item.paid_amount = paid
    totals = waybill_service.totals(items)
    payment_method = list(PaymentMethod.labels)[(sequence - 1) % len(PaymentMethod.labels)]
    paid = totals["trang_thai_tt"] != "Chưa thanh toán"
    payment_date = min(order_date + timedelta(days=rng.randrange(1, 8)), END_DATE)
    name = identity[0] if identity else (
        f"{FIRST_NAMES[(sequence - 1) % len(FIRST_NAMES)]} "
        f"{LAST_NAMES[((sequence - 1) // len(FIRST_NAMES)) % len(LAST_NAMES)]}"
    )
    phone = identity[1] if identity else f"+1 555 {100 + sequence // 10_000:03d} {sequence % 10_000:04d}"
    values = {
        "ma_don": f"{PREFIX}{sequence:04d}",
        "ten_khach": name,
        "so_dien_thoai": phone,
        "ngay": order_date.isoformat(),
        "quoc_gia": Market.CA.label,
        "bang": province,
        "thanh_pho": city,
        "zipcode": _postal_code(postal, rng),
        "dia_chi": f"{1 + rng.randrange(998)} {rng.choice(STREETS)}",
        "loai_tien": Currency.CAD,
        "pttt": payment_method,
        "nguoi_ban": display_name(seller),
        "trang_thai_vc": shipping,
        "ngay_tt": payment_date.isoformat() if paid else None,
        "bill": f"BILL-MAU-{sequence:05d}" if paid else None,
        "pttt_thuc_te": list(PaymentMethod.labels)[sequence % len(PaymentMethod.labels)] if paid else None,
        "ghi_chu": NOTES[(sequence - 1) % len(NOTES)],
        **totals,
    }
    return values, items, seller, courier


def _normalise(values, columns):
    result = {}
    for column in columns:
        if column.code in values:
            result[column.code] = record_service.parse_value(column, values[column.code])
    return result


@transaction.atomic
def populate(*, total=DEFAULT_TOTAL, seed=DEFAULT_SEED, dry_run=False):
    table, products, sellers, delivery, actor, columns = _preflight(total)
    cohort = list(DataRecord.all_objects.select_for_update().filter(
        table=table, data__ma_don__startswith=PREFIX,
    ).order_by("pk"))
    by_sequence = {}
    for row in cohort:
        sequence = _sequence(row)
        if sequence < 1 or sequence > total:
            raise CommandError(f"Mã mẫu {row.data['ma_don']} nằm ngoài --tong-so={total}; không tự xoá dữ liệu.")
        if sequence in by_sequence:
            raise CommandError(f"Trùng thứ tự mã mẫu {sequence}; không ghi dữ liệu.")
        if not row.data.get("ten_khach") or not row.data.get("so_dien_thoai"):
            raise CommandError(f"Dòng mẫu {row.pk} thiếu tên hoặc số điện thoại cần bảo toàn.")
        by_sequence[sequence] = row
    missing = [sequence for sequence in range(1, total + 1) if sequence not in by_sequence]
    new_phones = [f"+1 555 {100 + sequence // 10_000:03d} {sequence % 10_000:04d}" for sequence in missing]
    if DataRecord.all_objects.filter(table=table, val_phone__in=new_phones).exclude(
            data__ma_don__startswith=PREFIX).exists():
        raise CommandError("Số điện thoại mẫu mới trùng một vận đơn ngoài nhóm MAU; không ghi dữ liệu.")
    summary = {"updated": len(cohort), "created": len(missing), "table": table,
               "items_created": 0, "assignments_created": 0, "changed": False}
    if dry_run:
        transaction.set_rollback(True)
        return summary

    existing_items = {}
    for item in WaybillItem.objects.filter(record__in=cohort, deleted_at__isnull=True).order_by("pk"):
        existing_items.setdefault(item.record_id, []).append(item)
    existing_assignments = {
        assignment.record_id: assignment for assignment in
        WaybillAssignment.objects.select_for_update().filter(record__in=cohort)
    }
    rows_to_update = []
    new_rows = []
    desired = {}
    for sequence in range(1, total + 1):
        row = by_sequence.get(sequence)
        identity = None if row is None else (row.data["ten_khach"], row.data["so_dien_thoai"])
        values, items, seller, courier = _sample(
            sequence, seed, products, sellers, delivery, identity=identity,
        )
        data = _normalise(values, columns)
        if row is None:
            row = DataRecord(table=table, data=data, created_by=seller,
                             department=table.department, team=seller.profile.team)
            row.sync_indexed_columns(columns)
            new_rows.append(row)
        else:
            next_data = {**row.data, **data}
            if row.data != next_data or row.deleted_at is not None:
                row.data = next_data
                row.deleted_at = None
                row.deleted_by = None
                row.sync_indexed_columns(columns)
                rows_to_update.append(row)
        desired[sequence] = (row, items, seller, courier)

    if new_rows:
        DataRecord.objects.bulk_create(new_rows, batch_size=500)
    if rows_to_update:
        DataRecord.bulk_save(rows_to_update, fields=(
            "data", "deleted_at", "deleted_by", "val_date", "val_customer", "val_phone",
            "val_revenue", "val_seller", "val_product", "val_status",
        ))

    items_to_create = []
    items_to_update = []
    items_to_delete = []
    assignments_to_create = []
    assignments_to_update = []
    for sequence, (row, wanted_items, seller, courier) in desired.items():
        current_items = existing_items.get(row.pk, [])
        for position, wanted in enumerate(wanted_items):
            if position < len(current_items):
                current = current_items[position]
                fields = (wanted.product_id, wanted.quantity, wanted.unit_price, wanted.paid_amount)
                if fields != (current.product_id, current.quantity, current.unit_price, current.paid_amount):
                    current.product = wanted.product
                    current.quantity = wanted.quantity
                    current.unit_price = wanted.unit_price
                    current.paid_amount = wanted.paid_amount
                    items_to_update.append(current)
            else:
                wanted.record = row
                items_to_create.append(wanted)
        items_to_delete.extend(current_items[len(wanted_items):])

        assignment = existing_assignments.get(row.pk)
        if assignment is None:
            assignments_to_create.append(WaybillAssignment(
                record=row, delivery=courier, care=seller, version=1,
            ))
        elif assignment.delivery_id != courier.pk or assignment.care_id != seller.pk:
            assignment.delivery = courier
            assignment.care = seller
            assignment.version += 1
            assignments_to_update.append(assignment)

    if items_to_update:
        now = timezone.now()
        for item in items_to_update:
            item.updated_at = now
        WaybillItem.objects.bulk_update(
            items_to_update, ("product", "quantity", "unit_price", "paid_amount", "updated_at"),
            batch_size=500,
        )
    if items_to_delete:
        now = timezone.now()
        for item in items_to_delete:
            item.deleted_at = now
            item.deleted_by = actor
            item.updated_at = now
        WaybillItem.objects.bulk_update(items_to_delete, ("deleted_at", "deleted_by", "updated_at"),
                                        batch_size=500)
    if items_to_create:
        WaybillItem.objects.bulk_create(items_to_create, batch_size=500)
    if assignments_to_create:
        WaybillAssignment.objects.bulk_create(assignments_to_create, batch_size=500)
    if assignments_to_update:
        WaybillAssignment.objects.bulk_update(
            assignments_to_update, ("delivery", "care", "version"), batch_size=500,
        )

    changed = any((new_rows, rows_to_update, items_to_create, items_to_update,
                   items_to_delete, assignments_to_create, assignments_to_update))
    if changed:
        audit(AuditAction.IMPORT, actor=actor, target=table,
              detail=(f"Hoàn thiện {len(cohort)} và tạo {len(new_rows)} vận đơn mẫu {PREFIX}*; "
                      f"seed {seed}"))
    summary.update(items_created=len(items_to_create),
                   assignments_created=len(assignments_to_create), changed=changed)
    return summary


class Command(BaseCommand):
    help = "Hoàn thiện 10.000 vận đơn mẫu trong van_don_moi, không tạo đơn ERP"

    def add_arguments(self, parser):
        parser.add_argument("--tong-so", type=int, default=DEFAULT_TOTAL, dest="tong_so")
        parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
        parser.add_argument("--dry-run", action="store_true", dest="dry_run")

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Dữ liệu giả chỉ được nạp khi DEBUG đang bật.")
        result = populate(total=options["tong_so"], seed=options["seed"],
                          dry_run=options["dry_run"])
        action = "Dự kiến" if options["dry_run"] else "Đã xử lý"
        self.stdout.write(
            f"{action}: {result['updated']} dòng cập nhật, {result['created']} dòng tạo mới "
            f"trong {result['table'].code}."
        )
        if not options["dry_run"]:
            suffix = "Có thay đổi." if result["changed"] else "Dữ liệu đã đúng, không ghi lại."
            self.stdout.write(self.style.SUCCESS(suffix))
