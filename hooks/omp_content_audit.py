"""Deterministic content_conventions + wikilink checks for omp-audit.

Pure stdlib (re, pathlib). No file mutation. Returns violation dicts.
The `auditor` agent invokes these as the canonical check algorithm.
"""
from __future__ import annotations
import re
from pathlib import Path
from typing import Iterable

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
