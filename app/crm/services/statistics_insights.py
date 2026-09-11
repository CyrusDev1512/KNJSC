"""Sinh tối đa ba nhận định trung tính, có bằng chứng và đường xử lý."""
from decimal import Decimal


def comparison(current, previous, label):
    current, previous = Decimal(current or 0), Decimal(previous or 0)
    if previous == 0:
        if current > 0:
            return f"{label} mới xuất hiện; kỳ trước chưa có cơ sở so sánh."
        return f"{label} chưa có cơ sở so sánh với kỳ trước."
    change = (current - previous) * Decimal(100) / previous
    direction = "tăng" if change > 0 else "giảm" if change < 0 else "không đổi"
    return f"{label} {direction} {abs(change):.1f}% so với kỳ trước."


def item(priority, situation, evidence, source, href, tone="neutral"):
    return {"priority": priority, "situation": situation, "evidence": evidence,
            "source": source, "href": href, "tone": tone}


def threshold(column, value, source, href):
    """Nhận định ngưỡng chỉ xuất hiện khi cột đã được cấu hình."""
    if not column or not column.alert_op or column.alert_value is None or value is None:
        return None
    actual, limit = Decimal(value), Decimal(column.alert_value)
    exceeded = actual > limit if column.alert_op == "gt" else actual < limit
    if not exceeded:
        return None
    direction = "cao hơn" if column.alert_op == "gt" else "thấp hơn"
    return item(
        2,
        f"{column.name} vượt ngưỡng đã cấu hình",
        f"Giá trị {actual:.2f}, {direction} ngưỡng {limit:.2f} của bảng.",
        source,
        href,
        "warning",
    )


def top(items):
    return sorted(items, key=lambda value: value["priority"])[:3]
