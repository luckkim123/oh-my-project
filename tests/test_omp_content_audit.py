"""Tests for omp content_conventions + wikilink audit pure functions."""
from datetime import datetime
from pathlib import Path

from hooks.omp_content_audit import (
    check_content_rule, find_dead_links, split_frontmatter,
    scan_structure_drift, lint_wiki,
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
