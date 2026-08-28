"""Single declaration point for this repo's on-disk root literals — the unified
store `.hq` and the legacy store `.omp`.

Every derived path hooks/*.py computes (rules.json, secretary/, wiki/,
garden-state.json, verify-throttle.json, ...) is named here once. Callers never
join a root literal themselves; a re-entry lint (tests/test_omp_paths_lint.py)
fails the build if either literal appears anywhere outside this file.

Reference: ~/oh-my-orchestrator/skills/harness/references/store-spec.md
  §3 the four layers · §6 the four-state gate · §7 fallback · §9.3 omp's
  per-file layer assignment · §9.5 the six declaration sites.

P3 (2026-08-28) switched this module from "legacy only" to the cutover shape.
P7 (2026-08-28) closed store-spec §7 stage 2 — fallback removal. Two rules
govern every helper below, and they are not interchangeable:

**1. The anchor decides, per project, in both directions.** A project whose
root carries a parseable `.hq/.anchor` resolves every read *and* every write
to `.hq/` — no existence check, no legacy fallback. A project without one
resolves both to `.omp/`, exactly as it always did. Stage 1 needed a split
between the two (a write-only gate, plus a read that tried `.hq/` first only
if the specific file already existed there) because an anchor could be seeded
before its files were copied over; a reader had to keep finding content on
whichever path actually held it. Stage 2 declares that transition window
closed: an anchor is only created once its project's files are copied and
verified (`migrate-om-store.sh apply`), so there is nothing left for a
per-file existence check to protect. `_read` and `_write` collapse into one
`_resolve`, gated on `has_anchor` alone.

**2. The layer is per file, never per directory** (§3). `.omp/` is one flat
directory today and it fans out into four layers: rules/manifest/STRUCTURE/
DATASETS/learned/secretary -> `config/project/`, wiki -> `community/`,
garden-state and the old `state/` contents -> `runtime/project/`, and `work/`
-> `work/project/`.

Two P3 scope boundaries worth stating, because both look like bugs otherwise:

- `secretary/` moves **whole** into `config/project/`. §9.3 marks the narrative
  half (journal/BRIEF/raid/todo/done) a "community candidate — P6 approval
  item" whose transition needs a chronicler hook revision; splitting it here
  would force that decision rather than preserve it. `ledger.jsonl` is
  unambiguously `config/project/`, so the directory follows it and P6 promotes
  the narrative half.
- `wiki/` lands at `community/wiki/`, not `community/posts/`. §9.3's target is
  the *layer* (2); the `posts/` shape additionally requires converting each page
  into the post schema with a `subject:` field, which store-spec and
  decision/010 both assign to P6. The layer is correct now; the conversion is
  not P3's.
"""
from __future__ import annotations

import re
from pathlib import Path

HQ_ROOT = ".hq"
LEGACY_ROOT = ".omp"

# --- layer roots (store-spec section 3) ------------------------------------

ANCHOR_REL = f"{HQ_ROOT}/.anchor"
_CONFIG_REL = f"{HQ_ROOT}/config/project"
_COMMUNITY_REL = f"{HQ_ROOT}/community"
_RUNTIME_REL = f"{HQ_ROOT}/runtime/project"
_WORK_REL = f"{HQ_ROOT}/work/project"

_ANCHOR_ID_RE = re.compile(r"^id:\s*(\S.*)$")


def legacy_root(base: Path) -> Path:
    """The legacy store directory itself, given the project root `base`."""
    return Path(base) / LEGACY_ROOT


def anchor_file(base: Path) -> Path:
    return Path(base) / ANCHOR_REL


def config_dir(base: Path) -> Path:
    return Path(base) / _CONFIG_REL


def community_dir(base: Path) -> Path:
    return Path(base) / _COMMUNITY_REL


def runtime_dir(base: Path) -> Path:
    return Path(base) / _RUNTIME_REL


