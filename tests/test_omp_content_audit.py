"""Tests for omp content_conventions + wikilink audit pure functions."""
from datetime import datetime
from pathlib import Path

import subprocess

from hooks.omp_content_audit import (
    check_content_rule,
    find_dead_links,
    lint_wiki,
    scan_layers,
    scan_open_items,
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


def test_scan_structure_drift_skips_template_placeholders(tmp_path):
    """`YYYY`/`NNNN`/`...` 가 든 백틱은 경로가 아니라 *모양*이라 잡으면 안 된다.

    실측(2026-08-14, 한 vault): structure_drift 13건 중 4건이 이 부류였다. 대부분이 틀린
    목록은 읽히지 않고, 그러면 섞여 있던 진짜 4건도 같이 안 읽힌다. 그래서 오탐 제거가
    탐지력 유지의 일부다 — 아래 마지막 줄이 그 반대편(진짜 결손은 여전히 잡는다)이다.
    """
    (tmp_path / ".omp").mkdir()
    (tmp_path / ".omp" / "STRUCTURE.md").write_text(
        "| `journal/YYYY-MM-DD.md` | 일일 노트 형식 |\n"
        "| `3_Archive/calendar/daily_notes/YYYY-MM-DD.md` | 같은 부류 |\n"
        "| `decisions/NNNN-slug.md` | ADR 형식 |\n"
        "| `3_Archive/etc/...zip` | 생략 표기 |\n"
        "| `data/raw/` | 진짜 경로인데 디스크에 없다 |\n"
    )
    finds = [f["path"] for f in scan_structure_drift(tmp_path, {"structure": {"directories": []}})]
    assert finds == ["data/raw"], finds


# --- scan_open_items (r7, 2026-08-30: retargeted from wiki notes to post bodies) ---
#
# The wiki page-tree half of the old `lint_wiki` (roadmap #8c) is retired along with
# `wiki_dir` — `orphan` (backlink graph), `stale` (single-page mtime), `oversized`
# (single-page byte cap) described a page-tree shape that no longer exists: a post
# supersede chain has no backlink graph, and posts don't grow in place. `open_item`
# survives because it was never wiki-specific in premise — it is "the resurfacing
# channel for actions the notes promised" (docs/design/2026-08-14-resurfacing-detector
# -measurement.md), and a post body can make the same promise a wiki note could. It
# now scans `posts_dir(root)` recursively (posts nest one level under a post-directory,
# e.g. `posts/finding/001-x.md`) instead of `wiki_dir(root)`'s flat `*.md`.

def test_post_open_item_flags_unchecked_boxes_only(tmp_path):
    """열린 체크박스만 open_item. 닫힌 것·산문은 안 걸린다."""
    posts = tmp_path / ".hq" / "community" / "posts" / "finding"
    posts.mkdir(parents=True)
    (posts / "001-plan.md").write_text(
        "# plan\n\n"
        "- [ ] krit Kanban 결합 해제\n"
        "* [ ] workspace 이주 2차\n"
        "+ [ ]   앞뒤 공백 있는 항목\n"
        "- [x] 이미 끝난 것\n"
        "- [X] 대문자로 닫은 것\n"
        "- 그냥 항목\n"
    )
    finds = scan_open_items(tmp_path)
    assert len(finds) == 1, finds
    assert finds[0]["detail"].startswith("3 unchecked: ")
    assert "이미 끝난 것" not in finds[0]["detail"]


def test_post_open_item_does_not_fire_on_prose_markers(tmp_path):
    """오탐 회귀 — 산문 스캔을 기각한 이유가 여기 박혀 있다.

    실측(2026-08-14, 한 vault): 산문 마커(미결/TODO/보류) 매칭은 7건 중 3건이 오탐이었다.
    해소를 *선언하는* 제목이 걸리고, 파일명 `RL-ALBC - TODO.md` 가 걸린다. 아래 본문은
    그 세 부류를 그대로 담았으며 open_item 은 0건이어야 한다.
    """
    posts = tmp_path / ".hq" / "community" / "posts" / "finding"
    posts.mkdir(parents=True)
    (posts / "002-history.md").write_text(
        "### 미결 (omp-organize 별도 세션 대상)\n"
        "init 범위 밖이라 미실행. 이동 대상 후보:\n\n"
        "## 2026-08-14 — 이주 2차 실행, 1차 미결 전부 해소\n"
        "- dead link: `RL-ALBC - TODO.md:242` 가 이주된 reviews 를 가리킴\n"
        "- **보류: krit/Kanban.md** — 병렬 세션이 재편 중\n"
        "TODO 라는 단어가 산문에 있어도 항목이 아니다.\n"
    )
    assert not scan_open_items(tmp_path)


def test_post_open_item_is_per_file_not_per_note_body_leak(tmp_path):
    """포스트마다 자기 본문을 읽는가 (누적 루프에서 이전 파일 text 가 새면 안 된다)."""
    posts = tmp_path / ".hq" / "community" / "posts" / "finding"
    posts.mkdir(parents=True)
    (posts / "001-a-has-items.md").write_text("see subject b-clean\n- [ ] 유일한 열린 항목\n")
    (posts / "002-b-clean.md").write_text("see subject a-has-items\n본문에 체크박스 없음\n")
    finds = scan_open_items(tmp_path)
    assert [Path(f["path"]).name for f in finds] == ["001-a-has-items.md"]


def test_post_open_item_empty_when_no_store(tmp_path):
    """posts_dir 가 아예 없는 프로젝트는 결함이 아니라 N/A — 조용히 빈 리스트."""
    assert scan_open_items(tmp_path) == []


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


# ---------------------------------------------------------------------------
# scan_layers -- the `.hq/` store-layer axis (store-spec sections 3 and 5).
# ---------------------------------------------------------------------------

LAYERS = {"layers": {"root": ".hq", "tracked": ["community", "config"],
                     "ignored": ["work", "runtime"]}}


def _repo(tmp_path, gitignore):
    """A git repo carrying one four-layer .hq anchor and the given .gitignore."""
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / ".gitignore").write_text(gitignore)
    hq = tmp_path / ".hq"
    (hq).mkdir()
    (hq / ".anchor").write_text("id: fixture\n")
    for layer in ("community", "config", "work", "runtime"):
        (hq / layer).mkdir()
        (hq / layer / "keep.md").write_text("x\n")
    return tmp_path


