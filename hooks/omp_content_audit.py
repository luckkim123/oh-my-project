"""Deterministic content_conventions + wikilink checks for omp-audit.

Pure stdlib (re, pathlib). No file mutation. Returns violation dicts.
The `auditor` agent invokes these as the canonical check algorithm.
"""
from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

sys.path.insert(0, str(Path(__file__).parent))
from omp_paths import HQ_ROOT, datasets_md, learned_md, structure_md, wiki_dir  # noqa: E402

_FM = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?", re.DOTALL)


def split_frontmatter(text: str) -> tuple[str, str]:
    """Return (frontmatter_text, body_text). Empty frontmatter if no leading --- fence."""
    m = _FM.match(text)
    if not m:
        return "", text
    return m.group(1), text[m.end():]


def check_content_rule(rule: dict, files: Iterable[Path]) -> list[dict]:
    """Apply one content_conventions rule to files. Returns a list of violation dicts."""
    chk = rule["check"]
    pattern = re.compile(chk["pattern"], re.MULTILINE)
    expect = chk["expect"]                      # 'present' | 'absent'
    scope = chk.get("scope", "body")
    severity = rule.get("severity", "warn")
    violations = []
    for f in files:
        text = Path(f).read_text(encoding="utf-8", errors="replace")
        target = split_frontmatter(text)[0] if scope == "frontmatter" else text
        matched = bool(pattern.search(target))
        bad = (expect == "present" and not matched) or (expect == "absent" and matched)
        if bad:
            violations.append({"file": str(f), "severity": severity,
                               "rule": rule.get("description", ""), "expect": expect})
    return violations


_WIKILINK = re.compile(r"!?\[\[([^\]\|#]+)(?:#[^\]\|]+)?(?:\|[^\]]+)?\]\]")
_EXT = re.compile(r"\.([^.\\/]+)\Z")


def find_dead_links(root: Path) -> list[dict]:
    r"""Scan all .md under root for [[target]] links whose target resolves to no file.

    Obsidian resolution: match by basename, case-insensitively (wikilinks ignore case).
    A `.md` suffix is optional; a non-`.md` extension marks an attachment embed
    (e.g. `![[img.png]]`) which is skipped (attachment existence is out of scope).
    alias (|...) and heading (#...) are stripped before resolving; a table-escaped
    `\|` alias separator (Obsidian table cells) is normalized so its trailing
    backslash is not captured into the target. Returns info-level hints.
    """
    root = Path(root)
    md_files = list(root.rglob("*.md"))
    stems = {f.stem.casefold() for f in md_files}
    dead = []
    for f in md_files:
        text = f.read_text(encoding="utf-8", errors="replace")
        for m in _WIKILINK.finditer(text):
            target = m.group(1).strip().rstrip("\\").strip()
            base = target.rsplit("/", 1)[-1]
            ext = _EXT.search(base)
            if ext and ext.group(1).lower() != "md":
                continue
            stem = base[: ext.start()] if ext else base
            if stem.casefold() not in stems:
                dead.append({"file": str(f), "target": target, "severity": "info"})
    return dead


_BACKTICK_PATH = re.compile(r"`([\w.\-]+(?:/[\w.\-]+)+/?)`")

# A backtick string that names a *shape* rather than a file: `journal/YYYY-MM-DD.md`,
# `decisions/NNNN-slug.md`, `3_Archive/etc/...zip`. These can never exist on disk, so
# reporting them as drift is pure noise, and noise is not free -- a findings list that
# is mostly wrong stops being read, taking the real entries with it. Measured on one
# vault: 13 structure_drift findings, of which 4 were these (and 4 were genuine).
# Only shapes actually observed are listed; do not add speculative tokens, and note
# bare MM/DD are deliberately absent (too plausible as a real name fragment) -- the
# YYYY in a date template already carries the match.
_PLACEHOLDER_PATH = re.compile(r"YYYY|NNNN|\.\.\.")

