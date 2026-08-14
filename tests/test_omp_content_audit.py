"""Tests for omp content_conventions + wikilink audit pure functions."""
from datetime import datetime
from pathlib import Path

from hooks.omp_content_audit import (
    check_content_rule,
    find_dead_links,
    lint_wiki,
    scan_structure_drift,
    split_frontmatter,
)


def test_present_rule_passes_when_section_exists(tmp_path):
    f = tmp_path / "note.md"
    f.write_text("# Title\n\n## Main Ideas\n\nstuff\n")
    rule = {"applies_to": "*.md", "check": {"pattern": "^## Main Ideas$", "expect": "present"}, "severity": "warn"}
    violations = check_content_rule(rule, [f])
    assert violations == []


def test_present_rule_flags_when_section_missing(tmp_path):
    f = tmp_path / "note.md"
    f.write_text("# Title\n\nno sections here\n")
    rule = {"applies_to": "*.md", "check": {"pattern": "^## Main Ideas$", "expect": "present"}, "severity": "warn"}
    violations = check_content_rule(rule, [f])
    assert len(violations) == 1
    assert violations[0]["file"].endswith("note.md")
    assert violations[0]["severity"] == "warn"


def test_absent_rule_flags_when_forbidden_pattern_present(tmp_path):
    f = tmp_path / "c.md"
    f.write_text("1. first\n2. second\n")
    rule = {"applies_to": "*.md", "check": {"pattern": r"^\d+\.", "expect": "absent"}, "severity": "info"}
    violations = check_content_rule(rule, [f])
    assert len(violations) == 1


def test_frontmatter_scope_isolates_yaml_from_body(tmp_path):
    f = tmp_path / "t.md"
    f.write_text("---\ntitle: x\n---\n\n## Main Ideas\nbody\n")
    # rule looks for '## Main Ideas' but ONLY in frontmatter scope → must not match (it's in body)
    rule = {"applies_to": "*.md",
            "check": {"pattern": "^## Main Ideas$", "expect": "present", "scope": "frontmatter"},
            "severity": "warn"}
    violations = check_content_rule(rule, [f])
    assert len(violations) == 1  # present-required but absent from frontmatter scope


def test_split_frontmatter_extracts_yaml_block():
    body = "---\ntitle: x\ntags: [A]\n---\n\ncontent\n"
    fm, rest = split_frontmatter(body)
    assert "title: x" in fm
    assert "content" in rest
    assert "title" not in rest


def test_dead_link_detected(tmp_path):
    (tmp_path / "a.md").write_text("see [[b]] and [[missing]]\n")
    (tmp_path / "b.md").write_text("target\n")
    dead = find_dead_links(tmp_path)
    targets = {d["target"] for d in dead}
    assert "missing" in targets
    assert "b" not in targets


def test_link_alias_and_heading_resolve(tmp_path):
    (tmp_path / "a.md").write_text("[[b|alias]] and [[b#section]] and ![[b]]\n")
    (tmp_path / "b.md").write_text("x\n")
    dead = find_dead_links(tmp_path)
    assert dead == []


def test_non_md_embed_skipped_but_real_miss_dead(tmp_path):
    # fix1: non-md embed (.png) skipped even though no png file exists;
    # extension-less true miss still flagged.
    (tmp_path / "a.md").write_text("![[diagram.png]] and [[realmissing]]\n")
    dead = find_dead_links(tmp_path)
    targets = {d["target"] for d in dead}
    assert "diagram.png" not in targets
    assert "realmissing" in targets


def test_case_insensitive_resolution(tmp_path):
    # fix2: [[Note]] resolves against note.md (Obsidian wikilinks are case-insensitive).
    (tmp_path / "a.md").write_text("[[Note]]\n")
    (tmp_path / "note.md").write_text("x\n")
    dead = find_dead_links(tmp_path)
    assert dead == []


