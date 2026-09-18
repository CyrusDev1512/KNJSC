"""Kiểm tệp trước xác nhận và kiểm lại ngay trước khi ghi."""
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Trim

from core.exceptions import BusinessError
from forms_builder import choice_registry, record_policies
from forms_builder.meaning import FieldType
from . import record_service


def check(table, numbered_rows, columns):
    policy = record_policies.for_table(table)
    check_codes = getattr(table, 'workflow', '') == 'waybill' or table.code == 'van_don'
    order_column = next((c for c in columns if c.code == 'ma_don'), None)
    check_codes = check_codes and order_column is not None
    choices = {c.code: choice_registry.snapshot(choice_registry.for_column(c))
               for c in columns if c.field_type == FieldType.CHOICE and not c.is_computed}
    existing = set()
    if check_codes:
        keys = list({str(values.get('ma_don') or '').strip() for _, values in numbered_rows} - {''})
        # Không trả dữ liệu của đơn ngoài phạm vi: chỉ báo mã trong tệp đã tồn tại.
        for start in range(0, len(keys), 500):
            existing.update(table.records.annotate(import_code=Trim(KeyTextTransform('ma_don', 'data')))
                            .filter(import_code__in=keys[start:start + 500]).values_list('import_code', flat=True))
    accepted, errors, seen = [], [], set()
    for number, original in numbered_rows:
        try:
            values = policy.prepare_values(dict(original)) if policy else original
            parsed = {c.code: record_service.parse_value(c, values.get(c.code), choices=choices.get(c.code))
                      for c in columns if not c.is_computed}
            missing = record_service._thieu_bat_buoc(columns, parsed)
            if missing:
                raise BusinessError('Thiếu cột bắt buộc: ' + ', '.join(missing))
            key = str(parsed.get('ma_don') or '').strip()
            if check_codes and key:
                if key in existing:
                    raise BusinessError('Mã đơn đã tồn tại trong bảng; dòng này không được nhập lại.')
                if key in seen:
                    raise BusinessError('Mã đơn trùng với dòng hợp lệ trước đó trong tệp.')
                seen.add(key)
            accepted.append((number, original))
        except BusinessError as error:
            errors.append((number, str(error)))
    return accepted, errors