WIKI_STALE_DAYS = 30
WIKI_OVERSIZED_BYTES = 50_000
LEARNED_STUCK_DAYS = 30

# An unresolved commitment in a wiki note, written as a markdown checkbox.
# Deliberately NOT a prose scan: matching words like 미결/TODO/pending in running
# text measured 3 false positives out of 7 hits on one vault -- a heading that
# *declares the item resolved* matches, and so does a filename containing "TODO".
# Prose carries no machine-readable open/closed state; a checkbox does, and
# closing one is a single character. Full rejection:
# docs/design/2026-08-14-resurfacing-detector-measurement.md
_OPEN_ITEM = re.compile(r"^[ \t]*[-*+][ \t]+\[ \][ \t]+(\S.*)$", re.M)
OPEN_ITEM_PREVIEW = 3   # how many item texts a finding quotes
OPEN_ITEM_CHARS = 60    # per-item quote budget


def scan_structure_drift(root: Path, rules: dict) -> list[dict]:
    """Flag rules.json structure.directories[] paths (and backtick-quoted paths in
    STRUCTURE.md/DATASETS.md) that no longer exist on disk. Returns {"kind":"structure_drift", "path":...}.
    """
    root = Path(root)
    paths: list[str] = []
    for d in rules.get("structure", {}).get("directories", []):
        p = d.get("path")
        if p:
            paths.append(p)
    for f in (structure_md(root), datasets_md(root)):
        if f.is_file():
            text = f.read_text(encoding="utf-8", errors="replace")
            paths.extend(m.group(1).rstrip("/") for m in _BACKTICK_PATH.finditer(text)
                         if not _PLACEHOLDER_PATH.search(m.group(1)))
    seen = set()
    finds = []
    for p in paths:
        if p in seen:
            continue
        seen.add(p)
        if not (root / p).exists():
            finds.append({"kind": "structure_drift", "path": p})
    return finds


_OBS_ID = re.compile(r"^##\s*(OBS-\d+)", re.M)
_OBS_FIELD = re.compile(r"^-\s*(\w+):\s*(.*)$", re.M)


def _parse_obs_blocks(text: str) -> list[dict]:
    """Split learned.md into OBS-NNNN blocks and parse their '- field: value' lines."""
    ids = list(_OBS_ID.finditer(text))
    blocks = []
    for i, m in enumerate(ids):
        start = m.end()
        end = ids[i + 1].start() if i + 1 < len(ids) else len(text)
        chunk = text[start:end]
        fields = {"id": m.group(1)}
        for fm in _OBS_FIELD.finditer(chunk):
            fields[fm.group(1)] = fm.group(2).strip()
        blocks.append(fields)
    return blocks


