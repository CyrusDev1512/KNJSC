"""Kiểm và đồng bộ bộ skill dùng chung cho Codex và Claude Code.

Nội dung thật của mỗi skill nằm **một bản duy nhất** ở `.agents/skills/<tên>/`
(Codex đọc thẳng thư mục này). Claude Code chỉ khám phá `.claude/skills/<tên>/SKILL.md`,
không đọc `.agents/`, nên script sinh ở đó một **tệp cầu nối** cho từng skill:
frontmatter `name`/`description` chép y nguyên để Claude tự chọn skill đúng lúc,
thân tệp chỉ bảo đọc tệp thật. Không chép nội dung, không symlink (Windows
checkout biến symlink thành tệp chữ).

    python scripts/dong-bo-skill.py --check         # chỉ đọc, mặc định
    python scripts/dong-bo-skill.py --tao-cau-noi   # sinh lại 10 cầu nối rồi kiểm

Chỉ dùng thư viện chuẩn. Không tải mạng, không đụng Git, ứng dụng hay database.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

CANONICAL = ".agents/skills"
BRIDGE_ROOT = ".claude/skills"
BRIDGE_BODY = """\
Cầu nối cho Claude Code, sinh bởi `scripts/dong-bo-skill.py --tao-cau-noi`. Đừng sửa
tay: sửa xong ở nguồn thì chạy lại lệnh đó.