GOOD_IGNORE = "**/.hq/work/\n**/.hq/runtime/\n"


def test_layers_axis_is_inert_without_the_rule(tmp_path):
    """A project that never adopted the unified store is not in violation of it."""
    _repo(tmp_path, GOOD_IGNORE)
    assert scan_layers(tmp_path, {}) == []


def test_layers_clean_repo_has_no_findings(tmp_path):
    assert scan_layers(_repo(tmp_path, GOOD_IGNORE), LAYERS) == []


def test_layers_flags_a_tracked_layer_that_git_ignores(tmp_path):
    """The silent one: an over-broad rule ignores community/ and the record dies."""
    root = _repo(tmp_path, "**/.hq/\n")
    kinds = {f["kind"] for f in scan_layers(root, LAYERS)}
    assert "layer_tracked" in kinds


def test_layers_flags_an_ignored_layer_that_git_tracks(tmp_path):
    """runtime/ holds locks and session state; committing it dirties every sync."""
    root = _repo(tmp_path, "**/.hq/work/\n")
    finds = scan_layers(root, LAYERS)
    assert [f["path"] for f in finds if f["kind"] == "layer_ignored"] == [".hq/runtime"]


def test_layers_flags_an_undeclared_fifth_layer(tmp_path):
    root = _repo(tmp_path, GOOD_IGNORE)
    (root / ".hq" / "scratch").mkdir()
    finds = [f for f in scan_layers(root, LAYERS) if f["kind"] == "layer_unknown"]
    assert len(finds) == 1 and finds[0]["path"].endswith(".hq/scratch")


def test_layers_flags_an_unparseable_anchor(tmp_path):
    root = _repo(tmp_path, GOOD_IGNORE)
    (root / ".hq" / ".anchor").write_text("id: fixture\nmigrated: 2026-08-28\n")
    assert [f["kind"] for f in scan_layers(root, LAYERS)] == ["anchor_parse"]


def test_layers_reaches_a_nested_anchor(tmp_path):
    """Anchors nest -- workspace runs a three-deep chain, so root-only is wrong."""
    root = _repo(tmp_path, GOOD_IGNORE)
    inner = root / "sub" / "project" / ".hq"
    inner.mkdir(parents=True)
    (inner / ".anchor").write_text("id: inner\n")
    (inner / "scratch").mkdir()
    finds = [f for f in scan_layers(root, LAYERS) if f["kind"] == "layer_unknown"]
    assert len(finds) == 1 and "sub/project" in finds[0]["path"]
