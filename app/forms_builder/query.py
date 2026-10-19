"""Dựng truy vấn động trên bảng do người dùng tạo.

Bảng động không có cột vật lý cho từng trường, nên mọi phép lọc và sắp xếp
phải dịch từ **tên kỹ thuật của cột** sang đường dẫn truy vấn thật:

    cột có nhãn ý nghĩa  →  cột tách có chỉ mục   (val_revenue, val_date...)
    cột không có nhãn    →  khoá trong JSON        (data__cpo)

Đây là chỗ duy nhất biết cách dịch. Không view nào tự ghép chuỗi truy vấn —
ghép sai thì hoặc nổ, hoặc tệ hơn là trả nhầm dữ liệu.

**Phạm vi quyền không do tệp này lo.** Gọi `.in_scope(user)` trước, rồi mới
đưa queryset vào đây (quy tắc 11).
"""
from orders.constants import is_waybill_table
from datetime import date, datetime
from decimal import InvalidOperation
from django.conf import settings
from django.core.exceptions import FieldError, ValidationError
from django.db.models import Q, BooleanField, Case, DecimalField, Func, Value, When
from django.db.models.fields.json import KeyTextTransform
from core.exceptions import BusinessError
from core.money import parse_money, parse_stored_number

from .meaning import COLUMN_OF

#: Phép so sánh cho phép, ánh xạ sang tra cứu của Django.
#: Danh sách đóng — không nhận tra cứu tuỳ ý từ tham số trên URL.
OPERATORS = {
    "bang": "exact",
    "chua": "icontains",
    "bat_dau": "istartswith",
    "lon_hon": "gt",
    "lon_bang": "gte",
    "nho_hon": "lt",
    "nho_bang": "lte",
    "trong": "in",
    # Hai phép đặc biệt, không phải tra cứu Django: ô trống và ô có giá trị
    "rong": "blank",
    "co": "nonblank",
}

#: Giá trị của phép "trong" là danh sách; trên đường dẫn là nhiều tham số
#: cùng tên (`f_cot__trong=a&f_cot__trong=b`)
LIST_OPERATORS = {"trong"}

#: Cột tiền/số thập phân JSON được ép numeric có kiểm tra trước khi so sánh.
NUMERIC_OPERATORS = {"gt", "gte", "lt", "lte"}
#: Kiểu cột JSON mà phép so sánh khoảng vẫn đúng
JSON_RANGE_TYPES = {"integer", "decimal", "money", "date", "datetime"}


class InvalidFilter(BusinessError):
    """Bộ lọc đã biết nhưng giá trị sai: không được âm thầm bỏ lọc."""


def _numeric_path(queryset, column):
    """JSON số lưu chuỗi máy: numeric không làm tròn, dữ liệu cũ sai kiểu không gây 500.

    PostgreSQL 16 kiểm khả năng ép kiểu trước CAST; không đặt trần precision mới cho dữ liệu đã lưu.
    """
    name = f"_kn_number_{column.pk}"
    text = KeyTextTransform(column.code, "data")
    valid = Func(text, Value("numeric"), function="pg_input_is_valid", output_field=BooleanField())
    number = Func(text, template="(%(expressions)s)::numeric", output_field=DecimalField())
    finite = Q(**{f"data__{column.code}__regex": r"^[+-]?[0-9]+([.][0-9]+)?([eE][+-]?[0-9]+)?$"})
    return queryset.alias(**{name: Case(When(Q(valid) & finite, then=number), default=None, output_field=DecimalField())}), name


def _filter_value(column, path, value, operator):
    """Chữ người gõ và giá trị máy trong danh sách chọn đi hai bộ đọc riêng (ADR-052)."""
    kind = "money" if path == "val_revenue" else "date" if path == "val_date" else column.field_type
    def one(raw):
        try:
            if kind in ("money", "decimal"):
                value = parse_stored_number(raw) if operator == "in" else parse_money(raw)
                if value is None:
                    raise ValueError
                return value
            if kind == "integer":
                text = str(raw).strip().replace(".", "").replace(" ", "")
                if len(text) > 20:
                    raise ValueError
                return int(text)
            if kind == "date":
                text = str(raw).strip()
                return (datetime.strptime(text, "%d/%m/%Y").date() if "/" in text else date.fromisoformat(text)).isoformat()
            if kind == "datetime":
                text = str(raw).strip()
                return (datetime.strptime(text, "%d/%m/%Y %H:%M") if "/" in text else datetime.fromisoformat(text)).isoformat()
            return raw
        except (ValueError, TypeError, InvalidOperation, BusinessError):
            raise InvalidFilter(f'Bộ lọc cột "{column.name}" không hợp lệ. Kiểm tra ngày hoặc số đã nhập.') from None
    return [one(v) for v in value] if isinstance(value, (list, tuple)) else one(value)


