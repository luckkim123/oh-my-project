"""Plugin integrity — the 3-way sync invariant (review finding #1).

새 스킬을 추가할 때 세 곳이 동기화돼야 죽은 스킬/죽은 선언이 안 생긴다:
  (1) plugin.json skills[] 등록  (2) skills/omp-*/SKILL.md 실재  (3) route_emit 카탈로그.
기존엔 (3) route 카탈로그만 테스트가 강제했고, (1)·(2)는 미커버라 SKILL.md 삭제·
plugin.json 제거 시에도 테스트가 통과했다(회귀 사각). 이 파일이 그 사각을 메운다.
stdlib only."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
PLUGIN = ROOT / ".claude-plugin" / "plugin.json"
HOOK = ROOT / "hooks" / "omp_route_emit.py"

# route 카탈로그의 STAGE 이름 ↔ skills/omp-<name>/ 폴더 매핑.
# (omp-pilot·omp-doctor 는 'omp-' 접두 그대로, 나머지는 omp-<stage>.)
ROUTE_STAGES = (
    "init", "codify", "organize", "dataset", "env", "doc", "learn", "audit",
    "log", "brief", "review", "handoff",
    "omp-pilot", "omp-doctor",
)


def _plugin_skills():
    pj = json.loads(PLUGIN.read_text(encoding="utf-8"))
    return [s.strip("./") for s in pj["skills"]]


def test_every_registered_skill_has_skill_md():
    """(1)+(2): plugin.json 에 등록된 모든 스킬 경로에 SKILL.md 가 실재한다.
    SKILL.md 를 지우면 이 테스트가 깨진다(죽은 선언 감지)."""
    missing = [s for s in _plugin_skills() if not (ROOT / s / "SKILL.md").is_file()]
    assert missing == [], f"plugin.json 등록됐으나 SKILL.md 없음: {missing}"


def test_every_skill_dir_is_registered():
    """역방향: skills/omp-*/ 디렉토리는 모두 plugin.json 에 등록돼 있다.
    스킬 폴더를 만들고 등록을 잊으면(라우팅에 안 뜸) 깨진다."""
    on_disk = {("skills/" + p.name) for p in (ROOT / "skills").glob("omp-*") if p.is_dir()}
    registered = set(_plugin_skills())
    unregistered = on_disk - registered
    assert unregistered == set(), f"디스크에 있으나 plugin.json 미등록: {unregistered}"


def test_route_catalog_maps_to_real_skill_dirs():
    """(3)↔(2): route_emit 카탈로그의 각 STAGE 이름이 실제 skills/ 폴더와 1:1.
    카탈로그에만 있고 폴더 없는 stage(죽은 라우팅)·폴더만 있고 카탈로그 없는
    stage(발견 안 됨) 양방향을 막는다."""
    out = subprocess.run(
        [sys.executable, str(HOOK)], input='{"prompt":"x"}',
        capture_output=True, text=True,
    ).stdout
    ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    for stage in ROUTE_STAGES:
        name = stage if stage.startswith("omp-") else "omp-" + stage
        assert (ROOT / "skills" / name).is_dir(), \
            f"카탈로그 stage '{stage}' → skills/{name}/ 폴더 없음(죽은 라우팅)"
        assert stage in ctx, f"stage '{stage}' 가 route 카탈로그에 없음"


def test_omp_env_skill_registered():
    """omp-env stage skill exists with valid frontmatter."""
    skill = Path(__file__).parent.parent / "skills" / "omp-env" / "SKILL.md"
    assert skill.exists()
    text = skill.read_text(encoding="utf-8")
    assert text.startswith("---")
    assert "name: omp-env" in text
    # 생성 게이트·정본 위치 불변계약이 본문에 명시되어야 함
    assert ".omp/env/" in text
    assert "dry-run" in text.lower()
    assert "not-a-build-runner" in text.lower() or "not a build runner" in text.lower()


def test_omp_handoff_skill_registered():
    """R4: delegation-briefing skill exists with the §11.2 packet contract."""
    skill = ROOT / "skills" / "omp-handoff" / "SKILL.md"
    assert skill.exists()
    text = skill.read_text(encoding="utf-8")
    assert text.startswith("---") and "name: omp-handoff" in text
    # Anthropic 4-element packet skeleton
    for element in ("Objective", "Output format", "guidance", "Boundaries"):
        assert element in text, f"packet element missing: {element}"
    assert "omx" in text          # explicit target lane (user request 2026-07-11)
    assert "handoff_prepared" in text
    assert ".omp/work/handoffs/" in text
    assert "복붙" in text or "인라인하지 않는다" in text  # reference-only, never inline full docs


def test_handoff_contracts_synced():
    """R4: ledger enum + work layer stay in sync across the three contract docs."""
    proto = (ROOT / "references" / "secretary-protocol.md").read_text(encoding="utf-8")
    assert "handoff_prepared" in proto
    layout = (ROOT / "references" / "output-layout.md").read_text(encoding="utf-8")
    assert "handoffs/" in layout


def test_pipeline_frontmatter_resolves():
    """선택적 next-skill frontmatter 는 실재 skill 디렉토리로 resolve 돼야 한다(§2.6)."""
    import re
    for skill in (ROOT / "skills").rglob("SKILL.md"):
        fm = skill.read_text(encoding="utf-8").split("---")[1]
        m = re.search(r"^next-skill:\s*(\S+)", fm, re.M)
        if m:
            assert (ROOT / "skills" / m.group(1)).is_dir(), \
                f"{skill.parent.name}: next-skill '{m.group(1)}' 폴더 없음"