def test_md_target_resolves_against_stem(tmp_path):
    # fix3: an explicit .md target resolves against the stem set (no f.name dup needed).
    (tmp_path / "a.md").write_text("[[b.md]]\n")
    (tmp_path / "b.md").write_text("x\n")
    dead = find_dead_links(tmp_path)
    assert dead == []


def test_split_frontmatter_handles_crlf():
    # fix4: CRLF frontmatter fences split correctly.
    fm, rest = split_frontmatter("---\r\ntitle: x\r\n---\r\n\r\nbody\r\n")
    assert "title: x" in fm
    assert "body" in rest
    assert "title" not in rest


def test_table_escaped_pipe_link_resolves(tmp_path):
    # Obsidian table cell: [[Note\|alias]] — escaped pipe must still resolve to Note.md
    (tmp_path / "a.md").write_text("| x | [[Perceptron\\|MLP]] | and [[Perceptron\\|MLP]] |\n")
    (tmp_path / "Perceptron.md").write_text("p\n")
    dead = find_dead_links(tmp_path)
    assert dead == []  # escaped-pipe alias resolves, not dead


# --- scan_structure_drift (roadmap #8b) ---

def test_scan_structure_drift_flags_missing_path(tmp_path):
    (tmp_path / "exists").mkdir()
    rules = {"structure": {"directories": [
        {"path": "exists"}, {"path": "ghost/dir"}]}}
    finds = scan_structure_drift(tmp_path, rules)
    assert [f["path"] for f in finds] == ["ghost/dir"]


def test_scan_structure_drift_reads_backtick_paths_from_structure_md(tmp_path):
    (tmp_path / ".omp").mkdir()
    (tmp_path / ".omp" / "STRUCTURE.md").write_text("Data lives under `data/raw/` per convention.\n")
    finds = scan_structure_drift(tmp_path, {"structure": {"directories": []}})
    assert [f["path"] for f in finds] == ["data/raw"]


# --- lint_wiki (roadmap #8c) ---

def test_wiki_lint_orphan_stale_oversized(tmp_path):
    wiki = tmp_path / ".omp" / "wiki"
    wiki.mkdir(parents=True)
    (wiki / "orphan.md").write_text("no links here")
    (wiki / "hub.md").write_text("see [[orphan]]")   # orphan 은 피링크됨 → hub 가 orphan
    (wiki / "big.md").write_text("x" * 60_000)
    kinds = {(f["kind"], Path(f["path"]).name) for f in lint_wiki(tmp_path, now=datetime(2026, 7, 11))}
    assert ("orphan", "hub.md") in kinds and ("oversized", "big.md") in kinds


def test_wiki_open_item_flags_unchecked_boxes_only(tmp_path):
    """열린 체크박스만 open_item. 닫힌 것·산문은 안 걸린다."""
    wiki = tmp_path / ".omp" / "wiki"
    wiki.mkdir(parents=True)
    (wiki / "plan.md").write_text(
        "# plan\n\n"
        "- [ ] krit Kanban 결합 해제\n"
        "* [ ] workspace 이주 2차\n"
        "+ [ ]   앞뒤 공백 있는 항목\n"
        "- [x] 이미 끝난 것\n"
        "- [X] 대문자로 닫은 것\n"
        "- 그냥 항목\n"
    )
    finds = [f for f in lint_wiki(tmp_path, now=datetime(2026, 7, 11)) if f["kind"] == "open_item"]
    assert len(finds) == 1, finds
    assert finds[0]["detail"].startswith("3 unchecked: ")
    assert "이미 끝난 것" not in finds[0]["detail"]