class ColumnMap:
    """Bảng tra: tên kỹ thuật của cột → đường dẫn truy vấn.

    Dựng một lần cho mỗi bảng rồi dùng lại, tránh truy vấn lại định nghĩa cột
    cho từng lần lọc.
    """

    def __init__(self, table, columns=None):
        self.table = table
        self.columns = list(columns if columns is not None else table.columns.all())
        self.by_code = {c.code: c for c in self.columns}

    def path(self, code):
        """Đường dẫn truy vấn của một cột. Cột lạ thì trả None."""
        cot = self.by_code.get(code)
        if cot is None:
            return None
        from orders.services.assignment_service import COLUMNS
        if is_waybill_table(self.table) and code in COLUMNS:
            # Cột phụ trách hiện mã nhân sự (ADR-037) nên lọc/sắp theo mã
            return f'assignment__{COLUMNS[code]}__profile__staff_code'
        cot_tach = COLUMN_OF.get(cot.meaning) if cot.meaning else None
        return cot_tach or f"data__{code}"

    def is_indexed(self, code):
        """Cột này có nằm ở cột tách có chỉ mục không."""
        cot = self.by_code.get(code)
        return bool(cot and cot.meaning and COLUMN_OF.get(cot.meaning))

    def searchable_paths(self):
        """Các cột dùng để tìm kiếm chung.

        Chỉ lấy cột tách — tìm trên khoá JSON không dùng được chỉ mục, và với
        50.000 bản ghi thì sẽ quét toàn bảng (NFR-1).
        """
        return [
            COLUMN_OF[c.meaning] for c in self.columns
            if c.meaning and COLUMN_OF.get(c.meaning)
            and COLUMN_OF[c.meaning] not in ("val_date", "val_revenue")
        ]


def apply_filters(queryset, column_map, filters):
    """Lọc theo nhiều cột.

    `filters` là dict `{tên_cột: giá_trị}` hoặc `{tên_cột__phép_so_sánh: giá_trị}`.
    Cột/phép lạ bị bỏ qua. Giá trị sai của cột đã biết bị từ chối rõ ràng,
    không được âm thầm mở rộng kết quả và tệp xuất.
    """
    for khoa, gia_tri in (filters or {}).items():
        if gia_tri in (None, ""):
            continue
        code, _, ten_phep = khoa.partition("__")
        phep = OPERATORS.get(ten_phep or "bang")
        duong_dan = column_map.path(code)
        if not duong_dan or not phep:
            continue
        if (getattr(settings, 'PAYMENT_DOCUMENTS_ENABLED', False)
                and is_waybill_table(column_map.table) and code == 'bill'):
            from orders.models import PaymentDocument
            documents = PaymentDocument.objects.filter(deleted_at__isnull=True)
            if phep in ('blank', 'nonblank'):
                blank = (Q(data__bill__isnull=True) | Q(data__bill='') | Q(data__bill=None)) & ~Q(pk__in=documents.values('record_id'))
                queryset = queryset.filter(blank) if phep == 'blank' else queryset.exclude(blank)
            else:
                value = gia_tri if phep != 'in' or isinstance(gia_tri, (list, tuple)) else [gia_tri]
                matches = documents.filter(**{f'reference__{phep}': value})
                queryset = queryset.filter(Q(**{f'data__bill__{phep}': value}) | Q(pk__in=matches.values('record_id')))
            continue
        if is_waybill_table(column_map.table) and code == 'san_pham':
            from orders.models import WaybillItem
            items = WaybillItem.objects.filter(deleted_at__isnull=True)
            if phep in ('blank', 'nonblank'):
                condition = Q(pk__in=items.values('record_id'))
                queryset = queryset.exclude(condition) if phep == 'blank' else queryset.filter(condition)
            else:
                values = gia_tri if phep != 'in' or isinstance(gia_tri, (list, tuple)) else [gia_tri]
                items = items.filter(**{f'product__code__{phep}': values})
                queryset = queryset.filter(pk__in=items.values('record_id'))
            continue
        if duong_dan.startswith('assignment__') and phep in ('in', 'exact'):
            values = gia_tri if isinstance(gia_tri, (list, tuple)) else [gia_tri]
            condition = Q(**{f'{duong_dan}__in': [v for v in values if v != '__unassigned__']})
            if '__unassigned__' in values:
                condition |= Q(**{f'{duong_dan}__isnull': True})
            queryset = queryset.filter(condition)
            continue
        if phep in ("blank", "nonblank"):
            trong = Q(**{f"{duong_dan}__isnull": True})
            if duong_dan not in ("val_date", "val_revenue"):
                trong |= Q(**{duong_dan: ""})
            queryset = queryset.filter(trong) if phep == "blank" else queryset.exclude(trong)
            continue
        if phep == "in":
            gia_tri = [v for v in (gia_tri if isinstance(gia_tri, (list, tuple)) else [gia_tri]) if v != ""]
            if not gia_tri:
                continue
        cot = column_map.by_code.get(code)
        gia_tri = _filter_value(cot, duong_dan, gia_tri, phep)
        numeric_json = not column_map.is_indexed(code) and cot.field_type in ("money", "decimal")
        if numeric_json:
            queryset, duong_dan = _numeric_path(queryset, cot)
        if not column_map.is_indexed(code):
            # JSON số nguyên/ngày giữ kiểu đã chuẩn hoá; tiền/số thập phân dùng
            # biểu thức numeric ở trên. Cột chữ giữ phép bằng khi yêu cầu khoảng.
            if phep in NUMERIC_OPERATORS and cot.field_type not in JSON_RANGE_TYPES:
                phep = "exact"
        try:
            if phep == 'exact' and duong_dan.startswith('data__'):
                # GIN(data) dùng containment, không dùng biểu thức data->key = x.
                # Giữ phép bằng bên dưới để không thay ngữ nghĩa lọc hiện có.
                queryset = queryset.filter(data__contains={code: gia_tri})
            queryset = queryset.filter(**{f"{duong_dan}__{phep}": gia_tri})
        except (FieldError, ValidationError, ValueError, TypeError):
            raise InvalidFilter(f'Bộ lọc cột "{cot.name}" không hợp lệ.') from None
    return queryset


