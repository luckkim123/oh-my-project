"""Release 2 (R2): para preset must connect its known state surfaces to the
secretary.sources[] codify proposal — proposal-only, never auto-registered."""
from pathlib import Path

PARA = Path(__file__).parent.parent / "references" / "presets" / "para.md"
ORGANIZE = Path(__file__).parent.parent / "skills" / "omp-organize" / "SKILL.md"


def test_para_proposes_secretary_sources():
    text = PARA.read_text(encoding="utf-8")
    assert "secretary.sources" in text
    # the three known surfaces the design names (para.md §0 signals / §4-3 whitelist)
    assert "Kanban.md" in text and "daily_notes" in text and "Dashboard.md" in text
    # framing: proposal through the codify gate, no auto-registration
    assert "propose" in text.lower() or "제안" in text
    assert "auto-register" in text.lower() or "자동 등록" in text


def test_organize_dry_run_carries_wikilink_inbound_counts():
    text = ORGANIZE.read_text(encoding="utf-8")
    assert "[[" in text and "inbound" in text.lower()
    assert "para" in text.lower()  # scoped to para-preset projects