def lint_wiki(root: Path, now: Optional[datetime] = None) -> list[dict]:
    """Wiki + learned.md hygiene lint. Returns finding dicts {"kind":..., "path":..., "detail":...}.

    kinds: orphan (no backlink from another note), stale (mtime > WIKI_STALE_DAYS),
    oversized (> WIKI_OVERSIZED_BYTES), open_item (unchecked `- [ ]` commitments in a
    wiki note -- the resurfacing channel for actions the notes promised; no age gate,
    see _OPEN_ITEM), broken-ref (documented alias for find_dead_links,
    not re-run here to avoid duplicate reporting), stuck_candidate / ready_to_promote /
    contradiction (learned.md OBS blocks — see references/learning-protocol.md §2 for the
    block format; ready_to_promote = candidate at evidence_count>=3 with
    counter_examples==0 and user_overridden false, per §3 — ripe for omp-learn).
    """
    root = Path(root)
    now = now or datetime.now()
    wiki = wiki_dir(root)
    finds: list[dict] = []

    if wiki.is_dir():
        notes = sorted(wiki.glob("*.md"))
        linked = set()
        for f in notes:
            text = f.read_text(encoding="utf-8", errors="replace")
            for m in _WIKILINK.finditer(text):
                target = m.group(1).strip().rstrip("\\").strip().rsplit("/", 1)[-1]
                ext = _EXT.search(target)
                stem = target[: ext.start()] if ext else target
                linked.add(stem.casefold())
        for f in notes:
            if f.stem.casefold() not in linked:
                finds.append({"kind": "orphan", "path": str(f), "detail": "no backlink from another wiki note"})
            age_days = (now - datetime.fromtimestamp(f.stat().st_mtime)).days
            if age_days > WIKI_STALE_DAYS:
                finds.append({"kind": "stale", "path": str(f), "detail": "%dd since last edit" % age_days})
            if f.stat().st_size > WIKI_OVERSIZED_BYTES:
                finds.append({"kind": "oversized", "path": str(f), "detail": "%d bytes" % f.stat().st_size})
            # Unresolved commitments recorded in this note. No age gate: file mtime
            # answers "was the page edited", not "how long has this item sat" -- the
            # motivating vault case had a 3-month-old item in a file whose mtime was
            # 0.0d because a different session appended a section that morning. An
            # unchecked box is actionable on sight; omp-brief enumerates it and the
            # human decides. Reporting is per-file so one note cannot flood the brief.
            # Re-read rather than reusing the backlink pass's `text`: that name holds
            # whatever the LAST note in the first loop bound, not this file's body.
            body = f.read_text(encoding="utf-8", errors="replace")
            open_items = [t.strip() for t in _OPEN_ITEM.findall(body)]
            if open_items:
                preview = "; ".join(t[:OPEN_ITEM_CHARS] for t in open_items[:OPEN_ITEM_PREVIEW])
                if len(open_items) > OPEN_ITEM_PREVIEW:
                    preview += "; ..."
                finds.append({"kind": "open_item", "path": str(f),
                              "detail": "%d unchecked: %s" % (len(open_items), preview)})

    learned = learned_md(root)
    if learned.is_file():
        blocks = _parse_obs_blocks(learned.read_text(encoding="utf-8", errors="replace"))
        by_glob: dict[str, list[dict]] = {}
        for b in blocks:
            if b.get("status") != "candidate":
                continue
            try:
                evidence_count = int(b.get("evidence_count", "0"))
            except ValueError:
                evidence_count = 0
            first_seen = b.get("first_seen", "")
            if evidence_count < 3 and first_seen:
                try:
                    age_days = (now - datetime.strptime(first_seen, "%Y-%m-%d")).days
                    if age_days > LEARNED_STUCK_DAYS:
                        finds.append({"kind": "stuck_candidate", "path": b["id"],
                                      "detail": "evidence_count=%d, %dd since first_seen" % (evidence_count, age_days)})
                except ValueError:
                    pass
            elif evidence_count >= 3:
                # ripe for omp-learn promotion per protocol §3: evidence threshold
                # AND counter_examples == 0 (a counter-example kills promotion
                # outright) AND no durable user "no" (user_overridden). §3's
                # non-contradiction criterion stays at the human gate (the
                # contradiction finding below surfaces it independently).
                # A candidate at threshold otherwise produces no finding (stuck
                # fires only < 3), so it would be invisible to enumeration -- the
                # actionable-status gap this closes. Derived from existing fields
                # (no new schema); the human gate still decides.
                try:
                    counter_examples = int(b.get("counter_examples", "0"))
                except ValueError:
                    # malformed/unparseable value is unknown, not "no counter-examples" --
                    # must not satisfy the ==0 promote gate below (fail conservative,
                    # not permissive).
                    counter_examples = None
                overridden = b.get("user_overridden", "").strip().lower() == "true"
                if counter_examples == 0 and not overridden:
                    finds.append({"kind": "ready_to_promote", "path": b["id"],
                                  "detail": "evidence_count=%d >= 3 -- run omp-learn or defer" % evidence_count})
            applies_to = b.get("applies_to") or b.get("target")
            if applies_to:
                by_glob.setdefault(applies_to, []).append(b)
        for glob_key, group in by_glob.items():
            constraints = {b.get("path_constraint") for b in group if b.get("path_constraint")}
            if len(constraints) > 1:
                finds.append({"kind": "contradiction", "path": glob_key,
                              "detail": "conflicting path_constraint across %s" %
                                        ", ".join(b["id"] for b in group)})

    return finds