def read_filters(params, columns):
    """Đọc bộ lọc từ tham số đường dẫn: `f_<cột>` hoặc `f_<cột>__<phép>`.

    Chỉ nhận cột có thật; phép "trong" gom nhiều tham số cùng tên thành danh
    sách. Dùng chung cho màn hình bảng, xuất tệp và Bảng tính — một chỗ đọc
    duy nhất để xuất ra đúng thứ đang hiện (ADR-002).
    """
    ma_cot = {c.code for c in columns}
    bo_loc = {}
    lay_nhieu = getattr(params, "getlist", None)
    for khoa in params.keys():
        if not khoa.startswith("f_"):
            continue
        ten = khoa[2:]
        code, _, phep = ten.partition("__")
        if code not in ma_cot:
            continue
        if phep in LIST_OPERATORS and lay_nhieu:
            gia_tri = [v.strip() for v in lay_nhieu(khoa) if v.strip()]
            if gia_tri:
                bo_loc[ten] = gia_tri
            continue
        gia_tri = params.get(khoa)
        if isinstance(gia_tri, (list, tuple)):
            gia_tri = gia_tri[0] if gia_tri else ""
        if gia_tri is not None and str(gia_tri).strip():
            bo_loc[ten] = str(gia_tri).strip()
    return bo_loc


def apply_search(queryset, column_map, term):
    """Tìm kiếm chung trên các cột tách."""
    term = (term or "").strip()
    if not term:
        return queryset
    duong_dan = column_map.searchable_paths()
    if not duong_dan:
        return queryset
    dieu_kien = Q()
    for p in duong_dan:
        dieu_kien |= Q(**{f"{p}__icontains": term})
    if (getattr(settings, 'PAYMENT_DOCUMENTS_ENABLED', False)
            and is_waybill_table(column_map.table)):
        from orders.models import PaymentDocument
        matches = PaymentDocument.objects.filter(deleted_at__isnull=True, reference__icontains=term)
        dieu_kien |= Q(data__bill__icontains=term) | Q(pk__in=matches.values('record_id'))
    return queryset.filter(dieu_kien)


def apply_sort(queryset, column_map, sort_code, descending=False):
    """Sắp xếp theo một cột.

    Cột lạ thì rơi về thứ tự mặc định, không ném lỗi.
    """
    duong_dan = column_map.path(sort_code) if sort_code else None
    if not duong_dan:
        return queryset.order_by("-created_at", "pk")
    column = column_map.by_code[sort_code]
    if not column_map.is_indexed(sort_code) and column.field_type in ("money", "decimal"):
        queryset, duong_dan = _numeric_path(queryset, column)
    return queryset.order_by(f"{'-' if descending else ''}{duong_dan}", "pk")


def build(queryset, table, *, filters=None, search="", sort=None, descending=False,
          columns=None):
    """Dựng trọn truy vấn cho một màn hình bảng dữ liệu.

    Nhận queryset **đã áp phạm vi quyền**, trả về queryset đã lọc và sắp xếp.
    Việc cắt trang do `core.pagination` lo (quy tắc 1).
    """
    column_map = ColumnMap(table, columns)
    queryset = queryset.filter(table=table)
    queryset = apply_filters(queryset, column_map, filters)
    queryset = apply_search(queryset, column_map, search)
    queryset = apply_sort(queryset, column_map, sort, descending)
    if is_waybill_table(table):
        if not sort or not column_map.path(sort):
            queryset = queryset.order_by('created_at', 'pk')
        else:
            queryset = queryset.order_by(*queryset.query.order_by, 'pk')
        from orders.services.assignment_service import related
        queryset = related(queryset)
    return queryset, column_map


def read_row(record, columns):
    """Đọc một bản ghi ra dạng `[(cột, giá trị), ...]` theo đúng thứ tự hiển thị.

    Dùng ở tầng giao diện để khỏi phải biết giá trị nằm ở JSON hay cột tách.
    """
    from orders.services import assignment_service
    values = []
    for column in columns:
        value = record.data.get(column.code)
        if is_waybill_table(record.table) and column.code in assignment_service.COLUMNS:
            value = assignment_service.display(record, column.code)
        elif column.code == 'bill' and hasattr(record, 'export_payments'):
            references = [doc.reference for doc in record.export_payments]
            if value:
                references.append(str(value))
            value = '; '.join(references)
        values.append((column, value))
    return values
