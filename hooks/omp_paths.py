"""Single declaration point for this repo's on-disk root literal, `.omp`.

Every derived path hooks/*.py computes today (rules.json, secretary/, wiki/,
garden-state.json, verify-throttle.json, ...) is named here once. Callers
delete their inline `root / ".omp" / "..."` computation and call the matching
helper instead, importing it the same way the hooks already import each
other (`sys.path.insert(0, str(Path(__file__).parent))` then a flat import —
no new import mechanism).

P2 promise: **behavior-unchanged only.** `LEGACY_ROOT` is still `.omp` — this
repo's current legacy root, not the future unified `.hq/` store. Every helper
below returns exactly the path today's inline code already computed; a helper
that returns a different path is a bug, not an improvement. The `.hq/` rename
and its read-fallback are P3+ work and do not belong in this module yet.

A re-entry lint (tests/test_omp_paths_lint.py) fails the build if a new
`.omp` literal is added anywhere outside this file.

Reference: ~/oh-my-orchestrator/skills/harness/references/store-spec.md §9.5.
"""
from __future__ import annotations

from pathlib import Path

LEGACY_ROOT = ".omp"


def root(base: Path) -> Path:
    """The `.omp/` directory itself, given the project root `base`."""
    return Path(base) / LEGACY_ROOT


def structure_md(base: Path) -> Path:
    return root(base) / "STRUCTURE.md"


def datasets_md(base: Path) -> Path:
    return root(base) / "DATASETS.md"


def wiki_dir(base: Path) -> Path:
    return root(base) / "wiki"


def learned_md(base: Path) -> Path:
    return root(base) / "learned.md"


def garden_state_json(base: Path) -> Path:
    return root(base) / "garden-state.json"


def secretary_dir(base: Path) -> Path:
    return root(base) / "secretary"


def rules_json(base: Path) -> Path:
    return root(base) / "rules.json"


def brief_md(base: Path) -> Path:
    return secretary_dir(base) / "BRIEF.md"


def state_dir(base: Path) -> Path:
    return root(base) / "state"


def verify_throttle_json(base: Path) -> Path:
    return state_dir(base) / "verify-throttle.json"


# Relative-string (not Path) forms, for callers that compare against a
# `path.relative_to(root).as_posix()` string rather than joining onto a base
# (omp_doc_garden's OWNED_BY_AUDIT set) or a glob pattern (its DEFAULT_DOC_GLOBS).
STRUCTURE_MD_REL = f"{LEGACY_ROOT}/STRUCTURE.md"
DATASETS_MD_REL = f"{LEGACY_ROOT}/DATASETS.md"
DEFAULT_DOC_GLOBS = ("*.md", f"{LEGACY_ROOT}/*.md", "docs/*.md")


def is_inside_store(path_str: str) -> bool:
    """True if `path_str` names something inside `.omp/` — a `/.omp/` segment
    anywhere, or a path that ends at `.omp` itself.

    Exact port of the inline check omp_verify_emit.py used to compute this:
    `"/.omp/" in normalized or normalized.endswith("/.omp")`. Do not tighten
    this into a real path parse — P2 is behavior-unchanged only.
    """
    normalized = str(path_str).replace("\\", "/")
    return f"/{LEGACY_ROOT}/" in normalized or normalized.endswith(f"/{LEGACY_ROOT}")