def work_dir(base: Path) -> Path:
    return Path(base) / _WORK_REL


def migrated_jsonl(base: Path) -> Path:
    """The anchor-wide migration ledger — `config/`, not `config/project/`:
    it is shared across harnesses (store-spec section 2)."""
    return Path(base) / HQ_ROOT / "config" / "migrated.jsonl"


# --- anchor parse and the four-state gate (store-spec sections 2 and 6) -----

class AnchorError(Exception):
    """The anchor file exists but does not parse — a corrupt store, never an
    absent one."""


def parse_anchor_id(path: Path) -> str:
    """Exactly one non-empty line `id: <value>` after stripping one trailing
    newline. Anything else raises. Deliberately a 10-line reimplementation of
    omo's `hq.anchor.parse_anchor` rather than a cross-plugin import: omp
    cannot assume oh-my-orchestrator is installed, and an ImportError in a
    SessionStart hook is a worse failure than a duplicated regex."""
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except OSError as e:
        raise AnchorError(f"{path}: cannot read anchor file: {e}") from e
    text = raw[:-1] if raw.endswith("\n") else raw
    non_empty = [ln for ln in text.split("\n") if ln.strip() != ""]
    if len(non_empty) != 1:
        raise AnchorError(
            f"{path}: expected exactly one non-empty line, found {len(non_empty)}")
    m = _ANCHOR_ID_RE.match(non_empty[0])
    if not m:
        raise AnchorError(
            f"{path}: line does not match 'id: <value>': {non_empty[0]!r}")
    value = m.group(1).strip()
    if not value:
        raise AnchorError(f"{path}: empty id value")
    return value


def has_anchor(base: Path) -> bool:
    """True when `base` carries a *parseable* anchor. An unparseable one is
    False here and `corrupt` in `gate_state` — the write switch must not flip
    on a broken file."""
    f = anchor_file(base)
    if not f.is_file():
        return False
    try:
        parse_anchor_id(f)
        return True
    except AnchorError:
        return False


def has_legacy_store(base: Path) -> bool:
    return legacy_root(base).is_dir()


def has_store(base: Path) -> bool:
    """True when `base` is an omp project under either store. This is what
    replaced the old `root(base).is_dir()` existence check."""
    return anchor_file(base).is_file() or has_legacy_store(base)


GATE_OFF = "off"
GATE_LEGACY = "legacy"
GATE_NORMAL = "normal"
GATE_CORRUPT = "corrupt"


def gate_state(base: Path) -> str:
    """store-spec section 6, the pair (legacy store, anchor) — never a single
    marker.

    off      no legacy store, no anchor   — not an omp project; hooks exit 0
    legacy   legacy store, no anchor      — warn: unmigrated. Every read and
             write stays on `.omp/` — stage 2 removed the per-file existence
             fallback, so a `.hq/` file that happens to exist here already
             (partially seeded, or a stray copy) is never read
    normal   anchor present and parseable
    corrupt  anchor present, unparseable  — loud, never silent

    Row 4 is read as "never silent", not "always exit 2" (the PreCompact
    exception in section 6); each hook picks its own loud channel.
    """
    f = anchor_file(base)
    if f.is_file():
        try:
            parse_anchor_id(f)
            return GATE_NORMAL
        except AnchorError:
            return GATE_CORRUPT
    return GATE_LEGACY if has_legacy_store(base) else GATE_OFF


# --- resolution: the anchor decides, in both directions ---------------------

def _resolve(base: Path, new: Path, legacy: Path) -> Path:
    """Rule 1, stage 2. `has_anchor(base)` is the only test — not existence of
    either path. An anchored root resolves here whether or not this specific
    artifact has been copied yet; an unanchored root resolves to legacy even if
    a `.hq/` file already happens to exist. The per-file existence check stage 1
    needed to protect the seed-then-copy window is gone because that window is
    gone: an anchor is only ever created after its files are copied and
    verified (store-spec §7)."""
    return new if has_anchor(base) else legacy


