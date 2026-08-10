"""Graph-axis checks (v0.8.0).

The status fixture is the real output measured on one Obsidian vault, the case
that motivated the axis: 21,865 nodes from 101 files of vendored plugin JS, no
markdown, and a build 12 days behind HEAD.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))
import omp_graph_audit as ga  # noqa: E402

VAULT_STATUS = """Nodes: 21865
Edges: 142416
Files: 101
Languages: bash, python, javascript, cpp, objc
Last updated: 2026-07-29T16:17:12
Built on branch: main
Built at commit: 6cb80302ff8a
"""

CRG = {"tool": "code-review-graph", "path": ".crg/", "refresh": "code-review-graph update"}


@pytest.fixture
def graph_dir(tmp_path):
    (tmp_path / ".crg").mkdir()
    return tmp_path


def stub(monkeypatch, mapping):
    """Replace _run with a lookup on the first argument (the binary name)."""
    monkeypatch.setattr(ga, "_run", lambda args, cwd: mapping.get(args[0]))


def test_tool_enum_is_the_single_source():
    assert ga.GRAPH_TOOLS == ("code-review-graph", "graphify", "tokensave")
    assert "tokensave" in ga.NO_EXEC_TOOLS


def test_parse_crg_status():
    st = ga.parse_crg_status(VAULT_STATUS)
    assert st["nodes"] == 21865 and st["files"] == 101
    assert st["languages"] == ["bash", "python", "javascript", "cpp", "objc"]
    assert st["commit"] == "6cb80302ff8a"
    assert st["updated"] == "2026-07-29T16:17:12"


def test_parse_crg_status_ignores_unknown_lines():
    st = ga.parse_crg_status("Nodes: 5\nSomething New: x\nno colon here\n")
    assert st == {"nodes": 5}


def test_missing_artifact_is_a_finding(tmp_path):
    f = ga.check_graph_present(tmp_path, CRG)
    assert len(f) == 1 and f[0]["kind"] == "graph_missing"
    assert f[0]["refresh"] == "code-review-graph update"


def test_present_artifact_is_silent(graph_dir):
    assert ga.check_graph_present(graph_dir, CRG) == []


def test_stale_when_built_commit_differs(monkeypatch, graph_dir):
    stub(monkeypatch, {"code-review-graph": VAULT_STATUS,
                       "git": "45fa74e5300aaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n"})
    f = ga.check_graph_stale(graph_dir, CRG)
    assert len(f) == 1 and f[0]["kind"] == "graph_stale"
    assert "6cb80302ff8a" in f[0]["detail"] and "45fa74e5300a" in f[0]["detail"]


def test_not_stale_when_commit_matches_on_the_abbreviated_prefix(monkeypatch, graph_dir):
    stub(monkeypatch, {"code-review-graph": VAULT_STATUS,
                       "git": "6cb80302ff8affffffffffffffffffffffffffff\n"})
    assert ga.check_graph_stale(graph_dir, CRG) == []


def test_coverage_mismatch_names_the_missing_language(monkeypatch, graph_dir):
    stub(monkeypatch, {"code-review-graph": VAULT_STATUS, "git": "a\nb\nc\n"})
    entry = dict(CRG, covers=["python", ".md"])
    f = ga.check_graph_coverage(graph_dir, entry)
    assert len(f) == 1 and f[0]["kind"] == "graph_coverage_mismatch"
    assert f[0]["missing"] == ["md"]          # python is present, markdown is not
    assert "101 of 3 tracked files" in f[0]["detail"]


def test_coverage_silent_when_everything_declared_is_present(monkeypatch, graph_dir):
    stub(monkeypatch, {"code-review-graph": VAULT_STATUS, "git": "a\n"})
    assert ga.check_graph_coverage(graph_dir, dict(CRG, covers=["python", "cpp"])) == []


def test_graphify_stale_uses_the_needs_update_marker(tmp_path):
    e = {"tool": "graphify", "path": "graphify-out"}
    (tmp_path / "graphify-out").mkdir()
    assert ga.check_graph_stale(tmp_path, e) == []
    (tmp_path / "graphify-out" / "needs_update").write_text("")
    f = ga.check_graph_stale(tmp_path, e)
    assert len(f) == 1 and f[0]["kind"] == "graph_stale"


def test_tokensave_is_never_executed(monkeypatch, tmp_path):
    """D3: running its CLI rewrites the user's settings, so the axis must not call it."""
    called = []
    monkeypatch.setattr(ga, "_run", lambda args, cwd: called.append(args) or "")
    (tmp_path / ".tokensave").mkdir()
    e = {"tool": "tokensave", "path": ".tokensave", "covers": [".md"]}
    assert ga.check_graph_stale(tmp_path, e) == []
    assert ga.check_graph_coverage(tmp_path, e) == []
    assert called == []


def test_fail_open_when_binary_is_absent(monkeypatch, graph_dir):
    monkeypatch.setattr(ga, "_run", lambda args, cwd: None)
    assert ga.check_graph_stale(graph_dir, CRG) == []
    assert ga.check_graph_coverage(graph_dir, dict(CRG, covers=["python"])) == []


def test_scan_is_silent_without_the_section(tmp_path):
    assert ga.scan_graphs(tmp_path, {}) == []
    assert ga.scan_graphs(tmp_path, {"code_graphs": {}}) == []
    assert ga.scan_graphs(tmp_path, {"code_graphs": {"indexes": []}}) == []


def test_scan_skips_interrogation_when_artifact_is_missing(monkeypatch, tmp_path):
    """A registry pointing at nothing yields one finding, not three."""
    monkeypatch.setattr(ga, "_run", lambda args, cwd: pytest.fail("must not run"))
    f = ga.scan_graphs(tmp_path, {"code_graphs": {"indexes": [dict(CRG, covers=["python"])]}})
    assert [x["kind"] for x in f] == ["graph_missing"]


def test_scan_collects_stale_and_coverage_together(monkeypatch, graph_dir):
    stub(monkeypatch, {"code-review-graph": VAULT_STATUS, "git": "45fa74e5300a\n"})
    rules = {"code_graphs": {"indexes": [dict(CRG, covers=[".md"])]}}
    kinds = sorted(x["kind"] for x in ga.scan_graphs(graph_dir, rules))
    assert kinds == ["graph_coverage_mismatch", "graph_stale"]