def test_wiki_open_item_does_not_fire_on_prose_markers(tmp_path):
    """오탐 회귀 — 산문 스캔을 기각한 이유가 여기 박혀 있다.

    실측(2026-08-14, 한 vault): 산문 마커(미결/TODO/보류) 매칭은 7건 중 3건이 오탐이었다.
    해소를 *선언하는* 제목이 걸리고, 파일명 `RL-ALBC - TODO.md` 가 걸린다. 아래 본문은
    그 세 부류를 그대로 담았으며 open_item 은 0건이어야 한다.
    """
    wiki = tmp_path / ".omp" / "wiki"
    wiki.mkdir(parents=True)
    (wiki / "history.md").write_text(
        "### 미결 (omp-organize 별도 세션 대상)\n"
        "init 범위 밖이라 미실행. 이동 대상 후보:\n\n"
        "## 2026-08-14 — 이주 2차 실행, 1차 미결 전부 해소\n"
        "- dead link: `RL-ALBC - TODO.md:242` 가 이주된 reviews 를 가리킴\n"
        "- **보류: krit/Kanban.md** — 병렬 세션이 재편 중\n"
        "TODO 라는 단어가 산문에 있어도 항목이 아니다.\n"
    )
    assert not [f for f in lint_wiki(tmp_path, now=datetime(2026, 7, 11)) if f["kind"] == "open_item"]


def test_wiki_open_item_is_per_file_not_per_note_body_leak(tmp_path):
    """노트마다 자기 본문을 읽는가 (첫 루프의 text 가 새면 마지막 노트가 전파된다)."""
    wiki = tmp_path / ".omp" / "wiki"
    wiki.mkdir(parents=True)
    (wiki / "a-has-items.md").write_text("see [[b-clean]]\n- [ ] 유일한 열린 항목\n")
    (wiki / "b-clean.md").write_text("see [[a-has-items]]\n본문에 체크박스 없음\n")
    finds = [f for f in lint_wiki(tmp_path, now=datetime(2026, 7, 11)) if f["kind"] == "open_item"]
    assert [Path(f["path"]).name for f in finds] == ["a-has-items.md"]


def test_learned_stuck_candidate_flagged_below_threshold_and_stale(tmp_path):
    (tmp_path / ".omp").mkdir()
    learned = tmp_path / ".omp" / "learned.md"
    learned.write_text(
        "## OBS-0001  rare pattern seen once\n"
        "- id: OBS-0001\n"
        "- channel: rule\n"
        "- status: candidate\n"
        "- pattern: something rare\n"
        "- evidence_count: 1\n"
        "- first_seen: 2026-01-01\n"
        "- last_seen: 2026-01-01\n"
        "- user_overridden: false\n"
        "- source_stage: audit\n"
    )
    finds = lint_wiki(tmp_path, now=datetime(2026, 7, 11))
    stuck = [f for f in finds if f["kind"] == "stuck_candidate"]
    assert [f["path"] for f in stuck] == ["OBS-0001"]
    # evidence_count 1 (< 3) is NOT ready to promote
    assert not [f for f in finds if f["kind"] == "ready_to_promote"]


def test_learned_ready_to_promote_flagged_at_threshold(tmp_path):
    # a candidate that reached evidence_count>=3 is ripe for omp-learn promotion.
    # Without this it produces NO finding at all (stuck fires only < 3) -> invisible
    # to enumeration = the family failure class this closes.
    (tmp_path / ".omp").mkdir()
    (tmp_path / ".omp" / "learned.md").write_text(
        "## OBS-0009  ripe pattern\n"
        "- id: OBS-0009\n"
        "- channel: rule\n"
        "- status: candidate\n"
        "- pattern: seen enough\n"
        "- evidence_count: 3\n"
        "- first_seen: 2026-06-01\n"
        "- last_seen: 2026-07-01\n"
        "- user_overridden: false\n"
        "- source_stage: audit\n"
    )
    finds = lint_wiki(tmp_path, now=datetime(2026, 7, 11))
    ready = [f for f in finds if f["kind"] == "ready_to_promote"]
    assert [f["path"] for f in ready] == ["OBS-0009"]
    assert not [f for f in finds if f["kind"] == "stuck_candidate"]


