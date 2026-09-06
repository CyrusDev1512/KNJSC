"""Sổ danh sách chọn cho cột kiểu *Chọn một* của bảng động — FR-8.7, Q54.

Một chỗ duy nhất quyết định ô đó nhận giá trị nào (quy tắc 7): tầng dịch vụ
kiểm khi điền biểu mẫu, sửa ô và nhập tệp, còn giao diện lấy cùng danh sách đó
để vẽ ô chọn. `forms_builder` không nhập module nghiệp vụ nào — chỉ giữ sổ.

Ba tầng, phân giải ở `for_column()` theo đúng thứ tự:

1. **Sổ theo (bảng, cột)** — module nghiệp vụ đăng ký lúc khởi động, ví dụ `crm`
   đăng ký trạng thái vận đơn cho bảng `van_don`. Tầng này luôn thắng.
2. **Sổ theo nhãn ý nghĩa** — cột *Chọn một* mang nhãn Sản phẩm lấy danh mục
   sản phẩm (`orders` đăng ký), nhãn Người bán lấy nhân sự bộ phận (`forms_builder`
   tự đăng ký). Có thể kèm hàm `add` để "Thêm mới…" ngay tại ô chọn.
3. **Danh sách trên cột** — `ColumnDef.options`, Manager đặt trong Sửa cột.

Hai tầng sau chỉ áp cho kiểu *Chọn một*; cột kiểu chữ mang nhãn (như `san_pham`
trên bảng vận đơn) vẫn là ô chữ tự do.

Hai mức:

- **chặt** (`strict=True`): giá trị ngoài danh sách bị từ chối — trạng thái,
  sản phẩm, danh sách trên cột.
- **gợi ý** (`strict=False`): giao diện gợi ý danh sách, nhưng vẫn nhận giá
  trị khác — nhân viên vận đơn, người bán, vì tệp cũ ghi tên người không còn
  trong hệ thống và không được vì thế mà bỏ cả dòng.

So khớp **không phân biệt hoa thường và khoảng trắng thừa**: tệp thật ghi
"Đã Thanh Toán", hệ thống lưu "Đã thanh toán".
"""
import dataclasses
import unicodedata
from dataclasses import dataclass
from typing import Callable, Optional

from .meaning import FieldType

#: Giá trị đặc biệt của mục "＋ Thêm mới…" trong ô chọn. `static/js/chon.js`
#: dùng cùng chuỗi này — hai nơi vì hai ngôn ngữ, đổi thì đổi cả hai.
ADD_SENTINEL = "__them__"

#: Nguồn của một danh sách — để giao diện biết có cho "Thêm mới…" hay không
SOURCE_REGISTRY = "registry"    # sổ (bảng, cột) — module nghiệp vụ tự lo
SOURCE_MEANING = "meaning"      # sổ theo nhãn ý nghĩa
SOURCE_COLUMN = "column"        # ColumnDef.options

_SO = {}          # (mã bảng, mã cột) → ChoiceList
_THEO_NHAN = {}   # nhãn ý nghĩa → (hàm options(column), chặt, hàm add hoặc None)


@dataclass(frozen=True)
class ChoiceList:
    options: Callable[[], list]         # hàm trả về danh sách nhãn, gọi lúc cần
    strict: bool = True
    #: Hàm thêm giá trị mới: `add(label, *, actor, request) -> nhãn chuẩn`.
    #: None nghĩa là danh sách này không thêm được tại ô chọn.
    add: Optional[Callable[..., str]] = None
    source: str = SOURCE_REGISTRY

    @property
    def can_add(self):
        """Giao diện có nên vẽ mục "Thêm mới…" cho danh sách này không.

        Danh sách trên cột thì thêm được (ghi vào `ColumnDef.options`), sổ
        theo nhãn thì tuỳ có `add`, sổ của module nghiệp vụ thì không.
        """
        return self.source == SOURCE_COLUMN or self.add is not None


# ══ Tầng 1 — sổ theo (bảng, cột) ═══════════════════════════════════

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


# ══ Tầng 2 — sổ theo nhãn ý nghĩa ═════════════════════════════════

def register_meaning(meaning, options, *, strict=True, add=None):
    """Đăng ký nguồn danh sách cho mọi cột *Chọn một* mang một nhãn ý nghĩa.

    `options(column)` trả về danh sách nhãn cho cột đó (cột biết bảng, bảng
    biết bộ phận). `add(column, label, *, actor, request)` thêm một giá trị
    mới và trả về nhãn chuẩn; để None nếu không cho thêm tại ô chọn.
    """
    _THEO_NHAN[str(meaning)] = (options, strict, add)


def unregister_meaning(meaning):
    _THEO_NHAN.pop(str(meaning), None)


def has_meaning_source(meaning):
    """Nhãn này có nguồn danh sách do hệ thống cung cấp không."""
    return bool(meaning) and str(meaning) in _THEO_NHAN


# ══ Phân giải ═════════════════════════════════════════════════════

def for_column(column):
    """Danh sách chọn áp cho một cột, hoặc None nếu cột nhận mọi giá trị.

    Thứ tự: sổ (bảng, cột) → sổ theo nhãn → `ColumnDef.options`. Hai tầng sau
    chỉ xét khi cột kiểu *Chọn một*. Cột *Chọn một* không có nguồn nào thì trả
    về danh sách rỗng chặt — không nhận giá trị nào cho tới khi Manager thêm.
    """
    ds = _SO.get((column.table.code, column.code))
    if ds is not None:
        return ds
    if column.field_type != FieldType.CHOICE:
        return None

    nguon = _THEO_NHAN.get(str(column.meaning)) if column.meaning else None
    if nguon is not None:
        ham_options, chat, ham_add = nguon
        return ChoiceList(
            options=lambda: list(ham_options(column)), strict=chat,
            add=(lambda label, **kw: ham_add(column, label, **kw)) if ham_add else None,
            source=SOURCE_MEANING,
        )

    gia_tri = list(column.options or [])
    return ChoiceList(options=lambda: list(gia_tri), strict=True, source=SOURCE_COLUMN)


def snapshot(choice_list):
    """Bản chụp: gọi `options()` đúng một lần rồi giữ lại danh sách.

    Dùng khi kiểm hàng nghìn dòng (nhập tệp) — không thì mỗi dòng lại truy
    vấn danh mục sản phẩm một lần.
    """
    if choice_list is None:
        return None
    gia_tri = list(choice_list.options())
    return dataclasses.replace(choice_list, options=lambda: list(gia_tri))


def _khoa(text):
    return " ".join(unicodedata.normalize("NFC", str(text)).casefold().split())


def match(choice_list, value):
    """Đưa giá trị về đúng nhãn trong danh sách.

    Trả về `(giá trị chuẩn, hợp lệ)`. Không có danh sách → trả nguyên, hợp lệ.
    Có danh sách mà không khớp → trả nguyên; hợp lệ khi danh sách ở mức gợi ý.
    """
    if choice_list is None or value in (None, ""):
        return value, True
    khoa = _khoa(value)
    for nhan in choice_list.options():
        if _khoa(nhan) == khoa:
            return nhan, True
    return value, not choice_list.strict


def normalise(table_code, column_code, value):
    """Như `match`, nhưng tra sổ (bảng, cột) — API cũ, `crm` vẫn gọi."""
    return match(_SO.get((table_code, column_code)), value)
