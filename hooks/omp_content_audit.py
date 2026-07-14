"""Deterministic content_conventions + wikilink checks for omp-audit.

Pure stdlib (re, pathlib). No file mutation. Returns violation dicts.
The `auditor` agent invokes these as the canonical check algorithm.
"""
from __future__ import annotations
import re
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

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

WIKI_STALE_DAYS = 30
WIKI_OVERSIZED_BYTES = 50_000
LEARNED_STUCK_DAYS = 30


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
    for name in ("STRUCTURE.md", "DATASETS.md"):
        f = root / ".omp" / name
        if f.is_file():
            text = f.read_text(encoding="utf-8", errors="replace")
            paths.extend(m.group(1).rstrip("/") for m in _BACKTICK_PATH.finditer(text))
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
    oversized (> WIKI_OVERSIZED_BYTES), broken-ref (documented alias for find_dead_links,
    not re-run here to avoid duplicate reporting), stuck_candidate / ready_to_promote /
    contradiction (learned.md OBS blocks — see references/learning-protocol.md §2 for the
    block format; ready_to_promote = candidate at evidence_count>=3, ripe for omp-learn).
    """
    root = Path(root)
    now = now or datetime.now()
    wiki = root / ".omp" / "wiki"
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

    learned = root / ".omp" / "learned.md"
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
                # ripe for omp-learn promotion. A candidate at threshold otherwise
                # produces no finding (stuck fires only < 3), so it would be invisible
                # to enumeration -- the actionable-status gap this closes. Derived from
                # existing fields (no new schema); the human gate still decides.
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
