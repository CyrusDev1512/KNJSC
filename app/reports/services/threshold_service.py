"""Ngưỡng màu ba bậc của Báo cáo tổng hợp (ADR-042 đợt 3).

Ảnh mẫu tô ô chỉ số **xanh / vàng / đỏ** theo mốc cố định. Mốc là của nghiệp vụ nên không bịa:
Manager của bộ phận sở hữu nguồn (cùng luật với sửa cột, `grant_service.can_manage_columns`) đặt
trên chính màn hình báo cáo, lưu ở `ReportSource.thresholds` `{mã chỉ tiêu: {"tot", "kem"}}`.
Chỉ tiêu chưa có ngưỡng giữ cách tô tương đối ±10 % so với dòng Tổng (AC-22.16).

Đơn vị nhập theo đúng ô hiển thị: tỉ lệ theo % (8 = 8 %), tiền theo ₫ đã quy đổi, tỉ số CPQC/DS
Chốt là số thuần. Chiều tốt lấy từ `reports.constants.METRIC_DIRECTION`.
"""
from decimal import Decimal, InvalidOperation

from core.audit import record
from core.constants import AuditAction
from core.exceptions import BusinessError
from core.money import parse_money
from forms_builder.services import grant_service
from reports import constants

#: (mã chỉ tiêu, nhãn mặc định, đơn vị nhập) — thứ tự hiện trên form
METRICS = (
    ("conversion", "Tỉ lệ chốt", "%"), ("conversion_tt", "Tỉ lệ chốt (TT)", "%"),
    ("mess_cost", "Giá Mess", "₫"), ("cpo", "CPO", "₫"),
    ("cost_sales", "CPQC/DS Chốt", ""), ("aov", "AOV", "₫"),
)
CHIEU_LABEL = {"cao": "càng cao càng tốt", "thap": "càng thấp càng tốt"}


def can_set(user, source):
    """Ai đặt được ngưỡng: quản lý của bộ phận sở hữu bảng nguồn hoặc Admin — cùng luật sửa cột."""
    return grant_service.can_manage_columns(user, source.table)


def rows(source, labels=None):
    """Dòng của form Ngưỡng màu: nhãn theo nguồn (MKT/Sale khác nhau), mốc đang lưu, chiều tốt."""
    out = []
    for code, label, unit in METRICS:
        chieu = constants.METRIC_DIRECTION[code]
        muc = (source.thresholds or {}).get(code, {})
        out.append({
            "code": code, "label": (labels or {}).get(code, label), "unit": unit,
            "chieu": chieu, "chieu_label": CHIEU_LABEL[chieu],
            "tot": hien_so(muc.get("tot", "")), "kem": hien_so(muc.get("kem", "")),
            "dau_tot": "≥" if chieu == "cao" else "≤", "dau_kem": "<" if chieu == "cao" else ">",
        })
    return out


def hien_so(so):
    """Mốc đã lưu (`"84526646"`, `"7.32"`, `"0.345"`) hiện trên form theo cách người Việt gõ:
    `84.526.646`, `7,32`, `0,345` — đúng thứ `parse_money` đọc lại. Hiện chuỗi máy thì `0.345` bị đọc
    thành 345 (ba chữ số sau dấu chấm là ngăn nghìn) và người mở form rồi bấm Lưu sẽ lưu sai."""
    if so in ("", None):
        return ""
    gia = Decimal(str(so))
    nguyen, _, le = format(abs(gia), "f").partition(".")
    le = le.rstrip("0")
    nhom = f"{int(nguyen):,}".replace(",", ".")
    dau = "-" if gia < 0 else ""
    return f"{dau}{nhom},{le}" if le else f"{dau}{nhom}"


def parse(data, labels=None):
    """Đọc form thành `{mã: {"tot", "kem"}}`. Cả hai ô trống → bỏ ngưỡng của chỉ tiêu đó; một ô
    trống, không phải số, âm, hay sai thứ tự theo chiều tốt → `BusinessError` nói rõ chỉ tiêu nào.
    Chỉ nhận đúng các mã trong `METRICS` — khoá lạ trên form bị bỏ qua."""
    out = {}
    for code, label, unit in METRICS:
        ten = (labels or {}).get(code, label)
        tot = (data.get(f"tot_{code}", "") or "").strip()
        kem = (data.get(f"kem_{code}", "") or "").strip()
        if not tot and not kem:
            continue
        if not tot or not kem:
            raise BusinessError(f"{ten}: cần cả hai mốc Tốt và Kém, hoặc để trống cả hai.")
        try:
            so_tot, so_kem = parse_money(tot), parse_money(kem)
        except (InvalidOperation, ValueError):
            raise BusinessError(f"{ten}: mốc phải là số.")
        if so_tot is None or so_kem is None or so_tot < 0 or so_kem < 0:
            raise BusinessError(f"{ten}: mốc phải là số không âm.")
        chieu = constants.METRIC_DIRECTION[code]
        if (chieu == "cao" and so_tot <= so_kem) or (chieu == "thap" and so_tot >= so_kem):
            raise BusinessError(
                f"{ten} {CHIEU_LABEL[chieu]} nên mốc Tốt phải {'lớn' if chieu == 'cao' else 'nhỏ'} hơn mốc Kém.")
        out[code] = {"tot": str(so_tot), "kem": str(so_kem)}
    return out


def update(source, thresholds, *, actor=None, request=None):
    """Ghi ngưỡng lên nguồn và vào nhật ký (ai, khi nào, mốc nào) — BR-6."""
    source.thresholds = thresholds
    source.save(update_fields=["thresholds"])
    tom_tat = ", ".join(f"{code} {muc['tot']}/{muc['kem']}" for code, muc in thresholds.items()) or "bỏ hết ngưỡng"
    record(AuditAction.UPDATE, actor=actor, target=source.table,
           detail=f"Đặt ngưỡng màu Báo cáo tổng hợp: {tom_tat}", request=request)
    return source