# --------------------------------------------------------------------------
# Store-layer audit (`rules.json.layers`, store-spec §3/§5).
#
# The `.hq/` cutover assigns every file to one of four layers, and two of them
# are gitignored on purpose. That split is enforced by nothing at rest: a
# `.gitignore` that misses `community/` deletes the human record on the next
# clone, and neither git nor the migration tool says a word — the store looks
# healthy right up until another machine reads it. This axis is that missing
# detector, and it deliberately does NOT re-derive per-file layer assignment:
# `migrate-om-store.sh` owns that table, and a second copy of it here would
# drift invisibly (which is the defect the tool's own header warns about).
#
# Absent `rules.json.layers`, the axis returns nothing — a project with no
# unified store is not in violation of a layout it never adopted.
# --------------------------------------------------------------------------

_ANCHOR_LINE = re.compile(r"\Aid: (\S+)\n?\Z")


def _git_ignores(repo: Path, rel: str) -> Optional[bool]:
    """True/False if git can answer, None outside a work tree (no-git anchors)."""
    import subprocess
    try:
        p = subprocess.run(["git", "-C", str(repo), "check-ignore", "-q", rel],
                           capture_output=True)
    except (OSError, ValueError):
        return None
    # 0 = ignored, 1 = not ignored, 128 = not a repo / other fatal
    return True if p.returncode == 0 else (False if p.returncode == 1 else None)


def scan_layers(root: Path, rules: dict) -> list[dict]:
    """Check every `.hq/` anchor at or below root against rules.json.layers.

    Finding kinds:
      layer_unknown   a top-level entry under the store root that is not a
                      declared layer -- a fifth layer nobody agreed to
      layer_tracked   a layer declared tracked that git actually ignores
                      (the silent one: the record dies on the next clone)
      layer_ignored   a layer declared ignored that git does not ignore
                      (session state and locks leak into commits)
      anchor_parse    `.anchor` is not exactly one `id: <slug>` line
    """
    cfg = rules.get("layers")
    if not cfg:
        return []
    root = Path(root)
    store = cfg.get("root", HQ_ROOT)
    tracked = list(cfg.get("tracked", ["community", "config"]))
    ignored = list(cfg.get("ignored", ["work", "runtime"]))
    known = set(tracked) | set(ignored) | {".anchor"}
    finds: list[dict] = []

    anchors = sorted({p.parent.parent for p in root.rglob(f"{store}/.anchor")})
    for anchor in anchors:
        hq = anchor / store
        rel_anchor = str(anchor.relative_to(root)) if anchor != root else "."
        text = (hq / ".anchor").read_text(encoding="utf-8", errors="replace")
        if not _ANCHOR_LINE.match(text):
            finds.append({"kind": "anchor_parse", "path": f"{rel_anchor}/{store}/.anchor",
                          "detail": "expected exactly one 'id: <slug>' line"})
        for entry in sorted(hq.iterdir()):
            if entry.name not in known:
                finds.append({"kind": "layer_unknown", "path": f"{rel_anchor}/{store}/{entry.name}",
                              "detail": "not one of %s" % ", ".join(sorted(known))})
        for layer, want_ignored in [(l, False) for l in tracked] + [(l, True) for l in ignored]:
            if not (hq / layer).exists():
                continue
            rel = str((hq / layer).relative_to(root))
            got = _git_ignores(root, rel)
            if got is None or got == want_ignored:
                continue
            finds.append({"kind": "layer_ignored" if want_ignored else "layer_tracked",
                          "path": rel,
                          "detail": "declared %s but git says %s" % (
                              "ignored" if want_ignored else "tracked",
                              "tracked" if got is False else "ignored")})
    return finds
