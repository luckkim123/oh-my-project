#!/usr/bin/env python3
"""Documentation that no longer matches the tree — a periodic sweep, report only.

    python3 hooks/omp_doc_garden.py --root <project>
    python3 hooks/omp_doc_garden.py --root <project> --json
    python3 hooks/omp_doc_garden.py --root <project> --doc-glob 'notes/**/*.md'

MANUAL — not wired to any hook event, same as `omp_content_audit.py`. The
`omp-garden` skill invokes it; a human decides when to run it, and `/loop` or
`/schedule` is what makes it periodic. omp does not ship a scheduler.

**Why this exists next to `scan_structure_drift`, not inside it.** That function
(omp_content_audit.py:103) already flags declared paths that vanished, but only
from `rules.json structure.directories[]` and `.omp/STRUCTURE.md` /
`.omp/DATASETS.md`. Every path this project has actually lost track of was
somewhere else — a README, a handoff note, a sibling harness's wiki page. Those
files are this module's target, and the two `.omp/` documents the audit stage
already owns are deliberately excluded so one drift is never reported twice.

**It carries state, which is the other half of the job.** A stateless sweep
reports the same finding on every run, so the third report reads exactly like the
first and nothing distinguishes "new rot" from "we looked at this and did not
act". `.omp/garden-state.json` counts how many sweeps each finding survived and
escalates at three. That count is the numeric cap the loop contract asks for; the
sweep's stop condition is "no new findings".

Report only. It never edits a document and never deletes anything — closing a
finding is a human's call (D9), the same rule the rest of omp follows.

Suppression is a `GARDEN_OK` marker on the offending line, mirroring the vault's
`CITE_OK` convention. A historical path in a post-mortem is a legitimate mention,
and without an escape hatch the sweep would train its reader to ignore it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from omp_atomic import atomic_write_json  # noqa: E402
from omp_content_audit import _BACKTICK_PATH, _PLACEHOLDER_PATH  # noqa: E402
from omp_paths import DEFAULT_DOC_GLOBS, OWNED_BY_AUDIT_RELS, garden_state_json  # noqa: E402
from omp_paths import garden_state_json_write  # noqa: E402

STATE_VERSION = 1

# Root-level and top-of-docs/ markdown. Not a rules.json field on purpose: omp's
# 0.9.0 release already rejected a new schema key for costing four surfaces to
# keep in step (schema + codify + learn + audit). A default list plus
# `--doc-glob` buys the same reach for none of that.
#
# `docs/*.md`, NOT `docs/**/*.md`. Measured on claudebase 2026-08-16: recursing
# pulled in `docs/reference/omc-deep-analysis-v4.15.2/**`, a vendored analysis of
# a DIFFERENT repository, and 99 of the 110 findings were that document
# faithfully citing omc's paths. A subtree that documents someone else's tree is
# not this project's documentation; widen with --doc-glob when it is.
# (value itself lives in omp_paths.DEFAULT_DOC_GLOBS, imported above)

# `omp-audit`'s scan_structure_drift owns these two. Scanning them here would
# report one drift under two stages, and the duplicate outlives whichever copy
# gets fixed.
OWNED_BY_AUDIT = OWNED_BY_AUDIT_RELS

SUPPRESS_MARKER = "GARDEN_OK"
ESCALATE_AFTER = 3       # sweeps a finding may survive before it needs a decision
SWEEP_HISTORY = 20       # sweeps kept in state; older ones are dropped

_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv"}


def _iso(now: datetime) -> str:
    return now.replace(microsecond=0).isoformat()


def doc_files(root, globs=None) -> list:
    """Markdown the sweep reads, audit-owned files removed, sorted and unique."""
    root = Path(root)
    out: list = []
    for pattern in (globs or DEFAULT_DOC_GLOBS):
        for path in sorted(root.glob(pattern)):
            if not path.is_file():
                continue
            rel = path.relative_to(root).as_posix()
            if rel in OWNED_BY_AUDIT:
                continue
            if any(part in _SKIP_DIRS for part in path.parts):
                continue
            if path not in out:
                out.append(path)
    return out


def _is_symbol_ref(target: str) -> bool:
    """`hooks/omp_content_audit.check_content_rule` is a symbol, not a file.

    Real extensions in this stack are short and have no underscore (md, py,
    json, jsonl, sh, mjs, yaml, toml, cpp). A dotted tail that breaks either rule
    is a qualified name someone wrote with a slash in front of it."""
    tail = target.rsplit("/", 1)[-1]
    if "." not in tail:
        return False
    ext = tail.rsplit(".", 1)[-1]
    return len(ext) > 5 or "_" in ext


def _is_in_scope(root: Path, target: str) -> bool:
    """Does this repo plausibly ever have held that path? Parent must exist.

    Without this the sweep drowns: measured on claudebase 2026-08-16, the bare
    "backtick with a slash" rule produced **755 findings**, essentially all of
    them things that were never paths here — `origin/main` (a git ref),
    `remotion-dev/claude-code-plugin` (a repo slug), `a/b` (an example in
    prose), and `claude/settings.json` (the tail of `~/.claude/settings.json`,
    with the leading `~/.` outside the pattern).

    Requiring the PARENT directory to exist is what separates "this used to be
    here and moved" from "this was never about this tree". A drift that also
    deleted the parent directory is missed by design — the alternative is a
    report nobody reads, which is the failure mode this whole stage exists to
    prevent."""
    parent = target.rstrip("/").rsplit("/", 1)[0]
    return (root / parent).is_dir()


def sweep(root, globs=None) -> list:
    """[{kind, file, line, path, quote}] — backticked paths that do not exist.

    Four filters, each of which was worth its line on a real corpus: GARDEN_OK
    on the line, placeholder shapes (`YYYY`, `NNNN`, `...` — the same rule the
    audit stage uses), qualified symbol names, and paths whose parent directory
    is not in this tree at all."""
    root = Path(root)
    finds = []
    for doc in doc_files(root, globs):
        try:
            lines = doc.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        rel = doc.relative_to(root).as_posix()
        for n, line in enumerate(lines, 1):
            if SUPPRESS_MARKER in line:
                continue
            for m in _BACKTICK_PATH.finditer(line):
                target = m.group(1)
                if _PLACEHOLDER_PATH.search(target):
                    continue
                if _is_symbol_ref(target):
                    continue
                if not _is_in_scope(root, target):
                    continue
                if (root / target.rstrip("/")).exists():
                    continue
                finds.append({"kind": "doc_drift", "file": rel, "line": n,
                              "path": target.rstrip("/"),
                              "quote": " ".join(line.split())[:100]})
    return finds


def fingerprint(finding: dict) -> str:
    """Stable id for a finding across sweeps — file and cited path, NOT the line.

    Line numbers move whenever the document is edited above the citation, and a
    fingerprint that moves with them resets the survival count to 1 on every
    unrelated edit. The recurrence signal would then never reach three."""
    key = f"{finding['file']}|{finding['path']}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


def load_state(root) -> dict:
    path = garden_state_json(root)
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": STATE_VERSION, "sweeps": [], "findings": {}}
    state.setdefault("version", STATE_VERSION)
    state.setdefault("sweeps", [])
    state.setdefault("findings", {})
    return state


def merge(state: dict, findings: list, now: datetime) -> tuple:
    """(new state, annotated findings, resolved) — pure, so recurrence is testable.

    Annotated findings carry `count` (sweeps survived), `first_seen`, and
    `escalate`. Resolved entries are the fingerprints state knew about that this
    sweep no longer sees; they are returned so the caller can say what got fixed,
    then dropped from state."""
    stamp = _iso(now)
    known = dict(state.get("findings") or {})
    seen, annotated = set(), []

    for finding in findings:
        fp = fingerprint(finding)
        seen.add(fp)
        prior = known.get(fp)
        count = (prior.get("count", 0) if prior else 0) + 1
        first_seen = prior.get("first_seen", stamp) if prior else stamp
        known[fp] = {"file": finding["file"], "line": finding["line"],
                     "path": finding["path"], "first_seen": first_seen,
                     "last_seen": stamp, "count": count}
        annotated.append(dict(finding, fingerprint=fp, count=count,
                              first_seen=first_seen,
                              escalate=count >= ESCALATE_AFTER))

    resolved = [dict(v, fingerprint=fp) for fp, v in known.items() if fp not in seen]
    for entry in resolved:
        known.pop(entry["fingerprint"], None)

    fresh = sum(1 for a in annotated if a["count"] == 1)
    sweeps = list(state.get("sweeps") or [])
    sweeps.append({"at": stamp, "found": len(annotated), "new": fresh,
                   "resolved": len(resolved)})
    new_state = {"version": STATE_VERSION, "sweeps": sweeps[-SWEEP_HISTORY:],
                 "findings": known}
    return new_state, annotated, resolved


def record(root, state: dict) -> None:
    atomic_write_json(garden_state_json_write(root), state)


def format_report(annotated: list, resolved: list, doc_count: int) -> str:
    L = [f"omp-garden — {doc_count} document(s) swept",
         f"  findings {len(annotated)}   "
         f"new {sum(1 for a in annotated if a['count'] == 1)}   "
         f"resolved since last sweep {len(resolved)}"]
    if not annotated:
        L.append("  no drift — every cited path resolves")
    for a in sorted(annotated, key=lambda a: (-a["count"], a["file"], a["line"])):
        flag = "  ESCALATE" if a["escalate"] else ""
        L.append(f"  {a['file']}:{a['line']}  ->  {a['path']}   "
                 f"(sweep {a['count']}){flag}")
        L.append(f"      {a['quote']}")
    for r in resolved:
        L.append(f"  resolved  {r['file']}  ->  {r['path']}")
    if any(a["escalate"] for a in annotated):
        L.append(f"  ESCALATE = seen in {ESCALATE_AFTER}+ sweeps and still open. "
                 f"Fix the document, or mark the line {SUPPRESS_MARKER}: <reason>.")
    return "\n".join(L)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--root", default=".", help="project root (default: cwd)")
    parser.add_argument("--doc-glob", action="append", default=None,
                        help="glob to sweep, relative to root (repeatable; "
                             f"default: {' '.join(DEFAULT_DOC_GLOBS)})")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--no-state", action="store_true",
                        help="do not read or write .omp/garden-state.json")
    args = parser.parse_args(argv)

    root = Path(args.root).expanduser()
    globs = tuple(args.doc_glob) if args.doc_glob else None
    findings = sweep(root, globs)
    docs = len(doc_files(root, globs))

    if args.no_state:
        annotated = [dict(f, fingerprint=fingerprint(f), count=1,
                          first_seen=None, escalate=False) for f in findings]
        resolved = []
    else:
        state, annotated, resolved = merge(load_state(root), findings, datetime.now())
        record(root, state)

    if args.json:
        print(json.dumps({"findings": annotated, "resolved": resolved,
                          "documents": docs}, ensure_ascii=False, indent=1))
    else:
        print(format_report(annotated, resolved, docs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
