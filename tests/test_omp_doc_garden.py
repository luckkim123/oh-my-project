"""Tests for the omp-garden doc-drift sweep.

Two properties carry the stage and both are easy to get silently wrong:

  1. The sweep must stay quiet on a healthy tree. A path checker that flags
     everything is worse than none — its reader stops looking, which is the
     failure `citation-check.py` in the vault was rebuilt to avoid.
  2. The survival count must be stable across unrelated edits. Fingerprinting a
     finding by line number resets it to 1 whenever anything above it is edited,
     so the escalation at three sweeps would never fire and the state file would
     look healthy while doing nothing.
"""
from datetime import datetime, timedelta
from pathlib import Path

from hooks.omp_doc_garden import (
    ESCALATE_AFTER,
    OWNED_BY_AUDIT,
    doc_files,
    fingerprint,
    format_report,
    load_state,
    merge,
    record,
    sweep,
)

T0 = datetime(2026, 8, 16, 0, 0, 0)


def _project(tmp_path: Path, readme: str) -> Path:
    (tmp_path / ".omp").mkdir()
    (tmp_path / "README.md").write_text(readme, encoding="utf-8")
    return tmp_path


# ─── the sweep ──────────────────────────────────────────────────────────────

def test_existing_path_is_not_a_finding(tmp_path):
    root = _project(tmp_path, "See `src/main.py` for the entry point.\n")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("x = 1\n")
    assert sweep(root) == []


def test_missing_path_is_a_finding_with_its_line_and_quote(tmp_path):
    root = _project(tmp_path, "intro\n\nMoved to `old/place/notes.md` last year.\n")
    (tmp_path / "old" / "place").mkdir(parents=True)   # the leaf moved, not the tree
    found = sweep(root)
    assert len(found) == 1
    assert found[0]["file"] == "README.md"
    assert found[0]["line"] == 3
    assert found[0]["path"] == "old/place/notes.md"
    assert "Moved to" in found[0]["quote"]


def test_placeholder_paths_are_skipped(tmp_path):
    root = _project(tmp_path, "Runs land in `runs/YYYY-MM-DD/log.txt`.\n")
    assert sweep(root) == []


def test_suppression_marker_silences_the_line(tmp_path):
    root = _project(
        tmp_path,
        "The bug was in `old/pid.cpp` at the time.  GARDEN_OK: post-mortem\n")
    assert sweep(root) == []


def test_audit_owned_documents_are_not_swept(tmp_path):
    """scan_structure_drift already reports these two; a second report under a
    different stage outlives whichever copy someone fixes."""
    root = _project(tmp_path, "clean\n")
    for rel in OWNED_BY_AUDIT:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("Gone: `vanished/dir`\n", encoding="utf-8")
    assert [p.name for p in doc_files(root)] == ["README.md"]
    assert sweep(root) == []


def test_a_path_whose_parent_is_not_here_is_not_this_tree_s_problem(tmp_path):
    """The single filter that made the sweep readable. Measured on claudebase
    2026-08-16: without it, 755 findings, almost all of them strings that were
    never paths in this repo."""
    root = _project(tmp_path, "\n".join([
        "Push to `origin/main` only.",                       # a git ref
        "Vendored from `remotion-dev/claude-code-plugin`.",  # a repo slug
        "Any backticked `a/b` string.",                      # prose example
        "Tail of ~/.claude: `claude/settings.json`.",        # someone else's tree
    ]) + "\n")
    assert sweep(root) == []


def test_a_moved_file_under_a_surviving_directory_is_still_caught(tmp_path):
    """The other side of the same filter — the drift it must not swallow."""
    root = _project(tmp_path, "The installer is `installer/setup.sh`.\n")
    (tmp_path / "installer").mkdir()
    (tmp_path / "installer" / "install.sh").write_text("#!/bin/sh\n")
    assert [f["path"] for f in sweep(root)] == ["installer/setup.sh"]


def test_qualified_symbol_names_are_not_paths(tmp_path):
    root = _project(tmp_path, "See `hooks/omp_content_audit.check_content_rule` for the rule.\n")
    (tmp_path / "hooks").mkdir()
    assert sweep(root) == []