# --- config/project/ layer --------------------------------------------------

def rules_json(base: Path) -> Path:
    return _resolve(base, config_dir(base) / "rules.json",
                     legacy_root(base) / "rules.json")


def manifest_json(base: Path) -> Path:
    return _resolve(base, config_dir(base) / "manifest.json",
                     legacy_root(base) / "manifest.json")


def structure_md(base: Path) -> Path:
    return _resolve(base, config_dir(base) / "STRUCTURE.md",
                     legacy_root(base) / "STRUCTURE.md")


def datasets_md(base: Path) -> Path:
    return _resolve(base, config_dir(base) / "DATASETS.md",
                     legacy_root(base) / "DATASETS.md")


def learned_md(base: Path) -> Path:
    return _resolve(base, config_dir(base) / "learned.md",
                     legacy_root(base) / "learned.md")


def secretary_dir(base: Path) -> Path:
    """The anchor decides — no existence check. An anchored root's secretary/
    lives in `config/project/` whether or not it has been created there yet;
    callers `mkdir(parents=True, exist_ok=True)` as needed. Serves both readers
    and writers now that stage 2 makes them the same computation."""
    return _resolve(base, config_dir(base) / "secretary",
                     legacy_root(base) / "secretary")


def brief_md(base: Path) -> Path:
    return secretary_dir(base) / "BRIEF.md"


# --- community/ layer -------------------------------------------------------

def wiki_dir(base: Path) -> Path:
    return _resolve(base, community_dir(base) / "wiki", legacy_root(base) / "wiki")


# --- runtime/project/ layer -------------------------------------------------

def garden_state_json(base: Path) -> Path:
    return _resolve(base, runtime_dir(base) / "garden-state.json",
                     legacy_root(base) / "garden-state.json")


def verify_throttle_json(base: Path) -> Path:
    return _resolve(base, runtime_dir(base) / "verify-throttle.json",
                     legacy_root(base) / "state" / "verify-throttle.json")


# --- relative-string forms --------------------------------------------------
# For callers that compare against a `path.relative_to(root).as_posix()` string
# rather than joining onto a base (omp_doc_garden's OWNED_BY_AUDIT) or that
# need a glob pattern (its DEFAULT_DOC_GLOBS). Both stores are listed because
# an anchored project's copy lives under `_CONFIG_REL`/`_COMMUNITY_REL` and an
# unanchored one's still lives under `LEGACY_ROOT` — whichever this project is,
# not both at once (rule 1).

STRUCTURE_MD_RELS = (f"{_CONFIG_REL}/STRUCTURE.md", f"{LEGACY_ROOT}/STRUCTURE.md")
DATASETS_MD_RELS = (f"{_CONFIG_REL}/DATASETS.md", f"{LEGACY_ROOT}/DATASETS.md")
OWNED_BY_AUDIT_RELS = frozenset(STRUCTURE_MD_RELS + DATASETS_MD_RELS)

DEFAULT_DOC_GLOBS = (
    "*.md",
    f"{LEGACY_ROOT}/*.md",
    f"{_CONFIG_REL}/*.md",
    f"{_COMMUNITY_REL}/*.md",
    "docs/*.md",
)


def is_inside_store(path_str: str) -> bool:
    """True if `path_str` names something inside either store — a legacy-root
    or unified-root segment anywhere, or a path ending at one of the roots.

    Widened from the legacy-only check omp_verify_emit used before P3. The
    unified store holds sibling harnesses' state as well as omp's, and the
    caller's question ("is this a harness state file I should not nag about?")
    is answered the same way for all of them.
    """
    normalized = str(path_str).replace("\\", "/")
    for r in (LEGACY_ROOT, HQ_ROOT):
        if f"/{r}/" in normalized or normalized.endswith(f"/{r}"):
            return True
    return False
