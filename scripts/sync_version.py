"""Version SSOT drift checker, ported from oh-my-scholar's sync_version.py
(same semantics, adapted to omp's version source).

① `.claude-plugin/plugin.json` `version` — the anchor. ② CHANGELOG.md top
*released* entry (`## [Unreleased]` is skipped, it is not a release). ③ the
latest `v*` git tag (exact `vMAJOR.MINOR.PATCH` match only — `-rc` suffixes
and non-`v`-prefixed tags don't count, max by numeric tuple). ④ the omha
card at `<OMHA_ROOT>/cards/omp.json` (a foreign repo — optional surface).

Pre-tag window: right after a CHANGELOG/plugin.json bump but before the
release tag is cut, `latest_tag` still equals the *previous* release — that
is expected, not drift, so the tag surface accepts either the current or the
previous released version (release-in-progress OK). Two or more versions
behind is drift. A fresh clone with no tags at all skips the tag surface
entirely rather than failing.

Only the *latest* tag is checked, not full tag history.

This CLI is read-only: it reports drift, it never edits plugin.json,
CHANGELOG.md, or the card.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

TAG_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
CHANGELOG_RE = re.compile(r"^## \[(\d+\.\d+\.\d+)\]")


def parse_changelog(path) -> list:
    """Released version strings, top-to-bottom, `## [Unreleased]` skipped."""
    text = Path(path).read_text(encoding="utf-8")
    return [m.group(1) for line in text.splitlines() if (m := CHANGELOG_RE.match(line))]


def parse_tags(tags):
    """Latest exact `vMAJOR.MINOR.PATCH` tag by numeric tuple, or None."""
    best, best_tuple = None, None
    for t in tags:
        m = TAG_RE.match(t)
        if not m:
            continue
        tup = tuple(int(x) for x in m.groups())
        if best_tuple is None or tup > best_tuple:
            best, best_tuple = t, tup
    return best


def gather(repo_root) -> dict:
    """Read the 3 local surfaces + resolve the (optional, foreign) card."""
    repo_root = Path(repo_root)
    plugin = json.loads((repo_root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]

    versions = parse_changelog(repo_root / "CHANGELOG.md")
    changelog_top = versions[0] if versions else None
    changelog_prev = versions[1] if len(versions) > 1 else None

    try:
        out = subprocess.run(
            ["git", "-C", str(repo_root), "tag", "-l", "v*"],
            capture_output=True, text=True, check=True,
        ).stdout
        latest_tag = parse_tags([t for t in out.splitlines() if t.strip()])
    except (subprocess.CalledProcessError, OSError):
        latest_tag = None

    omha_root = Path(os.environ.get("OMHA_ROOT", "~/oh-my-heroacademia")).expanduser()
    card = None
    try:
        data = json.loads((omha_root / "cards" / "omp.json").read_text(encoding="utf-8"))
        if isinstance(data, dict):
            version = data.get("version")
            if isinstance(version, str):
                card = version
    except (OSError, ValueError):
        pass

    return {
        "plugin": plugin,
        "changelog_top": changelog_top,
        "changelog_prev": changelog_prev,
        "latest_tag": latest_tag,
        "card": card,
    }


def check(plugin, changelog_top, changelog_prev, latest_tag, card) -> list:
    """Drift strings across the 4 surfaces (empty = in sync). Card drift is
    prefixed `card:` — a foreign-repo surface that downstream consumers must
    route to WARN, never FAIL, unlike the other 3 surfaces."""
    drift = []

    if plugin != changelog_top:
        drift.append(f"plugin.json version {plugin} != CHANGELOG top released {changelog_top}")

    if latest_tag is not None:
        tag_version = latest_tag[1:] if latest_tag.startswith("v") else latest_tag
        if tag_version not in (plugin, changelog_prev):
            drift.append(
                f"latest tag {latest_tag} matches neither plugin.json {plugin} "
                f"nor previous released {changelog_prev}"
            )

    if card is not None and card != plugin:
        drift.append(f"card: omha card version {card} != plugin.json {plugin}")

    return drift


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Report version drift across the 4 SSOT surfaces (read-only).")
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args(argv)
    repo_root = Path(args.repo_root).resolve()

    s = gather(repo_root)
    drift = check(s["plugin"], s["changelog_top"], s["changelog_prev"], s["latest_tag"], s["card"])

    # Rows below read PASS/DRIFT off `drift` (check()'s output) by surface
    # prefix rather than re-deriving the comparison — one rule source only.
    def row(prefix, drift_value):
        hit = next((d for d in drift if d.startswith(prefix)), None)
        return f"DRIFT: {drift_value}" if hit else "PASS"

    print(f"plugin.json version:    {s['plugin']} (anchor)")
    print(f"CHANGELOG top released: {row('plugin.json version', s['changelog_top'])}")

    if s["latest_tag"] is None:
        print("latest git tag:         SKIP (no v* tags found)")
    else:
        print(f"latest git tag:         {row('latest tag', s['latest_tag'])}")

    if s["card"] is None:
        print("omha card version:      SKIP (card not found)")
    else:
        print(f"omha card version:      {row('card:', 'card:' + s['card'])}")

    if drift:
        print("\nDrift detected:")
        for d in drift:
            print(f"  - {d}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
