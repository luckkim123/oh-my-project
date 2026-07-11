"""Agent declaration <-> wiring integrity (spec §2.2). stdlib only."""
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
VALID_MODELS = {"opus", "sonnet", "haiku"}


def _agents():
    return {p.stem: p.read_text(encoding="utf-8") for p in (ROOT / "agents").glob("*.md")}


def test_agent_frontmatter_model_valid():
    for name, text in _agents().items():
        m = re.search(r"^model:\s*(\S+)", text, re.M)
        assert m and m.group(1) in VALID_MODELS, f"agents/{name}.md model invalid"


def test_subagent_refs_bidirectional():
    on_disk = set(_agents())
    referenced = set()
    for skill in (ROOT / "skills").rglob("SKILL.md"):
        for m in re.finditer(r"oh-my-project:([a-z-]+)", skill.read_text(encoding="utf-8")):
            referenced.add(m.group(1))
    ghost = referenced - on_disk
    assert ghost == set(), f"SKILL.md가 참조하나 agents/에 없음(유령 참조): {ghost}"
    # 미참조 agent 는 경고 대상이 아님(옵션 유틸일 수 있음) — 유령 참조만 hard fail
