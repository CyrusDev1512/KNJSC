"""Điểm đăng ký luật bảng nghiệp vụ; bảng động không import module nghiệp vụ."""

POLICIES = {}
WORKFLOW_POLICIES = {}


def register(code, policy):
    POLICIES[code] = policy


def for_table(table):
    return POLICIES.get(table.code) or WORKFLOW_POLICIES.get(getattr(table, "workflow", ""))


GRID_POLICIES = {}


def register_grid(code, policy):
    """Đăng ký phần trình bày; không thay quy tắc nhập/ghi của bảng."""
    GRID_POLICIES[code] = policy


def grid_for(table):
    return GRID_POLICIES.get(table.code) or for_table(table)


def register_workflow(name, policy):
    WORKFLOW_POLICIES[name] = policy