def test_docs_subtree_is_not_recursed_by_default(tmp_path):
    """A docs/ subtree is often a vendored analysis of ANOTHER repository, whose
    every cited path is correctly absent here — 99 of claudebase's 110 findings
    came from exactly one such directory."""
    root = _project(tmp_path, "clean\n")
    (tmp_path / "docs" / "reference").mkdir(parents=True)
    (tmp_path / "docs" / "top.md").write_text("Ours: `docs/gone.md`\n", encoding="utf-8")
    (tmp_path / "docs" / "reference" / "other-repo.md").write_text(
        "Theirs: `docs/their-thing.md`\n", encoding="utf-8")
    assert [f["path"] for f in sweep(root)] == ["docs/gone.md"]
    widened = sweep(root, ("docs/**/*.md",))
    assert len(widened) == 2


def test_custom_globs_reach_beyond_the_default(tmp_path):
    root = _project(tmp_path, "clean\n")
    notes = tmp_path / "notes"
    notes.mkdir()
    (notes / "handoff.md").write_text("Tree lives at `gone/tree`\n", encoding="utf-8")
    (tmp_path / "gone").mkdir()
    assert sweep(root) == []
    found = sweep(root, ("notes/**/*.md",))
    assert [f["path"] for f in found] == ["gone/tree"]


# ─── recurrence and state ───────────────────────────────────────────────────

def test_fingerprint_survives_a_line_move():
    a = {"file": "README.md", "line": 3, "path": "old/dir"}
    b = {"file": "README.md", "line": 41, "path": "old/dir"}
    assert fingerprint(a) == fingerprint(b)


def test_count_rises_per_sweep_and_escalates_at_the_cap():
    finding = {"kind": "doc_drift", "file": "README.md", "line": 3,
               "path": "old/dir", "quote": "..."}
    state = {"version": 1, "sweeps": [], "findings": {}}
    for i in range(1, ESCALATE_AFTER + 1):
        state, annotated, resolved = merge(state, [finding], T0 + timedelta(days=i))
        assert annotated[0]["count"] == i
        assert annotated[0]["escalate"] is (i >= ESCALATE_AFTER)
        assert resolved == []
    assert annotated[0]["first_seen"] == "2026-08-17T00:00:00"


def test_a_fixed_finding_is_reported_resolved_then_forgotten():
    finding = {"kind": "doc_drift", "file": "README.md", "line": 3,
               "path": "old/dir", "quote": "..."}
    state, _, _ = merge({"version": 1, "sweeps": [], "findings": {}}, [finding], T0)
    state, annotated, resolved = merge(state, [], T0 + timedelta(days=1))
    assert annotated == []
    assert [r["path"] for r in resolved] == ["old/dir"]
    assert state["findings"] == {}


def test_sweep_history_is_capped():
    state = {"version": 1, "sweeps": [], "findings": {}}
    for i in range(25):
        state, _, _ = merge(state, [], T0 + timedelta(days=i))
    assert len(state["sweeps"]) == 20


def test_state_round_trips_through_disk(tmp_path):
    root = _project(tmp_path, "Gone: `old/dir`\n")
    (tmp_path / "old").mkdir()
    state, _, _ = merge(load_state(root), sweep(root), T0)
    record(root, state)
    reloaded = load_state(root)
    assert reloaded["version"] == 1
    assert len(reloaded["findings"]) == 1
    entry = next(iter(reloaded["findings"].values()))
    assert entry["path"] == "old/dir" and entry["count"] == 1


def test_missing_state_file_is_an_empty_state(tmp_path):
    assert load_state(tmp_path) == {"version": 1, "sweeps": [], "findings": {}}


def test_corrupt_state_file_does_not_crash_the_sweep(tmp_path):
    (tmp_path / ".omp").mkdir()
    (tmp_path / ".omp" / "garden-state.json").write_text("{ not json", encoding="utf-8")
    assert load_state(tmp_path)["findings"] == {}


# ─── report ─────────────────────────────────────────────────────────────────

def test_report_names_the_escape_hatch_only_when_something_escalated():
    quiet = format_report([], [], 3)
    assert "no drift" in quiet and "GARDEN_OK" not in quiet
    hot = format_report([{"file": "README.md", "line": 3, "path": "old/dir",
                          "quote": "q", "count": ESCALATE_AFTER, "escalate": True}], [], 3)
    assert "ESCALATE" in hot and "GARDEN_OK" in hot
