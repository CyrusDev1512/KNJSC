"""Điểm đăng ký luật bảng nghiệp vụ; bảng động không import module nghiệp vụ."""

POLICIES = {}


def register(code, policy):
    POLICIES[code] = policy


def for_table(table):
    return POLICIES.get(table.code)