def test_learned_contradiction_flagged_for_conflicting_path_constraint(tmp_path):
    (tmp_path / ".omp").mkdir()
    learned = tmp_path / ".omp" / "learned.md"
    learned.write_text(
        "## OBS-0002  pkl under data/processed\n"
        "- id: OBS-0002\n"
        "- channel: rule\n"
        "- status: candidate\n"
        "- pattern: pkl under data/processed\n"
        "- evidence_count: 4\n"
        "- first_seen: 2026-06-01\n"
        "- last_seen: 2026-06-10\n"
        "- user_overridden: false\n"
        "- source_stage: audit\n"
        "- applies_to: **/*.pkl\n"
        "- path_constraint: data/processed\n"
        "\n"
        "## OBS-0003  pkl under outputs\n"
        "- id: OBS-0003\n"
        "- channel: rule\n"
        "- status: candidate\n"
        "- pattern: pkl under outputs\n"
        "- evidence_count: 3\n"
        "- first_seen: 2026-06-05\n"
        "- last_seen: 2026-06-11\n"
        "- user_overridden: false\n"
        "- source_stage: audit\n"
        "- applies_to: **/*.pkl\n"
        "- path_constraint: outputs/models\n"
    )
    finds = lint_wiki(tmp_path, now=datetime(2026, 7, 11))
    contradictions = [f for f in finds if f["kind"] == "contradiction"]
    assert len(contradictions) == 1
    assert contradictions[0]["path"] == "**/*.pkl"


def test_learned_counter_example_blocks_ready_to_promote(tmp_path):
    # protocol §3.2: counter_examples > 0 kills promotion outright, regardless
    # of evidence_count — must NOT surface as ready_to_promote
    (tmp_path / ".omp").mkdir()
    (tmp_path / ".omp" / "learned.md").write_text(
        "## OBS-0010  strong but violated pattern\n"
        "- id: OBS-0010\n"
        "- channel: rule\n"
        "- status: candidate\n"
        "- pattern: everything lives under data/\n"
        "- evidence_count: 5\n"
        "- counter_examples: 3\n"
        "- first_seen: 2026-07-01\n"
        "- last_seen: 2026-07-10\n"
        "- user_overridden: false\n"
        "- source_stage: audit\n"
    )
    finds = lint_wiki(tmp_path, now=datetime(2026, 7, 11))
    assert not [f for f in finds if f["kind"] == "ready_to_promote"]


def test_learned_malformed_counter_examples_blocks_ready_to_promote(tmp_path):
    # the ValueError fallback for counter_examples must be conservative (block
    # promotion), not permissive (default to 0 -> treated as "no counter-examples").
    # A garbage/unparseable value means "unknown", never "safe to promote".
    (tmp_path / ".omp").mkdir()
    (tmp_path / ".omp" / "learned.md").write_text(
        "## OBS-0012  malformed counter_examples\n"
        "- id: OBS-0012\n"
        "- channel: rule\n"
        "- status: candidate\n"
        "- pattern: garbage counter_examples value\n"
        "- evidence_count: 5\n"
        "- counter_examples: not-a-number\n"
        "- first_seen: 2026-07-01\n"
        "- last_seen: 2026-07-10\n"
        "- user_overridden: false\n"
        "- source_stage: audit\n"
    )
    finds = lint_wiki(tmp_path, now=datetime(2026, 7, 11))
    assert not [f for f in finds if f["kind"] == "ready_to_promote"]


def test_learned_user_overridden_blocks_ready_to_promote(tmp_path):
    # protocol §3.3: the user's "no" is durable — an overridden candidate must
    # NOT surface as ready_to_promote however much evidence accrues
    (tmp_path / ".omp").mkdir()
    (tmp_path / ".omp" / "learned.md").write_text(
        "## OBS-0011  user already said no\n"
        "- id: OBS-0011\n"
        "- channel: rule\n"
        "- status: candidate\n"
        "- pattern: rename all notebooks\n"
        "- evidence_count: 4\n"
        "- counter_examples: 0\n"
        "- first_seen: 2026-07-01\n"
        "- last_seen: 2026-07-10\n"
        "- user_overridden: true\n"
        "- source_stage: audit\n"
    )
    finds = lint_wiki(tmp_path, now=datetime(2026, 7, 11))
    assert not [f for f in finds if f["kind"] == "ready_to_promote"]
