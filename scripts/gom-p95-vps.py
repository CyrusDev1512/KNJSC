#!/usr/bin/env python3
"""Gom p95 thật của KN CRM từ log VPS — đóng khoản nợ "chưa đo trên VPS".

**Không đo gì mới.** Số liệu đã có sẵn: `deploy/production/compose.yml` đặt
`CRM_REQUEST_METRICS: '1'`, nên `core/request_metrics.py` ghi **một dòng JSON
cho mỗi yêu cầu** ra stdout của container, và Docker giữ chúng. Script này chỉ
đọc lại, gom theo tuyến và tính phân vị. Nghĩa là chạy lần đầu đã có ngay lịch
sử của những ngày qua, không phải chờ hứng số mới.

Chạy **trên VPS** (Claude Code trên web không tới được VPS — CLAUDE.md):

    cd /opt/knjsc-runtime
    python3 /opt/knjsc/scripts/gom-p95-vps.py --since 24h
    python3 /opt/knjsc/scripts/gom-p95-vps.py --since 7d --json bien-ban.json
    python3 /opt/knjsc/scripts/gom-p95-vps.py --tep dalu.log        # tệp đã lưu
    docker compose logs --no-color crm | python3 .../gom-p95-vps.py --tep -

Ngưỡng lấy đúng theo `app/core/constants.py` (ADR-016, chủ dự án chốt 16.09):
đọc p95 ≤ 1000 ms, ghi ≤ 500 ms, hỏi thăm ≤ 300 ms.

Mã thoát: 0 khi mọi nhóm đạt, 1 khi có nhóm không đạt, 2 khi không đủ mẫu để
kết luận. Nhờ vậy cắm được vào cron hay CI.

Chỉ dùng thư viện chuẩn của Python — quy tắc 8, không thêm phụ thuộc.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from collections import defaultdict

# ── Ngưỡng, chép từ core/constants.py ────────────────────────────────
# Chép chứ không nhập: script chạy trên máy chủ ngoài container, không có
# Django trên đường dẫn. Đổi ngưỡng thì đổi cả hai chỗ — bài kiểm canh việc đó.
READ_P95_MS = 1000
WRITE_P95_MS = 500
POLL_P95_MS = 300

#: Dưới ngần này mẫu thì p95 không có nghĩa, chỉ là số lớn nhất trong nhúm nhỏ.
MIN_SAMPLES_VERDICT = 20
#: Dưới ngần này thì không kết luận gì cả.
MIN_SAMPLES_ANY = 5

#: Tuyến chậm theo bản chất, không tính vào phán quyết nhóm nhưng vẫn in ra:
#: nhập tệp, xuất tệp, tải mẫu, đăng nhập (băm mật khẩu cố ý chậm).
SLOW_BY_DESIGN = ("nhap/", "xuat/", "mau-nhap.xlsx", "dang-nhap/", "tai/", "sao-luu")

GROUPS = {
    "doc": ("Đọc", READ_P95_MS),
    "ghi": ("Ghi", WRITE_P95_MS),
    "hoi_tham": ("Hỏi thăm", POLL_P95_MS),
}

#: Dòng log có tiền tố của Docker và của Django trước phần JSON.
#: Bắt object JSON cuối dòng, không cắt theo cột — tiền tố đổi theo phiên bản.
JSON_TAIL = re.compile(r"\{.*\}\s*$")


class Bucket:
    """Số đo gom của một tuyến hoặc một nhóm.

    Lớp thường chứ không phải `dataclass`: script này được nạp cả bằng
    `importlib.util.spec_from_file_location` (bài kiểm, và bất kỳ ai muốn gọi
    lại hàm), mà `dataclass` cần module có mặt trong `sys.modules` mới dựng
    được. Bớt phép thuật lúc nạp thì chạy được ở mọi chỗ.
    """

    def __init__(self) -> None:
        self.durations: list[float] = []
        self.db_ms: list[float] = []
        self.queries: list[int] = []
        self.errors = 0
        self.methods: set[str] = set()

    def add(self, entry: dict) -> None:
        self.durations.append(float(entry["ms"]))
        if isinstance(entry.get("db_ms"), (int, float)):
            self.db_ms.append(float(entry["db_ms"]))
        if isinstance(entry.get("queries"), int):
            self.queries.append(entry["queries"])
        if isinstance(entry.get("status"), int) and entry["status"] >= 500:
            self.errors += 1
        if entry.get("method"):
            self.methods.add(entry["method"])


def percentile(values: list[float], pct: float) -> float:
    """Phân vị theo **thứ hạng gần nhất** (nearest-rank), không nội suy.

    Chọn cách này vì nó trả về một giá trị **đã thật sự xảy ra**, nên đối
    chiếu được với một dòng log cụ thể khi cần truy nguyên. Nội suy cho số
    mượt hơn nhưng là số chưa ai từng gặp.
    """
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = math.ceil(pct / 100 * len(ordered))
    return ordered[min(max(rank, 1), len(ordered)) - 1]


def classify(entry: dict) -> str:
    """Xếp một yêu cầu vào nhóm: hỏi thăm, ghi, hay đọc.

    Xếp theo **phương thức HTTP cộng đuôi tuyến**, không theo danh sách tuyến
    liệt kê tay: thêm tuyến mới thì không phải sửa script, và không có tuyến
    nào lặng lẽ rơi ra ngoài mọi nhóm.
    """
    route = entry.get("route") or ""
    if route.endswith("moi-nhat/"):
        return "hoi_tham"
    if entry.get("method") in ("POST", "PUT", "PATCH", "DELETE"):
        return "ghi"
    return "doc"


def is_slow_by_design(route: str) -> bool:
    return any(mark in route for mark in SLOW_BY_DESIGN)


def read_lines(args: argparse.Namespace) -> tuple[list[str], str]:
    """Lấy dòng log, từ tệp hoặc từ `docker compose logs`. Trả kèm mô tả nguồn."""
    if args.tep == "-":
        return sys.stdin.read().splitlines(), "đầu vào chuẩn"
    if args.tep:
        with open(args.tep, encoding="utf-8", errors="replace") as fh:
            return fh.read().splitlines(), f"tệp {args.tep}"

    base = ["docker", "compose"]
    for path in args.compose:
        base += ["-f", path]

    # `--no-log-prefix` cho log sạch hơn nhưng chỉ có ở Docker Compose đủ mới.
    # Không đoán phiên bản trên máy chủ: thử có cờ, hỏng thì thử lại không cờ.
    # Bộ đọc bắt JSON ở cuối dòng nên còn tiền tố cũng không sao.
    for flags in (["--no-log-prefix"], []):
        command = base + ["logs", "--no-color", *flags, "--since", args.since, args.dich_vu]
        try:
            done = subprocess.run(command, capture_output=True, text=True, timeout=args.timeout)
        except FileNotFoundError:
            sys.exit("Không thấy lệnh `docker`. Chạy script này trên VPS, hoặc dùng --tep.")
        except subprocess.TimeoutExpired:
            sys.exit(f"`docker compose logs` quá {args.timeout} giây. Thu hẹp --since rồi thử lại.")
        if done.returncode == 0:
            return done.stdout.splitlines(), f"docker compose logs {args.dich_vu} --since {args.since}"
        loi = done.stderr.strip()

    sys.exit(f"`docker compose logs` lỗi:\n{loi[:800]}")


def parse(lines: list[str]) -> tuple[list[dict], int]:
    """Đọc các dòng của logger `knjsc.request`. Trả `(bản ghi, số dòng bỏ qua)`.

    Bỏ qua lặng lẽ mọi dòng không phải số đo (khởi động, cảnh báo, traceback)
    — chúng chiếm phần lớn log và không phải lỗi.
    """
    entries, skipped = [], 0
    for line in lines:
        match = JSON_TAIL.search(line)
        if not match:
            continue
        try:
            entry = json.loads(match.group(0))
        except ValueError:
            skipped += 1
            continue
        if isinstance(entry, dict) and "ms" in entry and "route" in entry:
            entries.append(entry)
    return entries, skipped


def summarise(bucket: Bucket) -> dict:
    d = bucket.durations
    return {
        "so_yeu_cau": len(d),
        "p50": round(percentile(d, 50), 1),
        "p90": round(percentile(d, 90), 1),
        "p95": round(percentile(d, 95), 1),
        "p99": round(percentile(d, 99), 1),
        "max": round(max(d), 1) if d else 0.0,
        "db_ms_p95": round(percentile(bucket.db_ms, 95), 1) if bucket.db_ms else None,
        "truy_van_p95": int(percentile([float(q) for q in bucket.queries], 95)) if bucket.queries else None,
        "loi_5xx": bucket.errors,
    }


def verdict(p95: float, limit: int, samples: int) -> str:
    if samples < MIN_SAMPLES_ANY:
        return "thiếu mẫu"
    if samples < MIN_SAMPLES_VERDICT:
        return "ĐẠT (ít mẫu)" if p95 <= limit else "KHÔNG ĐẠT (ít mẫu)"
    return "ĐẠT" if p95 <= limit else "KHÔNG ĐẠT"


def build_report(entries: list[dict], source: str, skipped: int) -> dict:
    by_group: dict[str, Bucket] = defaultdict(Bucket)
    by_route: dict[tuple[str, str], Bucket] = defaultdict(Bucket)

    for entry in entries:
        route = entry.get("route") or "(không rõ)"
        group = classify(entry)
        by_route[(group, route)].add(entry)
        if not is_slow_by_design(route):
            by_group[group].add(entry)

    groups = {}
    for key, (label, limit) in GROUPS.items():
        bucket = by_group.get(key, Bucket())
        stats = summarise(bucket)
        groups[key] = {
            "nhan": label, "nguong_p95_ms": limit,
            "ket_luan": verdict(stats["p95"], limit, stats["so_yeu_cau"]), **stats,
        }

    routes = []
    for (group, route), bucket in sorted(by_route.items(), key=lambda kv: -percentile(kv[1].durations, 95)):
        routes.append({
            "nhom": GROUPS[group][0], "tuyen": route,
            "phuong_thuc": "/".join(sorted(bucket.methods)),
            "cham_theo_ban_chat": is_slow_by_design(route),
            **summarise(bucket),
        })

    return {
        "nguon": source,
        "tong_yeu_cau": len(entries),
        "dong_bo_qua": skipped,
        "nhom": groups,
        "tuyen": routes,
    }


def _in_khong_co_so_do() -> None:
    """Bảng rỗng là lúc người vận hành cần chỉ dẫn nhất, không phải lúc im lặng."""
    print("\nKhông có dòng số đo nào. Ba nguyên nhân thường gặp:")
    print("  1. CRM_REQUEST_METRICS chưa bật — kiểm `docker compose exec crm env | grep CRM_REQUEST`")
    print("  2. Khoảng --since quá hẹp, hoặc log đã bị xoay vòng mất")
    print("  3. Sai tên dịch vụ — KN CRM là `crm`, KN ERP là `erp`")


def _in_nhom(nhom: dict) -> None:
    print("\n── Theo nhóm (đã loại các tuyến chậm theo bản chất) ──")
    head = f"{'Nhóm':<11}{'Số':>7}{'p50':>8}{'p95':>9}{'p99':>9}{'Ngưỡng':>9}  Kết luận"
    print(head)
    print("─" * (len(head) + 8))
    for data in nhom.values():
        print(f"{data['nhan']:<11}{data['so_yeu_cau']:>7}{data['p50']:>8.0f}{data['p95']:>9.0f}"
              f"{data['p99']:>9.0f}{data['nguong_p95_ms']:>9}  {data['ket_luan']}")

    thieu = [d["nhan"] for d in nhom.values() if d["so_yeu_cau"] < MIN_SAMPLES_VERDICT]
    if thieu:
        print(f"\n  ⚠ Nhóm {', '.join(thieu)} dưới {MIN_SAMPLES_VERDICT} mẫu — p95 ở đó chưa nói lên điều gì."
              "\n    Nới --since, hoặc đo lại sau một ngày làm việc thật.")


def _in_tuyen(tuyen: list) -> None:
    print("\n── Mười tuyến chậm nhất theo p95 ──")
    head = f"{'p95':>8}{'p99':>8}{'Số':>7}{'db p95':>9}{'TV':>5}  Tuyến"
    print(head)
    print("─" * (len(head) + 20))
    for route in tuyen:
        mark = " *" if route["cham_theo_ban_chat"] else ""
        db = f"{route['db_ms_p95']:.0f}" if route["db_ms_p95"] is not None else "—"
        tv = route["truy_van_p95"] if route["truy_van_p95"] is not None else "—"
        print(f"{route['p95']:>8.0f}{route['p99']:>8.0f}{route['so_yeu_cau']:>7}{db:>9}{tv:>5}  "
              f"{route['tuyen']}{mark}")
    if any(r["cham_theo_ban_chat"] for r in tuyen):
        print("\n  * chậm theo bản chất (nhập, xuất, đăng nhập) — không tính vào phán quyết nhóm")

    print("\n  TV = số truy vấn cơ sở dữ liệu (p95). db p95 gần bằng p95 tổng nghĩa là nghẽn ở")
    print("  cơ sở dữ liệu; chênh nhau nhiều nghĩa là nghẽn ở Python hoặc ở hàng đợi.")


def print_report(report: dict) -> None:
    print(f"\nNguồn: {report['nguon']}")
    print(f"Tổng số yêu cầu đọc được: {report['tong_yeu_cau']}"
          + (f" (bỏ qua {report['dong_bo_qua']} dòng không đọc được)" if report["dong_bo_qua"] else ""))

    if not report["tong_yeu_cau"]:
        _in_khong_co_so_do()
        return

    _in_nhom(report["nhom"])
    _in_tuyen(report["tuyen"][:10])

    loi = sum(d["loi_5xx"] for d in report["nhom"].values())
    if loi:
        print(f"\n  ⚠ {loi} yêu cầu trả 5xx trong khoảng này.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Gom p95 thật của KN CRM từ log VPS.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Chạy trên VPS. Ngưỡng theo ADR-016: đọc 1000 ms, ghi 500 ms, hỏi thăm 300 ms.",
    )
    parser.add_argument("--since", default="24h", help="khoảng thời gian cho docker logs (mặc định 24h)")
    parser.add_argument("--dich-vu", default="crm", help="tên service: crm cho KN CRM, erp cho KN ERP")
    parser.add_argument("--compose", action="append", default=[],
                        help="tệp compose, lặp lại được; mặc định để docker tự tìm")
    parser.add_argument("--tep", help="đọc từ tệp thay vì docker; '-' là đầu vào chuẩn")
    parser.add_argument("--json", dest="json_path", help="ghi thêm kết quả dạng JSON vào tệp này")
    parser.add_argument("--timeout", type=int, default=180, help="giây, cho docker compose logs")
    args = parser.parse_args(argv)

    lines, source = read_lines(args)
    entries, skipped = parse(lines)
    report = build_report(entries, source, skipped)
    print_report(report)

    if args.json_path:
        with open(args.json_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)
        print(f"\nĐã ghi {args.json_path}")

    ket_luan = [d["ket_luan"] for d in report["nhom"].values()]
    if any(k.startswith("KHÔNG ĐẠT") for k in ket_luan):
        return 1
    if all(k == "thiếu mẫu" for k in ket_luan):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
