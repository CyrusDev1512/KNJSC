"""Ngày đọc trong ô lưới dùng D/M/Y, giá trị lưu/lọc vẫn là ISO."""
from types import SimpleNamespace

import pytest

from crm.services.grid_service import display_value, filter_chips


@pytest.mark.parametrize('kind,value,expected', [
    ('date', '2026-01-22', '22/01/2026'),
    ('date', '2024-02-29', '29/02/2024'),
    ('datetime', '2026-09-15T18:30:00Z', '16/09/2026 01:30'),
    ('date', None, None),
    ('date', '', ''),
    ('date', 'ngày chưa xác định', 'ngày chưa xác định'),
    ('text', '2026-01-22', '2026-01-22'),
])
def test_date_cell_display(kind, value, expected):
    column = SimpleNamespace(field_type=kind)
    assert display_value(column, value) == expected
    assert display_value(column, value, {'bg': 'red', 'fmt': 'text'}) == expected


def test_date_filter_label_keeps_query_value():
    column = SimpleNamespace(code='ngay', name='Ngày', field_type='date')
    filters = {'ngay__lon_bang': '2026-01-22'}
    assert filter_chips(filters, [column]) == [('f_ngay__lon_bang', 'Ngày ≥ 22/01/2026')]
    assert filters == {'ngay__lon_bang': '2026-01-22'}
