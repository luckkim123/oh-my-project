"""Deterministic code-graph registry checks for omp-audit (the graph axis).

Pure stdlib (subprocess, pathlib). No file mutation, and it never builds or
refreshes an index — omp registers a graph, a human refreshes it (the same
not-a-build-runner boundary omp-env holds). Returns finding dicts; the `auditor`
agent invokes these as the canonical check algorithm.

Warn-default, like the docker and secretary axes: a graph finding never blocks an
overall PASS. A stale or mis-declared index is a hygiene signal for omp-codify,
not a rule violation.

Why the axis exists. A graph tool answers "is there a graph?" but not "does that
graph cover what you are about to ask it". Measured on one Obsidian vault: the
CRG index held 21,865 nodes from 101 files, while the repo tracked 2,277 files of
which 828 were notes — the graph was entirely vendored plugin JS, the notes were
absent, and nothing reported that. A search-guard hook then told every session to
consult that graph before grepping. Registering the real coverage and checking it
against the tool's own status output is what closes that gap.

Fail-open everywhere: a missing binary, a non-zero exit, or a timeout yields no
findings rather than a false alarm, so a machine without the tools installed sees
a quiet axis instead of a wall of warnings.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional

# Must stay identical to rules.schema.json code_graphs.indexes[].tool enum
# (asserted by tests/test_schemas.py::test_rules_schema_has_code_graphs).
GRAPH_TOOLS = ("code-review-graph", "graphify", "tokensave")

# `tokensave` re-installs its agent integration as a side effect of commands that
# look read-only — a measured `tokensave status` rewrote ~/.claude/settings.json
# and re-injected its own hooks, which then ran twice per prompt alongside the
# wrapper already wired there. So the audit NEVER executes it: a tokensave entry
# is registration-only, and its coverage is reported as undeclarable rather than
# verified. Registration still earns its keep — it is what tells a sibling lane
# "prose lives in tokensave, not in the code graph".
NO_EXEC_TOOLS = ("tokensave",)

_TIMEOUT = 20


def _run(args: list[str], cwd: Path) -> Optional[str]:
    """Run a read-only command, returning stdout or None on any failure."""
    try:
        p = subprocess.run(args, cwd=str(cwd), capture_output=True,
                           text=True, timeout=_TIMEOUT)
    except (OSError, subprocess.SubprocessError):
        return None
    if p.returncode != 0:
        return None
    return p.stdout


def parse_crg_status(text: str) -> dict:
    """Parse `code-review-graph status` key/value output into a dict.

    Recognised keys become nodes/edges/files (int), languages (list), commit, updated.
    Unknown lines are ignored, so a future field does not break the parse.
    """
    out: dict = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        k, v = k.strip().lower(), v.strip()
        if k in ("nodes", "edges", "files"):
            try:
                out[k] = int(v)
            except ValueError:
                pass
        elif k == "languages":
            out["languages"] = [x.strip() for x in v.split(",") if x.strip()]
        elif k == "built at commit":
            out["commit"] = v
        elif k == "last updated":
            out["updated"] = v
    return out


def _head_commit(root: Path) -> Optional[str]:
    out = _run(["git", "rev-parse", "HEAD"], root)
    return out.strip() if out else None


def _tracked_count(root: Path) -> Optional[int]:
    out = _run(["git", "ls-files"], root)
    return len(out.splitlines()) if out is not None else None


def check_graph_present(root: Path, entry: dict) -> list[dict]:
    """Registered but absent on disk -> the registry points at nothing."""
    p = entry.get("path")
    if not p:
        return []
    if (Path(root) / p).exists():
        return []
    return [{"kind": "graph_missing", "tool": entry.get("tool"), "path": p,
             "detail": "registered in rules.json but not present on disk",
             "refresh": entry.get("refresh")}]


def check_graph_stale(root: Path, entry: dict) -> list[dict]:
    """The index no longer matches the working tree.

    code-review-graph: its status reports the commit it was built at; compare to HEAD.
    graphify: it drops a `needs_update` marker beside the graph when the tree moved.
    tokensave: never executed (see NO_EXEC_TOOLS) -> no staleness verdict.
    """
    root = Path(root)
    tool = entry.get("tool")
    if tool in NO_EXEC_TOOLS:
        return []
    if tool == "code-review-graph":
        out = _run(["code-review-graph", "status"], root)
        if not out:
            return []
        st = parse_crg_status(out)
        built, head = st.get("commit"), _head_commit(root)
        if not built or not head:
            return []
        # status abbreviates the sha, so compare on the shorter of the two.
        n = min(len(built), len(head))
        if built[:n] != head[:n]:
            return [{"kind": "graph_stale", "tool": tool,
                     "detail": f"built at {built}, HEAD is {head[:len(built)]}",
                     "updated": st.get("updated"), "refresh": entry.get("refresh")}]
        return []
    if tool == "graphify":
        p = entry.get("path") or "graphify-out"
        if (root / p / "needs_update").exists():
            return [{"kind": "graph_stale", "tool": tool,
                     "detail": "graphify left a needs_update marker",
                     "refresh": entry.get("refresh")}]
    return []


def check_graph_coverage(root: Path, entry: dict) -> list[dict]:
    """The declared `covers` does not match what the index actually holds.

    Only code-review-graph reports its languages, so only it is verifiable today.
    A declared language the graph does not contain is the finding that would have
    caught the vault case in this module's docstring.
    """
    root = Path(root)
    tool = entry.get("tool")
    declared = [c.lower().lstrip(".") for c in entry.get("covers", []) if c]
    if tool != "code-review-graph" or not declared:
        return []
    out = _run(["code-review-graph", "status"], root)
    if not out:
        return []
    st = parse_crg_status(out)
    actual = [x.lower() for x in st.get("languages", [])]
    if not actual:
        return []
    missing = [d for d in declared if d not in actual]
    if not missing:
        return []
    tracked, files = _tracked_count(root), st.get("files")
    scale = (f"; index holds {files} of {tracked} tracked files"
             if files is not None and tracked else "")
    return [{"kind": "graph_coverage_mismatch", "tool": tool,
             "declared": declared, "actual": actual, "missing": missing,
             "detail": f"declared {missing} absent from the index{scale}",
             "refresh": entry.get("refresh")}]


def scan_graphs(root: Path, rules: dict) -> list[dict]:
    """Run every graph-axis check over rules.json code_graphs.indexes[].

    Returns [] when the section is absent, which is the common case — the axis is
    opt-in and silent until a project registers an index through omp-codify.
    """
    root = Path(root)
    finds: list[dict] = []
    for entry in (rules.get("code_graphs") or {}).get("indexes", []) or []:
        present = check_graph_present(root, entry)
        finds.extend(present)
        if present:
            continue  # nothing on disk to interrogate
        finds.extend(check_graph_stale(root, entry))
        finds.extend(check_graph_coverage(root, entry))
    return finds
