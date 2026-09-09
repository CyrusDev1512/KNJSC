"""Read-only validation of the single project skill source in .agents.

Standard library only. No downloads, Git mutations, application or database work.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


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


def run(root):
    root = root.resolve()
    errors = []
    manifest = json.loads((root / ".agents/skill-sources.json").read_text(encoding="utf-8"))
    if manifest["schema_version"] != 1 or manifest["canonical_root"] != ".agents/skills":
        raise ValueError("Unsupported manifest or canonical root")
    names = {item["name"] for item in manifest["skills"]}
    if len(names) != 10 or len(manifest["skills"]) != 10:
        errors.append("Expected the approved inventory of 10 unique skills")
    canonical = root / ".agents/skills"
    if {p.name for p in canonical.iterdir() if p.is_dir()} != names:
        errors.append("Skill inventory differs from manifest")
    for item in manifest["skills"]:
        base = inside(root, ".agents/skills/" + item["name"])
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
    for rel in ("ai", ".impeccable", ".claude/skills"):
        if (root / rel).exists():
            errors.append(f"Unexpected legacy directory: {rel}; keep skills in .agents/skills")
    for rel in ("AGENTS.md", "PRODUCT.md", "DESIGN.md", "docs/bo-skill-knjsc.md",
                ".agents/NGUON-THIET-KE.md", ".agents/design-state/design.json"):
        if not (root / rel).is_file():
            errors.append(f"Missing shared context: {rel}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Read-only check (default)")
    parser.parse_args()
    try:
        errors = run(Path(__file__).resolve().parents[1])
    except (ValueError, OSError, KeyError) as exc:
        errors = [str(exc)]
    for error in errors:
        print("FAIL:", error)
    if errors:
        return 1
    print("PASS: 10 skills in .agents/skills; hashes, metadata, provenance and context checked.")
    print("PASS: no ai, root .impeccable or .claude/skills directory.")
    print("Automatic skill selection still requires representative tasks in a new session.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
