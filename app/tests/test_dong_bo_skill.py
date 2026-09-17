"""Bộ skill dùng chung: `.agents/skills` là nguồn, `.claude/skills` là cầu nối
sinh tự động cho Claude Code — hai bên phải khớp nhau (docs/dong-bo-ai-nhieu-may.md)."""
import importlib.util
from pathlib import Path

GOC = Path(__file__).resolve().parents[2]


def _script():
    spec = importlib.util.spec_from_file_location("dong_bo_skill", GOC / "scripts" / "dong-bo-skill.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cau_noi_claude_khop_nguon_agents():
    """Mỗi skill trong `.agents/skill-sources.json` có đúng một cầu nối
    `.claude/skills/<tên>/SKILL.md` sinh từ nguồn, không có cầu nối mồ côi, hash
    nguồn khớp manifest — chạy `python scripts/dong-bo-skill.py --tao-cau-noi` khi đỏ."""
    assert _script().run(GOC) == []


def test_cau_noi_chi_mang_ten_mo_ta_va_tro_ve_nguon():
    """Cầu nối chép nguyên `name`/`description` để Claude tự chọn skill, thân tệp chỉ
    trỏ về tệp nguồn, không chép nội dung."""
    m = _script()
    for thu_muc in sorted((GOC / ".agents" / "skills").iterdir()):
        nguon = m.metadata(thu_muc / "SKILL.md")
        cau_noi = GOC / ".claude" / "skills" / thu_muc.name / "SKILL.md"
        assert m.metadata(cau_noi) == nguon
        assert f".agents/skills/{thu_muc.name}/SKILL.md" in cau_noi.read_text(encoding="utf-8")
        assert cau_noi.stat().st_size < 1500
