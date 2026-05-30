"""Tests for omp content_conventions + wikilink audit pure functions."""
from hooks.omp_content_audit import check_content_rule, find_dead_links, split_frontmatter


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