Nội dung thật của skill này nằm ở `{source}`. Đọc tệp đó và làm đúng theo nó.
Mọi đường dẫn tương đối trong đó (`reference/`, `references/`, `scripts/`, `agents/`)
tính từ thư mục `{folder}/`. Quy tắc dự án ở `AGENTS.md` đứng trên skill.
"""


def inside(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Path outside repository: {relative}")
    return path


def metadata(path):
    text = path.read_text(encoding="utf-8")
    front = re.match(r"\A---\r?\n(.*?)\r?\n---", text, re.S)
    if not front:
        raise ValueError(f"Missing frontmatter: {path}")
    values = {}
    for key in ("name", "description"):
        match = re.search(rf"^{key}: (.+)$", front[1], re.M)
        if not match:
            raise ValueError(f"Expected single-line {key}: {path}")
        value = match[1].strip()
        if value.startswith('"'):
            value = json.loads(value)
        if value in ("|", ">"):
            raise ValueError(f"Multiline {key} is not supported: {path}")
        values[key] = value
    return values


def bridge_text(name, description):
    """Nội dung cầu nối cho một skill — cùng một hàm dùng để sinh và để kiểm."""
    folder = f"{CANONICAL}/{name}"
    return (
        "---\n"
        f"name: {name}\n"
        f"description: {json.dumps(description, ensure_ascii=False)}\n"
        "---\n\n"
        + BRIDGE_BODY.format(source=f"{folder}/SKILL.md", folder=folder)
    )


def write_bridges(root):
    """Sinh lại `.claude/skills/<tên>/SKILL.md` cho mọi skill trong manifest.
    Trả về danh sách tệp đã ghi."""
    manifest = json.loads((root / ".agents/skill-sources.json").read_text(encoding="utf-8"))
    written = []
    for item in manifest["skills"]:
        source = inside(root, f"{CANONICAL}/{item['name']}/SKILL.md")
        meta = metadata(source)
        target = inside(root, f"{BRIDGE_ROOT}/{item['name']}/SKILL.md")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(bridge_text(meta["name"], meta["description"]), encoding="utf-8", newline="\n")
        written.append(target.relative_to(root).as_posix())
    return written


def check_bridges(root, manifest):
    """Mỗi skill có đúng một cầu nối, nội dung khớp bản sinh từ nguồn; không có cầu nối mồ côi."""
    errors = []
    names = {item["name"] for item in manifest["skills"]}
    bridge_root = root / BRIDGE_ROOT
    if not bridge_root.is_dir():
        return [f"Missing {BRIDGE_ROOT}; run: python scripts/dong-bo-skill.py --tao-cau-noi"]
    present = {p.name for p in bridge_root.iterdir() if p.is_dir()}
    for orphan in sorted(present - names):
        errors.append(f"Orphan bridge without a source skill: {BRIDGE_ROOT}/{orphan}")
    for name in sorted(names):
        source = root / CANONICAL / name / "SKILL.md"
        bridge = bridge_root / name / "SKILL.md"
        if not bridge.is_file():
            errors.append(f"Missing bridge: {BRIDGE_ROOT}/{name}/SKILL.md")
            continue
        meta = metadata(source)
        if bridge.read_text(encoding="utf-8").replace("\r\n", "\n") != bridge_text(meta["name"], meta["description"]):
            errors.append(f"Bridge out of date: {BRIDGE_ROOT}/{name}/SKILL.md; re-run --tao-cau-noi")
        extra = [p for p in (bridge_root / name).rglob("*") if p.is_file() and p != bridge]
        if extra:
            errors.append(f"Bridge folder must contain only SKILL.md: {BRIDGE_ROOT}/{name}")
    return errors


def run(root):
    root = root.resolve()
    errors = []
    manifest = json.loads((root / ".agents/skill-sources.json").read_text(encoding="utf-8"))
    if manifest["schema_version"] != 1 or manifest["canonical_root"] != CANONICAL:
        raise ValueError("Unsupported manifest or canonical root")
    names = {item["name"] for item in manifest["skills"]}
    if len(names) != 10 or len(manifest["skills"]) != 10:
        errors.append("Expected the approved inventory of 10 unique skills")
    canonical = root / CANONICAL
    if {p.name for p in canonical.iterdir() if p.is_dir()} != names:
        errors.append("Skill inventory differs from manifest")
    for item in manifest["skills"]:
        base = inside(root, f"{CANONICAL}/{item['name']}")
        actual = {p.relative_to(base).as_posix() for p in base.rglob("*") if p.is_file()}
        if actual != set(item["files"]):
            errors.append(f"Missing or extra files: {item['name']}")
        for rel, expected in item["files"].items():
            p = inside(base, rel)
            if not p.is_file() or hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest() != expected:
                errors.append(f"Missing or changed skill file: {p.relative_to(root)}")
        entry = base / "SKILL.md"
        if entry.is_file():
            if metadata(entry)["name"] != item["name"]:
                errors.append(f"Metadata name mismatch: {item['name']}")
        if not item.get("license") or not item.get("commit") or not item.get("repository"):
            errors.append(f"Missing provenance: {item['name']}")
    errors.extend(check_bridges(root, manifest))
    for rel in ("ai", ".impeccable"):
        if (root / rel).exists():
            errors.append(f"Unexpected legacy directory: {rel}; keep skills in {CANONICAL}")
    for rel in ("AGENTS.md", "CLAUDE.md", "PRODUCT.md", "DESIGN.md", "docs/bo-skill-knjsc.md",
                ".agents/NGUON-THIET-KE.md", ".agents/design-state/design.json"):
        if not (root / rel).is_file():
            errors.append(f"Missing shared context: {rel}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Chỉ đọc và kiểm (mặc định)")
    parser.add_argument("--tao-cau-noi", action="store_true", dest="tao_cau_noi",
                        help="Sinh lại cầu nối .claude/skills/<tên>/SKILL.md rồi kiểm")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        if args.tao_cau_noi:
            for rel in write_bridges(root):
                print("WROTE:", rel)
        errors = run(root)
    except (ValueError, OSError, KeyError) as exc:
        errors = [str(exc)]
    for error in errors:
        print("FAIL:", error)
    if errors:
        return 1
    print(f"PASS: 10 skills in {CANONICAL}; hashes, metadata, provenance and context checked.")
    print(f"PASS: 10 bridges in {BRIDGE_ROOT} match their sources; no ai or root .impeccable directory.")
    print("Automatic skill selection still requires representative tasks in a new session.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
