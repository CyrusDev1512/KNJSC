"""Tiền tệ.

Quy tắc BR-8: mọi số tiền lưu dạng số thập phân chính xác. Không dùng số
thực dấu phẩy động vì cộng tiền bị sai số.

Phase 1 có hai loại tiền là VND và USD. Mỗi số tiền lưu kèm loại tiền của
nó và không quy đổi khi lưu — quy đổi là việc của lúc lập báo cáo, và tỉ
giá lúc đó khác tỉ giá lúc chốt đơn.
"""
from decimal import Decimal

from django.db import models

from .constants import CURRENCY_DECIMALS, CURRENCY_SYMBOL, Currency

# 18 chữ số đủ cho hàng nghìn tỉ đồng, 2 số lẻ đủ cho USD
MONEY_MAX_DIGITS = 18
MONEY_DECIMAL_PLACES = 2
ZERO = Decimal("0.00")


def money_field(verbose_name, **kwargs):
    """Tạo một cột tiền. Dùng hàm này thay vì tự khai DecimalField."""
    kwargs.setdefault("max_digits", MONEY_MAX_DIGITS)
    kwargs.setdefault("decimal_places", MONEY_DECIMAL_PLACES)
    kwargs.setdefault("default", ZERO)
    return models.DecimalField(verbose_name, **kwargs)


def currency_field(verbose_name="Loại tiền", **kwargs):
    kwargs.setdefault("max_length", 3)
    kwargs.setdefault("choices", Currency.choices)
    kwargs.setdefault("default", Currency.VND)
    return models.CharField(verbose_name, **kwargs)


def parse_money(text):
    """Đọc số tiền người dùng gõ, theo tập quán Việt Nam.

    **Phải đọc lại được đúng thứ `format_money` in ra.** Không thì hệ thống
    hiện một con số mà chính nó không nhận lại được — người dùng chép số trên
    màn hình dán vào ô nhập là sai gấp nghìn lần.

        1.234,56  →  1234.56    chấm ngăn nghìn, phẩy thập phân
        1234,56   →  1234.56
        1.234     →  1234       chỉ có chấm, ba chữ số cuối → ngăn nghìn
        150.00    →  150.00     chỉ có chấm, hai chữ số cuối → thập phân

    Chỗ nhập nhằng duy nhất là dấu chấm đứng một mình. Quy tắc: đúng một dấu
    chấm và sau nó một hoặc hai chữ số thì là dấu thập phân, còn lại là dấu
    ngăn nghìn. `150.00` là máy sinh ra, `1.234` là người Việt gõ.

    Ném `InvalidOperation` nếu không đọc được — người gọi tự đổi thành thông
    báo tiếng Việt.
    """
    chuoi = str(text).strip().replace(" ", "").replace(" ", "")
    for ky_hieu in CURRENCY_SYMBOL.values():
        chuoi = chuoi.replace(ky_hieu, "")
    chuoi = chuoi.strip()
    if not chuoi:
        return None

    am = chuoi.startswith("-")
    chuoi = chuoi.lstrip("-+")

    co_cham, co_phay = "." in chuoi, "," in chuoi
    if co_cham and co_phay:
        # Dấu đứng sau cùng là dấu thập phân, dấu kia là ngăn nghìn
        if chuoi.rfind(",") > chuoi.rfind("."):
            chuoi = chuoi.replace(".", "").replace(",", ".")
        else:
            chuoi = chuoi.replace(",", "")
    elif co_phay:
        chuoi = chuoi.replace(",", ".")
    elif co_cham:
        phan = chuoi.split(".")
        la_thap_phan = len(phan) == 2 and 1 <= len(phan[1]) <= 2
        if not la_thap_phan:
            chuoi = chuoi.replace(".", "")

    so = Decimal(chuoi)
    return -so if am else so


def format_money(amount, currency=Currency.VND):
    """Hiển thị số tiền theo tập quán Việt Nam.

    VND không có số lẻ, USD có hai số lẻ.
    """
    if amount is None:
        return ""
    so_le = CURRENCY_DECIMALS.get(currency, 2)
    amount = Decimal(amount).quantize(Decimal(1) if so_le == 0 else Decimal("0.01"))
    nguyen, _, le = f"{abs(amount):.{so_le}f}".partition(".")
    nhom = f"{int(nguyen):,}".replace(",", ".")
    chuoi = f"{nhom},{le}" if so_le else nhom
    dau = "-" if amount < 0 else ""
    ky_hieu = CURRENCY_SYMBOL.get(currency, "")
    if currency == Currency.USD:
        return f"{dau}{ky_hieu}{chuoi}"
    return f"{dau}{chuoi} {ky_hieu}"
