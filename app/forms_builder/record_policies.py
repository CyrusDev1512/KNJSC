"""Điểm đăng ký luật bảng nghiệp vụ; bảng động không import module nghiệp vụ."""

POLICIES = {}


def register(code, policy):
    POLICIES[code] = policy


def for_table(table):
    return POLICIES.get(table.code)


GRID_POLICIES = {}


def register_grid(code, policy):
    """Đăng ký phần trình bày; không thay quy tắc nhập/ghi của bảng."""
    GRID_POLICIES[code] = policy


def grid_for(table):
    return GRID_POLICIES.get(table.code) or for_table(table)
