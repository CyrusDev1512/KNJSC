"""Loại tiền theo thị trường; đổi đơn vị tiền giữ số tiền sau xác nhận rõ ràng."""
from decimal import Decimal, InvalidOperation
import hashlib
import json
from django.core import signing
from core.constants import Currency
from core.exceptions import BusinessError
from orders.constants import Market

MARKET_CURRENCIES = {Market.US: Currency.USD, Market.CA: Currency.CAD, Market.PH: Currency.PHP}


def for_market(value):
    try:
        return MARKET_CURRENCIES[Market(value)]
    except (ValueError, KeyError):
        raise BusinessError('Chọn quốc gia hợp lệ để xác định loại tiền.')


def for_label(label, allow_empty=False):
    """Nhãn quốc gia → loại tiền. `allow_empty`: quốc gia trống thì tiền cũng trống
    (xoá ô Quốc gia trên lưới, chủ dự án chốt 18.09.2026); nhập tệp và lên đơn vẫn bắt buộc."""
    if allow_empty and str(label or '').strip() == '':
        return ''
    market = next((m for m in Market if m.label.casefold() == str(label).strip().casefold()), None)
    return for_market(market)


class CurrencyConfirmation(BusinessError):
    def __init__(self, confirmations):
        self.currency_confirmations = confirmations
        super().__init__(
            f'Đổi hoặc xoá quốc gia sẽ đổi loại tiền của {len(confirmations)} dòng đã có tiền. '
            'Bạn xác nhận giữ nguyên các số tiền, chỉ đổi loại tiền và không quy đổi tỷ giá?',
            code='currency_confirmation')


def _has_money(row):
    for code in ('gia_tien', 'so_tien_tt'):
        value = row.data.get(code)
        if value in (None, ''):
            continue
        try:
            if Decimal(str(value)) != 0:
                return True
        except (InvalidOperation, ValueError):
            return True
    return False


def change(row, market_label, confirmations=None):
    """Đổi hay xoá Quốc gia trên một dòng: trả `loai_tien` đi kèm; dòng đã có tiền phải xác nhận."""
    market_label = str(market_label or '').strip()   # '' và None cùng một chữ ký xác nhận
    currency = for_label(market_label, allow_empty=True)
    if currency != (row.data.get('loai_tien') or '') and _has_money(row):
        # Gắn xác nhận với phiên bản đã xem; người khác sửa dòng thì phải xác nhận lại.
        snapshot = [row.pk, row.updated_at.isoformat(), row.data.get('quoc_gia'),
                    row.data.get('loai_tien'), market_label, currency]
        digest = hashlib.sha256(json.dumps(snapshot).encode()).hexdigest()
        token = signing.Signer(salt='orders.currency-change').sign(digest)
        if not isinstance(confirmations, dict) or confirmations.get(str(row.pk)) != token:
            raise CurrencyConfirmation({str(row.pk): token})
    return {'loai_tien': currency}
