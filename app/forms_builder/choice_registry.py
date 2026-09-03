"""Sổ danh sách chọn cho cột kiểu *Chọn một* của bảng động.

`ColumnDef` kiểu CHOICE không có trường lưu danh sách lựa chọn (backlog K22).
Module nghiệp vụ nào biết danh sách của cột nào thì **đăng ký** vào đây lúc
khởi động app — ví dụ `crm` đăng ký trạng thái vận đơn, trạng thái thanh
toán, nhân viên Vận đơn cho bảng `van_don`.

Một chỗ duy nhất quyết định ô đó nhận giá trị nào (quy tắc 7): tầng dịch vụ
kiểm khi sửa ô và khi nhập tệp, còn giao diện lấy cùng danh sách đó để vẽ ô
chọn. `forms_builder` không nhập module nào khác — chỉ giữ sổ.

Hai mức:

- **chặt** (`strict=True`): giá trị ngoài danh sách bị từ chối — trạng thái.
- **gợi ý** (`strict=False`): giao diện gợi ý danh sách, nhưng vẫn nhận giá
  trị khác — nhân viên vận đơn, vì tệp cũ ghi mã người không còn trong hệ
  thống và không được vì thế mà bỏ cả dòng.

So khớp **không phân biệt hoa thường và khoảng trắng thừa**: tệp thật ghi
"Đã Thanh Toán", hệ thống lưu "Đã thanh toán".
"""
import unicodedata
from dataclasses import dataclass
from typing import Callable

_SO = {}


@dataclass(frozen=True)
class ChoiceList:
    options: Callable[[], list]     # hàm trả về danh sách nhãn, gọi lúc cần
    strict: bool = True


def register(table_code, column_code, options, *, strict=True):
    """Đăng ký danh sách cho một cột. `options` là hàm không tham số."""
    _SO[(table_code, column_code)] = ChoiceList(options, strict)


def unregister(table_code, column_code):
    _SO.pop((table_code, column_code), None)


def get(table_code, column_code):
    return _SO.get((table_code, column_code))


def options_for(table_code, column_code):
    """Danh sách nhãn hiện tại, hoặc None nếu cột không có sổ."""
    ds = _SO.get((table_code, column_code))
    return list(ds.options()) if ds else None


def _khoa(text):
    return " ".join(unicodedata.normalize("NFC", str(text)).casefold().split())


def normalise(table_code, column_code, value):
    """Đưa giá trị về đúng nhãn trong danh sách.

    Trả về `(giá trị chuẩn, hợp lệ)`. Không có sổ → trả nguyên, hợp lệ.
    Có sổ mà không khớp → trả nguyên; hợp lệ khi sổ ở mức gợi ý.
    """
    ds = _SO.get((table_code, column_code))
    if ds is None or value in (None, ""):
        return value, True
    khoa = _khoa(value)
    for nhan in ds.options():
        if _khoa(nhan) == khoa:
            return nhan, True
    return value, not ds.strict
