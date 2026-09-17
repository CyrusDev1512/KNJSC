"""Chuẩn bị dữ liệu SVG cho Bàn điều hành; không phụ thuộc JavaScript."""
from decimal import Decimal


COLORS = ("#3a37a3", "#087f72", "#4f6f9f", "#80558b", "#687386", "#2e7d9a")


def _number(value):
    return Decimal(value or 0)


def bar(title, groups, note="", *, value_label="Số lượng"):
    """Cột ngang 2.5D: mặt trước mang đúng tỷ lệ, chiều sâu cố định 6px."""
    full = [dict(item) for item in groups]
    shown = full[:10]
    maximum = max([_number(item.get("value")) for item in shown] + [Decimal(1)])
    for index, item in enumerate(shown):
        width = _number(item.get("value")) * Decimal(520) / maximum
        width = max(Decimal(0), width)
        item.update(
            color=item.get("color") or COLORS[index % len(COLORS)],
            width=f"{width:.2f}",
            depth_points=f"{width:.2f},4 {width + 6:.2f},0 {width + 6:.2f},18 {width:.2f},22",
        )
    return {
        "kind": "bar", "title": title, "note": note, "groups": shown,
        "table_groups": full, "value_label": value_label,
    }


def line(title, labels, series, note="", *, value_label="Số lượng"):
    """Biểu đồ đường phẳng, tọa độ tính sẵn để HTML không cần script."""
    width, height, left, top = Decimal(680), Decimal(210), Decimal(38), Decimal(14)
    plot_w, plot_h = width - left - Decimal(18), height - top - Decimal(34)
    maximum = max(
        [_number(point) for item in series for point in item.get("values", [])] + [Decimal(1)]
    )
    count = max(len(labels), 1)
    finished = []
    table = [{"label": label, "values": []} for label in labels]
    for index, item in enumerate(series):
        values = [_number(v) for v in item.get("values", [])]
        points = []
        dots = []
        for position, value in enumerate(values):
            x = left + (plot_w * Decimal(position) / Decimal(max(count - 1, 1)))
            y = top + plot_h - (plot_h * value / maximum)
            points.append(f"{x:.2f},{y:.2f}")
            dots.append({
                "x": f"{x:.2f}", "y": f"{y:.2f}", "value": value,
                "label": labels[position] if position < len(labels) else "",
                "show_label": (
                    count <= 12 or position in {0, len(values) - 1}
                    or value == maximum
                ),
                "label_y": f"{max(Decimal(10), y - Decimal(7)):.2f}",
            })
            if position < len(table):
                table[position]["values"].append(value)
        finished.append({**item, "values": values, "points": " ".join(points),
                         "dots": dots, "color": item.get("color") or COLORS[index % len(COLORS)]})
    return {
        "kind": "line", "title": title, "note": note, "labels": labels,
        "series": finished, "table_groups": table, "value_label": value_label,
        "view_width": int(width), "view_height": int(height), "axis_y": f"{top + plot_h:.2f}",
    }


def single_series_from_rows(title, rows, note="", *, value_label="Số lượng"):
    labels = [row["label"] for row in rows]
    return line(title, labels, [{"label": value_label, "values": [row["value"] for row in rows]}],
                note, value_label=value_label)
